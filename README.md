# 煤矿综合能源管理系统（MineEnergySystem）

[![FastAPI](https://img.shields.io/badge/FastAPI-2.0-009688.svg)](https://fastapi.tiangolo.com)
[![Vue3](https://img.shields.io/badge/Vue-3.x-4FC08D.svg)](https://vuejs.org)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-PostgreSQL-336791.svg)](https://www.timescale.com)
[![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-3C5280.svg)](https://mosquitto.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> 基于 FastAPI + Vue3 + TimescaleDB + MQTT 的工业级能源监控和管理平台

---

## ⚡ 快速开始（3分钟上手）

> 💡 **新手提示**：首次使用建议阅读 [快速启动指南](./docs/01-新手入门/快速启动指南.md)

```bash
# 1️⃣ 克隆项目
git clone https://github.com/your-repo/MineEnergySystem.git
cd MineEnergySystem

# 2️⃣ 一键启动（需要 Docker Desktop）
./bin/fast_start.sh   # 日常使用（有缓存时最快）⭐
./scripts/shell/start.sh   # 或完整启动/首次构建

# 3️⃣ 访问系统
# 打开浏览器访问: http://localhost:8088/docs
# 默认账号: admin / 123456
```

**前置条件**: 已安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/) ✅

**启动遇到问题？** → 查看 [故障排查](#-故障排查) 或 [快速启动指南](./docs/01-新手入门/快速启动指南.md)

---

## 📖 目录

- [快速开始](#-快速开始3分钟上手) ⭐
- [启动方式选择](#-启动方式选择) 🔥
  - [开发环境启动](#1️⃣-开发环境启动推荐)
  - [生产部署启动](#2️⃣-生产部署启动)
- [项目简介](#-项目简介)
- [技术栈](#-技术栈)
- [功能特性](#-功能特性)
- [系统架构](#-系统架构)
- [API 文档](#-api-文档)
- [开发指南](#-开发指南)
- [运维管理](#-运维管理)
- [故障排查](#-故障排查) 🔧
- [项目路线图](#-项目路线图)

---

## 🎯 项目简介

**煤矿综合能源管理系统**是一套面向工业场景的现代化能源监控和管理解决方案，适用于煤矿、工厂、园区等场景：

### 核心功能

- ⚡ **实时能耗监控** - 设备电压、电流、功率、能耗数据实时采集
- 📊 **数据分析统计** - 能耗趋势、峰谷分析、设备效率评估
- 🚨 **智能报警系统** - 过载、欠压、异常自动检测与通知
- 🔧 **远程设备控制** - 通过 MQTT 协议远程控制设备启停
- 📈 **可视化大屏** - ECharts 实时图表展示，WebSocket 实时推送
- 🔐 **权限管理** - JWT 认证 + 基于角色的访问控制
- 📥 **数据导出** - CSV 格式报表导出
- 🏥 **健康监控** - 系统健康检查，支持 Docker/K8s 部署

### 项目特点

- ✅ **生产就绪** - 完整的错误处理、日志记录、健康检查
- ✅ **高性能** - TimescaleDB 时序数据库，Redis 缓存加速
- ✅ **可扩展** - 分层架构设计，易于维护和扩展
- ✅ **Docker 化** - 一键启动所有服务，跨平台支持
- ✅ **文档完善** - 详细的 API 文档和开发指南

---

## 🛠️ 技术栈

### 后端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.10+ | 编程语言 |
| **FastAPI** | 0.104+ | 高性能 Web 框架 |
| **SQLModel** | 0.0.14 | ORM（基于 Pydantic + SQLAlchemy）|
| **TimescaleDB** | 2.x | 时序数据库（基于 PostgreSQL）|
| **Redis** | 7.0 | 缓存 + 会话管理 |
| **MQTT** | 2.0 | 消息队列（Mosquitto）|
| **Uvicorn** | 最新 | ASGI 服务器 |
| **Loguru** | 0.7+ | 日志管理 |
| **Python-Jose** | 3.3+ | JWT 认证 |
| **Bcrypt** | 4.2+ | 密码加密 |

### 前端技术

| 技术 | 版本 | 用途 |
|------|------|------|
| **Vue** | 3.x | 前端框架 |
| **Vite** | 5.x | 构建工具 |
| **TypeScript** | 5.x | 类型安全 |
| **Pinia** | 2.x | 状态管理 |
| **Element Plus** | 2.x | UI 组件库 |
| **ECharts** | 5.x | 数据可视化 |

### 基础设施

- **Docker** - 容器化部署
- **Docker Compose** - 服务编排
- **Nginx** - 反向代理（生产环境）

---

## ✨ 功能特性

### 已实现功能

#### 1. 设备管理
- [x] 设备 CRUD 操作
- [x] 设备状态监控（在线/离线）
- [x] 设备分组管理
- [x] 设备远程控制（启动/停止）

#### 2. 数据采集
- [x] 实时遥测数据接收（MQTT）
- [x] 数据清洗和验证
- [x] 时序数据存储（TimescaleDB Hypertable）
- [x] 数据压缩策略（7天后自动压缩）
- [x] 支持模拟器（`simulator_unified.py`）与真实设备接入（MQTT 同主题；详见 [真实设备接入指南](./docs/02-功能使用/真实设备接入指南.md)）

#### 3. 报警系统
- [x] 阈值自动检测（电压、电流、功率）
- [x] 多级报警（警告/严重/紧急）
- [x] 报警历史查询
- [x] 报警确认和处理

#### 4. 数据分析
- [x] 能耗趋势分析（时/日/月）
- [x] 设备运行效率统计
- [x] 峰谷能耗分布
- [x] 自定义时间段查询

#### 5. 可视化
- [x] 实时数据大屏（WebSocket 推送）
- [x] ECharts 多维度图表
- [x] 设备拓扑图
- [x] 报警实时弹窗

#### 6. 系统管理
- [x] JWT Token 认证
- [x] 密码 Bcrypt 加密
- [x] 配置文件管理
- [x] 日志分级记录
- [x] 数据导出（CSV）
- [x] 系统健康检查

#### 7. 预测功能
- [x] 负荷预测（移动平均、线性回归、LSTM）
- [x] 风光预测（光伏、风电）
- [x] LSTM深度学习模型训练和预测
- [x] 多变量预测（电压、电流、功率）
- [x] 模型版本管理和对比
- [x] 超参数自动搜索
- [x] 定时自动训练任务
- [x] 模型性能评估（MAE、MAPE、RMSE）
- [x] 数据生成工具（用于训练和测试）

📖 **详细文档**: 查看 [docs/LSTM完整使用指南.md](./docs/LSTM完整使用指南.md)

### 规划中功能

- [ ] 单元测试和集成测试（进行中）
- [ ] API 限流保护
- [ ] 数据库迁移工具（Alembic）
- [ ] 性能监控（Prometheus）
- [ ] CI/CD 流程
- [ ] 故障诊断专家系统增强
- [ ] 移动端 App

📌 **距离实际应用还缺什么？** 见 [与实际应用的差距](./docs/05-架构与设计/与实际应用的差距.md)：安全（HTTPS、限流、RBAC）、测试与迁移、监控与告警、备份策略等清单与优先级。

---

## 🚀 启动方式选择

根据你的使用场景，选择合适的启动方式：

| 场景 | 启动方式 | 特点 | 适用人群 |
|------|---------|------|---------|
| 🔧 **日常开发** | [开发环境](#1️⃣-开发环境启动推荐) | 快速重启、热重载、方便调试 | 开发人员 |
| 🚀 **测试部署** | [Docker 完整部署](#2️⃣-生产部署启动) | 环境一致、一键启动 | 测试/运维 |
| 🏢 **生产环境** | [生产部署](#2️⃣-生产部署启动) | 稳定可靠、易于扩展 | 运维人员 |

---

### 1️⃣ 开发环境启动（推荐）

> 💡 **适用场景**：日常开发、代码调试、功能测试  
> ⚡ **优势**：启动快速（秒级）、支持热重载、方便打断点调试

#### 前置要求

- **Python**: 3.10+ ([下载](https://www.python.org/downloads/))
- **Node.js**: 16+ ([下载](https://nodejs.org/))
- **Docker Desktop**: 24.0+ ([下载](https://www.docker.com/products/docker-desktop/))

#### 步骤 1: 克隆项目并安装依赖

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/MineEnergySystem.git
cd MineEnergySystem

# 2. 创建并激活 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装 Python 依赖
pip install -r requirements.txt

# 4. 安装前端依赖（可选，如果需要前端开发）
cd frontend
npm install
cd ..
```

#### 步骤 2: 启动基础服务（Docker）

```bash
# 启动数据库、Redis、MQTT（不启动后端）
docker-compose up -d db redis mqtt

# 等待服务就绪（约 10-20 秒）
docker-compose ps

# 预期输出：db、redis、mqtt 都是 healthy 状态
```

#### 步骤 3: 启动后端（本地）

```bash
# 激活虚拟环境（如果还未激活）
source venv/bin/activate

# 启动后端开发服务器
python run.py

# 看到以下输出表示启动成功：
# INFO:     Uvicorn running on http://0.0.0.0:8088 (Press CTRL+C to quit)
# INFO:     Started reloader process
```

**访问后端**：
- API 文档：http://localhost:8088/docs
- 健康检查：http://localhost:8088/health

#### 步骤 4: 启动前端（可选）

```bash
# 新开一个终端
cd frontend
npm run dev

# 前端访问地址：http://localhost:5173
```

#### 开发环境配置说明

**环境变量**（自动使用本地配置）：
```bash
# 本地开发时，连接 Docker 中的基础服务
DATABASE_URL=postgresql://admin:password123@localhost:5433/mine_energy
REDIS_URL=redis://localhost:6379/0
MQTT_BROKER=localhost
MQTT_PORT=1883
```

#### 日常开发工作流

```bash
# 每天开始工作
cd MineEnergySystem

# 1. 启动基础服务（如果还未运行）
docker-compose up -d db redis mqtt

# 2. 激活虚拟环境并启动后端
source venv/bin/activate
python run.py

# 3. 修改代码后自动重载，无需重启

# 4. 结束工作时可以停止基础服务（可选）
docker-compose stop
```

#### 优势

✅ **快速重启**：后端启动只需 2-3 秒  
✅ **热重载**：修改代码自动生效  
✅ **方便调试**：可以直接打断点、查看变量  
✅ **低资源占用**：只运行必要的基础服务  
✅ **灵活配置**：可以随时修改代码和配置

---

### 2️⃣ 生产部署启动

> 🚀 **适用场景**：完整测试、预发布环境、生产部署  
> 🏢 **优势**：环境一致、自动化部署、易于维护

#### ⚠️ 企业部署

**如果您要部署到企业生产环境，请参考：**
- 📖 [企业部署完整指南](./docs/03-开发与部署/企业部署完整指南.md) - 详细的企业级部署步骤
- ⚡ [企业部署快速参考](./docs/03-开发与部署/企业部署快速参考.md) - 5分钟快速上手

**企业部署包含：**
- ✅ 生产环境配置（docker-compose.prod.yml）
- ✅ 安全加固（密码、密钥、防火墙）
- ✅ Nginx反向代理和HTTPS配置
- ✅ 数据备份和恢复脚本
- ✅ 监控和日志管理
- ✅ 高可用部署方案

#### 前置要求

- **Docker Desktop**: 24.0+ ([下载](https://www.docker.com/products/docker-desktop/))
- **可用端口**: 8088(后端) / 5433(数据库) / 6379(Redis) / 1883(MQTT)

#### 方式 A: 一键启动（推荐 ⭐）

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/MineEnergySystem.git
cd MineEnergySystem

# 2. 使用快速启动脚本
./bin/fast_start.sh

# 首次启动约需 3-5 分钟（下载镜像 + 构建）
# 后续启动只需 30-60 秒
```

#### 方式 B: 手动启动（了解细节）

```bash
# 1. 创建必要的目录
mkdir -p mosquitto/data mosquitto/log logs pg_data

# 2. 启动所有服务（包括后端）
docker-compose up -d --build

# 3. 查看服务状态
docker-compose ps

# 4. 查看后端日志
docker-compose logs -f backend
```

#### 启动成功验证

```bash
# 1. 检查所有服务状态
docker-compose ps
# 预期：所有服务都是 Up (healthy) 状态

# 2. 测试健康检查
curl http://localhost:8088/health
# 预期输出：{"status":"healthy", ...}

# 3. 访问 API 文档
open http://localhost:8088/docs
```

#### 生产环境配置

**环境变量**（在 `docker-compose.yml` 中配置）：
```yaml
environment:
  - DATABASE_URL=postgresql://admin:password123@db:5432/mine_energy
  - REDIS_URL=redis://redis:6379/0
  - MQTT_BROKER=mqtt
  - SECRET_KEY=your-secret-key-change-me  # ⚠️ 必须修改
  - DEBUG=False
  - LOG_LEVEL=INFO
```

**⚠️ 生产环境安全配置**：
```bash
# 1. 生成强密钥
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. 修改 docker-compose.yml 中的 SECRET_KEY

# 3. 修改默认数据库密码
# 编辑 docker-compose.yml 中的 POSTGRES_PASSWORD

# 4. 创建管理员账号（首次部署）
docker exec -it mine_backend python scripts/python/create_admin.py
```

#### 常用管理命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend    # 后端日志
docker-compose logs -f db         # 数据库日志
docker-compose logs -f            # 所有服务日志

# 重启服务
docker-compose restart backend    # 重启后端
docker-compose restart            # 重启所有服务

# 停止服务
docker-compose stop               # 停止（保留数据）
docker-compose down               # 停止并删除容器
docker-compose down -v            # 停止并删除数据卷（⚠️ 删除所有数据）

# 更新代码后重新部署
git pull
docker-compose up -d --build
```

#### 数据备份

```bash
# 备份数据库
docker exec mine_energy_db pg_dump -U admin mine_energy > backup_$(date +%Y%m%d).sql

# 备份并压缩
docker exec mine_energy_db pg_dump -U admin mine_energy | gzip > backup.sql.gz

# 恢复数据库
docker exec -i mine_energy_db psql -U admin mine_energy < backup.sql
```

#### 生产环境 Nginx 配置（可选）

```nginx
# /etc/nginx/sites-available/mine-energy
server {
    listen 80;
    server_name api.yourdomain.com;

    # API 转发
    location / {
        proxy_pass http://127.0.0.1:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket 支持
    location /ws {
        proxy_pass http://127.0.0.1:8088/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

### 📊 两种方式对比

| 对比项 | 开发环境 | 生产部署 |
|--------|---------|---------|
| **启动速度** | ⚡ 快（2-3秒） | 🐢 慢（30-60秒） |
| **代码修改** | ✅ 热重载 | ❌ 需重新构建 |
| **调试便利** | ✅ 可断点调试 | ⚠️ 需查看日志 |
| **环境隔离** | ⚠️ 部分隔离 | ✅ 完全隔离 |
| **资源占用** | 💚 小 | 💛 中等 |
| **部署一致性** | ❌ 依赖本地环境 | ✅ 完全一致 |
| **适用场景** | 🔧 开发调试 | 🚀 测试部署 |

---

### 💡 推荐使用方式

**个人开发者**：
```bash
# 使用开发环境，快速迭代
docker-compose up -d db redis mqtt
source venv/bin/activate
python run.py
```

**团队协作**：
```bash
# 基础服务用 Docker，后端本地运行
docker-compose up -d db redis mqtt
python run.py
```

**生产部署**：
```bash
# 完全使用 Docker，环境一致
docker-compose up -d --build
```

---

## 🔧 其他有用的命令

### 验证服务是否正常

```bash
# 1. 测试后端健康检查
curl http://localhost:8088/health

# 2. 访问 API 文档（浏览器）
open http://localhost:8088/docs

# 3. 测试数据库连接
docker exec -it mine_energy_db psql -U admin -d mine_energy -c "SELECT version();"

# 4. 测试 Redis
docker exec -it ems_redis redis-cli ping

# 5. 测试 MQTT
docker exec -it mine_mqtt mosquitto_sub -h localhost -t 'mine/#' -v
```

### 默认账号

系统首次启动会自动创建默认管理员账号：
- **用户名**: `admin`
- **密码**: `123456`

⚠️ **生产环境务必修改默认密码！**

### 使用脚本工具

```bash
# 查看所有可用脚本
ls scripts/shell/
ls scripts/python/

# 设备模拟器
python scripts/python/simulator_unified.py

# 创建管理员
python scripts/python/create_admin.py

# 更多脚本使用说明
cat scripts/README.md
```

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端层 (Vue3 + Vite)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ 设备监控 │  │ 数据分析 │  │ 报警管理 │  │ 系统设置 │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────────▼────────────────────────────────────────┐
│                    API 网关 (FastAPI)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  /auth  /devices  /telemetry  /alarms  /analysis  /health│  │
│  └──────────────────────────────────────────────────────────┘  │
└─────┬──────────────────┬──────────────────┬────────────────────┘
      │                  │                  │
┌─────▼─────┐      ┌─────▼─────┐     ┌─────▼─────┐
│ TimescaleDB│      │   Redis   │     │   MQTT    │
│ (时序数据) │      │  (缓存)   │     │ (消息队列)│
└───────────┘      └───────────┘     └─────▲─────┘
                                            │
                        ┌───────────────────┴───────────────────┐
                        │         IoT 设备 / 模拟器             │
                        │  (电压/电流/功率传感器)               │
                        └───────────────────────────────────────┘
```

### 数据流向

#### 设备数据上报
```
设备传感器 → MQTT (mine/telemetry) → mqtt_worker.py → 
data_processor.py (报警检测) → TimescaleDB (存储) → 
WebSocket (实时推送) → 前端大屏
```

#### 远程控制
```
前端操作 → HTTP API (/devices/{id}/control) → 
mqtt_publisher.py → MQTT (mine/control/{id}) → 
设备接收指令 → 执行动作
```

### 项目结构

```
MineEnergySystem/
├── app/                      # 后端应用
│   ├── api/                  # API 层
│   │   └── endpoints/       # API 端点（auth, devices, telemetry, etc.）
│   ├── core/                # 核心基础设施
│   │   └── ...             # database, redis, security, logger, etc.
│   ├── services/            # 业务逻辑层
│   ├── models/              # 数据模型
│   └── main.py              # 应用入口
├── frontend/                # 前端应用
│   ├── src/                # 源代码（api, components, views, stores）
│   └── package.json
├── scripts/                 # 脚本工具集 ⭐ 已整理
│   ├── shell/              # Shell 脚本（启动、停止、测试等）
│   ├── python/             # Python 脚本（模拟器、工具等）
│   └── README.md           # 脚本使用指南
├── docs/                    # 文档中心
│   ├── archive/            # 归档文档
│   └── README.md           # 文档导航
├── config/                  # 配置文件
├── logs/                    # 运行日志
├── backups/                 # 备份文件
├── docker-compose.yml       # Docker 编排
├── Dockerfile              # Docker 镜像
├── requirements.txt        # Python 依赖
├── bin/                    # 快速启动脚本（fast_start.sh 等）
├── docs/                   # 完整文档
└── README.md               # 本文档
```

**📖 详细说明**：查看 [docs/07-快速参考/根目录结构说明](docs/07-快速参考/根目录结构说明.md)

---

## 📚 API 文档

### 访问方式

- **Swagger UI**: http://localhost:8088/docs
- **ReDoc**: http://localhost:8088/redoc

### 核心端点

#### 认证 (`/auth`)

```bash
# 登录获取 Token
POST /auth/login
{
  "username": "admin",
  "password": "123456"
}
```

#### 设备管理 (`/devices`)

```bash
# 获取设备列表
GET /devices

# 获取设备详情
GET /devices/{device_id}

# 创建设备
POST /devices

# 控制设备
POST /devices/{device_id}/control
{
  "action": "start"  # 或 "stop"
}
```

#### 遥测数据 (`/telemetry`)

```bash
# 上传遥测数据
POST /telemetry

# 获取历史数据
GET /telemetry/{device_id}?limit=50
```

#### 报警管理 (`/alarms`)

```bash
# 获取报警列表
GET /alarms?skip=0&limit=20&is_resolved=false

# 确认报警
POST /alarms/{alarm_id}/resolve
```

#### 健康检查 (`/health`)

```bash
# 完整健康检查
GET /health

# 存活检查（Kubernetes Liveness Probe）
GET /health/live

# 就绪检查（Kubernetes Readiness Probe）
GET /health/ready
```

---

## 💻 开发指南

### 本地开发环境

#### 1. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
```
# 4. 启动模拟器产生数据（新终端）⭐ 如果没有真实设备
python scripts/python/simulator_unified.py


#### 2. 启动服务

```bash
# 启动后端（需要先启动 Docker 服务）
docker compose up -d db redis mqtt
python run.py

# 启动前端
cd frontend
npm run dev
```


#### 3. 访问应用

- 前端: http://localhost:5173
- 后端 API: http://localhost:8088/docs

### LSTM预测功能开发

系统已实现完整的LSTM深度学习预测功能，包括：
- 模型训练和预测
- 多变量预测支持
- 模型版本管理
- 超参数自动搜索
- 定时训练任务

📖 **完整使用指南**: 查看 [docs/LSTM完整使用指南.md](./docs/LSTM完整使用指南.md)

**快速开始**:
```bash
# 1. 生成训练数据
POST /data-generator/generate/device/1
{"days": 60, "interval_minutes": 60, "data_type": "load"}

# 2. 训练LSTM模型
POST /forecast/lstm/train
{"prediction_type": "load", "device_id": 1, "days": 60}

# 3. 使用LSTM预测
POST /forecast/load?device_id=1&hours=24&algorithm=lstm
```

### 添加新功能

#### 1. 创建 Service 层

```python
# app/services/your_service.py
from sqlmodel import Session
from app.core.exceptions import ResourceNotFoundException

class YourService:
    @staticmethod
    def get_something(session: Session, id: int):
        """获取某个资源"""
        # 业务逻辑
        pass
```

#### 2. 创建 API 端点

```python
# app/api/endpoints/your_endpoint.py
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.core.database import get_session
from app.services.your_service import YourService

router = APIRouter()

@router.get("/{id}")
def get_something(id: int, session: Session = Depends(get_session)):
    """获取资源"""
    return YourService.get_something(session, id)
```

#### 3. 注册路由

```python
# app/main.py
from app.api.endpoints import your_endpoint

app.include_router(
    your_endpoint.router,
    prefix="/your_endpoint",
    tags=["你的模块"],
    dependencies=[Depends(get_current_user)]
)
```

---

## 🔧 运维管理

### 日常维护

#### 查看服务状态

```bash
# 查看所有容器
docker compose ps

# 查看后端日志
docker compose logs -f backend

# 查看应用日志
tail -f logs/ems_app_$(date +%Y-%m-%d).log
```

#### 重启服务

```bash
# 重启后端
docker compose restart backend

# 重启所有服务
docker compose restart

# 重新构建并启动
docker compose up -d --build
```

### 数据库管理

#### 备份数据库

```bash
# 备份
docker exec mine_energy_db pg_dump -U admin mine_energy > backup_$(date +%Y%m%d).sql

# 压缩备份
docker exec mine_energy_db pg_dump -U admin mine_energy | gzip > backup.sql.gz
```

#### 恢复数据库

```bash
# 恢复
docker exec -i mine_energy_db psql -U admin mine_energy < backup.sql

# 从压缩文件恢复
gunzip -c backup.sql.gz | docker exec -i mine_energy_db psql -U admin mine_energy
```

#### 清理历史数据

```bash
# 进入数据库
docker exec -it mine_energy_db psql -U admin -d mine_energy

# 删除 30 天前的数据
DELETE FROM devicedata WHERE timestamp < NOW() - INTERVAL '30 days';
```

### 性能监控

#### 查看资源占用

```bash
# 容器资源占用
docker stats

# 数据库性能
docker exec -it mine_energy_db psql -U admin -d mine_energy -c "
SELECT * FROM pg_stat_statements 
ORDER BY mean_exec_time DESC LIMIT 10;
"
```

### 生产环境部署

#### Nginx 反向代理

```nginx
# /etc/nginx/sites-available/mine-energy
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket 支持
    location /ws {
        proxy_pass http://127.0.0.1:8088/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### HTTPS 配置

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d api.yourdomain.com
```

---

## 🔍 故障排查

### 启动问题排查（最常见）

#### 问题 1: Docker Desktop 未安装或未启动

**症状**:
```bash
./bin/fast_start.sh
# 输出: ❌ Docker 未安装 或 ❌ Docker 未运行
```

**解决方案**:
```bash
# macOS - 检查 Docker 是否已安装
ls /Applications/Docker.app

# 如果未安装，使用 Homebrew 安装
brew install --cask docker

# 启动 Docker Desktop
open /Applications/Docker.app

# 等待 Docker 完全启动（菜单栏图标不再闪烁）
# 然后重新运行启动脚本
./bin/fast_start.sh
```

#### 问题 2: 端口被占用

**症状**:
```bash
Error response from daemon: Ports are not available: listen tcp 0.0.0.0:8088: bind: address already in use
```

**检查占用端口**:
```bash
# macOS/Linux
lsof -i :8088  # 后端
lsof -i :5433  # 数据库
lsof -i :6379  # Redis
lsof -i :1883  # MQTT

# 查看占用进程的 PID
lsof -ti:8088

# 杀掉占用进程（谨慎使用）
kill -9 $(lsof -ti:8088)
```

**解决方案**:

**方案1**（推荐）：修改端口映射
```bash
# 编辑 docker-compose.yml
# 将 "8088:8088" 改为 "8089:8088"
# 然后重新启动
docker compose up -d --build
```

**方案2**：停止占用进程
```bash
# 如果是之前的项目实例在运行
docker compose down
./bin/fast_start.sh
```

#### 问题 3: 首次启动速度慢

**症状**:
- 首次启动需要 3-5 分钟
- 下载镜像缓慢

**这是正常现象**，因为需要：
1. 下载 Docker 镜像（约 750MB）
2. 构建后端镜像
3. 初始化数据库

**优化建议**:
```bash
# 提前下载镜像
docker compose pull

# 后续启动会快很多（30-60秒）
```

#### 问题 4: 服务启动后无法访问

**症状**:
- 容器启动成功，但访问 http://localhost:8088/docs 失败
- 浏览器显示 "无法访问此网站"

**检查步骤**:
```bash
# 1. 查看容器状态（所有容器应该是 Up 状态）
docker compose ps

# 2. 查看后端日志
docker compose logs backend

# 3. 测试健康检查
curl http://localhost:8088/health

# 4. 检查后端是否在监听
docker exec mine_backend netstat -tln | grep 8088
```

**解决方案**:
```bash
# 方案1: 等待服务完全启动（首次启动需要 20-30 秒）
sleep 30
curl http://localhost:8088/health

# 方案2: 查看是否有启动错误
docker compose logs backend | grep -i error

# 方案3: 重启后端容器
docker compose restart backend
docker compose logs -f backend
```

---

### 常见运行时问题

#### 1. 数据库连接失败

**检查步骤**:
```bash
# 测试数据库连接
docker exec -it mine_energy_db psql -U admin -d mine_energy -c "SELECT 1;"

# 查看数据库日志
docker compose logs db

# 检查数据库健康状态
docker compose ps db
```

**解决方案**:
```bash
# 方案1: 等待健康检查通过（约 10-20 秒）
docker compose ps

# 方案2: 重启数据库
docker compose restart db

# 方案3: 完全重置数据库（⚠️ 会删除所有数据）
docker compose down -v
rm -rf pg_data/*
docker compose up -d
```

#### 3. WebSocket 连接失败

**检查步骤**:
```bash
# 检查后端日志
docker compose logs -f backend | grep WebSocket

# 测试 WebSocket
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  http://localhost:8088/ws
```

**解决方案**:
- 检查 CORS 配置
- 确认后端服务运行正常
- 查看浏览器控制台错误信息

#### 4. 启动速度慢

**原因**:
- 首次启动需要下载镜像（约750MB）
- 首次构建镜像需要时间（3-5分钟）

**优化方案**:
- 后续启动会使用缓存，速度快很多（30-70秒）
- 预下载镜像: `docker compose pull`
- 保持容器运行，避免频繁重启

### 完全重置（最后手段）

```bash
# 停止所有容器并删除数据
docker compose down -v

# 删除数据目录（会丢失所有数据）
rm -rf pg_data/* mosquitto/data/* logs/*

# 重新启动
docker compose up -d --build
```

---

## 🗺️ 项目路线图

### ✅ 已完成

- [x] 后端架构：FastAPI + 分层架构
- [x] 前端架构：Vue3 + Vite + Pinia
- [x] 数据存储：TimescaleDB + Redis
- [x] 实时通信：MQTT + WebSocket
- [x] 核心业务：设备管理、数据采集、报警、分析
- [x] 安全认证：JWT + Bcrypt
- [x] Docker 部署：完整的 Docker Compose 配置
- [x] 健康检查：系统监控端点（2026-01-12）
- [x] 文档完善：README、API 文档、开发指南

### 🔄 进行中

- [ ] **单元测试**：建立 pytest 测试框架
- [ ] **API 限流**：防止 API 滥用
- [ ] **安全加固**：更换默认密码、HTTPS

### 📋 计划中

#### 短期（1-2个月）
- [ ] 数据库迁移工具（Alembic）
- [ ] 性能监控（Prometheus + Grafana）
- [ ] CI/CD 流程（GitHub Actions）
- [ ] 数据库查询优化
- [ ] 缓存层优化

#### 中期（3-6个月）
- [ ] 完善故障诊断（FDD）功能
- [ ] 前端单元测试
- [ ] 移动端适配
- [ ] 多租户支持
- [ ] 国际化（i18n）

#### 长期（6-12个月）
- [x] AI 能耗预测（LSTM深度学习模型）✅ 已完成
- [ ] 微服务拆分（按需）
- [ ] 大数据分析平台集成
- [ ] 移动端 App

---

## 📝 配置说明

### 环境变量

创建 `.env` 文件（可选）：

```bash
# 数据库配置
DATABASE_URL=postgresql://admin:password123@db:5432/mine_energy

# Redis 配置
REDIS_URL=redis://redis:6379/0

# JWT 密钥（必须修改！）
SECRET_KEY=your-secret-key-min-32-chars

# MQTT 配置
MQTT_BROKER=mqtt
MQTT_PORT=1883

# 日志配置
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=7

# CORS 配置
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
```

**生成强密钥**:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 端口映射

| 服务 | 容器端口 | 主机端口 | 说明 |
|------|----------|----------|------|
| 后端 | 8088 | 8088 | HTTP API |
| 数据库 | 5432 | 5433 | PostgreSQL |
| Redis | 6379 | 6379 | Redis |
| MQTT | 1883 | 1883 | MQTT |
| MQTT WS | 9001 | 9001 | MQTT WebSocket |

---

## 🧪 测试

### 运行测试脚本

```bash
# 测试健康检查
./test_health.sh

# 测试 WebSocket
./check_websocket.sh
```

### 数据来源：模拟器与真实设备

当前数据可通过**模拟器**或**真实设备**接入，后端均通过 MQTT 接收，无需改代码。**真实设备接入**（协议、MQTT 格式、本仓库设备网关脚本用法）见 [真实设备接入指南](./docs/02-功能使用/真实设备接入指南.md)。

### 使用设备模拟器

**使用 Docker 运行（推荐）⭐**
```bash
# 模拟设备数据上报
docker exec -it mine_backend python scripts/python/simulator_unified.py

# 压力测试
docker exec -it mine_backend python scripts/python/stress_test.py

# 初始化设备
docker exec -it mine_backend python scripts/python/init_devices.py
```

**本地运行（需要先安装依赖）**
```bash
# 激活虚拟环境
source venv/bin/activate
pip install -r requirements.txt

# 运行脚本
python scripts/python/simulator_unified.py
```

---

## 🤝 贡献指南

### 提交代码

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交代码：`git commit -am 'Add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 提交 Pull Request

### 代码规范

- 遵循 PEP 8（Python）
- 遵循 ESLint 规则（TypeScript）
- 添加必要的单元测试
- 更新相关文档

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 📞 联系方式

- **项目地址**: https://github.com/your-repo/MineEnergySystem
- **问题反馈**: https://github.com/your-repo/MineEnergySystem/issues
- **文档地址**: http://localhost:8088/docs

---

## 🙏 致谢

感谢以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com)
- [Vue.js](https://vuejs.org)
- [TimescaleDB](https://www.timescale.com)
- [Eclipse Mosquitto](https://mosquitto.org)
- [Element Plus](https://element-plus.org)

---

## 📊 项目统计

- **开发时间**: 2025-2026
- **当前版本**: v2.0.0
- **代码行数**: ~10,000+ 行
- **API 端点**: 30+ 个
- **数据库表**: 7 个

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**

**🚀 现在就开始使用吧：`docker compose up -d --build`**
