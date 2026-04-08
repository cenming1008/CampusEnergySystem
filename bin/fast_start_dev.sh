#!/bin/bash
# 开发模式快捷入口
# 说明：
# - 中间件启动逻辑复用 scripts/shell/start_dev_env.sh
# - 这里只额外负责本地后端、MQTT ingest worker 和前端的后台启动

set -e

# 切换到项目根目录
PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJECT_DIR"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🔧 园区综合能源管理系统开发模式启动${NC}"
echo -e "${BLUE}  （中间件 Docker + 后端/worker/前端本地）${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

mkdir -p logs

VENV_PYTHON="./venv/bin/python"
PID_DIR="logs/pids"
BACKEND_PID_FILE="$PID_DIR/backend_dev.pid"
WORKER_PID_FILE="$PID_DIR/mqtt_ingest_worker_dev.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend_dev.pid"

mkdir -p "$PID_DIR"

is_pid_running() {
    local pid="$1"
    [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

stop_pid_file() {
    local pid_file="$1"
    local label="$2"

    if [ ! -f "$pid_file" ]; then
        return
    fi

    local pid
    pid=$(cat "$pid_file" 2>/dev/null || true)
    if is_pid_running "$pid"; then
        echo -e "${YELLOW}⚠️  发现旧${label}进程 (PID: $pid)，先停止后再重新启动${NC}"
        kill "$pid" 2>/dev/null || true
        sleep 1
    fi
    rm -f "$pid_file"
}

wait_http_ready() {
    local url="$1"
    local label="$2"

    for i in {1..30}; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ ${label}就绪 (${url})${NC}"
            return 0
        fi
        sleep 1
    done

    echo -e "${RED}❌ ${label}未在预期时间内就绪: ${url}${NC}"
    return 1
}

# 1. 启动中间件（复用完整脚本）
echo -e "${YELLOW}➜ 启动中间件环境...${NC}"
./scripts/shell/start_dev_env.sh
echo ""

# 2. 启动后端（本地）
echo -e "${YELLOW}➜ 启动后端（本地）...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ 未找到 venv，请先创建虚拟环境: python -m venv venv${NC}"
    exit 1
fi
if [ ! -x "$VENV_PYTHON" ]; then
    echo -e "${RED}❌ 未找到可执行的 Python 解释器: $VENV_PYTHON${NC}"
    exit 1
fi

stop_pid_file "$BACKEND_PID_FILE" "后端"
stop_pid_file "$WORKER_PID_FILE" "MQTT ingest worker"
stop_pid_file "$FRONTEND_PID_FILE" "前端"

# 8088 已被占用时，再启动会得到 Address already in use，健康检查也可能一直等不到「新」进程
if command -v lsof >/dev/null 2>&1; then
    OLD_PIDS=$(lsof -nP -iTCP:8088 -sTCP:LISTEN -t 2>/dev/null || true)
    if [ -n "$OLD_PIDS" ]; then
        echo -e "${YELLOW}⚠️  端口 8088 已被占用 (PID: $OLD_PIDS)，先结束旧进程以便重启后端${NC}"
        kill $OLD_PIDS 2>/dev/null || true
        sleep 1
    fi
fi

echo -e "${GREEN}✅ 后端将在后台运行${NC}"
nohup env RELOAD=False "$VENV_PYTHON" run.py > logs/backend_dev.log 2>&1 < /dev/null &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$BACKEND_PID_FILE"
echo "   后端 PID: $BACKEND_PID (日志: logs/backend_dev.log)"
echo ""

# 3. 等待后端就绪
echo -e "${YELLOW}➜ 等待后端就绪...${NC}"
if ! wait_http_ready "http://127.0.0.1:8088/health/live" "后端"; then
    echo -e "${RED}❌ 后端未成功启动，开发环境启动中止${NC}"
    rm -f "$BACKEND_PID_FILE"
    exit 1
fi
echo ""

# 4. 启动 MQTT ingest worker（本地）
echo -e "${YELLOW}➜ 启动 MQTT ingest worker（本地）...${NC}"
echo -e "${GREEN}✅ MQTT ingest worker 将在后台运行${NC}"
nohup "$VENV_PYTHON" scripts/python/run_mqtt_ingest_worker.py > logs/mqtt_ingest_worker_dev.log 2>&1 < /dev/null &
WORKER_PID=$!
echo "$WORKER_PID" > "$WORKER_PID_FILE"
echo "   Worker PID: $WORKER_PID (日志: logs/mqtt_ingest_worker_dev.log)"
echo ""

# 5. 启动前端（本地）
echo -e "${YELLOW}➜ 启动前端（本地）...${NC}"
if [ ! -d "frontend" ]; then
    echo -e "${RED}❌ 未找到 frontend 目录${NC}"
    exit 1
fi
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}   首次运行，安装前端依赖...${NC}"
    (cd frontend && npm install)
fi
echo -e "${GREEN}✅ 前端将在后台运行${NC}"
nohup bash -lc "cd frontend && npm run dev" > logs/frontend_dev.log 2>&1 < /dev/null &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$FRONTEND_PID_FILE"
echo "   前端 PID: $FRONTEND_PID (日志: logs/frontend_dev.log)"
sleep 3
echo ""

FRONTEND_URL=$(grep -Eo 'http://localhost:[0-9]+' logs/frontend_dev.log | tail -n 1 || true)
if [ -z "$FRONTEND_URL" ]; then
    FRONTEND_URL="http://localhost:3000"
fi

# 6. 完成
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 开发环境已启动！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📚 访问地址：${NC}"
echo -e "   ${GREEN}前端:${NC}     ${FRONTEND_URL}"
echo -e "   ${GREEN}后端 API:${NC} http://localhost:8088/docs"
echo ""
echo -e "${BLUE}📝 说明：${NC}"
echo -e "   • 前端支持热重载；后端当前以稳定常驻模式运行"
echo -e "   • 停止: ${YELLOW}./scripts/shell/stop_dev_env.sh${NC} (停止 Docker)"
echo -e "   • 停止本地进程: ${YELLOW}kill $BACKEND_PID $WORKER_PID $FRONTEND_PID${NC}"
echo -e "   • 查看后端日志: ${YELLOW}tail -f logs/backend_dev.log${NC}"
echo -e "   • 查看 worker 日志: ${YELLOW}tail -f logs/mqtt_ingest_worker_dev.log${NC}"
echo -e "   • 查看前端日志: ${YELLOW}tail -f logs/frontend_dev.log${NC}"
echo ""
