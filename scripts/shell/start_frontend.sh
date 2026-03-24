#!/bin/bash
# 前端开发服务器启动脚本

set -e

# 获取脚本所在目录，并得到项目根目录（scripts/shell 的上级的上级）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
cd "$PROJECT_ROOT"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🚀 前端开发服务器启动脚本${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js 未安装${NC}"
    echo ""
    echo -e "${YELLOW}📦 请先安装 Node.js：${NC}"
    echo "   访问: https://nodejs.org/"
    echo "   或使用 Homebrew: brew install node"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✅ Node.js 已安装: $NODE_VERSION${NC}"
echo ""

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm 未安装${NC}"
    exit 1
fi

NPM_VERSION=$(npm --version)
echo -e "${GREEN}✅ npm 已安装: $NPM_VERSION${NC}"
echo ""

# 进入前端目录
cd frontend

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 首次运行，正在安装依赖...${NC}"
    npm install
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
    echo ""
fi

# 检查端口占用
echo "🔌 检查端口占用..."
if lsof -i :3000 &> /dev/null; then
    PROCESS=$(lsof -i :3000 | tail -n 1 | awk '{print $1}')
    PID=$(lsof -i :3000 | tail -n 1 | awk '{print $2}')
    echo -e "${YELLOW}⚠️  端口 3000 已被占用 (进程: $PROCESS, PID: $PID)${NC}"
    echo ""
    read -p "是否要终止该进程并继续？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill -9 $PID 2>/dev/null || true
        sleep 1
        echo -e "${GREEN}✅ 进程已终止${NC}"
    else
        echo -e "${YELLOW}💡 你可以手动终止进程或使用其他端口${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ 端口 3000 可用${NC}"
fi
echo ""

# 检查后端服务
echo "🔍 检查后端服务..."
if curl -s -f http://localhost:8088/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 后端服务正在运行 (http://localhost:8088)${NC}"
else
    echo -e "${YELLOW}⚠️  后端服务未运行${NC}"
    echo -e "${YELLOW}💡 请先启动后端服务: cd .. && ./start.sh${NC}"
    echo ""
    read -p "是否继续启动前端？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# 启动前端开发服务器
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 启动前端开发服务器...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}📚 访问地址：${NC}"
echo -e "   ${GREEN}前端界面:${NC} http://localhost:3000"
echo -e "   ${GREEN}前端界面:${NC} http://127.0.0.1:3000"
echo ""
echo -e "${BLUE}💡 提示：${NC}"
echo -e "   按 ${YELLOW}Ctrl+C${NC} 停止服务器"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 启动 Vite 开发服务器
npm run dev
