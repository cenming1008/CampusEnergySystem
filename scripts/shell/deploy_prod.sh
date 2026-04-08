#!/bin/bash
# ============================================
# 生产环境部署脚本
# ============================================
# 使用方法：
# chmod +x scripts/shell/deploy_prod.sh
# ./scripts/shell/deploy_prod.sh
# ============================================

set -euo pipefail

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

# 2. 收紧 .env.prod 文件权限
chmod 600 "$ENV_FILE" 2>/dev/null || true

# 3. 检查必要配置
echo -e "${YELLOW}📋 检查配置...${NC}"

DB_PASSWORD=$(grep -E '^DB_PASSWORD=' "$ENV_FILE" | tail -1 | cut -d '=' -f2- || true)
SECRET_KEY=$(grep -E '^SECRET_KEY=' "$ENV_FILE" | tail -1 | cut -d '=' -f2- || true)
MQTT_PASSWORD=$(grep -E '^MQTT_PASSWORD=' "$ENV_FILE" | tail -1 | cut -d '=' -f2- || true)
ALERTMANAGER_WEBHOOK_URL=$(grep -E '^ALERTMANAGER_WEBHOOK_URL=' "$ENV_FILE" | tail -1 | cut -d '=' -f2- || true)

if [[ -z "$DB_PASSWORD" || "$DB_PASSWORD" == *"change-me"* || "$DB_PASSWORD" == *"ChangeThis"* ]]; then
    echo -e "${RED}❌ 错误: 请修改 .env.prod 中的 DB_PASSWORD${NC}"
    exit 1
fi

if [[ -z "$SECRET_KEY" || "$SECRET_KEY" == *"change-me"* || "$SECRET_KEY" == *"ChangeThis"* ]]; then
    echo -e "${RED}❌ 错误: 请修改 .env.prod 中的 SECRET_KEY${NC}"
    exit 1
fi

if [[ -z "$MQTT_PASSWORD" || "$MQTT_PASSWORD" == *"change-me"* || "$MQTT_PASSWORD" == *"ChangeThis"* ]]; then
    echo -e "${RED}❌ 错误: 请修改 .env.prod 中的 MQTT_PASSWORD${NC}"
    exit 1
fi

if [[ -n "$ALERTMANAGER_WEBHOOK_URL" && "$ALERTMANAGER_WEBHOOK_URL" == *".invalid"* ]]; then
    echo -e "${RED}❌ 错误: 请修改 .env.prod 中的 ALERTMANAGER_WEBHOOK_URL${NC}"
    exit 1
fi

ENV_MODE=$(stat -f '%A' "$ENV_FILE" 2>/dev/null || stat -c '%a' "$ENV_FILE" 2>/dev/null || echo "600")
if [ "$ENV_MODE" != "600" ]; then
    echo -e "${YELLOW}⚠️  提醒: $ENV_FILE 当前权限为 $ENV_MODE，建议收紧为 600${NC}"
fi

# 3. 拉取最新代码（如果使用Git）
if [ -d ".git" ]; then
    echo -e "${YELLOW}📥 拉取最新代码...${NC}"
    git pull origin main || echo "⚠️  Git拉取失败，继续使用当前代码"
fi

# 4. 创建必要目录
echo -e "${YELLOW}📁 创建目录...${NC}"
mkdir -p logs backups pg_data mosquitto/{config,data,log} nginx/{ssl,log}

# 4.1 发布前检查
echo -e "${YELLOW}🧪 执行发布前检查...${NC}"
bash ./scripts/shell/release_readiness.sh
python3 ./scripts/python/check_production_readiness.py --env-file "$ENV_FILE"

# 4.2 部署前备份
if docker ps --format '{{.Names}}' | grep -q "^campus_energy_db_prod$"; then
    echo -e "${YELLOW}💾 创建部署前备份...${NC}"
    bash ./scripts/shell/backup.sh --label pre_deploy
fi

# 5. 构建后端镜像
echo -e "${YELLOW}🔨 构建后端镜像...${NC}"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache backend

# 6. 滚动更新（仅重建 backend 和 nginx，不停止基础设施服务）
echo -e "${YELLOW}▶️  滚动更新 backend + nginx...${NC}"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --no-deps --remove-orphans backend
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --no-deps nginx

# 8. 等待服务就绪
echo -e "${YELLOW}⏳ 等待服务启动（30秒）...${NC}"
sleep 30

# 9. 健康检查
echo -e "${YELLOW}🏥 健康检查...${NC}"
max_attempts=10
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -f -s http://localhost/health/live > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 服务健康检查通过${NC}"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "  尝试 $attempt/$max_attempts..."
    sleep 5
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ 健康检查失败，请查看日志:${NC}"
    echo "docker compose -f $COMPOSE_FILE logs backend"
    echo "如需回滚，可执行: bash ./scripts/shell/rollback_prod.sh backups/latest_pre_deploy.dump"
    exit 1
fi

# 10. 显示服务状态
echo -e "${GREEN}📊 服务状态:${NC}"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps

echo ""
echo -e "${GREEN}✅ 部署完成！${NC}"
echo ""
echo "访问地址:"
echo "  - API文档: https://localhost/docs"
echo "  - 健康检查: http://localhost/health/live"
echo ""
echo "查看日志:"
echo "  docker compose -f $COMPOSE_FILE logs -f"
