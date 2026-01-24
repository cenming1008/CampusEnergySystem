# Git 完整操作指南

> 包含 Git 文件管理、推送优化和 GitHub SSH 配置的完整指南

---

## 📋 目录

- [1. Git 文件管理 (.gitignore)](#1-git-文件管理-gitignore)
- [2. Git 推送优化](#2-git-推送优化)
- [3. GitHub SSH 永久配置](#3-github-ssh-永久配置)

---

## 1. Git 文件管理 (.gitignore)

### 为什么需要 .gitignore？

在项目开发中，有些文件不应该被提交到 Git 仓库：
- ❌ 敏感信息（密码、密钥）
- ❌ 大文件（图片、视频、数据库文件）
- ❌ 临时文件（日志、缓存）
- ❌ 依赖包（node_modules、venv）

### .gitignore 配置

项目的 `.gitignore` 已经配置了常见的忽略规则：

```gitignore
# Python 相关
__pycache__/
*.py[cod]
venv/
.venv

# 环境配置
.env
.env.local
*.env

# 日志文件
logs/
*.log

# 数据库数据
pg_data/
*.db
*.sqlite

# 前端相关
node_modules/
dist/
build/

# 大文件
*.png
*.jpg
*.mp4
*.zip
*.tar.gz

# 例外：保留必要的小图标
!frontend/public/logo.svg
!frontend/public/favicon.ico
```

### 常用 Git 忽略命令

```bash
# 查看哪些文件被忽略
git status --ignored

# 强制添加被忽略的文件（不推荐）
git add -f <file>

# 检查文件是否被忽略
git check-ignore -v <file>

# 清除 Git 缓存（应用新的 .gitignore）
git rm -r --cached .
git add .
git commit -m "Update .gitignore"
```

### 如果已经提交了不该提交的文件

#### 方法1：从 Git 删除但保留本地文件

```bash
# 从 Git 中移除，但保留本地文件
git rm --cached <file>

# 或移除整个目录
git rm -r --cached <directory>

# 提交更改
git commit -m "Remove sensitive files from Git"
```

#### 方法2：从 Git 历史中完全删除

```bash
# 使用 filter-branch 删除文件
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch <file>' \
  --prune-empty --tag-name-filter cat -- --all

# 清理引用
git for-each-ref --format="delete %(refname)" refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 强制推送（需要仓库权限）
git push origin --force --all
```

⚠️ **注意**：`--force` 会重写 Git 历史，如果有协作者需要提前通知！

---

## 2. Git 推送优化

### 为什么 Git Push 慢？

常见原因：
1. **使用 HTTPS 协议**（比 SSH 慢 2-5 倍）
2. **仓库中有大文件**（图片、视频等）
3. **首次推送大量文件**
4. **网络问题**（国内访问 GitHub 慢）

### 快速诊断

```bash
# 检查当前使用的协议
git remote -v

# 检查仓库大小
du -sh .git

# 检查大文件
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  awk '/^blob/ {if ($3 > 1048576) print $3/1048576 " MB\t" substr($0, index($0,$4))}' | \
  sort -rn | head -10
```

### 解决方案 1：切换到 SSH（推荐 ⭐）

**最有效的优化，速度提升 2-5 倍！**

```bash
# 切换到 SSH
git remote set-url origin git@github.com:用户名/仓库名.git

# 验证
git remote -v

# 重新推送
git push
```

### 解决方案 2：优化 Git 配置

```bash
# 增加缓冲区（处理大文件）
git config --global http.postBuffer 524288000  # 500MB

# 启用最大压缩
git config --global core.compression 9

# 使用 HTTP/2
git config --global http.version HTTP/2

# 增加网络超时
git config --global http.lowSpeedLimit 0
git config --global http.lowSpeedTime 999999
```

### 解决方案 3：移除大文件

```bash
# 查看仓库中的大文件
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  awk '/^blob/ {if ($3 > 1048576) print $3/1048576 " MB\t" substr($0, index($0,$4))}' | \
  sort -rn | head -10

# 从 Git 中删除大文件（但保留本地）
git rm --cached <large-file>

# 提交
git commit -m "Remove large files"

# 推送
git push
```

### 优化建议

按上面的步骤执行即可完成仓库清理与性能优化。

### 性能对比

| 操作 | HTTPS | SSH | 提升 |
|------|-------|-----|------|
| 小文件推送 | 5-10s | 2-3s | 2-3倍 |
| 大文件推送 | 60-120s | 15-30s | 4-5倍 |
| 网络不稳定 | 经常失败 | 很少失败 | 稳定性↑ |

---

## 3. GitHub SSH 永久配置

### 为什么需要 SSH？

- ✅ **更快**：比 HTTPS 快 2-5 倍
- ✅ **更安全**：使用密钥认证，不需要密码
- ✅ **更方便**：配置一次，永久使用
- ✅ **更稳定**：不受网络限制

### 快速配置（3步）

#### Step 1: 生成 SSH 密钥

```bash
# 生成 ED25519 密钥（推荐）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 按回车使用默认位置：~/.ssh/id_ed25519
# 可以设置密码（推荐）或直接回车（空密码）
```

#### Step 2: 添加密钥到 GitHub

```bash
# 查看公钥
cat ~/.ssh/id_ed25519.pub

# 复制输出的内容，然后：
# 1. 访问 https://github.com/settings/keys
# 2. 点击 "New SSH key"
# 3. Title: MineEnergySystem-MacBook
# 4. Key: 粘贴公钥
# 5. 点击 "Add SSH key"
```

#### Step 3: 配置 SSH config（macOS 永久配置）

```bash
# 创建或编辑 SSH config
nano ~/.ssh/config

# 添加以下内容：
Host github.com
  HostName ssh.github.com
  Port 443
  User git
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes
  AddKeysToAgent yes
  UseKeychain yes

# 保存并设置权限
chmod 600 ~/.ssh/config
```

**配置说明**：
- `Port 443`：使用 HTTPS 端口，更容易通过防火墙
- `AddKeysToAgent yes`：自动添加密钥到 agent
- `UseKeychain yes`：使用 macOS Keychain 存储密钥（永久保存）

#### Step 4: 添加密钥到 macOS Keychain（永久配置的关键！）

```bash
# 添加密钥到 Keychain（永久保存）
ssh-add --apple-use-keychain ~/.ssh/id_ed25519

# 验证
ssh-add -l
# 应该看到你的密钥
```

#### Step 5: 测试连接

```bash
# 测试 SSH 连接
ssh -T git@github.com

# 成功会显示：
# Hi username! You've successfully authenticated...
```

### 配置后的效果

| 场景 | 需要重新配置？ | 说明 |
|------|----------------|------|
| 系统重启 | ❌ 不需要 | Keychain 自动加载 |
| 新开终端 | ❌ 不需要 | SSH agent 自动管理 |
| 登出/登入 | ❌ 不需要 | 配置永久保存 |
| 1年后 | ❌ 不需要 | 密钥不过期 |

### 常见问题

#### 问题1：ssh-add -l 显示 "no identities"

**解决**：
```bash
# 重新添加密钥
ssh-add --apple-use-keychain ~/.ssh/id_ed25519

# 验证
ssh-add -l
```

#### 问题2：git push 仍然要求密码

**原因**：使用的是 HTTPS URL

**解决**：
```bash
# 检查
git remote -v

# 如果是 https://，切换到 SSH
git remote set-url origin git@github.com:用户名/仓库名.git
```

#### 问题3：Connection timeout

**原因**：22 端口被阻止

**解决**：确保 `~/.ssh/config` 使用 443 端口（见 Step 3）

#### 问题4：Permission denied (publickey)

**原因**：公钥未添加到 GitHub

**解决**：
1. 复制公钥：`cat ~/.ssh/id_ed25519.pub`
2. 添加到 GitHub：https://github.com/settings/keys

### 手动加载密钥（如果自动加载失败）

```bash
# 启动 ssh-agent
eval "$(ssh-agent -s)"

# 添加私钥
ssh-add ~/.ssh/id_ed25519
```

---

## 🔧 实用 Git 命令

### 查看状态和历史

```bash
# 查看当前状态
git status

# 查看提交历史
git log --oneline --graph --all

# 查看远程仓库
git remote -v

# 查看分支
git branch -a
```

### 撤销操作

```bash
# 撤销工作区修改
git checkout -- <file>

# 撤销暂存区（保留修改）
git reset HEAD <file>

# 撤销最后一次提交（保留修改）
git reset --soft HEAD~1

# 撤销最后一次提交（丢弃修改）
git reset --hard HEAD~1
```

### 分支操作

```bash
# 创建新分支
git branch <branch-name>

# 切换分支
git checkout <branch-name>

# 创建并切换
git checkout -b <branch-name>

# 删除分支
git branch -d <branch-name>

# 合并分支
git merge <branch-name>
```

### 暂存操作

```bash
# 暂存当前修改
git stash

# 查看暂存列表
git stash list

# 恢复最近的暂存
git stash pop

# 恢复指定暂存
git stash apply stash@{0}
```

---

## 🎯 最佳实践

### 提交规范

```bash
# 好的提交信息格式
git commit -m "feat: 添加 LSTM 预测功能"
git commit -m "fix: 修复数据库连接问题"
git commit -m "docs: 更新安装文档"
git commit -m "refactor: 重构预测服务"

# 类型：
# feat: 新功能
# fix: 修复bug
# docs: 文档更新
# style: 代码格式
# refactor: 重构
# test: 测试
# chore: 构建/工具
```

### 推送前检查

```bash
# 1. 查看要提交的内容
git status
git diff

# 2. 确保不提交敏感信息
git diff | grep -i "password\|secret\|key"

# 3. 检查大文件
git ls-files | xargs ls -lh | sort -k5 -rh | head -10

# 4. 推送
git push
```

### 保持仓库整洁

```bash
# 定期清理（每周）
git gc --aggressive --prune=now

# 查看仓库大小
du -sh .git

# 删除已合并的分支
git branch --merged | grep -v '\*\|main\|master' | xargs -n 1 git branch -d
```

---

## 🚨 安全提示

1. **保护私钥**：
   ```bash
   chmod 600 ~/.ssh/id_ed25519
   chmod 644 ~/.ssh/id_ed25519.pub
   ```

2. **使用密码保护**：生成密钥时设置密码

3. **定期轮换密钥**：建议每年更换一次 SSH 密钥

4. **备份密钥**：
   ```bash
   cp ~/.ssh/id_ed25519* ~/Documents/ssh_backup/
   ```

5. **不要提交私钥**：确保 `.gitignore` 包含 `*.pem`, `id_*`

---

## 🎉 总结

### 立即优化 Git（3步）

```bash
# 1. 配置 SSH（按上文步骤）
ssh -T git@github.com

# 2. 清理大文件（如有需要）
git gc --aggressive --prune=now

# 3. 推送测试
git push
```

配置完成后，您的 Git 操作将：
- ⚡ 更快（速度提升 2-5 倍）
- 🔒 更安全（密钥认证）
- 💪 更稳定（自动重连）
- 😊 更方便（无需密码）

---

**🎓 相关文档**：
- [../01-新手入门/快速启动指南.md](../01-新手入门/快速启动指南.md)
- [../04-故障排查/README.md](../04-故障排查/README.md)
