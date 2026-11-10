import tempfile, unittest
from aggregator.db import connect, store_records
from aggregator.signals import build_signals

class PipelineTests(unittest.TestCase):
    def test_warn_signal_is_context_not_lead(self):
        row={"source":"illinois_warn","source_id":"r1","published_at":"2026-10-01",
             "retrieved_at":"2026-10-02T00:00:00Z","source_url":"https://example.gov/report",
             "payload":{"Company Name":"Example Co","City":"Woodstock"}}
        signal=build_signals([row])[0]
        self.assertEqual(signal["score"],0)
        self.assertEqual(signal["signal_type"],"reported_labor_notice")
        self.assertIn("not proof",signal["explanation"])
    def test_records_upsert(self):
        with tempfile.TemporaryDirectory() as d:
            con=connect(d+"/test.db")
            row={"source":"sec","source_id":"cik:acc","published_at":"2026-01-01",
                 "retrieved_at":"2026-01-02T00:00:00Z","source_url":"https://sec.gov/x","payload":{"form":"8-K"}}
            store_records(con,[row,row])
            self.assertEqual(con.execute("select count(*) from raw_records").fetchone()[0],1)
            con.close()

if __name__=="__main__": unittest.main()
