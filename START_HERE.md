# 🚀 从这里开始！

> 欢迎使用煤矿综合能源管理系统！这份文档帮助您在 3 分钟内启动系统。

---

## ⚡ 快速启动（3 步）

### 1️⃣ 确保 Docker 已安装并运行

```bash
# 检查 Docker 是否安装
docker --version

# 检查 Docker 是否运行
docker info
```

**没有 Docker？** 
- macOS: [下载 Docker Desktop](https://www.docker.com/products/docker-desktop/)
- 或使用 Homebrew: `brew install --cask docker`

### 2️⃣ 一键启动系统

```bash
# 方式A：完整构建（首次使用 或 修改了依赖）
./bin/quick_start.sh

# 方式B：快速启动（日常使用，推荐）⭐
./bin/fast_start.sh
```

**首次启动** 需要 3-5 分钟（下载镜像 + 构建）  
**后续启动** 只需 10-30 秒（使用 `fast_start.sh`）

### 3️⃣ 访问系统

```bash
# 打开 API 文档（浏览器）
open http://localhost:8088/docs

# 或在浏览器中访问
# http://localhost:8088/docs
```

**默认账号**：
- 用户名：`admin`
- 密码：`123456`

#### 💡 启动前端（可选）

如果需要 Web 界面：

```bash
# 方式A：使用快捷脚本
./bin/start_frontend.sh

# 方式B：手动启动
cd frontend
npm run dev

# 访问前端界面
# http://localhost:5173
```

---

## ✅ 验证启动成功

```bash
# 测试健康检查
curl http://localhost:8088/health

# 查看服务状态
docker compose ps

# 所有容器的 STATUS 应该显示 "Up"
```

---

## 📚 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看后端日志（实时）
docker compose logs -f backend

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 查看服务状态（脚本）
./bin/check_system.sh
```

---

## ❓ 启动失败？

### Docker 未运行
```bash
# macOS - 启动 Docker Desktop
open /Applications/Docker.app
# 等待菜单栏图标不再闪烁
```

### 端口被占用
```bash
# 查看端口占用
lsof -i :8088

# 停止旧服务
docker compose down

# 重新启动
./bin/quick_start.sh
```

### 查看详细错误
```bash
# 查看容器日志
docker compose logs backend
docker compose logs db
```

---

## 📖 更多文档

- **[快速启动指南](./docs/快速启动指南.md)** - 详细启动教程 ⭐
- **[DOCKER_SCRIPTS.md](./docs/DOCKER_SCRIPTS.md)** - 使用 Docker 运行脚本 🐳
- **[README.md](./README.md)** - 完整项目文档
- **[INSTALL.md](./docs/INSTALL.md)** - 安装指南
- **[bin/README.md](./bin/README.md)** - 脚本使用说明 🔧
- **[docs/README.md](./docs/README.md)** - 文档索引
- **[LSTM完整使用指南](./docs/LSTM完整使用指南.md)** - AI 预测功能

---

## 🎯 下一步做什么？

### 1. 测试 API
访问 http://localhost:8088/docs 浏览所有 API 接口

### 2. 运行设备模拟器

**方式A：使用快捷脚本（推荐）⭐**
```bash
# 一键运行模拟器
./bin/run_simulator.sh

# 按 Ctrl+C 停止
```

**方式B：使用 Docker 命令**
```bash
# 在 Docker 容器中运行
docker exec mine_backend bash -c \
  "MQTT_BROKER=mqtt API_BASE=http://localhost:8088 python -u scripts/python/simulator.py"
```

**方式C：本地运行（需要先安装依赖）**
```bash
# 激活虚拟环境
source venv/bin/activate
# 安装依赖（首次需要）
pip install -r requirements.txt
# 运行模拟器
python scripts/python/simulator.py
```

### 3. 初始化测试设备

**方式A：使用快捷脚本（推荐）⭐**
```bash
./bin/init_devices.sh
```

**方式B：使用 Docker 命令**
```bash
docker exec mine_backend bash -c \
  "API_BASE=http://localhost:8088 python scripts/python/init_devices.py"
```

**方式C：本地运行**
```bash
source venv/bin/activate
python scripts/python/init_devices.py
```

### 4. 使用 LSTM 预测功能
查看 [LSTM完整使用指南](./docs/LSTM完整使用指南.md)

---

## 💡 提示

- 🔑 **生产环境**请务必修改默认密码！
- 📊 **API 文档**非常详细，建议仔细阅读
- 🐛 **遇到问题**先查看日志：`docker compose logs -f`
- 📝 **详细文档**在 `docs/` 目录下

---

## 🆘 获取帮助

- **查看日志**: `docker compose logs -f`
- **查看状态**: `docker compose ps`
- **完全重置**: `docker compose down -v` (⚠️ 会删除数据)
- **故障排查**: 查看 [README.md - 故障排查](./README.md#-故障排查)
- **提交问题**: [GitHub Issues](https://github.com/your-repo/MineEnergySystem/issues)

---

**🎉 祝您使用愉快！**

如有问题，请查看：
- 📘 [快速启动指南](./docs/快速启动指南.md)
- 📗 [完整 README](./README.md)
- 📕 [文档索引](./docs/README.md)
