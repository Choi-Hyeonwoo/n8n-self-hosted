# ETF Tracker 시스템 아키텍처 가이드

> TIMEFOLIO ETF 보유종목 자동 추적 및 AI 분석 시스템

---

## 1. 시스템 개요

n8n 자동화를 통해 **TIMEFOLIO의 6개 ETF 보유종목**을 매일 자동으로 추적하고, **Claude AI 기반 심층 분석**으로 보고서를 생성하여 **Telegram으로 전송**하는 완전 자동화된 시스템입니다.

### 핵심 특징
- **자동 스케줄**: 국내(월~금 16:00), 해외(화~토 08:00)
- **Deep Research**: Claude API를 활용한 종목별 심층 분석
- **지식축적**: Obsidian 기반 자동 지식베이스 구축
- **비용효율**: 월 약 1,800원의 Claude API 비용

---

## 2. 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                     n8n Workflow (웹)                           │
│  [Schedule: 0 16 * * 1-5] or [0 8 * * 2-6]                     │
└─────────────────┬───────────────────────────────────────────────┘
                  │ (HTTP Request)
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│           api_server.py:8765 (HTTP API Server)                 │
│  - /health, /status, /run/domestic, /run/overseas              │
│  - 비동기 실행 (Thread 기반)                                     │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│        run_etf_tracker.py (자동화 래퍼)                         │
│  - 공휴일 체크 (한국/미국)                                       │
│  - etf_tracker.py 호출                                         │
│  - Telegram 전송 관리                                           │
└─────────────────┬───────────────────────────────────────────────┘
                  │
        ┌─────────┴──────────┐
        ↓                    ↓
 ┌──────────────┐  ┌──────────────────┐
 │ etf_tracker  │  │ Obsidian KB      │
 │     .py      │  │ (자동 저장)       │
 │ (분석 엔진)   │  │ - daily/         │
 │              │  │ - stocks/        │
 │ 1. 수집      │  │ - etfs/          │
 │ 2. 파싱      │  │ - themes/        │
 │ 3. 분석      │  │                  │
 │ 4. 렌더링    │  │                  │
 └──┬───────────┘  └──────────────────┘
    │
    ├→ timeetf.co.kr (데이터 수집)
    ├→ Google News RSS (뉴스 수집)
    ├→ Claude API (Deep Research)
    └→ matplotlib (이미지 생성)

    ↓ (결과)
    Telegram @TF_ETF_TRACKER 채널
```

---

## 3. 디렉토리 구조

```
openclaw-skills/etf-tracker/
├── SKILL.md                          # 기능 문서
├── scripts/
│   ├── etf_tracker.py               # 메인 분석 엔진 (~26KB)
│   ├── run_etf_tracker.py           # 자동화 래퍼 (스케줄 체크)
│   ├── api_server.py                # HTTP API 서버 (n8n 연동용)
│   └── setup_cron.sh                # Cron 설정 스크립트
├── etf-tracker.env.example          # 환경설정 템플릿
├── etf-tracker-api.service          # systemd 서비스
├── etf-domestic.service             # 국내 실행 서비스
├── etf-domestic.timer               # 국내 스케줄 타이머
├── etf-overseas.service             # 해외 실행 서비스
├── etf-overseas.timer               # 해외 스케줄 타이머
└── knowledge/                       # 자동 생성 지식베이스
    ├── README.md
    ├── MASTER_CONTEXT.md
    ├── RON_GUIDE.md
    ├── daily/                       # 일별 분석 리포트
    ├── etfs/                        # ETF별 전략 추적
    ├── stocks/                      # 종목별 프로필
    └── themes/                      # 테마별 트렌드
```

---

## 4. 추적 ETF 목록

### 해외투자 (OVERSEAS)
| 키 | ETF 명 | idx | 스케줄 |
|---|------|-----|------|
| NQ100 | 미국나스닥100액티브 | 2 | 화~토 08:00 |
| CN_AI | 차이나AI테크액티브 | 19 | 화~토 08:00 |
| GLOBAL_AI | 글로벌AI인공지능액티브 | 6 | 화~토 08:00 |

### 국내투자 (DOMESTIC)
| 키 | ETF 명 | idx | 스케줄 |
|---|------|-----|------|
| KOSPI_ACTIVE | 코스피액티브 | 11 | 월~금 16:00 |
| K_CULTURE | K컬처액티브 | 1 | 월~금 16:00 |
| K_BIO | K바이오액티브 | 13 | 월~금 16:00 |

---

## 5. 핵심 스크립트 설명

### 5.1 etf_tracker.py (메인 분석 엔진)

**주요 함수:**

```python
# 1. 데이터 수집
fetch_page(idx, cate="001")                    # timeetf.co.kr 페이지 다운로드
fetch_period_comparison(idx, period)            # AJAX로 비중 변동 데이터
parse_full_holdings(html)                       # 보유종목 테이블 파싱

