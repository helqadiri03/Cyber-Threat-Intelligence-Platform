#!/usr/bin/env bash
# Fixes intermittent "lookup registry-1.docker.io / production.cloudfront.docker.com: no such host"
# when using systemd-resolved stub DNS (127.0.0.53). Run once with: sudo ./scripts/fix-docker-dns.sh

set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run with sudo: sudo $0"
  exit 1
fi

mkdir -p /etc/systemd/resolved.conf.d
cat > /etc/systemd/resolved.conf.d/docker-dns.conf <<'EOF'
[Resolve]
DNS=8.8.8.8 1.1.1.1
FallbackDNS=1.0.0.1
EOF

ln -sf /run/systemd/resolve/resolv.conf /etc/resolv.conf
systemctl restart systemd-resolved
systemctl restart docker

echo "Done. Test with: docker pull python:3.11-slim"
