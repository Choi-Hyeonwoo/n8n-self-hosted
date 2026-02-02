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

**VPS 작업 경로**: `/home/openclaw/.openclaw/workspace/knowledge/`
**최종 목적지**: Google Drive > Obsidian Vault (n8n 자동 동기화)

## 기존 Vault 구조 (Google Drive)

현우님의 기존 Obsidian Vault는 이미 GICS 기반 섹터 분류 체계를 갖추고 있습니다.

```
Obsidian/                              # Google Drive Root
├── 00. Inbox/                         # 일반 노트, 메모
│   ├── 05. Telegram/                  # 텔레그램 저장
│   └── 07. Clippings/                 # 웹 클리핑
├── 050. Book/                         # 도서 노트
│   └── 51. 도서 목록/
├── 10. Daily Notes/                   # 일일/주간 기록
│   ├── 11. Daily/                     # 일일 로그
│   └── 12. Weekly/                    # 주간 리포트
├── 100. Research/                     # 리서치/개념 문서
│   ├── 110. Asset Class/              # 자산군별 리서치
│   ├── 120. Strategy/                 # 투자 전략
│   └── 130. Geographic/               # 지역별 리서치
├── 200. Sectors/                      # ★ GICS 기반 섹터 분류
│   ├── 210. Energy/                   # GICS 10
│   ├── 220. Industrials/              # GICS 20
│   ├── 225. Materials/                # GICS 15
│   ├── 230. Consumer/                 # GICS 25+30 (Discretionary + Staples)
│   ├── 240. Health Care/              # GICS 35
│   ├── 250. Financials/               # GICS 40
│   ├── 260. Information Technology/   # GICS 45
│   │   ├── 261. Software & Services/  # GICS 4510
│   │   ├── 262. Technology Hardware/  # GICS 4520
│   │   └── 263. Semiconductors/       # GICS 4530
│   ├── 270. Communication Services/   # GICS 50
│   ├── 280. Utilities/                # GICS 55
│   └── 290. Real Estate/              # GICS 60
├── 90. Template/                      # 문서 템플릿
├── 99. Attachment/                    # 첨부파일
├── Clippings/                         # 클리핑 (Readwise 등)
├── Guides/                            # 가이드 문서
└── .obsidian/                         # 옵시디언 설정
```

## VPS → Vault 폴더 매핑

Ron이 VPS에서 생성하는 파일이 Google Drive Vault의 어느 폴더로 동기화되는지:

| VPS 경로 | → Vault 경로 | 설명 |
|-----------|-------------|------|
| `00-MOC/` | Vault Root (`/`) | MOC 파일은 루트 레벨 |
| `01-Concepts/` | `100. Research/` | 핵심 개념 → 리서치 폴더 |
| `02-Entities/` | `200. Sectors/{GICS}/` | 기업 → GICS 섹터별 자동 분류 |
| `03-Notes/` | `00. Inbox/` | 일반 노트 → 인박스 |
| `04-Daily/` | `10. Daily Notes/11. Daily/` | 일일 로그 |
| `05-Weekly/` | `10. Daily Notes/12. Weekly/` | 주간 리포트 |
| `06-Projects/` | Vault Root (`/`) | 프로젝트 문서 |
| `07-Reference/` | `100. Research/` | 참조 자료 → 리서치 |
| `templates/` | `90. Template/` | 문서 템플릿 |

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
   - 없으면 → `01-Concepts/AI-Agent.md` 생성 → Google Drive `100. Research/`에 동기화
3. **노트 생성**: `03-Notes/tech/2026-02-02_AI-에이전트의-미래.md`
   - YAML frontmatter 자동 생성
   - [[AI-Agent]] 위키링크 자동 삽입
   - [[MOC-Tech]] 참조 추가
   - → Google Drive `00. Inbox/`에 동기화
4. **MOC 업데이트**: `00-MOC/MOC-Tech.md`에 새 노트 링크 추가 → Vault Root에 동기화
5. **일일 로그 업데이트**: `04-Daily/2026-02-02.md`에 학습 기록 추가 → `10. Daily Notes/11. Daily/`에 동기화

### /save entity 처리 (기업 문서)

사용자가 `/save entity NVIDIA`를 보내면:
1. **GICS 분류**: NVIDIA → GICS 45 (IT) → 4530 (Semiconductors)
2. **Entity 생성**: `02-Entities/NVIDIA.md`
3. **자동 라우팅**: GICS 4530 → `200. Sectors/260. Information Technology/263. Semiconductors/`에 동기화
4. **섹터 내 같은 기업 링크**: 같은 `263. Semiconductors/` 내 기업들과 `[[링크]]` 연결

## 동기화 전략 (VPS → Google Drive Vault)

### 이중 동기화 체계
```
VPS knowledge/                        Google Drive Obsidian/
├── 생성/수정 감지                    ├── 00. Inbox/
│                                     ├── 10. Daily Notes/
├─── n8n 워크플로우 ──────────────→  ├── 100. Research/
│    (폴더 매핑 + GICS 라우팅)       ├── 200. Sectors/{GICS}/
│                                     └── ...
├─── Git push ──→ GitHub ──→ Obsidian Git 플러그인 ──→ 로컬 Mac
```

### 방법 1: n8n Google Drive 직접 동기화 (Primary)
- 매일 03:00, 15:00 자동 실행
- VPS에서 변경된 .md 파일 감지 (timestamp + git diff)
- 폴더 매핑 테이블에 따라 정확한 Google Drive 폴더에 업로드
- 기업 Entity는 GICS 코드로 자동 라우팅
- 텔레그램 리포트 알림

### 방법 2: Git 자동 동기화 (Backup)
```bash
cd /home/openclaw/.openclaw/workspace/knowledge
git add -A
git commit -m "knowledge update $(date +%Y-%m-%d-%H%M)" 2>/dev/null
git push origin main 2>/dev/null
```
→ GitHub Private Repo → Obsidian Git 플러그인으로 로컬 Mac에서도 접근 가능

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
