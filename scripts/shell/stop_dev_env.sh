#!/bin/bash

# ============================================
# 停止本地开发环境 Docker 服务
# ============================================

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

PID_DIR="logs/pids"

stop_pid_file() {
    local pid_file="$1"
    local label="$2"

    if [ ! -f "$pid_file" ]; then
        return
    fi

    local pid
    pid=$(cat "$pid_file" 2>/dev/null || true)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo -e "${YELLOW}➜${NC} 停止本地${label}进程 (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        sleep 1
    fi
    rm -f "$pid_file"
}

echo "=========================================="
echo "  停止开发环境 Docker 服务"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 docker-compose.dev.yml 是否存在
if [ ! -f "docker-compose.dev.yml" ]; then
    echo -e "${RED}✖${NC} 找不到 docker-compose.dev.yml 文件"
    exit 1
fi

stop_pid_file "$PID_DIR/backend_dev.pid" "后端"
stop_pid_file "$PID_DIR/mqtt_ingest_worker_dev.pid" "MQTT ingest worker"
stop_pid_file "$PID_DIR/frontend_dev.pid" "前端"

# 停止服务
echo -e "${YELLOW}➜${NC} 停止 Docker 服务..."
docker compose -f docker-compose.dev.yml stop

echo ""
echo -e "${GREEN}✔${NC} Docker 服务已停止"
echo ""
echo -e "${YELLOW}提示：${NC}"
echo "  • 数据已保存，下次启动时数据仍然存在"
echo "  • 如需完全删除容器: docker compose -f docker-compose.dev.yml down"
echo "  • 如需删除数据卷: docker compose -f docker-compose.dev.yml down -v"
echo ""
