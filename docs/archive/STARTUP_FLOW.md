# MineEnergySystem 启动流程详解

本文档详细说明从安装 Docker 到系统完全启动的完整流程。

---

## 📋 目录

1. [前置准备](#前置准备)
2. [启动命令](#启动命令)
3. [Docker Compose 启动流程](#docker-compose-启动流程)
4. [服务启动顺序](#服务启动顺序)
5. [后端应用启动流程](#后端应用启动流程)
6. [服务连接关系](#服务连接关系)
7. [验证流程](#验证流程)
8. [启动时间线](#启动时间线)

---

## 🔧 前置准备

### 1. 安装 Docker Desktop

**步骤**：
1. 下载 Docker Desktop：https://www.docker.com/products/docker-desktop/
2. 安装并启动 Docker Desktop
3. 等待 Docker 完全启动（菜单栏图标不再闪烁）

**验证**：
```bash
docker --version
docker compose version
docker info
```

### 2. 项目准备

**目录结构**：
```
MineEnergySystem/
├── docker-compose.yml    # Docker 编排配置
├── Dockerfile            # 后端镜像构建文件
├── start.sh              # 启动脚本
├── .env                  # 环境变量（可选）
└── ...
```

**检查**：
- ✅ Docker Desktop 运行中
- ✅ 项目目录存在
- ✅ `docker-compose.yml` 存在

---

## 🚀 启动命令

### 方式一：使用启动脚本（推荐）

```bash
cd /Users/todo/MineEnergySystem
./start.sh
```

### 方式二：直接使用 Docker Compose

```bash
cd /Users/todo/MineEnergySystem
docker compose up -d --build
```

---

## 🐳 Docker Compose 启动流程

### 阶段 1：环境检查（start.sh）

```
1. 检查 Docker 是否安装
   ├─ 未安装 → 提示安装 → 退出
   └─ 已安装 → 继续

2. 检查 Docker 是否运行
   ├─ 未运行 → 提示启动 → 退出
   └─ 已运行 → 继续

3. 创建必要目录
   ├─ mosquitto/data
   ├─ mosquitto/log
   ├─ logs
   └─ pg_data

4. 检查端口占用
   ├─ 8088 (后端)
   ├─ 5433 (数据库)
   ├─ 6379 (Redis)
   └─ 1883 (MQTT)
```

### 阶段 2：Docker Compose 启动

```
docker compose up -d --build
│
├─ 1. 创建网络 (app_network)
│   └─ 类型: bridge
│
├─ 2. 创建卷 (redis_data)
│   └─ 类型: local
│
└─ 3. 启动服务（按依赖顺序）
    ├─ 数据库 (db)
    ├─ Redis (redis)
    ├─ MQTT (mqtt)
    └─ 后端 (backend) - 等待依赖服务就绪
```

---

## 📦 服务启动顺序

### 步骤 1：启动基础服务（并行）

```
┌─────────────────┐
│   数据库 (db)   │
│  TimescaleDB    │
└─────────────────┘
        │
        ├─ 拉取镜像 (timescale/timescaledb:latest-pg14)
        ├─ 启动容器 (mine_energy_db)
        ├─ 初始化数据库
        ├─ 健康检查启动 (start_period: 10s)
        └─ 健康检查通过 ✅
            └─ 等待被依赖...

┌─────────────────┐
│   Redis (redis) │
│   Redis 7.0     │
└─────────────────┘
        │
        ├─ 拉取镜像 (redis:7.0-alpine)
        ├─ 启动容器 (ems_redis)
        ├─ 加载持久化数据 (redis_data volume)
        ├─ 健康检查启动 (start_period: 5s)
        └─ 健康检查通过 ✅
            └─ 等待被依赖...

┌─────────────────┐
│   MQTT (mqtt)   │
│  Mosquitto 2.0  │
└─────────────────┘
        │
        ├─ 拉取镜像 (eclipse-mosquitto:2.0)
        ├─ 启动容器 (mine_mqtt)
        ├─ 加载配置文件 (mosquitto/config/mosquitto.conf)
        ├─ 健康检查启动 (start_period: 5s)
        └─ 健康检查通过 ✅
            └─ 等待被依赖...
```

### 步骤 2：启动后端服务（等待依赖就绪）

```
┌─────────────────┐
│ 后端 (backend)  │
│   FastAPI       │
└─────────────────┘
        │
        ├─ 构建镜像（首次启动）
        │   ├─ 使用 Dockerfile
        │   ├─ 安装系统依赖
        │   ├─ 安装 Python 包
        │   └─ 复制项目代码
        │
        ├─ 等待依赖服务健康
        │   ├─ 等待 db: service_healthy ✅
        │   ├─ 等待 redis: service_healthy ✅
        │   └─ 等待 mqtt: service_healthy ✅
        │
        ├─ 启动容器 (mine_backend)
        │   └─ 设置环境变量
        │       ├─ DATABASE_URL=postgresql://admin:password123@db:5432/mine_energy
        │       ├─ REDIS_URL=redis://redis:6379/0
        │       ├─ MQTT_BROKER=mqtt
        │       └─ ...
        │
        └─ 执行启动命令: python run.py
            └─ 进入后端应用启动流程...
```

---

## 🔄 后端应用启动流程

### run.py 执行流程

```
python run.py
│
└─ uvicorn.run()
    │
    ├─ 加载配置 (app.core.settings)
    │   ├─ 从环境变量读取
    │   └─ 从 .env 文件读取（如果存在）
    │
    └─ 启动 ASGI 应用 (app.main:app)
        └─ 进入 FastAPI 生命周期...
```

### FastAPI 应用启动（app/main.py）

```
FastAPI 应用启动
│
├─ 阶段 1: 生命周期 - 启动阶段 (lifespan)
    │
    ├─ 1.1 初始化数据库
    │   └─ init_db()
    │       ├─ SQLModel.metadata.create_all(engine)
    │       │   └─ 创建所有表结构
    │       │
    │       └─ _try_enable_timescaledb_hypertable()
    │           └─ 将 devicedata 转换为 hypertable
    │               └─ 日志: "✅ 数据库初始化完成"
    │
    ├─ 1.2 连接 Redis
    │   └─ RedisClient.get_client()
    │       ├─ 创建连接
    │       ├─ await redis.ping()
    │       └─ 日志: "✅ Redis连接成功"
    │
    ├─ 1.3 启动 MQTT 监听
    │   └─ start_mqtt_background()
    │       ├─ 连接到 MQTT Broker (mqtt:1883)
    │       ├─ 订阅主题 (mine/device/+/telemetry)
    │       ├─ 启动消息处理循环
    │       └─ 日志: "✅ MQTT服务启动完成"
    │
    └─ 1.4 系统就绪
        └─ 日志: "✨ 系统就绪"
│
├─ 阶段 2: 应用配置
    │
    ├─ 2.1 注册异常处理器
    │   └─ register_exception_handlers(app)
    │
    ├─ 2.2 配置 CORS
    │   └─ CORSMiddleware
    │       └─ 允许的来源: http://localhost:5173 等
    │
    └─ 2.3 注册路由
        ├─ /auth/*          (认证)
        ├─ /devices/*       (设备管理)
        ├─ /telemetry/*     (遥测数据)
        ├─ /alarms/*        (报警管理)
        ├─ /analysis/*      (数据分析)
        ├─ /fdd/*           (故障诊断)
        ├─ /reports/*       (报表导出)
        └─ /ws              (WebSocket)
│
└─ 阶段 3: 启动 HTTP 服务器
    │
    └─ Uvicorn 启动监听
        ├─ Host: 0.0.0.0
        ├─ Port: 8088
        └─ 等待 HTTP 请求...
```

---

## 🔗 服务连接关系

### 网络拓扑

```
┌─────────────────────────────────────────────────────┐
│            Docker 网络 (app_network)                │
│                                                      │
│  ┌──────────────┐    ┌──────────────┐              │
│  │   Backend    │───▶│  Database    │              │
│  │  :8088       │    │  :5432       │              │
│  │              │    │  (db)        │              │
│  └──────────────┘    └──────────────┘              │
│         │                                             │
│         ├──────────────┐                             │
│         │              │                             │
│         ▼              ▼                             │
│  ┌──────────────┐  ┌──────────────┐                │
│  │    Redis     │  │     MQTT     │                │
│  │  :6379       │  │  :1883       │                │
│  │  (redis)     │  │  (mqtt)      │                │
│  └──────────────┘  └──────────────┘                │
│                                                       │
└─────────────────────────────────────────────────────┘
         │                    │              │
         │                    │              │
         ▼                    ▼              ▼
    Host:8088          Host:5433      Host:6379
                                              Host:1883
```

### 连接配置

| 服务 | 连接目标 | 连接地址 | 说明 |
|------|----------|----------|------|
| Backend → Database | db:5432 | `postgresql://admin:password123@db:5432/mine_energy` | 容器内网络 |
| Backend → Redis | redis:6379 | `redis://redis:6379/0` | 容器内网络 |
| Backend → MQTT | mqtt:1883 | `mqtt:1883` | 容器内网络 |
| Host → Backend | localhost:8088 | `http://localhost:8088` | 端口映射 |
| Host → Database | localhost:5433 | `postgresql://admin:password123@localhost:5433/mine_energy` | 端口映射 |

---

## ✅ 验证流程

### 1. 容器状态验证

```bash
# 查看所有容器状态
docker compose ps

# 预期输出：
# NAME              STATUS          PORTS
# mine_backend      Up (healthy)    0.0.0.0:8088->8088/tcp
# mine_energy_db    Up (healthy)    0.0.0.0:5433->5432/tcp
# ems_redis         Up (healthy)    0.0.0.0:6379->6379/tcp
# mine_mqtt         Up (healthy)    0.0.0.0:1883->1883/tcp, 0.0.0.0:9001->9001/tcp
```

### 2. 后端 API 验证

```bash
# 测试 API 文档
curl http://localhost:8088/docs

# 或浏览器访问
# http://localhost:8088/docs
```

### 3. 数据库验证

```bash
# 测试数据库连接
docker exec -it mine_energy_db psql -U admin -d mine_energy -c "SELECT 1;"

# 查看表结构
docker exec -it mine_energy_db psql -U admin -d mine_energy -c "\dt"
```

### 4. Redis 验证

```bash
# 测试 Redis 连接
docker exec -it ems_redis redis-cli ping

# 预期输出：PONG
```

### 5. MQTT 验证

```bash
# 订阅 MQTT 主题（测试）
docker exec -it mine_mqtt mosquitto_sub -h localhost -t 'mine/#' -v

# 发布测试消息
docker exec -it mine_mqtt mosquitto_pub -h localhost -t 'mine/test' -m 'hello'
```

### 6. 后端日志验证

```bash
# 查看后端日志
docker compose logs backend | grep -E "✅|启动|就绪"

# 预期看到：
# ✅ 数据库初始化完成
# ✅ Redis连接成功
# ✅ MQTT服务启动完成
# ✨ 系统就绪
```

---

## ⏱️ 启动时间线

### 首次启动（无缓存）

```
时间轴（分钟）：
0:00 ──────────────────────────────────────────────────
     │
     ├─ Docker Compose 开始
     │   ├─ 创建网络
     │   └─ 创建卷
     │
0:30 │
     ├─ 并行启动基础服务
     │   ├─ 下载 db 镜像 (~500MB) ──────────┐
     │   ├─ 下载 redis 镜像 (~30MB) ───────┤
     │   └─ 下载 mqtt 镜像 (~10MB) ────────┤
     │                                     │
2:00 │                                     │
     ├─ 镜像下载完成                        │
     │   ├─ db 启动中...                   │
     │   ├─ redis 启动中...                │
     │   └─ mqtt 启动中...                 │
     │                                     │
2:30 │                                     │
     ├─ 基础服务健康检查                   │
     │   ├─ db: 等待健康检查 (10s) ────────┤
     │   ├─ redis: 等待健康检查 (5s) ──────┤
     │   └─ mqtt: 等待健康检查 (5s) ───────┤
     │                                     │
3:00 │                                     │
     ├─ 基础服务就绪 ✅                    │
     │                                     │
     ├─ 构建后端镜像                       │
     │   ├─ 下载 Python 基础镜像 (~150MB) ─┤
     │   ├─ 安装系统依赖                  │
     │   ├─ 安装 Python 包                │
     │   └─ 复制代码                       │
     │                                     │
5:00 │                                     │
     ├─ 后端镜像构建完成                   │
     │                                     │
     ├─ 启动后端容器                       │
     │   └─ 等待依赖服务就绪 ✅            │
     │                                     │
5:30 │                                     │
     ├─ 后端应用启动                       │
     │   ├─ 初始化数据库                  │
     │   ├─ 连接 Redis                    │
     │   ├─ 启动 MQTT 监听                │
     │   └─ 注册路由                      │
     │                                     │
6:00 │                                     │
     ├─ 系统就绪 ✅                        │
     │                                     │
     └─ 可用: http://localhost:8088/docs  │
```

### 后续启动（有缓存）

```
时间轴（秒）：
0:00 ──────────────────────────────────────────────────
     │
     ├─ Docker Compose 开始
     │
5:00 │
     ├─ 并行启动所有服务（使用缓存镜像）
     │   ├─ db 启动中...
     │   ├─ redis 启动中...
     │   ├─ mqtt 启动中...
     │   └─ backend 启动中...
     │
15:00 │
     ├─ 基础服务健康检查
     │
20:00 │
     ├─ 后端等待依赖就绪
     │
30:00 │
     ├─ 后端应用启动
     │   ├─ 初始化数据库 ✅
     │   ├─ 连接 Redis ✅
     │   └─ 启动 MQTT ✅
     │
40:00 │
     ├─ 系统就绪 ✅
     │
     └─ 可用: http://localhost:8088/docs
```

---

## 📝 关键文件说明

### 启动相关文件

| 文件 | 作用 |
|------|------|
| `start.sh` | 启动脚本（环境检查 + 启动服务）|
| `docker-compose.yml` | Docker 编排配置（定义所有服务）|
| `Dockerfile` | 后端镜像构建文件 |
| `run.py` | 后端应用入口（启动 Uvicorn）|
| `app/main.py` | FastAPI 应用主文件（生命周期管理）|

### 配置相关文件

| 文件 | 作用 |
|------|------|
| `.env` | 环境变量配置（可选）|
| `app/core/settings.py` | 配置管理（读取环境变量）|
| `mosquitto/config/mosquitto.conf` | MQTT 配置 |

---

## 🔍 启动问题排查

### 查看启动日志

```bash
# 查看所有服务日志
docker compose logs

# 查看特定服务日志
docker compose logs backend
docker compose logs db

# 实时查看日志
docker compose logs -f

# 查看最近 100 行
docker compose logs --tail=100
```

### 常见问题

1. **容器无法启动** → 查看 `TROUBLESHOOTING.md`
2. **启动慢** → 查看 `STARTUP_OPTIMIZATION.md`
3. **端口被占用** → 修改 `docker-compose.yml` 端口映射

---

## 🎯 总结

**完整启动流程**：
1. ✅ 前置准备（Docker Desktop）
2. ✅ 运行启动脚本（`./start.sh`）
3. ✅ Docker Compose 启动服务
4. ✅ 基础服务并行启动（db, redis, mqtt）
5. ✅ 后端等待依赖就绪
6. ✅ 后端应用启动（数据库初始化、连接 Redis、启动 MQTT）
7. ✅ 系统就绪，可以访问

**访问地址**：
- 后端 API 文档：http://localhost:8088/docs
- 后端 ReDoc：http://localhost:8088/redoc

---

**现在你了解了完整的启动流程！** 🚀
