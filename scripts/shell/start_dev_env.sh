#!/bin/bash

# ============================================
# 本地开发环境启动脚本
# ============================================
# 用途：启动 Docker 服务（TimescaleDB, MQTT, Redis）
# 说明：Backend 和 Frontend 需要手动启动
# ============================================

set -e

echo "=========================================="
echo "  启动本地开发环境"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Docker 是否运行
echo -e "${YELLOW}➜${NC} 检查 Docker 状态..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✖${NC} Docker 未运行，请先启动 Docker"
    exit 1
fi
echo -e "${GREEN}✔${NC} Docker 正在运行"
echo ""

# 检查 docker-compose.dev.yml 是否存在
if [ ! -f "docker-compose.dev.yml" ]; then
    echo -e "${RED}✖${NC} 找不到 docker-compose.dev.yml 文件"
    exit 1
fi

# 启动 Docker 服务
echo -e "${YELLOW}➜${NC} 启动 Docker 服务 (TimescaleDB, MQTT, Redis)..."
docker-compose -f docker-compose.dev.yml up -d

# 等待服务启动
echo ""
echo -e "${YELLOW}➜${NC} 等待服务健康检查..."
sleep 5

# 检查服务状态
echo ""
echo -e "${YELLOW}➜${NC} 检查服务状态..."
docker-compose -f docker-compose.dev.yml ps

# 测试服务连接
echo ""
echo "=========================================="
echo "  测试服务连接"
echo "=========================================="

# 测试数据库
echo -e "${YELLOW}➜${NC} 测试 TimescaleDB 连接..."
if docker exec mine_energy_db_dev pg_isready -U admin -d mine_energy > /dev/null 2>&1; then
    echo -e "${GREEN}✔${NC} TimescaleDB 连接成功 (localhost:5432)"
else
    echo -e "${RED}✖${NC} TimescaleDB 连接失败"
fi

# 测试 Redis
echo -e "${YELLOW}➜${NC} 测试 Redis 连接..."
if docker exec ems_redis_dev redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✔${NC} Redis 连接成功 (localhost:6379)"
else
    echo -e "${RED}✖${NC} Redis 连接失败"
fi

# 测试 MQTT（简单检查容器是否运行）
echo -e "${YELLOW}➜${NC} 测试 MQTT 服务..."
if docker ps | grep mine_mqtt_dev > /dev/null 2>&1; then
    echo -e "${GREEN}✔${NC} MQTT 服务正在运行 (localhost:1883)"
else
    echo -e "${RED}✖${NC} MQTT 服务未运行"
fi

echo ""
echo "=========================================="
echo "  Docker 服务启动完成！"
echo "=========================================="
echo ""
echo -e "${GREEN}已启动的服务：${NC}"
echo "  • TimescaleDB: localhost:5432"
echo "  • MQTT:        localhost:1883"
echo "  • Redis:       localhost:6379"
echo ""
echo -e "${YELLOW}下一步操作：${NC}"
echo ""
echo "1. 配置环境变量（如果还未配置）："
echo "   cp env.example .env"
echo "   # 然后修改 .env 文件中的连接地址为 localhost"
echo ""
echo "2. 启动 Backend（新终端）："
echo "   source venv/bin/activate  # 激活虚拟环境"
echo "   python run.py"
echo ""
echo "3. 启动 Frontend（新终端）："
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "4. 访问系统："
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8088"
echo "   API Docs: http://localhost:8088/docs"
echo ""
echo -e "${YELLOW}停止 Docker 服务：${NC}"
echo "   docker-compose -f docker-compose.dev.yml stop"
echo ""
echo -e "${YELLOW}查看服务日志：${NC}"
echo "   docker-compose -f docker-compose.dev.yml logs -f"
echo ""
