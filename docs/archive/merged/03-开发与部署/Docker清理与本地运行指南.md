# Docker 清理与本地运行指南

生成时间：2026-01-24

## 📋 项目当前状态分析

### 项目支持两种运行方式：

1. **🐳 Docker 容器化运行**（推荐用于生产环境）
   - 使用 `docker-compose.yml` 配置
   - 包含：数据库、Redis、MQTT、后端应用
   - 优点：环境隔离、一键部署、跨平台

2. **💻 本地直接运行**（推荐用于开发调试）
   - 使用 `run.py` 启动
   - 需要本地安装：PostgreSQL、Redis、Mosquitto
   - 优点：调试方便、开发快速

---

## 🔍 如何判断当前运行方式

### 方法1：检查Docker容器
```bash
docker ps -a
```

如果看到以下容器，说明正在使用Docker：
- `mine_energy_db` - TimescaleDB数据库
- `mine_mqtt` - Mosquitto MQTT服务
- `ems_redis` - Redis缓存
- `mine_backend` - FastAPI后端（可选）

### 方法2：检查端口占用
```bash
# macOS/Linux
lsof -i :5433  # 数据库端口
lsof -i :6379  # Redis端口
lsof -i :1883  # MQTT端口
lsof -i :8088  # 后端API端口

# 或使用
netstat -an | grep -E "5433|6379|1883|8088"
```

### 方法3：检查进程
```bash
# 查看Python进程
ps aux | grep "python.*run.py"

# 查看Docker进程
ps aux | grep docker
```

---

## 🧹 完整清除 Docker 容器

### 方法一：使用 docker-compose（推荐）

#### 1. 停止并删除所有服务
```bash
cd /Users/todo/MineEnergySystem
docker-compose down
```

#### 2. 停止并删除，同时删除数据卷
```bash
# ⚠️ 警告：这会删除所有数据！
docker-compose down -v
```

#### 3. 停止并删除，包括镜像
```bash
# ⚠️ 警告：会删除数据和镜像！
docker-compose down -v --rmi all
```

---

### 方法二：手动删除容器

#### 1. 停止所有相关容器
```bash
docker stop mine_energy_db mine_mqtt ems_redis mine_backend
```

#### 2. 删除所有相关容器
```bash
docker rm mine_energy_db mine_mqtt ems_redis mine_backend
```

#### 3. 删除相关镜像（可选）
```bash
docker rmi timescale/timescaledb:latest-pg14
docker rmi eclipse-mosquitto:2.0
docker rmi redis:7.0-alpine
docker rmi mineenergysystem_backend  # 如果存在
```

#### 4. 删除数据卷
```bash
# 查看数据卷
docker volume ls

# 删除项目相关的数据卷
docker volume rm mineenergysystem_redis_data

# 或删除所有未使用的数据卷
docker volume prune
```

#### 5. 删除网络
```bash
docker network rm mineenergysystem_app_network
```

---

### 方法三：一键清理脚本

创建清理脚本 `scripts/shell/cleanup_docker.sh`：

```bash
#!/bin/bash

echo "🧹 开始清理 Docker 容器和资源..."

# 停止容器
echo "1️⃣ 停止所有容器..."
docker stop mine_energy_db mine_mqtt ems_redis mine_backend 2>/dev/null || true

# 删除容器
echo "2️⃣ 删除容器..."
docker rm mine_energy_db mine_mqtt ems_redis mine_backend 2>/dev/null || true

# 删除镜像（可选，取消注释启用）
# echo "3️⃣ 删除镜像..."
# docker rmi timescale/timescaledb:latest-pg14 2>/dev/null || true
# docker rmi eclipse-mosquitto:2.0 2>/dev/null || true
# docker rmi redis:7.0-alpine 2>/dev/null || true

# 删除数据卷
echo "3️⃣ 删除数据卷..."
docker volume rm mineenergysystem_redis_data 2>/dev/null || true

# 删除网络
echo "4️⃣ 删除网络..."
docker network rm mineenergysystem_app_network 2>/dev/null || true

# 清理未使用的资源
echo "5️⃣ 清理未使用的资源..."
docker system prune -f

echo "✅ Docker 清理完成！"
echo ""
echo "💡 提示："
echo "   - 容器数据已删除"
echo "   - 镜像保留（需要时可手动删除）"
echo "   - 本地代码和配置文件未受影响"
```

使用方法：
```bash
chmod +x scripts/shell/cleanup_docker.sh
./scripts/shell/cleanup_docker.sh
```

---

## 🚀 本地运行配置指南

### 前置条件

本地运行需要安装以下服务：

#### 1. PostgreSQL / TimescaleDB
```bash
# macOS (使用 Homebrew)
brew install postgresql@14
brew services start postgresql@14

# 或安装 TimescaleDB
brew tap timescale/tap
brew install timescaledb
timescaledb-tune --quiet --yes
brew services start postgresql@14
```

#### 2. Redis
```bash
# macOS
brew install redis
brew services start redis
```

#### 3. Mosquitto (MQTT)
```bash
# macOS
brew install mosquitto
brew services start mosquitto
```

---

### 配置步骤

#### 1. 创建数据库
```bash
# 连接PostgreSQL
psql postgres

# 创建数据库和用户
CREATE DATABASE mine_energy;
CREATE USER admin WITH PASSWORD 'password123';
GRANT ALL PRIVILEGES ON DATABASE mine_energy TO admin;
\q

# 启用TimescaleDB扩展（如果使用TimescaleDB）
psql -d mine_energy
CREATE EXTENSION IF NOT EXISTS timescaledb;
\q
```

