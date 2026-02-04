# 현우 시스템 마스터 컨텍스트

> 이 문서는 현우와 Claude가 3일간 구축한 시스템의 전체 맥락입니다.
> RON은 이 문서를 참조하여 일관된 서비스를 제공해야 합니다.

---

## 1. 시스템 구조

### VPS 환경
- **서버**: Hostinger VPS (72.62.255.251)
- **OS**: Ubuntu
- **사용자**: `openclaw` (UID 1000)
- **Docker**: OpenClaw 컨테이너로 RON 실행

### 주요 경로 (VPS)
```
/opt/openclaw/                    # OpenClaw 설치 디렉토리
/opt/openclaw/.env                # 환경설정 (API 키, 경로 등)
/opt/openclaw/docker-compose.yml  # Docker 설정

/home/openclaw/.openclaw/         # OpenClaw 데이터 디렉토리
├── openclaw.json                 # 메인 설정 (모델, 게이트웨이 등)
├── auth-profiles.json            # API 키 저장
├── agents/main/agent/            # RON 에이전트 설정
├── skills/                       # 스킬 스크립트
│   └── etf-tracker/              # ETF 분석 스킬
├── workspace/                    # 작업 공간
└── knowledge/                    # 지식 베이스
```

### 컨테이너 내부 경로 매핑
```
호스트: /home/openclaw/.openclaw/
컨테이너: /home/node/.openclaw/
```

---

## 2. ETF 리포트 시스템

### 스크립트 위치
```
/home/openclaw/.openclaw/skills/etf-tracker/scripts/etf_tracker.py
```

### 실행 방법
```bash
# 해외 ETF (NQ100, 차이나AI, 글로벌AI)
python3 /home/openclaw/.openclaw/skills/etf-tracker/scripts/etf_tracker.py overseas

# 국내 ETF (코스피, K컬처, K바이오)
python3 /home/openclaw/.openclaw/skills/etf-tracker/scripts/etf_tracker.py domestic

# 전체
python3 /home/openclaw/.openclaw/skills/etf-tracker/scripts/etf_tracker.py
```

### 출력물 (3가지)
1. **이미지 1 (Page 1)**: `/tmp/etf_p1_해외_YYYY-MM-DD.png`
   - 1일 비중 증가 TOP 5 (빨간색)
   - 1일 비중 감소 BOTTOM 3 (파란색)
   - ETF별 Holdings TOP 10 (1D/1W/1M 변동)

2. **이미지 2 (Page 2)**: `/tmp/etf_p2_해외_YYYY-MM-DD.png`
   - 주요 종목별 뉴스 분석
   - 원인 2줄 + 변동 판단 1줄

3. **텍스트 요약**: Telegram HTML 형식
   - 포트폴리오 종합 판단

### ETF 목록
| 키 | 이름 | 분류 |
|---|------|-----|
| NQ100 | 미국나스닥100액티브 | 해외 |
| CN_AI | 차이나AI테크액티브 | 해외 |
| GLOBAL_AI | 글로벌AI인공지능액티브 | 해외 |
| KOSPI_ACTIVE | 코스피액티브 | 국내 |
| K_CULTURE | K컬처액티브 | 국내 |
| K_BIO | K바이오액티브 | 국내 |

### 데이터 소스
- **timeetf.co.kr**: TIMEFOLIO ETF 포트폴리오 데이터
- **Google News RSS**: 종목별 뉴스 수집
- **Claude API**: Deep Research 심층 분석 (선택적)

---

## 3. Deep Research 분석

### 활성화 조건
- `anthropic` 라이브러리 설치
- `ANTHROPIC_API_KEY` 환경변수 설정

### 분석 형식
```
1. <b>[종목명]</b>: [사업 특성], [뉴스/실적/업황] 고려해 [비중 확대/축소] 판단. [구체적 사유 1-2문장]

ETF 전체 포트폴리오 방향성 1문장 결론.
```

### 키워드 기반 판단 규칙 (Deep Research 없을 때)
| 키워드 | 비중 증가 시 | 비중 감소 시 |
|-------|------------|------------|
| AI, GPU, 데이터센터 | AI 인프라 투자 확대 수혜 | 성장 대비 고평가 우려 |
| 실적, 매출, 어닝 | 어닝 모멘텀 지속 기대 | 실적 하향 사이클 우려 |
| 임상, FDA, 바이오 | 파이프라인 가치 반영 | 파이프라인 리스크 확대 |
| 메모리, HBM, 반도체 | 업사이클 수혜 기대 | 다운사이클 우려 |
| 현금 | 방어적 포지션 전환 | 적극적 투자 확대 |

---

## 4. 폰트 설정 (이미지 생성용)

### 필요 폰트
```
/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc
/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc
```

