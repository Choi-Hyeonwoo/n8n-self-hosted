#!/bin/bash
# ETF Tracker Cron 설정 스크립트
# RON이 실행하여 자동화 스케줄 설정

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="/usr/bin/python3"
RUNNER="$SCRIPT_DIR/run_etf_tracker.py"

# 환경변수 로드
source ~/.bashrc

echo "═══════════════════════════════════════"
echo "  ETF Tracker Cron 설정"
echo "═══════════════════════════════════════"

# 기존 ETF tracker cron 제거
crontab -l 2>/dev/null | grep -v "run_etf_tracker.py" > /tmp/crontab.tmp

# 새 cron 추가
# 국내 ETF: 월~금 16:00 KST
echo "0 16 * * 1-5 cd $SCRIPT_DIR && ANTHROPIC_API_KEY=\"$ANTHROPIC_API_KEY\" $PYTHON $RUNNER domestic >> /var/log/etf_tracker.log 2>&1" >> /tmp/crontab.tmp

# 해외 ETF: 화~토 08:00 KST
echo "0 8 * * 2-6 cd $SCRIPT_DIR && ANTHROPIC_API_KEY=\"$ANTHROPIC_API_KEY\" $PYTHON $RUNNER overseas >> /var/log/etf_tracker.log 2>&1" >> /tmp/crontab.tmp

# crontab 적용
crontab /tmp/crontab.tmp
rm /tmp/crontab.tmp

echo ""
echo "✅ Cron 설정 완료!"
echo ""
echo "현재 설정된 스케줄:"
crontab -l | grep "run_etf_tracker"
echo ""
echo "스케줄 요약:"
echo "  - 국내 ETF: 월~금 16:00 KST"
echo "  - 해외 ETF: 화~토 08:00 KST"
echo ""
echo "로그 확인: tail -f /var/log/etf_tracker.log"
