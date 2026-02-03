#!/usr/bin/env python3
"""
ETF Tracker 자동화 실행 스크립트
RON이 cron/n8n을 통해 호출하는 엔트리포인트

사용법:
    python3 run_etf_tracker.py domestic   # 국내 ETF (월~금 16:00 KST)
    python3 run_etf_tracker.py overseas   # 해외 ETF (화~토 08:00 KST)
    python3 run_etf_tracker.py --force domestic  # 공휴일 무시하고 실행

환경변수:
    ANTHROPIC_API_KEY: Claude API 키 (Deep Research용)
    TG_BOT_TOKEN: Telegram 봇 토큰 (기본값 내장)
    TG_CHANNEL_ID: Telegram 채널 ID (기본값 내장)
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
import argparse

# ─── 설정 ─────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "8310012683:AAFf7Ut9xut6WofPAQemNvf-A4CRi6ttkVs")
CHANNEL_ID = os.environ.get("TG_CHANNEL_ID", "-1002796769091")

# 스크립트 경로
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

import etf_tracker
from etf_tracker import DOMESTIC_KEYS, OVERSEAS_KEYS

# ─── 공휴일 데이터 ────────────────────────────────────────────────────
# 2026년 한국 공휴일 (KRX 휴장일)
KOREAN_HOLIDAYS_2026 = {
    "2026-01-01",  # 신정
    "2026-02-16", "2026-02-17", "2026-02-18",  # 설날
    "2026-03-01",  # 삼일절
    "2026-05-05",  # 어린이날
    "2026-05-24",  # 부처님오신날
    "2026-06-06",  # 현충일
    "2026-08-15",  # 광복절
    "2026-09-26", "2026-09-27", "2026-09-28",  # 추석
    "2026-10-03",  # 개천절
    "2026-10-09",  # 한글날
    "2026-12-25",  # 성탄절
}

# 2026년 미국 공휴일 (NYSE 휴장일)
US_HOLIDAYS_2026 = {
    "2026-01-01",  # New Year's Day
    "2026-01-19",  # MLK Day
    "2026-02-16",  # Presidents Day
    "2026-04-03",  # Good Friday
    "2026-05-25",  # Memorial Day
    "2026-06-19",  # Juneteenth
    "2026-07-03",  # Independence Day (observed)
    "2026-09-07",  # Labor Day
    "2026-11-26",  # Thanksgiving
    "2026-12-25",  # Christmas
}


def is_korean_business_day(date_str: str) -> bool:
    """한국 영업일 체크 (월~금, 공휴일 제외)"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    # 주말 체크
    if dt.weekday() >= 5:  # 토(5), 일(6)
        return False
    # 공휴일 체크
    if date_str in KOREAN_HOLIDAYS_2026:
        return False
    return True


def is_us_business_day(date_str: str) -> bool:
    """미국 영업일 체크 (월~금 US시간, 공휴일 제외)

    참고: 한국 화~토 오전 = 미국 월~금 장 마감 후
    따라서 한국 날짜 기준으로 전날 미국 영업일 체크
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    # 한국 기준 화~토 = 미국 월~금
    # 한국 화요일 = 미국 월요일 장 마감 후
    us_date = dt - timedelta(days=1)  # 전날 미국 날짜
    us_date_str = us_date.strftime("%Y-%m-%d")

    # 미국 주말 체크 (토, 일)
    if us_date.weekday() >= 5:
        return False
    # 미국 공휴일 체크
    if us_date_str in US_HOLIDAYS_2026:
        return False
    return True


def send_to_telegram(images: list, summary: str) -> bool:
    """Telegram 채널로 이미지와 분석 전송"""
    success = True

    # 1. 이미지 전송
    if images:
        media = []
        for i, img_path in enumerate(images):
            media.append({
                'type': 'photo',
                'media': f'attach://photo{i}'
            })

        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body_parts = []

        body_parts.append(f'--{boundary}')
        body_parts.append('Content-Disposition: form-data; name="chat_id"')
        body_parts.append('')
        body_parts.append(CHANNEL_ID)

        body_parts.append(f'--{boundary}')
        body_parts.append('Content-Disposition: form-data; name="media"')
        body_parts.append('')
        body_parts.append(json.dumps(media))

        body_str = '\r\n'.join(body_parts)
        body = body_str.encode('utf-8')

        for i, img_path in enumerate(images):
            with open(img_path, 'rb') as f:
                file_data = f.read()
            file_part = f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="photo{i}"; filename="photo{i}.png"\r\nContent-Type: image/png\r\n\r\n'.encode('utf-8')
            body = body + file_part + file_data

        body = body + f'\r\n--{boundary}--\r\n'.encode('utf-8')

        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMediaGroup'
        req = urllib.request.Request(url, data=body, headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                print("[OK] Images sent to channel")
        except Exception as e:
            print(f"[ERROR] Image send failed: {e}")
            success = False

    # 2. 분석 텍스트 전송
    msg_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = urllib.parse.urlencode({
        'chat_id': CHANNEL_ID,
        'text': summary,
        'parse_mode': 'HTML'
    }).encode()
    req = urllib.request.Request(msg_url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            if result.get('ok'):
                print("[OK] Analysis sent to channel")
            else:
                print(f"[ERROR] Analysis send failed: {result}")
                success = False
    except Exception as e:
        print(f"[ERROR] Analysis send failed: {e}")
        success = False

    return success


def log_execution(market: str, date: str, success: bool, skip_reason: str = None):
    """실행 로그를 Obsidian에 기록 (RON 학습용)"""
    log_dir = os.path.join(SCRIPT_DIR, "..", "knowledge", "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"{date[:7]}_execution.md")  # 월별 로그

    # 기존 로그 읽기 또는 새로 생성
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = f"""# ETF Tracker 실행 로그 - {date[:7]}

