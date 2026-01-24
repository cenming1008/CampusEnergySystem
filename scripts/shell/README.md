# Shell 脚本工具集

Shell 脚本用于系统运维、服务管理、环境配置和日常维护。

## 📁 脚本列表

### 🚀 服务启停管理

#### `start.sh` - 启动所有服务 ⭐

**用途**：启动完整的系统（生产环境）

**使用**：
```bash
./scripts/shell/start.sh
```

**功能**：
- ✅ 检查 Docker 环境
- ✅ 创建必要目录
- ✅ 检查端口占用
- ✅ 启动所有容器（数据库、Redis、MQTT、后端）
- ✅ 等待服务就绪
- ✅ 显示启动状态

**适用场景**：
- 首次启动系统
- 完全重启所有服务

---

#### `start_dev_env.sh` - 启动开发环境 ⭐

**用途**：启动开发环境（仅中间件）

**使用**：
```bash
./scripts/shell/start_dev_env.sh
```

**功能**：
- ✅ 启动数据库（localhost:5432）
- ✅ 启动 Redis（localhost:6379）
- ✅ 启动 MQTT（localhost:1883）
- ❌ 不启动后端（本地运行）

**适用场景**：
- 本地开发
- 后端代码调试

**配套使用**：
```bash
# 启动中间件
./scripts/shell/start_dev_env.sh

# 本地运行后端
python run.py

# 启动前端
./scripts/shell/start_frontend.sh
```

---

#### `stop.sh` - 停止所有服务

**用途**：停止系统所有容器

**使用**：
```bash
./scripts/shell/stop.sh
```

**功能**：
- 停止所有 Docker 容器
- 保留数据（不删除 volumes）

**适用场景**：
- 临时停止系统
- 系统维护前

---

#### `stop_dev_env.sh` - 停止开发环境

**用途**：停止开发环境的中间件服务

**使用**：
```bash
./scripts/shell/stop_dev_env.sh
```

---

#### `restart_backend.sh` - 重启后端服务

**用途**：仅重启后端容器

**使用**：
```bash
./scripts/shell/restart_backend.sh
```

**功能**：
- 重启后端容器
- 不影响数据库、Redis、MQTT

**适用场景**：
- 后端代码更新
- 后端配置修改
- 后端服务异常

---

#### `rebuild_backend.sh` - 重新构建后端

**用途**：重新构建后端 Docker 镜像

**使用**：
```bash
./scripts/shell/rebuild_backend.sh
```

**功能**：
- 重新构建 Docker 镜像
- 应用依赖更新
- 重新部署后端

**适用场景**：
- 修改 `requirements.txt`
- 修改 `Dockerfile`
- 更新系统依赖

---

#### `start_frontend.sh` - 启动前端

**用途**：启动前端开发服务器

**使用**：
```bash
./scripts/shell/start_frontend.sh
```

**功能**：
- 检查 Node.js 环境
- 自动安装依赖（如需要）
- 启动 Vite 开发服务器

**访问**：http://localhost:3000

---

### 📊 状态检查

#### `status.sh` - 查看服务状态 ⭐

**用途**：显示所有服务的运行状态

**使用**：
```bash
./scripts/shell/status.sh
```

**输出信息**：
- 容器运行状态
- 健康检查结果
- 端口映射
- 资源使用情况

**输出示例**：
```
🔍 系统服务状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ mine_energy_db      | healthy | 0.0.0.0:5433->5432/tcp
✅ ems_redis           | healthy | 0.0.0.0:6379->6379/tcp
✅ mine_mqtt           | healthy | 0.0.0.0:1883->1883/tcp
✅ mine_backend        | healthy | 0.0.0.0:8088->8088/tcp
```

---

#### `test_health.sh` - 测试健康检查 ⭐

**用途**：测试系统健康检查端点

**使用**：
```bash
./scripts/shell/test_health.sh
```

**检查项目**：
- 后端服务可用性
- 系统健康状态
- 存活检查（liveness）
- 就绪检查（readiness）
- Docker 容器健康状态

**输出示例**：
```
🏥 健康检查测试
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 后端服务正在运行
✅ 系统状态: healthy
✅ 存活检查: alive
✅ 就绪检查: ready
✅ Docker 容器健康检查: healthy
```

---

#### `check_websocket.sh` - 测试 WebSocket

**用途**：测试 WebSocket 连接和实时数据推送

**使用**：
```bash
./scripts/shell/check_websocket.sh
```

