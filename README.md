# LedgerProof

Invoice review for finance teams. LedgerProof flags duplicate invoices and unusual amounts with plain rules, makes a person write a reason for every decision, and exports the result as CSV.

Built for the Vultr: Agent Rush Hackathon, challenge 2 (Powering the Future of Work, Finance and Accounting). It is a rule-based workflow, not an AI agent.

## What it does
1. Loads a server-built sample set of invoices (public demo mode, no uploads).
2. Checks each invoice: same vendor, amount and date; same vendor and invoice number; amount at least 3x the vendor median.
3. Shows flagged invoices as REVIEW with the reason for the flag.
4. A reviewer chooses APPROVE, HOLD or REJECT and must type a reason.
5. Export the review as CSV (formula-safe cells). Reset restores the demo.

## Run locally
    python3 server.py        # http://127.0.0.1:8080
    python3 -m unittest discover -s tests

## Deploy on a Vultr VM
Copy this folder to /opt/ledgerproof on an Ubuntu VM, then run `deploy/setup-vm.sh <domain-or-ip>`.
It builds the Docker image, runs it read-only with all capabilities dropped, 128 MB memory and a 64 process cap, and puts Caddy in front for HTTPS.

## Vultr usage
Vultr Cloud Compute hosts the app (Docker container behind Caddy). The app is the backend: it holds sessions, runs the checks and produces exports. No other Vultr service is used. Serverless Inference is optional for challenge 2 and is not used.

## Safety choices
Per-visitor sessions that expire after 30 minutes, a cap on sessions and decisions, origin checks on every POST, a strict Content-Security-Policy, escaped output, and no file upload in demo mode.

## License
MIT. See LICENSE.
