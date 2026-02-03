#!/bin/bash
#
# RON 모델을 gemini-3-preview로 변경
#

CONFIG_FILE="/home/openclaw/.openclaw/config.json"
SETTINGS_FILE="/home/openclaw/.openclaw/settings.json"

echo "=== RON 모델 변경 스크립트 ==="

# 현재 설정 확인
echo ""
echo "현재 모델 확인 중..."
docker exec openclaw-gateway env | grep -i model

# 설정 파일 찾기
if [ -f "$CONFIG_FILE" ]; then
    echo ""
    echo "config.json 발견"
    cat "$CONFIG_FILE"

    # 모델 변경 (gemini-3-flash-preview → gemini-3-preview)
    sed -i 's/gemini-3-flash-preview/gemini-3-preview/g' "$CONFIG_FILE"
    sed -i 's/gemini-flash/gemini-3-preview/g' "$CONFIG_FILE"

    echo ""
    echo "변경 후:"
    cat "$CONFIG_FILE"
fi

if [ -f "$SETTINGS_FILE" ]; then
    echo ""
    echo "settings.json 발견"
    cat "$SETTINGS_FILE"

    sed -i 's/gemini-3-flash-preview/gemini-3-preview/g' "$SETTINGS_FILE"
    sed -i 's/gemini-flash/gemini-3-preview/g' "$SETTINGS_FILE"

    echo ""
    echo "변경 후:"
    cat "$SETTINGS_FILE"
fi

# 환경변수로 설정되어 있으면 docker-compose 수정 필요
echo ""
echo "=== Docker 환경변수 확인 ==="
docker inspect openclaw-gateway --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -i model

echo ""
echo "=== 컨테이너 재시작 ==="
docker restart openclaw-gateway
sleep 5

echo ""
echo "=== 변경 확인 ==="
docker logs openclaw-gateway --tail 10 | grep model

echo ""
echo "완료!"
