# 📜 脚本工具集

本目录包含项目所有的脚本文件，按类型分类存放。

---

## 📁 目录结构

```
scripts/
├── README.md                   # 📖 本文件 - 脚本总览
├── QUICK_REFERENCE.md          # ⚡ 快速参考卡片
│
├── shell/                      # Shell 脚本（运维和管理）
│   ├── README.md              # 📖 Shell 脚本详细文档
│   │
│   ├── 🚀 服务启停
│   ├── start.sh               # 启动所有服务（生产）
│   ├── start_dev_env.sh       # 启动开发环境（仅中间件）
│   ├── stop.sh                # 停止所有服务
│   ├── stop_dev_env.sh        # 停止开发环境
│   ├── restart_backend.sh     # 重启后端服务
│   ├── rebuild_backend.sh     # 重新构建后端
│   ├── start_frontend.sh      # 启动前端开发服务器
│   │
│   ├── 📊 状态检查
│   ├── status.sh              # 查看服务状态
│   ├── test_health.sh         # 测试健康检查
│   ├── check_websocket.sh     # 测试 WebSocket
│   ├── check_mac_env.sh       # 检查 Mac 环境
│   │
│   ├── 🔧 维护工具
│   ├── backup.sh              # 数据库备份
│   ├── restore.sh             # 数据库恢复
│   ├── cleanup_logs.sh        # 清理日志文件
│   ├── cleanup_docker.sh      # 清理 Docker 资源
│   ├── fix_venv.sh            # 修复虚拟环境
│   ├── install_dependencies.sh # 安装系统依赖
│   │
│   └── 🚀 部署工具
       ├── deploy_prod.sh      # 生产环境部署
       └── uninstall_local_services.sh  # 卸载本地服务
│
└── python/                     # Python 脚本（数据和工具）
    ├── README.md              # 📖 Python 脚本详细文档
    │
    ├── 🚀 系统初始化
    ├── init_complete_system.py    # 完整系统初始化 ⭐
    ├── create_admin.py            # 创建管理员账号
    ├── rebuild_database.py        # 重建数据库 ⚠️
    ├── check_config.py            # 检查配置
    │
    ├── 🎯 功能演示
    ├── demo_unified_system.py     # 统一系统演示
    ├── demo_device_group.py       # 设备分组功能演示
    ├── demo_location.py           # 位置管理功能演示
    ├── demo_maintenance.py        # 维护管理功能演示
    │
    └── 🔧 开发工具
        ├── simulator_unified.py   # 统一设备模拟器 ⭐
        ├── simulator.py           # 设备数据模拟器
        ├── generate_training_data.py  # 生成训练数据
        └── stress_test.py         # 压力测试工具
```

---

## 🚀 Shell 脚本使用指南

### 1. 服务管理

#### `start.sh` - 启动所有服务
```bash
./scripts/shell/start.sh
```

**功能**：
- 检查 Docker 环境
- 创建必要目录
- 检查端口占用
- 启动所有 Docker 容器

**适用场景**：首次启动或完全重启系统

---

#### `stop.sh` - 停止所有服务
```bash
./scripts/shell/stop.sh
```

**功能**：
- 停止所有 Docker 容器
- 不删除数据

**适用场景**：临时停止系统

---

#### `status.sh` - 查看服务状态
```bash
./scripts/shell/status.sh
```

**功能**：
- 显示所有容器状态
- 显示健康检查结果
- 显示端口映射

---

#### `restart_backend.sh` - 重启后端服务
```bash
./scripts/shell/restart_backend.sh
```

**功能**：
- 只重启后端容器
- 不影响数据库、Redis、MQTT

**适用场景**：后端代码更新后

---

#### `rebuild_backend.sh` - 重新构建后端
```bash
./scripts/shell/rebuild_backend.sh
```

**功能**：
- 重新构建后端 Docker 镜像
- 应用依赖更新

**适用场景**：修改 `requirements.txt` 或 `Dockerfile` 后

---

#### `start_frontend.sh` - 启动前端
```bash
./scripts/shell/start_frontend.sh
```

**功能**：
- 启动前端开发服务器
- 自动安装依赖（如需要）

**访问**：http://localhost:5173

---

### 2. 检查和测试

