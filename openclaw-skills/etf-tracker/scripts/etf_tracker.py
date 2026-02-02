#!/usr/bin/env python3
"""
TIMEFOLIO ETF Holdings Tracker v2
- Telegram-optimized formatting (no tables)
- Multi-period comparison (1일/1개월/3개월 via AJAX API)
- 증감 TOP 5 (increase/decrease)
- News analysis prompts for significant movers
"""

import urllib.request
import urllib.parse
import json
import re
import os
import sys
from datetime import datetime, timedelta

# ─── ETF Configuration ───────────────────────────────────────────────
ETFS = {
    "NQ100":         {"idx": 2,  "name": "미국나스닥100액티브",     "flag": "\U0001f1fa\U0001f1f8", "cate": "001"},
    "CN_AI":         {"idx": 19, "name": "차이나AI테크액티브",     "flag": "\U0001f1e8\U0001f1f3", "cate": "001"},
    "GLOBAL_AI":     {"idx": 6,  "name": "글로벌AI인공지능액티브", "flag": "\U0001f916", "cate": "001"},
    "KOSPI_ACTIVE":  {"idx": 11, "name": "코스피액티브",           "flag": "\U0001f1f0\U0001f1f7", "cate": "001"},
    "K_CULTURE":     {"idx": 1,  "name": "K컬처액티브",           "flag": "\U0001f3ac", "cate": "001"},
    "K_BIO":         {"idx": 13, "name": "K바이오액티브",          "flag": "\U0001f9ec", "cate": "001"},
}

OVERSEAS_KEYS = ["NQ100", "CN_AI", "GLOBAL_AI"]
DOMESTIC_KEYS = ["KOSPI_ACTIVE", "K_CULTURE", "K_BIO"]

BASE_URL = "https://timeetf.co.kr/m11_view.php"
AJAX_URL = "https://timeetf.co.kr/past_pdf_json.php"
DATA_DIR = os.path.expanduser("~/.openclaw/workspace/knowledge/03-Portfolio/etf_data")


# ─── Fetching ─────────────────────────────────────────────────────────
def fetch_page(idx, cate="001"):
    url = f"{BASE_URL}?idx={idx}&cate={cate}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; OpenClaw/1.0)"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def fetch_period_comparison(idx, period):
    """Fetch comparison data via AJAX. period: pdfM1, pdfM3, pdfM6, pdfY1"""
    data = urllib.parse.urlencode({"period": period, "idx": idx}).encode()
    req = urllib.request.Request(AJAX_URL, data=data, headers={
        "User-Agent": "Mozilla/5.0 (compatible; OpenClaw/1.0)"
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


# ─── Parsing ──────────────────────────────────────────────────────────
def parse_date(html):
    match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})', html)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return datetime.now().strftime("%Y-%m-%d")


def parse_full_holdings(html):
    holdings = []
    table_match = re.search(
        r'<table[^>]*class="table3 moreList1"[^>]*>(.*?)</table>', html, re.DOTALL
    )
    if not table_match:
        return holdings
    tbody = table_match.group(1)
    rows = re.findall(r'<tr>\s*(.*?)\s*</tr>', tbody, re.DOTALL)
    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        if len(cells) >= 5:
            code = cells[0].strip()
            name = cells[1].strip()
            shares_str = cells[2].strip().replace(",", "")
            value_str = cells[3].strip().replace(",", "")
            weight_str = cells[4].strip()
            try:
                holdings.append({
                    "code": code, "name": name,
                    "shares": int(shares_str) if shares_str else 0,
                    "value": int(value_str) if value_str else 0,
                    "weight": float(weight_str) if weight_str else 0.0,
                })
            except ValueError:
                continue
    return holdings


# ─── Storage ──────────────────────────────────────────────────────────
def ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def save_data(etf_key, date, holdings):
    ensure_dir()
    fp = os.path.join(DATA_DIR, f"{etf_key}_{date}.json")
    with open(fp, "w", encoding="utf-8") as f:
        json.dump({
            "etf": etf_key, "date": date,
            "fetched_at": datetime.now().isoformat(),
            "holdings": holdings,
        }, f, ensure_ascii=False, indent=2)


