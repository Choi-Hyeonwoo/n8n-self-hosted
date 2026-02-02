#!/bin/bash
# OpenClaw MCP Server Setup Script
# Installs and configures MCP servers on VPS (72.62.255.251)
# Run via SSH: ssh root@72.62.255.251 'bash -s' < setup-mcp.sh

set -e

echo "=== OpenClaw MCP Server Setup ==="

# 1. Install Node.js 22
echo "Installing Node.js 22..."
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs

# 2. Install Python tools
echo "Installing pip3 and uv..."
apt-get install -y python3-pip
pip3 install uv --break-system-packages 2>/dev/null || pip3 install uv

# 3. Create MCP directory structure
MCP_DIR="/opt/mcp-servers"
mkdir -p "$MCP_DIR"/{yahoo-finance,memory,firecrawl,obsidian}
mkdir -p /var/log/mcp-servers /var/run/mcp-servers

# 4. Install MCP servers (npm-based)
echo "Installing Yahoo Finance MCP..."
cd "$MCP_DIR/yahoo-finance" && npm init -y > /dev/null 2>&1 && npm install yahoo-finance-mcp

echo "Installing Memory MCP..."
cd "$MCP_DIR/memory" && npm init -y > /dev/null 2>&1 && npm install @modelcontextprotocol/server-memory

echo "Installing Firecrawl MCP..."
cd "$MCP_DIR/firecrawl" && npm init -y > /dev/null 2>&1 && npm install firecrawl-mcp

echo "Installing Obsidian MCP..."
cd "$MCP_DIR/obsidian" && npm init -y > /dev/null 2>&1 && npm install obsidian-mcp

# 5. Install MCP servers (Python/uv-based)
echo "Installing Python MCP tools..."
export PATH="/root/.local/bin:$PATH"
uv tool install mcp-proxy
uv tool install basic-memory
uv tool install mcp-server-fetch
# uv tool install telegram-mcp  # Requires TELEGRAM_API_ID and TELEGRAM_API_HASH

# 5b. Setup Obsidian vault bind mount (avoid hidden dir in path)
VAULT_SRC="/home/openclaw/.openclaw/workspace/knowledge"
VAULT_DST="/opt/mcp-servers/obsidian-vault-data"
mkdir -p "$VAULT_DST"
if ! mountpoint -q "$VAULT_DST"; then
  mount --bind "$VAULT_SRC" "$VAULT_DST"
fi
grep -q obsidian-vault-data /etc/fstab || \
  echo "$VAULT_SRC $VAULT_DST none bind 0 0" >> /etc/fstab

# Ensure minimal .obsidian config exists for obsidian-mcp
mkdir -p "$VAULT_DST/.obsidian"
[ -f "$VAULT_DST/.obsidian/app.json" ] || cat > "$VAULT_DST/.obsidian/app.json" << 'OBSEOF'
{"alwaysUpdateLinks":true,"newFileLocation":"folder","newFileFolderPath":"03-Notes"}
OBSEOF
[ -f "$VAULT_DST/.obsidian/appearance.json" ] || echo '{"baseFontSize":16}' > "$VAULT_DST/.obsidian/appearance.json"
[ -f "$VAULT_DST/.obsidian/core-plugins.json" ] || echo '["file-explorer","global-search","graph","tag-pane"]' > "$VAULT_DST/.obsidian/core-plugins.json"

# 6. Deploy mcp-manager.sh
cat > "$MCP_DIR/mcp-manager.sh" << 'MANAGER_EOF'
#!/bin/bash
export PATH="/root/.local/bin:$PATH"
LOG_DIR="/var/log/mcp-servers"
PID_DIR="/var/run/mcp-servers"
mkdir -p "$LOG_DIR" "$PID_DIR"

VAULT_PATH="/opt/mcp-servers/obsidian-vault-data"

SERVERS=(
  "yahoo-finance|3100|node /opt/mcp-servers/yahoo-finance/node_modules/yahoo-finance-mcp/build/mcp-server.js"
  "basic-memory|3101|basic-memory mcp"
  "memory|3102|node /opt/mcp-servers/memory/node_modules/@modelcontextprotocol/server-memory/dist/index.js"
  "fetch|3103|mcp-server-fetch"
  "obsidian|3104|node /opt/mcp-servers/obsidian/node_modules/obsidian-mcp/build/main.js $VAULT_PATH"
)

start_server() {
  local name=$(echo "$1" | cut -d'|' -f1)
  local port=$(echo "$1" | cut -d'|' -f2)
  local cmd=$(echo "$1" | cut -d'|' -f3-)
  if [ -f "$PID_DIR/$name.pid" ] && kill -0 $(cat "$PID_DIR/$name.pid") 2>/dev/null; then
    echo "  $name: already running (PID $(cat $PID_DIR/$name.pid))"
    return
  fi
  nohup mcp-proxy --host 0.0.0.0 --port "$port" -- $cmd > "$LOG_DIR/$name.log" 2>&1 &
  echo $! > "$PID_DIR/$name.pid"
  echo "  $name: started on port $port (PID $!)"
}