#### `test_health.sh` - 测试健康检查
```bash
./scripts/shell/test_health.sh
```

**功能**：
- 测试所有健康检查端点
- 验证 Docker 容器健康状态
- 彩色输出结果

**输出示例**：
```
✅ 后端服务正在运行
✅ 系统状态: healthy
✅ 存活检查: alive
✅ 就绪检查: ready
✅ Docker 容器健康检查: healthy
```

---

#### `check_websocket.sh` - 测试 WebSocket
```bash
./scripts/shell/check_websocket.sh
```

**功能**：
- 测试 WebSocket 连接
- 检查实时数据推送

---

#### `check_mac_env.sh` - 检查 Mac 环境
```bash
./scripts/shell/check_mac_env.sh
```

**功能**：
- 检查 Docker 安装
- 检查端口占用
- 检查必要目录

**适用场景**：Mac 系统首次部署

---

### 3. 维护工具

#### `fix_venv.sh` - 修复虚拟环境
```bash
./scripts/shell/fix_venv.sh
```

**功能**：
- 修复 Python 虚拟环境问题
- 重新安装依赖

**适用场景**：虚拟环境损坏或依赖冲突

---

#### `install_dependencies.sh` - 安装依赖
```bash
./scripts/shell/install_dependencies.sh
```

**功能**：
- 安装系统级依赖
- 检查 Python 版本
- 配置开发环境

**适用场景**：首次部署或环境初始化

---

#### `cleanup_logs.sh` - 清理日志
```bash
./scripts/shell/cleanup_logs.sh
```

**功能**：
- 清理过期日志文件
- 释放磁盘空间
- 保留最近日志

**适用场景**：日志文件占用过多空间时

---

## 🐍 Python 脚本使用指南

### 1. 系统初始化与管理

#### `create_admin.py` - 创建管理员
```bash
python scripts/python/create_admin.py
```

**功能**：
- 创建管理员账号
- 交互式输入用户名和密码

**使用场景**：首次部署或重置管理员密码

---

#### `check_config.py` - 检查配置
```bash
python scripts/python/check_config.py
```

**功能**：
- 验证配置文件
- 检查环境变量
- 输出配置报告

---

#### `rebuild_database.py` - 重建数据库
```bash
python scripts/python/rebuild_database.py
```

**功能**：
- 删除并重建所有数据库表
- 重新初始化数据结构

**⚠️ 警告**：会删除所有数据，谨慎使用！

---

### 2. 功能演示脚本

#### `demo_unified_system.py` - 统一系统演示
```bash
python scripts/python/demo_unified_system.py
```

**功能**：
- 演示完整系统功能
- 创建测试数据
- 展示各模块协同工作

**使用场景**：系统功能演示、培训、测试

---

#### `demo_device_group.py` - 设备分组演示
```bash
python scripts/python/demo_device_group.py
```

**功能**：
- 演示设备分组功能
- 创建分组和关联设备
- 展示分组查询

---

#### `demo_location.py` - 位置管理演示
```bash
python scripts/python/demo_location.py
```

**功能**：
- 演示位置层级管理
- 创建区域、车间、设备位置
- 展示位置关联

---

#### `demo_maintenance.py` - 维护管理演示
```bash
python scripts/python/demo_maintenance.py
```

**功能**：
- 演示设备维护流程
- 创建维护计划和记录
- 展示维护状态管理

---

### 3. 开发工具

#### `simulator.py` - 设备模拟器
```bash
python scripts/python/simulator.py
```

**功能**：
- 模拟设备数据上报
- 生成随机遥测数据
- 通过 MQTT 发送数据

**使用场景**：
- 开发测试
- 演示系统功能
- 压力测试准备

**配置**：
- 设备数量：代码中配置
- 上报频率：默认 5 秒
- MQTT 主题：`mine/telemetry`

---

#### `stress_test.py` - 压力测试
```bash
python scripts/python/stress_test.py
```

**功能**：
- 并发 API 请求测试
- 数据库性能测试
- 生成性能报告

**测试项目**：
- API 响应时间
- 并发处理能力
- 数据库查询性能

---

#### `generate_training_data.py` - 生成训练数据
```bash
python scripts/python/generate_training_data.py
```

