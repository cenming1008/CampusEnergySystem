#!/bin/bash
# 修复虚拟环境脚本
# 虚拟环境的脚本包含绝对路径，如果项目移动了位置就会失效

cd "$(dirname "$0")/../.."

echo "🔍 检查当前虚拟环境..."
if [ -d "venv" ]; then
    echo "发现虚拟环境，但可能路径不正确"
    echo "虚拟环境中的 pip 路径："
    head -1 venv/bin/pip 2>/dev/null || echo "无法读取"
fi

echo ""
echo "📦 重新创建虚拟环境..."
echo "这将删除旧的虚拟环境并创建新的"

read -p "是否继续？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 1
fi

# 备份旧虚拟环境（可选）
if [ -d "venv" ]; then
    echo "备份旧虚拟环境..."
    mv venv venv.backup.$(date +%Y%m%d_%H%M%S)
fi

# 创建新虚拟环境
echo "创建新虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo "升级 pip..."
python -m pip install --upgrade pip

# 安装依赖
echo "安装依赖..."
python -m pip install -r requirements.txt

echo ""
echo "✅ 虚拟环境修复完成！"
echo ""
echo "验证安装："
python --version
python -m pip --version

echo ""
echo "💡 下次使用时，运行: source venv/bin/activate"
