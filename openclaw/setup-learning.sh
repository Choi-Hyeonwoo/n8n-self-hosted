#!/usr/bin/env bash
# =============================================================================
# OpenClaw Self-Learning System Setup
# =============================================================================
# Installs custom skills, creates knowledge base, and sets up learning cron jobs.
#
# Usage:
#   chmod +x setup-learning.sh
#   sudo ./setup-learning.sh
# =============================================================================

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }

CONTAINER="openclaw-openclaw-gateway-1"
SKILLS_HOST="/home/openclaw/.openclaw/skills"
KB_HOST="/home/openclaw/.openclaw/workspace/knowledge"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   OpenClaw Self-Learning System Setup   ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# =============================================================================
# 1. Create Knowledge Base Directory Structure
# =============================================================================
log_info "Creating knowledge base directories..."

mkdir -p "$KB_HOST"/{tech,finance,business,devops,n8n,insights,daily,weekly}
chown -R 1000:1000 "$KB_HOST"

# Create initial index
cat > "$KB_HOST/index.md" <<'INDEXEOF'
# Knowledge Index

Last updated: (auto-updated)
Total documents: 0

## By Category
- tech: 0
- finance: 0
- business: 0
- devops: 0
- n8n: 0
- insights: 0
- daily: 0
- weekly: 0

## Recent
(no documents yet)
INDEXEOF

chown 1000:1000 "$KB_HOST/index.md"
log_ok "Knowledge base created at $KB_HOST"

# =============================================================================
# 2. Install Custom Skills
# =============================================================================
log_info "Installing custom skills..."

mkdir -p "$SKILLS_HOST"/{self-learning,n8n-bridge,knowledge-manager}

# Copy skill files
cp "$SCRIPT_DIR/skills/self-learning/openclaw.md" "$SKILLS_HOST/self-learning/openclaw.md"
cp "$SCRIPT_DIR/skills/n8n-bridge/openclaw.md" "$SKILLS_HOST/n8n-bridge/openclaw.md"
cp "$SCRIPT_DIR/skills/knowledge-manager/openclaw.md" "$SKILLS_HOST/knowledge-manager/openclaw.md"

chown -R 1000:1000 "$SKILLS_HOST"
log_ok "Custom skills installed: self-learning, n8n-bridge, knowledge-manager"

# =============================================================================
# 3. Set Up Learning Cron Jobs
# =============================================================================
log_info "Setting up learning cron jobs..."

read -p "Enter your timezone (default: Asia/Seoul): " -r TZ
TZ=${TZ:-Asia/Seoul}

# Morning Brief - 08:00
docker exec "$CONTAINER" node dist/index.js cron add \
    --name "Morning Learning Brief" \
    --cron "0 8 * * *" \
    --tz "$TZ" \
    --session isolated \
    --message "모닝 브리핑을 수행해줘: 1) 한국 기술/AI 뉴스 top 5 검색 2) 금융 시장 동향 3) 현우님 관심 분야 최신 트렌드. 결과를 요약해서 텔레그램으로 보내고, knowledge/daily/ 에 오늘 날짜로 저장해줘." \
    --deliver \
    --channel telegram 2>/dev/null && \
    log_ok "Morning Brief (08:00)" || echo "  (manual setup needed)"

# Deep Research - 12:00
docker exec "$CONTAINER" node dist/index.js cron add \
    --name "Deep Research Session" \
    --cron "0 12 * * *" \
    --tz "$TZ" \
    --session isolated \
    --message "딥 리서치를 수행해줘: 최근 대화에서 나온 주제 중 가장 중요한 것 하나를 골라 tavily로 심층 검색하고, 기존 knowledge/ 에 있는 지식과 연결하여 인사이트를 도출해줘. 결과를 적절한 카테고리에 저장해줘." \
    --deliver \
    --channel telegram 2>/dev/null && \
    log_ok "Deep Research (12:00)" || echo "  (manual setup needed)"

# Daily Review - 22:00
docker exec "$CONTAINER" node dist/index.js cron add \
    --name "Daily Learning Review" \
    --cron "0 22 * * *" \
    --tz "$TZ" \
    --session isolated \
    --message "오늘의 학습 회고를 해줘: 1) 오늘 대화에서 배운 것 정리 2) 새로 저장한 지식 목록 3) 내일 학습할 주제 3개 제안. knowledge/daily/ 에 저장하고 index.md 업데이트해줘." \
    --deliver \
    --channel telegram 2>/dev/null && \
    log_ok "Daily Review (22:00)" || echo "  (manual setup needed)"

# Weekly Report - 일요일 20:00
docker exec "$CONTAINER" node dist/index.js cron add \
    --name "Weekly Knowledge Report" \
    --cron "0 20 * * 0" \
    --tz "$TZ" \
    --session isolated \
    --message "주간 지식 리포트를 작성해줘: 1) 이번 주 학습 내용 종합 2) 카테고리별 새로 추가된 지식 수 3) 핵심 인사이트 top 3 4) 다음 주 학습 추천 주제. knowledge/weekly/ 에 저장하고 텔레그램으로 리포트 보내줘." \
    --deliver \
    --channel telegram 2>/dev/null && \
    log_ok "Weekly Report (Sunday 20:00)" || echo "  (manual setup needed)"

# Server Health - 6시간마다
docker exec "$CONTAINER" node dist/index.js cron add \
    --name "Server Health Check" \
    --cron "0 */6 * * *" \
    --tz "$TZ" \
    --session isolated \
    --message "서버 상태를 점검해줘: 디스크, 메모리, CPU, Docker 컨테이너 상태. 문제가 있을 때만 텔레그램으로 알려줘." \
    --deliver \
    --channel telegram 2>/dev/null && \
    log_ok "Server Health (every 6h)" || echo "  (manual setup needed)"

# =============================================================================
# 4. Restart Gateway
# =============================================================================
log_info "Restarting gateway to load new skills..."
cd /opt/openclaw && docker compose restart openclaw-gateway
sleep 5
log_ok "Gateway restarted"

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}   Self-Learning System Ready!           ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "  ${YELLOW}Installed Skills:${NC}"
echo -e "    - self-learning:     자발적 학습 & 지식 축적"
echo -e "    - n8n-bridge:        n8n 워크플로우 연동"
echo -e "    - knowledge-manager: 지식 베이스 관리"
echo ""
echo -e "  ${YELLOW}Cron Jobs:${NC}"
echo -e "    - 08:00  Morning Brief (뉴스/시장 브리핑)"
echo -e "    - 12:00  Deep Research (심층 리서치)"
echo -e "    - 22:00  Daily Review (일일 회고)"
echo -e "    - Sun 20:00 Weekly Report (주간 리포트)"
echo -e "    - Every 6h  Server Health (서버 점검)"
echo ""
echo -e "  ${YELLOW}Knowledge Base:${NC} $KB_HOST"
echo ""
echo -e "  ${YELLOW}Test Commands (Telegram):${NC}"
echo -e "    '최근에 뭐 배웠어?'"
echo -e "    'AI 에이전트 트렌드에 대해 알아봐줘'"
echo -e "    'n8n 워크플로우 목록 보여줘'"
echo -e "    '주간 리포트 만들어줘'"
echo ""
