#!/bin/sh
set -eu

CF_BIN=/subxtract/data/cloudflared
URL_FILE=/subxtract/data/cloudflare_tunnel_url.txt
CF_LOG=/tmp/cf_tunnel.log
WEB_LOG=/tmp/web.log
ARIA2_LOG=/tmp/aria2.log
BOT_LOG=/tmp/bot.log

if [ ! -x "$CF_BIN" ]; then
    wget -qO "$CF_BIN" \
        https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
    chmod +x "$CF_BIN"
fi

aria2c --conf-path=./config/aria2.conf --enable-color=false > "$ARIA2_LOG" 2>&1 &
ARIA2_PID=$!

python3.10 -m uvicorn web.server:app \
    --host 127.0.0.1 \
    --port 8765 > "$WEB_LOG" 2>&1 &
WEB_PID=$!

WEB_READY=""
for i in $(seq 1 30); do
    if wget -qO /dev/null http://127.0.0.1:8765/app/files; then
        WEB_READY=1
        break
    fi
    sleep 1
done

if [ -z "$WEB_READY" ]; then
    echo "Web server failed to start:"
    cat "$WEB_LOG"
    kill "$ARIA2_PID" "$WEB_PID" 2>/dev/null || true
    exit 1
fi

"$CF_BIN" tunnel \
    --url http://127.0.0.1:8765 \
    --no-autoupdate > "$CF_LOG" 2>&1 &
CF_PID=$!

TUNNEL_URL=""
for i in $(seq 1 30); do
    TUNNEL_URL=$(grep -oE "https://[A-Za-z0-9-]+\.trycloudflare\.com" "$CF_LOG" | head -n 1 || true)
    if [ -n "$TUNNEL_URL" ]; then
        break
    fi
    sleep 1
done

if [ -z "$TUNNEL_URL" ]; then
    echo "Cloudflare tunnel failed to start:"
    cat "$CF_LOG"
    kill "$ARIA2_PID" "$WEB_PID" "$CF_PID" 2>/dev/null || true
    exit 1
fi

printf "%s\n" "$TUNNEL_URL" > "$URL_FILE"
echo "Cloudflare tunnel URL: $TUNNEL_URL"

python3.10 -u ./bot.py 2>&1 | tee -a "$BOT_LOG"