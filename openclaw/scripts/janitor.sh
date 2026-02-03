#!/bin/bash
#
# System Janitor for VPS Multi-Agent Environment
# Docker/Log/Temp 정리 및 시스템 건강성 유지
#
# Usage:
#   ./janitor.sh              # 전체 정리
#   ./janitor.sh --check      # 상태 확인만
#   ./janitor.sh --aggressive # 공격적 정리 (디스크 부족 시)
#

set -euo pipefail

LOG_FILE="/var/log/janitor.log"
REPORT_FILE="/tmp/janitor_report.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[$timestamp] $1"
    echo "[$timestamp] $1" >> "$LOG_FILE" 2>/dev/null || true
}

log_section() {
    echo ""
    log "${YELLOW}═══════════════════════════════════════${NC}"
    log "${YELLOW}  $1${NC}"
    log "${YELLOW}═══════════════════════════════════════${NC}"
}

# 디스크 사용량 확인
get_disk_usage() {
    df / | awk 'NR==2 {print $5}' | tr -d '%'
}

get_disk_free_gb() {
    df -BG / | awk 'NR==2 {print $4}' | tr -d 'G'
}

# Docker 정리
clean_docker() {
    log_section "Docker Cleanup"

    local before=$(docker system df --format '{{.Size}}' 2>/dev/null | head -1 || echo "0B")

    # 중지된 컨테이너 삭제
    stopped=$(docker ps -aq --filter status=exited 2>/dev/null | wc -l)
    if [ "$stopped" -gt 0 ]; then
        log "Removing $stopped stopped containers..."
        docker container prune -f 2>/dev/null || true
    fi

    # Dangling 이미지 삭제
    dangling=$(docker images -f "dangling=true" -q 2>/dev/null | wc -l)
    if [ "$dangling" -gt 0 ]; then
        log "Removing $dangling dangling images..."
        docker image prune -f 2>/dev/null || true
    fi

    # 사용하지 않는 볼륨 삭제
    unused_volumes=$(docker volume ls -qf dangling=true 2>/dev/null | wc -l)
    if [ "$unused_volumes" -gt 0 ]; then
        log "Removing $unused_volumes unused volumes..."
        docker volume prune -f 2>/dev/null || true
    fi

    # 빌드 캐시 정리
    log "Cleaning build cache..."
    docker builder prune -f --keep-storage 5GB 2>/dev/null || true

    local after=$(docker system df --format '{{.Size}}' 2>/dev/null | head -1 || echo "0B")
    log "${GREEN}Docker: $before → $after${NC}"
}

# 공격적 Docker 정리 (디스크 부족 시)
clean_docker_aggressive() {
    log_section "Aggressive Docker Cleanup"

    log "⚠️ Removing ALL unused images, networks, volumes..."
    docker system prune -af --volumes 2>/dev/null || true

    # 오래된 이미지 삭제 (7일 이상)
    log "Removing images older than 7 days..."
    docker image prune -af --filter "until=168h" 2>/dev/null || true
}

# 로그 파일 정리
clean_logs() {
    log_section "Log Cleanup"

    local freed=0

    # systemd journal (if exists)
    if command -v journalctl &>/dev/null; then
        log "Vacuuming journal logs..."
        journalctl --vacuum-time=3d 2>/dev/null || true
        journalctl --vacuum-size=100M 2>/dev/null || true
    fi

    # Docker 컨테이너 로그 truncate
    if [ -d /var/lib/docker/containers ]; then
        log "Truncating Docker container logs..."
        find /var/lib/docker/containers -name "*.log" -size +100M -exec truncate -s 10M {} \; 2>/dev/null || true
    fi

    # 애플리케이션 로그 정리
    log "Cleaning application logs..."

    # n8n 로그
    find /home/user/.n8n -name "*.log" -mtime +7 -delete 2>/dev/null || true

    # ETF tracker 로그 (보관 7일)
    find /var/log -name "etf_*.log" -mtime +7 -delete 2>/dev/null || true

    # execute_smart 로그 (보관 3일)
    if [ -f /var/log/execute_smart.log ]; then
        tail -n 1000 /var/log/execute_smart.log > /var/log/execute_smart.log.tmp 2>/dev/null && \
        mv /var/log/execute_smart.log.tmp /var/log/execute_smart.log 2>/dev/null || true
    fi

    # 일반 로그 로테이션
    find /var/log -name "*.log" -size +50M -exec truncate -s 5M {} \; 2>/dev/null || true
    find /var/log -name "*.log.*" -mtime +7 -delete 2>/dev/null || true

    log "${GREEN}Log cleanup completed${NC}"
}

