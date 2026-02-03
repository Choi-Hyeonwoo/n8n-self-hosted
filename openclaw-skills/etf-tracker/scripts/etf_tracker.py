#!/usr/bin/env python3
"""
TIMEFOLIO ETF Holdings Tracker v5
- Page 1: 비중 증가 TOP 5 + 비중 감소 BOTTOM 3 (이미지)
- Page 2: Holdings TOP 10 × 3 ETF 세로 합치기 (#, Ticker, 종목명, 비중, 1D, 1W, 1M)
- Page 3: 주요 종목 뉴스 분석 (이미지)
- 텍스트 리포트 (fallback)
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


def fetch_period_comparison(idx, period):
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


def load_daily(etf_key, current_date):
    return load_nearest(etf_key, current_date, direction="before", max_days=3)


def load_weekly(etf_key, current_date):
    return load_nearest(etf_key, current_date, direction="before", max_days=10)


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


def _build_diff_map(holdings, prev_data):
    """Build {name: diff} map from today vs prev stored data."""
    if not prev_data:
        return {}
    prev_map = {h["name"]: h["weight"] for h in prev_data.get("holdings", [])}
    result = {}
    for h in holdings:
        pw = prev_map.get(h["name"])
        if pw is not None:
            result[h["name"]] = round(h["weight"] - pw, 2)
    return result


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


def _draw_table_rows(ax, rows, col_defs, y_start, row_h, fonts, fig_w):
    """Draw table rows. col_defs: [(x, key, align, font_key, color_fn)]"""
    font, _, _, font_header, font_small, _ = fonts
    font_map = {"normal": font, "header": font_header, "small": font_small}

    for idx, row in enumerate(rows):
        y = y_start - idx * row_h
        if idx % 2 == 0:
            ax.add_patch(plt.Rectangle((0.15, y - row_h / 2 + 0.02),
                                        fig_w - 0.3, row_h,
                                        facecolor="#F8F9FA", edgecolor="none", zorder=1))
        for x, key, align, fkey, color_fn in col_defs:
            val = row.get(key, "")
            text = _diff_str(val) if color_fn else (val if isinstance(val, str) else str(val))
            color = _diff_color(val) if color_fn else "#333333"
            f = font_map.get(fkey, font)
            ax.text(x, y, text, fontproperties=f,
                    ha=align, va="center", color=color, zorder=3)


# ─── Page 1: 비중 변동 TOP 5 + BOTTOM 3 ─────────────────────────────
def render_page_changes(group_label, date, ups, downs, new_items):
    if not HAS_MPL:
        return None
    fonts = _get_fonts()
    font, font_title, font_section, font_header, font_small, _ = fonts

    n_ups = min(len(ups), 5)
    n_downs = min(len(downs), 3)
    n_new = min(len(new_items), 3) if new_items else 0
    row_h = 0.38
    sect_h = 0.48
    has_new = n_new > 0

    fig_h = (0.75 + sect_h + n_ups * row_h + 0.15
             + sect_h + n_downs * row_h + 0.15)
    if has_new:
        fig_h += sect_h + n_new * row_h + 0.1
    fig_h += 0.2
    fig_w = 12.5

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    col = {"rank": 0.4, "ticker": 1.6, "name": 3.8, "etf": 6.3, "weight": 8.0, "diff": 10.0, "new_tag": 11.5}

    # Title
    y = fig_h - 0.45
    ax.text(fig_w / 2, y, f"TIMEFOLIO {group_label} ETF  비중 변동",
            fontproperties=font_title, ha="center", va="center", color="#1A1A2E")
    ax.text(fig_w - 0.3, y, date, fontproperties=font_small,
            ha="right", va="center", color="#888888")

    # ─ UP section ─
    y -= 0.55
    ax.add_patch(plt.Rectangle((0.15, y - 0.17), fig_w - 0.3, 0.38,
                                facecolor="#C62828", edgecolor="none", zorder=2))
    ax.text(0.4, y + 0.02, "비중 증가 TOP 5", fontproperties=font_section,
            ha="left", va="center", color="white", zorder=3)
    # Column headers
    y -= 0.4
    for x, label in [(col["rank"], "#"), (col["ticker"], "Ticker"),
                      (col["name"], "종목명"), (col["etf"], "ETF"),
                      (col["weight"], "비중"), (col["diff"], "1M 변동")]:
        ax.text(x, y, label, fontproperties=font_header,
                ha="center", va="center", color="#666666")
    y -= 0.08

    for i, item in enumerate(ups[:5]):
        y -= row_h
        if i % 2 == 0:
            ax.add_patch(plt.Rectangle((0.15, y - row_h / 2 + 0.02),
                                        fig_w - 0.3, row_h,
                                        facecolor="#FFF5F5", edgecolor="none", zorder=1))
        ax.text(col["rank"], y, str(i + 1), fontproperties=font_small,
                ha="center", va="center", color="#555", zorder=3)
        ax.text(col["ticker"], y, item.get("ticker", ""), fontproperties=font_header,
                ha="center", va="center", color="#2C3E50", zorder=3)
        name = item["name"][:20] + ".." if len(item["name"]) > 20 else item["name"]
        ax.text(col["name"], y, name, fontproperties=font,
                ha="center", va="center", color="#333", zorder=3)
        ax.text(col["etf"], y, item.get("etf_short", ""), fontproperties=font_small,
                ha="center", va="center", color="#777", zorder=3)
        ax.text(col["weight"], y, f"{item['weight']:.1f}%", fontproperties=font,
                ha="center", va="center", color="#333", zorder=3)
        ds = _diff_str(item["diff"])
        ax.text(col["diff"], y, ds, fontproperties=font,
                ha="center", va="center", color="#D32F2F", zorder=3)

    # ─ DOWN section ─
    y -= 0.55
    ax.add_patch(plt.Rectangle((0.15, y - 0.17), fig_w - 0.3, 0.38,
                                facecolor="#1565C0", edgecolor="none", zorder=2))
    ax.text(0.4, y + 0.02, "비중 감소 BOTTOM 3", fontproperties=font_section,
            ha="left", va="center", color="white", zorder=3)
    y -= 0.4
    for x, label in [(col["rank"], "#"), (col["ticker"], "Ticker"),
                      (col["name"], "종목명"), (col["etf"], "ETF"),
                      (col["weight"], "비중"), (col["diff"], "1M 변동")]:
        ax.text(x, y, label, fontproperties=font_header,
                ha="center", va="center", color="#666666")
    y -= 0.08

    for i, item in enumerate(downs[:3]):
        y -= row_h
        if i % 2 == 0:
            ax.add_patch(plt.Rectangle((0.15, y - row_h / 2 + 0.02),
                                        fig_w - 0.3, row_h,
                                        facecolor="#F5F8FF", edgecolor="none", zorder=1))
        ax.text(col["rank"], y, str(i + 1), fontproperties=font_small,
                ha="center", va="center", color="#555", zorder=3)
        ax.text(col["ticker"], y, item.get("ticker", ""), fontproperties=font_header,
                ha="center", va="center", color="#2C3E50", zorder=3)
        name = item["name"][:20] + ".." if len(item["name"]) > 20 else item["name"]
        ax.text(col["name"], y, name, fontproperties=font,
                ha="center", va="center", color="#333", zorder=3)
        ax.text(col["etf"], y, item.get("etf_short", ""), fontproperties=font_small,
                ha="center", va="center", color="#777", zorder=3)
        ax.text(col["weight"], y, f"{item['weight']:.1f}%", fontproperties=font,
                ha="center", va="center", color="#333", zorder=3)
        ds = _diff_str(item["diff"])
        ax.text(col["diff"], y, ds, fontproperties=font,
                ha="center", va="center", color="#1565C0", zorder=3)

    # ─ NEW section ─
    if has_new:
        y -= 0.55
        ax.add_patch(plt.Rectangle((0.15, y - 0.17), fig_w - 0.3, 0.38,
                                    facecolor="#2E7D32", edgecolor="none", zorder=2))
        ax.text(0.4, y + 0.02, "신규 편입", fontproperties=font_section,
                ha="left", va="center", color="white", zorder=3)
        y -= 0.4
        for x, label in [(col["rank"], "#"), (col["ticker"], "Ticker"),
                          (col["name"], "종목명"), (col["etf"], "ETF"),
                          (col["weight"], "비중")]:
            ax.text(x, y, label, fontproperties=font_header,
                    ha="center", va="center", color="#666666")
        y -= 0.08
        for i, item in enumerate(new_items[:3]):
            y -= row_h
            if i % 2 == 0:
                ax.add_patch(plt.Rectangle((0.15, y - row_h / 2 + 0.02),
                                            fig_w - 0.3, row_h,
                                            facecolor="#F5FFF5", edgecolor="none", zorder=1))
            ax.text(col["rank"], y, str(i + 1), fontproperties=font_small,
                    ha="center", va="center", color="#555", zorder=3)
            ax.text(col["ticker"], y, item.get("ticker", ""), fontproperties=font_header,
                    ha="center", va="center", color="#2C3E50", zorder=3)
            name = item["name"][:20] + ".." if len(item["name"]) > 20 else item["name"]
            ax.text(col["name"], y, name, fontproperties=font,
                    ha="center", va="center", color="#333", zorder=3)
            ax.text(col["etf"], y, item.get("etf_short", ""), fontproperties=font_small,
                    ha="center", va="center", color="#777", zorder=3)
            ax.text(col["weight"], y, f"{item['weight']:.1f}%", fontproperties=font,
                    ha="center", va="center", color="#4CAF50", zorder=3)

    path = os.path.join(IMG_DIR, f"etf_p1_changes_{date}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white", pad_inches=0.1)
    plt.close(fig)
    return path


# ─── Page 2: Holdings TOP 10 × 3 ETF (stacked) ─────────────────────
def render_page_holdings(group_label, date, etf_sections):
    """etf_sections: list of {name, count, rows: [{rank,ticker,name,weight,d1,w1,m1}]}"""
    if not HAS_MPL or not etf_sections:
        return None
    fonts = _get_fonts()
    font, font_title, font_section, font_header, font_small, _ = fonts

    row_h = 0.34
    sect_head_h = 0.42
    col_head_h = 0.32
    spacing = 0.25

    total_rows = sum(len(s["rows"]) for s in etf_sections)
    n_sects = len(etf_sections)

    fig_h = (0.7 + n_sects * (sect_head_h + col_head_h) + total_rows * row_h
             + (n_sects - 1) * spacing + 0.3)
    fig_w = 12.5

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    col = {"rank": 0.35, "ticker": 1.5, "name": 3.6,
           "weight": 5.8, "d1": 7.3, "w1": 8.9, "m1": 10.5}
    col_labels = [("rank", "#"), ("ticker", "Ticker"), ("name", "종목명"),
                  ("weight", "비중"), ("d1", "1D"), ("w1", "1W"), ("m1", "1M")]

    # Title
    y = fig_h - 0.4
    ax.text(fig_w / 2, y, f"TIMEFOLIO {group_label} ETF  Holdings TOP 10",
            fontproperties=font_title, ha="center", va="center", color="#1A1A2E")
    ax.text(fig_w - 0.3, y, date, fontproperties=font_small,
            ha="right", va="center", color="#888888")

    y -= 0.45

    for si, sect in enumerate(etf_sections):
        # Section header
        ax.add_patch(plt.Rectangle((0.15, y - 0.17), fig_w - 0.3, 0.38,
                                    facecolor="#2C3E50", edgecolor="none", zorder=2))
        ax.text(0.4, y + 0.02, f"{sect['name']}  ({sect['count']}종목)",
                fontproperties=font_section, ha="left", va="center",
                color="white", zorder=3)
        y -= sect_head_h

        # Column headers
        for ck, cl in col_labels:
            ax.text(col[ck], y, cl, fontproperties=font_header,
                    ha="center", va="center", color="#888888")
        y -= col_head_h

        # Data rows
        for ri, row in enumerate(sect["rows"]):
            if ri % 2 == 0:
                ax.add_patch(plt.Rectangle((0.15, y - row_h / 2 + 0.01),
                                            fig_w - 0.3, row_h,
                                            facecolor="#F8F9FA", edgecolor="none", zorder=1))
            ax.text(col["rank"], y, row["rank"], fontproperties=font_small,
                    ha="center", va="center", color="#555", zorder=3)
            ax.text(col["ticker"], y, row["ticker"], fontproperties=font_header,
                    ha="center", va="center", color="#2C3E50", zorder=3)
            ax.text(col["name"], y, row["name"], fontproperties=font,
                    ha="center", va="center", color="#333", zorder=3)
            ax.text(col["weight"], y, row["weight"], fontproperties=font,
                    ha="center", va="center", color="#333", zorder=3)
            for k in ("d1", "w1", "m1"):
                ds = _diff_str(row[k])
                ax.text(col[k], y, ds, fontproperties=font,
                        ha="center", va="center", color=_diff_color(row[k]), zorder=3)
            y -= row_h

        # Separator
        if si < n_sects - 1:
            y -= spacing

    path = os.path.join(IMG_DIR, f"etf_p2_holdings_{date}.png")
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white", pad_inches=0.1)
    plt.close(fig)
    return path


# ─── Page 3: 뉴스 분석 ──────────────────────────────────────────────
def render_page_news(group_label, date, movers_with_news):
    """movers_with_news: [{name,ticker,diff,weight,etf_short,news_items,analysis}]"""
    if not HAS_MPL or not movers_with_news:
        return None
    fonts = _get_fonts()
    font, font_title, font_section, font_header, font_small, font_news = fonts

    n = len(movers_with_news)
    line_h = 0.30
    block_h = line_h * 4 + 0.12  # title + 2 headlines + analysis + gap
    fig_h = 0.7 + n * block_h + 0.2
    fig_w = 13.0

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # Title
    y = fig_h - 0.4
    ax.text(fig_w / 2, y, f"TIMEFOLIO {group_label} ETF  주요 종목 뉴스 분석",
            fontproperties=font_title, ha="center", va="center", color="#1A1A2E")
    ax.text(fig_w - 0.3, y, date, fontproperties=font_small,
            ha="right", va="center", color="#888888")

    y -= 0.55

    for i, m in enumerate(movers_with_news):
        diff_s = _diff_str(m["diff"])
        arrow = "+" if m["diff"] > 0 else ""
        dc = "#D32F2F" if m["diff"] > 0 else "#1565C0"

        # Stock header line
        tk = m.get("ticker", "")
        tk_s = f"{tk}  " if tk else ""
        header = f"{i+1}. {tk_s}{m['name']}  ({m['etf_short']})"
        ax.text(0.3, y, header, fontproperties=font_header,
                ha="left", va="center", color="#1A1A2E", zorder=3)
        tag = f"{diff_s}%p  ->  {m['weight']:.1f}%"
        ax.text(fig_w - 0.3, y, tag, fontproperties=font,
                ha="right", va="center", color=dc, zorder=3)

        # Light background
        ax.add_patch(plt.Rectangle((0.15, y - block_h + line_h + 0.06),
                                    fig_w - 0.3, block_h - 0.06,
                                    facecolor="#FAFAFA" if i % 2 == 0 else "white",
                                    edgecolor="#EEEEEE", linewidth=0.5, zorder=0))
        y -= line_h

        # Headlines
        news_items = m.get("news_items", [])
        for ni in news_items[:2]:
            src = ni.get("source", "")
            ib = ni.get("ib")
            label = ib or src
            prefix = f"[{label}]  " if label else ""
            title = ni.get("title", "")
            if len(title) > 65:
                title = title[:63] + ".."
            ax.text(0.6, y, f"{prefix}{title}", fontproperties=font_news,
                    ha="left", va="center", color="#444444", zorder=3)
            y -= line_h

        if not news_items:
            ax.text(0.6, y, "(최근 뉴스 없음)", fontproperties=font_news,
                    ha="left", va="center", color="#999999", zorder=3)
            y -= line_h

        # Analysis
        analysis = m.get("analysis", "")
        ax.text(0.6, y, f"-> {analysis}", fontproperties=font_small,
                ha="left", va="center", color=dc, zorder=3)
        y -= line_h + 0.12

    path = os.path.join(IMG_DIR, f"etf_p3_news_{date}.png")
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
    return text.strip()


def _extract_ib(headline):
    for ib in _IB_NAMES:
        if ib in headline:
            return ib
    return None


def fetch_stock_news(name, limit=2):
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
        for item_xml in items[:limit + 4]:
            title_m = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', item_xml)
            source_m = re.search(r'<source[^>]*>(.*?)</source>', item_xml)
            if not title_m:
                continue
            raw_title = _strip_html(title_m.group(1))
            source = _strip_html(source_m.group(1)) if source_m else ""
            title = re.sub(r'\s*-\s*[^-]{2,30}$', '', raw_title)
            if not title or len(title) <= 5:
                continue
            ib = _extract_ib(raw_title)
            results.append({"title": title, "source": source, "ib": ib})
            if len(results) >= limit:
                break
        return results
    except Exception:
        return []


# ─── Keyword-based analysis ──────────────────────────────────────────
KEYWORD_RULES = [
    (["사노피", "우선순위", "보류", "중단"],
     "파트너십 재평가 — 파이프라인 가치 유지 관점 비중 조정",
     "파트너사 우선순위 변경 → 리스크 확대로 비중 축소"),
    (["비만", "GLP", "오젠픽", "위고비", "경구", "알약"],
     "GLP-1/비만 치료제 시장 확대 모멘텀 → 비중 확대",
     "비만 치료제 경쟁 심화 우려 → 비중 축소"),
    (["임상", "FDA", "승인", "신약", "파이프라인", "IND", "심사", "바이오", "항체", "ADC"],
     "임상 진전/파이프라인 기대 → 비중 확대",
     "임상 지연/불확실성 → 비중 축소"),
    (["합병", "인수", "M&A", "분사", "스핀오프"],
     "M&A/기업구조 변화 → 가치 재평가 비중 확대",
     "M&A 불확실성 → 비중 축소"),
    (["출시", "흥행", "신작", "콘텐츠", "게임", "엔터"],
     "신작 출시/콘텐츠 흥행 기대 → 비중 확대",
     "콘텐츠 부진/기대 하회 → 비중 축소"),
    (["실적", "매출", "영업이익", "순이익", "호실적", "어닝", "흑자"],
     "실적 호조/서프라이즈 → 비중 확대",
     "실적 부진/기대 하회 → 비중 축소"),
    (["목표가", "투자의견", "리포트", "커버리지", "매수의견", "상향"],
     "애널리스트 목표가 상향 → 비중 확대",
     "애널리스트 목표가 하향 → 비중 축소"),
    (["메모리", "낸드", "NAND", "HBM", "D램", "DRAM", "반도체", "SSD"],
     "메모리/반도체 업황 개선 → 비중 확대",
     "반도체 업황 둔화 우려 → 비중 축소"),
    (["딥시크", "DeepSeek", "경쟁", "대안"],
     "AI 경쟁 구도 변화 속 수혜 → 비중 확대",
     "AI 경쟁 심화/밸류에이션 재조정 → 비중 축소"),
    (["AI", "인공지능", "GPU", "데이터센터"],
     "AI/데이터센터 수요 확대 수혜 → 비중 확대",
     "AI 경쟁 심화/밸류에이션 부담 → 비중 축소"),
    (["트럼프", "정책", "관세", "규제", "원자력", "에너지", "우라늄"],
     "정책 수혜 기대 → 비중 확대",
     "정책/규제 리스크 → 비중 축소"),
    (["수주", "계약", "공급", "파트너", "구매"],
     "대형 계약/수주 확보 → 비중 확대",
     "수주 감소/계약 불발 → 비중 축소"),
    (["수출", "환율", "진출", "해외", "글로벌"],
     "해외 시장 확대/수출 호조 → 비중 확대",
     "수출 둔화/환율 악재 → 비중 축소"),
]


def analyze_headlines(news_items, diff):
    headlines = [n["title"] for n in news_items] if news_items else []
    if not headlines:
        return "비중 확대 — 상세 사유 확인 필요" if diff > 0 else "비중 축소 — 상세 사유 확인 필요"
    combined = " ".join(headlines)
    for keywords, pos_a, neg_a in KEYWORD_RULES:
        if any(kw in combined for kw in keywords):
            return pos_a if diff > 0 else neg_a
    short = headlines[0][:40]
    return f"{short} → 비중 확대" if diff > 0 else f"{short} → 비중 축소"


# ─── Text formatting (fallback) ──────────────────────────────────────
def _ticker_label(item):
    tk = item.get("ticker", "")
    return f"{tk}  " if tk else ""


def build_text_report(group_label, date, all_ups, all_downs, all_new,
                      etf_sections, movers_with_news, errors):
    lines = [
        f"TIMEFOLIO {group_label} ETF 리포트",
        f"{date}",
        "=" * 32, "",
        "[ 비중 증가 TOP 5 ]",
    ]
    for i, u in enumerate(all_ups[:5], 1):
        tk = _ticker_label(u)
        lines.append(f"  {i}. {tk}{u['name']} ({u.get('etf_short','')})  "
                      f"{u['weight']:.1f}%  {_diff_str(u['diff'])}")
    lines += ["", "[ 비중 감소 BOTTOM 3 ]"]
    for i, d in enumerate(all_downs[:3], 1):
        tk = _ticker_label(d)
        lines.append(f"  {i}. {tk}{d['name']} ({d.get('etf_short','')})  "
                      f"{d['weight']:.1f}%  {_diff_str(d['diff'])}")
    if all_new:
        lines += ["", "[ 신규 편입 ]"]
        for n in all_new[:3]:
            tk = _ticker_label(n)
            lines.append(f"  {tk}{n['name']} ({n.get('etf_short','')})  {n['weight']:.1f}%")

    lines += ["", "-" * 32, ""]
    for sect in etf_sections:
        lines.append(f"[ {sect['name']} | {sect['count']}종목 ]")
        for r in sect["rows"]:
            lines.append(f"  {r['rank']:>2}. {r['ticker']:<12} {r['name']:<20} "
                          f"{r['weight']:>6}  1D:{_diff_str(r['d1']):>7}  "
                          f"1W:{_diff_str(r['w1']):>7}  1M:{_diff_str(r['m1']):>7}")
        lines.append("")

    if movers_with_news:
        lines += ["-" * 32, "[ 주요 종목 뉴스 분석 ]", ""]
        for i, m in enumerate(movers_with_news, 1):
            tk = _ticker_label(m)
            ds = _diff_str(m["diff"])
            lines.append(f"{i}. {tk}{m['name']} ({m['etf_short']})  {ds}%p -> {m['weight']:.1f}%")
            for n in m.get("news_items", [])[:2]:
                src = n.get("ib") or n.get("source", "")
                prefix = f"[{src}] " if src else ""
                lines.append(f"   {prefix}{n['title']}")
            lines.append(f"   -> {m.get('analysis', '')}")
            lines.append("")

    if errors:
        lines.append(f"Errors: {', '.join(errors)}")
    return "\n".join(lines)


# ─── Main ─────────────────────────────────────────────────────────────
def run(etf_keys=None, generate_images=True):
    """Returns (text_report, [image_paths])."""
    if etf_keys is None:
        etf_keys = list(ETFS.keys())

    date = None
    errors = []

    # Collect per-ETF data
    all_ups = []
    all_downs = []
    all_new = []
    etf_sections = []  # for page 2
    all_movers = []    # for page 3

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

            # Period data
            m1 = fetch_period_comparison(cfg["idx"], "pdfM1")
            daily = load_daily(key, page_date)
            weekly = load_weekly(key, page_date)

            # Diff maps
            d1_map = _build_diff_map(holdings, daily)
            w1_map = _build_diff_map(holdings, weekly)
            m1_map = {}
            if m1 and "today" in m1:
                for item in m1["today"]:
                    inc = item.get("increaseWei", "0")
                    if inc in ("신규", "\uc2e0\uaddc"):
                        m1_map[item["prodNm"]] = "NEW"
                    else:
                        try:
                            m1_map[item["prodNm"]] = float(inc)
                        except ValueError:
                            pass

            # Parse AJAX changes for page 1
            m1_ups, m1_downs, m1_news = parse_ajax_changes(m1, ticker_map)
            for item in m1_ups:
                item["etf_short"] = cfg["short"]
            for item in m1_downs:
                item["etf_short"] = cfg["short"]
            for item in m1_news:
                item["etf_short"] = cfg["short"]
            all_ups.extend(m1_ups)
            all_downs.extend(m1_downs)
            all_new.extend(m1_news)

            # Page 2: holdings rows
            rows = []
            for i, h in enumerate(holdings[:10], 1):
                name = h["name"][:22] + ".." if len(h["name"]) > 22 else h["name"]
                m1v = m1_map.get(h["name"])
                if isinstance(m1v, str) and m1v == "NEW":
                    m1v = "NEW"
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

            # Page 3: collect movers
            for item in m1_ups[:5]:
                all_movers.append({**item, "etf_short": cfg["short"]})
            for item in m1_downs[:3]:
                all_movers.append({**item, "etf_short": cfg["short"]})

        except Exception as e:
            errors.append(f"{key}: {e}")

    # Determine group
    keys_set = set(etf_keys)
    if keys_set <= set(OVERSEAS_KEYS):
        group_label = "해외"
    elif keys_set <= set(DOMESTIC_KEYS):
        group_label = "국내"
    else:
        group_label = "전체"

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # Sort movers
    all_ups.sort(key=lambda x: x["diff"], reverse=True)
    all_downs.sort(key=lambda x: x["diff"])

    # Dedupe movers for page 3
    seen = {}
    for m in all_movers:
        key = m["name"]
        if key not in seen or abs(m["diff"]) > abs(seen[key]["diff"]):
            seen[key] = m
    top_movers = sorted(seen.values(), key=lambda x: abs(x["diff"]), reverse=True)[:8]

    # Fetch news for movers (page 3)
    movers_with_news = []
    for m in top_movers:
        news_items = fetch_stock_news(m["name"], limit=2)
        analysis = analyze_headlines(news_items, m["diff"])
        movers_with_news.append({
            **m,
            "news_items": news_items,
            "analysis": analysis,
        })

    # Generate images
    image_paths = []
    if generate_images and HAS_MPL:
        p1 = render_page_changes(group_label, date, all_ups, all_downs, all_new)
        if p1:
            image_paths.append(p1)
        p2 = render_page_holdings(group_label, date, etf_sections)
        if p2:
            image_paths.append(p2)
        p3 = render_page_news(group_label, date, movers_with_news)
        if p3:
            image_paths.append(p3)

    # Text report (fallback)
    report = build_text_report(group_label, date, all_ups, all_downs, all_new,
                                etf_sections, movers_with_news, errors)
    return report, image_paths


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["overseas"] or args == ["\ud574\uc678"]:
        keys = OVERSEAS_KEYS
    elif args == ["domestic"] or args == ["\uad6d\ub0b4"]:
        keys = DOMESTIC_KEYS
    else:
        keys = args if args else None

    report, images = run(keys)
    print(report)
    if images:
        print(f"\nImages: {', '.join(images)}")
