#!/bin/bash
# 安装依赖脚本

set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$PROJECT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "🔍 检查 Python 环境..."
"$PYTHON_BIN" --version

"$PYTHON_BIN" - <<'PY'
import sys

if sys.version_info < (3, 10):
    current = f"{sys.version_info.major}.{sys.version_info.minor}"
    raise SystemExit(f"当前 Python {current}，后端最低要求 Python 3.10")
PY

if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    "$PYTHON_BIN" -m venv venv
fi

VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
VENV_PIP="$PROJECT_DIR/venv/bin/pip"

echo "📦 使用虚拟环境: $VENV_PYTHON"

echo "⬆️ 升级 pip..."
"$VENV_PYTHON" -m pip install --upgrade pip

echo "📥 安装依赖..."
"$VENV_PIP" install -r requirements.txt

echo ""
echo "✅ 安装完成！"
echo ""
echo "检查关键包："
"$VENV_PYTHON" -c "import fastapi; print('✓ FastAPI 已安装')" 2>/dev/null || echo "✗ FastAPI 未安装"
"$VENV_PYTHON" -c "import sqlmodel; print('✓ SQLModel 已安装')" 2>/dev/null || echo "✗ SQLModel 未安装"
"$VENV_PYTHON" -c "import dotenv; print('✓ python-dotenv 已安装')" 2>/dev/null || echo "✗ python-dotenv 未安装"

echo ""
echo "💡 提示：下次使用时，先运行: source venv/bin/activate"
