#!/bin/bash
# Git 清理脚本 - 从 Git 跟踪中移除应该被忽略的文件
# 使用方法: ./scripts/shell/cleanup_git.sh

set -e

echo "🧹 开始清理 Git 跟踪的文件..."
echo ""

# 检查是否在 Git 仓库中
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ 错误: 当前目录不是 Git 仓库"
    exit 1
fi

# 备份当前状态
echo "📦 创建备份分支..."
git branch cleanup-backup-$(date +%Y%m%d-%H%M%S) 2>/dev/null || true

echo ""
echo "🗑️  从 Git 中移除应该被忽略的文件..."
echo ""

# 从 Git 中移除但保留本地文件
echo "1. 移除 Python 缓存文件..."
git rm -r --cached __pycache__/ 2>/dev/null || true
git rm -r --cached app/**/__pycache__/ 2>/dev/null || true
git rm -r --cached scripts/**/__pycache__/ 2>/dev/null || true
git rm -r --cached tools/**/__pycache__/ 2>/dev/null || true
git rm --cached **/*.pyc 2>/dev/null || true

echo "2. 移除环境配置文件..."
git rm --cached .env 2>/dev/null || true
git rm --cached .env.* 2>/dev/null || true

echo "3. 移除日志文件..."
git rm -r --cached logs/ 2>/dev/null || true
git rm --cached *.log 2>/dev/null || true

echo "4. 移除数据库数据目录..."
git rm -r --cached pg_data/ 2>/dev/null || true

echo "5. 移除备份文件..."
git rm -r --cached backups/ 2>/dev/null || true
git rm --cached *.tar.gz 2>/dev/null || true
git rm --cached *.backup 2>/dev/null || true

echo "6. 移除虚拟环境..."
git rm -r --cached venv/ 2>/dev/null || true
git rm -r --cached env/ 2>/dev/null || true

echo "7. 移除前端构建产物..."
git rm -r --cached frontend/node_modules/ 2>/dev/null || true
git rm -r --cached frontend/dist/ 2>/dev/null || true
git rm -r --cached frontend/build/ 2>/dev/null || true
git rm -r --cached node_modules/ 2>/dev/null || true
git rm -r --cached dist/ 2>/dev/null || true

echo "8. 移除 IDE 配置文件..."
git rm -r --cached .vscode/ 2>/dev/null || true
git rm -r --cached .idea/ 2>/dev/null || true

echo "9. 移除操作系统文件..."
git rm --cached .DS_Store 2>/dev/null || true
git rm --cached Thumbs.db 2>/dev/null || true

echo "10. 移除敏感信息文件..."
git rm --cached 123456 2>/dev/null || true
git rm --cached *password* 2>/dev/null || true
git rm --cached *secret* 2>/dev/null || true

echo ""
echo "✅ 清理完成！"
echo ""
echo "📋 下一步操作："
echo "1. 检查变更: git status"
echo "2. 查看将被移除的文件: git status --short"
echo "3. 如果确认无误，提交变更:"
echo "   git add .gitignore"
echo "   git commit -m 'chore: 更新 .gitignore 并移除不应跟踪的文件'"
echo ""
echo "⚠️  注意: 此脚本只从 Git 跟踪中移除文件，不会删除本地文件"
echo "⚠️  如果某些文件不应该被移除，请使用 'git restore --staged <file>' 恢复"
