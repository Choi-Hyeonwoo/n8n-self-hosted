#!/usr/bin/env python3
"""
Anthropic API 비용 제어 프록시
비싼 모델(Sonnet/Opus) 호출 시 경고 또는 차단

Usage:
    # 환경변수로 설정
    export ANTHROPIC_API_BASE=http://localhost:8767

    # 프록시 실행
    python3 api_cost_guard.py
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.request
import os
from datetime import datetime

PORT = 8767
ANTHROPIC_API = "https://api.anthropic.com"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# 비용 설정 ($/1M tokens)
MODEL_COSTS = {
    "claude-opus-4": {"input": 15, "output": 75},
    "claude-sonnet-4": {"input": 3, "output": 15},
    "claude-haiku-3": {"input": 0.25, "output": 1.25},
}

# 제한 설정
CONFIG = {
    "block_opus": True,           # Opus 완전 차단
    "warn_sonnet": True,          # Sonnet 사용 시 경고 로그
    "force_haiku": False,         # 모든 요청을 Haiku로 강제 변환
    "daily_limit_usd": 5.0,       # 일일 비용 한도
    "max_input_tokens": 100000,   # 단일 요청 최대 입력 토큰
}

# 일일 사용량 추적
daily_usage = {"date": None, "cost": 0.0, "requests": 0}
LOG_FILE = "/var/log/api_cost_guard.log"


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass


def estimate_cost(model, input_tokens, output_tokens):
    """비용 추정"""
    for model_prefix, costs in MODEL_COSTS.items():
        if model_prefix in model.lower():
            input_cost = (input_tokens / 1_000_000) * costs["input"]
            output_cost = (output_tokens / 1_000_000) * costs["output"]
            return input_cost + output_cost
    return 0


def check_daily_limit():
    """일일 한도 체크"""
    global daily_usage
    today = datetime.now().strftime("%Y-%m-%d")

    if daily_usage["date"] != today:
        daily_usage = {"date": today, "cost": 0.0, "requests": 0}

    return daily_usage["cost"] < CONFIG["daily_limit_usd"]


def update_usage(cost):
    """사용량 업데이트"""
    global daily_usage
    daily_usage["cost"] += cost
    daily_usage["requests"] += 1


class CostGuardHandler(BaseHTTPRequestHandler):
    def _proxy_request(self, method, body=None):
        """Anthropic API로 프록시"""
        url = f"{ANTHROPIC_API}{self.path}"

        headers = {}
        for key, value in self.headers.items():
            if key.lower() not in ["host", "content-length"]:
                headers[key] = value

        # API 키 설정
        if "x-api-key" not in [k.lower() for k in headers.keys()]:
            headers["x-api-key"] = ANTHROPIC_API_KEY

        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                response_body = resp.read()
                self.send_response(resp.status)
                for key, value in resp.headers.items():
                    if key.lower() not in ["transfer-encoding", "connection"]:
                        self.send_header(key, value)
                self.end_headers()
                self.wfile.write(response_body)
                return response_body
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(e.read())
            return None

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        # /v1/messages 엔드포인트 체크
        if "/v1/messages" in self.path and body:
            try:
                data = json.loads(body.decode("utf-8"))
                model = data.get("model", "")
                max_tokens = data.get("max_tokens", 1000)

                # 입력 토큰 추정 (메시지 길이 기반)
                input_text = json.dumps(data.get("messages", []))
                estimated_input = len(input_text) // 4  # 대략적 토큰 추정

                # 1. Opus 차단
                if CONFIG["block_opus"] and "opus" in model.lower():
                    log(f"🚫 BLOCKED: Opus model request blocked - {model}")
                    self.send_response(403)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "error": {
                            "type": "blocked_by_cost_guard",
                            "message": "Opus model is blocked for cost control. Use Sonnet or Haiku."
                        }
                    }).encode())
                    return

                # 2. Sonnet 경고
                if CONFIG["warn_sonnet"] and "sonnet" in model.lower():
                    est_cost = estimate_cost(model, estimated_input, max_tokens)
                    log(f"⚠️ WARN: Sonnet request - est. ${est_cost:.4f} ({estimated_input} in / {max_tokens} out)")

                # 3. Haiku 강제
                if CONFIG["force_haiku"]:
                    data["model"] = "claude-3-haiku-20240307"
                    body = json.dumps(data).encode("utf-8")
                    log(f"🔄 FORCED: Model changed to Haiku")

                # 4. 일일 한도 체크
                if not check_daily_limit():
                    log(f"🚫 BLOCKED: Daily limit ${CONFIG['daily_limit_usd']} exceeded")
                    self.send_response(429)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "error": {
                            "type": "daily_limit_exceeded",
                            "message": f"Daily cost limit ${CONFIG['daily_limit_usd']} exceeded"
                        }
                    }).encode())
                    return

                # 5. 대형 입력 경고
                if estimated_input > CONFIG["max_input_tokens"]:
                    log(f"⚠️ WARN: Large input detected - {estimated_input} tokens")

            except Exception as e:
                log(f"Parse error: {e}")

        # 프록시 실행
        response = self._proxy_request("POST", body)

        # 사용량 추적
        if response and "/v1/messages" in self.path:
            try:
                resp_data = json.loads(response.decode("utf-8"))
                usage = resp_data.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                model = resp_data.get("model", "unknown")

                cost = estimate_cost(model, input_tokens, output_tokens)
                update_usage(cost)

                log(f"✅ API call: {model} | {input_tokens} in / {output_tokens} out | ${cost:.4f} | Daily: ${daily_usage['cost']:.2f}")
            except:
                pass

    def do_GET(self):
        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "running",
                "config": CONFIG,
                "daily_usage": daily_usage
            }, indent=2).encode())
            return

        self._proxy_request("GET")

    def log_message(self, format, *args):
        pass  # Suppress default logging


def main():
    global ANTHROPIC_API_KEY

    if not ANTHROPIC_API_KEY:
        # 환경변수에서 로드 시도
        if os.path.exists("/etc/etf-tracker.env"):
            with open("/etc/etf-tracker.env") as f:
                for line in f:
                    if "ANTHROPIC_API_KEY" in line:
                        key, val = line.strip().split("=", 1)
                        os.environ["ANTHROPIC_API_KEY"] = val
                        ANTHROPIC_API_KEY = val
                        break

    server = HTTPServer(("0.0.0.0", PORT), CostGuardHandler)

    log("═══════════════════════════════════════")
    log("  API Cost Guard Started")
    log(f"  Listening on http://0.0.0.0:{PORT}")
    log("═══════════════════════════════════════")
    log(f"Config: {json.dumps(CONFIG)}")
    log("")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Shutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
