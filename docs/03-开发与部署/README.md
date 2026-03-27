# 开发与部署指南

> 开发工具、部署流程和最佳实践

---

## 📚 文档列表

### 🔧 Git 完整指南

**[Git完整指南.md](./Git完整指南.md)** ⭐ **开发必读**

完整的 Git 操作指南，包含：

#### 📋 内容概览

1. **Git 文件管理** - .gitignore 配置和使用
2. **Git 推送优化** - 解决 push 慢的问题
3. **GitHub SSH 配置** - 永久配置，无需密码

**适合人群**：
- 需要提交代码的开发者
- 遇到 Git 推送慢的用户
- 想要配置 SSH 的用户

---

### 🐳 Docker 脚本指南

**[DOCKER_SCRIPTS.md](./DOCKER_SCRIPTS.md)**

Docker 相关脚本的完整使用指南：

- Docker Compose 配置
- 容器管理命令
- 服务启动和停止
- 日志查看和调试
- 数据持久化

**适合人群**：
- 使用 Docker 部署的用户
- 需要管理容器的运维人员

---

### 🗄️ 数据库存储说明

**[DATABASE_STORAGE.md](./DATABASE_STORAGE.md)**

数据库存储目录的完整说明：

- `pg_data/` 和 `pg_data_dev/` 目录的区别
- 生产环境与开发环境的数据隔离
- 数据库备份和恢复方法
- 故障排查和最佳实践

**适合人群**：
- 需要管理数据库的运维人员
- 需要了解数据存储的开发者

---

### 🚀 系统启动与运行

**[系统启动完整指南.md](./系统启动完整指南.md)**  
- 系统启动流程与脚本说明  

**[日志管理指南.md](./日志管理指南.md)**  
- 日志配置、轮转与查看  

---

### 🏢 企业部署指南

**[企业部署完整指南.md](./企业部署完整指南.md)** ⭐ **企业部署必读**

完整的企业级生产环境部署指南：

#### 📋 内容概览

1. **部署前准备** - 硬件、软件、网络规划
2. **服务器环境配置** - Docker、防火墙、目录结构
3. **生产环境配置** - docker-compose.prod.yml、环境变量
4. **安全加固** - 密码、密钥、MQTT认证、数据库安全
5. **Nginx反向代理** - 配置、SSL/HTTPS
6. **数据备份与恢复** - 自动备份脚本、恢复流程
7. **监控与日志管理** - 日志轮转、健康检查、系统监控
8. **高可用部署** - 数据库主从、Redis哨兵、负载均衡
9. **运维管理脚本** - 部署、重启、状态查看脚本
10. **故障排查** - 常见问题解决方案

**快速参考**：
- 生产部署以本指南为准；已归档的速查与阶段性验收材料见 `docs/archive/`

**适合人群**：
- 企业生产环境部署的运维人员
- 需要高可用和安全的部署场景
- 需要完整部署文档的团队

---

### ✅ 工业上线清单

**[工业上线清单.md](./工业上线清单.md)** ⭐ **上线前必看**

上线前验收与运行检查表，覆盖：

1. 当前已具备能力
2. 上线前必须确认项
3. 发布前推荐命令
4. 上线后观察指标
5. 仍建议补齐的 P0 / P1 / P2 项

---

### 📡 MQTT 协议冻结版

**[MQTT接入协议冻结版.md](./MQTT接入协议冻结版.md)**

试点与正式交付阶段统一使用的 MQTT 接入约定，覆盖：

1. Topic 规范
2. Payload 字段清单
3. 时间戳和设备编码规则
4. 幂等、重试与补偿约束

---

### 🧪 试点发布与现场演练

**[试点发布与现场演练手册.md](./试点发布与现场演练手册.md)** ⭐ **试点前必读**

把发布检查、备份恢复、回滚、冒烟验收、通知通道验证串成一条标准化演练路径。

**[试点验收证据包模板.md](./试点验收证据包模板.md)**

用于沉淀试点验收日志、容量基线、恢复演练和通知通道验证结果。

### 🚚 GitHub Actions 远程部署

**[GitHub_Actions_远程部署说明.md](./GitHub_Actions_远程部署说明.md)**

说明如何配置 `deploy.yml` 所需的 Environment secrets/vars，让发布工作流真正执行远端部署。

---

## 🚀 快速开始

### Git 快速配置

SSH 配置与推送优化请参考：[Git完整指南](./Git完整指南.md)

```bash
# 提交并推送代码
git add .
git commit -m "your message"
git push
```

### Docker 快速命令

```bash
# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f backend

# 重启服务
docker compose restart backend

# 停止服务
docker compose down
```

---

## 🔧 开发环境配置

### 本地开发模式

```bash
# 1. 启动基础服务（Docker）
docker compose up -d db redis mqtt

# 2. 激活 Python 虚拟环境
source venv/bin/activate

# 3. 启动后端（支持热重载）
python run.py

# 4. 新开终端启动前端
cd frontend && npm run dev
```

