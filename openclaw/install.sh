#!/usr/bin/env bash
# =============================================================================
# OpenClaw Installation Script for Hostinger VPS (Ubuntu 22.04/24.04)
# =============================================================================
# Usage:
#   chmod +x install.sh
#   sudo ./install.sh
#
# This script will:
#   1. Update system packages
#   2. Install Docker & Docker Compose (if not present)
#   3. Clone OpenClaw repository
#   4. Build Docker image
#   5. Run onboarding wizard
#   6. Start OpenClaw gateway
#   7. Configure firewall (UFW)
#   8. Set up systemd service for auto-restart
# =============================================================================

set -euo pipefail

# --- Configuration ---
OPENCLAW_REPO="https://github.com/openclaw/openclaw.git"
OPENCLAW_DIR="/opt/openclaw"
OPENCLAW_USER="openclaw"
OPENCLAW_GATEWAY_PORT=18789
OPENCLAW_BRIDGE_PORT=18790

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Helper Functions ---
log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_system() {
    log_info "Checking system requirements..."

    # Check OS
    if [[ ! -f /etc/os-release ]]; then
        log_error "Cannot detect OS. This script supports Ubuntu 22.04/24.04."
        exit 1
    fi

    source /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        log_warn "Detected OS: $ID. This script is designed for Ubuntu. Proceeding anyway..."
    fi

    # Check RAM (minimum 4GB recommended)
    TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
    if [[ $TOTAL_RAM_GB -lt 4 ]]; then
        log_warn "System has ${TOTAL_RAM_GB}GB RAM. 4GB+ is recommended for OpenClaw."
        read -p "Continue anyway? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_ok "RAM: ${TOTAL_RAM_GB}GB (4GB+ recommended)"
    fi

    # Check disk space (minimum 10GB free)
    FREE_DISK_GB=$(df / --output=avail -BG | tail -1 | tr -d 'G ')
    if [[ $FREE_DISK_GB -lt 10 ]]; then
        log_warn "Only ${FREE_DISK_GB}GB free disk space. 10GB+ recommended."
    else
        log_ok "Disk: ${FREE_DISK_GB}GB free"
    fi
}

# --- Step 1: Update System ---
update_system() {
    log_info "Step 1/7: Updating system packages..."
    apt-get update -qq
    apt-get upgrade -y -qq
    apt-get install -y -qq \
        curl \
        wget \
        git \
        ca-certificates \
        gnupg \
        lsb-release \
        ufw \
        openssl
    log_ok "System packages updated"
}

# --- Step 2: Install Docker ---
install_docker() {
    log_info "Step 2/7: Installing Docker..."

    if command -v docker &>/dev/null; then
        DOCKER_VERSION=$(docker --version)
        log_ok "Docker already installed: $DOCKER_VERSION"
    else
        # Add Docker's official GPG key
        install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
            gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        chmod a+r /etc/apt/keyrings/docker.gpg

        # Add Docker repository
        echo \
            "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
            https://download.docker.com/linux/ubuntu \
            $(lsb_release -cs) stable" | \
            tee /etc/apt/sources.list.d/docker.list > /dev/null

        apt-get update -qq
        apt-get install -y -qq \
            docker-ce \
            docker-ce-cli \
            containerd.io \
            docker-buildx-plugin \
            docker-compose-plugin

        # Enable and start Docker
        systemctl enable docker
        systemctl start docker

        log_ok "Docker installed successfully"
    fi

    # Verify Docker Compose
    if docker compose version &>/dev/null; then
        log_ok "Docker Compose: $(docker compose version --short)"
    else
        log_error "Docker Compose not available. Please install Docker Compose v2."
        exit 1
    fi
}

# --- Step 3: Create OpenClaw User ---
create_user() {
    log_info "Step 3/7: Creating OpenClaw system user..."

    if id "$OPENCLAW_USER" &>/dev/null; then
        log_ok "User '$OPENCLAW_USER' already exists"
    else
        useradd -r -m -s /bin/bash -d /home/$OPENCLAW_USER $OPENCLAW_USER
        usermod -aG docker $OPENCLAW_USER
        log_ok "User '$OPENCLAW_USER' created and added to docker group"
    fi
}

