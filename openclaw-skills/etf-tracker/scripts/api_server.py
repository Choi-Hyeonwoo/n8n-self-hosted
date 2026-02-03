#!/usr/bin/env python3
"""
ETF Tracker HTTP API 서버
n8n 또는 다른 스케줄러에서 HTTP 호출로 실행

포트: 8765
엔드포인트:
  GET /health          - 상태 확인
  POST /run/domestic   - 국내 ETF 실행
  POST /run/overseas   - 해외 ETF 실행
  GET /status          - 최근 실행 상태

사용법:
  python3 api_server.py &
  curl -X POST http://localhost:8765/run/domestic
"""

import os
import sys
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# 스크립트 경로 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# 환경변수 확인 (ANTHROPIC_API_KEY는 ~/.bashrc 또는 systemd에서 설정)
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("[WARN] ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다")

import run_etf_tracker

# 실행 상태 저장
execution_status = {
    "last_domestic": None,
    "last_overseas": None,
    "running": False
}


class ETFTrackerHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_GET(self):
        if self.path == '/health':
            self._send_json(200, {"status": "ok", "service": "etf-tracker"})

        elif self.path == '/status':
            self._send_json(200, execution_status)

        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        global execution_status

        if execution_status["running"]:
            self._send_json(409, {"error": "Already running", "status": "busy"})
            return

        if self.path == '/run/domestic':
            market = "domestic"
        elif self.path == '/run/overseas':
            market = "overseas"
        else:
            self._send_json(404, {"error": "Not found"})
            return

        # 비동기 실행
        def run_task():
            global execution_status
            execution_status["running"] = True
            try:
                # 실행
                sys.argv = ["run_etf_tracker.py", market]
                result = run_etf_tracker.main()
                execution_status[f"last_{market}"] = {
                    "time": datetime.now().isoformat(),
                    "success": result == 0,
                    "exit_code": result
                }
            except Exception as e:
                execution_status[f"last_{market}"] = {
                    "time": datetime.now().isoformat(),
                    "success": False,
                    "error": str(e)
                }
            finally:
                execution_status["running"] = False

        thread = threading.Thread(target=run_task)
        thread.start()

        self._send_json(202, {
            "status": "accepted",
            "market": market,
            "message": f"{market} ETF 분석 시작됨"
        })

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


def main():
    port = int(os.environ.get("ETF_API_PORT", 8765))
    server = HTTPServer(('0.0.0.0', port), ETFTrackerHandler)
    print(f"═══════════════════════════════════════")
    print(f"  ETF Tracker API Server")
    print(f"  Port: {port}")
    print(f"═══════════════════════════════════════")
    print(f"\n엔드포인트:")
    print(f"  GET  /health         - 상태 확인")
    print(f"  POST /run/domestic   - 국내 ETF 실행")
    print(f"  POST /run/overseas   - 해외 ETF 실행")
    print(f"  GET  /status         - 최근 실행 상태")
    print(f"\nn8n에서 HTTP Request 노드로 호출하세요.")
    print(f"예: POST http://localhost:{port}/run/domestic\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버 종료")
        server.shutdown()


if __name__ == "__main__":
    main()
