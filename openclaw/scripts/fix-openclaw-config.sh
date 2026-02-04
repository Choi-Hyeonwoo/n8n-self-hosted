#!/bin/bash
# =============================================================================
# OpenClaw Configuration Fix Script
# =============================================================================
# Fixes the OPENCLAW_CONFIG_DIR path issue where /root/.openclaw was set
# instead of /home/openclaw/.openclaw
#
# Usage (on VPS):
#   curl -fsSL [this-script-url] | sudo bash
#   or
#   sudo bash /path/to/fix-openclaw-config.sh
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Configuration
OPENCLAW_DIR="/opt/openclaw"
OPENCLAW_USER="openclaw"
CORRECT_CONFIG_DIR="/home/${OPENCLAW_USER}/.openclaw"
CORRECT_WORKSPACE_DIR="/home/${OPENCLAW_USER}/.openclaw/workspace"

echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   OpenClaw Configuration Fix Script    ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

# Step 1: Find and fix .env file
log_info "Step 1/5: Locating .env file..."

ENV_FILE=""
for path in "$OPENCLAW_DIR/.env" "/home/$OPENCLAW_USER/openclaw/.env" "/opt/openclaw/.env"; do
    if [[ -f "$path" ]]; then
        ENV_FILE="$path"
        log_ok "Found .env at: $ENV_FILE"
        break
    fi
done

if [[ -z "$ENV_FILE" ]]; then
    log_error "Could not find .env file. Checking all possible locations..."
    find /home /opt /root -name ".env" -path "*openclaw*" 2>/dev/null || true
    exit 1
fi

# Step 2: Backup current .env
log_info "Step 2/5: Backing up current configuration..."
BACKUP_FILE="${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$ENV_FILE" "$BACKUP_FILE"
log_ok "Backup created: $BACKUP_FILE"

# Step 3: Show current values
log_info "Step 3/5: Current configuration:"
echo "---"
grep -E "^OPENCLAW_CONFIG_DIR|^OPENCLAW_WORKSPACE_DIR" "$ENV_FILE" || echo "(not found)"
echo "---"

# Step 4: Fix the paths
log_info "Step 4/5: Fixing configuration paths..."

# Create a temporary file with fixed content
TEMP_FILE=$(mktemp)

# Process line by line to handle the replacement properly
while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" =~ ^OPENCLAW_CONFIG_DIR= ]]; then
        echo "OPENCLAW_CONFIG_DIR=${CORRECT_CONFIG_DIR}"
    elif [[ "$line" =~ ^OPENCLAW_WORKSPACE_DIR= ]]; then
        echo "OPENCLAW_WORKSPACE_DIR=${CORRECT_WORKSPACE_DIR}"
    else
        echo "$line"
    fi
done < "$ENV_FILE" > "$TEMP_FILE"

# Replace the original file
mv "$TEMP_FILE" "$ENV_FILE"
chmod 600 "$ENV_FILE"

log_ok "Configuration updated"

# Verify the fix
log_info "Updated configuration:"
echo "---"
grep -E "^OPENCLAW_CONFIG_DIR|^OPENCLAW_WORKSPACE_DIR" "$ENV_FILE"
echo "---"

# Step 5: Ensure directories exist with correct permissions
log_info "Step 5/5: Fixing directory permissions..."

mkdir -p "$CORRECT_CONFIG_DIR/workspace"
mkdir -p "$CORRECT_CONFIG_DIR/agents"
mkdir -p "$CORRECT_CONFIG_DIR/skills"

# Set ownership to UID 1000 (matches container's node user)
chown -R 1000:1000 "$CORRECT_CONFIG_DIR"
chmod -R 755 "$CORRECT_CONFIG_DIR"

log_ok "Directories configured with correct permissions"

# Show directory structure
log_info "Directory structure:"
ls -la "$CORRECT_CONFIG_DIR/" 2>/dev/null || echo "(directory empty or not accessible)"

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}   Configuration Fix Complete!           ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "  ${YELLOW}Next Steps:${NC}"
echo -e "    1. Restart OpenClaw container:"
echo -e "       ${BLUE}cd $OPENCLAW_DIR && docker compose down && docker compose up -d${NC}"
echo ""
echo -e "    2. Run onboarding if needed:"
echo -e "       ${BLUE}cd $OPENCLAW_DIR && docker compose run --rm openclaw-cli onboard${NC}"
echo ""
echo -e "    3. Check container logs:"
echo -e "       ${BLUE}docker logs openclaw-gateway${NC}"
echo ""
echo -e "  ${YELLOW}Backup saved at:${NC} $BACKUP_FILE"
echo ""