#### 2. 配置环境变量

创建 `.env` 文件（从 `env.example` 复制）：
```bash
cp env.example .env
```

编辑 `.env` 文件，修改为本地配置：
```ini
# 应用基础配置
APP_NAME=煤矿综合能源管理系统
APP_VERSION=2.0.0
DEBUG=True

# 数据库配置（本地PostgreSQL）
DATABASE_URL=postgresql://admin:password123@localhost:5432/mine_energy

# Redis配置（本地Redis）
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# MQTT配置（本地Mosquitto）
MQTT_BROKER=127.0.0.1
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TOPIC=mine/telemetry
MQTT_TOPIC_WILDCARD=mine/device/+/telemetry

# JWT安全配置
SECRET_KEY=your-secret-key-here-min-32-characters-long
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API服务配置
HOST=127.0.0.1
PORT=8088
RELOAD=True
WORKERS=1

# CORS配置
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173","http://localhost:3000"]

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

#### 3. 安装Python依赖
```bash
# 创建虚拟环境（如果还没有）
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 4. 初始化数据库
```bash
# 运行数据库初始化脚本（如果有）
python scripts/python/rebuild_database.py

# 创建管理员账号
python scripts/python/create_admin.py
```

#### 5. 启动后端
```bash
python run.py
```

#### 6. 启动前端
```bash
cd frontend
npm install  # 首次运行
npm run dev
```

---

## 📊 端口对比

| 服务 | Docker端口 | 本地端口 | 说明 |
|-----|-----------|---------|------|
| PostgreSQL | 5433 | 5432 | Docker映射到5433避免冲突 |
| Redis | 6379 | 6379 | 相同 |
| MQTT | 1883 | 1883 | 相同 |
| 后端API | 8088 | 8088 | 相同 |
| 前端 | - | 5173 | 前端始终本地运行 |

---

## 🔄 切换运行方式

### 从 Docker 切换到本地

1. **停止Docker服务**
```bash
docker-compose down
```

2. **启动本地服务**
```bash
# 启动PostgreSQL
brew services start postgresql@14

# 启动Redis
brew services start redis

# 启动Mosquitto
brew services start mosquitto
```

3. **修改 .env 文件**
- 确保 `DATABASE_URL` 使用 `localhost:5432`
- 确保 `MQTT_BROKER` 使用 `127.0.0.1`
- 确保 `REDIS_URL` 使用 `localhost:6379`

4. **启动应用**
```bash
python run.py
```

---

### 从本地切换到 Docker

1. **停止本地服务**
```bash
brew services stop postgresql@14
brew services stop redis
brew services stop mosquitto
```

2. **启动Docker**
```bash
docker-compose up -d
```

---

## 🗑️ 清理本地数据

### 删除数据库数据
```bash
# 进入PostgreSQL
psql postgres

# 删除数据库
DROP DATABASE mine_energy;

# 重新创建
CREATE DATABASE mine_energy;
GRANT ALL PRIVILEGES ON DATABASE mine_energy TO admin;
```

### 删除Redis数据
```bash
redis-cli FLUSHALL
```

### 删除日志和缓存
```bash
# 删除日志文件
rm -rf logs/*

# 删除Python缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

---

## 💡 最佳实践建议

### 开发环境（推荐本地运行）
✅ 优点：
- 调试方便
- 热重载快
- 直接访问数据库
- 开发效率高

❌ 缺点：
- 需要安装多个服务
- 环境配置复杂

**推荐配置：**
- 后端：本地 Python
- 前端：本地 npm dev
- 数据库/Redis/MQTT：可以用Docker或本地

---

### 生产环境（推荐Docker运行）
✅ 优点：
- 环境一致
- 部署简单
- 易于扩展
- 资源隔离

❌ 缺点：
- 调试稍麻烦
- 需要Docker知识

---

## 🛠️ 常用命令速查

### Docker 命令
```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend

# 重启服务
docker-compose restart

# 查看容器状态
docker-compose ps

# 进入容器
docker exec -it mine_energy_db bash
docker exec -it mine_backend bash
```

### 本地服务命令
```bash
# PostgreSQL
brew services start/stop/restart postgresql@14
psql -d mine_energy -U admin

# Redis
brew services start/stop/restart redis
redis-cli

# Mosquitto
brew services start/stop/restart mosquitto
mosquitto_sub -t '#' -v
```

---

## 🚨 常见问题

### Q1: Docker端口被占用
```bash
# 检查端口占用
lsof -i :5433

# 修改 docker-compose.yml 中的端口映射
ports:
  - "15433:5432"  # 改用其他端口
```

### Q2: Docker数据丢失
```bash
# 检查数据卷
docker volume ls

# 备份数据卷
docker run --rm -v mineenergysystem_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz /data
```

### Q3: 本地服务无法启动
```bash
# 检查服务状态
brew services list

# 查看服务日志
brew services info postgresql@14
tail -f /usr/local/var/log/postgres.log
```

---

## 📝 总结

| 操作 | 命令 |
|-----|------|
| **完全清除Docker** | `docker-compose down -v --rmi all` |
| **保留镜像清除** | `docker-compose down -v` |
| **仅停止容器** | `docker-compose down` |
| **启动本地开发** | `source venv/bin/activate && python run.py` |
| **切换到Docker** | `docker-compose up -d` |

---

**选择建议：**
- 👨‍💻 **日常开发**：使用本地运行（调试方便）
- 🚀 **生产部署**：使用Docker运行（环境一致）
- 🔄 **团队协作**：使用Docker运行（避免环境差异）

---

**需要帮助？** 随时询问！
