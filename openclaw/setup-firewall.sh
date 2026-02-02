#!/usr/bin/env bash
# =============================================================================
# OpenClaw Firewall Configuration Script for Hostinger VPS
# =============================================================================
# Standalone firewall setup script. The main install.sh already includes this,
# but you can run this separately if needed.
#
# Usage:
#   chmod +x setup-firewall.sh
#   sudo ./setup-firewall.sh
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }

if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}[ERROR]${NC} This script must be run as root (use sudo)"
    exit 1
fi

OPENCLAW_GATEWAY_PORT=${OPENCLAW_GATEWAY_PORT:-18789}
OPENCLAW_BRIDGE_PORT=${OPENCLAW_BRIDGE_PORT:-18790}

log_info "Configuring UFW firewall for OpenClaw..."

# Install UFW if not present
if ! command -v ufw &>/dev/null; then
    apt-get install -y -qq ufw
fi

# Reset rules if requested
if [[ "${1:-}" == "--reset" ]]; then
    log_warn "Resetting all UFW rules..."
    ufw --force reset
fi

# Allow SSH first (prevent lockout)
ufw allow 22/tcp comment "SSH"
log_ok "SSH (port 22) allowed"

# Allow OpenClaw ports
ufw allow ${OPENCLAW_GATEWAY_PORT}/tcp comment "OpenClaw Gateway"
log_ok "OpenClaw Gateway (port ${OPENCLAW_GATEWAY_PORT}) allowed"

ufw allow ${OPENCLAW_BRIDGE_PORT}/tcp comment "OpenClaw Bridge"
log_ok "OpenClaw Bridge (port ${OPENCLAW_BRIDGE_PORT}) allowed"

# Allow HTTP/HTTPS (for reverse proxy like Nginx/Caddy)
ufw allow 80/tcp comment "HTTP"
ufw allow 443/tcp comment "HTTPS"
log_ok "HTTP (80) and HTTPS (443) allowed"

# Enable firewall
ufw --force enable
log_ok "UFW firewall enabled"

# Show status
echo ""
log_info "Current firewall rules:"
ufw status verbose

echo ""
log_ok "Firewall configuration complete."
echo -e "${YELLOW}Tip: For production, consider restricting port ${OPENCLAW_GATEWAY_PORT} to specific IPs:${NC}"
echo -e "  ufw delete allow ${OPENCLAW_GATEWAY_PORT}/tcp"
echo -e "  ufw allow from YOUR_IP to any port ${OPENCLAW_GATEWAY_PORT} proto tcp"
