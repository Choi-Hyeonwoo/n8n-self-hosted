#!/usr/bin/env python3
"""
RON 토큰 사용량 모니터링 및 알림
Claude Code가 주기적으로 실행하여 RON 다이어트 판단

Usage:
    python3 ron_usage_monitor.py check     # 현재 상태 확인
    python3 ron_usage_monitor.py alert     # 임계치 초과 시 알림
    python3 ron_usage_monitor.py report    # 일일 리포트
"""

import os
import json
import sys
from datetime import datetime

USAGE_FILE = "/root/.openclaw/workspace/USAGE.md"
COST_THRESHOLD_DAILY = 5.0  # $5/일 임계치

# Claude API 가격 (Sonnet 4)
PRICE_INPUT = 3.0 / 1_000_000   # $3/1M tokens
PRICE_OUTPUT = 15.0 / 1_000_000  # $15/1M tokens


def parse_usage_file():
    """USAGE.md에서 사용량 파싱"""
    if not os.path.exists(USAGE_FILE):
        return None

    with open(USAGE_FILE, "r") as f:
        content = f.read()

    # 간단한 파싱 (테이블에서 마지막 행)
    lines = content.split("\n")
    for line in reversed(lines):
        if "|" in line and "$" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 5:
                try:
                    input_tokens = int(parts[2].replace(",", ""))
                    output_tokens = int(parts[3].replace(",", ""))
                    return {
                        "input": input_tokens,
                        "output": output_tokens,
                        "cost": input_tokens * PRICE_INPUT + output_tokens * PRICE_OUTPUT
                    }
                except:
                    pass
    return None


def check_status():
    """현재 상태 확인"""
    usage = parse_usage_file()
    if not usage:
        print("⚠️ RON 사용량 데이터 없음")
        return

    ratio = usage["input"] / max(usage["output"], 1)

    print("═══════════════════════════════════════")
    print("  RON 토큰 사용량 현황")
    print("═══════════════════════════════════════")
    print(f"  Input:  {usage['input']:,} tokens")
    print(f"  Output: {usage['output']:,} tokens")
    print(f"  Ratio:  {ratio:.0f}:1 {'⚠️ 비정상' if ratio > 100 else '✅ 정상'}")
    print(f"  Cost:   ${usage['cost']:.2f}")
    print("═══════════════════════════════════════")

    # 진단
    if ratio > 100:
        print("\n🔍 진단: Input 과다 - 컨텍스트 로딩 문제")
        print("   → RON에게 '/compact' 명령 권장")

    if usage["cost"] > COST_THRESHOLD_DAILY:
        print(f"\n🚨 경고: 일일 비용 ${COST_THRESHOLD_DAILY} 초과!")


def alert():
    """임계치 초과 알림"""
    usage = parse_usage_file()
    if not usage:
        return

    if usage["cost"] > COST_THRESHOLD_DAILY:
        print(f"🚨 RON 비용 경고: ${usage['cost']:.2f} (임계치: ${COST_THRESHOLD_DAILY})")
        print("권장 조치: RON 컨텍스트 압축 또는 세션 리셋")
        sys.exit(1)

    ratio = usage["input"] / max(usage["output"], 1)
    if ratio > 500:
        print(f"⚠️ RON Input/Output 비율 비정상: {ratio:.0f}:1")
        print("권장 조치: 불필요한 파일 참조 제거")
        sys.exit(1)

    print("✅ RON 사용량 정상 범위")


def report():
    """일일 리포트"""
    usage = parse_usage_file()
    if not usage:
        print("데이터 없음")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    print(f"""
📊 RON 일일 사용량 리포트 ({today})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input Tokens:  {usage['input']:>10,}
Output Tokens: {usage['output']:>10,}
Total Cost:    ${usage['cost']:>9.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

월간 예상 (22일 기준): ${usage['cost'] * 22:.2f}
""")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"

    if cmd == "check":
        check_status()
    elif cmd == "alert":
        alert()
    elif cmd == "report":
        report()
    else:
        print(f"Unknown command: {cmd}")
