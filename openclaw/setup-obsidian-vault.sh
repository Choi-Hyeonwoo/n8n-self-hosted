#!/usr/bin/env bash
# =============================================================================
# OpenClaw Obsidian Vault Setup
# =============================================================================
# Creates the Obsidian-compatible knowledge vault structure on VPS,
# seeds initial MOC files and templates, and optionally sets up Git sync.
#
# Usage:
#   chmod +x setup-obsidian-vault.sh
#   sudo ./setup-obsidian-vault.sh
# =============================================================================

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }

KB="/home/openclaw/.openclaw/workspace/knowledge"
CONTAINER="openclaw-openclaw-gateway-1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TODAY=$(date +%Y-%m-%d)

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}   Obsidian Vault Setup for OpenClaw        ${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# =============================================================================
# 1. Create Vault Directory Structure
# =============================================================================
log_info "Creating Obsidian vault directories..."

mkdir -p "$KB"/{00-MOC,01-Concepts,02-Entities,03-Notes/{tech,finance,business,devops,n8n},04-Daily,05-Weekly,06-Projects,07-Reference,templates,.obsidian}

chown -R 1000:1000 "$KB"
log_ok "Vault directories created"

# =============================================================================
# 2. Seed MOC Files
# =============================================================================
log_info "Creating MOC (Map of Content) files..."

cat > "$KB/00-MOC/MOC-Dashboard.md" <<'EOF'
---
type: moc
tags:
  - "#type/moc"
updated: REPLACE_DATE
---

# MOC - Dashboard

> 전체 지식 베이스 대시보드. 모든 카테고리의 진입점.

## 카테고리별 MOC
- [[MOC-Tech]] - AI, 프로그래밍, 개발 도구
- [[MOC-Finance]] - 금융, 투자, 시장 동향
- [[MOC-Business]] - 비즈니스, 마케팅, 전략
- [[MOC-DevOps]] - 서버, 인프라, 배포
- [[MOC-N8N]] - n8n 워크플로우, 자동화

## 핵심 엔티티
- [[OpenClaw]] - AI 에이전트 플랫폼
- [[n8n]] - 워크플로우 자동화 도구

## 최근 업데이트
- (자동 업데이트 예정)

## 통계
- 총 문서 수: (자동 집계)
- Seed: 0 | Growing: 0 | Evergreen: 0
EOF

cat > "$KB/00-MOC/MOC-Tech.md" <<'EOF'
---
type: moc
tags:
  - "#type/moc"
  - "#topic/tech"
updated: REPLACE_DATE
---

# MOC - Tech

> AI, 프로그래밍, 개발 도구 관련 지식

## 핵심 개념
- [[AI-Agent]] - AI 에이전트 기술과 아키텍처
- [[LLM]] - 대규모 언어 모델
- [[Workflow-Automation]] - 워크플로우 자동화

## 주요 엔티티
- [[OpenClaw]]
- [[Anthropic]]
- [[NVIDIA]]

## 최근 노트
- (자동 업데이트)

## 프로젝트
- [[OpenClaw-VPS-Setup]]
EOF

cat > "$KB/00-MOC/MOC-Finance.md" <<'EOF'
---
type: moc
tags:
  - "#type/moc"
  - "#topic/finance"
updated: REPLACE_DATE
---

# MOC - Finance

> 금융, 투자, 시장 동향 관련 지식

## 핵심 개념
- [[Stock-Market]] - 주식 시장
- [[Cryptocurrency]] - 암호화폐

## 주요 엔티티
- (추가 예정)

## 최근 노트
- (자동 업데이트)
EOF

cat > "$KB/00-MOC/MOC-Business.md" <<'EOF'
---
type: moc
tags:
  - "#type/moc"
  - "#topic/business"
updated: REPLACE_DATE
---

# MOC - Business

> 비즈니스, 마케팅, 전략 관련 지식

## 핵심 개념
- (추가 예정)

## 최근 노트
- (자동 업데이트)
EOF

cat > "$KB/00-MOC/MOC-DevOps.md" <<'EOF'
---
type: moc
tags:
  - "#type/moc"
  - "#topic/devops"
updated: REPLACE_DATE
---

# MOC - DevOps

> 서버, 인프라, 배포, Docker 관련 지식

## 핵심 개념
- [[Docker]] - 컨테이너화
- [[VPS-Management]] - VPS 서버 관리

## 주요 엔티티
- [[Hostinger]] - VPS 호스팅

## 최근 노트
- (자동 업데이트)

## 프로젝트
- [[OpenClaw-VPS-Setup]]
EOF

cat > "$KB/00-MOC/MOC-N8N.md" <<'EOF'
---
type: moc
tags:
  - "#type/moc"
  - "#topic/n8n"
updated: REPLACE_DATE
---

# MOC - N8N

> n8n 워크플로우, 자동화 관련 지식

## 핵심 개념
- [[Workflow-Automation]] - 워크플로우 자동화
- [[Webhook]] - 웹훅 트리거

## 주요 엔티티
- [[n8n]]

## 워크플로우 목록
- [[News-Pipeline]] - 뉴스 자동 수집 파이프라인

## 최근 노트
- (자동 업데이트)

## 프로젝트
- [[N8N-Automation]]
EOF

# Replace date placeholder
sed -i "s/REPLACE_DATE/$TODAY/g" "$KB"/00-MOC/*.md

log_ok "MOC files created (Dashboard, Tech, Finance, Business, DevOps, N8N)"

# =============================================================================
# 3. Seed Concept Files
# =============================================================================
log_info "Creating initial concept documents..."

cat > "$KB/01-Concepts/AI-Agent.md" <<EOF
---
date: $TODAY
type: concept
aliases: ["AI 에이전트", "인공지능 에이전트"]
tags:
  - "#type/concept"
  - "#topic/AI"
  - "#status/seed"
---

# AI Agent

## 정의
> 자율적으로 환경을 인식하고, 의사결정하며, 행동을 수행하는 AI 시스템

## 핵심 설명
AI 에이전트는 LLM을 기반으로 도구 사용(tool use), 계획 수립(planning), 메모리(memory) 기능을 갖추어 복잡한 태스크를 자율적으로 수행하는 시스템이다.

## 하위 개념
- [[LLM]] - 에이전트의 두뇌 역할
- [[Workflow-Automation]] - 에이전트의 실행 메커니즘

## 관련 엔티티
- [[OpenClaw]] - 오픈소스 AI 에이전트 플랫폼
- [[Anthropic]] - Claude AI 개발사

## 관련 노트
- (학습 시 자동 추가)

## 참고 자료
- https://www.anthropic.com/research/building-effective-agents
EOF

cat > "$KB/01-Concepts/LLM.md" <<EOF
---
date: $TODAY
type: concept
aliases: ["Large Language Model", "대규모 언어 모델"]
tags:
  - "#type/concept"
  - "#topic/AI"
  - "#status/seed"
---

# LLM (Large Language Model)

## 정의
> 대량의 텍스트 데이터로 학습된 대규모 언어 모델

## 핵심 설명
Transformer 아키텍처 기반으로 자연어를 이해하고 생성하는 모델. GPT, Claude, Gemini 등이 대표적.

## 하위 개념
- [[AI-Agent]] - LLM 기반 자율 에이전트

## 관련 엔티티
- [[Anthropic]] - Claude
- [[OpenClaw]] - Gemini Flash 사용 중

## 관련 노트
- (학습 시 자동 추가)
EOF

cat > "$KB/01-Concepts/Workflow-Automation.md" <<EOF
---
date: $TODAY
type: concept
aliases: ["워크플로우 자동화", "자동화"]
tags:
  - "#type/concept"
  - "#topic/n8n"
  - "#status/seed"
---

# Workflow Automation

## 정의
> 반복적인 작업을 자동화된 워크플로우로 구성하여 효율화하는 기법

## 핵심 설명
트리거 → 조건 분기 → 작업 실행 → 결과 전달의 흐름으로 구성. n8n, Zapier, Make 등의 도구 사용.

## 하위 개념
- [[Webhook]] - 이벤트 기반 트리거

## 관련 엔티티
- [[n8n]] - 워크플로우 자동화 플랫폼

## 관련 노트
- (학습 시 자동 추가)
EOF

log_ok "Concept files created (AI-Agent, LLM, Workflow-Automation)"

# =============================================================================
# 4. Seed Entity Files
# =============================================================================
log_info "Creating initial entity documents..."

cat > "$KB/02-Entities/OpenClaw.md" <<EOF
---
date: $TODAY
type: entity
entity_type: tool
aliases: ["오픈클로", "Ron"]
tags:
  - "#type/entity"
  - "#topic/AI"
website: "https://github.com/nicepkg/openclaw"
---

# OpenClaw

## 개요
> 오픈소스 AI 에이전트 플랫폼. 텔레그램 등 메신저를 통해 AI 에이전트를 제어.

## 핵심 정보
- **유형**: 오픈소스 AI 에이전트 플랫폼
- **분야**: AI Agent, Automation
- **특징**: Docker 기반, 스킬 시스템, 크론잡, 멀티 메신저 지원

## 현우님 프로젝트와의 관계
Hostinger VPS에 설치하여 "Ron"이라는 AI 비서로 운영 중. n8n Cloud와 연동하여 자동화 파이프라인 구축.

## 관련 개념
- [[AI-Agent]]
- [[Workflow-Automation]]

## 설치 정보
- VPS: Hostinger KVM 2 (72.62.255.251)
- Container: openclaw-openclaw-gateway-1
- Model: google/gemini-3-flash-preview
- Telegram Bot: @ronclawBot

## 최신 동향
- $TODAY: VPS 설치 완료, 자가학습 시스템 구축, Obsidian 지식 시스템 연동
EOF

cat > "$KB/02-Entities/n8n.md" <<EOF
---
date: $TODAY
type: entity
entity_type: tool
aliases: ["n8n", "엔에이트엔"]
tags:
  - "#type/entity"
  - "#topic/n8n"
website: "https://n8n.io"
---

# n8n

## 개요
> 오픈소스 워크플로우 자동화 플랫폼. 노드 기반 비주얼 프로그래밍.

## 핵심 정보
- **유형**: 워크플로우 자동화 도구
- **분야**: Automation, Integration
- **특징**: 400+ 인테그레이션, 코드 노드, 웹훅, 크론 트리거

## 현우님 프로젝트와의 관계
n8n Cloud (mangd.app.n8n.cloud) 사용 중. OpenClaw과 연동하여 뉴스 파이프라인, 데이터 수집 자동화.

## 관련 개념
- [[Workflow-Automation]]
- [[Webhook]]

## 워크플로우
- [[News-Pipeline]] - 뉴스 자동 수집

## 최신 동향
- $TODAY: OpenClaw 연동 완료, News Pipeline 워크플로우 생성
EOF

cat > "$KB/02-Entities/Anthropic.md" <<EOF
---
date: $TODAY
type: entity
entity_type: company
aliases: ["앤트로픽"]
tags:
  - "#type/entity"
  - "#topic/AI"
  - "#GICS/45/4510"
gics:
  sector: "45 - Information Technology"
  industry_group: "4510 - Software & Services"
  industry: "451030 - Software"
  sub_industry: "45103010 - Application Software"
website: "https://anthropic.com"
---

# Anthropic

## 개요
> Claude AI를 개발하는 AI 안전 연구 기업

## 핵심 정보
- **유형**: AI 연구 기업
- **분야**: AI Safety, LLM
- **GICS**: Information Technology > Software & Services > Software
- **특징**: Constitutional AI, Claude 모델 시리즈

## 현우님 프로젝트와의 관계
Claude Pro를 전략적 분석 도구로 활용. OpenClaw(Gemini)과 Claude의 하이브리드 구조 운영.

## 관련 개념
- [[LLM]]
- [[AI-Agent]]

## 최신 동향
- (학습 시 자동 추가)
EOF

log_ok "Entity files created (OpenClaw, n8n, Anthropic)"

# =============================================================================
# 4-B. Create GICS Reference
# =============================================================================
log_info "Creating GICS classification reference..."

cat > "$KB/07-Reference/GICS-Classification.md" <<'EOF'
---
type: reference
tags:
  - "#type/reference"
  - "#topic/finance"
updated: REPLACE_DATE
---

# GICS (Global Industry Classification Standard)

> MSCI와 S&P Dow Jones Indices가 개발한 글로벌 산업 분류 체계.
> 8자리 코드로 Sector → Industry Group → Industry → Sub-Industry 계층 구조.

## 코드 구조

```
45  10  30  20
|   |   |   |
|   |   |   +-- Sub-Industry (8자리) : Application Software
|   |   +------ Industry     (6자리) : Software
|   +---------- Industry Group (4자리): Software & Services
+-------------- Sector        (2자리) : Information Technology
```

## 11개 Sector

| 코드 | Sector | Industry Groups |
|------|--------|:-:|
| **10** | Energy | 1 |
| **15** | Materials | 1 |
| **20** | Industrials | 3 |
| **25** | Consumer Discretionary | 4 |
| **30** | Consumer Staples | 3 |
| **35** | Health Care | 2 |
| **40** | Financials | 3 |
| **45** | Information Technology | 3 |
| **50** | Communication Services | 2 |
| **55** | Utilities | 1 |
| **60** | Real Estate | 2 |

**총계**: 11 Sectors → 25 Industry Groups → 74 Industries → 163 Sub-Industries

## 상세 분류

### 10 - Energy
- **1010** Energy
  - 101010 Energy Equipment & Services
  - 101020 Oil, Gas & Consumable Fuels

### 15 - Materials
- **1510** Materials
  - 151010 Chemicals
  - 151020 Construction Materials
  - 151030 Containers & Packaging
  - 151040 Metals & Mining
  - 151050 Paper & Forest Products

### 20 - Industrials
- **2010** Capital Goods
  - 201010 Aerospace & Defense
  - 201020 Building Products
  - 201030 Construction & Engineering
  - 201040 Electrical Equipment
  - 201050 Industrial Conglomerates
  - 201060 Machinery
  - 201070 Trading Companies & Distributors
- **2020** Commercial & Professional Services
  - 202010 Commercial Services & Supplies
  - 202020 Professional Services
- **2030** Transportation
  - 203010 Air Freight & Logistics
  - 203020 Passenger Airlines
  - 203030 Marine Transportation
  - 203040 Ground Transportation
  - 203050 Transportation Infrastructure

### 25 - Consumer Discretionary
- **2510** Automobiles & Components
  - 251010 Automobile Components
  - 251020 Automobiles
- **2520** Consumer Durables & Apparel
  - 252010 Household Durables
  - 252020 Leisure Products
  - 252030 Textiles, Apparel & Luxury Goods
- **2530** Consumer Services
  - 253010 Hotels, Restaurants & Leisure
  - 253020 Diversified Consumer Services
- **2550** Consumer Discretionary Distribution & Retail
  - 255010 Distributors
  - 255030 Broadline Retail
  - 255040 Specialty Retail

### 30 - Consumer Staples
- **3010** Consumer Staples Distribution & Retail
  - 301010 Consumer Staples Distribution & Retail
- **3020** Food, Beverage & Tobacco
  - 302010 Beverages
  - 302020 Food Products
  - 302030 Tobacco
- **3030** Household & Personal Products
  - 303010 Household Products
  - 303020 Personal Care Products

### 35 - Health Care
- **3510** Health Care Equipment & Services
  - 351010 Health Care Equipment & Supplies
  - 351020 Health Care Providers & Services
  - 351030 Health Care Technology
- **3520** Pharmaceuticals, Biotechnology & Life Sciences
  - 352010 Biotechnology
  - 352020 Pharmaceuticals
  - 352030 Life Sciences Tools & Services

### 40 - Financials
- **4010** Banks
  - 401010 Banks
- **4020** Financial Services
  - 402010 Financial Services
  - 402020 Consumer Finance
  - 402030 Capital Markets
  - 402040 Mortgage REITs
- **4030** Insurance
  - 403010 Insurance

### 45 - Information Technology
- **4510** Software & Services
  - 451020 IT Services
  - 451030 Software
- **4520** Technology Hardware & Equipment
  - 452010 Communications Equipment
  - 452020 Technology Hardware, Storage & Peripherals
  - 452030 Electronic Equipment, Instruments & Components
- **4530** Semiconductors & Semiconductor Equipment
  - 453010 Semiconductors & Semiconductor Equipment

### 50 - Communication Services
- **5010** Telecommunication Services
  - 501010 Diversified Telecommunication Services
  - 501020 Wireless Telecommunication Services
- **5020** Media & Entertainment
  - 502010 Media
  - 502020 Entertainment
  - 502030 Interactive Media & Services

### 55 - Utilities
- **5510** Utilities
  - 551010 Electric Utilities
  - 551020 Gas Utilities
  - 551030 Multi-Utilities
  - 551040 Water Utilities
  - 551050 Independent Power & Renewable Electricity

### 60 - Real Estate
- **6010** Equity REITs
  - 601010 Diversified REITs
  - 601025 Industrial REITs
  - 601030 Hotel & Resort REITs
  - 601040 Office REITs
  - 601050 Health Care REITs
  - 601060 Residential REITs
  - 601070 Retail REITs
  - 601080 Specialized REITs
- **6020** Real Estate Management & Development
  - 602010 Real Estate Management & Development

## Vault에서의 활용

### 태그 규칙
- 기업 Entity 문서: `#GICS/{sector}/{industry_group}` 형태
- 예: `#GICS/45/4530` (NVIDIA - Semiconductors)
- 예: `#GICS/45/4510` (Anthropic - Software & Services)
- 예: `#GICS/50/5020` (Google - Media & Entertainment)

### Frontmatter 규칙
```yaml
gics:
  sector: "45 - Information Technology"
  industry_group: "4530 - Semiconductors & Semiconductor Equipment"
  industry: "453010 - Semiconductors & Semiconductor Equipment"
  sub_industry: "45301020 - Semiconductors"
```

### 관심 섹터 (현우님 프로젝트 기준)
1. **45 - IT**: AI 기업, 소프트웨어, 반도체 (핵심)
2. **50 - Communication Services**: 미디어, 엔터테인먼트, 인터랙티브
3. **40 - Financials**: 핀테크, 결제, 자산관리
4. **35 - Health Care**: 헬스테크, 바이오
5. **25 - Consumer Discretionary**: 이커머스, 자동차

## 참고
- MSCI GICS 공식: https://www.msci.com/indexes/index-resources/gics
- S&P Global: https://www.spglobal.com/spdji/en/landing/topic/gics/
- 최종 업데이트: 2023년 3월 (v12)
EOF

sed -i "s/REPLACE_DATE/$TODAY/g" "$KB/07-Reference/GICS-Classification.md"
log_ok "GICS classification reference created"

# =============================================================================
# 5. Seed Project Files
# =============================================================================
log_info "Creating project documents..."

cat > "$KB/06-Projects/OpenClaw-VPS-Setup.md" <<EOF
---
date: $TODAY
type: project
tags:
  - "#type/project"
  - "#topic/devops"
  - "#topic/AI"
  - "#status/growing"
---

# OpenClaw VPS Setup

## 개요
> Hostinger VPS에 OpenClaw AI 에이전트를 설치하고 자가학습 시스템을 구축하는 프로젝트

## 진행 상황
- [x] VPS 초기 설정 (Ubuntu 24.04)
- [x] OpenClaw Docker 설치
- [x] 텔레그램 봇 연동 (@ronclawBot)
- [x] 스킬 설치 (brave-search, tavily, github 등)
- [x] 자가학습 크론잡 설정
- [x] n8n Cloud 연동
- [x] Obsidian 지식 시스템 구축
- [ ] Git 동기화 설정 (VPS → GitHub → Obsidian)
- [ ] RAG 시스템 구축
- [ ] 멀티 에이전트 협업

## 핵심 정보
- **VPS**: Hostinger KVM 2 (8GB RAM, 100GB, 72.62.255.251)
- **컨테이너**: openclaw-openclaw-gateway-1
- **모델**: google/gemini-3-flash-preview
- **크론잡**: 5개 (모닝브리핑, 딥리서치, 데일리리뷰, 주간리포트, 서버점검)

## 관련 문서
- [[OpenClaw]]
- [[n8n]]
- [[MOC-DevOps]]
- [[MOC-Tech]]

## 7일 로드맵
- Day 1: 시스템 기반 구축 ✅
- Day 2-3: n8n 리서치 자동화
- Day 4-5: 지식 주입 (RAG)
- Day 6-7: 멀티 에이전트 협업
EOF

cat > "$KB/06-Projects/N8N-Automation.md" <<EOF
---
date: $TODAY
type: project
tags:
  - "#type/project"
  - "#topic/n8n"
  - "#status/growing"
---

# N8N Automation

## 개요
> n8n Cloud를 활용한 자동화 워크플로우 구축 프로젝트

## 워크플로우 목록
- [[News-Pipeline]] - 뉴스 자동 수집 (HN, TechCrunch, Verge, ZDNet)

## 진행 상황
- [x] n8n Cloud 설정 (mangd.app.n8n.cloud)
- [x] News Pipeline 워크플로우 생성
- [ ] Google Cloud 백업 연동
- [ ] Obsidian 동기화 워크플로우
- [ ] OpenClaw 웹훅 연동

## 관련 문서
- [[n8n]]
- [[OpenClaw]]
- [[Workflow-Automation]]
- [[MOC-N8N]]
EOF

log_ok "Project files created"

# =============================================================================
# 6. Create Templates
# =============================================================================
log_info "Creating document templates..."

cat > "$KB/templates/note-template.md" <<'EOF'
---
date: {{date}}
type: note
category: tech|finance|business|devops|n8n
tags:
  - "#topic/{{category}}/{{subtopic}}"
  - "#status/seed"
  - "#relevance/{{relevance}}"
source: "{{url_or_conversation}}"
created_by: Ron
---

# {{제목}}

## 요약
> {{3줄 이내 핵심 요약}}

## 핵심 내용
{{구조화된 학습 내용}}

## 현우님 맥락
{{실제 프로젝트에 어떻게 적용 가능한지}}

## 연결
- 관련 개념: [[{{Concept1}}]], [[{{Concept2}}]]
- 관련 도구: [[{{Entity1}}]]
- 관련 노트: [[{{Note1}}]]
- 상위 MOC: [[MOC-{{Category}}]]
EOF

cat > "$KB/templates/concept-template.md" <<'EOF'
---
date: {{date}}
type: concept
aliases: ["{{별칭1}}", "{{별칭2}}"]
tags:
  - "#type/concept"
  - "#topic/{{category}}"
  - "#status/growing"
---

# {{개념명}}

## 정의
> {{한 문장 정의}}

## 핵심 설명
{{개념의 상세 설명}}

## 하위 개념
- [[{{하위1}}]]
- [[{{하위2}}]]

## 관련 엔티티
- [[{{Entity1}}]] - {{관계 설명}}

## 관련 노트
- [[{{Note1}}]]

## 참고 자료
- {{URL 또는 출처}}
EOF

cat > "$KB/templates/entity-template.md" <<'EOF'
---
date: {{date}}
type: entity
entity_type: company|tool|person|project
aliases: ["{{별칭}}"]
tags:
  - "#type/entity"
  - "#topic/{{category}}"
website: "{{url}}"
---

# {{엔티티명}}

## 개요
> {{한 문장 설명}}

## 핵심 정보
- **유형**: {{company/tool/person}}
- **분야**: {{분야}}
- **특징**: {{핵심 특징}}

## 현우님 프로젝트와의 관계
{{어떻게 관련되는지}}

## 관련 개념
- [[{{Concept1}}]]

## 최신 동향
- {{날짜}}: {{최신 정보}}
EOF

cat > "$KB/templates/daily-template.md" <<'EOF'
---
date: {{date}}
type: daily
tags:
  - "#type/daily"
  - "#status/evergreen"
---

# {{date}} 일일 로그

## 오늘의 브리핑
{{모닝 브리핑 요약}}

## 학습한 것
- [[{{새로 만든 노트1}}]] - {{한 줄 요약}}

## 인사이트
{{대화에서 얻은 인사이트}}

## 내일 할 것
- [ ] {{액션1}}
- [ ] {{액션2}}

## 오늘의 연결
- {{기존 지식 A}}와 {{새 지식 B}}의 관계 발견: {{설명}}
EOF

log_ok "Templates created (note, concept, entity, daily)"

# =============================================================================
# 7. Create Obsidian Config
# =============================================================================
log_info "Creating Obsidian configuration..."

cat > "$KB/.obsidian/app.json" <<'EOF'
{
  "showLineNumber": true,
  "strictLineBreaks": false,
  "readableLineLength": true,
  "defaultViewMode": "source"
}
EOF

cat > "$KB/.obsidian/graph.json" <<'EOF'
{
  "collapse-filter": false,
  "search": "",
  "showTags": true,
  "showAttachments": false,
  "hideUnresolved": false,
  "showOrphans": true,
  "collapse-color-groups": false,
  "colorGroups": [
    {"query": "tag:#type/moc", "color": {"a": 1, "rgb": 16744448}},
    {"query": "tag:#type/concept", "color": {"a": 1, "rgb": 5614335}},
    {"query": "tag:#type/entity", "color": {"a": 1, "rgb": 65407}},
    {"query": "tag:#type/note", "color": {"a": 1, "rgb": 16776960}},
    {"query": "tag:#type/project", "color": {"a": 1, "rgb": 16711935}},
    {"query": "tag:#type/daily", "color": {"a": 1, "rgb": 8421504}}
  ],
  "collapse-display": false,
  "showArrow": true,
  "textFadeMultiplier": 0,
  "nodeSizeMultiplier": 1,
  "lineSizeMultiplier": 1,
  "collapse-forces": true,
  "centerStrength": 0.5,
  "repelStrength": 10,
  "linkStrength": 1,
  "linkDistance": 250
}
EOF

log_ok "Obsidian config created"

# =============================================================================
# 8. Create Initial Daily Log
# =============================================================================
log_info "Creating initial daily log..."

cat > "$KB/04-Daily/$TODAY.md" <<EOF
---
date: $TODAY
type: daily
tags:
  - "#type/daily"
  - "#status/evergreen"
---

# $TODAY 일일 로그

## 오늘의 브리핑
Obsidian 지식 시스템 구축 완료. OpenClaw 자가학습 시스템과 연동.

## 학습한 것
- [[OpenClaw-VPS-Setup]] - VPS에 AI 에이전트 설치 및 자가학습 시스템 구축
- [[Workflow-Automation]] - n8n 뉴스 파이프라인 구축

## 인사이트
Obsidian 온톨로지 구조를 적용하면 단순 마크다운 저장을 넘어 지식 그래프 형태의 연결된 학습이 가능하다.

## 내일 할 것
- [ ] n8n News Pipeline 워크플로우 활성화
- [ ] Git 동기화 설정 (VPS → GitHub)
- [ ] 첫 번째 자동 학습 결과 확인

## 오늘의 연결
- [[AI-Agent]]와 [[Workflow-Automation]]의 관계: OpenClaw 에이전트가 n8n 워크플로우를 트리거하고, 결과를 지식 베이스에 저장하는 순환 구조
EOF

log_ok "Daily log created"

# =============================================================================
# 9. Fix Ownership
# =============================================================================
log_info "Setting permissions..."
chown -R 1000:1000 "$KB"
chmod -R 755 "$KB"
log_ok "Permissions set (UID 1000)"

# =============================================================================
# 10. Update Knowledge Manager Skill
# =============================================================================
log_info "Updating knowledge-manager skill..."

SKILL_SRC="$SCRIPT_DIR/skills/knowledge-manager/openclaw.md"
SKILL_DST="/home/openclaw/.openclaw/skills/knowledge-manager/openclaw.md"

if [ -f "$SKILL_SRC" ]; then
    cp "$SKILL_SRC" "$SKILL_DST"
    chown 1000:1000 "$SKILL_DST"
    log_ok "Knowledge manager skill updated"
else
    log_warn "Skill source not found at $SKILL_SRC - skip"
fi

# =============================================================================
# 11. Restart Gateway
# =============================================================================
log_info "Restarting gateway to load updated skills..."
cd /opt/openclaw && docker compose restart openclaw-gateway
sleep 5
log_ok "Gateway restarted"

# =============================================================================
# Summary
# =============================================================================
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   Obsidian Vault Ready!                    ${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# Count files
TOTAL=$(find "$KB" -name "*.md" | wc -l)
MOC_COUNT=$(find "$KB/00-MOC" -name "*.md" | wc -l)
CONCEPT_COUNT=$(find "$KB/01-Concepts" -name "*.md" | wc -l)
ENTITY_COUNT=$(find "$KB/02-Entities" -name "*.md" | wc -l)

echo -e "  ${YELLOW}Vault Location:${NC} $KB"
echo -e "  ${YELLOW}Total Files:${NC} $TOTAL"
echo -e "  ${YELLOW}MOC:${NC} $MOC_COUNT | ${YELLOW}Concepts:${NC} $CONCEPT_COUNT | ${YELLOW}Entities:${NC} $ENTITY_COUNT"
echo ""
echo -e "  ${YELLOW}Structure:${NC}"
echo -e "    00-MOC/          - Dashboard, Tech, Finance, Business, DevOps, N8N"
echo -e "    01-Concepts/     - AI-Agent, LLM, Workflow-Automation"
echo -e "    02-Entities/     - OpenClaw, n8n, Anthropic"
echo -e "    03-Notes/        - tech/, finance/, business/, devops/, n8n/"
echo -e "    04-Daily/        - $TODAY.md"
echo -e "    05-Weekly/       - (ready)"
echo -e "    06-Projects/     - OpenClaw-VPS-Setup, N8N-Automation"
echo -e "    07-Reference/    - GICS-Classification (산업 분류 코드표)"
echo -e "    templates/       - note, concept, entity, daily"
echo -e "    .obsidian/       - graph.json (color-coded by type)"
echo ""
echo -e "  ${YELLOW}Next Steps:${NC}"
echo -e "    1. Git init: cd $KB && git init && git remote add origin <repo>"
echo -e "    2. First push: git add -A && git commit -m 'init vault' && git push"
echo -e "    3. Obsidian: Install 'Obsidian Git' plugin, set repo URL"
echo -e "    4. Ron에게: '옵시디언 볼트 확인해줘' 로 연동 테스트"
echo ""
