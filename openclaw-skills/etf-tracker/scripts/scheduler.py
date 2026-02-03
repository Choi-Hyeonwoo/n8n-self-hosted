#!/usr/bin/env python3
"""
ETF Tracker 스케줄러
systemd/cron 없이 백그라운드에서 스케줄 실행

스케줄:
- 국내: 월~금 17:00 KST (장 마감 후 데이터 업데이트 대기)
- 해외: 화~토 08:00 KST

실행:
  nohup python3 scheduler.py > /var/log/etf_scheduler.log 2>&1 &
"""

import os
import sys
import time
import threading
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# 환경변수 설정
if os.path.exists("/etc/etf-tracker.env"):
    with open("/etc/etf-tracker.env") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key] = val

import run_etf_tracker


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


def should_run_domestic(now):
    """국내: 월(0)~금(4) 17:00"""
    return now.weekday() <= 4 and now.hour == 17 and now.minute == 0


def should_run_overseas(now):
    """해외: 화(1)~토(5) 08:00"""
    return 1 <= now.weekday() <= 5 and now.hour == 8 and now.minute == 0


def run_task(market):
    """별도 스레드에서 실행"""
    log(f"Starting {market} ETF analysis...")
    try:
        sys.argv = ["run_etf_tracker.py", market]
        result = run_etf_tracker.main()
        log(f"{market} completed with exit code {result}")
    except Exception as e:
        log(f"{market} failed: {e}")


def main():
    log("═══════════════════════════════════════")
    log("  ETF Tracker Scheduler Started")
    log("═══════════════════════════════════════")
    log("Schedule:")
    log("  - Domestic: Mon-Fri 17:00 KST")
    log("  - Overseas: Tue-Sat 08:00 KST")
    log("")

    last_run = {"domestic": None, "overseas": None}

    while True:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")

        # 국내 체크
        if should_run_domestic(now) and last_run["domestic"] != today:
            last_run["domestic"] = today
            thread = threading.Thread(target=run_task, args=("domestic",))
            thread.start()

        # 해외 체크
        if should_run_overseas(now) and last_run["overseas"] != today:
            last_run["overseas"] = today
            thread = threading.Thread(target=run_task, args=("overseas",))
            thread.start()

        # 1분마다 체크
        time.sleep(60)


if __name__ == "__main__":
    main()