def load_data(etf_key, date_str):
    """Load data for a specific date."""
    fp = os.path.join(DATA_DIR, f"{etf_key}_{date_str}.json")
    if os.path.exists(fp):
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_prev(etf_key, current_date):
    """Load most recent previous data."""
    ensure_dir()
    target = f"{etf_key}_{current_date}.json"
    files = sorted([
        f for f in os.listdir(DATA_DIR)
        if f.startswith(f"{etf_key}_") and f.endswith(".json") and f != target
    ], reverse=True)
    if files:
        with open(os.path.join(DATA_DIR, files[0]), "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# ─── Comparison ───────────────────────────────────────────────────────
def build_diff(today_list, prev_list):
    """Compare two holdings lists, return sorted changes."""
    if not prev_list:
        return []
    prev_map = {h["name"]: h["weight"] for h in prev_list}
    today_map = {h["name"]: h["weight"] for h in today_list}
    changes = []

    for name, w in today_map.items():
        pw = prev_map.get(name, 0)
        diff = round(w - pw, 2)
        if abs(diff) >= 0.1:
            changes.append({"name": name, "weight": w, "prev": pw, "diff": diff,
                            "new": name not in prev_map})

    for name, pw in prev_map.items():
        if name not in today_map and pw >= 0.3:
            changes.append({"name": name, "weight": 0, "prev": pw,
                            "diff": round(-pw, 2), "removed": True})

    changes.sort(key=lambda x: x["diff"], reverse=True)
    return changes


# ─── Formatting (Telegram-optimized) ─────────────────────────────────
def fmt_change(diff, new=False, removed=False):
    if new:
        return "NEW"
    if removed:
        return "OUT"
    sign = "+" if diff > 0 else ""
    return f"{sign}{diff:.2f}%p"


def fmt_etf_block(etf_key, holdings, m1_data, m3_data, daily_changes, date):
    """Format a single ETF block for Telegram."""
    cfg = ETFS[etf_key]
    flag = cfg["flag"]
    name = cfg["name"]
    lines = []

    lines.append(f"{flag} TIME {name}")
    lines.append(f"   {len(holdings)}종목 | 기준일 {date}")
    lines.append("")

    # ── 1개월 비교: 증감 TOP 5 ──
    if m1_data and "today" in m1_data:
        today_items = m1_data["today"]
        # Separate increases, decreases, new
        ups = []
        downs = []
        news = []
        for item in today_items:
            nm = item["prodNm"]
            w = float(item["wei"])
            inc = item.get("increaseWei", "0")
            if inc == "\uc2e0\uaddc" or inc == "신규":
                news.append({"name": nm, "weight": w})
            else:
                try:
                    val = float(inc)
                    if val > 0:
                        ups.append({"name": nm, "weight": w, "diff": val})
                    elif val < 0:
                        downs.append({"name": nm, "weight": w, "diff": val})
                except ValueError:
                    pass

        ups.sort(key=lambda x: x["diff"], reverse=True)
        downs.sort(key=lambda x: x["diff"])

        if ups:
            lines.append("\u2191 \ube44\uc911 \uc99d\uac00 TOP 5 (1\uac1c\uc6d4)")
            for i, item in enumerate(ups[:5], 1):
                bar = "\u2588" * min(int(item["diff"] * 2), 10)
                lines.append(f"  {i}. {item['name']}")
                lines.append(f"     {item['weight']:.2f}%  +{item['diff']:.2f}%p {bar}")
            lines.append("")

        if downs:
            lines.append("\u2193 \ube44\uc911 \uac10\uc18c TOP 5 (1\uac1c\uc6d4)")
            for i, item in enumerate(downs[:5], 1):
                bar = "\u2591" * min(int(abs(item["diff"]) * 2), 10)
                lines.append(f"  {i}. {item['name']}")
                lines.append(f"     {item['weight']:.2f}%  {item['diff']:.2f}%p {bar}")
            lines.append("")

        if news:
            names = ", ".join(f"{n['name']}({n['weight']:.1f}%)" for n in news)
            lines.append(f"\u2b50 \uc2e0\uaddc \ud3b8\uc785: {names}")
            lines.append("")

    # ── 3개월 비교 요약 ──
    if m3_data and "today" in m3_data:
        items3 = m3_data["today"]
        ups3 = []
        downs3 = []
        for item in items3:
            inc = item.get("increaseWei", "0")
            if inc == "\uc2e0\uaddc" or inc == "신규":
                continue
            try:
                val = float(inc)
                if val > 0:
                    ups3.append({"name": item["prodNm"], "diff": val})
                elif val < 0:
                    downs3.append({"name": item["prodNm"], "diff": val})
            except ValueError:
                pass
        ups3.sort(key=lambda x: x["diff"], reverse=True)
        downs3.sort(key=lambda x: x["diff"])

        parts = []
        if ups3:
            top = ups3[0]
            parts.append(f"\u2191 {top['name']} +{top['diff']:.1f}%p")
        if downs3:
            bot = downs3[0]
            parts.append(f"\u2193 {bot['name']} {bot['diff']:.1f}%p")
        if parts:
            lines.append(f"\u23f3 3\uac1c\uc6d4 \ube44\uad50: {' | '.join(parts)}")
            lines.append("")

    # ── 전일 비교 (from stored data) ──
    if daily_changes:
        big = [c for c in daily_changes if abs(c["diff"]) >= 0.5]
        if big:
            ups_d = [c for c in big if c["diff"] > 0][:3]
            downs_d = [c for c in big if c["diff"] < 0]
            downs_d.sort(key=lambda x: x["diff"])
            downs_d = downs_d[:3]

            d_parts = []
            for c in ups_d:
                tag = " NEW" if c.get("new") else ""
                d_parts.append(f"\u2191{c['name']} +{c['diff']:.2f}%p{tag}")
            for c in downs_d:
                tag = " OUT" if c.get("removed") else ""
                d_parts.append(f"\u2193{c['name']} {c['diff']:.2f}%p{tag}")
            lines.append(f"\U0001f4c5 \uc804\uc77c\ub300\ube44: {', '.join(d_parts)}")
            lines.append("")

    return "\n".join(lines)


def build_news_section(all_movers):
    """Build news analysis section for stocks with large changes."""
    if not all_movers:
        return ""

    # Deduplicate and sort by absolute diff
    seen = {}
    for m in all_movers:
        key = m["name"]
        if key not in seen or abs(m["diff"]) > abs(seen[key]["diff"]):
            seen[key] = m
    top_movers = sorted(seen.values(), key=lambda x: abs(x["diff"]), reverse=True)[:10]

    if not top_movers:
        return ""

    lines = [
        "",
        "\u2500" * 28,
        "\U0001f50d \ub274\uc2a4 \ubd84\uc11d \ub300\uc0c1 \uc885\ubaa9",
        "",
    ]

    for i, m in enumerate(top_movers, 1):
        direction = "\u2191\ube44\uc911\uc99d\uac00" if m["diff"] > 0 else "\u2193\ube44\uc911\uac10\uc18c"
        etf = m.get("etf_name", "")
        diff_str = f"+{m['diff']:.2f}" if m["diff"] > 0 else f"{m['diff']:.2f}"
        lines.append(f"{i}. {m['name']} ({etf})")
        lines.append(f"   {direction} {diff_str}%p | {m['weight']:.2f}%")

        # Generate search suggestion and speculation
        if m["diff"] > 2:
            lines.append(f"   \u27a1 \uac80\uc0c9: \"{m['name']} \uc2e4\uc801 \ud638\uc7ac \uc131\uc7a5\"")
            lines.append(f"   \U0001f4ad \ucd94\uce21: \uc2e4\uc801 \uac1c\uc120 \ub610\ub294 \uc131\uc7a5 \uae30\ub300\uac10\uc73c\ub85c \uc6b4\uc6a9\uc5ed \ube44\uc911 \ud655\ub300")
        elif m["diff"] > 0:
            lines.append(f"   \u27a1 \uac80\uc0c9: \"{m['name']} \uc8fc\uac00 \uc0c1\uc2b9 \uc774\uc720\"")
            lines.append(f"   \U0001f4ad \ucd94\uce21: \uc12c\ud130 \uc131\uc7a5 \ub610\ub294 \ubcf8\uc5c5 \uae30\ub300\uac10 \ubc18\uc601")
        elif m["diff"] < -2:
            lines.append(f"   \u27a1 \uac80\uc0c9: \"{m['name']} \uc545\uc7ac \ub9ac\uc2a4\ud06c \ub17c\ub780\"")
            lines.append(f"   \U0001f4ad \ucd94\uce21: \uc2e4\uc801 \ubd80\uc9c4 \ub610\ub294 \ubc38\ub958\uc5d0\uc774\uc158 \ubd80\ub2f4\uc73c\ub85c \uc6b4\uc6a9\uc5ed \ube44\uc911 \ucd95\uc18c")
        else:
            lines.append(f"   \u27a1 \uac80\uc0c9: \"{m['name']} \uc8fc\uac00 \ud558\ub77d \uc774\uc720\"")
            lines.append(f"   \U0001f4ad \ucd94\uce21: \ucc28\uc775\uc2e4\ud604 \ub610\ub294 \uc139\ud130 \ud68c\uc804 \uc804\ub7b5")
        lines.append("")

    lines.append("\u203c \uc704 \uc885\ubaa9\ub4e4\uc758 \ucd5c\uadfc \ub274\uc2a4\ub97c \uac80\uc0c9\ud558\uc5ec")
    lines.append("   \uc6b4\uc6a9\uc5ed\uc758 \ube44\uc911 \ubcc0\ub3d9 \uc0ac\uc720\ub97c \ubd84\uc11d\ud574\uc8fc\uc138\uc694.")

    return "\n".join(lines)


# ─── Main ─────────────────────────────────────────────────────────────
def run(etf_keys=None):
    if etf_keys is None:
        etf_keys = list(ETFS.keys())

    date = None
    blocks = []
    all_movers = []
    errors = []

    for key in etf_keys:
        if key not in ETFS:
            errors.append(f"Unknown ETF: {key}")
            continue

        cfg = ETFS[key]
        try:
            # 1. Fetch page & parse
            html = fetch_page(cfg["idx"], cfg["cate"])
            page_date = parse_date(html)
            if date is None:
                date = page_date
            holdings = parse_full_holdings(html)

            # 2. Save today's data
            save_data(key, page_date, holdings)

            # 3. Fetch AJAX comparisons (1M, 3M)
            m1 = fetch_period_comparison(cfg["idx"], "pdfM1")
            m3 = fetch_period_comparison(cfg["idx"], "pdfM3")

            # 4. Load previous day for daily comparison
            prev = load_prev(key, page_date)
            daily_changes = build_diff(holdings, prev["holdings"] if prev else None)

            # 5. Format block
            block = fmt_etf_block(key, holdings, m1, m3, daily_changes, page_date)
            blocks.append(block)

            # 6. Collect significant movers for news section
            if m1 and "today" in m1:
                for item in m1["today"]:
                    inc = item.get("increaseWei", "0")
                    if inc in ("신규", "\uc2e0\uaddc"):
                        val = float(item["wei"])
                    else:
                        try:
                            val = float(inc)
                        except ValueError:
                            continue
                    if abs(val) >= 2.0:
                        all_movers.append({
                            "name": item["prodNm"],
                            "weight": float(item["wei"]),
                            "diff": val if inc not in ("신규", "\uc2e0\uaddc") else float(item["wei"]),
                            "etf_name": cfg["name"],
                        })

        except Exception as e:
            errors.append(f"{key}: {e}")

    # Build final report
    # Determine group label
    keys_set = set(etf_keys)
    if keys_set <= set(OVERSEAS_KEYS):
        group = "\U0001f30f \ud574\uc678"
    elif keys_set <= set(DOMESTIC_KEYS):
        group = "\U0001f1f0\U0001f1f7 \uad6d\ub0b4"
    else:
        group = "\uc804\uccb4"

    header = (
        f"\U0001f4ca TIMEFOLIO {group} ETF \ub9ac\ud3ec\ud2b8\n"
        f"\U0001f4c5 {date or 'unknown'}\n"
        f"{'=' * 28}"
    )

    separator = "\n" + "\u2500" * 28 + "\n"
    body = separator.join(blocks)

    news = build_news_section(all_movers)

    report = f"{header}\n\n{body}"
    if news:
        report += f"\n{news}"
    if errors:
        report += "\n\n\u26a0 Errors: " + ", ".join(errors)

    return report


if __name__ == "__main__":
    args = sys.argv[1:]
    # Support group shortcuts
    if args == ["overseas"] or args == ["해외"]:
        args = OVERSEAS_KEYS
    elif args == ["domestic"] or args == ["국내"]:
        args = DOMESTIC_KEYS
    print(run(args if args else None))