### 代码提交流程

---

## 🧭 当前建议入口

当前目录建议优先使用以下文档：

- `企业部署完整指南.md`
- `工业上线清单.md`
- `MQTT接入协议冻结版.md`
- `后端容量基线指南.md`
- `试点发布与现场演练手册.md`
- `GitHub_Actions_远程部署说明.md`

历史验收结论、差距清单、优化建议和演练记录已迁入 `docs/archive/`，不再作为当前主入口。

```bash
# 1. 查看修改
git status
git diff

# 2. 暂存修改
git add .

# 3. 提交（使用规范的提交信息）
git commit -m "feat: 添加新功能"

# 4. 推送到远程
git push
```

---

## 📊 Git 工作流程

### 功能开发流程

```bash
# 1. 创建功能分支
git checkout -b feature/new-feature

# 2. 开发和测试
# ... 编写代码 ...

# 3. 提交更改
git add .
git commit -m "feat: 实现新功能"

# 4. 推送分支
git push -u origin feature/new-feature

# 5. 创建 Pull Request
# 在 GitHub 上创建 PR

# 6. 合并到主分支
git checkout main
git merge feature/new-feature

# 7. 删除功能分支
git branch -d feature/new-feature
```

### Bug 修复流程

```bash
# 1. 创建修复分支
git checkout -b fix/bug-description

# 2. 修复 bug
# ... 修改代码 ...

# 3. 提交
git commit -m "fix: 修复XX问题"

# 4. 推送并合并
git push -u origin fix/bug-description
```

---

## 🐳 Docker 最佳实践

### 日常管理

```bash
# 查看容器资源占用
docker stats

# 清理未使用的镜像
docker image prune -a

# 查看容器日志（最近100行）
docker compose logs --tail=100 backend

# 进入容器调试
docker exec -it mine_backend bash
```

### 数据管理

```bash
# 备份数据库
docker exec mine_energy_db pg_dump -U admin mine_energy > backup.sql

# 恢复数据库
cat backup.sql | docker exec -i mine_energy_db psql -U admin mine_energy

# 清除所有数据（危险！）
docker compose down -v
```

---

## ⚡ 性能优化清单

### 开发环境

- [ ] 使用虚拟环境隔离依赖
- [ ] 启用后端热重载
- [ ] 配置前端代理
- [ ] 使用 Redis 缓存

### 生产环境

- [ ] 启用 Docker 资源限制
- [ ] 配置 Nginx 反向代理
- [ ] 启用 GZIP 压缩
- [ ] 配置 CDN
- [ ] 数据库连接池
- [ ] 定期清理日志

---

## 🔐 安全建议

### Git 安全

- ✅ 不要提交 `.env` 文件
- ✅ 不要提交密钥文件
- ✅ 使用 SSH 而不是 HTTPS
- ✅ 定期更新 `.gitignore`

### Docker 安全

- ✅ 不要使用 root 用户
- ✅ 限制容器资源
- ✅ 定期更新镜像
- ✅ 使用私有镜像仓库

### API 安全

- ✅ 使用 JWT 认证
- ✅ 启用 HTTPS
- ✅ 限制请求频率
- ✅ 验证输入数据

---

## 📝 常用脚本

项目提供的开发脚本（位于 `scripts/shell/` 目录）：

### 服务管理
- `start.sh` - 启动所有服务
- `stop.sh` - 停止所有服务
- `status.sh` - 查看服务状态
- `restart_backend.sh` - 重启后端服务
- `rebuild_backend.sh` - 重新构建后端

### 检查与维护
- `test_health.sh` - 健康检查
- `check_websocket.sh` - WebSocket 测试
- `check_mac_env.sh` - Mac 环境检查
- `fix_venv.sh` - 修复虚拟环境
- `install_dependencies.sh` - 安装依赖
- `cleanup_logs.sh` - 清理日志

更多脚本请参考：[scripts/README.md](../../scripts/README.md)

---

## 🎯 CI/CD 流程（建议）

### GitHub Actions 示例

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          docker compose up -d
          python -m pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          # 部署脚本
```

---

## 🔗 相关资源

### 内部文档

- [快速启动指南](../01-新手入门/快速启动指南.md)
- [安装配置指南](../01-新手入门/安装配置完整指南.md)
- [故障排查](../04-故障排查/README.md)

### 外部资源

- [Git 官方文档](https://git-scm.com/doc)
- [Docker 官方文档](https://docs.docker.com/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)

---

## 🎯 下一步

配置完开发环境后，您可以：

1. **开始开发**：修改代码，提交更改
2. **学习 LSTM**：查看 [../02-功能使用/LSTM预测完整指南.md](../02-功能使用/LSTM预测完整指南.md)
3. **部署上线**：配置生产环境
4. **性能优化**：阅读优化建议文档

---

**返回**：[docs 主目录](../README.md)
