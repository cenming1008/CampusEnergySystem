# 📜 脚本工具集

本目录包含项目所有的脚本文件，按类型分类存放。

---

## 📁 目录结构

```
scripts/
├── shell/          # Shell 脚本（运维和管理）
│   ├── start.sh           # 🚀 启动所有服务
│   ├── stop.sh            # 🛑 停止所有服务
│   ├── status.sh          # 📊 查看服务状态
│   ├── restart_backend.sh # 🔄 重启后端服务
│   ├── rebuild_backend.sh # 🔨 重新构建后端
│   ├── fix_db.sh          # 🔧 修复数据库问题
│   ├── test_health.sh     # 🏥 测试健康检查
│   ├── check_websocket.sh # 🌐 测试 WebSocket
│   ├── check_mac_env.sh   # 🍎 检查 Mac 环境
│   └── start_frontend.sh  # 💻 启动前端开发服务器
│
└── python/         # Python 脚本（数据和工具）
    ├── create_admin.py    # 👤 创建管理员账号
    ├── init_devices.py    # 📱 初始化测试设备
    ├── reset_system.py    # 🔄 重置系统数据
    ├── check_config.py    # ⚙️  检查配置文件
    ├── clear_db.py        # 🗑️  清空数据库
    ├── simulator.py       # 🎮 设备数据模拟器
    └── stress_test.py     # 💪 压力测试工具
```

---

## 🚀 Shell 脚本使用指南

### 1. 启动和停止

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

### 2. 检查和测试

#### `status.sh` - 查看服务状态
```bash
./scripts/shell/status.sh
```

**功能**：
- 显示所有容器状态
- 显示健康检查结果
- 显示端口映射

---

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

#### `fix_db.sh` - 修复数据库问题
```bash
./scripts/shell/fix_db.sh
```

**功能**：
- 修复数据库权限问题
- 重置数据库连接

**⚠️ 注意**：可能需要重启数据库

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

## 🐍 Python 脚本使用指南

### 1. 系统初始化

#### `create_admin.py` - 创建管理员
```bash
python scripts/python/create_admin.py
```

**功能**：
- 创建管理员账号
- 交互式输入用户名和密码

**使用场景**：首次部署或重置管理员密码

---

#### `init_devices.py` - 初始化设备
```bash
python scripts/python/init_devices.py
```

**功能**：
- 创建测试设备
- 初始化设备配置

**使用场景**：开发测试环境初始化

---

### 2. 系统维护

#### `reset_system.py` - 重置系统
```bash
python scripts/python/reset_system.py
```

**功能**：
- 清空所有数据
- 重新初始化数据库

**⚠️ 警告**：会删除所有数据，谨慎使用！

---

#### `clear_db.py` - 清空数据库
```bash
python scripts/python/clear_db.py
```

**功能**：
- 清空所有表数据
- 保留表结构

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
```

### 系统维护
```bash
# 停止系统
./scripts/shell/stop.sh

# 清空数据
python scripts/python/clear_db.py

# 重新初始化
python scripts/python/init_devices.py
```

---

## 🔧 脚本开发规范

### Shell 脚本
- 文件名：小写字母 + 下划线，`.sh` 后缀
- 首行：`#!/bin/bash`
- 注释：每个函数和关键步骤都要注释
- 错误处理：使用 `set -e` 或适当的错误检查
- 颜色输出：使用 ANSI 颜色代码提升可读性

### Python 脚本
- 文件名：小写字母 + 下划线，`.py` 后缀
- 编码：UTF-8
- 文档：使用 docstring 说明功能
- 日志：使用 `loguru` 记录日志
- 配置：从环境变量或配置文件读取

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
- Shell 脚本依赖：`bash`, `docker`, `docker compose`, `curl`
- Python 脚本依赖：见 `requirements.txt`

---

## 📚 相关文档

- [README.md](../README.md) - 项目主文档
- [app/README.md](../app/README.md) - 代码结构说明
- [docs/README.md](../docs/README.md) - 文档导航

---

**最后更新**：2026-01-12  
**维护状态**：活跃维护
