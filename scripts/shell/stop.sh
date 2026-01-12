#!/bin/bash
# MineEnergySystem 停止脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 颜色定义
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🛑 停止 MineEnergySystem 服务...${NC}"
echo ""

docker compose down

echo ""
echo -e "${GREEN}✅ 所有服务已停止${NC}"
echo ""
echo -e "${YELLOW}💡 提示：${NC}"
echo "   - 数据已保存在 ./pg_data 目录（数据库）"
echo "   - 数据已保存在 Docker volume redis_data（Redis）"
echo "   - 如需完全清理，运行: docker compose down -v"
