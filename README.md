# 园区综合能源管理系统

[![FastAPI](https://img.shields.io/badge/FastAPI-2.0-009688.svg)](https://fastapi.tiangolo.com)
[![Vue3](https://img.shields.io/badge/Vue-3.x-4FC08D.svg)](https://vuejs.org)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-PostgreSQL-336791.svg)](https://www.timescale.com)
[![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-3C5280.svg)](https://mosquitto.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

面向园区场景的综合能源管理系统，当前主线聚焦：

- 多能源接入
- 分层计量
- 分项分析
- 告警联动
- 驾驶舱展示

系统默认服务的核心对象包括园区、区域、楼栋、设备、表计、能源介质、告警和实时负荷。

---

## 快速开始

### 方式 1：本地开发

1. 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install
```

2. 启动基础服务

```bash
docker compose up -d db redis mqtt
```

3. 启动后端

```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8088
```

4. 启动前端

```bash
cd frontend
npm run dev
```

### 方式 2：Docker 一体启动

```bash
./bin/fast_start.sh
```

### 默认访问地址

- 后端 API / Swagger: `http://localhost:8088/docs`
- 后端健康检查: `http://localhost:8088/health`
- 前端开发环境: `http://localhost:5173`

首次创建管理员可执行：

```bash
./venv/bin/python scripts/python/create_admin.py
```

---

## 项目职责总览

### 技术栈

- 后端：FastAPI、SQLModel、Alembic、APScheduler
- 前端：Vue 3、TypeScript、Vite、Pinia、Element Plus、ECharts
- 数据与消息：TimescaleDB/PostgreSQL、Redis、MQTT（Mosquitto）
- 运维观测：Prometheus、Grafana、Alertmanager、Loki、Promtail

### 运行链路

1. 设备或模拟器通过 MQTT 上报遥测数据
2. 后端完成解析、校验、入库、告警和聚合
3. API 与 WebSocket 对外提供查询和实时推送
4. 前端页面展示驾驶舱、设备、告警和分析结果
5. 监控栈采集运行指标、日志和告警信号

---

## 根目录结构

下面只保留根目录关键文件和目录的职责说明，详细实现请进入对应子目录 README 或文档。

| 路径 | 职责 |
| --- | --- |
| `app/` | 后端主应用，包含 API、应用编排、领域规则、服务、仓储、核心基础设施和数据库表模型。 |
| `frontend/` | 前端应用，包含页面、组件、路由、状态管理和前端构建配置。 |
| `scripts/` | 仓库级脚本入口，放启动、演练、备份、初始化、调试和辅助工具。 |
| `docs/` | 文档中心，包含新手指南、开发部署、协作规范、计划与归档。 |
| `tests/` | 后端测试与验证脚本。 |
| `config/` | 运行配置，如告警阈值、设备网关或业务配置。 |
| `migrations/` | Alembic 数据库迁移目录，管理正式 schema 变更。 |
| `models/` | LSTM 训练产物目录，不是 ORM；用于保存模型、scaler 和版本文件。 |
| `lstm_forecast/` | 预测能力实现，包括训练、推理和版本管理。 |
| `monitoring/` | Prometheus、Grafana、Alertmanager、Loki、Promtail 等观测配置。 |
| `mosquitto/` | MQTT Broker 配置与本地挂载目录，含配置、运行数据和日志。 |
| `nginx/` | 反向代理与 HTTPS 模板配置。 |
| `bin/` | 高频快捷入口脚本，适合日常启动。 |

以下对象属于运行产物、本地数据或辅助目录，不作为主入口展开：

- `backups/`
- `logs/`
- `pg_data/`
- `pg_data_dev/`
- `artifacts/`
- `venv/`
- `__pycache__/`、`.pytest_cache/`、`.pycache/`

### 根目录关键文件

| 文件 | 职责 |
| --- | --- |
| `README.md` | 根目录导航，说明项目定位、启动方式和目录职责。 |
| `AGENTS.md` | AI 协作入口，定义线程职责、阅读顺序、修改原则和交接格式。 |
| `Dockerfile` | 后端镜像构建文件。 |
| `docker-compose.yml` | 默认 Compose 编排，包含数据库、Redis、MQTT、后端和 MQTT worker。 |
| `docker-compose.dev.yml` | 开发环境 Compose 配置。 |
| `docker-compose.prod.yml` | 生产部署 Compose 配置，含观测与代理相关服务。 |
| `requirements.txt` | 后端 Python 依赖。 |
| `run.py` | 本地运行入口之一。 |
| `alembic.ini` | Alembic 迁移配置入口。 |
| `env.example` | 通用环境变量示例。 |
| `env.local.example` | 本地开发环境变量示例。 |
| `env.prod.example` | 生产环境变量示例。 |

### `app/` 目录职责

| 路径 | 职责 |
| --- | --- |
| `app/main.py` | FastAPI 入口，注册中间件、路由、生命周期和异常处理。 |
| `app/api/` | HTTP/WebSocket 接入层。 |
| `app/application/` | 用例编排层，串联一次完整业务流程。 |
| `app/domain/` | 领域规则和纯业务逻辑。 |
| `app/services/` | 业务服务层。 |
| `app/repositories/` | 数据访问封装。 |
| `app/integrations/` | MQTT、预测等外部集成适配。 |
| `app/core/` | 数据库、配置、安全、日志、运行状态、指标和生命周期。 |
| `app/models/` | 后端 SQLModel 表结构定义。 |

---

## 重点目录补充说明

### `migrations/`

用于管理数据库正式迁移，而不是临时自动建表。

- `env.py`：迁移上下文，加载 `SQLModel.metadata`
- `versions/`：具体迁移脚本
- `script.py.mako`：Alembic 脚本模板

常用命令：

```bash
alembic stamp 20260325_0001
alembic upgrade head
```

### `models/`

这是机器学习模型产物目录，不是数据库模型目录。

- `models/lstm/`：训练后的 `.h5` / `.keras` 文件
- `models/scalers/`：数据标准化器 `.pkl`
- `models/versions/`：版本相关保留目录

数据库表模型请看 `app/models/`。

### `monitoring/`

统一放观测栈配置。

- `prometheus/`：抓取配置和告警规则
- `grafana/`：数据源和仪表盘模板
- `alertmanager/`：告警通知路由配置
- `loki/`：日志存储配置
- `promtail/`：日志采集配置

### `mosquitto/`

项目内置 MQTT Broker 的挂载目录。

- `config/mosquitto.conf`：Broker 配置
- `config/passwd`：认证密码文件
- `data/`：运行时数据
- `log/`：Broker 日志

---

## 常用命令

### 后端

```bash
source venv/bin/activate
uvicorn app.main:app --reload
pytest
```

### 前端

```bash
cd frontend
npm run dev
npm run build
npm run lint
```

### Compose

```bash
docker compose up -d db redis mqtt
docker compose up -d
docker compose ps
docker compose logs -f backend
```

### 备份与演练

```bash
bash ./scripts/shell/backup.sh
bash ./scripts/shell/release_readiness.sh
```

---

## 文档入口

### 新手与启动

- [快速启动指南](/Users/todo/CampusEnergySystem/docs/01-新手入门/快速启动指南.md)
- [安装配置完整指南](/Users/todo/CampusEnergySystem/docs/01-新手入门/安装配置完整指南.md)
- [本地开发环境配置](/Users/todo/CampusEnergySystem/docs/01-新手入门/本地开发环境配置.md)

### 开发与部署

- [开发与部署总览](/Users/todo/CampusEnergySystem/docs/03-开发与部署/README.md)
- [系统启动完整指南](/Users/todo/CampusEnergySystem/docs/03-开发与部署/系统启动完整指南.md)
- [企业部署完整指南](/Users/todo/CampusEnergySystem/docs/03-开发与部署/企业部署完整指南.md)
- [工业上线清单](/Users/todo/CampusEnergySystem/docs/03-开发与部署/工业上线清单.md)
- [试点发布与现场演练手册](/Users/todo/CampusEnergySystem/docs/03-开发与部署/试点发布与现场演练手册.md)

### 协作与计划

- [协作规范总览](/Users/todo/CampusEnergySystem/docs/guides/README.md)
- [产品定位规范](/Users/todo/CampusEnergySystem/docs/guides/product-positioning.md)
- [五线程协作框架](/Users/todo/CampusEnergySystem/docs/guides/five-thread-vibe-coding-framework.md)
- [当前状态](/Users/todo/CampusEnergySystem/docs/plans/current-status.md)
- [当前交接](/Users/todo/CampusEnergySystem/docs/plans/handoff.md)
- [计划目录](/Users/todo/CampusEnergySystem/docs/plans/README.md)

### 入口补充

- [文档中心](/Users/todo/CampusEnergySystem/docs/README.md)
- [脚本目录说明](/Users/todo/CampusEnergySystem/scripts/README.md)
- [快捷入口说明](/Users/todo/CampusEnergySystem/bin/README.md)

---

## 协作提醒

开始任何实现前，默认先阅读：

1. `AGENTS.md`
2. `docs/plans/current-status.md`
3. `docs/plans/handoff.md`
4. 当前主题对应 `PLAN-*.md`
5. `docs/guides/product-positioning.md`
6. `docs/guides/five-thread-vibe-coding-framework.md`

如果涉及具体实现，再按线程继续阅读对应 guide：

- 前端：`docs/guides/frontend-guidelines.md`
- 后端：`docs/guides/backend-guidelines.md`
- 脚本：`docs/guides/script-guidelines.md`

---

## 验证建议

做完修改后，至少按改动范围执行最小验证：

- 后端改动：`pytest` 或最小接口/脚本验证
- 前端改动：`npm run build` 或最小页面联调
- 脚本/部署改动：`docker compose config -q`、对应脚本 dry-run 或演练脚本

---

## 许可证

[MIT License](LICENSE)
