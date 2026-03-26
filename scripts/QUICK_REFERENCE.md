# 脚本快速参考卡片

> 🚀 常用脚本速查表 - 复制即用

## 📋 目录

- [快速开始](#快速开始)
- [日常开发](#日常开发)
- [服务管理](#服务管理)
- [数据管理](#数据管理)
- [问题排查](#问题排查)
- [系统维护](#系统维护)

---

## 🚀 快速开始

### 首次部署

```bash
# 1️⃣ 检查环境（Mac用户）
./scripts/shell/check_mac_env.sh

# 2️⃣ 启动系统
./scripts/shell/start.sh

# 3️⃣ 初始化数据
python scripts/python/init_complete_system.py

# 4️⃣ 查看状态
./scripts/shell/status.sh

# 5️⃣ 启动前端
./scripts/shell/start_frontend.sh
```

### 开发环境启动

```bash
# 1️⃣ 启动中间件（数据库、Redis、MQTT）
./scripts/shell/start_dev_env.sh

# 2️⃣ 本地运行后端
python run.py

# 3️⃣ 启动前端
./scripts/shell/start_frontend.sh

# 4️⃣ 模拟设备数据
python scripts/python/simulator_unified.py
```

---

## 💻 日常开发

### 启动开发环境

```bash
# 启动中间件
./scripts/shell/start_dev_env.sh

# 启动前端（在另一个终端）
./scripts/shell/start_frontend.sh

# 运行后端（在另一个终端）
python run.py

# 模拟设备数据（可选）
python scripts/python/simulator_unified.py
```

### 代码更新后

```bash
# 后端代码更新 - 仅重启容器
./scripts/shell/restart_backend.sh

# 依赖更新 - 重新构建镜像
./scripts/shell/rebuild_backend.sh

# 前端代码更新 - 自动热更新（无需操作）
```

### 查看系统状态

```bash
# 查看所有服务状态
./scripts/shell/status.sh

# 测试健康检查
./scripts/shell/test_health.sh

# 测试 WebSocket
./scripts/shell/check_websocket.sh
```

---

## 🔧 服务管理

### 启动服务

```bash
# 启动全部（生产环境）
./scripts/shell/start.sh

# 启动开发环境（仅中间件）
./scripts/shell/start_dev_env.sh

# 启动前端
./scripts/shell/start_frontend.sh
```

### 停止服务

```bash
# 停止全部
./scripts/shell/stop.sh

# 停止开发环境
./scripts/shell/stop_dev_env.sh

# 重启后端
./scripts/shell/restart_backend.sh
```

### 服务状态

```bash
# 查看状态
./scripts/shell/status.sh

# 查看Docker容器
docker ps

# 查看容器日志
docker logs mine_backend
docker logs mine_energy_db_dev
```

---

## 💾 数据管理

### 初始化数据

```bash
# 完整系统初始化（推荐）
python scripts/python/init_complete_system.py

# 仅创建管理员
python scripts/python/create_admin.py

# 生成LSTM训练数据
python scripts/python/generate_training_data.py
```

### 备份与恢复

```bash
# 备份数据库
./scripts/shell/backup.sh

# 恢复数据库
./scripts/shell/restore.sh backups/backup_file.sql.gz

# 查看备份
ls -lh backups/

# 一键执行恢复演练并生成记录
./scripts/shell/restore_drill.sh
```

### 重置数据

```bash
# ⚠️ 重建数据库（删除所有数据）
python scripts/python/rebuild_database.py

# 重新初始化
python scripts/python/init_complete_system.py
```

### 模拟与真实数据

```bash
# 设备模拟器（推荐开发/演示）
python scripts/python/simulator_unified.py

# 真实设备网关（Modbus/HTTP → MQTT，需配置 config/gateway_devices.json）
python scripts/python/device_gateway.py
```

---

## 🐛 问题排查

### 环境检查

```bash
# 检查Mac环境
./scripts/shell/check_mac_env.sh

# 检查配置
python scripts/python/check_config.py

# 生成生产密钥片段
python scripts/python/generate_prod_secrets.py

# 测试健康检查
./scripts/shell/test_health.sh

# 压测 / 生成容量基线
python scripts/python/stress_test.py --endpoint /health/live --workers 20 --duration-seconds 60 --output artifacts/load/health_live.json

# 一键跑后端容量基线
bash ./scripts/shell/load_baseline.sh
```

### 查看日志

```bash
# 后端日志
docker logs mine_backend
docker logs -f mine_backend  # 实时查看

# 数据库日志
docker logs mine_energy_db_dev

# 本地日志文件
tail -f logs/app.log
```

### 端口检查

```bash
# 查看端口占用
lsof -i :5432  # 数据库
lsof -i :6379  # Redis
lsof -i :8088  # 后端
lsof -i :3000  # 前端

# 杀死进程
kill -9 <PID>
```

### 容器问题

```bash
# 查看所有容器
docker ps -a

# 重启特定容器
docker restart mine_backend

# 删除容器重建
docker-compose down
docker-compose up -d
```

---

## 🧹 系统维护

### 日常维护

```bash
# 清理日志（每周）
./scripts/shell/cleanup_logs.sh

# 备份数据（每天）
./scripts/shell/backup.sh

# 清理Docker资源（每月）
./scripts/shell/cleanup_docker.sh
```

### 修复问题

```bash
# 修复Python虚拟环境
./scripts/shell/fix_venv.sh

# 重新安装依赖
./scripts/shell/install_dependencies.sh

# 重建后端镜像
./scripts/shell/rebuild_backend.sh
```

### 性能测试

```bash
# 运行压力测试
python scripts/python/stress_test.py

# 查看资源使用
docker stats
```

---

## 🎯 功能演示

### 演示脚本

```bash
# 完整系统演示
python scripts/python/demo_unified_system.py

# 设备分组演示
python scripts/python/demo_device_group.py

# 位置管理演示
python scripts/python/demo_location.py

# 维护管理演示
python scripts/python/demo_maintenance.py
```

---

## 📊 常用命令组合

### 完全重启系统

```bash
# 停止服务
./scripts/shell/stop.sh

# 清理资源
./scripts/shell/cleanup_docker.sh

# 启动服务
./scripts/shell/start.sh

# 查看状态
./scripts/shell/status.sh
```

### 开发环境重置

```bash
# 停止开发环境
./scripts/shell/stop_dev_env.sh

# 删除开发数据库数据
rm -rf pg_data_dev/

# 重新启动
./scripts/shell/start_dev_env.sh

# 初始化数据
python scripts/python/init_complete_system.py
```

### 更新部署

```bash
# 备份数据
./scripts/shell/backup.sh

# 拉取代码
git pull

# 重建后端
./scripts/shell/rebuild_backend.sh

# 测试服务
./scripts/shell/test_health.sh
```

---

## ⚡ 一键命令

### 快速启动（新手）

```bash
./scripts/shell/start.sh && \
python scripts/python/init_complete_system.py && \
./scripts/shell/start_frontend.sh
```

### 开发环境（开发者）

```bash
# 终端1：启动中间件
./scripts/shell/start_dev_env.sh

# 终端2：启动后端（等中间件就绪后）
python run.py

# 终端3：启动前端
./scripts/shell/start_frontend.sh

# 终端4：模拟数据（可选）
python scripts/python/simulator_unified.py
```

### 测试验证

```bash
./scripts/shell/status.sh && \
./scripts/shell/test_health.sh && \
./scripts/shell/check_websocket.sh
```

---

## 🔑 关键脚本速记

| 脚本 | 用途 | 使用频率 |
|------|------|----------|
| `start.sh` | 启动全部服务 | ⭐⭐⭐⭐⭐ |
| `start_dev_env.sh` | 启动开发环境 | ⭐⭐⭐⭐⭐ |
| `status.sh` | 查看状态 | ⭐⭐⭐⭐⭐ |
| `init_complete_system.py` | 初始化数据 | ⭐⭐⭐⭐ |
| `simulator_unified.py` | 模拟设备 | ⭐⭐⭐⭐ |
| `test_health.sh` | 健康检查 | ⭐⭐⭐⭐ |
| `restart_backend.sh` | 重启后端 | ⭐⭐⭐ |
| `backup.sh` | 备份数据 | ⭐⭐⭐ |
| `cleanup_logs.sh` | 清理日志 | ⭐⭐ |

---

## 💡 小技巧

### 终端快捷方式

在 `~/.bashrc` 或 `~/.zshrc` 中添加：

```bash
# 进入项目目录
alias mes='cd /path/to/MineEnergySystem'

# 常用脚本
alias mes-start='./scripts/shell/start_dev_env.sh'
alias mes-status='./scripts/shell/status.sh'
alias mes-backend='python run.py'
alias mes-frontend='./scripts/shell/start_frontend.sh'
alias mes-simulator='python scripts/python/simulator_unified.py'
```

### VS Code 任务

在 `.vscode/tasks.json` 中配置：

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "启动开发环境",
      "type": "shell",
      "command": "./scripts/shell/start_dev_env.sh"
    },
    {
      "label": "查看状态",
      "type": "shell",
      "command": "./scripts/shell/status.sh"
    }
  ]
}
```

---

## 📞 获取帮助

### 文档

- [脚本总览](./README.md)
- [Python脚本详解](./python/README.md)
- [Shell脚本详解](./shell/README.md)
- [快速启动指南](../docs/01-新手入门/快速启动指南.md)

### 问题排查

1. 查看脚本详细文档
2. 检查日志输出
3. 搜索常见问题
4. 查看 GitHub Issues

---

**提示**：本文档会持续更新，建议收藏！

**最后更新**：2026-01-24
