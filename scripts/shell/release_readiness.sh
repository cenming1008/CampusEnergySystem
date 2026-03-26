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

echo "==> 1. Syntax compile"
PYTHONPYCACHEPREFIX=/tmp "$PYTHON_BIN" -m compileall -q app tests scripts/python migrations

echo "==> 2. Runtime config check"
"$PYTHON_BIN" scripts/python/check_config.py

echo "==> 3. Production readiness check"
"$PYTHON_BIN" scripts/python/check_production_readiness.py --env-file env.prod.example

echo "==> 4. Alertmanager channel template validation"
ALERTMANAGER_CHANNEL=webhook \
ALERTMANAGER_WEBHOOK_URL=https://hooks.invalid/prod-channel \
ALERTMANAGER_TARGET_PATH=/tmp/mine_alertmanager_generated.yml \
  sh ./scripts/shell/render_alertmanager_config.sh >/tmp/mine_alertmanager_check.out

echo "==> 5. Unit tests"
"$PYTHON_BIN" -m unittest discover -s tests -p 'test_*.py'

echo "==> 6. Production compose validation"
docker compose -f docker-compose.prod.yml --env-file env.prod.example config >/tmp/mine_compose_config.out

echo "==> Release readiness PASSED"
