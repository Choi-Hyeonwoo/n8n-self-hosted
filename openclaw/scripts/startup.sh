#!/bin/bash
#
# OpenClaw/RON 서비스 시작 스크립트
# VPS 부팅 시 또는 수동으로 실행
#
# 사용법:
#   ./startup.sh          # 모든 서비스 시작
#   ./startup.sh status   # 상태 확인
#   ./startup.sh stop     # 모든 서비스 중지
#

set -e

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

start_services() {
    log "Starting OpenClaw services..."

    # 1. ETF Scheduler
    if ! pgrep -f "scheduler.py" > /dev/null; then
        log "Starting ETF Scheduler..."
        cd /home/user/n8n-self-hosted/openclaw-skills/etf-tracker/scripts
        source /etc/etf-tracker.env 2>/dev/null || true
        export ANTHROPIC_API_KEY
        nohup python3 scheduler.py > /var/log/etf_scheduler.log 2>&1 &
        log "ETF Scheduler started (PID: $!)"
    else
        log "ETF Scheduler already running"
    fi

    # 2. RON Tools API
    if ! pgrep -f "ron_tools_api.py" > /dev/null; then
        log "Starting RON Tools API..."
        nohup python3 /home/user/n8n-self-hosted/openclaw/scripts/ron_tools_api.py > /var/log/ron_tools_api.log 2>&1 &
        log "RON Tools API started on port 8766 (PID: $!)"
    else
        log "RON Tools API already running"
    fi

    # 3. MCP Servers (optional - currently has network issues)
    # Uncomment if MCP servers are needed
    # log "Starting MCP servers..."
    # /opt/mcp-servers/mcp-manager.sh start

    sleep 2
    show_status
}

stop_services() {
    log "Stopping OpenClaw services..."

    pkill -f "scheduler.py" 2>/dev/null && log "ETF Scheduler stopped" || log "ETF Scheduler not running"
    pkill -f "ron_tools_api.py" 2>/dev/null && log "RON Tools API stopped" || log "RON Tools API not running"
    pkill -f "mcp-proxy" 2>/dev/null && log "MCP servers stopped" || log "MCP servers not running"

    log "All services stopped"
}

show_status() {
    echo ""
    echo "═══════════════════════════════════════"
    echo "  OpenClaw Service Status"
    echo "═══════════════════════════════════════"

    # ETF Scheduler
    if pgrep -f "scheduler.py" > /dev/null; then
        PID=$(pgrep -f "scheduler.py" | head -1)
        echo "  ETF Scheduler:    ✅ Running (PID: $PID)"
    else
        echo "  ETF Scheduler:    ❌ Not running"
    fi

    # RON Tools API
    if pgrep -f "ron_tools_api.py" > /dev/null; then
        PID=$(pgrep -f "ron_tools_api.py" | head -1)
        echo "  RON Tools API:    ✅ Running (PID: $PID, port 8766)"
    else
        echo "  RON Tools API:    ❌ Not running"
    fi

    # MCP Servers
    MCP_COUNT=$(pgrep -f "mcp-proxy" 2>/dev/null | wc -l)
    if [ "$MCP_COUNT" -gt 0 ]; then
        echo "  MCP Servers:      ✅ Running ($MCP_COUNT servers)"
    else
        echo "  MCP Servers:      ⚠️ Not running (optional)"
    fi

    echo "═══════════════════════════════════════"
    echo ""
}

case "${1:-start}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 2
        start_services
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
