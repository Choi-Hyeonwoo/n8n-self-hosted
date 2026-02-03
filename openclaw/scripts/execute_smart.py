#!/usr/bin/env python3
"""
Self-Healing Execution Wrapper for RON
에러 발생 시 자동 분석 및 수정된 명령어로 재시도

Usage:
    python3 execute_smart.py "npm install something"
    python3 execute_smart.py --max-retries 5 "docker build ."
"""

import subprocess
import sys
import os
import json
import argparse
from datetime import datetime

# LLM API 설정 (Claude 또는 OpenAI)
def get_llm_fix(command: str, error: str) -> str:
    """LLM에게 에러 분석 및 수정 명령어 요청"""

    prompt = f"""내가 실행한 명령어: `{command}`
발생한 에러:
```
{error[:2000]}
```
Ubuntu/Debian 환경이다. 이 에러를 해결하기 위해 수정된 명령어만 딱 한 줄로 줘.
설명 없이 실행 가능한 셸 명령어만. 패키지 설치가 필요하면 apt-get install -y 포함."""

    # Try Claude API first
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip().replace('`', '')
        except Exception as e:
            log(f"Claude API 실패: {e}")

    # Fallback to OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai
            openai.api_key = openai_key
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip().replace('`', '')
        except Exception as e:
            log(f"OpenAI API 실패: {e}")

    # Fallback: 일반적인 수정 시도
    return suggest_basic_fix(command, error)


def suggest_basic_fix(command: str, error: str) -> str:
    """LLM 없이 기본 수정 제안"""
    error_lower = error.lower()

    # 패키지 없음
    if "command not found" in error_lower:
        missing = error.split("command not found")[0].split()[-1].replace(":", "")
        return f"apt-get update && apt-get install -y {missing} && {command}"

    # 권한 문제
    if "permission denied" in error_lower:
        return f"sudo {command}"

    # npm 문제
    if "npm err" in error_lower or "eacces" in error_lower:
        return f"npm cache clean --force && {command}"

    # pip 문제
    if "pip" in command and "externally-managed" in error_lower:
        return command.replace("pip install", "pip install --break-system-packages")

    # 디스크 공간
    if "no space left" in error_lower:
        return f"docker system prune -f && rm -rf /tmp/* && {command}"

    # 메모리 부족
    if "cannot allocate memory" in error_lower or "killed" in error_lower:
        return f"sync && echo 3 > /proc/sys/vm/drop_caches && {command}"

    # 네트워크 문제
    if "could not resolve" in error_lower or "connection refused" in error_lower:
        return f"sleep 5 && {command}"

    return command  # 수정 불가 - 원본 반환


LOG_FILE = "/var/log/execute_smart.log"

def log(msg: str):
    """로그 기록"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass


def run_command(command: str, attempt: int = 1, max_retries: int = 3, history: list = None) -> dict:
    """명령어 실행 및 자동 복구"""
    if history is None:
        history = []

    log(f"실행 시도 ({attempt}/{max_retries}): {command}")

    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=300  # 5분 타임아웃
    )

    history.append({
        "attempt": attempt,
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout[:1000] if result.stdout else "",
        "stderr": result.stderr[:1000] if result.stderr else ""
    })

    if result.returncode == 0:
        log("✅ 성공!")
        return {
            "success": True,
            "output": result.stdout,
            "attempts": attempt,
            "history": history
        }

    log(f"❌ 실패! (Exit Code: {result.returncode})")
    log(f"에러: {result.stderr[:500]}")

    if attempt >= max_retries:
        log("⚠️ 최대 재시도 횟수 초과. 중단합니다.")
        return {
            "success": False,
            "error": result.stderr,
            "attempts": attempt,
            "history": history
        }

    # Self-Healing: 수정된 명령어 생성
    log("🔧 에러 분석 중...")
    fixed_command = get_llm_fix(command, result.stderr)

    if fixed_command == command:
        log("수정 불가 - 동일 명령어로 재시도")
    else:
        log(f"🔄 수정된 명령어: {fixed_command}")

    # 재귀 호출로 재시도
    return run_command(fixed_command, attempt + 1, max_retries, history)


def main():
    parser = argparse.ArgumentParser(description="Self-Healing Command Executor")
    parser.add_argument("command", nargs="+", help="실행할 명령어")
    parser.add_argument("--max-retries", "-r", type=int, default=3, help="최대 재시도 횟수")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 출력")

    args = parser.parse_args()
    command = " ".join(args.command)

    try:
        result = run_command(command, max_retries=args.max_retries)
    except subprocess.TimeoutExpired:
        result = {"success": False, "error": "Timeout (300s)", "attempts": 1}
    except Exception as e:
        result = {"success": False, "error": str(e), "attempts": 1}

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
