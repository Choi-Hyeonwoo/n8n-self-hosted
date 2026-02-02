#!/usr/bin/env python3
"""
TIMEFOLIO ETF Holdings Tracker
Scrapes timeetf.co.kr for 6 ETFs, tracks daily weight changes,
and generates a formatted report highlighting significant moves.
"""

import urllib.request
import json
import re
import os
import sys
from datetime import datetime, timedelta

# ─── ETF Configuration ───────────────────────────────────────────────
ETFS = {
    # Global
    "NQ100":         {"idx": 2,  "name": "미국나스닥100액티브",        "cate": "001"},
    "CN_AI":         {"idx": 19, "name": "차이나AI테크액티브",        "cate": "001"},
    "GLOBAL_AI":     {"idx": 6,  "name": "글로벌AI인공지능액티브",    "cate": "001"},
    # Domestic
    "KOSPI_ACTIVE":  {"idx": 11, "name": "코스피액티브",              "cate": "001"},
    "K_CULTURE":     {"idx": 1,  "name": "K컬처액티브",              "cate": "001"},
    "K_BIO":         {"idx": 13, "name": "K바이오액티브",             "cate": "001"},
}

BASE_URL = "https://timeetf.co.kr/m11_view.php"
DATA_DIR = os.path.expanduser("~/.openclaw/workspace/knowledge/03-Portfolio/etf_data")

# ─── HTML Parsing ─────────────────────────────────────────────────────
def fetch_etf_page(idx, cate="001"):
    """Fetch ETF holdings page HTML."""
    url = f"{BASE_URL}?idx={idx}&cate={cate}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; OpenClaw/1.0)"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def parse_full_holdings(html):
    """Parse full holdings table (class=table3 moreList1)."""
    holdings = []
    # Find the table with full holdings
    table_match = re.search(r'<table[^>]*class="table3 moreList1"[^>]*>(.*?)</table>', html, re.DOTALL)
    if not table_match:
        return holdings

    tbody = table_match.group(1)
    rows = re.findall(r'<tr>\s*(.*?)\s*</tr>', tbody, re.DOTALL)

    for row in rows:
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
        if len(cells) >= 5:
            code = cells[0].strip()
            name = cells[1].strip()
            shares = cells[2].strip().replace(",", "")
            value = cells[3].strip().replace(",", "")
            weight = cells[4].strip()
            try:
                holdings.append({
                    "code": code,
                    "name": name,
                    "shares": int(shares) if shares else 0,
                    "value": int(value) if value else 0,
                    "weight": float(weight) if weight else 0.0,
                })
            except ValueError:
                continue
    return holdings


def parse_top10_with_changes(html):
    """Parse todayTop10 section which includes daily changes."""
    top10 = []
    ul_match = re.search(r'<ul id="todayTop10">(.*?)</ul>', html, re.DOTALL)
    if not ul_match:
        return top10

    items = re.findall(r'<li>(.*?)</li>', ul_match.group(1), re.DOTALL)
    for item in items:
        name_match = re.search(r'<span>\d+</span>(.*?)</div>', item)
        weight_match = re.findall(r'<div>([\d.]+%)</div>', item)
        change_match = re.search(r'class="(up|down|new)"[^>]*>([^<]+)<', item)

        if name_match and weight_match:
            name = name_match.group(1).strip()
            weight = float(weight_match[0].replace("%", ""))
            change_str = ""
            change_val = 0.0
            change_type = ""

            if change_match:
                change_type = change_match.group(1)
                change_str = change_match.group(2).strip()
                if change_type == "new":
                    change_str = "신규"
                else:
                    try:
                        change_val = float(change_str.replace("%", "").replace("+", ""))
                    except ValueError:
                        pass

            top10.append({
                "name": name,
                "weight": weight,
                "change": change_val,
                "change_str": change_str,
                "change_type": change_type,
            })
    return top10


def parse_date(html):
    """Extract the holdings date from page."""
    # Look for date patterns like 2026.01.30
    match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})', html)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return datetime.now().strftime("%Y-%m-%d")


