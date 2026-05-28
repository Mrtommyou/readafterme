#!/usr/bin/env python3
"""Run the ReadAfterMe backend server."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9004))
    ssl_cert = os.environ.get("SSL_CERT") or (
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs", "cert.pem")
        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs", "cert.pem"))
        else None
    )
    ssl_key = os.environ.get("SSL_KEY") or (
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs", "key.pem")
        if ssl_cert
        else None
    )

    proto = "https" if ssl_cert else "http"
    print(f"Starting ReadAfterMe backend on {proto}://0.0.0.0:{port}")

    ssl_kwargs = {}
    if ssl_cert and ssl_key:
        ssl_kwargs["ssl_certfile"] = ssl_cert
        ssl_kwargs["ssl_keyfile"] = ssl_key

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
        **ssl_kwargs,
    )
