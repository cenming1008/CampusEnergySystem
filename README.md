# 煤矿综合能源管理系统（MineEnergySystem）

[![FastAPI](https://img.shields.io/badge/FastAPI-2.0-009688.svg)](https://fastapi.tiangolo.com)
[![Vue3](https://img.shields.io/badge/Vue-3.x-4FC08D.svg)](https://vuejs.org)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-PostgreSQL-336791.svg)](https://www.timescale.com)
[![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-3C5280.svg)](https://mosquitto.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> 基于 FastAPI + Vue3 + TimescaleDB + MQTT 的工业级能源监控和管理平台

---

## 📖 目录

- [项目简介](#-项目简介)
- [技术栈](#-技术栈)
- [功能特性](#-功能特性)
- [快速开始](#-快速开始)
- [系统架构](#-系统架构)
- [API 文档](#-api-文档)
- [开发指南](#-开发指南)
- [运维管理](#-运维管理)
- [故障排查](#-故障排查)
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

### 规划中功能

- [ ] 单元测试和集成测试（进行中）
- [ ] API 限流保护
- [ ] 数据库迁移工具（Alembic）
- [ ] 性能监控（Prometheus）
- [ ] CI/CD 流程
- [ ] 故障诊断专家系统增强
- [ ] 移动端 App

---

## 🚀 快速开始

### 前置要求

- **操作系统**: macOS / Linux / Windows (WSL2)
- **Docker**: 24.0+
- **Docker Compose**: 2.x
- **端口**: 8088(后端) / 5433(数据库) / 6379(Redis) / 1883(MQTT)

### 一键启动（Docker Compose）

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/MineEnergySystem.git
cd MineEnergySystem

# 2. 启动所有服务（推荐使用快速启动脚本）
./quick_start.sh

# 或手动启动
docker compose up -d --build

# 3. 查看服务状态
docker compose ps
# 或使用状态脚本
./scripts/shell/status.sh

# 4. 访问 API 文档
open http://localhost:8088/docs
```

### 初始化数据

系统首次启动会自动创建数据库表和默认管理员账号：
- **用户名**: `admin`
- **密码**: `123456`

⚠️ **生产环境务必修改默认密码！**

### 验证服务

```bash
# 1. 测试后端 API
curl http://localhost:8088/health

# 2. 测试数据库
docker exec -it mine_energy_db psql -U admin -d mine_energy -c "SELECT 1;"

# 3. 测试 Redis
docker exec -it ems_redis redis-cli ping

# 4. 测试 MQTT
docker exec -it mine_mqtt mosquitto_sub -h localhost -t 'mine/#' -v
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
├── quick_start.sh          # 快速启动脚本 ⭐ 新增
├── PROJECT_STRUCTURE.md    # 详细结构说明 ⭐ 新增
└── README.md               # 本文档
```

**📖 详细说明**：查看 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

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

### 常见问题

#### 1. 容器启动失败

**检查步骤**:
```bash
# 查看容器状态
docker compose ps

# 查看日志
docker compose logs db
docker compose logs backend

# 检查端口占用
lsof -i :8088
lsof -i :5433
```

**解决方案**:
- 端口被占用 → 修改 `docker-compose.yml` 端口映射
- 权限问题 → `sudo chown -R $(id -u):$(id -g) pg_data/`
- Docker 未运行 → 启动 Docker Desktop

#### 2. 数据库连接失败

**检查步骤**:
```bash
# 测试数据库连接
docker exec -it mine_energy_db psql -U admin -d mine_energy -c "SELECT 1;"

# 查看数据库日志
docker compose logs db
```

**解决方案**:
- 等待健康检查通过（约10-20秒）
- 检查环境变量配置
- 重启数据库容器

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
- [ ] AI 能耗预测
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

### 使用设备模拟器

```bash
# 模拟设备数据上报
python tools/simulator.py

# 压力测试
python tools/stress_test.py
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