# ─── Data Storage ─────────────────────────────────────────────────────
def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def save_holdings(etf_key, date, holdings, top10):
    """Save daily holdings to JSON file."""
    ensure_data_dir()
    filepath = os.path.join(DATA_DIR, f"{etf_key}_{date}.json")
    data = {
        "etf": etf_key,
        "date": date,
        "fetched_at": datetime.now().isoformat(),
        "holdings": holdings,
        "top10": top10,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filepath


def load_previous(etf_key, current_date):
    """Load the most recent previous data file for comparison."""
    ensure_data_dir()
    files = sorted([
        f for f in os.listdir(DATA_DIR)
        if f.startswith(f"{etf_key}_") and f.endswith(".json") and f != f"{etf_key}_{current_date}.json"
    ], reverse=True)
    if files:
        filepath = os.path.join(DATA_DIR, files[0])
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# ─── Report Generation ────────────────────────────────────────────────
def compare_holdings(today_holdings, prev_holdings):
    """Compare today vs previous holdings, return changes."""
    if not prev_holdings:
        return []

    prev_map = {h["name"]: h for h in prev_holdings}
    today_map = {h["name"]: h for h in today_holdings}
    changes = []

    # Check today's holdings for changes
    for name, h in today_map.items():
        if name in prev_map:
            diff = h["weight"] - prev_map[name]["weight"]
            if abs(diff) >= 0.3:  # 0.3% threshold
                changes.append({
                    "name": name,
                    "code": h.get("code", ""),
                    "today_weight": h["weight"],
                    "prev_weight": prev_map[name]["weight"],
                    "diff": round(diff, 2),
                })
        else:
            changes.append({
                "name": name,
                "code": h.get("code", ""),
                "today_weight": h["weight"],
                "prev_weight": 0,
                "diff": h["weight"],
                "new": True,
            })

    # Check for removed holdings
    for name, h in prev_map.items():
        if name not in today_map and h["weight"] >= 0.5:
            changes.append({
                "name": name,
                "code": h.get("code", ""),
                "today_weight": 0,
                "prev_weight": h["weight"],
                "diff": -h["weight"],
                "removed": True,
            })

    changes.sort(key=lambda x: abs(x["diff"]), reverse=True)
    return changes


def format_report(results):
    """Generate a formatted markdown report."""
    date = results.get("date", "unknown")
    lines = [f"# TIMEFOLIO ETF 일일 리포트 ({date})", ""]

    significant_changes = []  # stocks needing news lookup

    for etf_key, data in results.get("etfs", {}).items():
        etf_cfg = ETFS.get(etf_key, {})
        etf_name = etf_cfg.get("name", etf_key)
        lines.append(f"## TIME {etf_name}")
        lines.append("")

        # Top 10 with changes
        top10 = data.get("top10", [])
        if top10:
            lines.append("| # | 종목명 | 비중 | 증감 |")
            lines.append("|---|--------|------|------|")
            for i, h in enumerate(top10, 1):
                change_str = h.get("change_str", "")
                if h.get("change_type") == "up":
                    change_str = f"▲ {change_str}"
                elif h.get("change_type") == "down":
                    change_str = f"▼ {change_str}"
                elif h.get("change_type") == "new":
                    change_str = "🆕 신규"
                lines.append(f"| {i} | {h['name']} | {h['weight']:.2f}% | {change_str} |")
            lines.append("")

        # Significant changes from full comparison
        changes = data.get("changes", [])
        if changes:
            big_changes = [c for c in changes if abs(c["diff"]) >= 1.0]
            if big_changes:
                lines.append("### 주요 비중 변동 (1%p 이상)")
                for c in big_changes[:10]:
                    direction = "▲ 증가" if c["diff"] > 0 else "▼ 감소"
                    extra = ""
                    if c.get("new"):
                        extra = " (신규 편입)"
                    elif c.get("removed"):
                        extra = " (전량 매도)"
                    lines.append(
                        f"- **{c['name']}**: {c['prev_weight']:.2f}% → {c['today_weight']:.2f}% "
                        f"({direction} {abs(c['diff']):.2f}%p){extra}"
                    )
                    significant_changes.append({
                        "name": c["name"],
                        "code": c.get("code", ""),
                        "etf": etf_name,
                        "diff": c["diff"],
                    })
                lines.append("")

        # Holdings count
        holdings = data.get("holdings", [])
        if holdings:
            total = sum(h["weight"] for h in holdings)
            lines.append(f"*전체 {len(holdings)}종목, 총 비중 {total:.1f}%*")
            lines.append("")

    # Summary of stocks needing news research
    if significant_changes:
        lines.append("---")
        lines.append("## 뉴스 확인 필요 종목")
        lines.append("아래 종목들의 비중이 크게 변동되었습니다. 뉴스를 확인해주세요:")
        lines.append("")
        for sc in significant_changes[:15]:
            direction = "편입 증가" if sc["diff"] > 0 else "비중 감소"
            lines.append(f"- **{sc['name']}** ({sc['etf']}): {direction} {abs(sc['diff']):.2f}%p")
        lines.append("")
        lines.append("*각 종목명으로 최근 뉴스를 검색하여 비중 변동 사유를 분석해주세요.*")

    return "\n".join(lines), significant_changes


# ─── Main ─────────────────────────────────────────────────────────────
def run(etf_keys=None):
    """Main entry point. Fetch all ETFs and generate report."""
    if etf_keys is None:
        etf_keys = list(ETFS.keys())

    results = {"date": None, "etfs": {}}
    errors = []

    for key in etf_keys:
        if key not in ETFS:
            errors.append(f"Unknown ETF key: {key}")
            continue

        cfg = ETFS[key]
        try:
            html = fetch_etf_page(cfg["idx"], cfg["cate"])
            date = parse_date(html)
            if results["date"] is None:
                results["date"] = date

            holdings = parse_full_holdings(html)
            top10 = parse_top10_with_changes(html)

            # Save today's data
            save_holdings(key, date, holdings, top10)

            # Load previous for comparison
            prev = load_previous(key, date)
            prev_holdings = prev["holdings"] if prev else None
            changes = compare_holdings(holdings, prev_holdings)

            results["etfs"][key] = {
                "holdings": holdings,
                "top10": top10,
                "changes": changes,
                "count": len(holdings),
            }
        except Exception as e:
            errors.append(f"{key}: {e}")

    report, significant = format_report(results)

    if errors:
        report += "\n\n### Errors\n" + "\n".join(f"- {e}" for e in errors)

    return report


if __name__ == "__main__":
    # Accept optional ETF keys as args
    keys = sys.argv[1:] if len(sys.argv) > 1 else None
    print(run(keys))
