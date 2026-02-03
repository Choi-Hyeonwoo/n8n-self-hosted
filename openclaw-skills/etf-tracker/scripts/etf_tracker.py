#!/usr/bin/env python3
"""
TIMEFOLIO ETF Holdings Tracker v12
- Page 1: ETF별 1일 비중 변동 TOP 5 / BOTTOM 3 + Holdings TOP 10 통합
- Page 2: 주요 종목 뉴스 분석 (원인 2줄 + 판단 1줄, 결과성 기사 제외)
- 비중 변동·뉴스 분석 모두 1D 기준 (d1_map)
- 1D/1W: pdfDate로 실제 과거 날짜 holdings 가져와서 비교
- 1M: pdfM1 AJAX (timeetf 1개월 전 비교, Holdings 테이블용)
- v11: 칼럼 라벨 상단 1회만, By Investing.com 제거, 현금 회색, 신규편입 1D기준 전체 표시
- v12: Claude API를 활용한 Deep Research 분석 (복합적 종목 분석)
"""

import urllib.request
import urllib.parse
import json
import re
import os
import sys
import tempfile
from datetime import datetime, timedelta

# ─── Image support (optional) ──────────────────────────────────────
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ─── Claude API support (for deep research) ────────────────────────
try:
    import anthropic
    HAS_CLAUDE = True
except ImportError:
    HAS_CLAUDE = False

FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_BOLD_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

# ─── ETF Configuration ───────────────────────────────────────────────
ETFS = {
    "NQ100":         {"idx": 2,  "name": "미국나스닥100액티브",     "short": "NQ100",  "cate": "001"},
    "CN_AI":         {"idx": 19, "name": "차이나AI테크액티브",     "short": "CN AI",  "cate": "001"},
    "GLOBAL_AI":     {"idx": 6,  "name": "글로벌AI인공지능액티브", "short": "GL AI",  "cate": "001"},
    "KOSPI_ACTIVE":  {"idx": 11, "name": "코스피액티브",           "short": "코스피", "cate": "001"},
    "K_CULTURE":     {"idx": 1,  "name": "K컬처액티브",           "short": "K컬처",  "cate": "001"},
    "K_BIO":         {"idx": 13, "name": "K바이오액티브",          "short": "K바이오","cate": "001"},
}

OVERSEAS_KEYS = ["NQ100", "CN_AI", "GLOBAL_AI"]
DOMESTIC_KEYS = ["KOSPI_ACTIVE", "K_CULTURE", "K_BIO"]

BASE_URL = "https://timeetf.co.kr/m11_view.php"
AJAX_URL = "https://timeetf.co.kr/past_pdf_json.php"
DATA_DIR = os.path.expanduser("~/.openclaw/workspace/knowledge/03-Portfolio/etf_data")
IMG_DIR = tempfile.gettempdir()


# ─── Fetching ─────────────────────────────────────────────────────────
def fetch_page(idx, cate="001"):
    url = f"{BASE_URL}?idx={idx}&cate={cate}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; OpenClaw/1.0)"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def fetch_period_comparison(idx, period, retries=3):
    import time
    data = urllib.parse.urlencode({"period": period, "idx": idx}).encode()
    for attempt in range(retries):
        req = urllib.request.Request(AJAX_URL, data=data, headers={
            "User-Agent": "Mozilla/5.0 (compatible; OpenClaw/1.0)"
        })
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            if attempt < retries - 1:
                time.sleep(1 + attempt)
    return None


def fetch_page_for_date(idx, cate="001", pdf_date=None):
    url = f"{BASE_URL}?idx={idx}&cate={cate}"
    if pdf_date:
        url += f"&pdfDate={pdf_date}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; OpenClaw/1.0)"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except Exception:
        return None


def parse_available_dates(html):
    dates = re.findall(r'\d{4}\.\d{2}\.\d{2}', html)
    cutoff = (datetime.now() - timedelta(days=400)).strftime("%Y.%m.%d")
    unique = sorted(set(d for d in dates if d >= cutoff), reverse=True)
    return unique


def find_comparison_dates(available_dates, current_date_dot):
    if not available_dates:
        return None, None
    td = datetime.strptime(current_date_dot, "%Y.%m.%d")

    def _nearest(target):
        best, best_diff = None, 999
        for d in available_dates:
            dd = datetime.strptime(d, "%Y.%m.%d")
            if dd >= td:
                continue
            diff = abs((dd - target).days)
            if diff < best_diff:
                best, best_diff = d, diff
        return best

    return _nearest(td - timedelta(days=1)), _nearest(td - timedelta(days=7))


def build_weight_map(holdings):
    return {h["name"]: h["weight"] for h in holdings}


def build_diff_map_from_weights(current_holdings, prev_weight_map):
    result = {}
    for h in current_holdings:
        pw = prev_weight_map.get(h["name"])
        if pw is not None:
            result[h["name"]] = round(h["weight"] - pw, 2)
    return result


# ─── Parsing ──────────────────────────────────────────────────────────
def parse_date(html):
    match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})', html)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return datetime.now().strftime("%Y-%m-%d")


