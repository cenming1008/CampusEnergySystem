# 📝 Git 忽略文件配置指南

**更新时间**：2026-01-12

---

## 📋 概述

`.gitignore` 文件已更新，现在包含了完整的忽略规则，用于排除不应该提交到 GitHub 的文件。

---

## ✅ 已配置的忽略规则

### 1. Python 相关
- `__pycache__/` - Python 字节码缓存目录
- `*.pyc`, `*.pyo`, `*.pyd` - 编译后的 Python 文件
- `venv/`, `env/` - 虚拟环境目录
- `*.egg-info/` - Python 包信息

### 2. 环境配置和敏感信息
- `.env` - 环境变量文件（包含敏感信息）
- `.env.local`, `.env.*.local` - 本地环境配置
- `*password*`, `*secret*`, `*key*` - 可能的敏感文件

### 3. 日志文件
- `logs/` - 日志目录
- `*.log` - 日志文件

### 4. 数据库数据
- `pg_data/` - PostgreSQL/TimescaleDB 数据目录
- `*.db`, `*.sqlite` - SQLite 数据库文件

### 5. 备份文件
- `backups/` - 备份目录
- `*.backup`, `*.bak`, `*.tar.gz`, `*.zip` - 备份文件

### 6. 前端相关
- `node_modules/` - Node.js 依赖
- `dist/`, `build/` - 构建产物
- `*.map` - Source map 文件

### 7. IDE 和编辑器
- `.vscode/`, `.idea/` - IDE 配置
- `*.swp`, `*.swo` - Vim 临时文件

### 8. 操作系统文件
- `.DS_Store` - macOS 系统文件
- `Thumbs.db` - Windows 缩略图
- `$RECYCLE.BIN/` - Windows 回收站

### 9. 测试和覆盖率
- `.pytest_cache/` - pytest 缓存
- `.coverage`, `htmlcov/` - 覆盖率报告

---

## 🚨 重要：清理已跟踪的文件

**问题**：如果文件在添加到 `.gitignore` 之前已经被 Git 跟踪，它们仍然会被提交。

**解决方案**：运行清理脚本从 Git 跟踪中移除这些文件（但保留本地文件）。

### 方法一：使用清理脚本（推荐）

```bash
# 运行清理脚本
./scripts/shell/cleanup_git.sh

# 检查变更
git status

# 如果确认无误，提交变更
git add .gitignore
git commit -m "chore: 更新 .gitignore 并移除不应跟踪的文件"
```

### 方法二：手动清理

```bash
# 1. 从 Git 中移除但保留本地文件
git rm -r --cached __pycache__/
git rm -r --cached app/**/__pycache__/
git rm --cached .env
git rm -r --cached logs/
git rm -r --cached pg_data/
git rm -r --cached backups/
git rm -r --cached venv/

# 2. 检查变更
git status

# 3. 提交变更
git add .gitignore
git commit -m "chore: 更新 .gitignore 并移除不应跟踪的文件"
```

### 方法三：使用 git filter-branch（适用于历史记录清理）

⚠️ **警告**：这会重写 Git 历史，请谨慎使用！

```bash
# 从整个 Git 历史中移除敏感文件
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all
```

---

## 🔍 验证忽略规则

### 检查文件是否被忽略

```bash
# 检查特定文件/目录是否被忽略
git check-ignore -v logs/
git check-ignore -v venv/
git check-ignore -v .env
```

### 查看所有被忽略的文件

```bash
# 查看被忽略的文件列表
git status --ignored
```

---

## 📝 常见问题

### Q1: 为什么 `.env` 文件仍然出现在 `git status` 中？

**A**: 如果 `.env` 在添加到 `.gitignore` 之前已经被 Git 跟踪，需要手动从跟踪中移除：

```bash
git rm --cached .env
git commit -m "chore: 从 Git 中移除 .env 文件"
```

### Q2: 如何保留配置文件结构但忽略内容？

**A**: 可以创建一个示例文件：

```bash
# 保留示例文件
config/settings.json.example

# 忽略实际配置文件
config/settings.json
```

### Q3: 如何忽略特定目录下的某些文件？

**A**: 使用路径前缀：

```gitignore
# 只忽略根目录下的 logs/
/logs/

# 忽略所有 logs/ 目录
logs/
```

### Q4: 如何强制添加被忽略的文件？

**A**: 使用 `-f` 参数（不推荐，除非有特殊原因）：

```bash
git add -f logs/important.log
```

---

## ⚠️ 安全注意事项

### 1. 敏感信息检查

在提交代码前，请确保以下内容不会被提交：

- ✅ 数据库密码
- ✅ API 密钥
- ✅ JWT Secret Key
- ✅ 用户凭证
- ✅ 私钥文件

### 2. 检查已提交的敏感信息

```bash
# 搜索可能包含敏感信息的文件
git log --all --full-history --source -- "*password*"
git log --all --full-history --source -- "*secret*"
```

### 3. 如果敏感信息已提交

如果敏感信息已经被提交到 Git 历史中：

1. **立即更改密码/密钥**
2. **使用 git filter-branch 清理历史**（见方法三）
3. **通知团队成员更新本地仓库**

---

## 📚 参考资源

- [Git 官方文档 - gitignore](https://git-scm.com/docs/gitignore)
- [GitHub 的 .gitignore 模板](https://github.com/github/gitignore)
- [Python .gitignore 模板](https://github.com/github/gitignore/blob/main/Python.gitignore)

---

## 🎯 最佳实践

1. **尽早配置**：在项目开始时就配置好 `.gitignore`
2. **定期检查**：每次提交前检查 `git status`
3. **使用示例文件**：为配置文件创建 `.example` 版本
4. **团队协作**：确保团队成员都了解忽略规则
5. **文档化**：在 README 中说明如何配置环境变量

---

**提示**：如果遇到问题，可以查看 `scripts/shell/cleanup_git.sh` 脚本了解详细的清理步骤。
