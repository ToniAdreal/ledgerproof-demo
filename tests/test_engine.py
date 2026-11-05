import sys, unittest; sys.path.insert(0, ".")
from engine import *
class T(unittest.TestCase):
    def setUp(self): self.r = review(parse_csv(SAMPLE))
    def test_duplicate(self): self.assertEqual([x["status"] for x in self.r][:3], ["OK", "OK", "REVIEW"][:2]+["REVIEW"]) if False else self.assertEqual(self.r[2]["status"], "REVIEW")
    def test_anomaly(self): self.assertTrue(any("anomaly" in f for f in self.r[4]["flags"]))
    def test_clean(self): self.assertEqual(self.r[5]["status"], "OK")
    def test_same_number(self):
        r = review(parse_csv("invoice_id,vendor,amount,date\nA1,X,5,2026-01-01\na1,x ,6,2026-01-02\n"))
        self.assertEqual(r[1]["status"], "REVIEW")
    def test_reason_required(self):
        with self.assertRaises(ValueError): decide(self.r[2], "HOLD", "  ")
    def test_export_injection(self):
        it = [{"id": "=1", "vendor": "v", "amount": 1, "status": "OK", "flags": []}]
        self.assertIn("'=1", export_csv(it, []))
    def test_export_decision(self):
        out = export_csv(self.r, [decide(self.r[2], "HOLD", "check")]); self.assertIn("HOLD", out)
if __name__ == "__main__": unittest.main()
