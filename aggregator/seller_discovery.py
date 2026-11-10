"""Publicly indexed property-opportunity discovery via Google News RSS.

This is a discovery feed, not a verified listing database. Each item retains its
publisher URL and publication timestamp. No owner contact details are harvested.
"""
from __future__ import annotations
import json, re, hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, urlparse
import xml.etree.ElementTree as ET
import requests

QUERIES = [
    ("Northern Illinois FSBO", '"for sale by owner" (Illinois OR "Lake County" OR "McHenry County" OR "Kane County" OR "Cook County") house'),
    ("Northern Illinois property auction", '(Illinois OR "Lake County" OR "McHenry County" OR "Kane County") (property OR home) (auction OR foreclosure OR sheriff sale)'),
    ("Northern Illinois tax sale", '(Illinois OR "Lake County" OR "McHenry County" OR "Kane County") property ("tax sale" OR "tax deed" OR "delinquent taxes")'),
    ("Northern Illinois price reductions", '(Illinois OR "Lake County" OR "McHenry County" OR "Kane County") home "price reduced" OR "price reduction"'),
]
RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
HEADERS = {"User-Agent": "NorthstarPropertyResearch/1.0 (public RSS discovery)"}

def clean(value):
    return re.sub(r"\\s+", " ", value or "").strip()

def run(output="public/data/seller_leads.json"):
    items, seen = [], set()
    errors = []
    for label, query in QUERIES:
        url = RSS.format(query=quote_plus(query))
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            for node in root.findall("./channel/item"):
                title = clean(node.findtext("title"))
                link = clean(node.findtext("link"))
                description = clean(node.findtext("description"))
                published = clean(node.findtext("pubDate"))
                if not title or not link:
                    continue
                key = hashlib.sha256((link.split("?")[0].rstrip("/") or title).lower().encode()).hexdigest()
                if key in seen:
                    continue
                seen.add(key)
                host = urlparse(link).netloc.lower()
                text = (title + " " + re.sub("<[^>]+>", " ", description)).lower()
                if not any(term in text for term in ("property", "home", "house", "real estate", "foreclosure", "auction", "tax sale", "for sale")):
                    continue
                items.append({
                    "id": key, "label": label, "title": title, "url": link,
                    "publisher": host, "published_at": published,
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "description": clean(re.sub("<[^>]+>", " ", description))[:1200],
                    "source_query": label, "verified": False
                })
        except Exception as exc:
            errors.append({"feed": label, "error": str(exc)})
    items.sort(key=lambda x: x["published_at"], reverse=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": "Google News public RSS search; results are unverified discovery leads",
        "count": len(items), "feeds": [x[0] for x in QUERIES],
        "errors": errors, "items": items[:300]
    }
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
    print(json.dumps({"output": str(path), "count": len(payload["items"]), "feed_errors": errors}, indent=2))
    return payload

if __name__ == "__main__":
    run()