# 2. 비중 변동 계산
build_weight_map(holdings)                      # 종목명→비중 매핑
build_diff_map_from_weights(current, prev)      # 전일 대비 변동 계산
parse_ajax_changes(ajax_data)                   # 신규편입/비중변동 분류

# 3. 이미지 렌더링
render_page1(group_label, date, per_etf_changes, etf_sections)
  # - 1일 비중 증가 TOP 5 (빨간색)
  # - 1일 비중 감소 BOTTOM 3 (파란색)
  # - ETF별 Holdings TOP 10

render_page2_news(group_label, date, per_etf_news)
  # - 주요 종목별 뉴스 분석
  # - 원인 2줄 + 변동 판단 1줄 형식

# 4. Claude API Deep Research
analyze_news_with_claude(mover, etf_key)
  # - 종목 프로필 + 뉴스 + 비중변동 종합 분석
```

**핵심 설정 상수:**
```python
BASE_URL = "https://timeetf.co.kr/m11_view.php"
AJAX_URL = "https://timeetf.co.kr/past_pdf_json.php"

ETFS = {
    "NQ100": {"idx": 2, "name": "미국나스닥100액티브"},
    "CN_AI": {"idx": 19, "name": "차이나AI테크액티브"},
    "GLOBAL_AI": {"idx": 6, "name": "글로벌AI인공지능액티브"},
    "KOSPI_ACTIVE": {"idx": 11, "name": "코스피액티브"},
    "K_CULTURE": {"idx": 1, "name": "K컬처액티브"},
    "K_BIO": {"idx": 13, "name": "K바이오액티브"},
}

_STOCK_PROFILES = {
    "SK하이닉스": {"sector": "반도체", "profile": "HBM 세계 1위..."},
    "NVIDIA Corp": {"sector": "반도체", "profile": "AI 가속기..."},
    # ... 48개 종목
}
```

### 5.2 run_etf_tracker.py (자동화 래퍼)

**주요 기능:**

```python
# 1. 공휴일 체크
is_korean_business_day(date_str)    # 한국 영업일 확인
is_us_business_day(date_str)        # 미국 영업일 확인

KOREAN_HOLIDAYS_2026 = {
    "2026-01-01", "2026-02-16~18" (설날), "2026-03-01" (삼일절), ...
}

US_HOLIDAYS_2026 = {
    "2026-01-01", "2026-01-19" (MLK), "2026-02-16" (Presidents Day), ...
}

# 2. Telegram 전송
send_to_telegram(images: list, summary: str)
  # - 이미지 업로드 (multipart/form-data)
  # - HTML 형식 텍스트 전송

# 3. 메인 실행
# python3 run_etf_tracker.py domestic|overseas [--force] [--dry-run]
```

### 5.3 api_server.py (HTTP API 서버)

**엔드포인트:**

```
GET  /health           → {"status": "ok"}
GET  /status           → {"last_domestic": {...}, "last_overseas": {...}}
POST /run/domestic     → 비동기 실행 시작 (202 Accepted)
POST /run/overseas     → 비동기 실행 시작 (202 Accepted)
```

---

## 6. 데이터 처리 흐름

```
timeetf.co.kr (실시간 데이터)
    ↓ (HTML 스크래핑)
전체 보유종목 테이블
    ↓ (parse_full_holdings)
Holdings JSON
    ↓ (1D/1W/1M 비교)
비중 변동 계산 (ups/downs/news)
    ↓
    ├→ render_page1() → 이미지 1 (보유종목 테이블)
    │
    ├→ Google News 수집
    │   └→ Claude Deep Research
    │       └→ render_page2_news() → 이미지 2 (뉴스 분석)
    │
    └→ 텍스트 분석 요약 (HTML)

    ↓ (최종 출력)
send_to_telegram() + save_daily_report()
```

### 비중 변동 계산 로직

```python
# 1. 3가지 기준 시점 데이터 다운로드
current = fetch_page(idx)                    # 현재
prev_1d = fetch_page_for_date(idx, 1일전)    # 1일 전
prev_1w = fetch_page_for_date(idx, 1주전)    # 1주 전
prev_1m = fetch_period_comparison(idx, "1M") # 1개월 전 (AJAX)

# 2. 변동 계산
diff_1d = current_weight - weight_1d_ago
diff_1w = current_weight - weight_1w_ago
diff_1m = current_weight - weight_1m_ago
```

---

## 7. 환경 설정

### 필수 환경변수 (/etc/etf-tracker.env)

```bash
# Claude API (Deep Research용)
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Telegram 알림
TG_BOT_TOKEN=your-telegram-bot-token
TG_CHANNEL_ID=-100xxxxxxxxxx

