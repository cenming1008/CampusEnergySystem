#!/bin/bash
# Mac 环境检查脚本
# 用于验证园区综合能源管理系统在 Mac 上的运行环境

echo "🔍 检查 Mac 运行环境..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查结果统计
PASSED=0
FAILED=0
WARNINGS=0

# 检查函数
check_item() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ $1${NC}"
        ((FAILED++))
        return 1
    fi
}

warn_item() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

# 1. 检查操作系统
echo "📱 系统信息："
echo "   macOS 版本: $(sw_vers -productVersion)"
echo "   架构: $(uname -m)"
echo ""

# 2. 检查 Docker
echo "🐳 Docker 环境："
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "   $DOCKER_VERSION"
    check_item "Docker 已安装"
    
    # 检查 Docker 是否运行
    if docker info &> /dev/null; then
        check_item "Docker 正在运行"
    else
        warn_item "Docker 未运行，请打开 Docker Desktop"
    fi
    
    # 检查 Docker Compose
    if docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version)
        echo "   $COMPOSE_VERSION"
        check_item "Docker Compose 已安装"
    else
        warn_item "Docker Compose 未找到"
    fi
else
    warn_item "Docker 未安装，请从 https://www.docker.com/products/docker-desktop/ 下载安装"
fi
echo ""

# 3. 检查端口占用
echo "🔌 端口检查："
PORTS=(8088 5433 6379 1883)
PORT_NAMES=("后端(8088)" "数据库(5433)" "Redis(6379)" "MQTT(1883)")

for i in "${!PORTS[@]}"; do
    PORT=${PORTS[$i]}
    NAME=${PORT_NAMES[$i]}
    if lsof -i :$PORT &> /dev/null; then
        PROCESS=$(lsof -i :$PORT | tail -n 1 | awk '{print $1}')
        warn_item "$NAME 端口被占用 (进程: $PROCESS)"
    else
        check_item "$NAME 端口可用"
    fi
done
echo ""

# 4. 检查项目文件
echo "📁 项目文件："
if [ -f ".env" ]; then
    check_item ".env 文件存在"
else
    warn_item ".env 文件不存在，请运行: cp env.example .env"
fi

if [ -f "docker-compose.yml" ]; then
    check_item "docker-compose.yml 存在"
fi

if [ -f "requirements.txt" ]; then
    check_item "requirements.txt 存在"
fi

# 检查必要目录
DIRS=("mosquitto/data" "mosquitto/log" "logs" "pg_data")
for DIR in "${DIRS[@]}"; do
    if [ -d "$DIR" ]; then
        check_item "目录 $DIR 存在"
    else
        warn_item "目录 $DIR 不存在，将自动创建"
        mkdir -p "$DIR" 2>/dev/null
    fi
done
echo ""

# 5. 检查文件权限
echo "🔐 文件权限："
if [ -w "logs" ] 2>/dev/null; then
    check_item "logs 目录可写"
else
    warn_item "logs 目录不可写，运行: chmod -R 755 logs/"
fi

if [ -w "mosquitto" ] 2>/dev/null; then
    check_item "mosquitto 目录可写"
else
    warn_item "mosquitto 目录不可写，运行: chmod -R 755 mosquitto/"
fi
echo ""

# 6. 检查 Python（可选，如果不用 Docker）
echo "🐍 Python 环境（可选）："
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   $PYTHON_VERSION"
    check_item "Python3 已安装"
    
    if [ -d "venv" ]; then
        check_item "虚拟环境 venv 存在"
    else
        warn_item "虚拟环境不存在（如果使用 Docker 可忽略）"
    fi
else
    warn_item "Python3 未安装（如果使用 Docker 可忽略）"
fi
echo ""

# 7. 检查 Node.js（前端开发需要）
echo "📦 Node.js 环境（前端开发需要）："
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "   Node.js: $NODE_VERSION"
    check_item "Node.js 已安装"
    
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        echo "   npm: $NPM_VERSION"
        check_item "npm 已安装"
    fi
else
    warn_item "Node.js 未安装（前端开发需要，从 https://nodejs.org/ 下载）"
fi
echo ""

# 8. 检查 Docker 容器状态（如果 Docker 正在运行）
if docker info &> /dev/null; then
    echo "📦 Docker 容器状态："
    if docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -q "campus_energy_db\|campus_mqtt\|campus_redis\|campus_backend"; then
        docker ps -a --format "table {{.Names}}\t{{.Status}}" | grep -E "campus_energy_db|campus_mqtt|campus_redis|campus_backend"
        echo ""
        echo "   运行 'docker compose ps' 查看详细状态"
    else
        warn_item "未找到项目容器，运行 'docker compose up -d' 启动服务"
    fi
    echo ""
fi

# 总结
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 检查总结："
echo -e "   ${GREEN}✅ 通过: $PASSED${NC}"
echo -e "   ${RED}❌ 失败: $FAILED${NC}"
echo -e "   ${YELLOW}⚠️  警告: $WARNINGS${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✨ 环境检查完成！可以尝试启动服务：${NC}"
    echo "   docker compose up -d --build"
else
    echo -e "${RED}❌ 发现 $FAILED 个问题，请先解决后再启动服务${NC}"
fi

echo ""
echo "📚 详细配置指南请查看: MAC_SETUP_GUIDE.md"
