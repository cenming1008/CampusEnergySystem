#!/bin/bash

# ============================================
# 卸载本地服务并使用 Docker 版本
# ============================================

set -e

echo "=========================================="
echo "  停止并卸载本地服务"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 停止本地服务
echo -e "${YELLOW}步骤 1: 停止本地服务${NC}"
echo ""

echo -e "${YELLOW}➜${NC} 停止 PostgreSQL..."
brew services stop postgresql@14 2>/dev/null || echo "  PostgreSQL 未运行或未安装"

echo -e "${YELLOW}➜${NC} 停止 Redis..."
brew services stop redis 2>/dev/null || echo "  Redis 未运行或未安装"

echo -e "${YELLOW}➜${NC} 停止 Mosquitto..."
brew services stop mosquitto 2>/dev/null || echo "  Mosquitto 未运行或未安装"

echo ""
echo -e "${GREEN}✔${NC} 所有本地服务已停止"
echo ""

# 2. 检查端口是否释放
echo -e "${YELLOW}步骤 2: 检查端口状态${NC}"
echo ""

check_port() {
    port=$1
    service=$2
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠${NC}  端口 $port ($service) 仍被占用"
        lsof -i :$port
    else
        echo -e "${GREEN}✔${NC}  端口 $port ($service) 已释放"
    fi
}

check_port 5432 "PostgreSQL"
check_port 6379 "Redis"
check_port 1883 "Mosquitto"

echo ""
echo "=========================================="
echo "  是否要完全卸载这些服务？"
echo "=========================================="
echo ""
echo "如果你确定不再需要本地安装的服务，可以运行："
echo ""
echo -e "${YELLOW}卸载命令：${NC}"
echo "  brew uninstall postgresql@14"
echo "  brew uninstall redis"
echo "  brew uninstall mosquitto"
echo ""
echo -e "${YELLOW}或者保留安装但不运行（推荐）：${NC}"
echo "  不需要做任何事，服务已停止且不会自动启动"
echo ""
echo "=========================================="
echo "  Docker 服务状态"
echo "=========================================="
echo ""
docker-compose -f docker-compose.dev.yml ps
echo ""
echo -e "${GREEN}✔${NC} 现在可以使用 Docker 中的服务了！"
echo ""