### 컨테이너에 폰트 없으면
```bash
docker exec openclaw-openclaw-gateway-1 mkdir -p /usr/share/fonts/opentype/noto
docker cp /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc openclaw-openclaw-gateway-1:/usr/share/fonts/opentype/noto/
docker cp /usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc openclaw-openclaw-gateway-1:/usr/share/fonts/opentype/noto/
```

---

## 5. 트러블슈팅 히스토리

### 문제 1: RON이 자기 모델을 잘못 변경
- **원인**: Google Gemini 429 에러 후 `openrouter/free`로 변경 (존재하지 않는 모델)
- **해결**: `openclaw configure`에서 Model 섹션으로 재설정

### 문제 2: "No API key found for provider google"
- **원인**: `auth-profiles.json`이 agent 폴더에 없음
- **해결**:
  ```bash
  cp /home/openclaw/.openclaw/auth-profiles.json /home/openclaw/.openclaw/agents/main/agent/
  ```

### 문제 3: .env 경로 오류
- **원인**: `OPENCLAW_CONFIG_DIR=/root/.openclaw` (잘못된 경로)
- **해결**: `/home/openclaw/.openclaw`로 수정
  ```bash
  sed -i 's|/root/.openclaw|/home/openclaw/.openclaw|g' /opt/openclaw/.env
  ```

### 문제 4: 컨테이너에서 스크립트 접근 불가
- **원인**: 스크립트가 VPS에 배포되지 않음
- **해결**: Git에서 clone 후 복사
  ```bash
  git clone https://github.com/Choi-Hyeonwoo/n8n-self-hosted.git
  git checkout claude/install-openclaw-vps-hY4FB
  cp -r openclaw-skills/etf-tracker /home/openclaw/.openclaw/skills/
  ```

### 문제 5: "관련 사유 확인 불가" 많이 뜸
- **원인**: 기본 뉴스 검색으로 관련 기사 못 찾음
- **해결**: Deep Research 모드 활성화 (Claude API)

### 문제 6: 이미지 폰트가 얇게 나옴
- **원인**: 컨테이너에 한글 폰트 없음
- **해결**: 호스트에서 컨테이너로 폰트 복사

---

## 6. API 키 설정

### 현재 설정된 API
- **Google Gemini**: RON 기본 모델 (`google/gemini-3-flash-preview`)
- **OpenRouter**: 백업 모델
- **Anthropic**: Deep Research용 (선택적)

### API 키 설정 방법
```bash
docker compose run --rm openclaw-cli configure
# → Model 섹션 선택 → API 키 입력
```

### auth-profiles.json 형식
```json
{
  "google:default": {
    "provider": "google",
    "mode": "api_key",
    "apiKey": "YOUR_KEY"
  }
}
```

---

## 7. 현우의 투자 철학 (분석 시 참고)

### 핵심 원칙
1. **TIMEFOLIO 추종**: 전문 운용사의 비중 변동을 추적하여 시장 인사이트 획득
2. **원인 분석 중시**: 단순 숫자가 아닌 "왜" 비중이 변했는지 파악
3. **선제적 정보**: 시장 전에 포트폴리오 변화를 감지

### 리포트 요구사항
- 이미지 2장 + 텍스트 요약
- 한글 가독성 높게 (굵은 폰트)
- "관련 사유 확인 불가" 최소화 → Deep Research 활용
- 이모지 과다 사용 금지

---

## 8. RON 행동 원칙 (SOUL.md 요약)

### 핵심: 선제적 완결성
- **"할까요?" 금지** → 먼저 하고 보고
- **에러 = 즉시 해결 시도** → 멈추지 말고 대안 실행
- **완료될 때까지 진행** → 현우가 다시 물어보게 만들지 마라

### 에러 자가 복구
| 에러 유형 | 자동 대응 |
|----------|----------|
| Browser 접근 불가 | → yt-dlp, WebSearch로 대체 |
| API 타임아웃 | → 재시도 (최대 3회) |
| 파일 없음 | → 경로 검색 후 재시도 |
| 권한 오류 | → sudo 또는 대안 경로 |

### Chain of Thought
1. **계획**: 무엇을 해야 하는가 정리
2. **실행**: 중간 결과 확인하며 진행
3. **평가**: 결과가 유용한지 자기 평가
4. **완결**: 후속 조치까지 마무리

---

## 9. 자주 쓰는 명령어

### ETF 리포트 생성
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

---

## 10. 연락처 및 채널

- **Telegram**: 492860021 (현우)
- **RON Bot**: @ronclawBot
- **GitHub**: Choi-Hyeonwoo/n8n-self-hosted

---

*마지막 업데이트: 2026-02-04*
*작성: Claude (현우 요청)*
