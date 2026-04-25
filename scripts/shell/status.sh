#!/bin/bash
# 园区综合能源管理系统状态查看脚本

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
COMPOSE_CMD=(docker compose -f docker-compose.dev.yml)
STOP_HINT="./bin/stop_dev.sh"
START_HINT="./bin/fast_start_dev.sh"
LOG_HINT="docker compose -f docker-compose.dev.yml logs -f [服务名]"
RESTART_HINT="docker compose -f docker-compose.dev.yml restart [服务名]"
PS_HINT="docker compose -f docker-compose.dev.yml ps"
declare -a CONTAINERS=()
declare -a SERVICE_SPECS=()

contains_running_container() {
    local pattern="$1"
    docker ps --format '{{.Names}}' | grep -Eq "$pattern"
}

compose_service_container() {
    local compose_file="$1"
    local service="$2"
    docker compose -f "$compose_file" ps -q "$service" 2>/dev/null | head -n 1
}

detect_env() {
    if contains_running_container '^campus_.*_prod$'; then
        echo "prod"
    elif [ -n "$(compose_service_container docker-compose.dev.yml db)" ] \
      || [ -n "$(compose_service_container docker-compose.dev.yml mqtt)" ] \
      || [ -n "$(compose_service_container docker-compose.dev.yml redis)" ]; then
        echo "dev"
    else
        echo "dev"
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

check_compose_service() {
    local name="$1"
    local compose_file="$2"
    local service="$3"
    local container
    container="$(compose_service_container "$compose_file" "$service")"

    if [ -z "$container" ]; then
        echo -e "   ${RED}❌ ${name}${NC} - 服务未运行 (${service})"
        return
    fi

    local health
    health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container" 2>/dev/null || echo "missing")"
    case "$health" in
        healthy)
            echo -e "   ${GREEN}✅ ${name}${NC} - healthy (${service})"
            ;;
        starting)
            echo -e "   ${YELLOW}⚠️  ${name}${NC} - starting (${service})"
            ;;
        unhealthy)
            echo -e "   ${RED}❌ ${name}${NC} - unhealthy (${service})"
            ;;
        none)
            echo -e "   ${GREEN}✅ ${name}${NC} - 运行中 (${service})"
            ;;
        *)
            echo -e "   ${YELLOW}⚠️  ${name}${NC} - 状态未知 (${service})"
            ;;
    esac
}

configure_env() {
    local selected="$1"
    case "$selected" in
        dev)
            COMPOSE_LABEL="dev"
            COMPOSE_CMD=(docker compose -f docker-compose.dev.yml)
            STOP_HINT="./bin/stop_dev.sh"
            START_HINT="./bin/fast_start_dev.sh"
            LOG_HINT="docker compose -f docker-compose.dev.yml logs -f [服务名]"
            RESTART_HINT="docker compose -f docker-compose.dev.yml restart [服务名]"
            PS_HINT="docker compose -f docker-compose.dev.yml ps"
            CONTAINERS=()
            SERVICE_SPECS=(
                "数据库|compose|db"
                "Redis|compose|redis"
                "MQTT|compose|mqtt"
                "本地后端健康检查|http|http://localhost:8088/health/live"
            )
            ;;
        prod)
            COMPOSE_LABEL="prod"
            COMPOSE_CMD=(docker compose -f docker-compose.prod.yml --env-file .env.prod)
            STOP_HINT="./bin/stop_prod.sh"
            START_HINT="./bin/fast_start.sh"
            LOG_HINT="docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f [服务名]"
            RESTART_HINT="docker compose -f docker-compose.prod.yml --env-file .env.prod restart [服务名]"
            PS_HINT="docker compose -f docker-compose.prod.yml --env-file .env.prod ps"
            CONTAINERS=(campus_backend_prod campus_mqtt_ingest_worker_prod campus_energy_db_prod campus_redis_prod campus_mqtt_prod campus_nginx_prod campus_prometheus_prod campus_alertmanager_prod)
            SERVICE_SPECS=(
                "生产后端|container|campus_backend_prod"
                "生产 MQTT ingest worker|container|campus_mqtt_ingest_worker_prod"
                "生产数据库|container|campus_energy_db_prod"
                "生产Redis|container|campus_redis_prod"
                "生产MQTT|container|campus_mqtt_prod"
                "生产Nginx|container|campus_nginx_prod"
                "生产Prometheus|container|campus_prometheus_prod"
                "生产Alertmanager|container|campus_alertmanager_prod"
            )
            ;;
        *)
            echo -e "${RED}❌ 不支持的环境: ${selected}${NC}"
            echo "用法: ./scripts/shell/status.sh [auto|dev|prod]"
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
echo -e "${BLUE}  园区综合能源管理系统服务状态 (${COMPOSE_LABEL})${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "提示：Compose 已收敛为 dev/prod 两套；开发环境只包含 db/redis/mqtt。"
echo ""

echo "🐳 容器状态："
"${COMPOSE_CMD[@]}" ps || true
echo ""

echo "💻 资源使用："
declare -a RUNNING_CONTAINERS=()
if declare -p CONTAINERS >/dev/null 2>&1 && [ "${#CONTAINERS[@]}" -gt 0 ]; then
    for container in "${CONTAINERS[@]}"; do
        if container_running "$container"; then
            RUNNING_CONTAINERS+=("$container")
        fi
    done
fi

if [ "${#RUNNING_CONTAINERS[@]}" -gt 0 ]; then
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" "${RUNNING_CONTAINERS[@]}"
elif [ "$COMPOSE_LABEL" = "dev" ]; then
    declare -a DEV_RUNNING_CONTAINERS=()
    for service in db redis mqtt; do
        container="$(compose_service_container docker-compose.dev.yml "$service")"
        if [ -n "$container" ]; then
            DEV_RUNNING_CONTAINERS+=("$container")
        fi
    done
    if [ "${#DEV_RUNNING_CONTAINERS[@]}" -gt 0 ]; then
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" "${DEV_RUNNING_CONTAINERS[@]}"
    else
        echo "  当前环境没有检测到运行中的目标容器"
    fi
else
    echo "  当前环境没有检测到运行中的目标容器"
fi
echo ""

echo "🏥 健康检查："
for spec in "${SERVICE_SPECS[@]}"; do
    IFS='|' read -r service_name service_kind service_target <<<"$spec"
    if [ "$service_kind" = "http" ]; then
        check_http_service "$service_name" "$service_target"
    elif [ "$service_kind" = "compose" ]; then
        check_compose_service "$service_name" "docker-compose.dev.yml" "$service_target"
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