# API 서버 포트 (선택)
ETF_API_PORT=8765
```

### 필수 Python 패키지

```bash
pip install requests beautifulsoup4 matplotlib anthropic
```

---

## 8. systemd 서비스 설정

### API 서버 (항상 실행)

**etf-tracker-api.service**
```ini
[Unit]
Description=ETF Tracker API Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/etf-tracker/scripts
EnvironmentFile=/etc/etf-tracker.env
ExecStart=/usr/bin/python3 api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 타이머 설정

**etf-domestic.timer**
```ini
[Timer]
OnCalendar=Mon..Fri 16:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

**etf-overseas.timer**
```ini
[Timer]
OnCalendar=Tue..Sat 08:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

### 서비스 활성화

```bash
# 서비스 파일 복사
sudo cp *.service *.timer /etc/systemd/system/

# 환경변수 파일 설정
sudo cp etf-tracker.env.example /etc/etf-tracker.env
sudo nano /etc/etf-tracker.env  # API 키 설정

# 서비스 활성화
sudo systemctl daemon-reload
sudo systemctl enable --now etf-tracker-api.service
sudo systemctl enable --now etf-domestic.timer
sudo systemctl enable --now etf-overseas.timer
```

---

## 9. n8n 워크플로우 설정

### HTTP Request 노드 설정

```json
{
  "method": "POST",
  "url": "http://localhost:8765/run/domestic",
  "headers": {
    "Content-Type": "application/json"
  }
}
```

### Schedule Trigger 설정

- **국내**: Cron `0 16 * * 1-5` (월~금 16:00)
- **해외**: Cron `0 8 * * 2-6` (화~토 08:00)

---

## 10. 지식베이스 구조

### 일별 리포트 (daily/)

```markdown
# 국내 ETF 분석 - 2026-02-02

## 분석 요약
**▶ 코스피액티브**
- [SK하이닉스]: HBM 수요 증가로 비중 확대...

**▶ K컬처액티브**
- ...

## 포트폴리오 종합 판단
- 방어적 포지션 전환
- 주요 테마: AI, 반도체
```

### 종목 프로필 (stocks/)

```markdown
# SK하이닉스

## 기본정보
- 섹터: 반도체
- 사업: HBM 세계 1위

## 포트폴리오 히스토리
| 날짜 | ETF | 비중 | 변동 | 분석 |
|------|-----|------|------|------|
| 2026-02-02 | 코스피액티브 | 5.23% | +0.53%p | AI 가속기... |
```

---

## 11. 비용 분석

| 항목 | 비용 |
|------|------|
| Claude API | 월 ~$1.32 (1,800원) |
| Telegram | 무료 |
| timeetf.co.kr | 무료 |
| Google News RSS | 무료 |

**Claude API 계산:**
- 영업일 22일 × 6 ETF = 132회/월
- 회당 ~$0.01 = 월 $1.32

---

## 12. 트러블슈팅

| 문제 | 원인 | 해결 |
|------|------|------|
| Claude API 오류 | 크레딧 부족 | Anthropic 콘솔에서 충전 |
| Telegram 전송 실패 | 봇 권한 없음 | 봇을 채널 관리자로 설정 |
| 데이터 수집 실패 | timeetf.co.kr 접근 불가 | VPN/방화벽 확인 |
| 공휴일 오류 | 연도별 데이터 누락 | HOLIDAYS 딕셔너리 업데이트 |
| 이미지 미생성 | matplotlib 미설치 | `pip install matplotlib` |

---

## 13. 수동 실행 방법

```bash
# 국내 ETF 실행
cd /path/to/etf-tracker/scripts
python3 run_etf_tracker.py domestic

# 해외 ETF 실행
python3 run_etf_tracker.py overseas

# 강제 실행 (공휴일 무시)
python3 run_etf_tracker.py domestic --force

# 드라이런 (실제 전송 없음)
python3 run_etf_tracker.py domestic --dry-run
```

---

## 14. 확장 가능성

### 단기
- Google Sheets 동기화
- 이메일 알림 추가
- 웹 대시보드

### 중기
- ML 기반 비중 변동 예측
- 포트폴리오 최적화 추천
- 섹터별 성과 분석

### 장기
- 자동 트레이딩 시그널
- 멀티마켓 확장 (유럽, 홍콩)
- AI 학습 기반 운용 패턴 분석

---

## 15. 핵심 로직 요약

1. **데이터 수집**: timeetf.co.kr에서 ETF 보유종목 HTML 스크래핑
2. **비중 계산**: 1D/1W/1M 기준 비중 변동 계산
3. **뉴스 수집**: Google News RSS로 관련 뉴스 수집
4. **AI 분석**: Claude API로 비중 변동 사유 분석
5. **이미지 생성**: matplotlib으로 보고서 이미지 렌더링
6. **알림 전송**: Telegram API로 채널에 전송
7. **지식 저장**: Obsidian 마크다운으로 히스토리 축적

---

*이 문서는 ETF Tracker 시스템의 논리 구조를 설명합니다.*
*다른 환경에서 구축 시 이 가이드를 참조하세요.*