def _parse_ticker(code_raw):
    if not code_raw:
        return ""
    t = code_raw.strip()
    t = re.sub(r'\s+EQUITY\s*$', '', t, flags=re.IGNORECASE)
    return t


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
            code_raw = cells[0].strip()
            name = cells[1].strip()
            shares_str = cells[2].strip().replace(",", "")
            value_str = cells[3].strip().replace(",", "")
            weight_str = cells[4].strip()
            try:
                holdings.append({
                    "code": code_raw,
                    "ticker": _parse_ticker(code_raw),
                    "name": name,
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


def load_nearest(etf_key, target_date, direction="before", max_days=10):
    ensure_dir()
    files = sorted([
        f for f in os.listdir(DATA_DIR)
        if f.startswith(f"{etf_key}_") and f.endswith(".json")
    ])
    if not files:
        return None
    candidates = []
    prefix = f"{etf_key}_"
    for fn in files:
        stem = fn.replace(".json", "")
        file_date = stem[len(prefix):]
        if not file_date:
            continue
        if direction == "before" and file_date < target_date:
            candidates.append((file_date, fn))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    best_date, best_fn = candidates[0]
    try:
        td = datetime.strptime(target_date, "%Y-%m-%d")
        bd = datetime.strptime(best_date, "%Y-%m-%d")
        if (td - bd).days > max_days:
            return None
    except ValueError:
        pass
    with open(os.path.join(DATA_DIR, best_fn), "r", encoding="utf-8") as f:
        return json.load(f)


# ─── Comparison helpers ──────────────────────────────────────────────
def parse_ajax_changes(ajax_data, ticker_map=None):
    if not ajax_data or "today" not in ajax_data:
        return [], [], []
    if ticker_map is None:
        ticker_map = {}
    ups, downs, news = [], [], []
    for item in ajax_data["today"]:
        nm = item["prodNm"]
        w = float(item["wei"])
        tk = ticker_map.get(nm, "")
        inc = item.get("increaseWei", "0")
        if inc in ("신규", "\uc2e0\uaddc"):
            news.append({"name": nm, "weight": w, "ticker": tk})
        else:
            try:
                val = float(inc)
                entry = {"name": nm, "weight": w, "diff": val, "ticker": tk}
                if val > 0:
                    ups.append(entry)
                elif val < 0:
                    downs.append(entry)
            except ValueError:
                pass
    ups.sort(key=lambda x: x["diff"], reverse=True)
    downs.sort(key=lambda x: x["diff"])
    return ups, downs, news


def build_d1_changes(holdings, d1_map):
    """Build 1D-based ups/downs lists from d1_map."""
    ups, downs = [], []
    for h in holdings:
        d1v = d1_map.get(h["name"])
        if d1v is None or d1v == 0:
            continue
        entry = {
            "name": h["name"],
            "weight": h["weight"],
            "diff": d1v,
            "ticker": h.get("ticker", ""),
        }
        if d1v > 0:
            ups.append(entry)
        else:
            downs.append(entry)
    ups.sort(key=lambda x: x["diff"], reverse=True)
    downs.sort(key=lambda x: x["diff"])
    return ups, downs


# ─── Image rendering helpers ─────────────────────────────────────────
def _get_fonts():
    fp = FONT_PATH if os.path.exists(FONT_PATH) else None
    fb = FONT_BOLD_PATH if os.path.exists(FONT_BOLD_PATH) else None
    font = FontProperties(fname=fp, size=10) if fp else FontProperties(size=10)
    font_title = FontProperties(fname=fb or fp, size=14, weight="bold") if (fb or fp) else FontProperties(size=14, weight="bold")
    font_section = FontProperties(fname=fb or fp, size=11, weight="bold") if (fb or fp) else FontProperties(size=11, weight="bold")
    font_header = FontProperties(fname=fb or fp, size=9.5, weight="bold") if (fb or fp) else FontProperties(size=9.5, weight="bold")
    font_small = FontProperties(fname=fp, size=9) if fp else FontProperties(size=9)
    font_news = FontProperties(fname=fp, size=8.5) if fp else FontProperties(size=8.5)
    return font, font_title, font_section, font_header, font_small, font_news


def _diff_str(val):
    if val is None or val == "":
        return "-"
    if isinstance(val, str):
        return val
    return f"+{val:.2f}" if val > 0 else f"{val:.2f}"


def _diff_color(val):
    if val is None or val == "" or val == "-":
        return "#999999"
    if isinstance(val, str):
        if val == "NEW":
            return "#4CAF50"
        if val.startswith("+"):
            return "#D32F2F"
        elif val.startswith("-"):
            return "#1565C0"
        return "#333333"
    if val > 0:
        return "#D32F2F"
    elif val < 0:
        return "#1565C0"
    return "#333333"


# ─── Page 1: 1일 비중 변동 + Holdings TOP 10 통합 ────────────────────
def render_page1(group_label, date, per_etf_changes, etf_sections, is_overseas=False):
    """Combined: 1일 비중 변동 (top) + Holdings TOP 10 (bottom)."""
    if not HAS_MPL or not per_etf_changes:
        return None
    fonts = _get_fonts()
    font, font_title, font_section, font_header, font_small, font_news = fonts

    n_etfs = len(per_etf_changes)
    col_w = 4.2
    gap = 0.15
    fig_w = 0.3 + n_etfs * col_w + (n_etfs - 1) * gap + 0.3

    row_h = 0.34
    sect_h = 0.40
    etf_head_h = 0.36
    col_head_h = 0.28
    n_ups = 5
    n_downs = 3

    # Holdings dimensions
    h_row_h = 0.30
    h_sect_h = 0.36
    h_col_h = 0.28
    h_spacing = 0.20
    n_sects = len(etf_sections)

    changes_h = (sect_h + etf_head_h + col_head_h + n_ups * row_h + 0.2
                 + sect_h + etf_head_h + col_head_h + n_downs * row_h)
    holdings_h = sum(
        h_sect_h + h_col_h + min(len(s["rows"]), 10) * h_row_h
        for s in etf_sections
    ) + max(0, n_sects - 1) * h_spacing

    fig_h = 0.7 + changes_h + 0.5 + holdings_h + 0.3
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    col_starts = [0.3 + i * (col_w + gap) for i in range(n_etfs)]
    rx = {"rank": 0.15, "ticker": 0.65, "name": 1.85, "weight": 3.05, "diff": 3.75}

    # Title
    y = fig_h - 0.4
    ax.text(fig_w / 2, y, f"TIMEFOLIO {group_label} ETF  1일 비중 변동 & Holdings",
            fontproperties=font_title, ha="center", va="center", color="#1A1A2E")
    ax.text(fig_w - 0.3, y, date, fontproperties=font_small,
            ha="right", va="center", color="#888888")

    def _draw_change_section(y_top, label, color, bg_tint, n_rows, get_items, dc_fn):
        y = y_top
        ax.add_patch(plt.Rectangle((0.15, y - 0.15), fig_w - 0.3, 0.34,
                                    facecolor=color, edgecolor="none", zorder=2))
        ax.text(0.4, y + 0.02, label, fontproperties=font_section,
                ha="left", va="center", color="white", zorder=3)
        y -= sect_h
        for ci, etf in enumerate(per_etf_changes):
            cx = col_starts[ci]
            ax.add_patch(plt.Rectangle((cx, y - 0.12), col_w, 0.30,
                                        facecolor="#37474F", edgecolor="none", zorder=2))
            ax.text(cx + col_w / 2, y + 0.02, etf["etf_name"],
                    fontproperties=font_header, ha="center", va="center",
                    color="white", zorder=3)
        y -= etf_head_h
        for ci in range(n_etfs):
            cx = col_starts[ci]
            for key, lbl in [("rank", "#"), ("ticker", "Ticker"),
                             ("name", "종목명"), ("weight", "비중"), ("diff", "1D변동")]:
                ax.text(cx + rx[key], y, lbl, fontproperties=font_header,
                        ha="center", va="center", color="#888888")
        y -= col_head_h
        for ri in range(n_rows):
            if ri % 2 == 0:
                for ci in range(n_etfs):
                    cx = col_starts[ci]
                    ax.add_patch(plt.Rectangle((cx, y - row_h / 2 + 0.01),
                                                col_w, row_h,
                                                facecolor=bg_tint, edgecolor="none", zorder=1))
            for ci, etf in enumerate(per_etf_changes):
                items = get_items(etf)
                if ri >= len(items):
                    continue
                item = items[ri]
                cx = col_starts[ci]
                ax.text(cx + rx["rank"], y, str(ri + 1), fontproperties=font_small,
                        ha="center", va="center", color="#555", zorder=3)
                ax.text(cx + rx["ticker"], y, item.get("ticker", ""),
                        fontproperties=font_header, ha="center", va="center",
                        color="#2C3E50", zorder=3)
                nm = item["name"][:12] + ".." if len(item["name"]) > 12 else item["name"]
                ax.text(cx + rx["name"], y, nm, fontproperties=font_small,
                        ha="center", va="center", color="#333", zorder=3)
                ax.text(cx + rx["weight"], y, f"{item['weight']:.1f}%",
                        fontproperties=font_small, ha="center", va="center",
                        color="#333", zorder=3)
                ds = _diff_str(item["diff"])
                if ds != "-":
                    ds += "%p"
                ax.text(cx + rx["diff"], y, ds, fontproperties=font_small,
                        ha="center", va="center", color=dc_fn(item["diff"]), zorder=3)
            y -= row_h
        top_y = y_top - sect_h + 0.18
        bot_y = y + 0.05
        for ci in range(1, n_etfs):
            sep_x = col_starts[ci] - gap / 2
            ax.plot([sep_x, sep_x], [bot_y, top_y], color="#DDDDDD",
                    linewidth=0.8, zorder=1)
        return y

    y = fig_h - 0.8
    y = _draw_change_section(y, "1일 비중 증가 TOP 5", "#C62828", "#FFF5F5", n_ups,
                              lambda e: e["ups"][:5], lambda v: "#D32F2F")
    y -= 0.2
    y = _draw_change_section(y, "1일 비중 감소 BOTTOM 3", "#1565C0", "#F5F8FF", n_downs,
                              lambda e: e["downs"][:3], lambda v: "#1565C0")

    # ─ Separator ─
    y -= 0.25
    ax.plot([0.3, fig_w - 0.3], [y, y], color="#CCCCCC", linewidth=1.0, zorder=1)
    y -= 0.15

    # ─ Holdings section (full width) ─
    if is_overseas:
        hx = {"rank": 0.5, "ticker": 1.8, "name": 5.0,
              "weight": 8.5, "d1": 9.7, "w1": 10.9, "m1": 12.2}
        h_name_limit = 24
    else:
        hx = {"rank": 0.5, "ticker": 2.0, "name": 5.0,
              "weight": 7.5, "d1": 9.0, "w1": 10.5, "m1": 12.0}
        h_name_limit = 18

    h_col_labels = [("rank", "#"), ("ticker", "Ticker"), ("name", "종목명"),
                    ("weight", "비중"), ("d1", "1D"), ("w1", "1W"), ("m1", "1M")]

    for si, sect in enumerate(etf_sections):
        ax.add_patch(plt.Rectangle((0.15, y - 0.12), fig_w - 0.3, 0.30,
                                    facecolor="#2C3E50", edgecolor="none", zorder=2))
        ax.text(0.4, y + 0.02, f"{sect['name']}  ({sect['count']}종목)",
                fontproperties=font_section, ha="left", va="center",
                color="white", zorder=3)
        y -= h_sect_h
        for ck, cl in h_col_labels:
            ax.text(hx[ck], y, cl, fontproperties=font_header,
                    ha="center", va="center", color="#888888")
        y -= h_col_h
        for ri, row in enumerate(sect["rows"][:10]):
            if ri % 2 == 0:
                ax.add_patch(plt.Rectangle((0.15, y - h_row_h / 2 + 0.01),
                                            fig_w - 0.3, h_row_h,
                                            facecolor="#F8F9FA", edgecolor="none", zorder=1))
            ax.text(hx["rank"], y, row["rank"], fontproperties=font_small,
                    ha="center", va="center", color="#555", zorder=3)
            ax.text(hx["ticker"], y, row["ticker"], fontproperties=font_header,
                    ha="center", va="center", color="#2C3E50", zorder=3)
            # Truncate name based on group
            rn = row["name"]
            if len(rn) > h_name_limit:
                rn = rn[:h_name_limit - 2] + ".."
            ax.text(hx["name"], y, rn, fontproperties=font_small,
                    ha="center", va="center", color="#333", zorder=3)
            ax.text(hx["weight"], y, row["weight"], fontproperties=font_small,
                    ha="center", va="center", color="#333", zorder=3)
            for k in ("d1", "w1", "m1"):
                ds = _diff_str(row[k])
                if ds != "-" and ds != "NEW":
                    ds += "%p"
                ax.text(hx[k], y, ds, fontproperties=font_small,
                        ha="center", va="center", color=_diff_color(row[k]), zorder=3)
            y -= h_row_h
        if si < n_sects - 1:
            y -= h_spacing

    glabel = group_label.replace(" ", "")
    path = os.path.join(IMG_DIR, f"etf_p1_{glabel}_{date}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white", pad_inches=0.1)
    plt.close(fig)
    return path


# ─── Page 2: 주요 종목 뉴스 분석 (2행 가로 배치) ─────────────────────
def render_page2_news(group_label, date, per_etf_news):
    """Horizontal 2-row layout: [종목|기사/원인|판단] per mover."""
    if not HAS_MPL or not per_etf_news:
        return None
    fonts = _get_fonts()
    font, font_title, font_section, font_header, font_small, font_news = fonts

    fig_w = 14.0
    row_h = 0.30
    sect_h = 0.40
    mover_gap = 0.10
    spacing = 0.25

    # Column positions (left | center | right)
    lx = 0.4       # left: 종목/비중
    cx = 3.3        # center: 기사/원인 (widest area)
    rx = 10.5       # right: 판단

    # Calculate height
    total_h = 0.7 + 0.32  # title + column labels (once at top)
    for en in per_etf_news:
        total_h += sect_h  # ETF header only (no column labels)
        n_movers = len(en.get("movers", []))
        total_h += n_movers * (2 * row_h + mover_gap)
        total_h += spacing
    total_h += 0.3
    fig_h = max(total_h, 3.0)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    y = fig_h - 0.4
    ax.text(fig_w / 2, y, f"TIMEFOLIO {group_label} ETF  주요 종목 뉴스 분석",
            fontproperties=font_title, ha="center", va="center", color="#1A1A2E")
    ax.text(fig_w - 0.3, y, date, fontproperties=font_small,
            ha="right", va="center", color="#888888")
    y -= 0.48

    # Column labels (only once at top)
    ax.text(lx, y, "종목 / 비중", fontproperties=font_header,
            ha="left", va="center", color="#888888")
    ax.text(cx, y, "원인 / 기사", fontproperties=font_header,
            ha="left", va="center", color="#888888")
    ax.text(rx, y, "변동 판단", fontproperties=font_header,
            ha="left", va="center", color="#888888")
    y -= 0.32

    for si, en in enumerate(per_etf_news):
        # ETF section header
        ax.add_patch(plt.Rectangle((0.15, y - 0.15), fig_w - 0.3, 0.35,
                                    facecolor="#2C3E50", edgecolor="none", zorder=2))
        ax.text(0.4, y + 0.02, en["etf_name"],
                fontproperties=font_section, ha="left", va="center",
                color="white", zorder=3)
        y -= sect_h

        movers = en.get("movers", [])
        sect_top_y = y

        for mi, m in enumerate(movers):
            is_new = m.get("is_new", False)
            diff = m.get("diff")
            is_cash = m.get("name") == "현금"

            if is_cash:
                # Gray styling for cash position
                dc = "#666666"
                bg = "#F5F5F5"
            elif is_new:
                dc = "#4CAF50"
                bg = "#E8F5E9"
            elif diff is not None and diff > 0:
                dc = "#D32F2F"
                bg = "#FFF5F5"
            else:
                dc = "#1565C0"
                bg = "#F5F8FF"

            # Background rectangle spanning 2 rows
            bg_h = 2 * row_h
            ax.add_patch(plt.Rectangle((0.15, y - bg_h + 0.02),
                                        fig_w - 0.3, bg_h - 0.04,
                                        facecolor=bg, edgecolor="none", zorder=1))

            # Get analysis
            analysis = m.get("analysis", {})
            if isinstance(analysis, str):
                causes = [analysis]
                judgment = ""
            else:
                causes = analysis.get("causes", [])
                judgment = analysis.get("judgment", "")

            tk = m.get("ticker", "")
            nm = m["name"][:16] + ".." if len(m["name"]) > 16 else m["name"]

            # ── Row 1: 종목명 | 원인1 | 판단 ──
            # Left: ticker + name
            name_label = f"{'[신규] ' if is_new else ''}{tk}  {nm}" if tk else f"{'[신규] ' if is_new else ''}{nm}"
            ax.text(lx, y - row_h / 2, name_label,
                    fontproperties=font_header, ha="left", va="center",
                    color="#1A1A2E", zorder=3)

            # Center: cause line 1
            if causes:
                c1 = causes[0]
                if len(c1) > 60:
                    c1 = c1[:58] + ".."
                ax.text(cx, y - row_h / 2, f"• {c1}",
                        fontproperties=font_news, ha="left", va="center",
                        color="#37474F", zorder=3)

            # Right: judgment
            if judgment:
                jd = judgment
                if len(jd) > 35:
                    jd = jd[:33] + ".."
                ax.text(rx, y - row_h / 2, jd,
                        fontproperties=font_news, ha="left", va="center",
                        color=dc, zorder=3)

            y -= row_h

            # ── Row 2: 비중/변동 | 원인2 | ──
            # Left: 비중 + 변동
            if is_new:
                diff_label = f"비중 {m['weight']:.1f}%  신규편입"
            else:
                ds = _diff_str(diff)
                if ds != "-":
                    ds += "%p"
                diff_label = f"비중 {m['weight']:.1f}%  {ds}"
            ax.text(lx, y - row_h / 2, diff_label,
                    fontproperties=font_small, ha="left", va="center",
                    color=dc, zorder=3)

            # Center: cause line 2
            if len(causes) > 1:
                c2 = causes[1]
                if len(c2) > 60:
                    c2 = c2[:58] + ".."
                ax.text(cx, y - row_h / 2, f"• {c2}",
                        fontproperties=font_news, ha="left", va="center",
                        color="#37474F", zorder=3)

            y -= row_h
            y -= mover_gap

        # Column separator lines
        if movers:
            ax.plot([cx - 0.1, cx - 0.1], [sect_top_y, y + mover_gap],
                    color="#E0E0E0", linewidth=0.5, zorder=1)
            ax.plot([rx - 0.1, rx - 0.1], [sect_top_y, y + mover_gap],
                    color="#E0E0E0", linewidth=0.5, zorder=1)

        if si < len(per_etf_news) - 1:
            y -= spacing

    glabel = group_label.replace(" ", "")
    path = os.path.join(IMG_DIR, f"etf_p2_{glabel}_{date}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white", pad_inches=0.1)
    plt.close(fig)
    return path


# ─── News fetching ───────────────────────────────────────────────────
_KR_ALIASES = {
    "NVIDIA": "엔비디아", "Tesla": "테슬라", "Alphabet": "구글 알파벳",
    "Microsoft": "마이크로소프트", "Apple": "애플", "Amazon": "아마존",
    "Meta Platforms": "메타 페이스북", "Intel": "인텔", "AMD": "AMD 반도체",
    "ASML": "ASML 반도체", "TSMC": "TSMC 반도체",
    "Taiwan Semiconductor": "TSMC 반도체",
    "Sandisk": "샌디스크", "Seagate": "씨게이트",
    "Micron": "마이크론", "Western Digital": "웨스턴디지털",
    "Bloom Energy": "블룸에너지", "Cameco": "카메코 우라늄",
    "Rocket Lab": "로켓랩", "Alibaba": "알리바바",
    "Zhongji Innolight": "중지이노라이트 광모듈",
    "Eoptolink": "이옵토링크 광트랜시버",
    "MediaTek": "미디어텍", "Ganfeng Lithium": "간펑리튬",
    "GE Vernova": "GE버노바 에너지", "Palantir": "팔란티어",
    "Broadcom": "브로드컴", "Netflix": "넷플릭스",
    "Qualcomm": "퀄컴", "Adobe": "어도비",
    "Powerchip": "파워칩 반도체",
    "Elite Material": "엘리트 머티리얼 PCB",
    "NVIDIA Corp": "엔비디아",
    "STX": "STX 해운 조선",
    "Nanya": "난야 테크놀로지",
    "Hesai": "헤사이 라이다",
    "Cambricon": "캠브리콘 AI",
    "Hua Hong": "화홍 반도체",
    "UBTech": "유비테크 로봇",
    "Macronix": "매크로닉스 플래시",
}

_IB_NAMES = [
    "모간스탠리", "Morgan Stanley", "골드만삭스", "Goldman Sachs",
    "JP모간", "JPMorgan", "UBS", "시티", "Citi", "바클레이즈", "Barclays",
    "도이치뱅크", "Deutsche Bank", "뱅크오브아메리카", "BofA",
    "노무라", "Nomura", "CLSA", "맥쿼리", "Macquarie",
    "번스타인", "Bernstein", "제프리스", "Jefferies", "웨드부시", "Wedbush",
    "키움증권", "하나증권", "미래에셋증권", "삼성증권", "NH투자증권",
    "KB증권", "대신증권", "신한투자증권", "한국투자증권", "메리츠증권",
    "교보증권", "유안타증권", "이베스트투자증권", "현대차증권",
    "다올투자증권", "다올투자", "SK증권", "한화투자증권", "유진투자증권",
    "LS증권", "BNK투자증권", "DB금융투자", "하이투자증권", "iM증권",
]

# ─── Stock Profile Database (for deep research) ──────────────────────
_STOCK_PROFILES = {
    # 반도체/메모리
    "Sandisk": "Pure-play NAND 플래시 전문기업. WD 합병 후 분사. 엔터프라이즈 SSD, 데이터센터 스토리지 강점",
    "Micron": "DRAM/NAND 메모리 반도체. HBM(고대역폭메모리) AI 수혜주. 데이터센터 핵심 공급사",
    "SK하이닉스": "HBM 세계 1위. AI 가속기용 메모리 핵심 공급. 엔비디아 주요 파트너",
    "NVIDIA": "AI GPU 절대 강자. 데이터센터 AI 가속기 시장 90%+ 점유. Blackwell/Hopper 아키텍처",
    "TSMC": "파운드리 세계 1위. 첨단 공정(3nm/2nm) 독점. 애플/엔비디아/AMD 생산",
    "Western Digital": "HDD/SSD 스토리지. 데이터센터 대용량 저장장치. Sandisk와 합병했다 분리",
    "Seagate": "HDD 세계 1위. 데이터센터 대용량 스토리지 전문",
    "Intel": "CPU 레거시 강자. 파운드리 사업 진출. AI PC 시장 공략",
    "AMD": "CPU/GPU 2위. 데이터센터 EPYC 프로세서. MI300 AI 가속기",
    "ASML": "EUV 노광장비 독점. 반도체 장비 핵심. TSMC/삼성 필수 장비",
    "Nanya": "대만 DRAM 전문. 범용 DRAM, DDR5 생산. 가격 민감도 높음",
    "Powerchip": "대만 파운드리. 성숙 공정 특화. 전력반도체, 디스플레이 드라이버",
    # AI/소프트웨어
    "Alphabet": "구글 모회사. 검색/광고/클라우드. Gemini AI 모델. 자율주행 Waymo",
    "Meta Platforms": "메타버스/소셜미디어. 페이스북/인스타그램. Llama AI 모델",
    "Tesla": "EV 선두주자. 자율주행 FSD. 로보택시, 옵티머스 휴머노이드",
    "Palantir": "빅데이터 분석 플랫폼. 정부/기업 AI 솔루션. AIP 플랫폼",
    # 바이오/헬스케어
    "에이비엘바이오": "이중항체 플랫폼 Grabody. 사노피/BMS와 기술이전 계약",
    "삼천당제약": "비만치료제 파이프라인. GLP-1 기반 신약 개발",
    "에이프릴바이오": "SAFA 플랫폼 기반 DDS 기술. 항체-약물 접합체",
    "셀트리온": "바이오시밀러 글로벌 1위급. 자가면역질환 치료제",
    "리가켐바이오": "ADC(항체약물접합체) 전문. 글로벌 기술이전 활발",
    "HLB": "항암제 리보세라닙. FDA 승인 추진. 간암 치료제",
    # 에너지/인프라
    "Bloom Energy": "SOFC 연료전지. 데이터센터 전력공급. 친환경 에너지",
    "GE Vernova": "GE 에너지 부문 분사. 가스터빈, 풍력, 전력망",
    "Cameco": "우라늄 채굴 글로벌 1위. 원자력 발전 수혜. SMR 테마",
    # 엔터테인먼트/컬처
    "하이브": "BTS 소속사. K-POP 글로벌 1위. 위버스 플랫폼",
    "펄어비스": "검은사막 개발사. 붉은사막 신작 출시 예정",
    "삼양식품": "불닭볶음면 글로벌 히트. K푸드 대표주",
    # 기타
    "Rocket Lab": "소형 위성 발사체. 스페이스X 대항마. Neutron 로켓 개발",
    "UBTech": "휴머노이드 로봇. Walker 시리즈. 중국 로봇 선두",
    "Hesai": "라이다 센서. 자율주행 핵심 부품. 중국 라이다 1위",
}


def _get_stock_profile(name):
    """Get stock profile for deep research."""
    for key, profile in _STOCK_PROFILES.items():
        if key.lower() in name.lower() or key in name:
            return profile
    return None


def deep_research_analysis(etf_name, movers, per_etf_changes):
    """Use Claude API to generate deep research analysis for ETF."""
    if not HAS_CLAUDE:
        return None

    # Build context for Claude
    mover_details = []
    for m in movers[:5]:  # Top 5 movers
        profile = _get_stock_profile(m["name"])
        news_titles = [n.get("title", "") for n in m.get("news_items", [])[:3]]
        analysis = m.get("analysis", {})

        detail = {
            "name": m["name"],
            "ticker": m.get("ticker", ""),
            "weight": m["weight"],
            "diff": m.get("diff", 0),
            "is_new": m.get("is_new", False),
            "profile": profile,
            "news": news_titles,
            "basic_analysis": analysis,
        }
        mover_details.append(detail)

    # Find ups/downs from changes
    changes = None
    for c in per_etf_changes:
        if c["etf_name"] == etf_name:
            changes = c
            break

    prompt = f"""당신은 TIMEFOLIO ETF 포트폴리오 분석 전문가입니다.

## ETF: {etf_name}

## 주요 비중 변동 종목:
"""
    for d in mover_details:
        direction = "신규편입" if d["is_new"] else (f"+{d['diff']:.2f}%p 증가" if d["diff"] > 0 else f"{d['diff']:.2f}%p 감소")
        prompt += f"""
### {d['name']} ({d['ticker']}) - {direction}, 현재 비중 {d['weight']:.1f}%
- 종목 특성: {d['profile'] or '정보 없음'}
- 관련 뉴스: {'; '.join(d['news']) if d['news'] else '뉴스 없음'}
"""

    prompt += """
## 분석 요청:
위 정보를 바탕으로 각 종목별로 다음 형식으로 복합적 분석을 작성해주세요:

1. <b>[종목명]</b>: [종목의 사업 특성], [최근 뉴스/실적/업황]을 고려해 [비중 확대/축소/편입] 판단. [구체적 사유 1-2문장]

전체를 3-4개 종목으로 요약하고, 마지막에 ETF 전체 포트폴리오 방향성을 1문장으로 정리해주세요.
이모지 없이, 간결하게 작성하세요.
중요: <b>종목명</b> 형식으로 bold 태그를 반드시 사용하세요 (Telegram HTML 형식)."""

    try:
        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        return f"Deep research 실패: {e}"


def _clean_stock_name(name):
    for eng, kr in _KR_ALIASES.items():
        if eng.lower() in name.lower():
            return kr
    clean = re.sub(r'\s*(Corp|Inc|Ltd|PLC|Co|NV|SA|AG|SE|GmbH|Holdings?)[./\s]*', ' ', name)
    clean = re.sub(r'/\w+$', '', clean)
    return clean.strip()


def _strip_html(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&apos;", "'")
    text = re.sub(r'[\U00010000-\U0010FFFF]', '', text)
    return text.strip()


def _extract_ib(headline):
    for ib in _IB_NAMES:
        if ib in headline:
            return ib
    return None


# Noise patterns: price movement / intraday / meaningless
_NOISE_PATTERNS = [
    r'장중\s*(\d+|강세|약세|상승|하락)',
    r'전일\s*대비\s*\d+',
    r'\d+(\.\d+)?%\s*(상승|하락|급등|급락|↑|↓)',
    r'(상승|하락|보합)\s*(출발|마감|세)',
    r'시초가',
    r'^\d+원\s*(대|에|선|돌파)',
    r'소폭\s*(상승|하락|반등)',
    r'(약보합|강보합|보합세)',
    r'전장\s*대비',
    r'52주\s*(신고가|신저가|최고가|최저가)',
    r'\d+거래일\s*(연속|만에)',
    r'(개장|장초)\s*(상승|하락|강세|약세)',
    r'종가\s*\d+',
    r'낙폭\s*과대',
    r'주가\s*\d+%',
    # Result-type patterns (not causes)
    r'\d+년간?\s*\d+(\.\d+)?%',
    r'\d+(배|%)\s*(올|상승|급등|폭등|성장)',
    r'(올해|지난해|전년|연간|연초대비)\s*\d+(\.\d+)?%',
    r'(사상|역대)\s*(최고|최대|최저|최소)',
    r'(수익률|상승률|하락률|등락률)\s*\d+',
    r'\d+%\s*(수익|수익률|리턴)',
    r'(몇|얼마나)\s*(올|상승|하락)',
    r'[\'"]?(껑충|뚝|쑥|훌쩍)[\'"]?',
    r'(마감|장마감|종장)\s*(직전|직후)',
    r'vs\s+\w+\s*[\'"]?(뚝|하락)',
]


def _is_noise_headline(title):
    for pat in _NOISE_PATTERNS:
        if re.search(pat, title):
            return True
    return False


# Causal indicators: keywords suggesting a headline contains cause info
_CAUSAL_KEYWORDS = [
    "발표", "승인", "출시", "계약", "투자", "인수", "합병", "개발",
    "진출", "수주", "체결", "목표가", "상향", "하향", "리포트",
    "임상", "FDA", "정책", "규제", "파트너", "협력", "공급",
    "실적", "매출", "호실적", "어닝", "분사", "신작", "흥행",
    "커버리지", "매수", "전망", "분석", "전략", "재편",
    "수요", "수출", "성장", "확대", "둔화", "감소", "축소",
    "경쟁", "기술", "혁신", "특허", "라이선스",
    "관세", "트럼프", "바이든", "중국", "미국",
    "금리", "연준", "Fed", "인플레이션",
    "배터리", "반도체", "AI", "로봇", "우주", "방산", "바이오",
    "HBM", "낸드", "NAND", "GPU", "데이터센터",
    "GLP", "비만", "치료제", "신약", "파이프라인",
]


def _is_causal_headline(title):
    """Check if headline contains clear causal/actionable information."""
    return any(kw in title for kw in _CAUSAL_KEYWORDS)


def _is_stock_mentioned(headline, orig_name, clean_name):
    """Check if headline specifically mentions this stock."""
    hl_lower = headline.lower()
    # Check first significant English name part
    parts = [p for p in re.split(r'[\s/,.()\-]+', orig_name) if len(p) > 2]
    if parts and parts[0].lower() in hl_lower:
        return True
    # Check Korean alias parts
    for part in clean_name.split():
        if len(part) > 1 and part in headline:
            return True
    return False


def fetch_stock_news(name, limit=3):
    """Fetch news, filtering noise and result-type articles. Returns more to allow filtering."""
    clean = _clean_stock_name(name)
    query = urllib.parse.quote(f"{clean} 주가")
    url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; OpenClaw/1.0)"
    })
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            xml = resp.read().decode("utf-8")
        items = re.findall(r'<item>(.*?)</item>', xml, re.DOTALL)
        results = []
        for item_xml in items[:limit + 15]:
            title_m = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item_xml)
            source_m = re.search(r'<source[^>]*>(.*?)</source>', item_xml)
            if not title_m:
                continue
            raw_title = _strip_html(title_m.group(1))
            source = _strip_html(source_m.group(1)) if source_m else ""
            title = re.sub(r'\s*-\s*[^-]{2,30}$', '', raw_title)
            # Remove "By Investing.com" suffix
            title = re.sub(r'\s*By\s+Investing\.com\s*$', '', title, flags=re.IGNORECASE)
            if not title or len(title) <= 5:
                continue
            if _is_noise_headline(title):
                continue
            ib = _extract_ib(raw_title)
            is_causal = _is_causal_headline(title)
            is_relevant = _is_stock_mentioned(title, name, clean)
            results.append({
                "title": title,
                "source": source,
                "ib": ib,
                "is_causal": is_causal,
                "is_relevant": is_relevant,
            })
            if len(results) >= limit:
                break
        return results
    except Exception:
        return []


