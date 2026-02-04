#!/bin/bash
# =============================================================================
# OpenClaw Diagnostic Script
# =============================================================================
# Checks OpenClaw configuration and identifies common issues
#
# Usage (on VPS):
#   sudo bash /path/to/diagnose-openclaw.sh
# =============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   OpenClaw Diagnostic Report           ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# 1. Check Docker
echo -e "${YELLOW}[1] Docker Status${NC}"
if command -v docker &>/dev/null; then
    echo -e "  ${GREEN}OK${NC} Docker installed: $(docker --version)"

    # Check if Docker is running
    if docker info &>/dev/null; then
        echo -e "  ${GREEN}OK${NC} Docker daemon is running"
    else
        echo -e "  ${RED}ERROR${NC} Docker daemon is not running"
    fi
else
    echo -e "  ${RED}ERROR${NC} Docker is not installed"
fi

# 2. Check OpenClaw container
echo ""
echo -e "${YELLOW}[2] OpenClaw Container${NC}"
if docker ps -a --format '{{.Names}}' | grep -q "openclaw-gateway"; then
    CONTAINER_STATUS=$(docker ps -a --filter "name=openclaw-gateway" --format '{{.Status}}')
    if echo "$CONTAINER_STATUS" | grep -q "Up"; then
        echo -e "  ${GREEN}OK${NC} openclaw-gateway is running"
        echo "  Status: $CONTAINER_STATUS"
    else
        echo -e "  ${YELLOW}WARN${NC} openclaw-gateway exists but not running"
        echo "  Status: $CONTAINER_STATUS"
    fi
else
    echo -e "  ${RED}ERROR${NC} openclaw-gateway container not found"
fi

# 3. Check .env file
echo ""
echo -e "${YELLOW}[3] Environment Configuration${NC}"
ENV_PATHS=(
    "/opt/openclaw/.env"
    "/home/openclaw/openclaw/.env"
)

for env_path in "${ENV_PATHS[@]}"; do
    if [[ -f "$env_path" ]]; then
        echo -e "  Found .env at: ${BLUE}$env_path${NC}"

        # Check OPENCLAW_CONFIG_DIR
        CONFIG_DIR=$(grep "^OPENCLAW_CONFIG_DIR=" "$env_path" | cut -d'=' -f2)
        if [[ "$CONFIG_DIR" == "/home/openclaw/.openclaw" ]]; then
            echo -e "  ${GREEN}OK${NC} OPENCLAW_CONFIG_DIR=$CONFIG_DIR"
        elif [[ "$CONFIG_DIR" == "/root/.openclaw" ]]; then
            echo -e "  ${RED}ERROR${NC} OPENCLAW_CONFIG_DIR=$CONFIG_DIR"
            echo -e "       Should be: /home/openclaw/.openclaw"
        else
            echo -e "  ${YELLOW}WARN${NC} OPENCLAW_CONFIG_DIR=$CONFIG_DIR"
        fi

        # Check OPENCLAW_WORKSPACE_DIR
        WORKSPACE_DIR=$(grep "^OPENCLAW_WORKSPACE_DIR=" "$env_path" | cut -d'=' -f2)
        echo "  OPENCLAW_WORKSPACE_DIR=$WORKSPACE_DIR"

        # Check API keys (just show if set, not the actual values)
        if grep -q "^ANTHROPIC_API_KEY=." "$env_path" 2>/dev/null; then
            echo -e "  ${GREEN}OK${NC} ANTHROPIC_API_KEY is set"
        else
            echo "  ANTHROPIC_API_KEY not set"
        fi

        if grep -q "^OPENAI_API_KEY=." "$env_path" 2>/dev/null; then
            echo -e "  ${GREEN}OK${NC} OPENAI_API_KEY is set"
        else
            echo "  OPENAI_API_KEY not set"
        fi

        if grep -q "^GOOGLE_API_KEY=." "$env_path" 2>/dev/null; then
            echo -e "  ${GREEN}OK${NC} GOOGLE_API_KEY is set"
        else
            echo "  GOOGLE_API_KEY not set"
        fi

        if grep -q "^OPENROUTER_API_KEY=." "$env_path" 2>/dev/null; then
            echo -e "  ${GREEN}OK${NC} OPENROUTER_API_KEY is set"
        else
            echo "  OPENROUTER_API_KEY not set"
        fi

        break
    fi
done

# 4. Check directories
echo ""
echo -e "${YELLOW}[4] Directory Structure${NC}"
for dir in "/home/openclaw/.openclaw" "/root/.openclaw"; do
    if [[ -d "$dir" ]]; then
        echo -e "  ${BLUE}$dir${NC}"
        OWNER=$(stat -c '%U:%G' "$dir" 2>/dev/null || echo "unknown")
        PERMS=$(stat -c '%a' "$dir" 2>/dev/null || echo "unknown")
        echo "    Owner: $OWNER, Permissions: $PERMS"

        # List subdirectories
        for subdir in workspace agents skills cron; do
            if [[ -d "$dir/$subdir" ]]; then
                echo -e "    ${GREEN}OK${NC} $subdir/"
            else
                echo "    - $subdir/ (missing)"
            fi
        done
    fi
done

# 5. Check container mounts
echo ""
echo -e "${YELLOW}[5] Container Volume Mounts${NC}"
if docker inspect openclaw-gateway &>/dev/null; then
    echo "  Mounted volumes:"
    docker inspect openclaw-gateway --format '{{range .Mounts}}  {{.Source}} -> {{.Destination}}{{println}}{{end}}' 2>/dev/null
else
    echo "  (Container not found or not running)"
fi

# 6. Check recent container logs for errors
echo ""
echo -e "${YELLOW}[6] Recent Container Errors${NC}"
if docker logs openclaw-gateway --tail 20 2>&1 | grep -iE "error|failed|permission denied|eacces" | tail -5; then
    :
else
    echo -e "  ${GREEN}OK${NC} No recent errors found"
fi

# 7. Summary
echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   Diagnostic Summary                   ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Check for critical issues
ISSUES=0

if [[ "$CONFIG_DIR" == "/root/.openclaw" ]]; then
    echo -e "  ${RED}CRITICAL${NC}: OPENCLAW_CONFIG_DIR points to /root/.openclaw"
    echo "           Run fix-openclaw-config.sh to fix this"
    ISSUES=$((ISSUES + 1))
fi

if [[ ! -d "/home/openclaw/.openclaw" ]]; then
    echo -e "  ${RED}CRITICAL${NC}: /home/openclaw/.openclaw directory missing"
    ISSUES=$((ISSUES + 1))
fi

if [[ $ISSUES -eq 0 ]]; then
    echo -e "  ${GREEN}No critical issues found${NC}"
fi

echo ""