**功能**：
- 生成 LSTM 模型训练数据
- 创建模拟的历史能耗数据
- 支持自定义时间范围和设备

**使用场景**：LSTM 预测模型训练前的数据准备

---

## 📝 常用操作速查

### 日常开发
```bash
# 启动系统
./scripts/shell/start.sh

# 查看状态
./scripts/shell/status.sh

# 启动前端
./scripts/shell/start_frontend.sh

# 模拟设备数据
python scripts/python/simulator.py
```

### 代码更新后
```bash
# 重启后端
./scripts/shell/restart_backend.sh

# 或重新构建（依赖更新）
./scripts/shell/rebuild_backend.sh
```

### 测试验证
```bash
# 测试健康检查
./scripts/shell/test_health.sh

# 测试 WebSocket
./scripts/shell/check_websocket.sh

# 配置检查
python scripts/python/check_config.py
```

### 功能演示
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

### 系统维护
```bash
# 停止系统
./scripts/shell/stop.sh

# 清理日志
./scripts/shell/cleanup_logs.sh

# 重建数据库（危险操作！）
python scripts/python/rebuild_database.py
```

---

## 🔧 脚本开发规范

### Shell 脚本
- **文件名**：小写字母 + 下划线，`.sh` 后缀
- **首行**：`#!/bin/bash`
- **注释**：每个函数和关键步骤都要注释
- **错误处理**：使用 `set -e` 或适当的错误检查
- **颜色输出**：使用 ANSI 颜色代码提升可读性

### Python 脚本
- **文件名**：小写字母 + 下划线，`.py` 后缀
- **编码**：UTF-8
- **文档**：使用 docstring 说明功能
- **日志**：使用 `loguru` 记录日志
- **配置**：从环境变量或配置文件读取

---

## 🚨 注意事项

### 权限问题
所有脚本需要执行权限：
```bash
chmod +x scripts/shell/*.sh
```

### 路径问题
脚本应该从**项目根目录**执行：
```bash
# 正确 ✅
./scripts/shell/start.sh

# 错误 ❌
cd scripts/shell && ./start.sh
```

### 环境依赖
- **Shell 脚本依赖**：`bash`, `docker`, `docker compose`, `curl`
- **Python 脚本依赖**：见 `requirements.txt`

### 危险操作
以下脚本会删除数据，使用前务必备份：
- `rebuild_database.py` - 重建数据库

---

## 📚 文档导航

### 脚本文档

- **[⚡ 快速参考卡片](./QUICK_REFERENCE.md)** - 常用脚本速查，复制即用 ⭐
- **[📖 Python 脚本详解](./python/README.md)** - Python 脚本完整文档
- **[📖 Shell 脚本详解](./shell/README.md)** - Shell 脚本完整文档

### 项目文档

- [README.md](../README.md) - 项目主文档
- [app/README.md](../app/README.md) - 代码结构说明
- [docs/README.md](../docs/README.md) - 文档总导航

### 新手指南

- [快速启动指南](../docs/01-新手入门/快速启动指南.md)
- [全新系统初始化指南](../docs/01-新手入门/全新系统初始化指南.md)
- [本地开发环境配置](../docs/01-新手入门/本地开发环境配置.md)

### 部署文档

- [企业部署完整指南](../docs/03-开发与部署/企业部署完整指南.md)
- [Docker 脚本说明](../docs/03-开发与部署/DOCKER_SCRIPTS.md)

---

## 🗂️ 脚本分类速查

### 按功能分类

**系统启停**：
- `start.sh`, `stop.sh`, `restart_backend.sh`, `rebuild_backend.sh`, `start_frontend.sh`

**检查测试**：
- `status.sh`, `test_health.sh`, `check_websocket.sh`, `check_mac_env.sh`, `check_config.py`, `stress_test.py`

**数据生成**：
- `simulator.py`, `generate_training_data.py`

**功能演示**：
- `demo_unified_system.py`, `demo_device_group.py`, `demo_location.py`, `demo_maintenance.py`

**系统管理**：
- `create_admin.py`, `rebuild_database.py`

**维护清理**：
- `cleanup_logs.sh`, `fix_venv.sh`

---

**最后更新**：2026-01-24  
**维护状态**：活跃维护
