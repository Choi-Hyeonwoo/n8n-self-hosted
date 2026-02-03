#!/usr/bin/env python3
"""
Claude Code → RON 메시지 서버
RON이 HTTP로 접근하여 메시지를 읽을 수 있음

Usage:
    python3 message_server.py

RON에서 접근:
    curl http://host.docker.internal:8768/messages
    curl http://172.17.0.1:8768/messages  (Docker bridge)
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from datetime import datetime

PORT = 8768
MESSAGE_FILE = "/root/.openclaw/workspace/CLAUDE_TO_RON.md"
STRATEGIES_FILE = "/home/user/n8n-self-hosted/openclaw/.brain/strategies.json"


class MessageHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def do_GET(self):
        if self.path == "/messages" or self.path == "/":
            # 메시지 파일 읽기
            try:
                with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
                    content = f.read()
                self._send_json({
                    "status": "ok",
                    "source": "claude-code",
                    "timestamp": datetime.now().isoformat(),
                    "message": content
                })
            except FileNotFoundError:
                self._send_json({"status": "no_messages", "message": ""})
            return

        if self.path == "/strategies":
            # brain_sync 전략 읽기
            try:
                with open(STRATEGIES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                pending = [s for s in data.get("strategies", []) if s.get("status") == "pending"]
                self._send_json({
                    "status": "ok",
                    "pending_count": len(pending),
                    "strategies": pending
                })
            except:
                self._send_json({"status": "error", "strategies": []})
            return

        if self.path == "/health":
            self._send_json({"status": "ok", "service": "claude-ron-bridge"})
            return

        self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        # RON이 메시지 보내기 (옵션)
        if self.path == "/ron-reply":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")

            # RON 응답 저장
            reply_file = "/root/.openclaw/workspace/RON_TO_CLAUDE.md"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            with open(reply_file, "a", encoding="utf-8") as f:
                f.write(f"\n## RON 응답 ({timestamp})\n{body}\n---\n")

            self._send_json({"status": "received"})
            return

        self._send_json({"error": "not found"}, 404)

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


def main():
    server = HTTPServer(("0.0.0.0", PORT), MessageHandler)
    print(f"═══════════════════════════════════════")
    print(f"  Claude-RON Message Bridge")
    print(f"  http://0.0.0.0:{PORT}")
    print(f"═══════════════════════════════════════")
    print(f"Endpoints:")
    print(f"  GET  /messages   - Claude의 메시지 읽기")
    print(f"  GET  /strategies - 대기 중인 전략 확인")
    print(f"  POST /ron-reply  - RON 응답 보내기")
    print(f"")
    print(f"RON에서 접근:")
    print(f"  curl http://host.docker.internal:{PORT}/messages")
    print(f"  curl http://172.17.0.1:{PORT}/messages")
    print(f"")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
