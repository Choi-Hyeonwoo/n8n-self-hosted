#!/bin/bash
# OpenClaw Obsidian Vault Knowledge Structure Setup
# Run: ssh root@72.62.255.251 'bash -s' < setup-vault.sh

VAULT="/opt/mcp-servers/obsidian-vault-data"

echo "=== Setting up Obsidian Vault Knowledge Structure ==="

# 1. Create folder structure
echo "Creating folders..."
mkdir -p "$VAULT"/{00-Inbox,01-Daily,02-Research/{Stocks,Sectors,Macro},03-Portfolio,04-Knowledge/{Concepts,Strategies},05-Templates,06-Archive}

# 2. Create .obsidian config
mkdir -p "$VAULT/.obsidian"
cat > "$VAULT/.obsidian/app.json" << 'JSON'
{
  "alwaysUpdateLinks": true,
  "newFileLocation": "folder",
  "newFileFolderPath": "00-Inbox",
  "attachmentFolderPath": "00-Inbox/attachments",
  "showLineNumber": true
}
JSON

# 3. Create Home note (vault index)
cat > "$VAULT/Home.md" << 'MD'
# Ron's Knowledge Vault

## Quick Links
- [[00-Inbox/README|Inbox]] - 새 노트 임시 저장
- [[01-Daily/README|Daily]] - 일일 마켓 노트
- [[02-Research/README|Research]] - 종목/섹터/매크로 리서치
- [[03-Portfolio/README|Portfolio]] - 포트폴리오 추적
- [[04-Knowledge/README|Knowledge]] - 영구 지식 저장소
- [[05-Templates/README|Templates]] - 노트 템플릿

## Tags
- #stock - 개별 종목
- #sector - 섹터 분석
- #macro - 거시경제
- #memo - 메모
- #action - 실행 필요 항목
- #insight - 인사이트/아이디어
MD

# 4. Folder README files
cat > "$VAULT/00-Inbox/README.md" << 'MD'
# Inbox
빠른 메모, 분류되지 않은 노트가 여기에 저장됩니다.
정기적으로 적절한 폴더로 이동하세요.
MD

cat > "$VAULT/01-Daily/README.md" << 'MD'
# Daily Notes
일일 마켓 요약, 뉴스, 관찰 기록.
파일명 형식: `YYYY-MM-DD.md`
MD

cat > "$VAULT/02-Research/README.md" << 'MD'
# Research
종목, 섹터, 매크로 심층 분석.

## 하위 폴더
- **Stocks/** - 개별 종목 분석 (파일명: `{티커}-{회사명}.md`)
- **Sectors/** - GICS 섹터 분석
- **Macro/** - 금리, 환율, 경제지표 등
MD

cat > "$VAULT/03-Portfolio/README.md" << 'MD'
# Portfolio
포트폴리오 구성, 매매 기록, 성과 추적.
MD

cat > "$VAULT/04-Knowledge/README.md" << 'MD'
# Knowledge Base
영구 보관 지식. 시간이 지나도 유효한 개념과 전략.

## 하위 폴더
- **Concepts/** - 재무/투자 개념, 용어 정리
- **Strategies/** - 투자 전략, 매매 규칙
MD

# 5. Templates
cat > "$VAULT/05-Templates/Stock-Analysis.md" << 'MD'
---
ticker: ""
company: ""
sector: ""
industry: ""
date: ""
tags: [stock, analysis]
---

# {Company} ({Ticker}) 분석

## 기업 개요
- **섹터**: 
- **산업**: 
- **시가총액**: 

## 재무 요약
| 지표 | 값 |
|------|-----|
| PER | |
| PBR | |
| ROE | |
| 배당수익률 | |

## 투자 포인트
1. 
2. 
3. 

## 리스크
1. 
2. 

## 결론
- **투자의견**: 
- **목표가**: 
MD

cat > "$VAULT/05-Templates/Daily-Market.md" << 'MD'
---
date: ""
tags: [daily, market]
---

# Daily Market Note - {date}

## 시장 요약
- **KOSPI**: 
- **S&P 500**: 
- **원/달러**: 

## 주요 뉴스
1. 
2. 
3. 

## 관심 종목 동향
| 종목 | 등락 | 메모 |
|------|------|------|
| | | |

## 오늘의 인사이트
> 
MD

cat > "$VAULT/05-Templates/Sector-Analysis.md" << 'MD'
---
sector: ""
date: ""
tags: [sector, analysis]
---

# {Sector} 섹터 분석

## 섹터 개요
- **GICS 분류**: 
- **주요 기업**: 

## 현황
- **트렌드**: 
- **밸류에이션**: 

## 핵심 종목
| 종목 | 시총 | PER | 투자의견 |
|------|------|-----|---------|
| | | | |

## 전망

MD

cat > "$VAULT/05-Templates/Memo.md" << 'MD'
---
date: ""
tags: [memo]
---

# {제목}

## 내용


## 관련 링크
- 
MD

# 6. Starter knowledge notes
cat > "$VAULT/04-Knowledge/Concepts/GICS-Sectors.md" << 'MD'
---
tags: [concept, sector, gics]
---

# GICS 섹터 분류

| 코드 | 섹터 | 영문 |
|------|------|------|
| 10 | 에너지 | Energy |
| 15 | 소재 | Materials |
| 20 | 산업재 | Industrials |
| 25 | 경기소비재 | Consumer Discretionary |
| 30 | 필수소비재 | Consumer Staples |
| 35 | 헬스케어 | Health Care |
| 40 | 금융 | Financials |
| 45 | IT | Information Technology |
| 50 | 커뮤니케이션 | Communication Services |
| 55 | 유틸리티 | Utilities |
| 60 | 부동산 | Real Estate |
MD

cat > "$VAULT/04-Knowledge/Concepts/Valuation-Metrics.md" << 'MD'
---
tags: [concept, valuation]
---

# 주요 밸류에이션 지표

## PER (Price-to-Earnings Ratio)
- 주가 / 주당순이익
- 높을수록 고평가, 낮을수록 저평가 (동일 업종 내 비교)

## PBR (Price-to-Book Ratio)
- 주가 / 주당순자산
- 1 미만이면 자산 가치 대비 저평가

## ROE (Return on Equity)
- 순이익 / 자기자본 × 100
- 높을수록 자본 효율성 우수

## EV/EBITDA
- 기업가치 / EBITDA
- 업종 비교에 유용, 자본구조 영향 배제

## 배당수익률
- 주당배당금 / 주가 × 100
- 현금흐름 관점 투자 매력도
MD

echo ""
echo "=== Vault Structure Created ==="
find "$VAULT" -not -path "*/.obsidian/*" -not -path "*/node_modules/*" | sort
echo ""
echo "Total files: $(find "$VAULT" -type f -not -path "*/.obsidian/*" | wc -l)"
echo "Total folders: $(find "$VAULT" -type d -not -path "*/.obsidian/*" | wc -l)"