stop_server() {
  local name=$(echo "$1" | cut -d'|' -f1)
  if [ -f "$PID_DIR/$name.pid" ]; then
    local pid=$(cat "$PID_DIR/$name.pid")
    kill "$pid" 2>/dev/null && pkill -P "$pid" 2>/dev/null
    rm -f "$PID_DIR/$name.pid"
    echo "  $name: stopped"
  fi
}

status_server() {
  local name=$(echo "$1" | cut -d'|' -f1)
  local port=$(echo "$1" | cut -d'|' -f2)
  if [ -f "$PID_DIR/$name.pid" ] && kill -0 $(cat "$PID_DIR/$name.pid") 2>/dev/null; then
    echo "  $name: RUNNING (PID $(cat $PID_DIR/$name.pid), port $port)"
  else
    echo "  $name: STOPPED"
  fi
}

case "${1:-status}" in
  start)   echo "Starting MCP servers..."; for s in "${SERVERS[@]}"; do start_server "$s"; done ;;
  stop)    echo "Stopping MCP servers..."; for s in "${SERVERS[@]}"; do stop_server "$s"; done ;;
  restart) echo "Restarting..."; for s in "${SERVERS[@]}"; do stop_server "$s"; done; sleep 2; for s in "${SERVERS[@]}"; do start_server "$s"; done ;;
  status)  echo "MCP Server Status:"; for s in "${SERVERS[@]}"; do status_server "$s"; done ;;
  *)       echo "Usage: $0 {start|stop|restart|status}" ;;
esac
MANAGER_EOF
chmod +x "$MCP_DIR/mcp-manager.sh"

# 7. Create systemd service
cat > /etc/systemd/system/mcp-servers.service << 'SERVICE_EOF'
[Unit]
Description=MCP Servers (via mcp-proxy)
After=network.target

[Service]
Type=oneshot
ExecStart=/opt/mcp-servers/mcp-manager.sh start
ExecStop=/opt/mcp-servers/mcp-manager.sh stop
RemainAfterExit=yes
Environment=PATH=/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target
SERVICE_EOF

systemctl daemon-reload
systemctl enable mcp-servers

# 8. Setup nginx reverse proxy (optional, for TLS)
mkdir -p /etc/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/mcp.key -out /etc/nginx/ssl/mcp.crt \
  -subj "/CN=72.62.255.251" 2>/dev/null

cat > /etc/nginx/sites-available/mcp-proxy << 'NGINX_EOF'
server {
    listen 8443 ssl;
    server_name 72.62.255.251;
    ssl_certificate /etc/nginx/ssl/mcp.crt;
    ssl_certificate_key /etc/nginx/ssl/mcp.key;

    location /mcp/yahoo-finance/ { proxy_pass http://127.0.0.1:3100/; proxy_http_version 1.1; proxy_set_header Connection ""; proxy_buffering off; proxy_read_timeout 86400s; }
    location /mcp/basic-memory/ { proxy_pass http://127.0.0.1:3101/; proxy_http_version 1.1; proxy_set_header Connection ""; proxy_buffering off; proxy_read_timeout 86400s; }
    location /mcp/memory/ { proxy_pass http://127.0.0.1:3102/; proxy_http_version 1.1; proxy_set_header Connection ""; proxy_buffering off; proxy_read_timeout 86400s; }
    location /mcp/fetch/ { proxy_pass http://127.0.0.1:3103/; proxy_http_version 1.1; proxy_set_header Connection ""; proxy_buffering off; proxy_read_timeout 86400s; }
    location /mcp/obsidian/ { proxy_pass http://127.0.0.1:3104/; proxy_http_version 1.1; proxy_set_header Connection ""; proxy_buffering off; proxy_read_timeout 86400s; }
}
NGINX_EOF

ln -sf /etc/nginx/sites-available/mcp-proxy /etc/nginx/sites-enabled/
nginx -t && nginx -s reload

# 9. Start servers
"$MCP_DIR/mcp-manager.sh" start

echo ""
echo "=== Setup Complete ==="
echo "MCP SSE Endpoints:"
echo "  Yahoo Finance: http://72.62.255.251:3100/sse"
echo "  Basic Memory:  http://72.62.255.251:3101/sse"
echo "  Memory Graph:  http://72.62.255.251:3102/sse"
echo "  Web Fetch:     http://72.62.255.251:3103/sse"
echo "  Obsidian:      http://72.62.255.251:3104/sse"
echo ""
echo "HTTPS (via nginx): https://72.62.255.251:8443/mcp/{server-name}/sse"
echo ""
echo "Management: /opt/mcp-servers/mcp-manager.sh {start|stop|restart|status}"
echo "Systemd:    systemctl {start|stop|restart|status} mcp-servers"
echo ""
echo "NOTE: MCP Agent workflow (2u3IEwTXbPa58Tyw) requires OpenAI API credential"
echo "      Configure in n8n Cloud UI: Settings > Credentials > OpenAI API"
