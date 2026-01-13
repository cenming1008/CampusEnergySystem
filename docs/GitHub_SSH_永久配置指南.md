# GitHub SSH 永久配置指南

> 一次配置，永久使用，随时推送

---

## 🎯 目标

配置完成后，您可以：
- ✅ 随时使用 `git push` 推送代码
- ✅ 无需每次输入密码
- ✅ 系统重启后自动加载
- ✅ 所有终端窗口都能使用

---

## 🚀 快速配置（推荐）

### 方式A：一键配置脚本 ⭐

```bash
./bin/setup_github_ssh.sh
```

脚本会自动：
1. ✅ 检查/生成 SSH 密钥
2. ✅ 配置 SSH config
3. ✅ 添加密钥到 macOS Keychain
4. ✅ 测试连接
5. ✅ 显示配置状态

---

## 📝 手动配置（详细步骤）

### Step 1: 检查现有 SSH 密钥

```bash
ls -la ~/.ssh/
```

如果看到 `id_ed25519` 和 `id_ed25519.pub`，说明已有密钥，跳到 Step 2。

如果没有，生成新密钥：

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# 按回车使用默认位置
# 可以设置密码（推荐）或直接回车（空密码）
```

### Step 2: 配置 SSH config

创建或编辑 `~/.ssh/config`：

```bash
nano ~/.ssh/config
```

添加以下内容：

```
Host github.com
  HostName ssh.github.com
  Port 443
  User git
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
  AddKeysToAgent yes
  UseKeychain yes
```

**说明**：
- `HostName ssh.github.com` + `Port 443`：使用 443 端口（更容易通过防火墙）
- `AddKeysToAgent yes`：自动添加密钥到 agent
- `UseKeychain yes`：使用 macOS Keychain 存储密钥

保存并设置权限：

```bash
chmod 600 ~/.ssh/config
```

### Step 3: 添加密钥到 macOS Keychain

**这是永久配置的关键步骤！**

```bash
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

**如果设置了密码**，会提示输入一次，之后永久保存到 Keychain。

**验证**：

```bash
ssh-add -l
```

应该看到类似：
```
256 SHA256:xxx... your_email@example.com (ED25519)
```

### Step 4: 添加公钥到 GitHub

```bash
# 查看公钥
cat ~/.ssh/id_ed25519.pub
```

复制输出的内容，然后：

1. 访问 https://github.com/settings/keys
2. 点击 **"New SSH key"**
3. **Title**: `MineEnergySystem-MacBook` （随便起名）
4. **Key**: 粘贴刚才复制的公钥
5. 点击 **"Add SSH key"**

### Step 5: 测试连接

```bash
ssh -T git@github.com
```

成功会显示：
```
Hi username! You've successfully authenticated, but GitHub does not provide shell access.
```

### Step 6: 配置 Git 仓库

确保使用 SSH URL：

```bash
cd /Users/todo/MineEnergySystem
git remote -v
```

应该看到：
```
origin  git@github.com:cenming1008/MineEnergySystem.git (fetch)
origin  git@github.com:cenming1008/MineEnergySystem.git (push)
```

如果是 HTTPS，切换到 SSH：

```bash
git remote set-url origin git@github.com:cenming1008/MineEnergySystem.git
```

---

## ✅ 验证配置

### 测试 1: 检查密钥加载

```bash
ssh-add -l
```

应该显示您的密钥。

### 测试 2: 测试 GitHub 连接

```bash
ssh -T git@github.com
```

应该显示成功消息。

### 测试 3: 测试推送

```bash
cd /Users/todo/MineEnergySystem
git push
```

应该可以直接推送，无需输入密码。

---

## 🔧 常见问题

### Q1: 系统重启后需要重新配置吗？

**不需要！** 如果正确配置了 Keychain（Step 3），系统重启后会自动加载。

### Q2: 新开终端窗口需要重新加载吗？

**不需要！** macOS 会自动管理 SSH agent。

### Q3: 如何确认密钥在 Keychain 中？

```bash
security find-generic-password -l "SSH: /Users/$(whoami)/.ssh/id_ed25519"
```