# --- Step 4: Clone OpenClaw ---
clone_openclaw() {
    log_info "Step 4/7: Cloning OpenClaw repository..."

    if [[ -d "$OPENCLAW_DIR" ]]; then
        log_warn "Directory $OPENCLAW_DIR already exists."
        read -p "Remove and re-clone? (y/N): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$OPENCLAW_DIR"
        else
            log_info "Pulling latest changes instead..."
            cd "$OPENCLAW_DIR"
            git pull origin main
            cd -
            return
        fi
    fi

    git clone "$OPENCLAW_REPO" "$OPENCLAW_DIR"
    chown -R $OPENCLAW_USER:$OPENCLAW_USER "$OPENCLAW_DIR"
    log_ok "OpenClaw cloned to $OPENCLAW_DIR"
}

# --- Step 5: Configure Environment ---
configure_env() {
    log_info "Step 5/7: Configuring environment..."

    # Create config directories
    mkdir -p /home/$OPENCLAW_USER/.openclaw/workspace
    chown -R $OPENCLAW_USER:$OPENCLAW_USER /home/$OPENCLAW_USER/.openclaw

    # Generate gateway token
    GATEWAY_TOKEN=$(openssl rand -hex 32)

    # Create .env file
    ENV_FILE="$OPENCLAW_DIR/.env"

    if [[ -f "$ENV_FILE" ]]; then
        log_warn ".env file already exists. Backing up to .env.backup"
        cp "$ENV_FILE" "${ENV_FILE}.backup"
    fi

    # Get openclaw user UID/GID
    OPENCLAW_UID=$(id -u $OPENCLAW_USER)
    OPENCLAW_GID=$(id -g $OPENCLAW_USER)

    cat > "$ENV_FILE" <<EOF
# OpenClaw Environment Configuration
# Generated on $(date -u +"%Y-%m-%d %H:%M:%S UTC")

OPENCLAW_GATEWAY_TOKEN=${GATEWAY_TOKEN}
OPENCLAW_IMAGE=openclaw:local
OPENCLAW_GATEWAY_PORT=${OPENCLAW_GATEWAY_PORT}
OPENCLAW_BRIDGE_PORT=${OPENCLAW_BRIDGE_PORT}

# Host paths for volume mounts (used by repo's docker-compose.yml)
OPENCLAW_CONFIG_DIR=/home/${OPENCLAW_USER}/.openclaw
OPENCLAW_WORKSPACE_DIR=/home/${OPENCLAW_USER}/.openclaw/workspace

# Container user mapping
OPENCLAW_UID=${OPENCLAW_UID}
OPENCLAW_GID=${OPENCLAW_GID}

# Session keys (optional, leave blank if not used)
CLAUDE_AI_SESSION_KEY=
CLAUDE_WEB_SESSION_KEY=
CLAUDE_WEB_COOKIE=
EOF

    chown $OPENCLAW_USER:$OPENCLAW_USER "$ENV_FILE"
    chmod 600 "$ENV_FILE"

    log_ok "Environment configured"
    echo ""
    echo -e "${YELLOW}=========================================${NC}"
    echo -e "${YELLOW}  IMPORTANT: Save your Gateway Token!   ${NC}"
    echo -e "${YELLOW}=========================================${NC}"
    echo -e "  Token: ${GREEN}${GATEWAY_TOKEN}${NC}"
    echo -e "${YELLOW}=========================================${NC}"
    echo ""
    echo -e "${BLUE}You will need this token to access the OpenClaw dashboard.${NC}"
    echo ""

    # Ask for API keys
    read -p "Enter your Anthropic API Key (or press Enter to skip): " -r ANTHROPIC_KEY
    if [[ -n "$ANTHROPIC_KEY" ]]; then
        echo "ANTHROPIC_API_KEY=${ANTHROPIC_KEY}" >> "$ENV_FILE"
        log_ok "Anthropic API key configured"
    fi

    read -p "Enter your OpenAI API Key (or press Enter to skip): " -r OPENAI_KEY
    if [[ -n "$OPENAI_KEY" ]]; then
        echo "OPENAI_API_KEY=${OPENAI_KEY}" >> "$ENV_FILE"
        log_ok "OpenAI API key configured"
    fi

    if [[ -z "$ANTHROPIC_KEY" && -z "$OPENAI_KEY" ]]; then
        log_warn "No API key provided. You can add one later in $ENV_FILE"
    fi
}

