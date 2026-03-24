#!/bin/bash
# 开发模式快捷入口
# 说明：
# - 中间件启动逻辑复用 scripts/shell/start_dev_env.sh
# - 这里只额外负责本地后端和前端的后台启动

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
echo -e "${BLUE}  🔧 MineEnergySystem 开发模式启动${NC}"
echo -e "${BLUE}  （中间件 Docker + 前后端本地）${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

mkdir -p logs

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
(
    source venv/bin/activate
    RELOAD=True python run.py
) > logs/backend_dev.log 2>&1 &
BACKEND_PID=$!
echo "   后端 PID: $BACKEND_PID (日志: logs/backend_dev.log)"
echo ""

# 3. 等待后端就绪
echo -e "${YELLOW}➜ 等待后端就绪...${NC}"
# 用 /health/live：只表示进程已监听，不依赖数据库（/health 可能因 DB 慢而长时间无响应）
for i in {1..30}; do
    if curl -s -f http://localhost:8088/health/live &>/dev/null; then
        echo -e "${GREEN}✅ 后端就绪 (http://localhost:8088)${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠️  后端启动超时，请查看 logs/backend_dev.log${NC}"
    fi
done
echo ""

# 4. 启动前端（本地）
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
(cd frontend && npm run dev) > logs/frontend_dev.log 2>&1 &
FRONTEND_PID=$!
echo "   前端 PID: $FRONTEND_PID (日志: logs/frontend_dev.log)"
sleep 3
echo ""

# 5. 完成
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 开发环境已启动！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📚 访问地址：${NC}"
echo -e "   ${GREEN}前端:${NC}     http://localhost:3000 或 http://localhost:5173"
echo -e "   ${GREEN}后端 API:${NC} http://localhost:8088/docs"
echo ""
echo -e "${BLUE}📝 说明：${NC}"
echo -e "   • 前后端支持热重载，修改代码自动生效"
echo -e "   • 停止: ${YELLOW}./scripts/shell/stop_dev_env.sh${NC} (停止 Docker)"
echo -e "   • 停止前后端: ${YELLOW}kill $BACKEND_PID $FRONTEND_PID${NC} 或 ${YELLOW}pkill -f 'python run.py' && pkill -f vite${NC}"
echo -e "   • 查看后端日志: ${YELLOW}tail -f logs/backend_dev.log${NC}"
echo -e "   • 查看前端日志: ${YELLOW}tail -f logs/frontend_dev.log${NC}"
echo ""
