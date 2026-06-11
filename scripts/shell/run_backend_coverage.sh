#!/bin/bash
# ============================================
# 后端 coverage 门槛统一入口
# ============================================

set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$PROJECT_DIR"

if [ -x "./venv/bin/python" ]; then
  PYTHON_BIN="./venv/bin/python"
else
  PYTHON_BIN="python3"
fi

BACKEND_COVERAGE_FAIL_UNDER="${BACKEND_COVERAGE_FAIL_UNDER:-57}"
BACKEND_COVERAGE_XML="${BACKEND_COVERAGE_XML:-false}"

echo "==> Using Python: $PYTHON_BIN"
echo "==> Backend coverage fail-under: ${BACKEND_COVERAGE_FAIL_UNDER}%"

"$PYTHON_BIN" -m coverage erase
"$PYTHON_BIN" -m coverage run -m pytest -q
"$PYTHON_BIN" -m coverage report --fail-under="$BACKEND_COVERAGE_FAIL_UNDER"

if [ "$BACKEND_COVERAGE_XML" = "true" ]; then
  "$PYTHON_BIN" -m coverage xml
fi
