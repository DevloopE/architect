#!/usr/bin/env bash
# Start the editor + relay + open browser
# Usage: bash start.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Kill any existing processes
echo "Cleaning up old processes..."
for port in 3002 3100; do
  pid=$(lsof -ti:$port 2>/dev/null || netstat -ano 2>/dev/null | grep ":$port " | grep LISTENING | awk '{print $5}' | head -1)
  if [ -n "$pid" ] && [ "$pid" != "0" ]; then
    kill -9 "$pid" 2>/dev/null || taskkill //PID "$pid" //F 2>/dev/null || true
  fi
done
sleep 1

# Start relay
echo "Starting WebSocket relay on ws://localhost:3100..."
cd "$SCRIPT_DIR/editor/apps/editor"
nohup node bridge-relay.mjs > /dev/null 2>&1 &

# Start editor
echo "Starting editor on http://localhost:3002..."
cd "$SCRIPT_DIR/editor"
nohup bun dev > /dev/null 2>&1 &

echo "Waiting for editor to start..."
sleep 20

# Open browser
echo "Opening browser..."
if command -v open &>/dev/null; then
  open http://localhost:3002
elif command -v xdg-open &>/dev/null; then
  xdg-open http://localhost:3002
elif command -v start &>/dev/null; then
  start http://localhost:3002
fi

echo "Waiting for browser to connect..."
sleep 10

echo ""
echo "Ready! Editor: http://localhost:3002 | Relay: ws://localhost:3100"
