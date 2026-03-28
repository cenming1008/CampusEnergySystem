#!/bin/bash
# 园区综合能源管理系统一键启动脚本（Mac/Linux 通用）
# 使用 Docker Compose 启动所有服务

set -e  # 遇到错误立即退出

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🚀 园区综合能源管理系统启动脚本${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    echo ""
    echo -e "${YELLOW}📦 请先安装 Docker Desktop：${NC}"
    echo "   1. 访问: https://www.docker.com/products/docker-desktop/"
    echo "   2. 或查看详细安装指南: cat INSTALL_DOCKER_MAC.md"
    echo "   3. 或使用 Homebrew: brew install --cask docker"
    echo ""
    echo -e "${BLUE}💡 安装完成后，运行此脚本即可启动项目${NC}"
    exit 1
fi

# 检查 Docker 是否运行
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker 未运行${NC}"
    echo ""
    echo -e "${YELLOW}🚀 请启动 Docker Desktop：${NC}"
    echo "   1. 打开 Applications 文件夹"
    echo "   2. 双击 Docker 图标启动"
    echo "   3. 等待菜单栏图标不再闪烁（约 1-2 分钟）"
    echo "   4. 然后再次运行此脚本"
    echo ""
    echo -e "${BLUE}💡 或使用命令启动: open /Applications/Docker.app${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker 环境检查通过${NC}"
echo ""

# 检查必要目录
echo "📁 检查项目目录..."
mkdir -p mosquitto/data mosquitto/log logs pg_data
chmod -R 755 mosquitto logs 2>/dev/null || true
echo -e "${GREEN}✅ 目录检查完成${NC}"
echo ""

# 检查端口占用（可选，仅提示）
echo "🔌 检查端口占用..."
PORTS=(8088 5433 6379 1883)
PORT_NAMES=("后端(8088)" "数据库(5433)" "Redis(6379)" "MQTT(1883)")
WARNED=false

for i in "${!PORTS[@]}"; do
    PORT=${PORTS[$i]}
    NAME=${PORT_NAMES[$i]}
    if command -v lsof &> /dev/null; then
        if lsof -i :$PORT &> /dev/null; then
            PROCESS=$(lsof -i :$PORT 2>/dev/null | tail -n 1 | awk '{print $1}' || echo "未知")
            echo -e "${YELLOW}⚠️  $NAME 端口可能被占用 (进程: $PROCESS)${NC}"
            WARNED=true
        fi
    fi
done

if [ "$WARNED" = false ]; then
    echo -e "${GREEN}✅ 端口检查通过${NC}"
fi
echo ""

# 启动服务
echo -e "${BLUE}🐳 启动 Docker 服务...${NC}"
echo ""

# 构建并启动（首次启动会构建镜像）
docker compose up -d --build

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 服务启动完成！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 等待服务就绪
echo "⏳ 等待服务就绪..."
sleep 5

# 检查服务状态
echo ""
echo "📊 服务状态："
docker compose ps

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📚 访问地址：${NC}"
echo -e "   ${GREEN}后端 API 文档:${NC} http://localhost:8088/docs"
echo -e "   ${GREEN}后端 ReDoc:${NC}    http://localhost:8088/redoc"
echo ""
echo -e "${BLUE}📝 常用命令：${NC}"
echo -e "   查看日志:    ${YELLOW}docker compose logs -f${NC}"
echo -e "   查看后端日志: ${YELLOW}docker compose logs -f backend${NC}"
echo -e "   停止服务:    ${YELLOW}docker compose down${NC}"
echo -e "   重启服务:    ${YELLOW}docker compose restart${NC}"
echo -e "   查看状态:    ${YELLOW}docker compose ps${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 显示实时日志（可选）
read -p "是否查看实时日志？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "📋 实时日志（按 Ctrl+C 退出）："
    echo ""
    docker compose logs -f
fi
