# 현우 시스템 마스터 컨텍스트 v2

> 아키(Claude)와 현우가 3일간 구축한 시스템 전체 맥락
> RON은 이 문서를 학습하여 일관된 서비스 제공

---

## 1. 팀 구조

| 이름 | 정체 | 환경 | 역할 |
|------|------|------|------|
| **아키** | Claude Opus 4.5 | Claude Code (데스크탑) | 설계, 문제해결, 지식 생성 |
| **RON** | OpenClaw (Gemini) | VPS Docker | 실행, 모니터링, 일상 서포트 |
| **웹키** | Claude 웹버전 | 브라우저 | 웹 작업 대행 (GitHub 등) |

### 팀 규칙
- RON이 모르는 문제 → **"아키한테 물어봐 달라"** 요청
- 아키가 만든 지식 → RON이 학습하고 따름
- **코드 직접 수정 금지** → 아키가 해결해줌

---

## 2. VPS 환경

### 서버 정보
- **IP**: 72.62.255.251
- **OS**: Ubuntu (Hostinger VPS)
- **사용자**: `openclaw` (UID 1000)
- **OpenClaw 포트**: 18789

### 주요 경로
```
/opt/openclaw/                    # OpenClaw 설치
├── .env                          # 환경설정
└── docker-compose.yml            # Docker 설정

/home/openclaw/.openclaw/         # 데이터 디렉토리
├── openclaw.json                 # 메인 설정
├── auth-profiles.json            # API 키
├── agents/main/agent/            # RON 에이전트
├── skills/etf-tracker/           # ETF 분석 스킬
└── workspace/                    # 작업 공간
```

### 컨테이너 경로 매핑
- 호스트: `/home/openclaw/.openclaw/`
- 컨테이너: `/home/node/.openclaw/`

---

## 3. ETF 리포트 시스템

### 스크립트 위치
```
/home/openclaw/.openclaw/skills/etf-tracker/scripts/etf_tracker.py
```

### 실행 방법
```bash
# 해외 ETF
python3 [스크립트경로] overseas

# 국내 ETF
python3 [스크립트경로] domestic
```

### 출력물
1. **이미지 1**: `/tmp/etf_p1_해외_YYYY-MM-DD.png`
   - 1일 비중 증가 TOP 5 / 감소 BOTTOM 3
   - Holdings TOP 10

2. **이미지 2**: `/tmp/etf_p2_해외_YYYY-MM-DD.png`
   - 주요 종목 뉴스 분석
   - 원인 2줄 + 판단 1줄

3. **텍스트 요약**: Telegram HTML 형식

### ETF 목록
| 키 | 이름 | 분류 |
|---|------|-----|
| NQ100 | 미국나스닥100액티브 | 해외 |
| CN_AI | 차이나AI테크액티브 | 해외 |
| GLOBAL_AI | 글로벌AI인공지능액티브 | 해외 |
| KOSPI_ACTIVE | 코스피액티브 | 국내 |
| K_CULTURE | K컬처액티브 | 국내 |
| K_BIO | K바이오액티브 | 국내 |

### ⚠️ 중요 규칙
- **etf_tracker.py 수정 금지** (1803줄 유지)
- 폰트 문제 → 환경으로 해결
- RON이 수정 시도 → 430줄로 파손된 적 있음

---

## 4. API 키 설정

### 현재 설정된 API
- **Google Gemini**: RON 기본 모델
- **OpenRouter**: 백업 모델
- **Anthropic**: Deep Research용

### API 키 설정 방법
```bash
docker compose run --rm openclaw-cli configure
# → Model 섹션 선택 → API 키 입력
```

---

## 5. 트러블슈팅 기록

### 문제 1: 모델 자동 변경
- **증상**: RON이 `openrouter/free`로 변경 (존재하지 않는 모델)
- **원인**: Gemini 429 에러 후 자가 수정 시도
- **해결**: `openclaw configure`로 재설정

### 문제 2: API 키 못 찾음
- **증상**: "No API key found for provider google"
- **원인**: `auth-profiles.json`이 agent 폴더에 없음
- **해결**:
  ```bash
  cp /home/openclaw/.openclaw/auth-profiles.json \
     /home/openclaw/.openclaw/agents/main/agent/
  ```

### 문제 3: .env 경로 오류
- **증상**: 컨테이너가 잘못된 경로 마운트
- **원인**: `OPENCLAW_CONFIG_DIR=/root/.openclaw`
- **해결**: `/home/openclaw/.openclaw`로 수정

### 문제 4: 스크립트 파손
- **증상**: 이미지 생성 안 됨
- **원인**: RON이 etf_tracker.py 수정 → 1803줄 → 430줄
- **해결**: Git에서 원본 복구

### 문제 5: 컨테이너 폰트 없음
- **증상**: 이미지 한글 안 보임/얇음
- **해결**:
  ```bash
  docker cp /usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc \
            openclaw-openclaw-gateway-1:/usr/share/fonts/opentype/noto/
  ```

---

## 6. 지식 동기화 구조

### 레포지토리
- **Private**: `Choi-Hyeonwoo/Ron_openclaw` (지식 동기화용)
- **Public**: `Choi-Hyeonwoo/n8n-self-hosted` (코드용, 민감정보 X)

### 동기화 파이프라인
```
아키 → 로컬 파일 생성 → VPS 복사 → Private 레포 push
                                    ↓
                              RON이 pull → 학습
```

### 학습 주기
- 4시간마다 Git pull (cron)
- 수동: "아키한테 배운 거 학습해" 명령

---

## 7. 자주 쓰는 명령어

### ETF 리포트
```bash
python3 /home/openclaw/.openclaw/skills/etf-tracker/scripts/etf_tracker.py overseas
```

### OpenClaw 재시작
```bash
cd /opt/openclaw && docker compose restart
```

### 로그 확인
```bash
docker logs openclaw-openclaw-gateway-1 --tail 50
```

### 설정 변경
```bash
docker compose run --rm openclaw-cli configure
```

### Git 동기화 (Private 레포)
```bash
cd /path/to/Ron_openclaw && git pull
```

---

## 8. 연락처

- **Telegram**: 492860021 (현우)
- **RON Bot**: @ronclawBot
- **Gateway**: ws://72.62.255.251:18789

---

*마지막 업데이트: 2026-02-04*
*작성: 아키 (Claude Opus 4.5)*
