# OpenClaw on Hostinger VPS - Setup Guide

## Overview

[OpenClaw](https://openclaw.ai/)은 오픈소스 AI 에이전트 플랫폼입니다 (구 Clawdbot/Moltbot).
WhatsApp, Telegram, Discord, Slack 등과 연동하여 개인 AI 비서로 사용할 수 있습니다.

이 가이드는 **Hostinger VPS**에 Docker를 사용하여 OpenClaw를 설치하는 방법을 설명합니다.

---

## Requirements

| 항목 | 최소 | 권장 |
|------|------|------|
| **RAM** | 2GB | 4GB+ |
| **CPU** | 1 vCPU | 2 vCPU+ |
| **Disk** | 10GB | 20GB+ |
| **OS** | Ubuntu 22.04 | Ubuntu 24.04 |

### Hostinger VPS Plan 추천

- **KVM 2** (4GB RAM, 2 vCPU, 100GB SSD) - 권장
- **KVM 1** (2GB RAM, 1 vCPU, 50GB SSD) - 최소 사양

### 사전 준비

- Hostinger VPS (Ubuntu 22.04 또는 24.04)
- SSH 접속 정보 (IP, root 비밀번호 또는 SSH 키)
- AI Provider API 키 (Anthropic 또는 OpenAI 중 하나 이상)
  - Anthropic: https://console.anthropic.com/
  - OpenAI: https://platform.openai.com/api-keys

---

## Installation

### 방법 1: 자동 설치 (권장)

SSH로 VPS에 접속한 후:

```bash
# 1. 이 저장소를 클론
git clone https://github.com/Choi-Hyeonwoo/n8n-self-hosted.git
cd n8n-self-hosted/openclaw

# 2. 설치 스크립트 실행
sudo ./install.sh
```

스크립트가 자동으로 다음을 수행합니다:
- 시스템 패키지 업데이트
- Docker & Docker Compose 설치
- OpenClaw 소스 클론 및 빌드
- 환경설정 및 API 키 입력
- 방화벽 설정
- systemd 서비스 등록 (자동 재시작)

### 방법 2: Hostinger Docker Manager (GUI)

Hostinger hPanel에서 직접 설치하는 방법:

1. hPanel 로그인 → VPS 관리 페이지
2. 좌측 사이드바에서 **Docker Manager** 클릭
3. Docker Manager 설치 (2-3분 소요)
4. **Catalog** 탭에서 "OpenClaw" 검색
5. **Deploy** 클릭
6. 환경 변수 설정:
   - `OPENCLAW_GATEWAY_TOKEN`: 자동 생성됨 (반드시 저장)
   - `ANTHROPIC_API_KEY`: Anthropic API 키 입력
7. Deploy 완료 후 할당된 포트로 대시보드 접속

### 방법 3: 수동 설치

```bash
# 1. 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 2. Docker 설치
curl -fsSL https://get.docker.com | sh

# 3. OpenClaw 소스 클론
git clone https://github.com/openclaw/openclaw.git /opt/openclaw
cd /opt/openclaw

# 4. 환경 설정
cp .env.example .env
# .env 파일을 편집하여 API 키와 토큰 입력
nano .env

# 5. Docker 이미지 빌드
docker build -t openclaw:local -f Dockerfile .

# 6. 온보딩 위저드 실행
docker compose run --rm openclaw-cli onboard

# 7. 게이트웨이 시작
docker compose up -d openclaw-gateway
```

---

## Post-Installation

### 대시보드 접속

브라우저에서 `http://YOUR_VPS_IP:18789/` 로 접속합니다.

### Gateway Token 입력

1. 대시보드 Settings 페이지로 이동
2. Gateway Token을 입력 (설치 시 생성된 토큰)

### 메시징 채널 연결

대시보드에서 원하는 채널을 연결할 수 있습니다:
- **WhatsApp**: QR 코드 스캔
- **Telegram**: Bot Token 입력
- **Discord**: Bot Token 입력
- **Slack**: OAuth 설정

---

## Management Commands

```bash
# 서비스 상태 확인
sudo systemctl status openclaw

# 로그 확인
docker compose -f /opt/openclaw/docker-compose.yml logs -f

# 서비스 재시작
sudo systemctl restart openclaw

# 서비스 중지
sudo systemctl stop openclaw

# OpenClaw 업데이트
cd /opt/openclaw
git pull origin main
docker build -t openclaw:local .
docker compose up -d openclaw-gateway
```

---

## Security Recommendations

### 1. SSH 키 기반 인증 활성화

```bash
# 로컬 머신에서 SSH 키 생성 (아직 없다면)
ssh-keygen -t ed25519

# VPS에 키 복사
ssh-copy-id root@YOUR_VPS_IP

# 비밀번호 인증 비활성화
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no 로 변경
sudo systemctl restart sshd
```

### 2. 리버스 프록시 설정 (HTTPS)

Nginx + Let's Encrypt를 사용하여 HTTPS를 설정하는 것을 권장합니다:

```bash
# Nginx 설치
sudo apt install nginx certbot python3-certbot-nginx -y

# Nginx 설정
sudo tee /etc/nginx/sites-available/openclaw <<'NGINX'
server {
    listen 80;
    server_name openclaw.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:18789;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

sudo ln -s /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# SSL 인증서 발급
sudo certbot --nginx -d openclaw.yourdomain.com
```

### 3. 방화벽 강화

```bash
# 특정 IP에서만 접근 허용
sudo ufw delete allow 18789/tcp
sudo ufw allow from YOUR_HOME_IP to any port 18789 proto tcp
```

---

## Troubleshooting

### Docker 빌드 실패
```bash
# 디스크 공간 확인
df -h
# Docker 캐시 정리
docker system prune -a
# 재빌드
docker build --no-cache -t openclaw:local .
```

### 포트 접근 불가
```bash
# 방화벽 규칙 확인
sudo ufw status
# Docker 컨테이너 상태 확인
docker ps
# 포트 리스닝 확인
ss -tlnp | grep 18789
```

### 메모리 부족
```bash
# 스왑 추가 (2GB)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 로그 확인
```bash
# 게이트웨이 로그
docker compose -f /opt/openclaw/docker-compose.yml logs openclaw-gateway

# 시스템 로그
journalctl -u openclaw -f
```

---

## Cost Estimation

| 항목 | 비용 |
|------|------|
| Hostinger VPS KVM 2 | ~$10/month |
| Anthropic API (Claude) | Usage-based (~$3-15/100K tokens) |
| OpenAI API (GPT-4) | Usage-based (~$5-30/100K tokens) |
| **Total** | **~$15-40/month** (사용량에 따라 변동) |

> API 비용은 사용량에 따라 크게 달라질 수 있습니다. 스케줄링 작업 등 자동화 기능을 사용하면 비용이 빠르게 증가할 수 있으니 주의하세요.

---

## Resources

- [OpenClaw Official Site](https://openclaw.ai/)
- [OpenClaw Documentation](https://docs.openclaw.ai/)
- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [Hostinger VPS Guide](https://www.hostinger.com/support/how-to-install-openclaw-on-hostinger-vps/)
- [Docker Installation Guide](https://docs.openclaw.ai/install/docker)
