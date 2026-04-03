#!/bin/bash
# 后端容器重启脚本（Mac 适配版）

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🔄 重启后端容器..."
docker compose restart backend
echo "🔄 重启 MQTT 采集 worker..."
docker compose restart mqtt_ingest_worker

echo "✅ 后端容器与 MQTT 采集 worker 已重启"
echo "📊 查看日志: docker compose logs -f backend"