# ─── Keyword-based analysis (원인 + 판단) ─────────────────────────────
# Each rule: (keywords, (pos_cause, pos_judgment), (neg_cause, neg_judgment))
KEYWORD_RULES = [
    (["사노피", "우선순위", "보류", "중단"],
     ("파트너사 전략 재조정 속 파이프라인 가치 재평가",
      "독자 파이프라인 성장 가능성 주목 → 비중 확대 판단"),
     ("파트너사 개발 우선순위 하향/보류 결정",
      "기술이전 불확실성 확대 → 리스크 관리 차원 비중 축소 판단")),
    (["비만", "GLP", "오젠픽", "위고비", "경구", "알약"],
     ("GLP-1/비만 치료제 시장 급성장 및 경구제 개발 진전",
      "비만 치료제 파이프라인 가치 부각 → 비중 확대 판단"),
     ("비만 치료제 경쟁 심화 및 파이프라인 차별화 약화",
      "경쟁 격화에 따른 밸류에이션 부담 → 비중 축소 판단")),
    (["임상", "FDA", "승인", "신약", "파이프라인", "IND", "심사", "바이오", "항체", "ADC"],
     ("임상시험 진전 또는 FDA 승인/심사 기대",
      "파이프라인 가치 반영 → 비중 확대 판단"),
     ("임상 지연·실패 또는 FDA 심사 불확실성",
      "파이프라인 리스크 확대 → 비중 축소 판단")),
    (["합병", "인수", "M&A", "분사", "스핀오프"],
     ("M&A 또는 기업구조 변화로 가치 재평가",
      "사업 재편 시너지 기대 → 비중 확대 판단"),
     ("M&A 또는 구조 변화에 따른 불확실성",
      "통합 리스크 및 가치 희석 우려 → 비중 축소 판단")),
    (["출시", "흥행", "신작", "콘텐츠", "게임", "엔터"],
     ("신작 출시 또는 콘텐츠 흥행 모멘텀",
      "매출 성장 가시화 → 비중 확대 판단"),
     ("콘텐츠 부진 또는 신작 기대 하회",
      "매출 성장 둔화 우려 → 비중 축소 판단")),
    (["실적", "매출", "영업이익", "순이익", "호실적", "어닝", "흑자"],
     ("실적 서프라이즈 — 매출·이익 시장 예상 상회",
      "어닝 모멘텀 지속 기대 → 비중 확대 판단"),
     ("실적 부진 — 매출·이익 시장 예상 하회",
      "실적 하향 사이클 진입 우려 → 비중 축소 판단")),
    (["목표가", "투자의견", "리포트", "커버리지", "매수의견", "상향"],
     ("증권사 목표가 상향 또는 커버리지 개시",
      "시장 컨센서스 상향 → 비중 확대 판단"),
     ("증권사 목표가 하향 또는 투자의견 하향",
      "시장 기대치 하락 → 비중 축소 판단")),
    (["메모리", "낸드", "NAND", "HBM", "D램", "DRAM", "반도체", "SSD"],
     ("메모리/반도체 업황 개선 및 수요 확대",
      "업사이클 수혜 기대 → 비중 확대 판단"),
     ("반도체 업황 둔화 또는 수급 악화",
      "다운사이클 우려 → 비중 축소 판단")),
    (["딥시크", "DeepSeek", "경쟁", "대안"],
     ("AI 경쟁 구도 변화 속 새로운 수혜 가능성",
      "기술 차별화 또는 대안 부각 → 비중 확대 판단"),
     ("AI 경쟁 심화로 밸류에이션 재조정",
      "경쟁 격화에 따른 성장 우려 → 비중 축소 판단")),
    (["AI", "인공지능", "GPU", "데이터센터"],
     ("AI/데이터센터 수요 폭발적 성장",
      "AI 인프라 투자 확대 수혜 → 비중 확대 판단"),
     ("AI 경쟁 심화 또는 밸류에이션 부담",
      "성장 대비 고평가 우려 → 비중 축소 판단")),
    (["트럼프", "정책", "관세", "규제", "원자력", "에너지", "우라늄"],
     ("정책 수혜 기대 — 규제 완화 또는 보조금 확대",
      "정책 모멘텀에 따른 실적 개선 기대 → 비중 확대 판단"),
     ("정책·규제 리스크 — 관세 또는 규제 강화",
      "사업 환경 악화 우려 → 비중 축소 판단")),
    (["수주", "계약", "공급", "파트너", "구매"],
     ("대형 계약 체결 또는 공급 파트너십 확보",
      "매출 가시성 확대 → 비중 확대 판단"),
     ("수주 감소 또는 계약 불발/지연",
      "매출 파이프라인 약화 → 비중 축소 판단")),
    (["수출", "환율", "진출", "해외", "글로벌"],
     ("해외 시장 진출 확대 또는 수출 호조",
      "글로벌 성장 동력 확보 → 비중 확대 판단"),
     ("수출 둔화 또는 환율 악재",
      "해외 매출 감소 우려 → 비중 축소 판단")),
    (["로봇", "휴머노이드", "로보틱스", "자율주행", "무인"],
     ("로봇/휴머노이드 시장 성장 가속화",
      "신성장 동력 본격화 기대 → 비중 확대 판단"),
     ("로봇/자율화 기술 상용화 지연",
      "성장 기대 후퇴 → 비중 축소 판단")),
    (["K뷰티", "화장품", "뷰티", "스킨케어"],
     ("K뷰티 글로벌 수출 확대 및 트렌드 수혜",
      "해외 매출 성장 모멘텀 → 비중 확대 판단"),
     ("K뷰티 성장 둔화 또는 경쟁 심화",
      "수출 성장 둔화 우려 → 비중 축소 판단")),
    (["우주", "위성", "발사", "SpaceX", "스페이스"],
     ("우주 산업 성장 및 발사 사업 확대",
      "우주 사업 수혜 기대 → 비중 확대 판단"),
     ("우주 사업 수주 감소 또는 기술 경쟁 심화",
      "우주 사업 불확실성 → 비중 축소 판단")),
    (["광모듈", "광트랜시버", "통신장비", "네트워크"],
     ("AI 인프라 확대에 따른 광통신 수요 급증",
      "데이터센터 연결 수혜 → 비중 확대 판단"),
     ("광통신 수요 둔화 또는 가격 경쟁 심화",
      "마진 축소 우려 → 비중 축소 판단")),
    (["배터리", "리튬", "2차전지", "양극재", "음극재", "전해질"],
     ("배터리/2차전지 시장 확대 및 수요 회복",
      "EV 성장 수혜 기대 → 비중 확대 판단"),
     ("배터리 수요 둔화 또는 원자재 가격 부담",
      "업황 악화 우려 → 비중 축소 판단")),
    (["방산", "방위", "무기", "국방", "미사일", "천무"],
     ("방산 수출 확대 및 지정학적 수혜",
      "수출 계약 확대 모멘텀 → 비중 확대 판단"),
     ("방산 수주 감소 또는 예산 축소",
      "매출 가시성 약화 → 비중 축소 판단")),
]


