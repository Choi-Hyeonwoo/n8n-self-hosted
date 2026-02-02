# ETF Tracker

TIMEFOLIO ETF 보유종목 추적기. timeetf.co.kr에서 6개 ETF의 보유 종목, 비중, 일별 변동을 수집하여 리포트를 생성합니다.

## 추적 ETF

### 해외투자
- **NQ100**: 미국나스닥100액티브 (idx=2)
- **CN_AI**: 차이나AI테크액티브 (idx=19)
- **GLOBAL_AI**: 글로벌AI인공지능액티브 (idx=6)

### 국내투자
- **KOSPI_ACTIVE**: 코스피액티브 (idx=11)
- **K_CULTURE**: K컬처액티브 (idx=1)
- **K_BIO**: K바이오액티브 (idx=13)

## 사용법

```bash
# 전체 ETF 리포트
python3 scripts/etf_tracker.py

# 특정 ETF만
python3 scripts/etf_tracker.py GLOBAL_AI K_BIO

# 해외 ETF만
python3 scripts/etf_tracker.py NQ100 CN_AI GLOBAL_AI
```

## 기능

1. **일일 보유종목 수집**: 전체 보유종목 테이블 + Top 10 변동 파싱
2. **일별 비중 변동 추적**: 전일 대비 비중 증감 계산 (데이터 `03-Portfolio/etf_data/`에 저장)
3. **주요 변동 알림**: 1%p 이상 비중 변동 종목 하이라이트
4. **뉴스 분석 제안**: 큰 비중 변동 종목에 대해 뉴스 검색 권고

## 데이터 저장

`~/.openclaw/workspace/knowledge/03-Portfolio/etf_data/` 디렉토리에 일별 JSON 파일로 저장됩니다.

```
{ETF_KEY}_{YYYY-MM-DD}.json
```

## 의존성

- Python 3 (stdlib only: urllib, json, re, os)
- 인터넷 접속 (timeetf.co.kr)
