# Knowledge Manager - 지식 관리 시스템

학습한 지식을 체계적으로 저장, 검색, 연결하는 스킬입니다.

## 지식 베이스 경로

`/home/node/.openclaw/workspace/knowledge/`

## 디렉토리 구조

```
knowledge/
├── tech/          # AI, 프로그래밍, 개발 도구
├── finance/       # 금융, 투자, 시장 분석
├── business/      # 비즈니스 전략, 마케팅
├── devops/        # 서버, 인프라, Docker, VPS
├── n8n/           # n8n 워크플로우, 자동화 패턴
├── insights/      # 대화에서 도출한 인사이트
├── daily/         # 일일 학습 로그
├── weekly/        # 주간 종합 리포트
└── index.md       # 전체 지식 인덱스
```

## 지식 저장 규칙

### 파일명 규칙
`{YYYY-MM-DD}_{주제_slug}.md`
예: `2026-02-02_openclaw-vps-setup.md`

### 문서 형식
```markdown
---
date: YYYY-MM-DD
category: tech|finance|business|devops|n8n|insights
tags: [tag1, tag2, tag3]
source: url 또는 conversation
relevance: high|medium|low
---

# {주제}

## 요약
(3줄 이내)

## 핵심 내용
(구조화된 내용)

## 현우님 맥락
(실제 프로젝트에 적용 가능한 방법)

## 관련 지식
- [[관련 문서1]]
- [[관련 문서2]]
```

## 명령어 처리

### 저장
"이거 기억해줘" / "저장해줘" → 대화 내용을 적절한 카테고리에 저장

### 검색
"~에 대해 알고 있는 거 알려줘" → knowledge/ 디렉토리에서 관련 파일 검색

### 목록
"지식 목록" / "뭐 배웠어?" → 카테고리별 저장된 지식 목록 표시

### 연결
"~와 ~의 관계" → 여러 지식을 연결하여 인사이트 도출

### 인덱스 갱신
저장/삭제 시 `index.md` 자동 업데이트

## 인덱스 형식 (index.md)

```markdown
# Knowledge Index

Last updated: {timestamp}
Total documents: {count}

## By Category
- tech: {count}개
- finance: {count}개
...

## Recent (최근 10개)
1. [{date}] {title} - {category}
...

## Most Referenced
1. {title} (referenced {n} times)
...
```

## 자동 정리

### 매주 일요일
- 중복 문서 감지 및 병합
- 오래된 저관련 문서 아카이브 제안
- 인덱스 갱신
- 주간 학습 리포트 생성

### 매월 1일
- 월간 지식 성장 리포트
- 카테고리별 트렌드 분석
- 지식 갭 분석 (학습이 부족한 영역 제안)
