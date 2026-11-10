"""Official-source ingestion. All requests retain provenance and retrieval timestamps."""
from __future__ import annotations
import io, json, os, re, time
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin
import requests

SEC_TICKERS = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
CAMPD_HOURLY = "https://api.epa.gov/easey/streaming-services/emissions/apportioned/hourly"
IL_WARN_ARCHIVE = "https://www.illinoisworknet.com/LayoffRecovery/Pages/ArchivedWARNReports.aspx"
TIMEOUT = 45

def now():
    return datetime.now(timezone.utc).isoformat()

def session(user_agent):
    s = requests.Session()
    s.headers.update({"User-Agent": user_agent, "Accept": "application/json, text/html, */*"})
    return s

def fetch_sec_filings(tickers=None, limit=40):
    ua = os.getenv("SEC_USER_AGENT", "").strip()
    if not ua or "@" not in ua:
        raise RuntimeError("Set SEC_USER_AGENT to a descriptive app name and monitored contact email before SEC ingestion.")
    s = session(ua)
    response = s.get(SEC_TICKERS, timeout=TIMEOUT)
    response.raise_for_status()
    mapping = response.json()
    wanted = {x.upper() for x in (tickers or [""]) if x}
    companies = [v for v in mapping.values() if not wanted or str(v.get("ticker","")).upper() in wanted]
    records = []
    for company in companies[:limit]:
        cik = str(company["cik_str"]).zfill(10)
        url = SEC_SUBMISSIONS.format(cik=cik)
        r = s.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        payload = r.json()
        recent = payload.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        for i, accession in enumerate(recent.get("accessionNumber", [])):
            form = forms[i] if i < len(forms) else ""
            if form not in {"8-K", "10-K", "10-Q", "6-K", "20-F"}:
                continue
            filed = recent.get("filingDate", [""])[i]
            primary = recent.get("primaryDocument", [""])[i]
            accn = accession.replace("-", "")
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn}/{primary}" if primary else url
            records.append({"source":"sec","source_id":f"{cik}:{accession}","published_at":filed,
                "retrieved_at":now(),"source_url":filing_url,
                "payload":{"cik":cik,"company":payload.get("name"),"ticker":company.get("ticker"),
                    "form":form,"filed":filed,"accession":accession,"primary_document":primary}})
        time.sleep(0.12)
    return records

def fetch_campd_hourly(begin_date, end_date, state=None):
    api_key = os.getenv("EPA_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("EPA CAMPD requires a free api.data.gov API key. Set EPA_API_KEY; no key is bundled.")
    from datetime import date
    start, end = date.fromisoformat(begin_date), date.fromisoformat(end_date)
    if end < start or (end-start).days > 31:
        raise ValueError("CAMPD hourly query must cover 0–31 days.")
    params = {"api_key":api_key,"beginDate":begin_date,"endDate":end_date}
    if state:
        params["state"] = state
    r = session("NorthstarResearch/1.0 contact: configured-in-environment").get(CAMPD_HOURLY, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise RuntimeError("Unexpected CAMPD response shape; inspect response before ingestion.")
    retrieved = now()
    records=[]
    for i,row in enumerate(data):
        source_id = str(row.get("facilityId") or row.get("orisCode") or row.get("unitId") or i) + ":" + str(row.get("date") or row.get("opDate") or row.get("beginDate") or i)
        records.append({"source":"campd","source_id":source_id,"published_at":row.get("date") or row.get("opDate"),
            "retrieved_at":retrieved,"source_url":r.url,"payload":row})
    return records

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]
    def handle_starttag(self, tag, attrs):
        if tag.lower()=="a":
            a=dict(attrs); href=a.get("href",""); label=a.get("aria-label","")
            if href: self.links.append((href,label))

def fetch_illinois_warn(months=3):
    """Discover official monthly XLSX reports from Illinois workNet's archive page."""
    s=session("NorthstarAggregator/1.0 (public data research)")
    page=s.get(IL_WARN_ARCHIVE,timeout=TIMEOUT); page.raise_for_status()
    parser=LinkParser(); parser.feed(page.text)
    candidates=[]
    for href,label in parser.links:
        full=urljoin(IL_WARN_ARCHIVE,href)
        text=(href+" "+label).lower()
        if (".xlsx" in full.lower() or "monthly warn report" in text) and ("warn" in text or "warn" in full.lower()):
            candidates.append(full)
    # De-duplicate while preserving the order exposed by the official archive.
    candidates=list(dict.fromkeys(candidates))[:max(1,min(int(months),12))]
    if not candidates:
        raise RuntimeError("No monthly XLSX links found on the official Illinois WARN archive page. Do not substitute a third-party feed.")
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError("Install openpyxl to parse official Illinois WARN workbooks.") from exc
    records=[]
    for report_url in candidates:
        res=s.get(report_url,timeout=TIMEOUT); res.raise_for_status()
        wb=load_workbook(io.BytesIO(res.content),read_only=True,data_only=True)
        ws=wb.active
        rows=ws.iter_rows(values_only=True)
        headers=None
        for rownum,row in enumerate(rows):
            values=[str(v).strip() if v is not None else "" for v in row]
            if headers is None:
                if any("company" in v.lower() for v in values) and any("city" in v.lower() for v in values):
                    headers=values
                continue
            if not any(values): continue
            item={headers[i]:values[i] for i in range(min(len(headers),len(values))) if headers[i]}
            if not item: continue
            stable="|".join([item.get(k,"") for k in headers[:5]]) or str(rownum)
            records.append({"source":"illinois_warn","source_id":report_url+"#"+str(rownum)+":"+stable,
                "published_at":None,"retrieved_at":now(),"source_url":report_url,"payload":item})
        wb.close()
    return records
