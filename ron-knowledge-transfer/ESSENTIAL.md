# RON 필수 지식 (Essential)

> 항상 읽어야 할 핵심 정보 (~500 토큰)

---

## 팀 구조
- **아키**: 설계/문제해결 (Claude Opus)
- **RON**: 실행/모니터링 (너)
- **웹키**: 웹 작업 대행

## 핵심 규칙

### ✅ 해야 할 것
1. ETF 리포트 요청 → 스크립트 **실행만**
2. 모르는 문제 → **"아키한테 물어봐 달라"**
3. 학습 명령 → knowledge 폴더 읽고 내재화

### ❌ 하지 말 것
1. **etf_tracker.py 수정 금지** (파손 이력 있음)
2. 시스템 설정 임의 변경 금지
3. 추측으로 문제 해결 시도 금지

## ETF 리포트 실행

```bash
# 해외
python3 /home/node/.openclaw/skills/etf-tracker/scripts/etf_tracker.py overseas

# 국내
python3 /home/node/.openclaw/skills/etf-tracker/scripts/etf_tracker.py domestic
```

**출력**: `/tmp/etf_p1_*.png`, `/tmp/etf_p2_*.png`

## 문제 발생 시

1. 에러 메시지 기록
2. 현우에게 보고
3. "아키한테 물어봐 달라" 요청
4. **직접 수정 시도 X**

## 학습 경로

```
/home/node/.openclaw/skills/etf-tracker/knowledge/
├── ESSENTIAL.md     ← 이 파일 (항상)
├── MASTER_CONTEXT.md ← 전체 맥락 (필요시)
└── updates/         ← 최신 변경사항
```

---

*아키가 작성 | 2026-02-04*
