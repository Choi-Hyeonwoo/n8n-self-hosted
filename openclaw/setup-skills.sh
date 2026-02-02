#!/usr/bin/env bash
# =============================================================================
# OpenClaw Skills & Capabilities Setup Script
# =============================================================================
# Run inside the VPS after OpenClaw is installed and running.
#
# Usage:
#   chmod +x setup-skills.sh
#   sudo ./setup-skills.sh
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }

OPENCLAW_DIR="/opt/openclaw"
SKILLS_DIR="/home/openclaw/.openclaw/skills"
CONTAINER="openclaw-openclaw-gateway-1"

echo ""
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   OpenClaw Skills & Capabilities Setup  ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Ensure skills directory exists
mkdir -p "$SKILLS_DIR"
chown -R 1000:1000 "$SKILLS_DIR"

# =============================================================================
# 1. SEARCH & RESEARCH - 웹 검색, 뉴스, 리서치
# =============================================================================
log_info "Installing Search & Research skills..."

# Brave Search - 웹 검색 (API 키 필요: https://brave.com/search/api/)
docker exec "$CONTAINER" npx clawdhub@latest install brave-search 2>/dev/null && \
    log_ok "brave-search installed" || log_warn "brave-search skipped"

# Tavily - AI 최적화 검색
docker exec "$CONTAINER" npx clawdhub@latest install tavily 2>/dev/null && \
    log_ok "tavily installed" || log_warn "tavily skipped"

# News Aggregator - 8개 소스 뉴스 (HN, GitHub Trending, Product Hunt 등)
docker exec "$CONTAINER" npx clawdhub@latest install news-aggregator 2>/dev/null && \
    log_ok "news-aggregator installed" || log_warn "news-aggregator skipped"

# YouTube Summarizer - 유튜브 요약
docker exec "$CONTAINER" npx clawdhub@latest install youtube-summarizer 2>/dev/null && \
    log_ok "youtube-summarizer installed" || log_warn "youtube-summarizer skipped"

# Perplexity - 웹 기반 리서치
docker exec "$CONTAINER" npx clawdhub@latest install perplexity 2>/dev/null && \
    log_ok "perplexity installed" || log_warn "perplexity skipped"

# =============================================================================
# 2. CODING & DEVELOPMENT - 코드 작성, GitHub 관리
# =============================================================================
log_info "Installing Coding & Development skills..."

# GitHub - gh CLI 통합
docker exec "$CONTAINER" npx clawdhub@latest install github 2>/dev/null && \
    log_ok "github installed" || log_warn "github skipped"

# GitHub PR - PR 생성, 리뷰, 테스트
docker exec "$CONTAINER" npx clawdhub@latest install github-pr 2>/dev/null && \
    log_ok "github-pr installed" || log_warn "github-pr skipped"

# Coding Agent - 다중 코딩 프레임워크
docker exec "$CONTAINER" npx clawdhub@latest install coding-agent 2>/dev/null && \
    log_ok "coding-agent installed" || log_warn "coding-agent skipped"

# Conventional Commits - 커밋 메시지 포맷
docker exec "$CONTAINER" npx clawdhub@latest install conventional-commits 2>/dev/null && \
    log_ok "conventional-commits installed" || log_warn "conventional-commits skipped"

# DeepWiki - GitHub 레포 문서 조회
docker exec "$CONTAINER" npx clawdhub@latest install deepwiki 2>/dev/null && \
    log_ok "deepwiki installed" || log_warn "deepwiki skipped"

# =============================================================================
# 3. DEVOPS & CLOUD - 서버 관리, 배포
# =============================================================================
log_info "Installing DevOps & Cloud skills..."

# Sysadmin Toolbox - DevOps/보안 도구 참조
docker exec "$CONTAINER" npx clawdhub@latest install sysadmin-toolbox 2>/dev/null && \
    log_ok "sysadmin-toolbox installed" || log_warn "sysadmin-toolbox skipped"

