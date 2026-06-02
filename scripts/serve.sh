#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

GUNICORN_PID=""

cleanup() {
    echo ""
    echo "Stopping servers..."
    [ -n "$GUNICORN_PID" ] && kill "$GUNICORN_PID" 2>/dev/null && echo "  ✓ gunicorn stopped"
    exit 0
}
trap cleanup INT TERM

# ── Guard: must build first ──────────────────────────────────────────────────
if [ ! -f "$ROOT/frontend/dist/index.html" ]; then
    echo "ERROR: frontend/dist/index.html not found."
    echo "       Run  make build  first."
    exit 1
fi

# ── Start gunicorn ────────────────────────────────────────────────────────────
echo ""
echo "▶ Starting gunicorn on http://127.0.0.1:8000 ..."
gunicorn backend.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 2 \
    --log-level warning \
    --access-logfile - \
    &
GUNICORN_PID=$!

# Give it a moment then verify it started
sleep 1
if ! kill -0 "$GUNICORN_PID" 2>/dev/null; then
    echo "ERROR: gunicorn failed to start. Check for port conflicts with: lsof -i :8000"
    exit 1
fi
echo "  ✓ gunicorn running (PID $GUNICORN_PID)"

# ── Quick smoke test ─────────────────────────────────────────────────────────
sleep 0.5
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
    echo "  ✓ Local smoke test passed (HTTP $HTTP_STATUS)"
else
    echo "  ⚠ Local smoke test returned HTTP $HTTP_STATUS (may still be starting)"
fi

# ── Start localtunnel ─────────────────────────────────────────────────────────
echo ""
echo "▶ Starting localtunnel..."
echo ""
echo "  ┌─────────────────────────────────────────┐"
echo "  │  App URL: https://biointel.loca.lt       │"
echo "  │  API URL: https://biointel.loca.lt/api/  │"
echo "  └─────────────────────────────────────────┘"
echo ""
echo "  Note: First-time visitors must click 'I agree' on the loca.lt landing page."
echo "  Press Ctrl+C to stop all servers."
echo ""

lt --port 8000 --subdomain biointel
