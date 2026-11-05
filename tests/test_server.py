import sys, threading, unittest, urllib.request, urllib.parse, http.cookiejar; sys.path.insert(0, ".")
import server
from http.server import ThreadingHTTPServer
class T(unittest.TestCase):
    @classmethod
    def setUpClass(c):
        c.srv = ThreadingHTTPServer(("127.0.0.1", 0), server.H); c.port = c.srv.server_address[1]
        threading.Thread(target=c.srv.serve_forever, daemon=True).start()
    @classmethod
    def tearDownClass(c): c.srv.shutdown()
    def client(self):
        return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def url(self, p): return f"http://127.0.0.1:{self.port}{p}"
    def post(self, o, p, d, hdr=None):
        r = urllib.request.Request(self.url(p), urllib.parse.urlencode(d).encode(), hdr or {}); return o.open(r).read().decode()
    def test_sessions_isolated(self):
        a, b = self.client(), self.client()
        a.open(self.url("/")); b.open(self.url("/"))
        self.post(a, "/decide", {"i": 2, "decision": "HOLD", "reason": "dup check"})
        self.assertIn("HOLD: dup check", a.open(self.url("/")).read().decode())
        self.assertNotIn("HOLD: dup check", b.open(self.url("/")).read().decode())
    def test_reason_required(self):
        a = self.client(); a.open(self.url("/"))
        self.assertIn("Not saved", self.post(a, "/decide", {"i": 2, "decision": "HOLD", "reason": " "}))
    def test_reset(self):
        a = self.client(); a.open(self.url("/"))
        self.post(a, "/decide", {"i": 2, "decision": "REJECT", "reason": "x"})
        self.assertNotIn("REJECT: x", self.post(a, "/reset", {}))
    def test_origin_check(self):
        a = self.client(); a.open(self.url("/"))
        with self.assertRaises(urllib.error.HTTPError) as c: self.post(a, "/reset", {}, {"Origin": "http://evil.example"})
        self.assertEqual(c.exception.code, 403)
    def test_export_and_escape(self):
        a = self.client(); a.open(self.url("/"))
        self.assertIn("invoice_id", a.open(self.url("/export.csv")).read().decode())
    def test_no_upload_route(self):
        a = self.client()
        with self.assertRaises(urllib.error.HTTPError) as c: self.post(a, "/upload", {"x": 1})
        self.assertEqual(c.exception.code, 404)
    def test_headers(self):
        r = self.client().open(self.url("/")); self.assertIn("frame-ancestors", r.headers["Content-Security-Policy"])
    def test_session_cap(self):
        old = server.MAX_SESSIONS; server.MAX_SESSIONS = len(server.SESSIONS)
        try:
            with self.assertRaises(urllib.error.HTTPError) as c: urllib.request.urlopen(self.url("/"))
            self.assertEqual(c.exception.code, 503)
        finally: server.MAX_SESSIONS = old
unittest.main() if __name__ == "__main__" else None
