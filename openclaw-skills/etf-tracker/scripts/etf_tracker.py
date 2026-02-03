#!/usr/bin/env python3
"""
TIMEFOLIO ETF Holdings Tracker v4
- 해외/국내 3종씩 분리
- 티커+거래소 표시 (Bloomberg code → SNDK US)
- 이미지 기반 테이블 (matplotlib) + 텍스트 리포트
- 1주일 / 1개월 증감 TOP 5
- 뉴스 헤드라인 + 매체 출처 + IB명 추출
- 3개월 비교는 엑셀 전용 (리포트에서 제외)
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


def _parse_ticker(code_raw):
    """Convert Bloomberg code to display ticker. 'SNDK US EQUITY' → 'SNDK US'"""
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


def load_data(etf_key, date_str):
    fp = os.path.join(DATA_DIR, f"{etf_key}_{date_str}.json")
    if os.path.exists(fp):
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_nearest(etf_key, target_date, direction="before", max_days=10):
    ensure_dir()
    files = sorted([
        f for f in os.listdir(DATA_DIR)
        if f.startswith(f"{etf_key}_") and f.endswith(".json")
    ])
    if not files:
        return None

    candidates = []
    for fn in files:
        parts = fn.replace(".json", "").split("_", 1)
        if len(parts) < 2:
            continue
        file_date = parts[1]
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


def load_weekly(etf_key, current_date):
    return load_nearest(etf_key, current_date, direction="before", max_days=10)


# ─── Comparison helpers ──────────────────────────────────────────────
def parse_ajax_changes(ajax_data, ticker_map=None):
    """Parse AJAX response into ups/downs/news lists.
    ticker_map: {name: ticker} to attach tickers to items.
    """
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


def build_stored_diff(today_list, prev_list, ticker_map=None):
    if not prev_list:
        return [], [], []
    if ticker_map is None:
        ticker_map = {}
    prev_map = {h["name"]: h["weight"] for h in prev_list}
    today_map = {h["name"]: h["weight"] for h in today_list}

    ups, downs, news = [], [], []
    for name, w in today_map.items():
        pw = prev_map.get(name, 0)
        diff = round(w - pw, 2)
        tk = ticker_map.get(name, "")
        if name not in prev_map and w >= 0.5:
            news.append({"name": name, "weight": w, "ticker": tk})
        elif diff >= 0.1:
            ups.append({"name": name, "weight": w, "diff": diff, "ticker": tk})
        elif diff <= -0.1:
            downs.append({"name": name, "weight": w, "diff": diff, "ticker": tk})

    ups.sort(key=lambda x: x["diff"], reverse=True)
    downs.sort(key=lambda x: x["diff"])
    return ups, downs, news


# ─── Image rendering ─────────────────────────────────────────────────
def _get_fonts():
    fp = FONT_PATH if os.path.exists(FONT_PATH) else None
    fb = FONT_BOLD_PATH if os.path.exists(FONT_BOLD_PATH) else None
    font = FontProperties(fname=fp, size=10) if fp else FontProperties(size=10)
    font_title = FontProperties(fname=fb or fp, size=13, weight="bold") if (fb or fp) else FontProperties(size=13, weight="bold")
    font_header = FontProperties(fname=fb or fp, size=10, weight="bold") if (fb or fp) else FontProperties(size=10, weight="bold")
    font_small = FontProperties(fname=fp, size=9) if fp else FontProperties(size=9)
    return font, font_title, font_header, font_small


def _diff_str(val):
    if val is None or val == "":
        return "-"
    if isinstance(val, str):
        return val
    return f"+{val:.2f}" if val > 0 else f"{val:.2f}"


def _diff_color(val):
    if val is None or val == "" or val == "-":
        return "#666666"
    if isinstance(val, str):
        if val == "NEW":
            return "#4CAF50"  # Green for new entries
        if val.startswith("+"):
            return "#D32F2F"  # Red for increase (Korean convention)
        elif val.startswith("-"):
            return "#1565C0"  # Blue for decrease
        return "#333333"
    if val > 0:
        return "#D32F2F"
    elif val < 0:
        return "#1565C0"
    return "#333333"


def _strip_emoji(text):
    """Remove emoji characters for font-safe rendering."""
    return re.sub(
        r'[\U0001f1e0-\U0001f1ff\U0001f300-\U0001f9ff\U00002600-\U000027bf'
        r'\U0000fe00-\U0000fe0f\U0000200d]+', '', text
    ).strip()


def render_etf_table(etf_name, flag, date, holdings, m1_map, weekly_map, top_n=15):
    """Render holdings table as PNG image. Returns file path."""
    if not HAS_MPL or not holdings:
        return None

    font, font_title, font_header, font_small = _get_fonts()

    # Build rows: #, Ticker, Name, Weight, 1W, 1M
    rows = []
    for i, h in enumerate(holdings[:top_n], 1):
        ticker = h.get("ticker", "")
        name = h["name"]
        if len(name) > 22:
            name = name[:20] + ".."
        weight = h["weight"]
        w1 = weekly_map.get(h["name"])
        m1 = m1_map.get(h["name"])
        # "신규" marker
        if m1 is None and h["name"] in m1_map and m1_map[h["name"]] == "NEW":
            m1 = "NEW"
        rows.append({
            "rank": str(i),
            "ticker": ticker,
            "name": name,
            "weight": f"{weight:.1f}%",
            "w1": w1,
            "m1": m1,
        })

    n_rows = len(rows)
    row_h = 0.38
    header_h = 0.55
    title_h = 0.65
    fig_h = title_h + header_h + n_rows * row_h + 0.3
    fig_w = 11.0

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, fig_w)
    ax.set_ylim(0, fig_h)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # Column positions (x coords)
    cols = {
        "rank":   0.3,
        "ticker": 1.4,
        "name":   3.8,
        "weight": 6.8,
        "w1":     8.2,
        "m1":     9.8,
    }

    # Title (strip emoji for font compatibility)
    y_title = fig_h - 0.4
    clean_title = _strip_emoji(f"{flag}  {etf_name}") or etf_name
    ax.text(fig_w / 2, y_title, clean_title,
            fontproperties=font_title, ha="center", va="center", color="#1A1A2E")
    ax.text(fig_w - 0.3, y_title, date,
            fontproperties=font_small, ha="right", va="center", color="#888888")

    # Header bar
    y_header = y_title - header_h
    ax.add_patch(plt.Rectangle((0.1, y_header - 0.15), fig_w - 0.2, 0.38,
                                facecolor="#2C3E50", edgecolor="none", zorder=2))
    for key, label in [("rank", "#"), ("ticker", "Ticker"), ("name", "종목명"),
                        ("weight", "비중"), ("w1", "1W"), ("m1", "1M")]:
        ax.text(cols[key], y_header + 0.04, label,
                fontproperties=font_header, ha="center", va="center", color="white", zorder=3)

    # Data rows
    for idx, row in enumerate(rows):
        y = y_header - 0.15 - (idx + 1) * row_h + 0.05

        # Alternating background
        if idx % 2 == 0:
            ax.add_patch(plt.Rectangle((0.1, y - 0.12), fig_w - 0.2, row_h,
                                        facecolor="#F8F9FA", edgecolor="none", zorder=1))

        # Rank
        ax.text(cols["rank"], y + 0.05, row["rank"],
                fontproperties=font_small, ha="center", va="center", color="#555555", zorder=3)
        # Ticker
        ax.text(cols["ticker"], y + 0.05, row["ticker"],
                fontproperties=font_header, ha="center", va="center", color="#2C3E50", zorder=3)
        # Name
        ax.text(cols["name"], y + 0.05, row["name"],
                fontproperties=font, ha="center", va="center", color="#333333", zorder=3)
        # Weight
        ax.text(cols["weight"], y + 0.05, row["weight"],
                fontproperties=font, ha="center", va="center", color="#333333", zorder=3)
        # 1W
        w1_str = _diff_str(row["w1"])
        ax.text(cols["w1"], y + 0.05, w1_str,
                fontproperties=font, ha="center", va="center",
                color=_diff_color(row["w1"]), zorder=3)
        # 1M
        m1_str = _diff_str(row["m1"])
        ax.text(cols["m1"], y + 0.05, m1_str,
                fontproperties=font, ha="center", va="center",
                color=_diff_color(row["m1"]), zorder=3)

    # Bottom line
    y_bottom = y_header - 0.15 - (n_rows) * row_h - 0.05
    ax.plot([0.1, fig_w - 0.1], [y_bottom, y_bottom], color="#DEE2E6", linewidth=1, zorder=2)
    ax.text(fig_w / 2, y_bottom - 0.15, f"총 {len(holdings)}종목 보유",
            fontproperties=font_small, ha="center", va="center", color="#999999")

    path = os.path.join(IMG_DIR, f"etf_{etf_name}_{date}.png")
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

# Known IB / research firm names to extract from headlines
_IB_NAMES = [
    "모간스탠리", "Morgan Stanley", "골드만삭스", "Goldman Sachs",
    "JP모간", "JPMorgan", "UBS", "시티", "Citi", "바클레이즈", "Barclays",
    "도이치뱅크", "Deutsche Bank", "크레디트스위스", "Credit Suisse",
    "뱅크오브아메리카", "BofA", "메릴린치", "Merrill Lynch",
    "노무라", "Nomura", "다이와", "Daiwa", "CLSA", "맥쿼리", "Macquarie",
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
    """Extract IB/research firm name from headline if mentioned."""
    for ib in _IB_NAMES:
        if ib in headline:
            return ib
    return None


def fetch_stock_news(name, limit=2):
    """Fetch recent news headlines + source from Google News RSS.
    Returns list of {"title": str, "source": str, "ib": str|None}
    """
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

            # Clean trailing " - source" from title
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


# ─── Keyword-based analysis from headlines ───────────────────────────
KEYWORD_RULES = [
    (["사노피", "우선순위", "보류", "중단"],
     "파트너십 재평가 — 핵심 파이프라인 가치 유지 관점에서 비중 조정",
     "파트너사 우선순위 변경에 따른 리스크 확대로 비중 축소"),
    (["비만", "GLP", "오젠픽", "위고비", "경구", "알약"],
     "GLP-1/비만 치료제 시장 확대 모멘텀으로 비중 확대",
     "비만 치료제 경쟁 심화 우려로 비중 축소"),
    (["임상", "FDA", "승인", "신약", "파이프라인", "IND", "심사", "바이오", "항체", "ADC"],
     "임상 진전/파이프라인 기대로 비중 확대",
     "임상 지연/불확실성으로 비중 축소"),
    (["합병", "인수", "M&A", "분사", "스핀오프", "재상장"],
     "M&A/기업구조 변화에 따른 가치 재평가로 비중 확대",
     "M&A 불확실성으로 비중 축소"),
    (["출시", "흥행", "신작", "콘텐츠", "게임", "엔터"],
     "신작 출시/콘텐츠 흥행 기대로 비중 확대",
     "콘텐츠 부진/기대 하회로 비중 축소"),
    (["실적", "매출", "영업이익", "순이익", "호실적", "어닝", "흑자"],
     "실적 호조/서프라이즈 기반 비중 확대",
     "실적 부진/기대 하회로 비중 축소"),
    (["목표가", "투자의견", "리포트", "커버리지", "매수의견", "상향"],
     "애널리스트 목표가 상향에 따른 비중 확대",
     "애널리스트 목표가 하향에 따른 비중 축소"),
    (["메모리", "낸드", "NAND", "HBM", "D램", "DRAM", "반도체", "SSD"],
     "메모리/반도체 업황 개선 기대로 비중 확대",
     "반도체 업황 둔화 우려로 비중 축소"),
    (["딥시크", "DeepSeek", "경쟁", "대안"],
     "AI 경쟁 구도 변화 속 수혜 기대로 비중 확대",
     "AI 경쟁 심화/밸류에이션 재조정으로 비중 축소"),
    (["AI", "인공지능", "GPU", "데이터센터"],
     "AI/데이터센터 수요 확대 수혜 기대로 비중 확대",
     "AI 경쟁 심화/밸류에이션 부담으로 비중 축소"),
    (["트럼프", "정책", "관세", "규제", "원자력", "에너지", "우라늄"],
     "정책 수혜 기대로 비중 확대",
     "정책/규제 리스크로 비중 축소"),
    (["수주", "계약", "공급", "파트너", "구매"],
     "대형 계약/수주 확보에 따른 비중 확대",
     "수주 감소/계약 불발 우려로 비중 축소"),
    (["수출", "환율", "진출", "해외", "글로벌"],
     "해외 시장 확대/수출 호조로 비중 확대",
     "수출 둔화/환율 악재로 비중 축소"),
]


def analyze_headlines(news_items, diff):
    """Generate analysis from actual headlines using keyword matching + diff direction."""
    headlines = [n["title"] for n in news_items] if news_items else []
    if not headlines:
        return "비중 확대 — 상세 사유 확인 필요" if diff > 0 else "비중 축소 — 상세 사유 확인 필요"

    combined = " ".join(headlines)
    for keywords, pos_analysis, neg_analysis in KEYWORD_RULES:
        if any(kw in combined for kw in keywords):
            return pos_analysis if diff > 0 else neg_analysis

    short = headlines[0][:45]
    return f"{short} → 비중 확대" if diff > 0 else f"{short} → 비중 축소"


# ─── Formatting (text) ───────────────────────────────────────────────
def _ticker_label(item):
    """Format ticker for display: 'SNDK US  ' or ''"""
    tk = item.get("ticker", "")
    return f"{tk}  " if tk else ""


def fmt_top5_section(title, ups, downs, news_items, limit=5):
    lines = [title]

    if ups:
        lines.append("  \U0001f4c8 비중 증가")
        for i, item in enumerate(ups[:limit], 1):
            tk = _ticker_label(item)
            lines.append(f"    {i}. {tk}{item['name']}")
            lines.append(f"       {item['weight']:.2f}% (+{item['diff']:.2f}%p)")
    if downs:
        lines.append("  \U0001f4c9 비중 감소")
        for i, item in enumerate(downs[:limit], 1):
            tk = _ticker_label(item)
            lines.append(f"    {i}. {tk}{item['name']}")
            lines.append(f"       {item['weight']:.2f}% ({item['diff']:.2f}%p)")
    if news_items:
        names = ", ".join(f"{_ticker_label(n)}{n['name']}({n['weight']:.1f}%)" for n in news_items[:3])
        lines.append(f"  \u2b50 신규: {names}")

    lines.append("")
    return "\n".join(lines)


def fmt_etf_block(etf_key, holdings, m1_data, weekly_data, date, ticker_map):
    cfg = ETFS[etf_key]
    lines = []

    lines.append(f"{cfg['flag']} {cfg['name']}")
    lines.append(f"  {len(holdings)}종목 | {date}")
    lines.append("")

    # 1주일 비교
    if weekly_data:
        w_ups, w_downs, w_news = build_stored_diff(
            holdings, weekly_data.get("holdings", []), ticker_map
        )
        week_label = f"\U0001f4ca 1주일 증감 TOP 5"
        if weekly_data.get("date"):
            week_label += f" (vs {weekly_data['date']})"
        lines.append(fmt_top5_section(week_label, w_ups, w_downs, w_news))
    else:
        lines.append("\U0001f4ca 1주일 증감: 데이터 축적 중\n")

    # 1개월 비교 (AJAX)
    m1_ups, m1_downs, m1_news = parse_ajax_changes(m1_data, ticker_map)
    lines.append(fmt_top5_section("\U0001f4ca 1개월 증감 TOP 5", m1_ups, m1_downs, m1_news))

    return "\n".join(lines)


def build_news_section(all_movers):
    if not all_movers:
        return ""

    seen = {}
    for m in all_movers:
        key = m["name"]
        if key not in seen or abs(m["diff"]) > abs(seen[key]["diff"]):
            seen[key] = m
    top_movers = sorted(seen.values(), key=lambda x: abs(x["diff"]), reverse=True)[:10]

    if not top_movers:
        return ""

    lines = [
        "\u2500" * 28,
        "\U0001f50d 주요 종목 뉴스 분석",
        "",
    ]

    for i, m in enumerate(top_movers, 1):
        diff_str = f"+{m['diff']:.2f}" if m["diff"] > 0 else f"{m['diff']:.2f}"
        direction = "\u2191" if m["diff"] > 0 else "\u2193"
        etf = m.get("etf_name", "")
        tk = _ticker_label(m)

        lines.append(f"{i}. {tk}{m['name']} ({etf})")
        lines.append(f"   {direction} {diff_str}%p \u2192 현재 {m['weight']:.2f}%")

        # Fetch real news with source
        news_items = fetch_stock_news(m["name"], limit=2)
        if news_items:
            for n in news_items:
                src = n.get("source", "")
                ib = n.get("ib")
                # Show IB name prominently if found, otherwise show source
                if ib:
                    lines.append(f"   \U0001f4f0 [{ib}] {n['title']}")
                elif src:
                    lines.append(f"   \U0001f4f0 [{src}] {n['title']}")
                else:
                    lines.append(f"   \U0001f4f0 {n['title']}")
        else:
            lines.append(f"   \U0001f4f0 (최근 뉴스 없음)")

        analysis = analyze_headlines(news_items, m["diff"])
        lines.append(f"   \U0001f4ad {analysis}")
        lines.append("")

    return "\n".join(lines)


# ─── Main ─────────────────────────────────────────────────────────────
def run(etf_keys=None, generate_images=True):
    """Run ETF tracker. Returns (text_report, [image_paths])."""
    if etf_keys is None:
        etf_keys = list(ETFS.keys())

    date = None
    blocks = []
    all_movers = []
    errors = []
    image_paths = []

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

            # 3. Build ticker map (name → ticker)
            ticker_map = {h["name"]: h.get("ticker", "") for h in holdings}

            # 4. Fetch 1-month AJAX comparison
            m1 = fetch_period_comparison(cfg["idx"], "pdfM1")

            # 5. Load weekly data
            weekly = load_weekly(key, page_date)

            # 6. Build change maps for image rendering
            m1_map = {}  # name → diff value or "NEW"
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

            weekly_map = {}
            if weekly:
                prev_wmap = {h["name"]: h["weight"] for h in weekly.get("holdings", [])}
                for h in holdings:
                    pw = prev_wmap.get(h["name"])
                    if pw is not None:
                        weekly_map[h["name"]] = round(h["weight"] - pw, 2)

            # 7. Generate image
            if generate_images and HAS_MPL:
                img_path = render_etf_table(
                    cfg["name"], cfg["flag"], page_date,
                    holdings, m1_map, weekly_map
                )
                if img_path:
                    image_paths.append(img_path)

            # 8. Format text block
            block = fmt_etf_block(key, holdings, m1, weekly, page_date, ticker_map)
            blocks.append(block)

            # 9. Collect movers for news section
            m1_ups, m1_downs, m1_news = parse_ajax_changes(m1, ticker_map)
            for item in m1_ups[:5]:
                all_movers.append({**item, "etf_name": cfg["name"]})
            for item in m1_downs[:5]:
                all_movers.append({**item, "etf_name": cfg["name"]})
            for item in m1_news:
                all_movers.append({
                    "name": item["name"], "weight": item["weight"],
                    "diff": item["weight"], "ticker": item.get("ticker", ""),
                    "etf_name": cfg["name"],
                })

        except Exception as e:
            errors.append(f"{key}: {e}")

    # Determine group label
    keys_set = set(etf_keys)
    if keys_set <= set(OVERSEAS_KEYS):
        group = "\U0001f30f 해외"
    elif keys_set <= set(DOMESTIC_KEYS):
        group = "\U0001f1f0\U0001f1f7 국내"
    else:
        group = "전체"

    header = (
        f"\U0001f4ca TIMEFOLIO {group} ETF 리포트\n"
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
        print(f"\n\U0001f5bc Images: {', '.join(images)}")