def _get_cash_analysis(diff):
    """Special analysis for 현금 (cash position changes)."""
    if diff > 0:
        return {
            "causes": [
                "시장 변동성 확대에 따른 방어적 포지션 전환",
                "포트폴리오 리밸런싱 과정에서 현금 비중 자연 증가",
            ],
            "judgment": "리스크 관리 차원 현금 확보 판단",
        }
    return {
        "causes": [
            "유망 종목 투자 기회 포착 — 현금 집행",
            "시장 회복 기대에 따른 적극적 비중 확대",
        ],
        "judgment": "투자 기회 활용을 위한 현금 투입 판단",
    }


def analyze_headlines(news_items, diff, stock_name="", is_new=False):
    """Returns dict with:
    - causes: list of 1-2 strings (factual reasons for price change)
    - judgment: single string (weight change conclusion)
    Only uses headlines that are RELEVANT (mention the stock) AND CAUSAL.
    """
    # Get short display name for keyword causes
    display_name = _clean_stock_name(stock_name).split()[0] if stock_name else ""

    # Only use relevant + causal headlines
    relevant_causal = [n["title"] for n in news_items
                       if n.get("is_relevant") and n.get("is_causal")] if news_items else []
    # Relevant headlines for keyword matching
    relevant_headlines = [n["title"] for n in news_items
                         if n.get("is_relevant")] if news_items else []

    if is_new:
        causes = []
        judgment = "신규 편입 — 포트폴리오 다변화 또는 신규 테마 반영"
        if relevant_headlines:
            combined = " ".join(relevant_headlines)
            for keywords, pos_t, neg_t in KEYWORD_RULES:
                if any(kw in combined for kw in keywords):
                    cause_text = f"{display_name}, {pos_t[0]}" if display_name else pos_t[0]
                    causes.append(cause_text)
                    judgment = "신규 편입 — " + pos_t[1].split(" → ")[0]
                    break
            if relevant_causal:
                hl = relevant_causal[0][:65]
                if not causes or hl != causes[0]:
                    causes.append(hl)
        if not causes:
            causes = ["신규 편입 종목 — 포트폴리오 구성 변경"]
        return {"causes": causes[:2], "judgment": judgment}

    if not relevant_headlines:
        dir_text = "비중 확대" if diff > 0 else "비중 축소"
        return {"causes": [f"관련 사유 확인 불가"],
                "judgment": f"{dir_text} 판단"}

    combined = " ".join(relevant_headlines)
    keyword_cause = None
    keyword_judgment = None

    for keywords, pos_t, neg_t in KEYWORD_RULES:
        if any(kw in combined for kw in keywords):
            t = pos_t if diff > 0 else neg_t
            keyword_cause = f"{display_name}, {t[0]}" if display_name else t[0]
            keyword_judgment = t[1]
            break

    # Build causes list: relevant causal headlines first, then keyword cause
    causes = []
    for hl in relevant_causal[:2]:
        if len(hl) > 70:
            hl = hl[:68] + ".."
        causes.append(hl)

    if keyword_cause:
        if len(causes) < 2 and keyword_cause not in causes:
            causes.append(keyword_cause)

    if not causes:
        dir_text = "비중 확대" if diff > 0 else "비중 축소"
        causes = [f"관련 사유 확인 불가"]

    if keyword_judgment:
        judgment = keyword_judgment
    elif diff > 0:
        judgment = "비중 확대 판단"
    else:
        judgment = "비중 축소 판단"

    return {"causes": causes[:2], "judgment": judgment}


