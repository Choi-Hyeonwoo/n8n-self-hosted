#!/usr/bin/env python3
"""
TIMEFOLIO ETF Holdings Tracker v3
- 해외/국내 3종씩 분리
- 1주일 / 1개월 증감 TOP 5 (증가+감소)
- 각 TOP 5 종목별 실제 뉴스 헤드라인 + 이벤트 기반 추론
- 3개월 비교는 엑셀 전용 (리포트에서 제외)
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
    "NQ100":         {"idx": 2,  "name": "미국나스닥100액티브",     "flag": "🇺🇸", "cate": "001"},
    "CN_AI":         {"idx": 19, "name": "차이나AI테크액티브",     "flag": "🇨🇳", "cate": "001"},
    "GLOBAL_AI":     {"idx": 6,  "name": "글로벌AI인공지능액티브", "flag": "🤖", "cate": "001"},
    "KOSPI_ACTIVE":  {"idx": 11, "name": "코스피액티브",           "flag": "🇰🇷", "cate": "001"},
    "K_CULTURE":     {"idx": 1,  "name": "K컬처액티브",           "flag": "🎬", "cate": "001"},
    "K_BIO":         {"idx": 13, "name": "K바이오액티브",          "flag": "🧬", "cate": "001"},
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
    fp = os.path.join(DATA_DIR, f"{etf_key}_{date_str}.json")
    if os.path.exists(fp):
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_nearest(etf_key, target_date, direction="before", max_days=10):
    """Load data nearest to target_date.
    direction='before': look for dates before target_date
    """
    ensure_dir()
    files = sorted([
        f for f in os.listdir(DATA_DIR)
        if f.startswith(f"{etf_key}_") and f.endswith(".json")
    ])
    if not files:
        return None

    candidates = []
    for fn in files:
        # Extract date from filename: ETFKEY_YYYY-MM-DD.json
        parts = fn.replace(".json", "").split("_", 1)
        if len(parts) < 2:
            continue
        file_date = parts[1]
        if direction == "before" and file_date < target_date:
            candidates.append((file_date, fn))

    if not candidates:
        return None

    # Get closest to target
    candidates.sort(key=lambda x: x[0], reverse=True)
    best_date, best_fn = candidates[0]

    # Check if within max_days
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
    """Load data from ~7 days ago for weekly comparison."""
    try:
        target = datetime.strptime(current_date, "%Y-%m-%d") - timedelta(days=7)
        target_str = target.strftime("%Y-%m-%d")
    except ValueError:
        return None
    return load_nearest(etf_key, current_date, direction="before", max_days=10)


# ─── Comparison helpers ──────────────────────────────────────────────
def parse_ajax_changes(ajax_data):
    """Parse AJAX response into ups/downs/news lists."""
    if not ajax_data or "today" not in ajax_data:
        return [], [], []

    ups, downs, news = [], [], []
    for item in ajax_data["today"]:
        nm = item["prodNm"]
        w = float(item["wei"])
        inc = item.get("increaseWei", "0")
        if inc in ("신규", "\uc2e0\uaddc"):
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
    return ups, downs, news


def build_stored_diff(today_list, prev_list):
    """Compare two holdings lists from stored data."""
    if not prev_list:
        return [], [], []
    prev_map = {h["name"]: h["weight"] for h in prev_list}
    today_map = {h["name"]: h["weight"] for h in today_list}

    ups, downs, news = [], [], []
    for name, w in today_map.items():
        pw = prev_map.get(name, 0)
        diff = round(w - pw, 2)
        if name not in prev_map and w >= 0.5:
            news.append({"name": name, "weight": w})
        elif diff >= 0.1:
            ups.append({"name": name, "weight": w, "diff": diff})
        elif diff <= -0.1:
            downs.append({"name": name, "weight": w, "diff": diff})

    ups.sort(key=lambda x: x["diff"], reverse=True)
    downs.sort(key=lambda x: x["diff"])
    return ups, downs, news


# ─── Formatting ──────────────────────────────────────────────────────
def fmt_top5_section(title, ups, downs, news_items, limit=5):
    """Format a TOP 5 section with ups and downs."""
    lines = []
    lines.append(title)

    if ups:
        lines.append("  📈 비중 증가")
        for i, item in enumerate(ups[:limit], 1):
            lines.append(f"    {i}. {item['name']}")
            lines.append(f"       {item['weight']:.2f}% (+{item['diff']:.2f}%p)")
    else:
        lines.append("  📈 비중 증가: 없음")

    if downs:
        lines.append("  📉 비중 감소")
        for i, item in enumerate(downs[:limit], 1):
            lines.append(f"    {i}. {item['name']}")
            lines.append(f"       {item['weight']:.2f}% ({item['diff']:.2f}%p)")
    else:
        lines.append("  📉 비중 감소: 없음")

    if news_items:
        names = ", ".join(f"{n['name']}({n['weight']:.1f}%)" for n in news_items[:3])
        lines.append(f"  ⭐ 신규: {names}")

    lines.append("")
    return "\n".join(lines)


def fmt_etf_block(etf_key, holdings, m1_data, weekly_data, date):
    """Format a single ETF block."""
    cfg = ETFS[etf_key]
    lines = []

    lines.append(f"{cfg['flag']} {cfg['name']}")
    lines.append(f"  {len(holdings)}종목 | {date}")
    lines.append("")

    # 1주일 비교
    if weekly_data:
        w_ups, w_downs, w_news = build_stored_diff(
            holdings, weekly_data.get("holdings", [])
        )
        week_label = f"📊 1주일 증감 TOP 5"
        if weekly_data.get("date"):
            week_label += f" (vs {weekly_data['date']})"
        lines.append(fmt_top5_section(week_label, w_ups, w_downs, w_news))
    else:
        lines.append("📊 1주일 증감: 데이터 축적 중\n")

    # 1개월 비교 (AJAX)
    m1_ups, m1_downs, m1_news = parse_ajax_changes(m1_data)
    lines.append(fmt_top5_section("📊 1개월 증감 TOP 5", m1_ups, m1_downs, m1_news))

    return "\n".join(lines)


# ─── News fetching ───────────────────────────────────────────────────
# Korean aliases for well-known foreign stocks (better news search results)
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
    "GE Vernova": "GE버노바 에너지",
}


def _clean_stock_name(name):
    """Clean stock name for news search query, prefer Korean alias."""
    # Check for Korean alias first
    for eng, kr in _KR_ALIASES.items():
        if eng.lower() in name.lower():
            return kr
    # Fallback: strip legal suffixes
    clean = re.sub(r'\s*(Corp|Inc|Ltd|PLC|Co|NV|SA|AG|SE|GmbH|Holdings?)[./\s]*', ' ', name)
    clean = re.sub(r'/\w+$', '', clean)  # Remove /DE etc.
    return clean.strip()


def _strip_html(text):
    """Remove HTML entities and tags."""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&apos;", "'")
    return text.strip()


def fetch_stock_news(name, limit=2):
    """Fetch recent news headlines from Google News RSS."""
    clean = _clean_stock_name(name)
    # Add "주가" for stock-relevant results
    query = urllib.parse.quote(f"{clean} 주가")
    url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; OpenClaw/1.0)"
    })
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            xml = resp.read().decode("utf-8")
        titles = re.findall(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', xml)
        results = []
        for t in titles[2:2 + limit + 2]:  # skip feed/channel title, grab extras
            t = _strip_html(t)
            # Remove trailing " - 출처명" for cleaner display
            t = re.sub(r'\s*-\s*[^-]{2,30}$', '', t)
            if t and len(t) > 5:
                results.append(t)
            if len(results) >= limit:
                break
        return results
    except Exception:
        return []


# ─── Keyword-based analysis from headlines ───────────────────────────
# (keywords, positive_analysis, negative_analysis)
KEYWORD_RULES = [
    # More specific rules first (bio/pharma before AI since "AI주식분석" misleads)
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


def analyze_headlines(headlines, diff):
    """Generate analysis from actual headlines using keyword matching + diff direction."""
    if not headlines:
        if diff > 0:
            return "비중 확대 — 상세 사유 확인 필요"
        return "비중 축소 — 상세 사유 확인 필요"

    combined = " ".join(headlines)
    for keywords, pos_analysis, neg_analysis in KEYWORD_RULES:
        if any(kw in combined for kw in keywords):
            return pos_analysis if diff > 0 else neg_analysis

    # Fallback: extract key phrase from first headline
    short = headlines[0][:45]
    if diff > 0:
        return f"{short} → 비중 확대"
    return f"{short} → 비중 축소"


def build_news_section(all_movers):
    """Build news analysis section with real headlines for TOP movers."""
    if not all_movers:
        return ""

    # Deduplicate by name, keep largest absolute diff
    seen = {}
    for m in all_movers:
        key = m["name"]
        if key not in seen or abs(m["diff"]) > abs(seen[key]["diff"]):
            seen[key] = m
    top_movers = sorted(seen.values(), key=lambda x: abs(x["diff"]), reverse=True)[:10]

    if not top_movers:
        return ""

    lines = [
        "─" * 28,
        "🔍 주요 종목 뉴스 분석",
        "",
    ]

    for i, m in enumerate(top_movers, 1):
        diff_str = f"+{m['diff']:.2f}" if m["diff"] > 0 else f"{m['diff']:.2f}"
        direction = "↑" if m["diff"] > 0 else "↓"
        etf = m.get("etf_name", "")

        lines.append(f"{i}. {m['name']} ({etf})")
        lines.append(f"   {direction} {diff_str}%p → 현재 {m['weight']:.2f}%")

        # Fetch real news
        headlines = fetch_stock_news(m["name"], limit=2)
        if headlines:
            for h in headlines:
                lines.append(f"   📰 {h}")
        else:
            lines.append(f"   📰 (최근 뉴스 없음)")

        # Keyword-based analysis from real headlines
        analysis = analyze_headlines(headlines, m["diff"])
        lines.append(f"   💭 {analysis}")
        lines.append("")

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

            # 3. Fetch 1-month AJAX comparison
            m1 = fetch_period_comparison(cfg["idx"], "pdfM1")

            # 4. Load weekly data (from stored)
            weekly = load_weekly(key, page_date)

            # 5. Format block
            block = fmt_etf_block(key, holdings, m1, weekly, page_date)
            blocks.append(block)

            # 6. Collect movers for news section (from 1M data)
            m1_ups, m1_downs, m1_news = parse_ajax_changes(m1)
            for item in m1_ups[:5]:
                all_movers.append({**item, "etf_name": cfg["name"]})
            for item in m1_downs[:5]:
                all_movers.append({**item, "etf_name": cfg["name"]})
            for item in m1_news:
                all_movers.append({
                    "name": item["name"], "weight": item["weight"],
                    "diff": item["weight"], "etf_name": cfg["name"],
                })

        except Exception as e:
            errors.append(f"{key}: {e}")

    # Determine group label
    keys_set = set(etf_keys)
    if keys_set <= set(OVERSEAS_KEYS):
        group = "🌏 해외"
    elif keys_set <= set(DOMESTIC_KEYS):
        group = "🇰🇷 국내"
    else:
        group = "전체"

    header = (
        f"📊 TIMEFOLIO {group} ETF 리포트\n"
        f"📅 {date or 'unknown'}\n"
        f"{'=' * 28}"
    )

    separator = "\n" + "─" * 28 + "\n"
    body = separator.join(blocks)

    news = build_news_section(all_movers)

    report = f"{header}\n\n{body}"
    if news:
        report += f"\n{news}"
    if errors:
        report += "\n\n⚠ Errors: " + ", ".join(errors)

    return report


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["overseas"] or args == ["해외"]:
        args = OVERSEAS_KEYS
    elif args == ["domestic"] or args == ["국내"]:
        args = DOMESTIC_KEYS
    print(run(args if args else None))
