"""LedgerProof engine: rule-based invoice review (duplicates, amount anomalies). Not AI."""
import csv, io, statistics
from collections import defaultdict

def norm(s): return " ".join(str(s).lower().split())

def parse_csv(text):
    rows = []
    for r in csv.DictReader(io.StringIO(text)):
        rows.append({"id": r["invoice_id"].strip(), "vendor": r["vendor"].strip(),
                     "amount": round(float(r["amount"]), 2), "date": r["date"].strip(),
                     "po": (r.get("po") or "").strip()})
    return rows

def review(invoices, z_limit=2.0, ratio_limit=3.0):
    flags = defaultdict(list)
    seen = {}
    for inv in invoices:
        key = (norm(inv["vendor"]), inv["amount"], inv["date"])
        idkey = (norm(inv["vendor"]), norm(inv["id"]))
        for k, tag in ((key, "duplicate: same vendor, amount and date"),
                       (idkey, "duplicate: same vendor and invoice number")):
            if (k, tag) in seen:
                flags[inv["id"] + "|" + str(invoices.index(inv))].append(tag + f" as {seen[(k, tag)]}")
            else:
                seen[(k, tag)] = inv["id"]
    byv = defaultdict(list)
    for inv in invoices: byv[norm(inv["vendor"])].append(inv)
    for v, lst in byv.items():
        amts = [i["amount"] for i in lst]
        if len(amts) < 3: continue
        for i in lst:
            others = [a for a in amts if a is not i["amount"]] or amts
            med = statistics.median(others)
            sd = statistics.pstdev(others)
            if med and i["amount"] / med >= ratio_limit or (sd and (i["amount"] - statistics.mean(others)) / sd >= z_limit * 2):
                flags[i["id"] + "|" + str(invoices.index(i))].append(f"amount anomaly: {i['amount']} vs vendor median {med}")
    out = []
    for n, inv in enumerate(invoices):
        f = flags.get(inv["id"] + "|" + str(n), [])
        out.append({**inv, "flags": f, "status": "REVIEW" if f else "OK"})
    return out

def decide(item, decision, reason):
    if decision not in ("APPROVE", "HOLD", "REJECT"): raise ValueError("bad decision")
    if not reason or not reason.strip(): raise ValueError("reason required")
    return {"id": item["id"], "decision": decision, "reason": reason.strip()[:200]}

def export_csv(items, decisions):
    d = {x["id"]: x for x in decisions}
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["invoice_id", "vendor", "amount", "status", "flags", "decision", "reason"])
    for i in items:
        x = d.get(i["id"], {})
        cells = [i["id"], i["vendor"], i["amount"], i["status"], "; ".join(i["flags"]), x.get("decision", ""), x.get("reason", "")]
        w.writerow(["'" + c if isinstance(c, str) and c and c[0] in "=+-@\t\r" else c for c in cells])
    return buf.getvalue()

SAMPLE = """invoice_id,vendor,amount,date,po
INV-100,Acme Supplies,1200.00,2026-10-01,PO-1
INV-101,Acme Supplies,1180.00,2026-10-08,PO-1
INV-102,Acme Supplies,1200.00,2026-10-01,PO-1
INV-103,Acme Supplies,1215.00,2026-10-15,PO-1
INV-104,Acme Supplies,9800.00,2026-10-20,PO-2
INV-200,Globex,500.00,2026-10-03,PO-9
"""
