#!/usr/bin/env bash
set -euo pipefail

# Generate self-signed cert for LAN HTTPS (if not exists)
CERT_DIR="$(dirname "$0")/certs"
mkdir -p "$CERT_DIR"

if [ ! -f "$CERT_DIR/key.pem" ]; then
    IP="${1:-10.0.0.233}"
    echo "Generating self-signed cert for IP: $IP"
    openssl req -x509 -newkey rsa:4096 -keyout "$CERT_DIR/key.pem" \
        -out "$CERT_DIR/cert.pem" -days 3650 -nodes \
        -subj "/CN=$IP" \
        -addext "subjectAltName=IP:$IP"
    echo "Cert generated at $CERT_DIR/"
fi

# Build frontend if not already built
FRONTEND_DIR="$(dirname "$0")/frontend/dist"
if [ ! -f "$FRONTEND_DIR/index.html" ]; then
    echo "Building frontend..."
    cd "$(dirname "$0")/frontend"
    npm install && npm run build
    cd ..
fi

# Start backend with HTTPS
export PORT="${PORT:-9004}"
echo "Starting server on https://0.0.0.0:$PORT"
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" \
    --ssl-keyfile="$CERT_DIR/key.pem" \
    --ssl-certfile="$CERT_DIR/cert.pem"