# 임시 파일 정리
clean_temp() {
    log_section "Temp Files Cleanup"

    # /tmp 정리 (1일 이상 된 파일)
    log "Cleaning /tmp..."
    find /tmp -type f -atime +1 -delete 2>/dev/null || true
    find /tmp -type d -empty -delete 2>/dev/null || true

    # npm cache
    if command -v npm &>/dev/null; then
        log "Cleaning npm cache..."
        npm cache clean --force 2>/dev/null || true
    fi

    # pip cache
    if command -v pip3 &>/dev/null; then
        log "Cleaning pip cache..."
        pip3 cache purge 2>/dev/null || true
    fi

    # apt cache
    log "Cleaning apt cache..."
    apt-get clean 2>/dev/null || true
    apt-get autoremove -y 2>/dev/null || true

    log "${GREEN}Temp cleanup completed${NC}"
}

# 메모리 최적화
optimize_memory() {
    log_section "Memory Optimization"

    # 메모리 사용량 확인
    local mem_used=$(free -m | awk 'NR==2{printf "%.0f", $3/$2*100}')
    log "Current memory usage: ${mem_used}%"

    if [ "$mem_used" -gt 80 ]; then
        log "⚠️ High memory usage detected. Optimizing..."

        # Page cache 정리
        sync
        echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true

        local mem_after=$(free -m | awk 'NR==2{printf "%.0f", $3/$2*100}')
        log "${GREEN}Memory after optimization: ${mem_after}%${NC}"
    fi
}

# 프로세스 좀비/고아 정리
clean_processes() {
    log_section "Process Cleanup"

    # 좀비 프로세스 찾기
    zombies=$(ps aux | awk '$8 ~ /^Z/ {print $2}' | wc -l)
    if [ "$zombies" -gt 0 ]; then
        log "⚠️ Found $zombies zombie processes"
    else
        log "${GREEN}No zombie processes${NC}"
    fi

    # 오래된 Python 프로세스 정리 (24시간 이상)
    old_python=$(ps aux | grep "[p]ython" | awk '$10 ~ /[0-9]+-/ {print $2}' | wc -l)
    if [ "$old_python" -gt 0 ]; then
        log "Found $old_python old Python processes (24h+)"
    fi
}

# 시스템 상태 리포트 생성
generate_report() {
    log_section "System Health Report"

    local disk_usage=$(get_disk_usage)
    local disk_free=$(get_disk_free_gb)
    local mem_usage=$(free -m | awk 'NR==2{printf "%.0f", $3/$2*100}')
    local load=$(uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $1}' | xargs)
    local docker_containers=$(docker ps -q 2>/dev/null | wc -l)
    local uptime_str=$(uptime -p)

    # JSON 리포트
    cat > "$REPORT_FILE" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "disk": {
        "usage_percent": $disk_usage,
        "free_gb": $disk_free
    },
    "memory": {
        "usage_percent": $mem_usage
    },
    "load": "$load",
    "docker_containers": $docker_containers,
    "uptime": "$uptime_str",
    "status": "$([ "$disk_usage" -lt 80 ] && [ "$mem_usage" -lt 80 ] && echo 'healthy' || echo 'warning')"
}
EOF

    # 콘솔 출력
    log "┌─────────────────────────────────┐"
    log "│ Disk Usage:    ${disk_usage}% (${disk_free}GB free)"
    log "│ Memory Usage:  ${mem_usage}%"
    log "│ Load Average:  $load"
    log "│ Docker:        $docker_containers containers"
    log "│ Uptime:        $uptime_str"
    log "└─────────────────────────────────┘"

    # 경고 상태
    if [ "$disk_usage" -gt 90 ]; then
        log "${RED}⚠️ CRITICAL: Disk usage above 90%!${NC}"
    elif [ "$disk_usage" -gt 80 ]; then
        log "${YELLOW}⚠️ WARNING: Disk usage above 80%${NC}"
    fi

    if [ "$mem_usage" -gt 90 ]; then
        log "${RED}⚠️ CRITICAL: Memory usage above 90%!${NC}"
    elif [ "$mem_usage" -gt 80 ]; then
        log "${YELLOW}⚠️ WARNING: Memory usage above 80%${NC}"
    fi
}

# 메인 실행
main() {
    log "═══════════════════════════════════════"
    log "  System Janitor Started"
    log "═══════════════════════════════════════"

    local mode="${1:-full}"

    case "$mode" in
        --check)
            generate_report
            ;;
        --aggressive)
            clean_docker_aggressive
            clean_logs
            clean_temp
            optimize_memory
            clean_processes
            generate_report
            ;;
        *)
            # 일반 정리
            local disk_usage=$(get_disk_usage)

            if [ "$disk_usage" -gt 85 ]; then
                log "${YELLOW}High disk usage ($disk_usage%). Running aggressive cleanup...${NC}"
                clean_docker_aggressive
            else
                clean_docker
            fi

            clean_logs
            clean_temp

            if [ "$disk_usage" -gt 80 ]; then
                optimize_memory
            fi

            clean_processes
            generate_report
            ;;
    esac

    log ""
    log "${GREEN}Janitor completed successfully${NC}"
}

# 실행
main "$@"
