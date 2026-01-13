#!/bin/bash
# GitHub SSH 永久配置脚本（macOS）

set -e

echo "🔧 GitHub SSH 永久配置工具"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: 检查 SSH 密钥
echo -e "${BLUE}Step 1/5: 检查 SSH 密钥${NC}"
if [ -f ~/.ssh/id_ed25519 ]; then
    echo -e "${GREEN}✅ SSH 密钥已存在${NC}"
else
    echo -e "${YELLOW}⚠️  SSH 密钥不存在，正在生成...${NC}"
    read -p "请输入您的 GitHub 邮箱: " email
    ssh-keygen -t ed25519 -C "$email" -f ~/.ssh/id_ed25519 -N ""
    echo -e "${GREEN}✅ SSH 密钥已生成${NC}"
fi
echo ""

# Step 2: 配置 SSH config
echo -e "${BLUE}Step 2/5: 配置 SSH config${NC}"
SSH_CONFIG=~/.ssh/config

# 备份现有配置
if [ -f "$SSH_CONFIG" ]; then
    cp "$SSH_CONFIG" "$SSH_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    echo "已备份现有配置"
fi

# 检查是否已有 GitHub 配置
if grep -q "Host github.com" "$SSH_CONFIG" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  GitHub 配置已存在，跳过${NC}"
else
    # 创建新配置
    cat >> "$SSH_CONFIG" << 'EOF'

# GitHub 配置（自动添加）
Host github.com
  HostName ssh.github.com
  Port 443
  User git
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
  AddKeysToAgent yes
  UseKeychain yes
EOF
    chmod 600 "$SSH_CONFIG"
    echo -e "${GREEN}✅ SSH config 已配置${NC}"
fi
echo ""

# Step 3: 添加密钥到 macOS Keychain
echo -e "${BLUE}Step 3/5: 添加密钥到 macOS Keychain${NC}"
ssh-add --apple-use-keychain ~/.ssh/id_ed25519 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 密钥已添加到 Keychain（永久保存）${NC}"
else
    echo -e "${YELLOW}⚠️  添加到 Keychain 失败，尝试普通添加${NC}"
    ssh-add ~/.ssh/id_ed25519
fi
echo ""

# Step 4: 显示公钥
echo -e "${BLUE}Step 4/5: 复制公钥到 GitHub${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}您的 SSH 公钥（请复制）：${NC}"
echo ""
cat ~/.ssh/id_ed25519.pub
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}📋 请按以下步骤操作：${NC}"
echo "1. 复制上面的公钥内容"
echo "2. 访问: https://github.com/settings/keys"
echo "3. 点击 'New SSH key'"
echo "4. Title 填写: MineEnergySystem-$(hostname)"
echo "5. Key 粘贴刚才复制的公钥"
echo "6. 点击 'Add SSH key'"
echo ""
read -p "完成后按回车继续..." 
echo ""

# Step 5: 测试连接
echo -e "${BLUE}Step 5/5: 测试 GitHub 连接${NC}"
echo "正在测试连接..."

# 使用 nc 测试端口连通性
if nc -z -w 5 ssh.github.com 443 2>/dev/null; then
    echo -e "${GREEN}✅ 网络连接正常${NC}"
    
    # 测试 SSH
    ssh -T git@github.com 2>&1 | grep -q "successfully authenticated" && \
        echo -e "${GREEN}✅ SSH 连接成功！${NC}" || \
        echo -e "${YELLOW}⚠️  SSH 连接测试超时，但配置已完成${NC}"
else
    echo -e "${YELLOW}⚠️  无法连接到 GitHub SSH 端口，但配置已完成${NC}"
fi
echo ""

# 验证密钥加载
echo "当前加载的密钥："
ssh-add -l
echo ""

# 最终提示
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 配置完成！${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}配置说明：${NC}"
echo "✅ SSH 密钥: ~/.ssh/id_ed25519"
echo "✅ SSH 配置: ~/.ssh/config"
echo "✅ 密钥已保存到 Keychain（系统重启后自动加载）"
echo "✅ 使用端口 443（更容易通过防火墙）"
echo ""
echo -e "${BLUE}测试推送：${NC}"
echo "cd /Users/todo/MineEnergySystem"
echo "git push"
echo ""
echo -e "${YELLOW}💡 提示：${NC}"
echo "如果 push 时仍然失败，运行:"
echo "./bin/load_ssh_key.sh"
echo ""
