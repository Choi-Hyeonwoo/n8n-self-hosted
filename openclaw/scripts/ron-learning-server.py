#!/usr/bin/env python3
"""
RON Learning Server
- n8n에서 지식사랑방 콘텐츠 학습 요청 수신
- RON workspace/knowledge 폴더에 저장
- RON에게 학습 알림

Usage:
    VPS에서 실행: python3 /home/openclaw/scripts/ron-learning-server.py

n8n workflow에서 호출:
    POST http://172.17.0.1:8768/learn
    {
        "action": "learn",
        "source": "지식사랑방",
        "topic": "AI기술",
        "threadId": "4",
        "folderId": "...",
        "timestamp": "2026-02-03_15-00-00",
        "content": "텍스트 내용...",
        "files": [{"type": "text", "id": "...", "name": "..."}],
        "title": "제목"
    }
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from datetime import datetime
import threading

# Configuration
PORT = 8768
WORKSPACE = "/home/openclaw/workspace"
KNOWLEDGE_DIR = os.path.join(WORKSPACE, "knowledge")
CLAUDE_MSG_FILE = os.path.join(WORKSPACE, "CLAUDE_TO_RON.md")
LEARNING_LOG = os.path.join(WORKSPACE, "LEARNING_LOG.md")

# Ensure directories exist
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

# Topic folder mapping (thread_id to folder name)
TOPIC_FOLDERS = {
    '2': '01-일반토론',
    '4': '02-AI기술',
    '14': '03-투자전략',
    '81': '04-개발노트',
    '83': '05-독서노트',
    '136': '06-시장분석',
    '147': '07-아이디어',
    '170': '08-프로젝트',
    '171': '09-학습자료',
    '179': '10-인사이트',
    '520': '11-뉴스공유',
    '619': '12-질문답변',
    '4681': '13-리서치',
    '11370': '14-회고록',
    '19852': '99-기타'
}


class LearningHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

    def send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/':
            # Return Claude message (backward compatible)
            try:
                with open(CLAUDE_MSG_FILE, 'r') as f:
                    msg = f.read()
            except:
                msg = "파일 없음"
            self.send_json(200, {'message': msg})

        elif self.path == '/status':
            # Return server status
            self.send_json(200, {
                'status': 'running',
                'port': PORT,
                'workspace': WORKSPACE,
                'knowledge_dir': KNOWLEDGE_DIR
            })

        elif self.path == '/knowledge':
            # List learned knowledge
            try:
                knowledge_files = []
                for root, dirs, files in os.walk(KNOWLEDGE_DIR):
                    for f in files:
                        if f.endswith('.md'):
                            knowledge_files.append(os.path.join(root, f).replace(KNOWLEDGE_DIR + '/', ''))
                self.send_json(200, {'files': knowledge_files[-20:]})  # Last 20 files
            except Exception as e:
                self.send_json(500, {'error': str(e)})

        else:
            self.send_json(404, {'error': 'Not found'})

    def do_POST(self):
        if self.path == '/learn':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(body)

                result = self.process_learning(data)
                self.send_json(200, result)

            except json.JSONDecodeError:
                self.send_json(400, {'error': 'Invalid JSON'})
            except Exception as e:
                self.send_json(500, {'error': str(e)})

        elif self.path == '/message':
            # Write message for RON to read
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(body)

                with open(CLAUDE_MSG_FILE, 'w') as f:
                    f.write(data.get('message', ''))

                self.send_json(200, {'status': 'ok'})
            except Exception as e:
                self.send_json(500, {'error': str(e)})

        else:
            self.send_json(404, {'error': 'Not found'})

    def process_learning(self, data):
        """Process learning data from n8n"""
        # Extract data
        source = data.get('source', 'unknown')
        topic = data.get('topic', '미분류')
        thread_id = data.get('threadId', '')
        timestamp = data.get('timestamp', datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        content = data.get('content', '')
        files = data.get('files', [])
        title = data.get('title', 'untitled')
        folder_id = data.get('folderId', '')

        # Determine topic folder
        topic_folder = TOPIC_FOLDERS.get(thread_id, '99-기타')
        topic_path = os.path.join(KNOWLEDGE_DIR, topic_folder)
        os.makedirs(topic_path, exist_ok=True)

        # Create knowledge file
        filename = f"{timestamp}_{title[:20]}.md"
        filepath = os.path.join(topic_path, filename)

        # Build knowledge content
        md_content = f"""# {title}

**소스**: {source}
**토픽**: {topic}
**시간**: {timestamp}
**Google Drive 폴더**: {folder_id}

---

{content}

---

## 첨부 파일
"""
        for f in files:
            md_content += f"- [{f.get('type')}] {f.get('name')} (ID: {f.get('id')})\n"

        # Save knowledge file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)

        # Update learning log
        log_entry = f"\n## [{timestamp}] {title}\n- 토픽: {topic}\n- 파일수: {len(files)}\n- 경로: {filepath}\n"
        try:
            with open(LEARNING_LOG, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except:
            pass

        return {
            'status': 'learned',
            'filepath': filepath,
            'topic': topic,
            'files_count': len(files)
        }


def run_server():
    server = HTTPServer(('0.0.0.0', PORT), LearningHandler)
    print(f"RON Learning Server started on port {PORT}")
    print(f"  - Workspace: {WORKSPACE}")
    print(f"  - Knowledge: {KNOWLEDGE_DIR}")
    print("Endpoints:")
    print(f"  GET  / - Claude message")
    print(f"  GET  /status - Server status")
    print(f"  GET  /knowledge - List learned files")
    print(f"  POST /learn - Process learning data")
    print(f"  POST /message - Write Claude message")
    server.serve_forever()


if __name__ == '__main__':
    run_server()