**测试内容**：
- WebSocket 连接
- 实时数据接收
- 心跳检测

---

#### `check_mac_env.sh` - 检查 Mac 环境

**用途**：检查 macOS 系统环境配置

**使用**：
```bash
./scripts/shell/check_mac_env.sh
```

**检查项目**：
- Docker 安装和版本
- Docker Compose 版本
- Python 版本
- Node.js 版本
- 端口占用情况
- 必要目录存在性
- 文件权限

**适用场景**：
- Mac 系统首次部署
- 环境问题排查

---

### 🔧 维护工具

#### `backup.sh` - 数据库备份 ⭐

**用途**：备份数据库数据

**使用**：
```bash
./scripts/shell/backup.sh
```

**功能**：
- 导出 PostgreSQL 数据
- 压缩备份文件
- 添加时间戳
- 存储到 backups/ 目录

**输出**：
- `backups/mine_energy_backup_20260124_120000.sql.gz`

**推荐**：
- 生产环境：每天自动备份
- 开发环境：重要操作前手动备份

---

#### `restore.sh` - 数据库恢复

**用途**：从备份文件恢复数据库

**使用**：
```bash
./scripts/shell/restore.sh backups/mine_energy_backup_20260124_120000.sql.gz
```

**功能**：
- 停止后端服务
- 清空现有数据
- 导入备份数据
- 重启服务

**警告**：
- ⚠️ 会覆盖现有数据
- ⚠️ 使用前先备份当前数据

---

#### `cleanup_logs.sh` - 清理日志 ⭐

**用途**：清理过期日志文件

**使用**：
```bash
./scripts/shell/cleanup_logs.sh
```

**功能**：
- 删除7天前的日志
- 保留最近日志
- 压缩旧日志（可选）
- 释放磁盘空间

**清理规则**：
- 保留最近7天的日志
- 删除空日志文件
- 清理临时日志

**适用场景**：
- 磁盘空间不足
- 定期维护（建议每周执行）

---

#### `cleanup_docker.sh` - 清理 Docker

**用途**：清理 Docker 资源

**使用**：
```bash
./scripts/shell/cleanup_docker.sh
```

**功能**：
- 清理未使用的镜像
- 清理停止的容器
- 清理未使用的网络
- 清理构建缓存

**警告**：
- ⚠️ 会删除未使用的资源
- ⚠️ 不会删除运行中的容器

---

#### `fix_venv.sh` - 修复虚拟环境

**用途**：修复 Python 虚拟环境问题

**使用**：
```bash
./scripts/shell/fix_venv.sh
```

**功能**：
- 删除旧虚拟环境
- 创建新虚拟环境
- 重新安装依赖

**适用场景**：
- 虚拟环境损坏
- 依赖冲突
- Python 版本升级后

---

#### `install_dependencies.sh` - 安装依赖

**用途**：安装系统级依赖

**使用**：
```bash
./scripts/shell/install_dependencies.sh
```

**功能**：
- 检查操作系统
- 安装必要的系统包
- 配置 Python 环境
- 安装 Python 依赖

**适用场景**：
- 首次部署
- 环境初始化

---

### 🚀 部署工具

#### `deploy_prod.sh` - 生产环境部署

**用途**：部署到生产环境

**使用**：
```bash
./scripts/shell/deploy_prod.sh
```

**功能**：
- ✅ 环境检查
- ✅ 拉取最新代码
- ✅ 构建镜像
- ✅ 备份数据库
- ✅ 启动服务
- ✅ 健康检查
- ✅ 回滚机制（如失败）

**适用场景**：
- 生产环境部署
- 版本升级

---

#### `uninstall_local_services.sh` - 卸载本地服务

**用途**：卸载本地安装的服务（PostgreSQL、Redis等）

**使用**：
```bash
./scripts/shell/uninstall_local_services.sh
```

**功能**：
- 停止本地服务
- 删除服务配置
- 清理数据目录

**适用场景**：
- 从本地服务迁移到 Docker
- 清理环境

---

## 🚀 快速开始

### 首次部署

```bash
# 1. 检查环境（Mac 用户）
./scripts/shell/check_mac_env.sh

# 2. 启动系统
./scripts/shell/start.sh

# 3. 查看状态
./scripts/shell/status.sh

# 4. 测试健康检查
./scripts/shell/test_health.sh
```

### 开发模式

```bash
# 1. 启动开发环境（仅中间件）
./scripts/shell/start_dev_env.sh

# 2. 本地运行后端
python run.py

# 3. 启动前端
./scripts/shell/start_frontend.sh
```

