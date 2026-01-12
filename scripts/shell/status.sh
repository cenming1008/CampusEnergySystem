#!/bin/bash
# MineEnergySystem 状态查看脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 颜色定义
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  📊 MineEnergySystem 服务状态${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 检查 Docker
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker 未运行${NC}"
    exit 1
fi

# 显示容器状态
echo "🐳 容器状态："
docker compose ps
echo ""

# 显示资源使用
echo "💻 资源使用："
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" \
    mine_backend mine_energy_db ems_redis mine_mqtt 2>/dev/null || echo "  部分容器未运行"
echo ""

# 检查服务健康状态
echo "🏥 健康检查："
SERVICES=("mine_backend:8088" "mine_energy_db:5433" "ems_redis:6379" "mine_mqtt:1883")
SERVICE_NAMES=("后端API" "数据库" "Redis" "MQTT")

for i in "${!SERVICES[@]}"; do
    SERVICE=${SERVICES[$i]}
    NAME=${SERVICE_NAMES[$i]}
    CONTAINER_NAME=$(echo $SERVICE | cut -d: -f1)
    PORT=$(echo $SERVICE | cut -d: -f2)
    
    if docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        if command -v curl &> /dev/null && [ "$CONTAINER_NAME" = "mine_backend" ]; then
            if curl -s http://localhost:$PORT/docs > /dev/null 2>&1; then
                echo -e "   ${GREEN}✅ $NAME${NC} - 运行正常"
            else
                echo -e "   ${YELLOW}⚠️  $NAME${NC} - 容器运行但服务未就绪"
            fi
        else
            echo -e "   ${GREEN}✅ $NAME${NC} - 容器运行中"
        fi
    else
        echo -e "   ${RED}❌ $NAME${NC} - 未运行"
    fi
done

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📝 快速命令："
echo "   查看日志:    docker compose logs -f [服务名]"
echo "   重启服务:    docker compose restart [服务名]"
echo "   停止所有:    ./stop.sh"
echo "   启动所有:    ./start.sh"
