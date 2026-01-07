# 煤矿综合能源管理系统（MineEnergySystem）

[![FastAPI](https://img.shields.io/badge/FastAPI-2.0-009688.svg)](https://fastapi.tiangolo.com)
[![Vue3](https://img.shields.io/badge/Vue-3.x-4FC08D.svg)](https://vuejs.org)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-PostgreSQL-336791.svg)](https://www.timescale.com)
[![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-3C5280.svg)](https://mosquitto.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📖 目录

- [项目简介](#项目简介)
- [系统架构](#系统架构)
- [技术栈](#技术栈)
- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [详细部署](#详细部署)
- [开发指南](#开发指南)
- [API 文档](#api-文档)
- [运维管理](#运维管理)
- [常见问题](#常见问题)
- [性能优化](#性能优化)
- [贡献指南](#贡献指南)

---

## 项目简介

**煤矿综合能源管理系统**是一套基于 **FastAPI + Vue3 + TimescaleDB + MQTT** 的工业级能源监控和管理平台，适用于煤矿、工厂、园区等场景的：
- ⚡ **实时能耗监控**：设备电压、电流、功率、能耗数据采集
- 📊 **数据分析统计**：能耗趋势、峰谷分析、设备效率
- 🚨 **智能报警系统**：过载、欠压、异常自动检测
- 🔧 **远程设备控制**：通过 MQTT 反向下发控制指令
- 📈 **可视化大屏**：ECharts 实时图表展示
- 🔐 **权限管理**：JWT 认证 + 用户角色控制

---

## 系统架构

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
│  │  /auth    /devices    /telemetry    /alarms    /reports  │  │
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

#### 1. 设备数据上报流程
```
设备传感器 → MQTT (mine/telemetry) → mqtt_worker.py → 
data_processor.py (报警检测) → TimescaleDB (存储) → 
WebSocket (实时推送) → 前端大屏
```

#### 2. 远程控制流程
```
前端操作 → HTTP API (/devices/{id}/control) → 
mqtt_publisher.py → MQTT (mine/control/{id}) → 
设备接收指令 → 执行动作 (启动/停止)
```

#### 3. 数据查询流程
```
前端请求 → API 端点 → Service 层 (业务逻辑) → 
TimescaleDB (查询优化) → Redis (缓存结果) → 
返回前端
```

---

## 技术栈

### 后端
| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.10+ | 编程语言 |
| **FastAPI** | 0.115+ | Web 框架 |
| **SQLModel** | 0.0.22+ | ORM（基于 Pydantic + SQLAlchemy）|
| **TimescaleDB** | 2.x | 时序数据库（基于 PostgreSQL）|
| **Redis** | 7.0 | 缓存 + 会话管理 |
| **MQTT (Mosquitto)** | 2.0 | 消息队列 |
| **Uvicorn** | 最新 | ASGI 服务器 |
| **Paho-MQTT** | 2.1+ | MQTT 客户端 |
| **Loguru** | 0.7+ | 日志管理 |
| **Python-Jose** | 3.3+ | JWT 认证 |
| **Bcrypt** | 4.2+ | 密码哈希 |

### 前端
| 技术 | 版本 | 用途 |
|------|------|------|
| **Vue** | 3.x | 前端框架 |
| **Vite** | 5.x | 构建工具 |
| **TypeScript** | 5.x | 类型安全 |
| **Pinia** | 2.x | 状态管理 |
| **Vue Router** | 4.x | 路由管理 |
| **Element Plus** | 2.x | UI 组件库 |
| **ECharts** | 5.x | 数据可视化 |
| **Axios** | 1.x | HTTP 客户端 |

### 容器化
| 技术 | 版本 | 用途 |
|------|------|------|
| **Docker** | 24.0+ | 容器运行时 |
| **Docker Compose** | 2.x | 容器编排 |

---

## 功能特性

### ✅ 已实现功能

#### 1. 设备管理
- [x] 设备增删改查（CRUD）
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

#### 6. 用户权限
- [x] JWT Token 认证
- [x] 密码 Bcrypt 加密
- [x] 接口权限控制

#### 7. 系统管理
- [x] 配置文件管理（settings.json）
- [x] 日志分级记录（Loguru）
- [x] 数据导出（CSV）
- [x] API 文档自动生成（Swagger）

### 🚧 规划中功能
- [ ] 故障诊断专家系统（FDD）
- [ ] 多租户支持
- [ ] 移动端 App
- [ ] AI 能耗预测
- [ ] 报表定时推送（邮件/短信）

---

## 快速开始

### 前置要求
- **操作系统**：Linux / macOS / Windows (WSL2)
- **Docker**：24.0+
- **Docker Compose**：2.x
- **端口**：8088(后端) / 5433(数据库) / 6379(Redis) / 1883(MQTT)

### 一键启动（Docker Compose）

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/MineEnergySystem.git
cd MineEnergySystem

# 2. 可选：配置环境变量
cp env.example .env
# 编辑 .env，修改 SECRET_KEY、数据库密码等

# 3. 启动所有服务（后端 + 数据库 + Redis + MQTT）
docker compose up -d --build

# 4. 查看启动状态
docker compose ps
docker compose logs -f backend

# 5. 访问 API 文档
# 浏览器打开：http://localhost:8088/docs
```

### 初始化数据（可选）

系统首次启动会自动创建数据库表和默认管理员账号：
- **用户名**：`admin`
- **密码**：`123456`

**⚠️ 生产环境务必修改默认密码！**

---

## 详细部署

### 方式一：Docker Compose（推荐）

#### 1. 准备环境

**检查 Docker 可用：**
```bash
docker version
docker compose version
```

**（可选）配置 Docker 镜像加速**（国内服务器建议配置）：
```bash
# 编辑 Docker 配置
sudo nano /etc/docker/daemon.json

# 添加内容：
{
  "registry-mirrors": [
    "https://docker.rainbond.cc",
    "https://docker.m.daocloud.io"
  ]
}

# 重启 Docker
sudo systemctl restart docker
```

#### 2. 配置项目

**复制环境变量模板：**
```bash
cp env.example .env
```

**编辑 `.env` 文件（重要配置项）：**
```bash
# 数据库配置
DATABASE_URL=postgresql://admin:password123@db:5432/mine_energy

# Redis 配置
REDIS_URL=redis://redis:6379/0

# JWT 密钥（必须修改！）
SECRET_KEY=请使用python生成强密钥

# MQTT 配置
MQTT_BROKER=mqtt
MQTT_PORT=1883

# 日志配置
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=7
```

**生成强密钥：**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 3. 启动服务

```bash
# 构建并启动（首次启动约 1-2 分钟）
docker compose up -d --build

# 查看容器状态（应全部为 Up）
docker compose ps

# 查看后端日志
docker compose logs -f backend
```

**成功的日志标志：**
```
✅ 数据库初始化完成
✅ Redis连接成功
✅ MQTT服务启动完成
✨ 系统就绪
```

#### 4. 验证服务

```bash
# 测试后端 API
curl http://localhost:8088/docs

# 测试数据库连接
docker exec -it mine_energy_db psql -U admin -d mine_energy -c "SELECT 1;"

# 测试 Redis
docker exec -it ems_redis redis-cli ping

# 测试 MQTT
docker exec -it mine_mqtt mosquitto_sub -h localhost -t 'mine/#' -v
```

#### 5. 访问系统

- **后端 API 文档**：http://localhost:8088/docs
- **后端 ReDoc**：http://localhost:8088/redoc
- **前端（需单独启动）**：http://localhost:5173

---

### 方式二：本地开发模式

适用于开发调试，不使用 Docker。

#### 1. 安装依赖服务

**安装 PostgreSQL (TimescaleDB)：**
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE DATABASE mine_energy;"
sudo -u postgres psql -c "CREATE USER admin WITH PASSWORD 'password123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mine_energy TO admin;"

# 安装 TimescaleDB 扩展
sudo apt install postgresql-14-timescaledb
```

**安装 Redis：**
```bash
sudo apt install redis-server
sudo systemctl start redis
```

**安装 MQTT：**
```bash
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

#### 2. 安装 Python 依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 3. 配置环境变量

```bash
export DATABASE_URL='postgresql://admin:password123@localhost:5432/mine_energy'
export REDIS_URL='redis://localhost:6379/0'
export MQTT_BROKER='127.0.0.1'
export SECRET_KEY='your-secret-key-here'
```

#### 4. 初始化数据库

```bash
python -c "from app.core.database import init_db; init_db()"
```

#### 5. 启动后端

```bash
python run.py
# 或
uvicorn app.main:app --host 0.0.0.0 --port 8088 --reload
```

#### 6. 启动前端

```bash
cd frontend
npm install
npm run dev
```

---

### 方式三：生产环境部署（Nginx + Systemd）

#### 1. 后端服务化（Systemd）

创建服务文件：
```bash
sudo nano /etc/systemd/system/mine-energy.service
```

内容：
```ini
[Unit]
Description=Mine Energy System Backend
After=network.target postgresql.service redis.service mosquitto.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/www/wwwroot/MineEnergySystem
Environment="DATABASE_URL=postgresql://admin:password123@localhost:5432/mine_energy"
Environment="REDIS_URL=redis://localhost:6379/0"
Environment="SECRET_KEY=your-production-secret-key"
ExecStart=/www/wwwroot/MineEnergySystem/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable mine-energy
sudo systemctl start mine-energy
sudo systemctl status mine-energy
```

#### 2. Nginx 反向代理

创建配置：
```bash
sudo nano /etc/nginx/sites-available/mine-energy
```

内容：
```nginx
# API 后端
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 支持
    location /ws {
        proxy_pass http://127.0.0.1:8088/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}

# 前端静态文件
server {
    listen 80;
    server_name yourdomain.com;

    root /www/wwwroot/MineEnergySystem/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/mine-energy /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 3. HTTPS（Let's Encrypt）

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com
```

---

## 开发指南

### 项目结构

```
MineEnergySystem/
├── app/                      # 后端应用
│   ├── api/                  # API 层
│   │   ├── deps.py          # 依赖注入
│   │   └── endpoints/       # API 端点
│   │       ├── auth.py      # 认证接口
│   │       ├── devices.py   # 设备管理
│   │       ├── telemetry.py # 遥测数据
│   │       ├── alarms.py    # 报警管理
│   │       ├── analysis.py  # 数据分析
│   │       ├── fdd.py       # 故障诊断
│   │       └── reports.py   # 报表导出
│   ├── core/                # 核心基础设施
│   │   ├── config.py        # 配置加载
│   │   ├── database.py      # 数据库连接
│   │   ├── error_handlers.py # 异常处理
│   │   ├── exceptions.py    # 自定义异常
│   │   ├── logger.py        # 日志配置
│   │   ├── redis.py         # Redis 客户端
│   │   ├── response.py      # 统一响应
│   │   ├── security.py      # JWT 认证
│   │   ├── settings.py      # 配置管理
│   │   └── socket_manager.py # WebSocket 管理
│   ├── services/            # 业务逻辑层
│   │   ├── alarm_service.py
│   │   ├── analysis_service.py
│   │   ├── data_processor.py
│   │   ├── device_service.py
│   │   ├── fdd_service.py
│   │   ├── mqtt_publisher.py
│   │   └── mqtt_worker.py
│   ├── models/              # 数据模型
│   │   └── tables.py
│   └── main.py              # 应用入口
├── frontend/                # 前端应用
│   ├── src/
│   │   ├── api/            # API 请求
│   │   ├── components/     # 组件
│   │   ├── views/          # 页面
│   │   ├── stores/         # 状态管理
│   │   ├── router/         # 路由
│   │   └── main.ts
│   └── package.json
├── tools/                   # 工具脚本
│   ├── simulator.py        # 设备模拟器
│   └── stress_test.py      # 压力测试
├── config/                  # 配置文件
│   └── settings.json       # 报警阈值配置
├── logs/                    # 日志目录
├── docker-compose.yml       # Docker 编排
├── Dockerfile              # Docker 镜像构建
├── requirements.txt        # Python 依赖
├── run.py                  # 后端启动脚本
├── env.example             # 环境变量模板
├── CODE_STYLE_GUIDE.md     # 代码规范
├── NEXT_STEPS.md           # 后续优化指南
└── README.md               # 本文档
```

### 代码规范

请参考 [CODE_STYLE_GUIDE.md](CODE_STYLE_GUIDE.md)，包含：
- 命名规范
- 代码组织
- 类型提示
- 文档字符串
- 异常处理
- 日志使用

### 添加新功能

#### 1. 添加新的 API 端点

**Step 1：创建 Service 层**
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

**Step 2：创建 API 端点**
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

**Step 3：注册路由**
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

#### 2. 添加新的数据模型

```python
# app/models/tables.py
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class YourModel(SQLModel, table=True):
    """你的数据模型"""
    __tablename__ = "your_table"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now)
```

### 测试

#### 单元测试（示例）

```python
# tests/test_services/test_device_service.py
import pytest
from sqlmodel import Session, create_engine, SQLModel
from app.models import Device
from app.services import DeviceService

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_get_device_by_id(session):
    device = Device(name="测试设备", sn="TEST001", location="A区")
    session.add(device)
    session.commit()
    
    result = DeviceService.get_device_by_id(session, device.id)
    assert result.name == "测试设备"
```

运行测试：
```bash
pytest tests/ -v --cov=app --cov-report=html
```

---

## API 文档

### 认证

所有需要认证的接口都需要在请求头中携带 JWT Token：
```
Authorization: Bearer <your_token>
```

#### 登录获取 Token

**POST** `/auth/login`

**请求体：**
```json
{
  "username": "admin",
  "password": "123456"
}
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 设备管理

#### 获取设备列表

**GET** `/devices`

**响应：**
```json
[
  {
    "id": 1,
    "name": "变压器-01",
    "sn": "TR-001",
    "device_type": "TRANSFORMER",
    "location": "A区-1号楼",
    "is_active": true,
    "created_at": "2026-01-07T10:00:00"
  }
]
```

#### 获取设备详情

**GET** `/devices/{device_id}`

#### 创建设备

**POST** `/devices`

**请求体：**
```json
{
  "name": "新设备",
  "sn": "DEV-001",
  "device_type": "VENTILATOR",
  "location": "B区",
  "is_active": true
}
```

#### 更新设备

**PUT** `/devices/{device_id}`

#### 删除设备

**DELETE** `/devices/{device_id}`

#### 控制设备

**POST** `/devices/{device_id}/control`

**请求体：**
```json
{
  "action": "start"  // 或 "stop"
}
```

### 遥测数据

#### 上传遥测数据

**POST** `/telemetry`

**请求体：**
```json
{
  "device_id": 1,
  "voltage": 220.5,
  "current": 35.2,
  "power": 7.76,
  "energy": 1234.56,
  "timestamp": 1704614400
}
```

#### 获取设备历史数据

**GET** `/telemetry/{device_id}?limit=50`

### 报警管理

#### 获取报警列表

**GET** `/alarms?skip=0&limit=20&is_resolved=false`

#### 确认报警

**POST** `/alarms/{alarm_id}/resolve`

### 数据分析

#### 能耗统计

**GET** `/analysis/energy?device_id=1&start_time=2026-01-01&end_time=2026-01-07`

#### 趋势分析

**GET** `/analysis/trend?device_id=1&interval=hour`

### 完整 API 文档

访问 **http://localhost:8088/docs** 查看交互式 API 文档（Swagger UI）。

---

## 运维管理

### 日常维护

#### 查看服务状态

```bash
# Docker Compose 模式
docker compose ps
docker compose logs -f backend

# Systemd 模式
sudo systemctl status mine-energy
sudo journalctl -u mine-energy -f
```

#### 重启服务

```bash
# 重启后端
docker compose restart backend

# 重启所有服务
docker compose restart

# 重新构建（代码更新后）
docker compose up -d --build backend
```

#### 查看日志

```bash
# 后端日志（文件）
tail -f logs/ems_app_$(date +%Y-%m-%d).log

# 错误日志
tail -f logs/ems_error_$(date +%Y-%m-%d).log

# Docker 日志
docker compose logs --tail=200 backend
```

### 数据库管理

#### 备份数据库

```bash
# Docker 容器内备份
docker exec mine_energy_db pg_dump -U admin mine_energy > backup_$(date +%Y%m%d).sql

# 压缩备份
docker exec mine_energy_db pg_dump -U admin mine_energy | gzip > backup_$(date +%Y%m%d).sql.gz
```

#### 恢复数据库

```bash
# 从备份恢复
docker exec -i mine_energy_db psql -U admin mine_energy < backup_20260107.sql

# 从压缩文件恢复
gunzip -c backup_20260107.sql.gz | docker exec -i mine_energy_db psql -U admin mine_energy
```

#### 清理历史数据

```bash
# 进入数据库
docker exec -it mine_energy_db psql -U admin -d mine_energy

# 删除 30 天前的数据
DELETE FROM devicedata WHERE timestamp < NOW() - INTERVAL '30 days';

# 清理已解决的报警（90 天前）
DELETE FROM alarm WHERE is_resolved = true AND timestamp < NOW() - INTERVAL '90 days';
```

### 性能监控

#### 查看资源占用

```bash
# 容器资源占用
docker stats

# 单个容器
docker stats mine_backend
```

#### 数据库性能

```sql
-- 查看慢查询
SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;

-- 查看表大小
SELECT 
    schemaname || '.' || tablename AS table_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 安全加固

#### 1. 修改默认密码

```bash
# 修改管理员密码（进入数据库）
docker exec -it mine_energy_db psql -U admin -d mine_energy

# 执行 SQL
UPDATE "user" SET hashed_password = '$2b$12$...' WHERE username = 'admin';
```

使用 Python 生成新密码哈希：
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
print(pwd_context.hash("新密码"))
```

#### 2. 配置防火墙

```bash
# 只开放必要端口
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8088/tcp
sudo ufw enable
```

#### 3. 定期更新依赖

```bash
# 检查过期依赖
pip list --outdated

# 更新依赖
pip install -U package_name
```

---

## 常见问题

### Q1: 启动失败，提示端口被占用

**原因**：8088、5433、6379、1883 端口已被占用。

**解决方案**：
```bash
# 查看端口占用
sudo netstat -tlnp | grep 8088

# 修改 docker-compose.yml 的端口映射
ports:
  - "8089:8088"  # 改成其他端口
```

### Q2: 数据库连接失败

**检查步骤**：
```bash
# 1. 确认数据库容器运行
docker compose ps db

# 2. 查看数据库日志
docker compose logs db

# 3. 测试连接
docker exec -it mine_energy_db psql -U admin -d mine_energy -c "SELECT 1;"
```

### Q3: MQTT 消息未收到

**排查方法**：
```bash
# 1. 测试 MQTT 服务
docker exec -it mine_mqtt mosquitto_sub -h localhost -t 'mine/#' -v

# 2. 手动发送测试消息
docker exec -it mine_mqtt mosquitto_pub -h localhost -t 'mine/test' -m 'hello'

# 3. 查看后端 MQTT 日志
docker compose logs backend | grep MQTT
```

### Q4: WebSocket 连接失败

**检查点**：
1. 确认后端正常运行
2. 检查 CORS 配置（`settings.py` 的 `cors_origins`）
3. 如果用 Nginx，确认 WebSocket 代理配置正确

### Q5: 前端无法连接后端

**解决方案**：
```bash
# 检查前端 API 地址配置
# frontend/src/api/config.ts
export const API_BASE_URL = 'http://你的服务器IP:8088'
export const WS_BASE_URL = 'ws://你的服务器IP:8088'
```

### Q6: Docker 构建很慢

**优化方案**：
```bash
# 配置 Docker 镜像加速（见"详细部署"章节）
sudo nano /etc/docker/daemon.json

# 添加国内镜像源
{
  "registry-mirrors": [
    "https://docker.rainbond.cc",
    "https://docker.m.daocloud.io"
  ]
}

sudo systemctl restart docker
```

---

## 性能优化

### 数据库优化

#### 1. 添加索引

```sql
-- 设备数据查询优化
CREATE INDEX idx_devicedata_device_timestamp 
ON devicedata(device_id, timestamp DESC);

-- 报警查询优化
CREATE INDEX idx_alarm_resolved_timestamp 
ON alarm(is_resolved, timestamp DESC);
```

#### 2. TimescaleDB 压缩

```sql
-- 启用自动压缩（7天后压缩数据）
SELECT add_compression_policy('devicedata', INTERVAL '7 days');

-- 手动压缩
SELECT compress_chunk(c) 
FROM show_chunks('devicedata', older_than => INTERVAL '7 days') AS c;
```

#### 3. 分区表（如果数据量很大）

```sql
-- TimescaleDB 已自动分区（Hypertable）
-- 查看分区状态
SELECT * FROM timescaledb_information.chunks;
```

### 缓存优化

#### 使用 Redis 缓存设备列表

```python
from app.core.redis import RedisClient
import json

async def get_devices_cached():
    redis = RedisClient.get_client()
    
    # 尝试从缓存获取
    cached = await redis.get("devices:list")
    if cached:
        return json.loads(cached)
    
    # 缓存未命中，查询数据库
    devices = session.exec(select(Device)).all()
    
    # 写入缓存（5分钟过期）
    await redis.setex("devices:list", 300, json.dumps(devices))
    
    return devices
```

### 后端优化

#### 1. 异步处理（提高并发）

```python
# 使用异步函数
@router.get("/devices")
async def get_devices(session: Session = Depends(get_session)):
    return await DeviceService.get_all_devices_async(session)
```

#### 2. 批量操作

```python
# 批量插入数据
devices = [Device(...) for _ in range(100)]
session.add_all(devices)
session.commit()
```

#### 3. 使用连接池

```python
# app/core/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # 连接池大小
    max_overflow=40,  # 最大溢出连接
    pool_pre_ping=True  # 连接健康检查
)
```

### 前端优化

#### 1. 数据分页加载

```javascript
// 分页请求
const { data } = await api.get('/devices', {
  params: { skip: 0, limit: 20 }
})
```

#### 2. 虚拟滚动（大数据列表）

```vue
<virtual-list
  :data-sources="devices"
  :data-key="'id'"
  :data-component="DeviceItem"
/>
```

#### 3. ECharts 按需引入

```javascript
// 只引入需要的图表类型
import { LineChart } from 'echarts/charts'
import { GridComponent } from 'echarts/components'
```

---

## 贡献指南

### 提交代码

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交代码：`git commit -am 'Add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 提交 Pull Request

### 代码审查

- 遵循 [CODE_STYLE_GUIDE.md](CODE_STYLE_GUIDE.md)
- 添加必要的单元测试
- 更新相关文档

### 报告问题

提交 Issue 时请包含：
- 问题描述
- 复现步骤
- 期望行为
- 实际行为
- 环境信息（操作系统、Docker 版本等）

---

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 联系方式

- **项目地址**：https://github.com/your-repo/MineEnergySystem
- **文档地址**：http://docs.your-domain.com
- **问题反馈**：https://github.com/your-repo/MineEnergySystem/issues

---

## 致谢

感谢以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com)
- [Vue.js](https://vuejs.org)
- [TimescaleDB](https://www.timescale.com)
- [Eclipse Mosquitto](https://mosquitto.org)
- [Element Plus](https://element-plus.org)

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**

