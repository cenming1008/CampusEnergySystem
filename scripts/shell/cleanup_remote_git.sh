#!/bin/bash
# 清理远程 Git 仓库中的敏感文件
# ⚠️ 警告：这会重写 Git 历史，请谨慎使用！
# 使用方法: ./scripts/shell/cleanup_remote_git.sh

set -e

echo "⚠️  警告：此脚本会重写 Git 历史！"
echo "⚠️  请确保已经备份了仓库！"
echo ""
read -p "是否继续？(yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ 已取消操作"
    exit 1
fi

echo ""
echo "🧹 开始清理远程仓库中的敏感文件..."
echo ""

# 要清理的文件列表
FILES_TO_REMOVE=(
    ".env"
    "123456"
    "123456.pub"
    "__pycache__"
    "*.pyc"
    "backups/"
    "logs/"
    "pg_data/"
    "venv/"
    "frontend/node_modules/"
    "frontend/dist/"
    "frontend/.vite/"
)

# 使用 git filter-branch 或 git filter-repo 清理历史
# 注意：git filter-repo 需要单独安装，这里使用 git filter-branch

echo "📋 要清理的文件："
for file in "${FILES_TO_REMOVE[@]}"; do
    echo "  - $file"
done

echo ""
echo "🔄 使用 git filter-branch 清理历史..."
echo "⚠️  这可能需要一些时间..."

# 方法1：使用 git filter-branch（较慢但不需要额外工具）
git filter-branch --force --index-filter \
    "git rm -rf --cached --ignore-unmatch .env 123456 123456.pub __pycache__ backups logs pg_data venv frontend/node_modules frontend/dist frontend/.vite" \
    --prune-empty --tag-name-filter cat -- --all

echo ""
echo "✅ 清理完成！"
echo ""
echo "📋 下一步操作："
echo "1. 检查清理结果: git log --oneline -5"
echo "2. 强制推送到远程（⚠️ 会覆盖远程历史）:"
echo "   git push origin --force --all"
echo "   git push origin --force --tags"
echo ""
echo "⚠️  重要提示："
echo "- 强制推送会覆盖远程仓库的历史"
echo "- 团队成员需要重新克隆仓库或执行: git fetch && git reset --hard origin/main"
echo "- 确保所有团队成员都了解这个操作"