如果找到记录，说明在 Keychain 中。

### Q4: 如果忘记密钥密码怎么办？

只能重新生成密钥：

```bash
# 备份旧密钥
mv ~/.ssh/id_ed25519 ~/.ssh/id_ed25519.old
mv ~/.ssh/id_ed25519.pub ~/.ssh/id_ed25519.pub.old

# 生成新密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 重新配置
./bin/setup_github_ssh.sh
```

### Q5: 为什么使用 443 端口？

有些网络（公司、学校）会阻止 22 端口（标准 SSH 端口），但通常不会阻止 443 端口（HTTPS 端口）。

GitHub 在 `ssh.github.com:443` 提供 SSH 服务。

### Q6: 如何检查配置是否正确？

运行诊断脚本：

```bash
./bin/load_ssh_key.sh
```

---

## 🎯 配置检查清单

- [ ] SSH 密钥已生成（`~/.ssh/id_ed25519`）
- [ ] SSH config 已配置（`~/.ssh/config`）
- [ ] 密钥已添加到 Keychain
- [ ] 公钥已添加到 GitHub
- [ ] SSH 连接测试成功
- [ ] Git 远程仓库使用 SSH URL
- [ ] `git push` 可以正常工作

---

## 📊 配置文件位置

```
~/.ssh/
├── id_ed25519          # 私钥（不要泄露！）
├── id_ed25519.pub      # 公钥（可以公开）
├── config              # SSH 配置
└── known_hosts         # 已知主机
```

---

## 🔐 安全建议

1. **保护私钥**
   ```bash
   chmod 600 ~/.ssh/id_ed25519
   chmod 644 ~/.ssh/id_ed25519.pub
   ```

2. **使用密码保护**
   - 生成密钥时设置密码
   - 第一次使用时输入，之后 Keychain 自动管理

3. **定期轮换密钥**
   - 建议每年更换一次 SSH 密钥

4. **备份密钥**
   ```bash
   cp ~/.ssh/id_ed25519* ~/Documents/ssh_backup/
   ```

5. **不要提交私钥到 Git**
   - 确保 `.gitignore` 包含 `*.pem`, `id_*`

---

## 🚨 故障排查

### 问题：ssh-add -l 显示 "The agent has no identities"

**解决**：

```bash
# 重新添加密钥
ssh-add --apple-use-keychain ~/.ssh/id_ed25519

# 验证
ssh-add -l
```

### 问题：git push 仍然要求密码

**可能原因**：使用的是 HTTPS URL

**解决**：

```bash
# 检查
git remote -v

# 如果是 https://，切换到 SSH
git remote set-url origin git@github.com:cenming1008/MineEnergySystem.git
```

### 问题：Connection timeout

**可能原因**：22 端口被阻止

**解决**：确保 `~/.ssh/config` 使用 443 端口（见 Step 2）

### 问题：Permission denied (publickey)

**可能原因**：公钥未添加到 GitHub

**解决**：
1. 复制公钥：`cat ~/.ssh/id_ed25519.pub`
2. 添加到 GitHub：https://github.com/settings/keys

---

## 📚 相关命令参考

```bash
# 查看 SSH 配置
cat ~/.ssh/config

# 查看加载的密钥
ssh-add -l

# 查看公钥
cat ~/.ssh/id_ed25519.pub

# 测试 GitHub 连接
ssh -T git@github.com

# 查看 Git 远程仓库
git remote -v

# 添加密钥到 agent
ssh-add ~/.ssh/id_ed25519

# 添加密钥到 Keychain（永久）
ssh-add --apple-use-keychain ~/.ssh/id_ed25519

# 从 agent 删除所有密钥
ssh-add -D

# 查看详细 SSH 连接信息
ssh -vT git@github.com
```

---

## 🎉 完成！

配置完成后，您可以随时使用：

```bash
cd /Users/todo/MineEnergySystem
git add .
git commit -m "your message"
git push
```

**完全不需要输入密码！** 🚀

---

**遇到问题？运行诊断脚本：**

```bash
./bin/setup_github_ssh.sh
```
