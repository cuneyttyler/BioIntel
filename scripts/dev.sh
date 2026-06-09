#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DJANGO_PID=""

cleanup() {
    echo ""
    echo "Stopping dev servers..."
    [ -n "$DJANGO_PID" ] && kill "$DJANGO_PID" 2>/dev/null && echo "  ✓ Django stopped"
}
trap cleanup EXIT

python manage.py runserver &
DJANGO_PID=$!
echo "  ✓ Django dev server on :8000 (PID $DJANGO_PID)"
echo "  Starting Vite dev server on :5173..."
echo "  Press Ctrl+C to stop all servers."
echo ""

cd frontend && npm run dev
