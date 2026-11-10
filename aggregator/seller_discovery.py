"""Public property-opportunity discovery using indexed public sources.

The collector queries Google News RSS, which indexes public reporting and
publicly indexed notices. It does not bypass logins, paywalls, CAPTCHAs, robots
rules, or access controls, and does not harvest private owner contact details.
Results are research leads only, never verified listings or seller motivation.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote_plus, urlparse

import requests

AREAS = [
    '"Lake County" Illinois', '"McHenry County" Illinois',
    '"Kane County" Illinois', '"Cook County" Illinois',
    '"DuPage County" Illinois', '"Will County" Illinois',
    '"Northern Illinois"',
]
TOPICS = [
    ('FSBO / owner-listed', '("for sale by owner" OR FSBO OR "owner listed") (house OR home OR property)'),
    ('Foreclosure / sheriff sale', '(foreclosure OR "sheriff sale" OR "judicial sale") (house OR home OR property)'),
    ('Tax sale / tax deed', '("tax sale" OR "tax deed" OR "delinquent property tax") (house OR home OR parcel)'),
    ('Auction / REO', '(real estate auction OR REO OR "bank owned" OR "foreclosed home")'),
]
QUERIES = [(f"{area} · {label}", f'{area} {topic}') for area in AREAS for label, topic in TOPICS]
QUERIES += [
    ("Illinois official foreclosure notices", 'site:il.gov (foreclosure OR "sheriff sale") property'),
    ("Illinois county treasurer tax sales", 'site:*.il.us ("tax sale" OR "tax deed" OR "delinquent taxes") property'),
    ("Illinois county sheriff sales", 'site:*.il.us ("sheriff sale" OR "foreclosure sale") real estate'),
    ("Illinois court foreclosure notices", 'site:illinoiscourts.gov foreclosure property sale'),
    ("HUD homes", 'site:hud.gov homes for sale Illinois HUD homes'),
    ("Fannie Mae HomePath", 'site:homepath.fanniemae.com Illinois property'),
    ("Freddie Mac HomeSteps", 'site:homesteps.com Illinois property'),
    ("USDA property sales", 'site:usda.gov Illinois single family housing REO property sale'),
    ("VA acquired properties", 'site:va.gov acquired property sales Illinois'),
    ("Public FSBO listings", 'Illinois FSBO homes for sale owner listed'),
    ("Public real estate price reductions", 'Illinois house "price reduced" OR "price improvement"'),
]
RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
MAX_AGE_DAYS = 365
MAX_ITEMS = 1200
HEADERS = {"User-Agent": "NorthstarPublicPropertyResearch/1.1 (+public RSS discovery)"}
INTENT = (
    "for sale by owner", "fsbo", "auction", "foreclosure", "sheriff sale",
    "tax sale", "tax deed", "price reduced", "price reduction", "reo",
    "bank owned", "homes for sale", "property sale",
)
PROPERTY = ("property", "home", "house", "residential", "real estate", "parcel", "land")


def clean(value: str | None) -> str:
    return re.sub(r"\\s+", " ", value or "").strip()


def parse_feed(label: str, query: str) -> tuple[list[dict], dict | None]:
    url = RSS.format(query=quote_plus(query))
    try:
        response = requests.get(url, headers=HEADERS, timeout=(8, 22))
        response.raise_for_status()
        root = ET.fromstring(response.content)
        found = []
        for node in root.findall("./channel/item"):
            title = clean(node.findtext("title"))
            link = clean(node.findtext("link"))
            description = clean(node.findtext("description"))
            published = clean(node.findtext("pubDate"))
            if not title or not link:
                continue
            try:
                dt = parsedate_to_datetime(published)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) - dt.astimezone(timezone.utc) > timedelta(days=MAX_AGE_DAYS):
                    continue
            except (TypeError, ValueError, OverflowError):
                continue
            plain = re.sub(r"<[^>]+>", " ", description)
            searchable = (title + " " + plain).lower()
            if not any(term in searchable for term in INTENT):
                continue
            if not any(term in searchable for term in PROPERTY):
                continue
            source = node.find("source")
            publisher = clean(source.text) if source is not None else urlparse(link).netloc.lower()
            publisher_url = clean(source.get("url", "")) if source is not None else ""
            found.append({
                "title": title,
                "url": link,
                "publisher": publisher or urlparse(link).netloc.lower(),
                "publisher_url": publisher_url,
                "published_at": published,
                "description": clean(plain)[:1600],
                "source_query": label,
            })
        return found, None
    except Exception as exc:
        return [], {"feed": label, "error": f"{type(exc).__name__}: {exc}"}


def run(output: str = "public/data/seller_leads.json") -> dict:
    items: dict[str, dict] = {}
    errors = []
    # Parallelize independent public RSS requests, while keeping concurrency modest.
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(parse_feed, label, query) for label, query in QUERIES]
        for future in as_completed(futures):
            rows, error = future.result()
            if error:
                errors.append(error)
            for row in rows:
                canonical = row["url"].split("?", 1)[0].rstrip("/")
                key = hashlib.sha256((canonical or row["title"]).lower().encode()).hexdigest()
                existing = items.get(key)
                if existing is None:
                    row.update({
                        "id": key,
                        "retrieved_at": datetime.now(timezone.utc).isoformat(),
                        "verified": False,
                        "record_type": "public_search_reference",
                    })
                    items[key] = row
                elif row["source_query"] not in existing["source_query"]:
                    existing["source_query"] += " | " + row["source_query"]

    results = sorted(items.values(), key=lambda x: x["published_at"], reverse=True)[:MAX_ITEMS]
    generated = datetime.now(timezone.utc).isoformat()
    payload = {
        "generated_at": generated,
        "method": "Google News RSS indexing of public reporting and indexed public notices; no restricted-site scraping",
        "count": len(results),
        "query_count": len(QUERIES),
        "areas": AREAS,
        "feeds": [label for label, _ in QUERIES],
        "errors": errors,
        "items": results,
        "limitations": [
            "Search references may be news articles, stale pages, duplicates, or non-active listings.",
            "No result verifies ownership, seller authority, availability, price, liens, condition, or motivation.",
            "Government source coverage varies by county; many records are not exposed through a common public feed.",
            "Open each original source and independently verify all facts before relying on it.",
        ],
    }
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
    print(json.dumps({
        "output": str(path),
        "count": len(results),
        "queries": len(QUERIES),
        "feed_errors": errors,
    }, indent=2))
    return payload


if __name__ == "__main__":
    run()