# --- Step 6: Build and Start OpenClaw ---
build_and_start() {
    log_info "Step 6/7: Building and starting OpenClaw..."

    cd "$OPENCLAW_DIR"

    # Copy our docker-compose if the repo doesn't have one
    if [[ ! -f "docker-compose.yml" ]]; then
        log_warn "No docker-compose.yml found in repo. This is unexpected."
        log_info "Using bundled docker-compose.yml..."
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        cp "$SCRIPT_DIR/docker-compose.yml" "$OPENCLAW_DIR/docker-compose.yml"
    fi

    # Build Docker image
    log_info "Building Docker image (this may take several minutes)..."
    docker build -t openclaw:local -f Dockerfile .
    log_ok "Docker image built"

    # Run onboarding wizard
    log_info "Starting onboarding wizard..."
    echo -e "${YELLOW}Follow the prompts to configure your AI provider and messaging channels.${NC}"
    echo ""
    docker compose run --rm openclaw-cli onboard

    # Start gateway
    log_info "Starting OpenClaw gateway..."
    docker compose up -d openclaw-gateway
    log_ok "OpenClaw gateway started"
}

# --- Step 7: Configure Firewall ---
configure_firewall() {
    log_info "Step 7/7: Configuring firewall..."

    # Enable UFW if not already enabled
    if ! ufw status | grep -q "Status: active"; then
        # Allow SSH first to prevent lockout
        ufw allow 22/tcp comment "SSH"
        ufw --force enable
        log_ok "UFW firewall enabled"
    fi

    # Allow OpenClaw ports
    ufw allow ${OPENCLAW_GATEWAY_PORT}/tcp comment "OpenClaw Gateway"
    ufw allow ${OPENCLAW_BRIDGE_PORT}/tcp comment "OpenClaw Bridge"

    # Allow HTTP/HTTPS for reverse proxy (optional)
    ufw allow 80/tcp comment "HTTP"
    ufw allow 443/tcp comment "HTTPS"

    ufw reload
    log_ok "Firewall configured"
}

# --- Step 8: Create Systemd Service ---
create_systemd_service() {
    log_info "Creating systemd service for auto-start..."

    cat > /etc/systemd/system/openclaw.service <<EOF
[Unit]
Description=OpenClaw AI Agent Gateway
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=${OPENCLAW_USER}
WorkingDirectory=${OPENCLAW_DIR}
ExecStart=/usr/bin/docker compose up -d openclaw-gateway
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable openclaw.service
    log_ok "Systemd service created and enabled"
}

# --- Main ---
main() {
    echo ""
    echo -e "${BLUE}=========================================${NC}"
    echo -e "${BLUE}   OpenClaw Installer for Hostinger VPS  ${NC}"
    echo -e "${BLUE}=========================================${NC}"
    echo ""

    check_root
    check_system

    echo ""
    log_info "Starting installation..."
    echo ""

    update_system
    install_docker
    create_user
    clone_openclaw
    configure_env
    build_and_start
    configure_firewall
    create_systemd_service

    # Get server IP
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

    echo ""
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}   OpenClaw Installation Complete!       ${NC}"
    echo -e "${GREEN}=========================================${NC}"
    echo ""
    echo -e "  Dashboard:  ${BLUE}http://${SERVER_IP}:${OPENCLAW_GATEWAY_PORT}/${NC}"
    echo -e "  Config Dir: ${BLUE}/home/${OPENCLAW_USER}/.openclaw/${NC}"
    echo -e "  Env File:   ${BLUE}${OPENCLAW_DIR}/.env${NC}"
    echo -e "  Logs:       ${BLUE}docker compose -f ${OPENCLAW_DIR}/docker-compose.yml logs -f${NC}"
    echo ""
    echo -e "  ${YELLOW}Useful Commands:${NC}"
    echo -e "    View logs:     docker compose -f ${OPENCLAW_DIR}/docker-compose.yml logs -f"
    echo -e "    Restart:       sudo systemctl restart openclaw"
    echo -e "    Stop:          sudo systemctl stop openclaw"
    echo -e "    Status:        sudo systemctl status openclaw"
    echo -e "    Update:        cd ${OPENCLAW_DIR} && git pull && docker build -t openclaw:local . && docker compose up -d"
    echo ""
    echo -e "  ${YELLOW}Next Steps:${NC}"
    echo -e "    1. Open http://${SERVER_IP}:${OPENCLAW_GATEWAY_PORT}/ in your browser"
    echo -e "    2. Enter your Gateway Token in the Settings page"
    echo -e "    3. Connect your messaging channels (WhatsApp, Telegram, Discord, etc.)"
    echo -e "    4. Start chatting with your AI assistant!"
    echo ""
}

main "$@"