# ─── Text formatting (fallback) ──────────────────────────────────────
def _ticker_label(item):
    tk = item.get("ticker", "")
    return f"{tk}  " if tk else ""


def build_text_report(group_label, date, per_etf_changes,
                      etf_sections, movers_with_news, errors):
    lines = [
        f"TIMEFOLIO {group_label} ETF 리포트",
        f"{date}",
        "=" * 32, "",
    ]
    for etf in per_etf_changes:
        lines.append(f"[ {etf['etf_name']} 1일 비중 증가 TOP 5 ]")
        for i, u in enumerate(etf["ups"][:5], 1):
            tk = _ticker_label(u)
            lines.append(f"  {i}. {tk}{u['name']}  "
                          f"{u['weight']:.1f}%  {_diff_str(u['diff'])}%p")
        lines += ["", f"[ {etf['etf_name']} 1일 비중 감소 BOTTOM 3 ]"]
        for i, d in enumerate(etf["downs"][:3], 1):
            tk = _ticker_label(d)
            lines.append(f"  {i}. {tk}{d['name']}  "
                          f"{d['weight']:.1f}%  {_diff_str(d['diff'])}%p")
        lines.append("")

    lines += ["", "-" * 32, ""]
    for sect in etf_sections:
        lines.append(f"[ {sect['name']} | {sect['count']}종목 ]")
        for r in sect["rows"]:
            lines.append(f"  {r['rank']:>2}. {r['ticker']:<12} {r['name']:<20} "
                          f"{r['weight']:>6}  1D:{_diff_str(r['d1']):>7}  "
                          f"1W:{_diff_str(r['w1']):>7}  1M:{_diff_str(r['m1']):>7}")
        lines.append("")

    if movers_with_news:
        lines += ["-" * 32, "[ 주요 종목 뉴스 분석 (1D 기준) ]", ""]
        for i, m in enumerate(movers_with_news, 1):
            tk = _ticker_label(m)
            is_new = m.get("is_new", False)
            if is_new:
                lines.append(f"{i}. {tk}{m['name']} ({m['etf_short']})  [신규편입] {m['weight']:.1f}%")
            else:
                ds = _diff_str(m["diff"])
                lines.append(f"{i}. {tk}{m['name']} ({m['etf_short']})  {ds}%p -> {m['weight']:.1f}%")
            analysis = m.get("analysis", {})
            if isinstance(analysis, dict):
                for cause in analysis.get("causes", []):
                    lines.append(f"   • {cause}")
                lines.append(f"   ▸ {analysis.get('judgment', '')}")
            else:
                lines.append(f"   -> {analysis}")
            lines.append("")

    if errors:
        lines.append(f"Errors: {', '.join(errors)}")
    return "\n".join(lines)