| 날짜 | 시간 | 마켓 | 상태 | 비고 |
|------|------|------|------|------|
"""

    # 새 로그 추가
    now = datetime.now().strftime("%H:%M:%S")
    status = "✅ 성공" if success else "❌ 실패"
    note = skip_reason or ""

    new_entry = f"| {date} | {now} | {market} | {status} | {note} |\n"

    # 테이블 헤더 다음에 삽입
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("|---"):
            lines.insert(i + 1, new_entry.strip())
            break

    with open(log_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[LOG] Execution logged to {log_file}")


def main():
    parser = argparse.ArgumentParser(description="ETF Tracker 자동 실행")
    parser.add_argument("market", choices=["domestic", "overseas", "국내", "해외"],
                        help="실행할 마켓 (domestic/overseas)")
    parser.add_argument("--force", action="store_true",
                        help="공휴일 무시하고 강제 실행")
    parser.add_argument("--dry-run", action="store_true",
                        help="실제 전송 없이 테스트")
    args = parser.parse_args()

    # 마켓 정규화
    market = args.market
    if market in ["domestic", "국내"]:
        market = "domestic"
        etf_keys = DOMESTIC_KEYS
        market_label = "국내"
    else:
        market = "overseas"
        etf_keys = OVERSEAS_KEYS
        market_label = "해외"

    today = datetime.now().strftime("%Y-%m-%d")
    print(f"═══════════════════════════════════════")
    print(f"  ETF Tracker - {market_label} ({today})")
    print(f"═══════════════════════════════════════")

    # 영업일 체크
    if not args.force:
        if market == "domestic":
            if not is_korean_business_day(today):
                reason = "한국 휴장일"
                print(f"[SKIP] {reason} - 실행 건너뜀")
                log_execution(market_label, today, True, f"스킵: {reason}")
                return 0
        else:  # overseas
            if not is_us_business_day(today):
                reason = "미국 휴장일"
                print(f"[SKIP] {reason} - 실행 건너뜀")
                log_execution(market_label, today, True, f"스킵: {reason}")
                return 0

    # ETF 분석 실행
    print(f"\n[RUN] ETF 분석 시작: {etf_keys}")
    try:
        report, images, summary = etf_tracker.run(etf_keys)
        print(f"[OK] 분석 완료 - 이미지 {len(images)}개 생성")
    except Exception as e:
        print(f"[ERROR] 분석 실패: {e}")
        log_execution(market_label, today, False, str(e))
        return 1

    # Telegram 전송
    if args.dry_run:
        print("\n[DRY-RUN] Telegram 전송 스킵")
        print("\n=== SUMMARY ===")
        print(summary[:500] + "...")
        success = True
    else:
        print("\n[SEND] Telegram 채널로 전송 중...")
        success = send_to_telegram(images, summary)

    # 로그 기록
    log_execution(market_label, today, success)

    if success:
        print(f"\n✅ {market_label} ETF 리포트 전송 완료!")
    else:
        print(f"\n❌ {market_label} ETF 리포트 전송 실패")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