# Linux Service Triage - 리눅스 서비스 진단
docker exec "$CONTAINER" npx clawdhub@latest install linux-service-triage 2>/dev/null && \
    log_ok "linux-service-triage installed" || log_warn "linux-service-triage skipped"

# Vercel Deploy - 웹사이트 배포
docker exec "$CONTAINER" npx clawdhub@latest install vercel-deploy 2>/dev/null && \
    log_ok "vercel-deploy installed" || log_warn "vercel-deploy skipped"

# =============================================================================
# 4. FINANCE & MARKET - 금융 정보, 시장 분석
# =============================================================================
log_info "Installing Finance & Market skills..."

# SerpAPI - Google/금융 검색
docker exec "$CONTAINER" npx clawdhub@latest install serpapi 2>/dev/null && \
    log_ok "serpapi installed" || log_warn "serpapi skipped"

# =============================================================================
# 5. PRODUCTIVITY - 생산성 도구
# =============================================================================
log_info "Installing Productivity skills..."

# TLDR - 간소화된 매뉴얼 페이지
docker exec "$CONTAINER" npx clawdhub@latest install tldr 2>/dev/null && \
    log_ok "tldr installed" || log_warn "tldr skipped"

# JQ - JSON 데이터 처리
docker exec "$CONTAINER" npx clawdhub@latest install jq 2>/dev/null && \
    log_ok "jq installed" || log_warn "jq skipped"

# DuckDB - SQL 데이터 분석
docker exec "$CONTAINER" npx clawdhub@latest install duckdb-en 2>/dev/null && \
    log_ok "duckdb-en installed" || log_warn "duckdb-en skipped"

# =============================================================================
# 6. BROWSER & AUTOMATION - 브라우저 자동화
# =============================================================================
log_info "Installing Browser & Automation skills..."

# Playwright CLI - 브라우저 테스트/스크래핑
docker exec "$CONTAINER" npx clawdhub@latest install playwright-cli 2>/dev/null && \
    log_ok "playwright-cli installed" || log_warn "playwright-cli skipped"

# =============================================================================
# 7. IMAGE & MEDIA - 이미지/미디어 생성
# =============================================================================
log_info "Installing Image & Media skills..."

# Pollinations - 멀티모델 이미지 생성 (무료)
docker exec "$CONTAINER" npx clawdhub@latest install pollinations 2>/dev/null && \
    log_ok "pollinations installed" || log_warn "pollinations skipped"

# =============================================================================
# 8. MEMORY & SELF-IMPROVEMENT - 메모리, 자기 개선
# =============================================================================
log_info "Installing Memory & Self-Improvement skills..."

# Self Reflect - 대화 분석 및 학습
docker exec "$CONTAINER" npx clawdhub@latest install self-reflect 2>/dev/null && \
    log_ok "self-reflect installed" || log_warn "self-reflect skipped"

# Auto Updater - 자동 업데이트
docker exec "$CONTAINER" npx clawdhub@latest install auto-updater 2>/dev/null && \
    log_ok "auto-updater installed" || log_warn "auto-updater skipped"

# Skills Audit - 보안 감사
docker exec "$CONTAINER" npx clawdhub@latest install skills-audit 2>/dev/null && \
    log_ok "skills-audit installed" || log_warn "skills-audit skipped"

# Fix permissions
chown -R 1000:1000 "$SKILLS_DIR" 2>/dev/null || true

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}   Skills Installation Complete!         ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "  ${YELLOW}Restart gateway to load new skills:${NC}"
echo -e "    cd /opt/openclaw && docker compose restart openclaw-gateway"
echo ""
echo -e "  ${YELLOW}API Keys needed for some skills:${NC}"
echo -e "    - Brave Search: https://brave.com/search/api/"
echo -e "    - Tavily:       https://tavily.com/"
echo -e "    - Perplexity:   https://www.perplexity.ai/settings/api"
echo -e "    - SerpAPI:      https://serpapi.com/"
echo ""
echo -e "  ${YELLOW}Add API keys to config:${NC}"
echo -e "    Edit /home/openclaw/.openclaw/openclaw.json"
echo ""
