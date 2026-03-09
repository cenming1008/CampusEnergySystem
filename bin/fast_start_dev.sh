#!/bin/bash
# ============================================
# 开发模式快速启动 - 前后端本地运行，中间件 Docker
# ============================================
# 适合二次开发：热重载、断点调试、快速重启
# - Docker: 数据库 + Redis + MQTT
# - 本地: 后端 (python run.py) + 前端 (npm run dev)
# ============================================

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

# 1. 检查 Docker
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker 未运行${NC}"
    echo -e "${YELLOW}请先启动 Docker Desktop${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker 运行中${NC}"
echo ""

mkdir -p logs

# 2. 启动中间件（仅 db, redis, mqtt）
echo -e "${YELLOW}➜ 启动中间件（数据库 + Redis + MQTT）...${NC}"
docker compose -f docker-compose.dev.yml up -d
echo -e "${GREEN}✅ 中间件已启动${NC}"
echo ""

# 3. 等待中间件就绪
echo -e "${YELLOW}➜ 等待中间件就绪...${NC}"
sleep 5
if docker exec mine_energy_db_dev pg_isready -U admin -d mine_energy &>/dev/null; then
    echo -e "${GREEN}✅ 数据库就绪 (localhost:5432)${NC}"
else
    echo -e "${YELLOW}⚠️  数据库可能仍在启动中，请稍候${NC}"
fi
echo ""

# 4. 启动后端（本地）
echo -e "${YELLOW}➜ 启动后端（本地）...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ 未找到 venv，请先创建虚拟环境: python -m venv venv${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 后端将在后台运行${NC}"
(
    source venv/bin/activate
    RELOAD=True python run.py
) > logs/backend_dev.log 2>&1 &
BACKEND_PID=$!
echo "   后端 PID: $BACKEND_PID (日志: logs/backend_dev.log)"
echo ""

# 5. 等待后端就绪
echo -e "${YELLOW}➜ 等待后端就绪...${NC}"
for i in {1..30}; do
    if curl -s -f http://localhost:8088/health &>/dev/null; then
        echo -e "${GREEN}✅ 后端就绪 (http://localhost:8088)${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠️  后端启动超时，请查看 logs/backend_dev.log${NC}"
    fi
done
echo ""

# 6. 启动前端（本地）
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

# 7. 完成
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
