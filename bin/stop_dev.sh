#!/bin/bash
# 开发环境快捷停止入口。
# 停止本地后端、MQTT ingest worker、前端进程，并停止 docker-compose.dev.yml 中的开发中间件。

set -e

PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJECT_DIR"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

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

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  园区综合能源管理系统开发环境停止${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

stop_pid_file "$PID_DIR/backend_dev.pid" "后端"
stop_pid_file "$PID_DIR/mqtt_ingest_worker_dev.pid" "MQTT ingest worker"
stop_pid_file "$PID_DIR/frontend_dev.pid" "前端"

if ! command -v docker >/dev/null 2>&1; then
    echo -e "${RED}Docker 未安装，无法停止开发中间件${NC}"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}Docker 未运行，已完成本地进程清理${NC}"
    exit 0
fi

if [ ! -f "docker-compose.dev.yml" ]; then
    echo -e "${RED}找不到 docker-compose.dev.yml 文件${NC}"
    exit 1
fi

echo -e "${YELLOW}➜${NC} 停止开发中间件..."
docker compose -f docker-compose.dev.yml stop

echo ""
echo -e "${GREEN}开发环境已停止${NC}"
echo -e "${YELLOW}提示：数据库、Redis、MQTT 数据会保留；如需删除容器可手动执行 docker compose -f docker-compose.dev.yml down。${NC}"
