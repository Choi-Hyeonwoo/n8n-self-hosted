# Knowledge Learning Skill - 지식사랑방 학습 시스템

지식사랑방 텔레그램 채널에서 수집된 지식을 학습하고 활용하는 스킬입니다.

## 아키텍처

```
지식사랑방 (Telegram)
    ↓ webhook
n8n Workflow
    ↓ Google Drive 업로드
    ↓ RON 학습 트리거 (HTTP POST to :8768/learn)
RON Learning Server
    ↓ knowledge/ 폴더에 저장
RON (OpenClaw)
    → 학습된 지식 활용
```

## 지식 폴더 구조

```
~/.openclaw/workspace/knowledge/
├── 01-일반토론/
├── 02-AI기술/
├── 03-투자전략/
├── 04-개발노트/
├── 05-독서노트/
├── 06-시장분석/
├── 07-아이디어/
├── 08-프로젝트/
├── 09-학습자료/
├── 10-인사이트/
├── 11-뉴스공유/
├── 12-질문답변/
├── 13-리서치/
├── 14-회고록/
└── 99-기타/
```

## 명령어

### 최근 학습 내용 확인
```bash
# 학습 로그 확인
cat ~/.openclaw/workspace/LEARNING_LOG.md | tail -30

# 최근 학습된 파일 목록
find ~/.openclaw/workspace/knowledge -name "*.md" -mtime -1 | head -20
```

### 특정 토픽의 지식 검색
```bash
# AI기술 관련 학습 내용
ls -la ~/.openclaw/workspace/knowledge/02-AI기술/

# 특정 키워드로 검색
grep -r "키워드" ~/.openclaw/workspace/knowledge/
```

### 학습 상태 확인
```bash
# 학습 서버 상태
curl -s http://172.17.0.1:8768/status | jq .

# 학습된 파일 목록
curl -s http://172.17.0.1:8768/knowledge | jq .
```

## Google Drive 연동

지식사랑방 콘텐츠는 Google Drive에도 저장됩니다.

### 토픽별 폴더 ID 매핑
| Thread ID | 토픽명 | Google Drive Folder ID |
|-----------|--------|----------------------|
| 2 | 일반토론 | 1ElawYn7WHWjOKZwJMPE_u2Weqp1_988G |
| 4 | AI기술 | 1vT_EhvjFuZ1QhyMWSr3gp-pdHZ_9dBXR |
| 14 | 투자전략 | 163idlblhh3YdKCjFIeGKj3kxe5et3VRZ |
| 81 | 개발노트 | 1DKaevA7QlMloqyfrAk2ENqgVbqwyG73G |
| 83 | 독서노트 | 1ydV3NnqRgc7IVrv8BnnMS4czrKMMlzs8 |
| 136 | 시장분석 | 1rVdWfZZIehJ2hMmW7oVxtiz9afp2JrbP |
| 147 | 아이디어 | 1UWimpISHlS3O-vPu7PLaTPpfOVCbF6oh |
| 170 | 프로젝트 | 1XAmNFJiHD1rYLCwrc_pVcA7oCfA5O0qr |
| 171 | 학습자료 | 11VKbtM20uYh3eHQqMgNDDnd7j3_zCv74 |
| 179 | 인사이트 | 10AqsptixxTJ8MQ5wPcYmPSXMsAQsSYht |
| 520 | 뉴스공유 | 1hCotZ_yQVSXu8LhSG2_a-BXU1nvoCNFo |
| 619 | 질문답변 | 1lK9cx_VafSiYGU5nRl4_lYQrSK5-plC3 |
| 4681 | 리서치 | 15cGUb5hwoMRJeqB_pAUxjFRY7cw0Q6q- |
| 11370 | 회고록 | 1WnVoWCTCk1JxT8KTAGERkgWiugg_Q1Lk |
| 19852 | 기타 | 1AaLxyWt6S_Fv76AbPdfP_RdzxvNtEN7B |

## 활용 시나리오

### 1. 현우님이 질문할 때
현우님이 특정 주제에 대해 질문하면, 해당 토픽 폴더에서 관련 지식을 검색하여 참조합니다.

```bash
# 예: "AI 에이전트 관련 내용 알려줘"
grep -rli "에이전트" ~/.openclaw/workspace/knowledge/02-AI기술/ | head -5
```

### 2. 데일리 브리프에 활용
최근 학습된 인사이트를 데일리 브리프에 포함합니다.

### 3. 투자 분석 시
시장분석, 투자전략 토픽의 학습 내용을 참조합니다.

## 주의사항

- 학습된 내용의 출처는 항상 "지식사랑방"으로 명시
- 개인적인 메모나 민감한 정보는 외부에 공유하지 않음
- Google Drive의 원본 파일 ID를 통해 필요시 원본 접근 가능
