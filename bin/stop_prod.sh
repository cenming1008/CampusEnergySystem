#!/bin/bash
# 生产环境快捷停止入口。
# 只停止 docker-compose.prod.yml 中的生产服务，不删除数据库卷或挂载数据目录。

set -e

PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJECT_DIR"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  园区综合能源管理系统生产停止${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if ! command -v docker >/dev/null 2>&1; then
    echo -e "${RED}Docker 未安装，无法停止生产服务${NC}"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}Docker 未运行，无法停止生产服务${NC}"
    exit 1
fi

COMPOSE_ENV_ARGS=(--env-file .env.prod)
if [ ! -f ".env.prod" ]; then
    if [ -f "env.prod.example" ]; then
        echo -e "${YELLOW}未找到 .env.prod，将使用 env.prod.example 解析 Compose 并停止生产服务${NC}"
        COMPOSE_ENV_ARGS=(--env-file env.prod.example)
    else
        echo -e "${YELLOW}未找到 .env.prod 或 env.prod.example，将直接按 docker-compose.prod.yml 停止生产服务${NC}"
        COMPOSE_ENV_ARGS=()
    fi
fi

echo -e "${YELLOW}停止生产服务...${NC}"
docker compose -f docker-compose.prod.yml "${COMPOSE_ENV_ARGS[@]}" down

echo ""
echo -e "${GREEN}生产服务已停止${NC}"
echo -e "${YELLOW}提示：数据库、Mosquitto、日志、备份等挂载数据不会被删除。${NC}"
