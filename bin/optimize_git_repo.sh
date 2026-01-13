#!/bin/bash
# Git 仓库优化脚本

set -e

echo "🔧 Git 仓库优化工具"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Step 1: 切换到 SSH
echo -e "${BLUE}Step 1/5: 切换到 SSH 协议${NC}"
CURRENT_URL=$(git remote get-url origin)
echo "当前远程仓库: $CURRENT_URL"

if [[ $CURRENT_URL == https://* ]]; then
    echo -e "${YELLOW}检测到 HTTPS 协议，切换到 SSH...${NC}"
    
    # 提取仓库信息
    REPO_PATH=$(echo $CURRENT_URL | sed 's#https://github.com/##')
    SSH_URL="git@github.com:$REPO_PATH"
    
    git remote set-url origin "$SSH_URL"
    echo -e "${GREEN}✅ 已切换到 SSH: $SSH_URL${NC}"
else
    echo -e "${GREEN}✅ 已在使用 SSH${NC}"
fi
echo ""

# Step 2: 优化 Git 配置
echo -e "${BLUE}Step 2/5: 优化 Git 配置${NC}"

# 增加缓冲区
git config --global http.postBuffer 524288000
echo "✅ HTTP 缓冲区: 500MB"

# 启用压缩
git config --global core.compression 9
echo "✅ 压缩级别: 9"

# 使用 HTTP/2
git config --global http.version HTTP/2
echo "✅ HTTP 版本: HTTP/2"

# 增加网络超时
git config --global http.lowSpeedLimit 0
git config --global http.lowSpeedTime 999999
echo "✅ 网络超时: 已优化"

echo ""

# Step 3: 检查大文件
echo -e "${BLUE}Step 3/5: 检查大文件${NC}"
echo "正在扫描仓库中的大文件..."

LARGE_FILES=$(git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  awk '/^blob/ {if ($3 > 1048576) print $3/1048576 " MB\t" substr($0, index($0,$4))}' | \
  sort -rn | head -10)

if [ -n "$LARGE_FILES" ]; then
    echo -e "${YELLOW}发现大文件（>1MB）：${NC}"
    echo "$LARGE_FILES"
    echo ""
    echo -e "${YELLOW}建议：${NC}"
    echo "1. 将图片/二进制文件添加到 .gitignore"
    echo "2. 使用 Git LFS 管理大文件"
    echo "3. 运行: ./bin/remove_large_files.sh"
else
    echo -e "${GREEN}✅ 没有发现大文件${NC}"
fi
echo ""

# Step 4: 清理和压缩
echo -e "${BLUE}Step 4/5: 清理和压缩仓库${NC}"
echo "正在运行 git gc..."

git gc --aggressive --prune=now
echo -e "${GREEN}✅ 仓库已优化${NC}"
echo ""

# Step 5: 显示优化结果
echo -e "${BLUE}Step 5/5: 优化结果${NC}"

REPO_SIZE=$(du -sh .git | awk '{print $1}')
echo "📦 仓库大小: $REPO_SIZE"

REMOTE_URL=$(git remote get-url origin)
echo "🔗 远程仓库: $REMOTE_URL"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 优化完成！${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}现在可以推送了：${NC}"
echo "git push"
echo ""
echo -e "${YELLOW}💡 提示：${NC}"
echo "• SSH 推送速度通常是 HTTPS 的 2-5 倍"
echo "• 首次推送大量文件会较慢，后续会很快"
echo "• 建议将大文件（图片、视频）添加到 .gitignore"
echo ""
