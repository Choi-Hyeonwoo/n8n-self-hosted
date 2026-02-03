#!/bin/bash
# RON Learning Server Deployment Script
# VPS에서 실행: bash /home/user/n8n-self-hosted/openclaw/scripts/deploy-learning-server.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_SCRIPT="$SCRIPT_DIR/ron-learning-server.py"
TARGET_DIR="/home/openclaw/scripts"
TARGET_SCRIPT="$TARGET_DIR/ron-learning-server.py"
SERVICE_NAME="ron-learning-server"

echo "=== RON Learning Server Deployment ==="

# 1. Create directories
echo "[1/5] Creating directories..."
sudo mkdir -p /home/openclaw/scripts
sudo mkdir -p /home/openclaw/workspace/knowledge
sudo chown -R 1000:1000 /home/openclaw

# 2. Copy server script
echo "[2/5] Copying server script..."
sudo cp "$SERVER_SCRIPT" "$TARGET_SCRIPT"
sudo chmod +x "$TARGET_SCRIPT"

# 3. Kill existing server on port 8768
echo "[3/5] Stopping existing server..."
sudo fuser -k 8768/tcp 2>/dev/null || true
sleep 1

# 4. Start the server
echo "[4/5] Starting RON Learning Server..."
cd /home/openclaw
nohup python3 "$TARGET_SCRIPT" > /tmp/ron-learning-server.log 2>&1 &
echo "Server PID: $!"
sleep 2

# 5. Verify server is running
echo "[5/5] Verifying server..."
if curl -s http://localhost:8768/status | grep -q "running"; then
    echo ""
    echo "=== Deployment Successful ==="
    echo "Server is running on port 8768"
    echo ""
    echo "Test endpoints:"
    echo "  curl http://localhost:8768/status"
    echo "  curl http://localhost:8768/knowledge"
    echo ""
    echo "Logs: tail -f /tmp/ron-learning-server.log"
else
    echo "ERROR: Server failed to start"
    echo "Check logs: cat /tmp/ron-learning-server.log"
    exit 1
fi

# Also restart OpenClaw container to pick up new skills
echo ""
echo "Restarting OpenClaw container..."
docker restart openclaw-gateway 2>/dev/null && echo "OpenClaw restarted" || echo "Note: Docker command not available or container not found"

echo ""
echo "=== Done ==="