### 日常维护

```bash
# 查看状态
./scripts/shell/status.sh

# 重启后端
./scripts/shell/restart_backend.sh

# 清理日志
./scripts/shell/cleanup_logs.sh

# 备份数据
./scripts/shell/backup.sh
```

---

## 📝 使用规范

### 脚本权限

所有脚本已设置执行权限：

```bash
# 查看权限
ls -l scripts/shell/*.sh

# 如需添加权限
chmod +x scripts/shell/*.sh
```

### 执行路径

脚本必须从**项目根目录**执行：

```bash
# ✅ 正确
./scripts/shell/start.sh

# ❌ 错误
cd scripts/shell && ./start.sh
```

### 环境要求

- Bash 4.0+
- Docker 20.0+
- Docker Compose 2.0+

---

## 🎨 脚本特性

### 彩色输出

所有脚本使用彩色输出，提升可读性：

```
✅ 绿色 - 成功
❌ 红色 - 错误
⚠️  黄色 - 警告
ℹ️  蓝色 - 信息
```

### 错误处理

脚本包含完善的错误处理：
- 检查前置条件
- 验证输入参数
- 捕获执行错误
- 提供清晰的错误信息

### 交互确认

危险操作会要求确认：

```bash
⚠️  警告：此操作会删除所有数据！
确认继续？(yes/no):
```

---

## 🐛 故障排查

### 问题1：权限被拒绝

**错误**：`Permission denied`

**解决**：
```bash
chmod +x scripts/shell/*.sh
```

### 问题2：Docker 命令未找到

**错误**：`docker: command not found`

**解决**：
```bash
# Mac
brew install docker docker-compose

# 或安装 Docker Desktop
```

### 问题3：端口已被占用

**错误**：`port is already allocated`

**解决**：
```bash
# 查找占用端口的进程
lsof -i :5432
lsof -i :8088

# 杀死进程
kill -9 <PID>
```

### 问题4：容器无法启动

**检查**：
```bash
# 查看容器日志
docker logs mine_backend

# 查看容器详情
docker inspect mine_backend
```

---

## ⚠️ 注意事项

### 危险操作

以下脚本可能影响数据安全：

- ⚠️ `cleanup_docker.sh` - 清理 Docker 资源
- ⚠️ `restore.sh` - 覆盖现有数据

### 生产环境

生产环境使用时注意：

1. ✅ 操作前先备份
2. ✅ 在测试环境验证
3. ✅ 选择低峰时段
4. ✅ 准备回滚方案

### 资源清理

定期执行维护脚本：

```bash
# 每周执行
./scripts/shell/cleanup_logs.sh
./scripts/shell/cleanup_docker.sh

# 每月执行
./scripts/shell/backup.sh
```

---

## 📚 相关文档

- [脚本总览](../README.md) - 脚本工具集主文档
- [Python 脚本](../python/README.md) - Python 脚本文档
- [Docker 脚本说明](../../docs/03-开发与部署/DOCKER_SCRIPTS.md)
- [快速启动指南](../../docs/01-新手入门/快速启动指南.md)

---

## 📊 脚本分类速查

### 按使用频率

**高频使用**：
- ⭐ `start.sh` / `start_dev_env.sh` - 启动服务
- ⭐ `status.sh` - 查看状态
- ⭐ `test_health.sh` - 健康检查
- `restart_backend.sh` - 重启后端

**中频使用**：
- `start_frontend.sh` - 启动前端
- `stop.sh` - 停止服务
- `cleanup_logs.sh` - 清理日志
- `backup.sh` - 备份数据

**低频使用**：
- `deploy_prod.sh` - 生产部署
- `rebuild_backend.sh` - 重建镜像
- `cleanup_docker.sh` - 清理 Docker
- `fix_venv.sh` - 修复环境

### 按用户类型

**新手用户**：
- `start.sh` - 启动系统
- `status.sh` - 查看状态
- `test_health.sh` - 测试服务

**开发人员**：
- `start_dev_env.sh` - 开发环境
- `start_frontend.sh` - 前端开发
- `restart_backend.sh` - 快速重启

**运维人员**：
- `deploy_prod.sh` - 生产部署
- `backup.sh` / `restore.sh` - 数据管理
- `cleanup_*.sh` - 资源清理

---

**创建日期**: 2026-01-24  
**最后更新**: 2026-01-24  
**维护状态**: ✅ 活跃维护