def _build_basic_etf_analysis(changes, movers):
    """Fallback basic analysis when Claude API is not available.

    Uses HTML formatting for Telegram.
    """
    lines = []
    ups = changes.get("ups", [])
    downs = changes.get("downs", [])

    if ups:
        top_up = ups[0]
        lines.append(f"• <b>{top_up['name']}</b>: +{top_up['diff']:.2f}%p 증가")
    if downs:
        top_down = downs[0]
        lines.append(f"• <b>{top_down['name']}</b>: {top_down['diff']:.2f}%p 감소")

    new_stocks = [m for m in movers if m.get("is_new")]
    if new_stocks:
        new_names = ", ".join([f"<b>{s['name'][:10]}</b>" for s in new_stocks[:3]])
        lines.append(f"• 신규편입: {new_names}")

    key_judgments = []
    for m in movers[:2]:
        analysis = m.get("analysis", {})
        if isinstance(analysis, dict):
            jd = analysis.get("judgment", "")
            if jd and "→" in jd:
                key_judgments.append(jd.split("→")[0].strip())
    if key_judgments:
        lines.append(f"• 주요 사유: {'; '.join(key_judgments[:2])}")

    return "\n".join(lines)


# ─── Deep Analysis Summary ────────────────────────────────────────────
def build_analysis_summary(group_label, date, per_etf_changes, per_etf_news, use_deep_research=True):
    """Generate deep analysis summary for Telegram message with Claude API deep research.

    Uses HTML formatting for Telegram (parse_mode='HTML'):
    - <b>bold</b> for emphasis
    - <i>italic</i> for secondary emphasis
    """
    lines = [f"📊 <b>TIMEFOLIO {group_label} ETF 분석 리포트</b>", f"📅 {date}", ""]

    # Deep research for each ETF
    for i, (changes, news) in enumerate(zip(per_etf_changes, per_etf_news)):
        etf_name = changes["etf_name"]
        movers = news.get("movers", [])

        lines.append(f"<b>▶ {etf_name}</b>")
        lines.append("")

        # Use Claude API for deep research
        if use_deep_research and HAS_CLAUDE and movers:
            deep_analysis = deep_research_analysis(etf_name, movers, per_etf_changes)
            if deep_analysis and not deep_analysis.startswith("Deep research 실패"):
                lines.append(deep_analysis)
            else:
                # Fallback to basic analysis
                lines.append(_build_basic_etf_analysis(changes, movers))
        else:
            lines.append(_build_basic_etf_analysis(changes, movers))

        lines.append("")

    # Overall portfolio analysis
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("<b>📈 포트폴리오 종합 판단</b>")
    lines.append("")

    # Aggregate analysis
    total_ups = sum(len(c.get("ups", [])) for c in per_etf_changes)
    total_downs = sum(len(c.get("downs", [])) for c in per_etf_changes)
    all_new = []
    cash_changes = []

    for news in per_etf_news:
        for m in news.get("movers", []):
            if m.get("is_new"):
                all_new.append(m["name"])
            if m.get("name") == "현금":
                cash_changes.append(m.get("diff", 0))

    # Determine market stance
    if cash_changes:
        avg_cash = sum(cash_changes) / len(cash_changes)
        if avg_cash > 0.3:
            lines.append("• <b>방어적 포지션</b> 전환 — 현금 비중 증가 추세")
        elif avg_cash < -0.3:
            lines.append("• <b>적극적 투자 확대</b> — 현금 비중 감소 추세")

    # Sector rotation hints
    all_movers = []
    for news in per_etf_news:
        all_movers.extend(news.get("movers", []))

    # Extract key themes from judgments
    themes = {"AI": 0, "반도체": 0, "바이오": 0, "실적": 0, "정책": 0}
    for m in all_movers:
        analysis = m.get("analysis", {})
        if isinstance(analysis, dict):
            jd = analysis.get("judgment", "")
            causes = analysis.get("causes", [])
            text = jd + " ".join(causes)
            for theme in themes:
                if theme in text:
                    themes[theme] += 1

    top_themes = sorted(themes.items(), key=lambda x: x[1], reverse=True)[:2]
    if top_themes[0][1] > 0:
        theme_str = ", ".join([f"<b>{t[0]}</b>" for t in top_themes if t[1] > 0])
        lines.append(f"• 주요 테마: {theme_str} 섹터 중심 리밸런싱")

    # New additions summary
    if all_new:
        lines.append(f"• <b>신규편입</b>: {len(all_new)}개 — 포트폴리오 다변화 진행")

    # Final conclusion
    lines.append("")
    if total_ups > total_downs * 1.5:
        lines.append("💡 <b>결론</b>: 전반적 비중 확대 기조 — 시장 상승 기대감 반영")
    elif total_downs > total_ups * 1.5:
        lines.append("💡 <b>결론</b>: 전반적 비중 축소 기조 — 리스크 관리 강화")
    else:
        lines.append("💡 <b>결론</b>: 섹터별 선별적 리밸런싱 — 차별화 전략 유지")

    return "\n".join(lines)


