# 🐳 使用 Docker 运行脚本

> 当后端在 Docker 中运行时，您不需要在本地安装 Python 依赖。直接使用 `docker exec` 在容器中运行脚本。

---

## 📋 前提条件

```bash
# 确保服务已启动
docker compose ps

# 应该看到 campus_backend 容器状态为 Up
```

命名约定：
- `docker compose logs/restart/ps` 使用 service 名，例如 `backend`
- `docker exec/logs/inspect` 直接操作容器时使用 `campus_backend`
- 容器内访问数据库、Redis、MQTT 时继续使用 `db`、`redis`、`mqtt`

---

## 🎯 常用脚本命令

### 1. 初始化测试设备

```bash
# 创建测试设备（电机、风机等）
docker exec campus_backend bash -c \
  "API_BASE=http://localhost:8088 python scripts/python/init_devices.py"
```

**注意**：不要使用 `-it` 标志，除非需要交互式操作。这里使用的是可见容器名 `campus_backend`，不是 compose service 名 `backend`。

### 2. 运行设备模拟器

```bash
# 方式1：前台运行（推荐用于测试，按 Ctrl+C 停止）
docker exec campus_backend bash -c \
  "MQTT_BROKER=mqtt API_BASE=http://localhost:8088 python -u scripts/python/simulator.py"

# 方式2：后台运行（不阻塞终端）
docker exec -d campus_backend bash -c \
  "MQTT_BROKER=mqtt API_BASE=http://localhost:8088 python -u scripts/python/simulator.py"

# 方式3：简化命令（如果在容器内已设置环境变量）
docker exec -it campus_backend python scripts/python/simulator_unified.py
```

**重要提示**：在 Docker 容器内运行时，必须使用：
- `MQTT_BROKER=mqtt` (不是 127.0.0.1)
- `API_BASE=http://localhost:8088` (因为脚本在 backend 容器内)
- 这里的 `mqtt` 是 Compose service 名，不是 `campus_mqtt` 容器名

### 3. 创建管理员账号

```bash
# 创建新的管理员账号
docker exec campus_backend python scripts/python/create_admin.py
```

### 4. 清空数据库

```bash
# ⚠️ 危险操作：清空所有数据
docker exec campus_backend python scripts/python/clear_db.py
```

### 5. 检查配置

```bash
# 检查系统配置和数据库连接
docker exec campus_backend python scripts/python/check_config.py
```

### 6. 系统重置

```bash
# 重置系统（清空数据 + 重新初始化）
docker exec campus_backend python scripts/python/reset_system.py
```

### 7. 压力测试

```bash
# 对 API 进行压力测试
docker exec campus_backend python scripts/python/stress_test.py
```

**💡 提示**：通常不需要 `-it` 标志。只有需要交互式输入时才使用。

### 8. 生成 LSTM 训练数据

```bash
# 生成用于 LSTM 训练的数据
docker exec -it campus_backend python scripts/generate_training_data.py
```

---

## 🔧 进入容器交互模式

如果需要运行多个命令，可以进入容器：

```bash
# 进入后端容器
docker exec -it campus_backend bash

# 现在可以像在本地一样运行命令
python scripts/python/init_devices.py
python scripts/python/simulator_unified.py
ls -la
cat config/settings.json

# 退出容器
exit
```

---

## 📊 对比：Docker vs 本地运行

### 使用 Docker（推荐）⭐

```bash
# ✅ 优点
# - 无需本地安装 Python 依赖
# - 环境与后端完全一致
# - 可以访问容器内的配置和数据
# - 不会污染本地环境

docker exec -it campus_backend python scripts/python/init_devices.py
```

### 本地运行

```bash
# ❌ 缺点
# - 需要安装所有依赖
# - 需要维护虚拟环境
# - 可能环境不一致
# - 配置文件路径可能不同

source venv/bin/activate
pip install -r requirements.txt
python scripts/python/init_devices.py
```

---

## 💡 实用技巧

### 1. 创建命令别名（可选）

在 `~/.zshrc` 或 `~/.bashrc` 中添加：

