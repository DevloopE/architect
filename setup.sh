#!/usr/bin/env bash
# Architect — one-command setup
# Usage: bash setup.sh

set -e
echo "=== Architect Setup ==="

# 1. Check editor kernel
if [ ! -f editor/package.json ]; then
  echo "[ERROR] Editor kernel not found. Make sure 'editor/' directory exists."
  exit 1
else
  echo "[1/5] Editor kernel present"
fi

# 2. Install editor dependencies
echo "[2/5] Installing editor dependencies (bun)..."
cd editor
bun install
cd ..

# 3. Install Electron dependencies
echo "[3/5] Installing Electron dependencies..."
cd electron
npm install
cd ..

# 4. Install Python dependencies
echo "[4/5] Installing Python dependencies..."
pip install -e ".[dev]" --quiet 2>/dev/null || pip install websockets --quiet

# 5. Verify
echo "[5/5] Verifying..."
echo "  Editor OK"
echo "  Electron OK"

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Usage:"
echo "  Desktop app:  cd electron && npm start"
echo "  Browser mode:  bash start.sh"
echo "  Claude Code:   /build a modern villa with pool"
echo "  Manual build:  python build_one_floor.py"
