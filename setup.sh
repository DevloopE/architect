#!/usr/bin/env bash
# ArchitectBot — one-command setup
# Usage: bash setup.sh

set -e
echo "=== ArchitectBot Setup ==="

# 1. Initialize editor submodule if needed
if [ ! -f editor/package.json ]; then
  echo "[1/4] Cloning editor submodule..."
  git submodule update --init --recursive
else
  echo "[1/4] Editor submodule already present"
fi

# 2. Install editor dependencies
echo "[2/4] Installing editor dependencies (bun)..."
cd editor
bun install
cd ..

# 3. Install Python dependencies
echo "[3/4] Installing Python dependencies..."
pip install -e ".[dev]" --quiet

# 4. Verify
echo "[4/4] Verifying..."
python -c "from architect.client import EditorClient; print('  Python OK')"
echo "  Editor OK"

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Usage:"
echo "  In Claude Code, run:  /build a modern villa with pool"
echo ""
echo "Or manually:"
echo "  1. bash start.sh        (starts editor + relay + browser)"
echo "  2. python build_one_floor.py  (builds the last generated design)"