```bash
# Docker 脚本快捷方式
alias dexec='docker exec -it campus_backend'
alias dpython='docker exec -it campus_backend python'

# 使用示例
dpython scripts/python/init_devices.py
dexec bash
```

### 2. 查看脚本输出

```bash
# 实时查看日志
docker logs -f campus_backend

# 只看最近 100 行
docker logs --tail=100 campus_backend
```

### 3. 后台运行长时间脚本

```bash
# 使用 -d 标志后台运行
docker exec -d campus_backend python scripts/python/simulator_unified.py

# 查看是否在运行
docker exec campus_backend ps aux | grep simulator
```

### 4. 传递参数给脚本

```bash
# 如果脚本支持参数
docker exec -it campus_backend python scripts/python/simulator_unified.py --duration 60 --interval 5
```

---

## 🔍 故障排查

### 问题 1：容器未运行

```bash
# 错误：Error response from daemon: Container ... is not running

# 解决：启动容器
docker compose up -d
```

### 问题 2：容器名称不对

```bash
# 错误：Error: No such container: campus_backend

# 查看容器名称
docker compose ps

# 使用正确的名称
docker exec -it <实际容器名> python scripts/python/init_devices.py
```

### 问题 3：脚本文件不存在

```bash
# 错误：python: can't open file 'scripts/python/init_devices.py'

# 检查容器内的文件
docker exec -it campus_backend ls -la scripts/python/

# 确保工作目录正确
docker exec -it campus_backend pwd
```

### 问题 4：权限问题

```bash
# 某些操作可能需要特定权限

# 检查容器内用户
docker exec -it campus_backend whoami

# 如果需要 root 权限
docker exec -it -u root campus_backend python scripts/python/some_script.py
```

---

## 📝 脚本说明

### init_devices.py
- **功能**：初始化测试设备
- **用途**：首次使用时创建示例设备
- **执行时间**：< 1 秒

### simulator_unified.py
- **功能**：模拟设备数据上报
- **用途**：生成测试数据，测试系统功能
- **执行时间**：持续运行（Ctrl+C 停止）

### create_admin.py
- **功能**：创建管理员账号
- **用途**：添加新的管理员用户
- **执行时间**：< 1 秒

### clear_db.py
- **功能**：清空数据库
- **用途**：重置数据（⚠️ 危险操作）
- **执行时间**：< 5 秒

### reset_system.py
- **功能**：完整系统重置
- **用途**：清空并重新初始化系统
- **执行时间**：< 10 秒

### stress_test.py
- **功能**：API 压力测试
- **用途**：测试系统性能
- **执行时间**：根据配置，通常 1-5 分钟

---

## 🎯 常见使用场景

### 场景 1：首次使用系统

```bash
# 1. 启动服务
./fast_start.sh

# 2. 初始化设备
docker exec -it campus_backend python scripts/python/init_devices.py

# 3. 启动模拟器生成数据
docker exec -d campus_backend python scripts/python/simulator_unified.py

# 4. 访问系统
open http://localhost:8088/docs
```

### 场景 2：开发测试

```bash
# 1. 清空旧数据
docker exec -it campus_backend python scripts/python/clear_db.py

# 2. 重新初始化
docker exec -it campus_backend python scripts/python/init_devices.py

# 3. 生成测试数据
docker exec -it campus_backend python scripts/python/simulator_unified.py
```

### 场景 3：性能测试

```bash
# 1. 确保有足够数据
docker exec -d campus_backend python scripts/python/simulator_unified.py

# 2. 运行压力测试
docker exec -it campus_backend python scripts/python/stress_test.py

# 3. 查看系统资源
docker stats
```

---

## 📚 相关文档

- [README.md](../../README.md) - 完整项目文档
- [快速启动指南](../01-新手入门/快速启动指南.md) - 详细启动教程
- [scripts/README.md](../../scripts/README.md) - 脚本详细说明
- [根目录结构说明](../07-快速参考/根目录结构说明.md) - 根目录与各目录说明

---

**💡 提示**：使用 Docker 运行脚本是推荐的方式，可以避免本地环境配置问题！
