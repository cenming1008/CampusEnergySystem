#!/bin/bash
# MineEnergySystem 状态查看脚本

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

TARGET_ENV="${1:-auto}"
COMPOSE_LABEL=""
COMPOSE_CMD=(docker compose)
STOP_HINT="./scripts/shell/stop.sh"
START_HINT="./scripts/shell/start.sh"
LOG_HINT="docker compose logs -f [服务名]"
RESTART_HINT="docker compose restart [服务名]"
PS_HINT="docker compose ps"
CONTAINERS=()
SERVICE_SPECS=()

contains_running_container() {
    local pattern="$1"
    docker ps --format '{{.Names}}' | grep -Eq "$pattern"
}

detect_env() {
    if contains_running_container '^mine_.*_prod$|^ems_redis_prod$'; then
        echo "prod"
    elif contains_running_container '^mine_energy_db_dev$|^mine_mqtt_dev$|^ems_redis_dev$'; then
        echo "dev"
    elif contains_running_container '^mine_backend$|^mine_energy_db$|^mine_mqtt$|^ems_redis$'; then
        echo "default"
    else
        echo "default"
    fi
}

container_running() {
    local name="$1"
    docker ps --format '{{.Names}}' | grep -q "^${name}$"
}

container_health() {
    local name="$1"
    docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$name" 2>/dev/null || echo "missing"
}

check_http_service() {
    local name="$1"
    local url="$2"
    if command -v curl >/dev/null 2>&1 && curl -fsS --max-time 3 "$url" >/dev/null 2>&1; then
        echo -e "   ${GREEN}✅ ${name}${NC} - ${url}"
    else
        echo -e "   ${YELLOW}⚠️  ${name}${NC} - ${url} 不可达"
    fi
}

check_container_service() {
    local name="$1"
    local container="$2"

    if ! container_running "$container"; then
        echo -e "   ${RED}❌ ${name}${NC} - 容器未运行 (${container})"
        return
    fi

    local health
    health="$(container_health "$container")"
    case "$health" in
        healthy)
            echo -e "   ${GREEN}✅ ${name}${NC} - healthy (${container})"
            ;;
        starting)
            echo -e "   ${YELLOW}⚠️  ${name}${NC} - starting (${container})"
            ;;
        unhealthy)
            echo -e "   ${RED}❌ ${name}${NC} - unhealthy (${container})"
            ;;
        none)
            echo -e "   ${GREEN}✅ ${name}${NC} - 容器运行中 (${container})"
            ;;
        *)
            echo -e "   ${YELLOW}⚠️  ${name}${NC} - 状态未知 (${container})"
            ;;
    esac
}

configure_env() {
    local selected="$1"
    case "$selected" in
        default)
            COMPOSE_LABEL="default"
            CONTAINERS=(mine_backend mine_energy_db ems_redis mine_mqtt)
            SERVICE_SPECS=(
                "后端API|container|mine_backend"
                "数据库|container|mine_energy_db"
                "Redis|container|ems_redis"
                "MQTT|container|mine_mqtt"
                "后端健康检查|http|http://localhost:8088/health/live"
            )
            ;;
        dev)
            COMPOSE_LABEL="dev"
            COMPOSE_CMD=(docker compose -f docker-compose.dev.yml)
            STOP_HINT="./scripts/shell/stop_dev_env.sh"
            START_HINT="./scripts/shell/start_dev_env.sh"
            LOG_HINT="docker compose -f docker-compose.dev.yml logs -f [服务名]"
            RESTART_HINT="docker compose -f docker-compose.dev.yml restart [服务名]"
            PS_HINT="docker compose -f docker-compose.dev.yml ps"
            CONTAINERS=(mine_energy_db_dev ems_redis_dev mine_mqtt_dev)
            SERVICE_SPECS=(
                "数据库|container|mine_energy_db_dev"
                "Redis|container|ems_redis_dev"
                "MQTT|container|mine_mqtt_dev"
                "本地后端健康检查|http|http://localhost:8088/health/live"
            )
            ;;
        prod)
            COMPOSE_LABEL="prod"
            COMPOSE_CMD=(docker compose -f docker-compose.prod.yml)
            LOG_HINT="docker compose -f docker-compose.prod.yml logs -f [服务名]"
            RESTART_HINT="docker compose -f docker-compose.prod.yml restart [服务名]"
            PS_HINT="docker compose -f docker-compose.prod.yml ps"
            CONTAINERS=(mine_backend_prod mine_energy_db_prod ems_redis_prod mine_mqtt_prod mine_nginx_prod mine_prometheus_prod mine_alertmanager_prod)
            SERVICE_SPECS=(
                "生产后端|container|mine_backend_prod"
                "生产数据库|container|mine_energy_db_prod"
                "生产Redis|container|ems_redis_prod"
                "生产MQTT|container|mine_mqtt_prod"
                "生产Nginx|container|mine_nginx_prod"
                "生产Prometheus|container|mine_prometheus_prod"
                "生产Alertmanager|container|mine_alertmanager_prod"
            )
            ;;
        *)
            echo -e "${RED}❌ 不支持的环境: ${selected}${NC}"
            echo "用法: ./scripts/shell/status.sh [auto|default|dev|prod]"
            exit 1
            ;;
    esac
}

if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未运行${NC}"
    exit 1
fi

if [ "$TARGET_ENV" = "auto" ]; then
    TARGET_ENV="$(detect_env)"
fi

configure_env "$TARGET_ENV"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  MineEnergySystem 服务状态 (${COMPOSE_LABEL})${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "🐳 容器状态："
"${COMPOSE_CMD[@]}" ps || true
echo ""

echo "💻 资源使用："
RUNNING_CONTAINERS=()
for container in "${CONTAINERS[@]}"; do
    if container_running "$container"; then
        RUNNING_CONTAINERS+=("$container")
    fi
done

if [ "${#RUNNING_CONTAINERS[@]}" -gt 0 ]; then
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" "${RUNNING_CONTAINERS[@]}"
else
    echo "  当前环境没有检测到运行中的目标容器"
fi
echo ""

echo "🏥 健康检查："
for spec in "${SERVICE_SPECS[@]}"; do
    IFS='|' read -r service_name service_kind service_target <<<"$spec"
    if [ "$service_kind" = "http" ]; then
        check_http_service "$service_name" "$service_target"
    else
        check_container_service "$service_name" "$service_target"
    fi
done

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "📝 快速命令："
echo "   查看状态:    ${PS_HINT}"
echo "   查看日志:    ${LOG_HINT}"
echo "   重启服务:    ${RESTART_HINT}"
echo "   停止环境:    ${STOP_HINT}"
echo "   启动环境:    ${START_HINT}"
