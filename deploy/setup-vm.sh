#!/usr/bin/env bash
# Run on a fresh Ubuntu Vultr VM as root. Installs Docker, builds and runs LedgerProof behind Caddy.
set -euo pipefail
DOMAIN="${1:?usage: setup-vm.sh <domain-or-ip>}"
apt-get update -y && apt-get install -y docker.io caddy
docker build -t ledgerproof /opt/ledgerproof
docker rm -f ledgerproof 2>/dev/null || true
docker run -d --name ledgerproof --restart unless-stopped --read-only --cap-drop ALL \
  --memory 128m --pids-limit 64 -p 127.0.0.1:8080:8080 ledgerproof
cat > /etc/caddy/Caddyfile <<CADDY
${DOMAIN} {
  reverse_proxy 127.0.0.1:8080
}
CADDY
systemctl restart caddy
echo "LedgerProof up at https://${DOMAIN}"
