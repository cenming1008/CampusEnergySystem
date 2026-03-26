#!/bin/bash
# ============================================
# 发布前检查脚本
# ============================================

set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$PROJECT_DIR"

if [ -x "./venv/bin/python" ]; then
  PYTHON_BIN="./venv/bin/python"
else
  PYTHON_BIN="python3"
fi

echo "==> Using Python: $PYTHON_BIN"

TEMP_PROD_ENV="$(mktemp /tmp/mine_env_prod_readiness.XXXXXX)"
trap 'rm -f "$TEMP_PROD_ENV" /tmp/mine_alertmanager_generated.yml /tmp/mine_alertmanager_check.out /tmp/mine_compose_config.out' EXIT

cat env.prod.example >"$TEMP_PROD_ENV"
cat >>"$TEMP_PROD_ENV" <<'EOF'
DB_PASSWORD=Readiness_DbPass_24Chars!
REDIS_PASSWORD=Readiness_RedisPass_24!
SECRET_KEY=ReadinessKey_7qL2mP9rT4vX8sD1nH6jK3cW5zB0yFa
GRAFANA_ADMIN_PASSWORD=Readiness_GrafanaPass_24!
MQTT_PASSWORD=Readiness_MqttPass_24Chars!
ALERTMANAGER_WEBHOOK_URL=https://alerts.mine-energy.local/webhook
EOF
chmod 600 "$TEMP_PROD_ENV"

echo "==> 1. Syntax compile"
PYTHONPYCACHEPREFIX=/tmp "$PYTHON_BIN" -m compileall -q app tests scripts/python migrations

echo "==> 2. Runtime config check"
"$PYTHON_BIN" scripts/python/check_config.py

echo "==> 3. Production readiness check"
"$PYTHON_BIN" scripts/python/check_production_readiness.py --env-file "$TEMP_PROD_ENV"

echo "==> 4. Alertmanager channel template validation"
ALERTMANAGER_CHANNEL=webhook \
ALERTMANAGER_WEBHOOK_URL=https://alerts.mine-energy.local/prod-channel \
ALERTMANAGER_TARGET_PATH=/tmp/mine_alertmanager_generated.yml \
  sh ./scripts/shell/render_alertmanager_config.sh >/tmp/mine_alertmanager_check.out

echo "==> 5. Unit tests"
"$PYTHON_BIN" -m unittest discover -s tests -p 'test_*.py'

echo "==> 6. Production compose validation"
docker compose -f docker-compose.prod.yml --env-file "$TEMP_PROD_ENV" config >/tmp/mine_compose_config.out

echo "==> Release readiness PASSED"