# ─── Main ─────────────────────────────────────────────────────────────

# Knowledge base path for Obsidian
KNOWLEDGE_BASE = os.path.join(os.path.dirname(__file__), "..", "knowledge")


def save_to_obsidian(group_label, date, per_etf_changes, per_etf_news, analysis_summary):
    """Save analysis results to Obsidian knowledge base for RON's market learning."""
    if not os.path.exists(KNOWLEDGE_BASE):
        os.makedirs(KNOWLEDGE_BASE, exist_ok=True)

    # 1. Save daily report
    daily_dir = os.path.join(KNOWLEDGE_BASE, "daily")
    os.makedirs(daily_dir, exist_ok=True)

    label_map = {"국내": "domestic", "해외": "overseas", "전체": "all"}
    filename = f"{date}_{label_map.get(group_label, group_label)}.md"

    # Convert HTML to Markdown for Obsidian
    md_summary = analysis_summary.replace("<b>", "**").replace("</b>", "**")

    daily_content = f"""# {group_label} ETF 분석 - {date}

## 분석 요약
{md_summary}

## 메타데이터
- 생성일시: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- 분석 대상: {group_label} ETF
- ETF 수: {len(per_etf_changes)}

## 관련 링크
"""
    # Add stock links
    all_stocks = set()
    for news in per_etf_news:
        for m in news.get("movers", []):
            all_stocks.add(m["name"])

    for stock in sorted(all_stocks):
        daily_content += f"- [[stocks/{stock}]]\n"

    # Add ETF links
    daily_content += "\n"
    for changes in per_etf_changes:
        etf_name = changes["etf_name"]
        daily_content += f"- [[etfs/{etf_name}]]\n"

    with open(os.path.join(daily_dir, filename), "w", encoding="utf-8") as f:
        f.write(daily_content)

    # 2. Update stock profiles with history
    stocks_dir = os.path.join(KNOWLEDGE_BASE, "stocks")
    os.makedirs(stocks_dir, exist_ok=True)

    for news in per_etf_news:
        etf_name = news["etf_name"]
        for m in news.get("movers", []):
            stock_name = m["name"]
            stock_file = os.path.join(stocks_dir, f"{stock_name}.md")

            # Get existing content or create new
            if os.path.exists(stock_file):
                with open(stock_file, "r", encoding="utf-8") as f:
                    existing = f.read()
            else:
                profile = _STOCK_PROFILES.get(stock_name, "프로필 미등록")
                existing = f"""# {stock_name}

## 프로필
{profile}

## 변동 히스토리
| 날짜 | ETF | 변동 | 판단 |
|------|-----|------|------|
"""

            # Add new history entry
            diff = m.get("diff", 0)
            analysis = m.get("analysis", {})
            judgment = ""
            if isinstance(analysis, dict):
                judgment = analysis.get("judgment", "")[:30]

            diff_str = f"+{diff:.2f}%p" if diff > 0 else f"{diff:.2f}%p"
            if m.get("is_new"):
                diff_str = "신규편입"

            new_entry = f"| {date} | {etf_name} | {diff_str} | {judgment} |\n"

            # Insert after header row if not already present
            if date not in existing:
                # Find the header row and insert after
                lines = existing.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("|---"):
                        lines.insert(i + 1, new_entry.strip())
                        break
                existing = "\n".join(lines)

                with open(stock_file, "w", encoding="utf-8") as f:
                    f.write(existing)

    # 3. Update ETF profiles
    etfs_dir = os.path.join(KNOWLEDGE_BASE, "etfs")
    os.makedirs(etfs_dir, exist_ok=True)

    for changes in per_etf_changes:
        etf_name = changes["etf_name"]
        etf_file = os.path.join(etfs_dir, f"{etf_name}.md")

        if os.path.exists(etf_file):
            with open(etf_file, "r", encoding="utf-8") as f:
                existing = f.read()
        else:
            existing = f"""# {etf_name}

## 전략 히스토리
| 날짜 | 주요 증가 | 주요 감소 | 방향성 |
|------|----------|----------|--------|
"""

        if date not in existing:
            ups = changes.get("ups", [])
            downs = changes.get("downs", [])
            top_up = ups[0]["name"] if ups else "-"
            top_down = downs[0]["name"] if downs else "-"
            direction = "확대" if len(ups) > len(downs) else "축소" if len(downs) > len(ups) else "중립"

            new_entry = f"| {date} | [[stocks/{top_up}]] | [[stocks/{top_down}]] | {direction} |\n"

            lines = existing.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("|---"):
                    lines.insert(i + 1, new_entry.strip())
                    break
            existing = "\n".join(lines)

            with open(etf_file, "w", encoding="utf-8") as f:
                f.write(existing)

    # 4. Update theme tracking
    themes_dir = os.path.join(KNOWLEDGE_BASE, "themes")
    os.makedirs(themes_dir, exist_ok=True)

    theme_stocks = {
        "AI": ["NVIDIA", "Alphabet", "Microsoft", "Meta", "Tesla"],
        "반도체": ["SK하이닉스", "삼성전자", "Sandisk", "NVIDIA", "AMD"],
        "바이오": ["에이비엘바이오", "에이프릴바이오", "알테오젠", "삼성바이오로직스"],
    }

    for theme, keywords in theme_stocks.items():
        theme_file = os.path.join(themes_dir, f"{theme}.md")

        if os.path.exists(theme_file):
            with open(theme_file, "r", encoding="utf-8") as f:
                existing = f.read()
        else:
            existing = f"""# {theme} 테마

## 관련 종목
{chr(10).join([f'- [[stocks/{s}]]' for s in keywords])}

## 트렌드 히스토리
| 날짜 | 종목 동향 | 비고 |
|------|----------|------|
"""

        if date not in existing:
            # Check which theme stocks moved
            moved = []
            for news in per_etf_news:
                for m in news.get("movers", []):
                    if m["name"] in keywords:
                        diff = m.get("diff", 0)
                        moved.append(f"{m['name']}({'+' if diff > 0 else ''}{diff:.1f}%p)")

            if moved:
                new_entry = f"| {date} | {', '.join(moved[:3])} | {group_label} ETF |\n"

                lines = existing.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("|---"):
                        lines.insert(i + 1, new_entry.strip())
                        break
                existing = "\n".join(lines)

                with open(theme_file, "w", encoding="utf-8") as f:
                    f.write(existing)

    return True


