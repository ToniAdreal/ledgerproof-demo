"""LedgerProof web app (stdlib only). Public demo mode: server-built sample data only, no uploads."""
import html, json, os, secrets, time, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import engine

TTL = 1800; MAX_SESSIONS = 200; MAX_DECISIONS = 50
SESSIONS = {}

def get_session(sid):
    now = time.time()
    for k in [k for k, v in SESSIONS.items() if now - v["t"] > TTL]: del SESSIONS[k]
    if sid in SESSIONS:
        SESSIONS[sid]["t"] = now; return sid, SESSIONS[sid]
    if len(SESSIONS) >= MAX_SESSIONS: return None, None
    sid = secrets.token_urlsafe(24)
    SESSIONS[sid] = {"t": now, "items": engine.review(engine.parse_csv(engine.SAMPLE)), "decisions": []}
    return sid, SESSIONS[sid]

def page(s, msg=""):
    e = html.escape; d = {x["id"]: x for x in s["decisions"]}
    rows = ""
    for i, it in enumerate(s["items"]):
        dec = d.get(it["id"])
        form = (f'<form method="post" action="/decide"><input type="hidden" name="i" value="{i}">'
                '<select name="decision"><option>APPROVE</option><option>HOLD</option><option>REJECT</option></select> '
                '<input name="reason" maxlength="200" placeholder="Reason (required)" required> <button>Save</button></form>')
        rows += (f'<tr class="{it["status"]}"><td>{e(it["id"])}</td><td>{e(it["vendor"])}</td><td>{it["amount"]:.2f}</td>'
                 f'<td><b>{it["status"]}</b><br>{e("; ".join(it["flags"]))}</td>'
                 f'<td>{e(dec["decision"] + ": " + dec["reason"]) if dec else form}</td></tr>')
    return f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>LedgerProof</title><style>
body{{font:15px system-ui;margin:0;background:#f6f7f9;color:#1c2330}}main{{max-width:980px;margin:auto;padding:24px}}
h1{{margin:0 0 4px}}p.s{{color:#566;margin:0 0 16px}}table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden}}
th,td{{padding:10px;border-bottom:1px solid #e5e8ee;text-align:left;vertical-align:top}}th{{background:#eef1f6}}
tr.REVIEW{{background:#fff6e5}}button{{background:#2456d6;color:#fff;border:0;padding:6px 12px;border-radius:6px}}
.bar{{display:flex;gap:12px;margin:12px 0}}.msg{{color:#a33}}a.b{{background:#fff;border:1px solid #ccd;padding:6px 12px;border-radius:6px;text-decoration:none;color:#222}}
</style><main><h1>LedgerProof</h1><p class=s>Invoice review with duplicate and amount-anomaly rules. Demo data only. Rule-based, no AI.</p>
<p class=msg>{e(msg)}</p><table><tr><th>Invoice</th><th>Vendor</th><th>Amount</th><th>Check</th><th>Human decision</th></tr>{rows}</table>
<div class=bar><a class=b href="/export.csv">Export CSV</a><form method=post action=/reset><button>Reset demo</button></form></div>
<p class=s>Session expires after 30 minutes. Each visitor has an isolated copy.</p></main>"""

class H(BaseHTTPRequestHandler):
    def sid(self):
        for c in self.headers.get("Cookie", "").split(";"):
            k, _, v = c.strip().partition("=")
            if k == "lp": return v
    def send(self, code, body, ctype="text/html; charset=utf-8", sid=None, extra=None):
        b = body.encode()
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b)))
        self.send_header("X-Content-Type-Options", "nosniff"); self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'")
        if sid: self.send_header("Set-Cookie", f"lp={sid}; Path=/; HttpOnly; SameSite=Strict; Max-Age={TTL}")
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self.end_headers(); self.wfile.write(b)
    def origin_ok(self):
        o = self.headers.get("Origin") or self.headers.get("Referer") or ""
        return not o or urllib.parse.urlparse(o).netloc == self.headers.get("Host")
    def do_GET(self):
        sid, s = get_session(self.sid())
        if s is None: return self.send(503, "Busy, try later")
        if self.path == "/healthz": return self.send(200, "ok", "text/plain")
        if self.path == "/export.csv":
            return self.send(200, engine.export_csv(s["items"], s["decisions"]), "text/csv; charset=utf-8", sid,
                             {"Content-Disposition": "attachment; filename=ledgerproof-review.csv"})
        if self.path == "/": return self.send(200, page(s), sid=sid)
        self.send(404, "Not found", "text/plain")
    def do_POST(self):
        if not self.origin_ok(): return self.send(403, "Bad origin", "text/plain")
        n = min(int(self.headers.get("Content-Length") or 0), 4096)
        form = urllib.parse.parse_qs(self.rfile.read(n).decode("utf-8", "replace"))
        sid, s = get_session(self.sid())
        if s is None: return self.send(503, "Busy, try later")
        msg = ""
        if self.path == "/reset":
            s["decisions"].clear(); msg = "Demo reset."
        elif self.path == "/decide":
            try:
                it = s["items"][int(form["i"][0])]
                if len(s["decisions"]) >= MAX_DECISIONS: raise ValueError("decision limit reached")
                if any(d["id"] == it["id"] for d in s["decisions"]): raise ValueError("already decided")
                s["decisions"].append(engine.decide(it, form.get("decision", [""])[0], form.get("reason", [""])[0]))
            except (ValueError, KeyError, IndexError) as ex: msg = f"Not saved: {ex}"
        else: return self.send(404, "Not found", "text/plain")
        self.send(200, page(s, msg), sid=sid)
    def log_message(self, *a): pass

if __name__ == "__main__":
    ThreadingHTTPServer((os.environ.get("HOST", "127.0.0.1"), int(os.environ.get("PORT", "8080"))), H).serve_forever()
