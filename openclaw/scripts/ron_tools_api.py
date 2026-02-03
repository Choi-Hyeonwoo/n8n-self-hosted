#!/usr/bin/env python3
"""
RON Tools API - Simple REST endpoints for RON
MCP 없이 직접 호출 가능한 도구 API

Usage:
    python3 ron_tools_api.py
    # Then call: curl http://localhost:8766/stock/AAPL

Endpoints:
    GET  /stock/<symbol>       - 주식 시세 조회
    GET  /fetch?url=<url>      - 웹 페이지 내용 가져오기
    GET  /health               - 서버 상태 확인
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.request
import urllib.parse
import ssl
import re
from datetime import datetime

PORT = 8766
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def fetch_url(url: str, max_length: int = 50000) -> dict:
    """URL 내용 가져오기"""
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            content = resp.read().decode("utf-8", errors="ignore")

            # HTML 태그 제거 (간단한 텍스트 추출)
            text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()

            return {
                "success": True,
                "url": url,
                "content": text[:max_length],
                "truncated": len(text) > max_length
            }
    except Exception as e:
        return {"success": False, "error": str(e), "url": url}


def get_stock_quote(symbol: str) -> dict:
    """Yahoo Finance에서 주식 시세 조회"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        result = data.get("chart", {}).get("result", [{}])[0]
        meta = result.get("meta", {})

        if not meta:
            return {"success": False, "error": f"Symbol not found: {symbol}"}

        # 가격 변동 계산
        current = meta.get("regularMarketPrice", 0)
        prev_close = meta.get("chartPreviousClose", meta.get("previousClose", current))
        change = current - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0

        return {
            "success": True,
            "symbol": symbol.upper(),
            "name": meta.get("longName", meta.get("shortName", symbol)),
            "currency": meta.get("currency", "USD"),
            "price": current,
            "previousClose": prev_close,
            "change": round(change, 2),
            "changePercent": round(change_pct, 2),
            "dayHigh": meta.get("regularMarketDayHigh"),
            "dayLow": meta.get("regularMarketDayLow"),
            "fiftyTwoWeekHigh": meta.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": meta.get("fiftyTwoWeekLow"),
            "volume": meta.get("regularMarketVolume"),
            "exchange": meta.get("exchangeName"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e), "symbol": symbol}


class RonToolsHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Health check
        if path == "/health":
            self._send_json({"status": "ok", "timestamp": datetime.now().isoformat()})
            return

        # Stock quote: /stock/AAPL or /stock?symbol=AAPL
        if path.startswith("/stock"):
            if path == "/stock":
                symbol = query.get("symbol", [""])[0]
            else:
                symbol = path.split("/")[-1]

            if not symbol:
                self._send_json({"success": False, "error": "Symbol required"}, 400)
                return

            result = get_stock_quote(symbol)
            self._send_json(result, 200 if result["success"] else 500)
            return

        # Web fetch: /fetch?url=https://example.com
        if path == "/fetch":
            url = query.get("url", [""])[0]
            max_len = int(query.get("max_length", [50000])[0])

            if not url:
                self._send_json({"success": False, "error": "URL required"}, 400)
                return

            result = fetch_url(url, max_len)
            self._send_json(result, 200 if result["success"] else 500)
            return

        # API docs
        if path == "/" or path == "/help":
            self._send_json({
                "name": "RON Tools API",
                "version": "1.0",
                "endpoints": {
                    "GET /stock/<symbol>": "주식 시세 조회 (예: /stock/AAPL)",
                    "GET /fetch?url=<url>": "웹 페이지 내용 가져오기",
                    "GET /health": "서버 상태 확인"
                },
                "examples": [
                    "curl http://localhost:8766/stock/AAPL",
                    "curl http://localhost:8766/stock/005930.KS",
                    "curl 'http://localhost:8766/fetch?url=https://example.com'"
                ]
            })
            return

        self._send_json({"error": "Not found"}, 404)

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {args[0]}")


def main():
    server = HTTPServer(("0.0.0.0", PORT), RonToolsHandler)
    print(f"═══════════════════════════════════════")
    print(f"  RON Tools API Server")
    print(f"  Listening on http://0.0.0.0:{PORT}")
    print(f"═══════════════════════════════════════")
    print(f"Endpoints:")
    print(f"  GET /stock/<symbol>  - Stock quote")
    print(f"  GET /fetch?url=<url> - Web fetch")
    print(f"  GET /health          - Health check")
    print(f"")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
