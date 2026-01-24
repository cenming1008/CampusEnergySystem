#!/bin/bash
# ============================================
# 生产环境部署脚本
# ============================================
# 使用方法：
# chmod +x scripts/shell/deploy_prod.sh
# ./scripts/shell/deploy_prod.sh
# ============================================

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"
PROJECT_DIR=$(cd "$(dirname "$0")/../.." && pwd)

echo -e "${GREEN}🚀 开始生产环境部署...${NC}"
echo "项目目录: $PROJECT_DIR"
cd "$PROJECT_DIR"

# 1. 检查环境文件
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ 错误: 未找到 $ENV_FILE 文件${NC}"
    echo "请先复制 env.prod.example 为 .env.prod 并修改配置"
    exit 1
fi

# 2. 检查必要配置
echo -e "${YELLOW}📋 检查配置...${NC}"
source "$ENV_FILE"

if [ "$DB_PASSWORD" = "your-strong-database-password-change-me-min-16-chars" ]; then
    echo -e "${RED}❌ 错误: 请修改 .env.prod 中的 DB_PASSWORD${NC}"
    exit 1
fi

if [ "$SECRET_KEY" = "your-super-secret-jwt-key-min-32-chars-change-me-immediately" ]; then
    echo -e "${RED}❌ 错误: 请修改 .env.prod 中的 SECRET_KEY${NC}"
    exit 1
fi

# 3. 拉取最新代码（如果使用Git）
if [ -d ".git" ]; then
    echo -e "${YELLOW}📥 拉取最新代码...${NC}"
    git pull origin main || echo "⚠️  Git拉取失败，继续使用当前代码"
fi

# 4. 创建必要目录
echo -e "${YELLOW}📁 创建目录...${NC}"
mkdir -p logs backups pg_data mosquitto/{config,data,log}

# 5. 构建镜像
echo -e "${YELLOW}🔨 构建Docker镜像...${NC}"
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache

# 6. 停止旧服务
echo -e "${YELLOW}🛑 停止旧服务...${NC}"
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down

# 7. 启动新服务
echo -e "${YELLOW}▶️  启动服务...${NC}"
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

# 8. 等待服务就绪
echo -e "${YELLOW}⏳ 等待服务启动（30秒）...${NC}"
sleep 30

# 9. 健康检查
echo -e "${YELLOW}🏥 健康检查...${NC}"
max_attempts=10
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -f -s http://localhost:8088/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 服务健康检查通过${NC}"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "  尝试 $attempt/$max_attempts..."
    sleep 5
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ 健康检查失败，请查看日志:${NC}"
    echo "docker-compose -f $COMPOSE_FILE logs backend"
    exit 1
fi

# 10. 显示服务状态
echo -e "${GREEN}📊 服务状态:${NC}"
docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps

echo ""
echo -e "${GREEN}✅ 部署完成！${NC}"
echo ""
echo "访问地址:"
echo "  - API文档: http://localhost:8088/docs"
echo "  - 健康检查: http://localhost:8088/health"
echo ""
echo "查看日志:"
echo "  docker-compose -f $COMPOSE_FILE logs -f"
