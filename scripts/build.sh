#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo ""
echo "╔══════════════════════════════╗"
echo "║   BioIntel Production Build  ║"
echo "╚══════════════════════════════╝"
echo ""

# ── Step 1: Python deps ──────────────────────────────────────────────────────
echo "▶ [1/4] Installing Python dependencies..."
pip install -r requirements.txt -q
echo "  ✓ Done"

# ── Step 2: Frontend build ───────────────────────────────────────────────────
echo "▶ [2/4] Building Vue frontend..."
cd "$ROOT/frontend"
npm install --silent
npm run build
echo "  ✓ Done  (output: frontend/dist/)"

# ── Step 3: Collect Django static files (admin CSS etc.) ─────────────────────
echo "▶ [3/4] Collecting Django static files..."
cd "$ROOT"
python manage.py collectstatic --noinput -v 0
echo "  ✓ Done  (output: staticfiles/)"

# ── Step 4: Migrate ──────────────────────────────────────────────────────────
echo "▶ [4/4] Running database migrations..."
python manage.py migrate --run-syncdb -v 0
echo "  ✓ Done"

echo ""
echo "✅ Build complete. Run  make serve  to start."
echo ""
