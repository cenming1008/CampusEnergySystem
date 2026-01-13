#!/bin/bash
# 快速启动脚本 - 使用缓存的镜像，不重新构建
# 适合日常开发使用

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🚀 MineEnergySystem 快速启动（使用缓存）${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 检查 Docker
if ! docker info &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker 未运行，正在启动...${NC}"
    open /Applications/Docker.app
    echo "等待 Docker 启动..."
    sleep 10
fi

echo -e "${GREEN}✅ Docker 运行中${NC}"
echo ""

# 检查是否有镜像
IMAGES_COUNT=$(docker images | grep -c -E "python|timescale|redis|mosquitto|mine" || echo "0")

if [ "$IMAGES_COUNT" -lt 4 ]; then
    echo -e "${YELLOW}⚠️  检测到镜像缺失，将执行完整构建...${NC}"
    docker compose up -d --build
else
    echo -e "${GREEN}✅ 使用缓存的镜像快速启动${NC}"
    echo ""
    # 不使用 --build，直接启动
    docker compose up -d
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 启动完成！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 等待服务就绪
echo "⏳ 等待服务就绪..."
sleep 3

# 检查服务状态
echo ""
echo "📊 服务状态："
docker compose ps

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📚 访问地址：${NC}"
echo -e "   ${GREEN}后端 API 文档:${NC} http://localhost:8088/docs"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
