#!/bin/bash
# 生产环境快捷启动入口。
# Compose 已收敛为 docker-compose.dev.yml / docker-compose.prod.yml 两套；
# 本脚本只负责用 docker-compose.prod.yml 启动生产服务。

set -e

PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJECT_DIR"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  园区综合能源管理系统生产快速启动${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if ! command -v docker >/dev/null 2>&1; then
    echo -e "${RED}Docker 未安装，请先安装 Docker Desktop 或 Docker Engine${NC}"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi

if [ ! -f ".env.prod" ]; then
    echo -e "${RED}未找到 .env.prod${NC}"
    echo -e "${YELLOW}请先执行: cp env.prod.example .env.prod，并修改其中的密码、密钥和域名配置${NC}"
    exit 1
fi

mkdir -p logs backups pg_data mosquitto/config mosquitto/data mosquitto/log nginx/ssl nginx/log

if [ ! -f "mosquitto/config/passwd" ]; then
    echo -e "${YELLOW}未发现 Mosquitto 密码文件，正在根据 .env.prod 生成...${NC}"
    MQTT_USERNAME_FROM_ENV=$(grep -E '^MQTT_USERNAME=' .env.prod | tail -1 | cut -d '=' -f2- || true)
    MQTT_PASSWORD_FROM_ENV=$(grep -E '^MQTT_PASSWORD=' .env.prod | tail -1 | cut -d '=' -f2- || true)
    MQTT_USERNAME_FROM_ENV="${MQTT_USERNAME_FROM_ENV:-campus_mqtt}"
    if [ -z "$MQTT_PASSWORD_FROM_ENV" ]; then
        echo -e "${RED}.env.prod 中缺少 MQTT_PASSWORD，无法生成 Mosquitto 密码文件${NC}"
        exit 1
    fi
    bash ./scripts/shell/setup_mqtt_auth.sh "$MQTT_USERNAME_FROM_ENV" "$MQTT_PASSWORD_FROM_ENV" --force
fi

echo -e "${YELLOW}启动生产服务...${NC}"
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

echo ""
echo -e "${GREEN}生产服务启动命令已执行${NC}"
echo ""
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
echo ""
