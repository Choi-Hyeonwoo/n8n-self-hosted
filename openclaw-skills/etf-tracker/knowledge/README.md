# ETF Tracker Knowledge Base

RON이 TIMEFOLIO ETF 분석을 통해 축적하는 시장 지식 온톨로지입니다.

## 구조

```
knowledge/
├── daily/           # 일별 분석 리포트
│   ├── 2026-02-02_domestic.md
│   └── 2026-02-02_overseas.md
├── stocks/          # 종목별 프로필 & 히스토리
│   ├── Sandisk.md
│   ├── NVIDIA.md
│   └── SK하이닉스.md
├── etfs/            # ETF별 전략 추적
│   ├── 미국나스닥100액티브.md
│   └── 코스피액티브.md
└── themes/          # 테마별 트렌드
    ├── AI.md
    ├── 반도체.md
    └── 바이오.md
```

## 링크 규칙 (Obsidian Wikilinks)

- 종목 참조: `[[stocks/Sandisk]]`
- ETF 참조: `[[etfs/미국나스닥100액티브]]`
- 테마 참조: `[[themes/AI]]`
- 일별 리포트: `[[daily/2026-02-02_overseas]]`

## 자동 업데이트

ETF 분석 실행 시 자동으로:
1. 일별 리포트 저장
2. 종목 히스토리 업데이트
3. 테마 트렌드 갱신