def run(etf_keys=None, generate_images=True):
    """Returns (text_report, [image_paths])."""
    if etf_keys is None:
        etf_keys = list(ETFS.keys())

    date = None
    errors = []

    per_etf_changes = []
    etf_sections = []
    per_etf_news = []

    is_overseas = set(etf_keys) <= set(OVERSEAS_KEYS)

    for key in etf_keys:
        if key not in ETFS:
            errors.append(f"Unknown ETF: {key}")
            continue

        cfg = ETFS[key]
        try:
            html = fetch_page(cfg["idx"], cfg["cate"])
            page_date = parse_date(html)
            if date is None:
                date = page_date
            holdings = parse_full_holdings(html)
            save_data(key, page_date, holdings)

            ticker_map = {h["name"]: h.get("ticker", "") for h in holdings}

            avail_dates = parse_available_dates(html)
            current_dot = page_date.replace("-", ".")
            d1_date, w1_date = find_comparison_dates(avail_dates, current_dot)

            # 1D comparison (primary basis for changes & movers & 신규편입)
            d1_map = {}
            d1_holdings = None
            d1_news = []  # 1D 신규편입
            if d1_date:
                d1_html = fetch_page_for_date(cfg["idx"], cfg["cate"], d1_date)
                if d1_html:
                    d1_holdings = parse_full_holdings(d1_html)
                    d1_weight_map = build_weight_map(d1_holdings)
                    d1_map = build_diff_map_from_weights(holdings, d1_weight_map)
                    # Detect 1D 신규편입: stocks in current but not in d1
                    for h in holdings:
                        if h["name"] not in d1_weight_map and h["name"] != "현금":
                            d1_news.append({
                                "name": h["name"],
                                "weight": h["weight"],
                                "ticker": h.get("ticker", ""),
                            })

            # 1W comparison
            w1_map = {}
            if w1_date:
                w1_html = fetch_page_for_date(cfg["idx"], cfg["cate"], w1_date)
                if w1_html:
                    w1_holdings = parse_full_holdings(w1_html)
                    w1_map = build_diff_map_from_weights(holdings, build_weight_map(w1_holdings))

            # 1M comparison (for Holdings table + 신규편입 detection)
            m1 = fetch_period_comparison(cfg["idx"], "pdfM1")
            m1_map = {}
            m1_news = []
            if m1 and "today" in m1:
                for item in m1["today"]:
                    inc = item.get("increaseWei", "0")
                    if inc in ("신규", "\uc2e0\uaddc"):
                        m1_map[item["prodNm"]] = "NEW"
                        m1_news.append({
                            "name": item["prodNm"],
                            "weight": float(item["wei"]),
                            "ticker": ticker_map.get(item["prodNm"], ""),
                        })
                    else:
                        try:
                            m1_map[item["prodNm"]] = float(inc)
                        except ValueError:
                            pass

            # Build 1D-based ups/downs for changes section
            d1_ups, d1_downs = build_d1_changes(holdings, d1_map)

            # Fallback to m1 if no d1 data
            if not d1_ups and not d1_downs:
                m1_ups_fb, m1_downs_fb, _ = parse_ajax_changes(m1, ticker_map)
                change_ups = m1_ups_fb[:5]
                change_downs = m1_downs_fb[:3]
                change_basis = "1M"
            else:
                change_ups = d1_ups[:5]
                change_downs = d1_downs[:3]
                change_basis = "1D"

            per_etf_changes.append({
                "etf_name": cfg["name"],
                "ups": change_ups,
                "downs": change_downs,
                "basis": change_basis,
            })

            # Holdings rows (keep all diff columns)
            rows = []
            h_name_limit = 24 if is_overseas else 18
            for i, h in enumerate(holdings[:10], 1):
                name = h["name"]
                if len(name) > h_name_limit:
                    name = name[:h_name_limit - 2] + ".."
                m1v = m1_map.get(h["name"])
                rows.append({
                    "rank": str(i),
                    "ticker": h.get("ticker", ""),
                    "name": name,
                    "weight": f"{h['weight']:.1f}%",
                    "d1": d1_map.get(h["name"]),
                    "w1": w1_map.get(h["name"]),
                    "m1": m1v,
                })
            etf_sections.append({
                "name": cfg["name"],
                "count": len(holdings),
                "rows": rows,
            })

            # Movers with news (1D basis)
            n_movers = 5 if is_overseas else 3
            etf_movers_raw = sorted(
                change_ups[:5] + change_downs[:3],
                key=lambda x: abs(x["diff"]), reverse=True
            )[:n_movers]

            etf_movers = []
            for item in etf_movers_raw:
                if item["name"] == "현금":
                    analysis = _get_cash_analysis(item["diff"])
                    etf_movers.append({
                        **item,
                        "etf_short": cfg["name"],
                        "news_items": [],
                        "analysis": analysis,
                        "is_new": False,
                    })
                else:
                    news_items = fetch_stock_news(item["name"], limit=3)
                    analysis = analyze_headlines(news_items, item["diff"],
                                                stock_name=item["name"])
                    etf_movers.append({
                        **item,
                        "etf_short": cfg["name"],
                        "news_items": news_items,
                        "analysis": analysis,
                        "is_new": False,
                    })

            # 신규편입 stocks (1D basis) - show all
            for item in d1_news:
                news_items = fetch_stock_news(item["name"], limit=3)
                analysis = analyze_headlines(news_items, 0,
                                            stock_name=item["name"], is_new=True)
                etf_movers.append({
                    **item,
                    "diff": 0,
                    "etf_short": cfg["name"],
                    "news_items": news_items,
                    "analysis": analysis,
                    "is_new": True,
                })

            per_etf_news.append({
                "etf_name": cfg["name"],
                "movers": etf_movers,
            })

        except Exception as e:
            errors.append(f"{key}: {e}")

    keys_set = set(etf_keys)
    if keys_set <= set(OVERSEAS_KEYS):
        group_label = "해외"
    elif keys_set <= set(DOMESTIC_KEYS):
        group_label = "국내"
    else:
        group_label = "전체"

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    image_paths = []
    if generate_images and HAS_MPL:
        p1 = render_page1(group_label, date, per_etf_changes, etf_sections,
                          is_overseas=is_overseas)
        if p1:
            image_paths.append(p1)
        p2 = render_page2_news(group_label, date, per_etf_news)
        if p2:
            image_paths.append(p2)

    all_movers_news = []
    for en in per_etf_news:
        all_movers_news.extend(en.get("movers", []))

    report = build_text_report(group_label, date, per_etf_changes,
                                etf_sections, all_movers_news, errors)

    # Build analysis summary for Telegram
    analysis_summary = build_analysis_summary(group_label, date,
                                               per_etf_changes, per_etf_news)

    # Save to Obsidian knowledge base for RON's learning
    try:
        save_to_obsidian(group_label, date, per_etf_changes, per_etf_news, analysis_summary)
    except Exception as e:
        print(f"Warning: Failed to save to Obsidian: {e}")

    return report, image_paths, analysis_summary


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["overseas"] or args == ["\ud574\uc678"]:
        report, images, summary = run(OVERSEAS_KEYS)
        print(report)
        print("\n" + "=" * 40 + "\n")
        print(summary)
        if images:
            print(f"\nImages: {', '.join(images)}")
    elif args == ["domestic"] or args == ["\uad6d\ub0b4"]:
        report, images, summary = run(DOMESTIC_KEYS)
        print(report)
        print("\n" + "=" * 40 + "\n")
        print(summary)
        if images:
            print(f"\nImages: {', '.join(images)}")
    else:
        all_images = []
        all_summaries = []
        for group_keys in [DOMESTIC_KEYS, OVERSEAS_KEYS]:
            report, images, summary = run(group_keys)
            print(report)
            print()
            all_images.extend(images)
            all_summaries.append(summary)
        print("\n" + "=" * 40 + "\n")
        for s in all_summaries:
            print(s)
            print()
        if all_images:
            print(f"\nAll Images: {', '.join(all_images)}")
