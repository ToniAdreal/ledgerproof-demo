# Architecture
- engine.py: pure functions. parse_csv, review (duplicate and anomaly rules), decide (reason required), export_csv.
- server.py: stdlib HTTP server. In-memory sessions keyed by a random cookie, 30 minute TTL, 200 session cap, 50 decisions per session.
- Container: python:3.12-slim, non-root user, read-only filesystem, no capabilities, 128 MB memory, 64 PIDs.
- Edge: Caddy terminates HTTPS and proxies to 127.0.0.1:8080 on a Vultr Cloud Compute VM.
- Data: sample fixtures only. Nothing is stored on disk.
