# Knowledge Manager - Obsidian 온톨로지 지식 시스템

학습한 지식을 옵시디언(Obsidian) 호환 형식으로 체계적으로 저장하고, 그래프 구조로 연결하는 스킬입니다.
현우님의 **기존 Obsidian Vault (Google Drive)**에 통합하여 운영합니다.

## 핵심 원칙

1. 모든 문서는 옵시디언 호환 마크다운 (.md)
2. YAML frontmatter 필수 (메타데이터)
3. [[위키링크]]로 문서 간 연결 (그래프 뷰 활용)
4. 태그는 계층형 (#카테고리/하위주제)
5. MOC(Map of Content) 패턴으로 인덱싱
6. **기존 Vault 구조를 유지**하며 Ron의 지식을 통합

## 지식 베이스 경로

**통합 경로** (bind mount로 아래 두 경로는 동일한 물리 디렉토리):
- **VPS 호스트**: `/home/openclaw/.openclaw/workspace/knowledge/`
- **Obsidian MCP**: `/opt/mcp-servers/obsidian-vault-data/` (bind mount)
- **컨테이너 내부**: `/home/node/.openclaw/workspace/knowledge/`

**최종 목적지**: Google Drive > Obsidian Vault (n8n 자동 동기화)

## Vault 폴더 구조

```
knowledge/                             # 통합 Vault Root
├── 00-Inbox/                          # 빠른 메모, 미분류 노트
├── 01-Daily/                          # 일일 마켓 노트 (YYYY-MM-DD.md)
├── 02-Research/                       # 심층 분석
│   ├── Stocks/                        # 개별 종목 (NVIDIA.md 등)
│   ├── Sectors/                       # GICS 섹터 분석
│   └── Macro/                         # 금리, 환율, 경제지표
├── 03-Portfolio/                      # 포트폴리오 추적
├── 04-Knowledge/                      # 영구 지식
│   ├── Concepts/                      # 개념/용어 (GICS, 밸류에이션 등)
│   └── Strategies/                    # 투자 전략, 매매 규칙
├── 05-Templates/                      # 노트 템플릿
├── 06-Archive/                        # 보관함
└── Home.md                            # Vault 인덱스
```

## VPS → Google Drive 동기화 매핑

| VPS 폴더 | → Google Drive 경로 | 설명 |
|-----------|---------------------|------|
| `00-Inbox/` | `00. Inbox/` | 미분류 노트 |
| `01-Daily/` | `10. Daily Notes/11. Daily/` | 일일 마켓 로그 |
| `02-Research/Stocks/` | `200. Sectors/{GICS}/` | 종목 → GICS 자동 라우팅 |
| `02-Research/Sectors/` | `200. Sectors/` | 섹터 분석 |
| `02-Research/Macro/` | `100. Research/` | 매크로 리서치 |
| `04-Knowledge/` | `100. Research/` | 개념/전략 |
| `05-Templates/` | `90. Template/` | 문서 템플릿 |

### GICS → Vault 섹터 매핑 (기업 Entity 자동 라우팅)

기업(company) Entity는 GICS 코드에 따라 `200. Sectors/` 하위의 정확한 폴더로 자동 라우팅됩니다.

| GICS 코드 | GICS 섹터 | → Vault 폴더 |
|-----------|-----------|-------------|
| 10 | Energy | `200. Sectors/210. Energy/` |
| 15 | Materials | `200. Sectors/225. Materials/` |
| 20 | Industrials | `200. Sectors/220. Industrials/` |
| 25 | Consumer Discretionary | `200. Sectors/230. Consumer/` |
| 30 | Consumer Staples | `200. Sectors/230. Consumer/` |
| 35 | Health Care | `200. Sectors/240. Health Care/` |
| 40 | Financials | `200. Sectors/250. Financials/` |
| 45 | Information Technology | `200. Sectors/260. Information Technology/` |
| 50 | Communication Services | `200. Sectors/270. Communication Services/` |
| 55 | Utilities | `200. Sectors/280. Utilities/` |
| 60 | Real Estate | `200. Sectors/290. Real Estate/` |

**IT 세부 분류:**
| GICS 코드 | Industry Group | → Vault 폴더 |
|-----------|---------------|-------------|
| 4510 | Software & Services | `260. Information Technology/261. Software & Services/` |
| 4520 | Technology Hardware | `260. Information Technology/262. Technology Hardware/` |
| 4530 | Semiconductors | `260. Information Technology/263. Semiconductors/` |

## 온톨로지 스키마

### 노드 타입 (문서 유형)
- **Concept**: 추상 개념 (AI 에이전트, 자동화, RAG 등)
- **Entity**: 구체적 대상 (OpenClaw, n8n, NVIDIA 등)
- **Note**: 학습/분석 노트
- **Daily**: 일일 로그
- **Project**: 프로젝트 문서
- **MOC**: Map of Content (인덱스)

### 관계 타입 (링크 의미)
- `[[개념]]` - 관련 개념 참조
- `[[개념|별칭]]` - 별칭으로 참조
- 부모-자식: MOC → 하위 문서
- 관련: Note ↔ Note, Concept ↔ Entity

### 태그 계층 (Nested Tags)
```
#type/concept    #type/entity    #type/note    #type/daily
#topic/AI        #topic/AI/agent  #topic/AI/LLM
#topic/finance   #topic/finance/stock  #topic/finance/crypto
#topic/devops    #topic/devops/docker  #topic/devops/vps
#topic/n8n       #topic/n8n/workflow
#status/seed     #status/growing  #status/evergreen
#relevance/high  #relevance/medium  #relevance/low
```

### GICS 산업 분류 태그 (기업 엔티티 전용)

기업(Entity) 문서에는 GICS(Global Industry Classification Standard) 태그를 부여한다.
8자리 코드 체계: Sector(2) → Industry Group(4) → Industry(6) → Sub-Industry(8)

```
#GICS/10          # Energy
#GICS/15          # Materials
#GICS/20          # Industrials
#GICS/25          # Consumer Discretionary
#GICS/30          # Consumer Staples
#GICS/35          # Health Care
#GICS/40          # Financials
#GICS/45          # Information Technology
#GICS/45/4510     # Software & Services
#GICS/45/4520     # Technology Hardware & Equipment
#GICS/45/4530     # Semiconductors
#GICS/50          # Communication Services
#GICS/55          # Utilities
#GICS/60          # Real Estate
```

**기업 Entity 문서에서 GICS 사용 예시:**
```yaml
# NVIDIA 문서의 frontmatter
gics:
  sector: "45 - Information Technology"
  industry_group: "4530 - Semiconductors & Semiconductor Equipment"
  industry: "453010 - Semiconductors & Semiconductor Equipment"
  sub_industry: "45301020 - Semiconductors"
tags:
  - "#type/entity"
  - "#GICS/45/4530"
```

**GICS 분류 규칙:**
1. 모든 기업 Entity에 `gics:` frontmatter 필수
2. 태그는 Sector + Industry Group 수준까지만 (깊이 2)
3. 상세 코드는 frontmatter에 기록
4. 분류가 불확실한 경우 주요 매출원 기준으로 판단
5. GICS 전체 코드표는 `07-Reference/GICS-Classification.md` 참조

## 문서 템플릿

### 학습 노트 (Note)
```markdown
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
```

### 개념 문서 (Concept)
```markdown
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
- [[{{Entity2}}]] - {{관계 설명}}

## 관련 노트
- [[{{Note1}}]]

## 참고 자료
- {{URL 또는 출처}}
```

### 엔티티 문서 (Entity)
```markdown
---
date: {{date}}
type: entity
entity_type: company|tool|person|project
aliases: ["{{별칭}}"]
tags:
  - "#type/entity"
  - "#topic/{{category}}"
  - "#GICS/{{sector_code}}/{{industry_group_code}}"
gics:
  sector: "{{sector_code}} - {{sector_name}}"
  industry_group: "{{ig_code}} - {{ig_name}}"
  industry: "{{ind_code}} - {{ind_name}}"
  sub_industry: "{{sub_code}} - {{sub_name}}"
website: "{{url}}"
---

# {{엔티티명}}

## 개요
> {{한 문장 설명}}

## 핵심 정보
- **유형**: {{company/tool/person}}
- **분야**: {{분야}}
- **GICS**: {{sector_name}} > {{ig_name}} > {{ind_name}}
- **특징**: {{핵심 특징}}

## 현우님 프로젝트와의 관계
{{어떻게 관련되는지}}

## 관련 개념
- [[{{Concept1}}]]

## 같은 GICS 섹터
- [[{{같은_섹터_기업1}}]]
- [[{{같은_섹터_기업2}}]]

## 최신 동향
- {{날짜}}: {{최신 정보}}
```

> **GICS 분류 참고**: entity_type이 `company`인 경우에만 GICS 태그와 frontmatter를 추가한다.
> `tool`, `person`, `project` 타입은 GICS 생략 가능.

### 일일 로그 (Daily)
```markdown
---
date: {{date}}
type: daily
tags:
  - "#type/daily"
  - "#status/evergreen"
---

# {{date}} 일일 로그

## 📊 오늘의 브리핑
{{모닝 브리핑 요약}}

## 🧠 학습한 것
- [[{{새로 만든 노트1}}]] - {{한 줄 요약}}
- [[{{새로 만든 노트2}}]] - {{한 줄 요약}}

## 💡 인사이트
{{대화에서 얻은 인사이트}}

## 📋 내일 할 것
- [ ] {{액션1}}
- [ ] {{액션2}}

## 🔗 오늘의 연결
- {{기존 지식 A}}와 {{새 지식 B}}의 관계 발견: {{설명}}
```

### MOC (Map of Content)
```markdown
---
type: moc
tags:
  - "#type/moc"
updated: {{date}}
---

# MOC - {{카테고리}}

> {{카테고리 설명}}

## 핵심 개념
- [[{{Concept1}}]] - {{한 줄 설명}}
- [[{{Concept2}}]] - {{한 줄 설명}}

## 주요 엔티티
- [[{{Entity1}}]]
- [[{{Entity2}}]]

## 최근 노트
- [[{{최근노트1}}]] ({{날짜}})
- [[{{최근노트2}}]] ({{날짜}})

## 프로젝트
- [[{{Project1}}]]
```

## /save 명령어 처리 로직

사용자가 `/save tech AI 에이전트의 미래`를 보내면:

1. **카테고리 분석**: `tech` → `#topic/AI`
2. **개념 추출**: "AI 에이전트" → [[AI-Agent]] 개념 문서 확인
   - 없으면 → `04-Knowledge/Concepts/AI-Agent.md` 생성
3. **노트 생성**: `00-Inbox/2026-02-02_AI-에이전트의-미래.md`
   - YAML frontmatter 자동 생성
   - [[AI-Agent]] 위키링크 자동 삽입
   - → Google Drive `00. Inbox/`에 동기화
4. **일일 로그 업데이트**: `01-Daily/2026-02-02.md`에 학습 기록 추가

### /save entity 처리 (기업 문서)

사용자가 `/save entity NVIDIA`를 보내면:
1. **GICS 분류**: NVIDIA → GICS 45 (IT) → 4530 (Semiconductors)
2. **Entity 생성**: `02-Research/Stocks/NVIDIA.md`
3. **자동 라우팅**: GICS 4530 → Google Drive `200. Sectors/260. Information Technology/263. Semiconductors/`에 동기화
4. **섹터 내 같은 기업 링크**: 같은 섹터 기업들과 `[[링크]]` 연결

## 동기화 전략 (VPS → Google Drive Vault)

### 동기화 체계
```
VPS knowledge/ (= obsidian-vault-data/)
├── Obsidian MCP (port 3104) ←→ 직접 읽기/쓰기
├── n8n 워크플로우 ──→ Google Drive Obsidian/
│   (03:00, 15:00 자동 / 웹훅 수동)
│   (폴더 매핑 + GICS 라우팅)
└── OpenClaw 컨테이너 ←→ 직접 읽기/쓰기 (/home/node/.openclaw/workspace/knowledge/)
```

### n8n Google Drive 동기화 (Primary)
- 매일 03:00, 15:00 자동 실행
- VPS에서 변경된 .md 파일 감지 (timestamp)
- 폴더 매핑 테이블에 따라 정확한 Google Drive 폴더에 업로드
- 기업 Entity는 GICS 코드로 자동 라우팅
- 텔레그램 리포트 알림

## 그래프 최적화

### 허브 문서 (가장 많이 연결될 문서)
- [[AI-Agent]] - AI 에이전트 관련 모든 것의 허브
- [[n8n]] - 자동화 관련 허브
- [[OpenClaw]] - 현재 프로젝트의 중심
- [[현우님-프로젝트]] - 모든 실무 연결의 중심

### 고아 문서 방지
- 모든 노트는 최소 1개의 [[링크]]와 1개의 MOC 참조 필수
- 주간 정리 시 고아 문서 감지 → 연결 제안

## 상태 진화 (Evergreen Notes)
- `#status/seed` → 방금 생성, 미완성
- `#status/growing` → 내용 추가 중, 연결 확장 중
- `#status/evergreen` → 충분히 성숙, 정기 업데이트만
