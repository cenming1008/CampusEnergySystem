#!/bin/bash

# ============================================
# 停止本地开发环境 Docker 服务
# ============================================

set -e

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
