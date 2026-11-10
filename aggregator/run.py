from __future__ import annotations
import argparse, json, os
from datetime import date, timedelta
from .db import connect, store_records
from .sources import fetch_sec_filings, fetch_campd_hourly, fetch_illinois_warn
from .signals import build_signals

def main():
    p=argparse.ArgumentParser(description="Official-source alternative-data ingestion")
    p.add_argument("--source",choices=["all","sec","campd","warn"],default="all")
    p.add_argument("--sec-tickers",default="",help="Comma-separated ticker symbols; default is first 40 SEC ticker entries")
    p.add_argument("--campd-days",type=int,default=1)
    p.add_argument("--warn-months",type=int,default=2)
    p.add_argument("--db",default="data/aggregator.sqlite3")
    args=p.parse_args()
    con=connect(args.db); sources=[]
    if args.source in ("all","sec"): sources.append(("sec",lambda:fetch_sec_filings([x.strip() for x in args.sec_tickers.split(",") if x.strip()] or None)))
    if args.source in ("all","campd"):
        end=date.today(); begin=end-timedelta(days=max(0,min(args.campd_days-1,30)))
        sources.append(("campd",lambda:fetch_campd_hourly(begin.isoformat(),end.isoformat())))
    if args.source in ("all","warn"): sources.append(("illinois_warn",lambda:fetch_illinois_warn(args.warn_months)))
    summary=[]
    for name,fn in sources:
        try:
            records=fn(); store_records(con,records); signals=build_signals(records)
            for s in signals:
                con.execute("""INSERT INTO signals(source,source_id,signal_type,signal_date,entity,geography,score,explanation,source_url,created_at)
                VALUES(:source,:source_id,:signal_type,:signal_date,:entity,:geography,:score,:explanation,:source_url,:created_at)
                ON CONFLICT(source,source_id,signal_type) DO UPDATE SET explanation=excluded.explanation,created_at=excluded.created_at""",s)
            con.commit(); summary.append({"source":name,"status":"ok","records":len(records),"signals":len(signals)})
        except Exception as exc:
            summary.append({"source":name,"status":"error","error":str(exc)})
    print(json.dumps(summary,indent=2))
    con.close()
    if any(x["status"]=="error" for x in summary): raise SystemExit(1)

if __name__=="__main__": main()
