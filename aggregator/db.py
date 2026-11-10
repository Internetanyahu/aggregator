import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_records (
 id INTEGER PRIMARY KEY,
 source TEXT NOT NULL,
 source_id TEXT NOT NULL,
 published_at TEXT,
 retrieved_at TEXT NOT NULL,
 source_url TEXT NOT NULL,
 payload_json TEXT NOT NULL,
 UNIQUE(source, source_id)
);
CREATE TABLE IF NOT EXISTS signals (
 id INTEGER PRIMARY KEY,
 source TEXT NOT NULL,
 source_id TEXT NOT NULL,
 signal_type TEXT NOT NULL,
 signal_date TEXT,
 entity TEXT,
 geography TEXT,
 score REAL NOT NULL,
 explanation TEXT NOT NULL,
 source_url TEXT NOT NULL,
 created_at TEXT NOT NULL,
 UNIQUE(source, source_id, signal_type)
);
CREATE TABLE IF NOT EXISTS ingestion_runs (
 id INTEGER PRIMARY KEY,
 source TEXT NOT NULL,
 started_at TEXT NOT NULL,
 finished_at TEXT,
 status TEXT NOT NULL,
 records_seen INTEGER DEFAULT 0,
 error TEXT
);
"""

def connect(path="data/aggregator.sqlite3"):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(target)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con

def store_records(con, records):
    for r in records:
        con.execute(
            """INSERT INTO raw_records(source,source_id,published_at,retrieved_at,source_url,payload_json)
            VALUES(?,?,?,?,?,?) ON CONFLICT(source,source_id) DO UPDATE SET
            published_at=excluded.published_at,retrieved_at=excluded.retrieved_at,
            source_url=excluded.source_url,payload_json=excluded.payload_json""",
            (r["source"], r["source_id"], r.get("published_at"), r["retrieved_at"],
             r["source_url"], json.dumps(r["payload"], ensure_ascii=False, sort_keys=True)),
        )
    con.commit()
