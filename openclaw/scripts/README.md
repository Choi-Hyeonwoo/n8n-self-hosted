# OpenClaw Multi-Agent Scripts

VPS 환경에서 여러 Claude Code/RON 인스턴스 협업을 위한 스크립트 모음.

## 컴포넌트

### 1. execute_smart.py - Self-Healing Executor
에러 발생 시 자동으로 분석하고 수정된 명령어로 재시도.

```bash
# 기본 사용
python3 execute_smart.py "npm install package"

# 최대 재시도 횟수 지정
python3 execute_smart.py --max-retries 5 "docker build ."

# JSON 출력
python3 execute_smart.py --json "apt-get update"
```

**작동 원리:**
1. 명령어 실행
2. 실패 시 에러 분석 (Claude/OpenAI API)
3. 수정된 명령어로 재시도
4. 성공 또는 최대 횟수 도달 시 종료

### 2. janitor.sh - System Cleanup
Docker, 로그, 임시파일 정리 및 시스템 상태 모니터링.

```bash
# 상태 확인만
./janitor.sh --check

# 일반 정리
./janitor.sh

# 공격적 정리 (디스크 부족 시)
./janitor.sh --aggressive
```

**정리 대상:**
- Docker: 중지된 컨테이너, dangling 이미지, 미사용 볼륨
- 로그: 오래된 로그 파일, 과대 로그 truncate
- 임시: /tmp, npm/pip 캐시, apt 캐시

### 3. brain_sync.js - Multi-Agent Communication
여러 Claude Code 인스턴스 간 전략/컨텍스트 동기화.

```bash
# 전략 추가
node brain_sync.js push "ETF 분석 실행" --priority high

# 대기 중인 전략 확인
node brain_sync.js pull --status pending

# 전략 완료 표시
node brain_sync.js complete <strategy-id>

# 컨텍스트 공유
node brain_sync.js share "current_task" "RON ETF tracker setup"

# 공유 컨텍스트 읽기
node brain_sync.js get current_task

# 에이전트 등록
node brain_sync.js register my-agent claude-code

# 전체 상태
node brain_sync.js status

# 실시간 감시 모드
node brain_sync.js watch
```

## 2개 Claude Code 창 사용법

### 창 1 (Claude Code A)
```bash
# 에이전트 등록
node brain_sync.js register claude-a claude-code

# 작업 추가
node brain_sync.js push "API 서버 구현" --priority high --source claude-a
```

### 창 2 (Claude Code B)
```bash
# 에이전트 등록
node brain_sync.js register claude-b claude-code

# 대기 중인 작업 확인
node brain_sync.js pull

# 작업 완료 시
node brain_sync.js complete <id>
```

## 환경 변수

```bash
# execute_smart.py
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...       # fallback

# brain_sync.js
export BRAIN_SYNC_DIR=/custom/path/.brain
export AGENT_ID=my-custom-agent
```

## 로그 위치

- `/var/log/execute_smart.log` - 자가 복구 실행 로그
- `/var/log/janitor.log` - 시스템 정리 로그
- `/tmp/janitor_report.json` - 최근 정리 리포트
