# RON ETF Tracker 운영 가이드

이 문서는 RON이 ETF Tracker를 운영하고 학습하기 위한 종합 가이드입니다.

## 시스템 개요

```
┌─────────────────────────────────────────────────────────────┐
│                    ETF Tracker v12                          │
├─────────────────────────────────────────────────────────────┤
│  n8n Scheduler (Schedule Trigger 노드)                      │
│  ├── 국내: 월~금 16:00 KST                                  │
│  └── 해외: 화~토 08:00 KST                                  │
│                    ↓                                        │
│  HTTP Request → api_server.py (포트 8765)                   │
│  ├── POST /run/domestic                                     │
│  └── POST /run/overseas                                     │
│                    ↓                                        │
│  run_etf_tracker.py                                         │
│  ├── 공휴일 체크 (한국/미국)                                │
│  ├── etf_tracker.py 호출                                    │
│  │   ├── timeetf.co.kr 데이터 수집                         │
│  │   ├── Google News 뉴스 수집                              │
│  │   ├── Claude API Deep Research                           │
│  │   └── Obsidian 지식베이스 저장                           │
│  └── Telegram @TF_ETF_TRACKER 전송                          │
└─────────────────────────────────────────────────────────────┘
```

## 파일 구조

```
etf-tracker/
├── scripts/
│   ├── etf_tracker.py      # 메인 분석 엔진 (v12)
│   ├── run_etf_tracker.py  # 자동화 실행 래퍼
│   ├── api_server.py       # HTTP API 서버 (n8n용)
│   └── setup_cron.sh       # Cron 설정 (옵션)
├── etf-tracker-api.service # systemd 서비스 파일
└── knowledge/              # Obsidian 지식베이스
    ├── daily/              # 일별 분석 리포트
    ├── stocks/             # 종목별 프로필 & 히스토리
    ├── etfs/               # ETF별 전략 추적
    ├── themes/             # 테마별 트렌드
    ├── logs/               # 실행 로그
    └── RON_GUIDE.md        # 이 문서
```

## 실행 방법

### 수동 실행
```bash
# 국내 ETF 실행
cd /home/user/n8n-self-hosted/openclaw-skills/etf-tracker/scripts
python3 run_etf_tracker.py domestic

# 해외 ETF 실행
python3 run_etf_tracker.py overseas

# 강제 실행 (공휴일 무시)
python3 run_etf_tracker.py domestic --force

# 테스트 (전송 없이)
python3 run_etf_tracker.py overseas --dry-run
```

### API 서버 실행 (n8n 연동용)
```bash
# 백그라운드 실행
cd /home/user/n8n-self-hosted/openclaw-skills/etf-tracker/scripts
nohup python3 api_server.py > /var/log/etf_api.log 2>&1 &

# 또는 systemd 서비스로 등록
sudo cp ../etf-tracker-api.service /etc/systemd/system/
sudo systemctl enable etf-tracker-api
sudo systemctl start etf-tracker-api
```

### n8n 워크플로우 설정
1. **Schedule Trigger 노드** 추가
   - 국내: Cron `0 16 * * 1-5` (월~금 16:00)
   - 해외: Cron `0 8 * * 2-6` (화~토 08:00)

2. **HTTP Request 노드** 연결
   - Method: POST
   - URL: `http://localhost:8765/run/domestic` 또는 `/run/overseas`

### API 엔드포인트
| 메소드 | 경로 | 설명 |
|--------|------|------|
| GET | /health | 서버 상태 확인 |
| POST | /run/domestic | 국내 ETF 실행 |
| POST | /run/overseas | 해외 ETF 실행 |
| GET | /status | 최근 실행 상태 |

## 스케줄 상세

### 국내 ETF (DOMESTIC_KEYS)
- **ETF**: 코스피액티브, K컬처액티브, K바이오액티브
- **시간**: 월~금 16:00 KST
- **제외**: 한국 공휴일 (KRX 휴장일)
- **데이터 기준**: 당일 종가 기준

### 해외 ETF (OVERSEAS_KEYS)
- **ETF**: 미국나스닥100액티브, 차이나AI테크액티브, 글로벌AI인공지능액티브
- **시간**: 화~토 08:00 KST
- **제외**: 미국 공휴일 (NYSE 휴장일)
- **데이터 기준**: 전일 미국장 마감 기준

## 환경변수

| 변수 | 용도 | 기본값 |
|------|------|--------|
| ANTHROPIC_API_KEY | Claude API (Deep Research) | ~/.bashrc에 설정됨 |
| TG_BOT_TOKEN | Telegram 봇 토큰 | 8310012683:AAFf... |
| TG_CHANNEL_ID | Telegram 채널 ID | -1002796769091 |

## Deep Research 분석

Claude Sonnet 4를 사용하여 각 종목별 복합 분석 수행:

1. **종목 프로필**: `_STOCK_PROFILES` 딕셔너리에서 기업 특성 참조
2. **뉴스 컨텍스트**: Google News에서 최근 뉴스 수집
3. **비중 변동**: timeetf.co.kr에서 1D 기준 변동 계산
4. **종합 판단**: Claude가 위 정보를 종합하여 분석 생성

### 토큰 비용 (월간 추정)
- 영업일 22일 × 6 ETF = 132회 호출
- 회당 ~$0.01 → **월 $1.32 (약 1,800원)**

## 지식베이스 활용

### RON이 학습할 수 있는 패턴

1. **종목 히스토리** (`stocks/*.md`)
   - 특정 종목이 어느 ETF에서 자주 비중 조정되는지
   - 비중 변동의 계절성/패턴

2. **ETF 전략** (`etfs/*.md`)
   - 각 ETF의 운용 스타일
   - 선호하는 섹터/종목 유형

3. **테마 트렌드** (`themes/*.md`)
   - AI, 반도체, 바이오 등 테마별 흐름
   - 섹터 로테이션 패턴

4. **실행 로그** (`logs/*.md`)
   - 시스템 안정성 모니터링
   - 오류 패턴 분석

## 트러블슈팅

### Claude API 오류
```
Error: credit balance is too low
→ Anthropic 콘솔에서 크레딧 충전
```

### Telegram 전송 실패
```
→ 봇이 채널 관리자인지 확인
→ 채널 ID가 올바른지 확인
```

### 데이터 수집 실패
```
→ timeetf.co.kr 접속 확인
→ VPN/방화벽 설정 확인
```

## 업데이트 방법

### 공휴일 추가 (연간)
`run_etf_tracker.py`의 `KOREAN_HOLIDAYS_2026`, `US_HOLIDAYS_2026` 수정

### 새 ETF 추가
`etf_tracker.py`의 `ETFS` 딕셔너리에 추가

### 종목 프로필 추가
`etf_tracker.py`의 `_STOCK_PROFILES` 딕셔너리에 추가

---

**마지막 업데이트**: 2026-02-03
**버전**: v12 (Deep Research + Obsidian Knowledge)
