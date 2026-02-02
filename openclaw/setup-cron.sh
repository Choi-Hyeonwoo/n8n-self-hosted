#!/usr/bin/env bash
# =============================================================================
# OpenClaw Cron Jobs Setup Script
# =============================================================================
# Sets up automated scheduled tasks for OpenClaw.
#
# Usage:
#   chmod +x setup-cron.sh
#   sudo ./setup-cron.sh
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }

CONTAINER="openclaw-openclaw-gateway-1"

echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   OpenClaw Cron Jobs Setup              ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Ask for timezone
read -p "Enter your timezone (default: Asia/Seoul): " -r TZ
TZ=${TZ:-Asia/Seoul}

# =============================================================================
# 1. Morning Brief - 매일 아침 8시 뉴스 브리핑
# =============================================================================
log_info "Setting up Morning Brief (8:00 AM daily)..."

docker exec "$CONTAINER" node dist/index.js cron add \
    --name "Morning Brief" \
    --cron "0 8 * * *" \
    --tz "$TZ" \
    --session isolated \
    --message "오늘의 주요 뉴스, 기술 트렌드, 금융 시장 요약을 한국어로 간결하게 정리해줘. 중요도 순으로 5개 항목으로 요약." \
    --deliver \
    --channel telegram 2>/dev/null && \
    log_ok "Morning Brief cron job created" || echo "  (manual setup needed)"

# =============================================================================
# 2. Server Health Check - 6시간마다 서버 상태 확인
# =============================================================================
log_info "Setting up Server Health Check (every 6 hours)..."

docker exec "$CONTAINER" node dist/index.js cron add \
    --name "Server Health Check" \
    --cron "0 */6 * * *" \
    --tz "$TZ" \
    --session isolated \
    --message "서버 상태를 점검해줘: 디스크 사용량, 메모리 사용량, CPU 로드, Docker 컨테이너 상태를 확인하고 문제가 있으면 알려줘." \
    --deliver \
    --channel telegram 2>/dev/null && \
    log_ok "Server Health Check cron job created" || echo "  (manual setup needed)"

# =============================================================================
# 3. Weekly Security Audit - 매주 월요일 보안 점검
# =============================================================================
log_info "Setting up Weekly Security Audit (Monday 9:00 AM)..."

docker exec "$CONTAINER" node dist/index.js cron add \
    --name "Weekly Security Audit" \
    --cron "0 9 * * 1" \
    --tz "$TZ" \
    --session isolated \
    --message "주간 보안 점검을 실행해줘: 시스템 업데이트 확인, Docker 이미지 취약점, 열린 포트, 로그인 시도 확인." \
    --deliver \
    --channel telegram 2>/dev/null && \
    log_ok "Weekly Security Audit cron job created" || echo "  (manual setup needed)"

# =============================================================================
# 4. GitHub Activity Summary - 매일 저녁 6시
# =============================================================================
log_info "Setting up GitHub Activity Summary (6:00 PM daily)..."

docker exec "$CONTAINER" node dist/index.js cron add \
    --name "GitHub Daily Summary" \
    --cron "0 18 * * *" \
    --tz "$TZ" \
    --session isolated \
    --message "오늘의 GitHub 활동을 요약해줘: 새로운 이슈, PR, 커밋 내역을 정리하고 내일 해야 할 작업을 제안해줘." \
    --deliver \
    --channel telegram 2>/dev/null && \
    log_ok "GitHub Daily Summary cron job created" || echo "  (manual setup needed)"

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}   Cron Jobs Setup Complete!             ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "  ${YELLOW}Manage cron jobs:${NC}"
echo -e "    List:    docker exec $CONTAINER node dist/index.js cron list"
echo -e "    Run now: docker exec $CONTAINER node dist/index.js cron run <job-id> --force"
echo -e "    Delete:  docker exec $CONTAINER node dist/index.js cron remove <job-id>"
echo ""
echo -e "  ${YELLOW}Jobs stored at:${NC} /home/openclaw/.openclaw/cron/jobs.json"
echo ""
