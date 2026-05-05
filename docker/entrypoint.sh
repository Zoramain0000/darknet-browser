#!/bin/bash
# ─── Robin AI - Docker Entrypoint ────────────────────────────────────
# Starts Tor and then launches the Streamlit application

set -e

echo "╔══════════════════════════════════════════════════════╗"
echo "║          🦉 Robin AI - Dark Web OSINT                ║"
echo "║          Starting container...                       ║"
echo "╚══════════════════════════════════════════════════════╝"

# ─── Start Tor ────────────────────────────────────────────────────────
echo "[*] Starting Tor proxy..."
tor -f /etc/tor/torrc &
TOR_PID=$!
echo "[*] Tor PID: $TOR_PID"

# Wait for Tor to be ready
echo "[*] Waiting for Tor to establish connection..."
for i in $(seq 1 30); do
    if timeout 3 bash -c "echo -e 'AUTHENTICATE\r\nGETINFO circuit-status\r\nQUIT\r\n' | nc 127.0.0.1 9051 2>/dev/null | grep -q BUILT"; then
        echo "[✓] Tor is ready (circuit established)"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "[!] Tor may not have fully initialized. Continuing..."
    fi
    sleep 2
done

# Get Tor exit IP
TOR_IP=$(timeout 5 curl --socks5-hostname 127.0.0.1:9050 -s https://check.torproject.org/api/ip 2>/dev/null | grep -o '"IP":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
echo "[*] Tor exit node IP: $TOR_IP"

# ─── Check Environment ────────────────────────────────────────────────
if [ -z "$MISTRAL_API_KEY" ]; then
    echo "[!] WARNING: MISTRAL_API_KEY is not set!"
    echo "[!] Set it in docker-compose.yml or .env file"
    echo "[!] Get a key at: https://console.mistral.ai"
else
    KEY_LEN=${#MISTRAL_API_KEY}
    echo "[✓] Mistral API key configured (${KEY_LEN} chars)"
fi

echo "[*] Mistral Model: ${MISTRAL_MODEL:-mistral-large-latest}"
echo "[*] Max Threads: ${MAX_THREADS:-16}"
echo "[*] Request Timeout: ${REQUEST_TIMEOUT:-30}s"

# ─── Start Streamlit ──────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  🚀 Launching Streamlit application...               ║"
echo "║  📡 UI available at http://0.0.0.0:8501              ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

exec streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=true \
    --browser.gatherUsageStats=false

# Cleanup on exit
kill $TOR_PID 2>/dev/null || true