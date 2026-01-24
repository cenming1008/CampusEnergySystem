#!/bin/bash
# 安装依赖脚本

cd "$(dirname "$0")/.."

echo "🔍 检查 Python 环境..."
python3 --version

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

echo "📦 激活虚拟环境..."
source venv/bin/activate

# 检查虚拟环境中的 Python 版本
VENV_PYTHON=$(which python)
echo "虚拟环境 Python: $VENV_PYTHON"

echo "⬆️ 升级 pip..."
python -m pip install --upgrade pip || pip3 install --upgrade pip

echo "📥 安装依赖..."
python -m pip install -r requirements.txt || pip3 install -r requirements.txt

echo ""
echo "✅ 安装完成！"
echo ""
echo "检查关键包："
python3 -c "import fastapi; print('✓ FastAPI 已安装')" 2>/dev/null || echo "✗ FastAPI 未安装"
python3 -c "import sqlmodel; print('✓ SQLModel 已安装')" 2>/dev/null || echo "✗ SQLModel 未安装"
python3 -c "import tensorflow; print('✓ TensorFlow 已安装')" 2>/dev/null || echo "✗ TensorFlow 未安装（可选）"
python3 -c "import sklearn; print('✓ scikit-learn 已安装')" 2>/dev/null || echo "✗ scikit-learn 未安装（可选）"

echo ""
echo "💡 提示：下次使用时，先运行: source venv/bin/activate"
