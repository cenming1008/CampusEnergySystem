# 后端应用目录说明

本文档描述当前后端代码目录、分层边界以及主要运行链路。  
内容已按 2026-03-26 仓库状态更新，旧文档中已废弃的 `telemetry.py`、`data_processor.py` 等结构不再作为现状说明。

## 📁 目录结构

```
app/
├── __init__.py
├── main.py                    # FastAPI 入口：中间件、异常处理、WebSocket 与 API 路由注册
│
├── api/                       # HTTP / WebSocket 接入层
│   ├── deps.py                # 依赖注入（认证、数据库会话）
│   ├── router_registry.py     # 公开路由与受保护路由集中注册
│   ├── websocket.py           # WebSocket 端点（默认路径 /ws，支持 token 鉴权）
│   ├── endpoint_utils.py      # 端点共用工具
│   └── endpoints/             # 按业务拆分的路由模块（部分为子包聚合）
│       ├── auth.py
│       ├── audit.py
│       ├── alarms.py
│       ├── analysis.py
│       ├── frontend_errors.py
│       ├── fdd.py
│       ├── reports.py
│       ├── health.py          # 健康检查（公开）
│       ├── data_generator.py
│       ├── maintenance.py
│       ├── locations.py
│       ├── device_groups.py
│       ├── inspection.py
│       ├── users.py
│       ├── devices/           # 设备：管理、数据上报、接入健康
│       ├── energy/            # 能源数据与碳相关
│       ├── forecast/          # 预测与 LSTM
│       └── data_cleanup/      # 数据清理
│
├── core/                      # 基础设施
│   ├── database.py            # 数据库引擎、会话、init_db
│   ├── lifecycle.py           # 应用 lifespan：DB/Redis/MQTT/调度器启停与 MQTT→WS 回调
│   ├── error_handlers.py
│   ├── exceptions.py
│   ├── logger.py
│   ├── metrics.py
│   ├── redis.py
│   ├── runtime_state.py
│   ├── response.py
│   ├── access_control.py
│   ├── security.py
│   ├── security_headers.py
│   ├── settings.py
│   ├── socket_manager.py      # WebSocket 连接与广播
│   ├── startup_checks.py
│   ├── audit.py
│   ├── notifications.py
│   ├── rate_limit.py
│   └── device_registry.py
│
├── application/               # 用例编排（薄层，组合领域与服务）
│   ├── device_reporting.py
│   ├── telemetry_ingestion.py # 单条遥测：落库、告警、健康状态、广播数据
│   ├── energy_management.py
│   ├── reporting.py
│   ├── analysis.py
│   └── forecasting.py
│
├── domain/                    # 领域模型与规则（与框架无关的纯逻辑）
│   ├── device_payloads.py
│   └── energy_rules.py
│
├── repositories/              # 数据访问封装（按聚合根或表划分）
│   ├── base.py
│   ├── device_repository.py
│   ├── energy_repository.py
│   └── user_repository.py
│
├── integrations/              # 外部系统适配
│   ├── mqtt/
│   │   └── processor.py     # MQTT 解析、校验、别名、落库与广播消息构造（主实现）
│   └── forecasting/
│       └── adapter.py        # 预测相关适配（与 forecast 服务配合）
│
├── services/                  # 业务服务（可被 application / 集成层调用）
│   ├── device_service.py
│   ├── energy_service.py
│   ├── alarm_service.py
│   ├── analysis_service.py
│   ├── fdd_service.py
│   ├── device_group_service.py
│   ├── location_service.py
│   ├── maintenance_service.py
│   ├── inspection_service.py
│   ├── forecast_adapter.py
│   ├── data_cleanup_service.py
│   ├── ingestion_health_service.py
│   ├── mqtt_worker.py        # paho 订阅线程，收到消息后调用 integrations.mqtt.process_payload
│   ├── mqtt_publisher.py
│   ├── mqtt_models.py        # 遥测广播等 MQTT 相关数据结构
│   ├── mqtt_device_resolver.py  # 从 payload / topic 解析 device_id
│   ├── mqtt_processor.py     # 兼容旧导入路径，内部转发到 integrations.mqtt.processor
│   ├── scheduler_service.py  # APScheduler 启停
│   ├── scheduler_registry.py # 默认任务定义与注册（读 settings）
│   └── scheduler_jobs.py     # 定时任务实际函数（清理、预测、LSTM 等）
│
└── models/
    └── tables.py              # SQLModel 表定义
```

---

## 📇 Endpoints 文件索引

HTTP 路径前缀以 `router_registry.py` 为准（如设备模块为 `/devices`）；下列为**源码文件**与**一句话职责**。WebSocket 见 `api/websocket.py`（路径 `/ws`）。

### `api/`（非 `endpoints/`）

| 文件 | 说明 |
|------|------|
| `deps.py` | 依赖注入：数据库会话、当前登录用户等。 |
| `router_registry.py` | 将公开路由与需认证路由批量挂到 `FastAPI` 应用，并统一追加鉴权与首次改密约束。 |
| `websocket.py` | WebSocket 连接接入与断开，配合 `socket_manager` 广播。 |
| `endpoint_utils.py` | 端点复用：`ValueError`→400、统一记录异常日志。 |

### `api/endpoints/`（顶层模块）

| 文件 | 说明 |
|------|------|
| `__init__.py` | 聚合 import 各业务子模块，供注册表等处统一引用。 |
| `auth.py` | 登录、刷新令牌、登出。 |
| `health.py` | 健康检查、就绪检查、存活检查、Prometheus 指标。 |
| `frontend_errors.py` | 接收前端运行时异常并计入观测指标。 |
| `users.py` | 用户管理、自助改密、强制下线、锁定解除、权限范围调整。 |
| `audit.py` | 审计事件查询、筛选与摘要。 |
| `alarms.py` | 报警列表、确认与统计等。 |
| `analysis.py` | 单设备数据分析（今日能耗/费用等）。 |
| `fdd.py` | 全系统故障诊断统计与单设备诊断。 |
| `reports.py` | 设备能源历史数据 CSV 导出。 |
| `data_generator.py` | 模拟负荷/光伏/风电数据生成（经预测适配器）。 |
| `maintenance.py` | 设备维护计划与维护记录 CRUD。 |
| `locations.py` | 位置层级、设备挂载与位置统计。 |
| `device_groups.py` | 设备分组及组成员管理。 |
| `inspection.py` | 巡检路线、点、计划、任务与记录。 |

### `api/endpoints/devices/`

| 文件 | 说明 |
|------|------|
| `__init__.py` | 聚合 `management`、`data`、`health` 三个子路由。 |
| `management.py` | 设备列表/详情/增删改、类型元数据、MQTT 控制指令下发。 |
| `data.py` | HTTP 上报单设备测点数据、查询历史与统计（走统一上报用例）。 |
| `health.py` | 单设备与概览维度的 MQTT 接入健康状态。 |
| `shared.py` | 设备创建/更新/上报等 Pydantic 模型。 |

### `api/endpoints/energy/`

| 文件 | 说明 |
|------|------|
| `__init__.py` | 聚合能源数据与碳排放子路由。 |
| `data.py` | 通用能源数据写入、查询、统计（走能源管理用例）。 |
| `carbon.py` | 碳排放查询、汇总及手动试算（领域规则）。 |
| `shared.py` | 能源与碳相关请求/响应模型及字段提取工具。 |

### `api/endpoints/forecast/`

| 文件 | 说明 |
|------|------|
| `__init__.py` | 聚合 `basic`、`lstm`、`admin` 路由；导出预测/LSTM 可用性等。 |
| `basic.py` | 负荷与可再生预测、预测历史、最新结果与准确度评估。 |
| `lstm.py` | LSTM 训练、评估、版本列表/切换、超参搜索等。 |
| `admin.py` | 查询当前进程内 APScheduler 已注册任务列表。 |
| `shared.py` | 预测类型校验、结果序列化、适配器获取与可选依赖探测。 |

### `api/endpoints/data_cleanup/`

| 文件 | 说明 |
|------|------|
| `__init__.py` | 聚合基础清理与管理级清理路由。 |
| `basic.py` | 清理接口自检、按时间窗触发清理等（需登录）。 |
| `admin.py` | 更广范围/全量清理与清理统计等管理操作。 |

---

## 🎯 架构分层说明

### 1. API 层 (`api/`)

**职责**：

- 处理 HTTP / WebSocket 请求与响应
- 参数校验（Pydantic）
- 调用 Service 或组合好的用例
- 返回统一响应格式

**规范**：

- 端点函数保留简洁 docstring
- 使用类型注解
- 通过 `Depends` 注入会话、用户、角色约束
- 不在路由里堆业务规则

**路由注册**：

- 在 `router_registry.py` 的 `PUBLIC_ROUTERS` / `PROTECTED_ROUTERS` 中登记模块路由；`main.py` 只调用 `register_routers(app)` 与 `include_router(websocket_router)`。
- 当前受保护路由会统一追加 `get_current_user` 与 `ensure_password_change_completed`。

---

### 2. Application 层 (`application/`)

**职责**：

- 编排「一次用户意图或一条消息」的完整流程（例如单条遥测：健康标记 → 上报落库 → 告警 → 返回广播用数据）
- 依赖 `Session` 与各类 Service，保持路由与集成层轻薄

**规范**：

- 用例函数命名清晰（如 `ingest_telemetry_use_case`）
- 避免在 application 中直接写 SQL，优先通过 Service 或 Repository

---

### 3. Service 层 (`services/`)

**职责**：

- 封装可复用的业务逻辑与持久化协作
- 抛出业务异常（由全局处理器转换）

**规范**：

- 复杂查询可下沉到 `repositories/`
- 使用 `logger` 记录关键路径
- MQTT 后台线程入口在 `mqtt_worker.py`；消息解析与持久化的主逻辑在 `integrations/mqtt/processor.py`
- 与正式投产相关的告警、审计、运行时指标、调度注册等能力也主要落在 service/core 层协作完成

---

### 4. Core 层 (`core/`)

**职责**：

- 数据库、Redis、配置、日志、安全、WebSocket 管理器、应用生命周期、运行时指标、审计与通知

**规范**：

- 不写具体业务规则
- 配置统一来自 `settings.py`
- `lifecycle.py` 负责启动时 `init_db`、探测 Redis、启动 MQTT 后台与调度器，关闭时停止调度器并关闭 Redis
- `metrics.py`、`runtime_state.py` 负责进程内运行状态与 Prometheus 指标暴露
- `startup_checks.py` 用于启动前配置校验，配合生产 readiness 脚本使用

---

### 5. Model 层 (`models/`)

**职责**：

- 表结构与 ORM 映射

**规范**：

- 使用 SQLModel；字段约束与索引合理；时间字段注意默认值策略

---

### 6. Domain / Repository / Integrations

- **domain/**：与存储、HTTP 无关的规则与数据结构
- **repositories/**：按表或聚合封装查询与写入，供 Service 或 application 使用
- **integrations/**：MQTT、预测等外部边界，便于单测与替换实现

---

## 🔄 数据流转

### 1. 设备遥测（MQTT）

```
MQTT Broker
    ↓
mqtt_worker.py（订阅 settings.mqtt_topic / mqtt_topic_wildcard）
    ↓
process_data() → integrations.mqtt.processor.process_payload（或经 mqtt_processor 兼容层）
    ↓
字段别名、resolve_device_id、校验时间戳与测点
    ↓
application.telemetry_ingestion.ingest_telemetry_use_case
    → report_device_data_use_case、AlarmService、IngestionHealthService
    ↓
lifecycle.mqtt_to_ws_callback（run_coroutine_threadsafe）
    ↓
socket_manager.manager.broadcast() → 前端 WebSocket（/ws）
```

### 2. API 请求流程

```
前端请求
    ↓
API 端点（校验参数）
    ↓
deps.py（可选认证 + get_session）
    ↓
Service / application 用例
    ↓
Database（经 Session 与可选 Repository）
    ↓
统一响应
```

---

## 🛠️ 开发规范

### 导入顺序

```python
# 1. 标准库
from datetime import datetime
from typing import List, Optional

# 2. 第三方库
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

# 3. 项目内部
from app.core.database import get_session
from app.models.tables import Device
from app.services.device_service import DeviceService
```

### 命名规范

- **文件名**：小写 + 下划线 (`device_service.py`)
- **类名**：大驼峰 (`DeviceService`)
- **函数/变量**：小写 + 下划线 (`get_device_by_id`)
- **常量**：全大写 + 下划线 (`MAX_RETRY_COUNT`)

### 日志使用

```python
from app.core.logger import logger

logger.info(f"设备 {device_id} 创建成功")
logger.warning(f"设备 {device_id} 数据异常")
logger.error(f"数据库操作失败: {e}")
logger.exception(f"未处理异常: {e}")
```

### 异常处理

```python
from app.core.exceptions import ResourceNotFoundException

if not device:
    raise ResourceNotFoundException("设备", device_id)
```

---

## 🔐 安全规范

### 1. 认证保护

受保护路由在 `router_registry.PROTECTED_ROUTERS` 中已统一挂上 `Depends(get_current_user)`。若新增公开接口，应放入 `PUBLIC_ROUTERS`。

```python
from app.api.deps import get_current_user

@router.get("/")
def protected_endpoint(current_user: User = Depends(get_current_user)):
    pass
```

### 2. 密码与 JWT

```python
from app.core.security import get_password_hash, verify_password, create_access_token

hashed = get_password_hash("plain_password")
is_valid = verify_password("plain_password", hashed)
token = create_access_token(data={"sub": username})
```

---

## 📊 数据库操作

### 使用依赖注入获取会话

```python
from app.core.database import get_session

@router.get("/")
def endpoint(session: Session = Depends(get_session)):
    pass
```

### 查询与增删改示例

与原先一致：使用 `session.exec(select(...))`、`session.add`、`session.commit` 等；复杂查询可抽到 `repositories/`。

---

## 🧪 测试

仓库根目录 `tests/` 中已有与当前模块对应的示例：

- `tests/test_mqtt_processor.py`：`mqtt_processor` 兼容层（解析、指标归一、`process_payload` 与 mock 落库）
- `tests/test_scheduler_jobs.py`：`scheduler_jobs` 在成功/禁用/模块不可用时的日志与分支

可按业务继续补充 `test_api/`、`test_services/` 等结构。

---

## 📝 添加新功能指南

### 1. 添加新的 API 端点

1. 在 `services/` 或 `application/` 中实现业务或用例。
2. 在 `api/endpoints/` 下新增路由模块（或子包内文件），定义 `APIRouter`。
3. 在 `app/api/router_registry.py` 的 `PUBLIC_ROUTERS` 或 `PROTECTED_ROUTERS` 中增加一项 `(router, prefix, ("标签",))`。
4. 若需完全无认证的独立前缀，使用 `PUBLIC_ROUTERS`；默认业务接口走 `PROTECTED_ROUTERS`。

### 2. 添加新的数据模型

在 `app/models/tables.py` 中定义 SQLModel 表，必要时配合迁移脚本（项目若使用 Alembic 等）。

### 3. 添加新的配置项

在 `app/core/settings.py` 的 `Settings` 中增加字段，并通过 `env` 或环境变量注入。

---

## 🔍 常见问题

### Q1: Service 层如何使用 logger？

```python
from app.core.logger import logger

class YourService:
    @staticmethod
    def your_method():
        logger.info("操作开始")
```

### Q2: 业务异常如何变成 HTTP 响应？

抛出 `app.core.exceptions` 中的异常，由 `error_handlers` 统一转换为标准 JSON 响应。

### Q3: 如何向所有 WebSocket 客户端推送？

```python
from app.core.socket_manager import manager

await manager.broadcast({"type": "telemetry_update", "data": {...}})
```

前端连接地址为应用根路径下的 **`/ws`**（见 `api/websocket.py`）。

### Q4: 如何使用 Redis？

```python
from app.core.redis import RedisClient

redis = RedisClient.get_client()
await redis.set("key", "value")
value = await redis.get("key")
```

### Q5: 定时任务在哪里配置？

- 任务函数：`scheduler_jobs.py`
- 是否注册、触发器类型：`scheduler_registry.py`（结合 `settings` 中的开关）
- 进程内调度器生命周期：`scheduler_service.py`，由 `lifecycle.startup` / `shutdown` 调用

---

## 📚 相关文档

- [文档中心](../docs/README.md)
- [快速启动指南](../docs/01-新手入门/快速启动指南.md)
- [后端功能实现详解](../docs/05-架构与设计/后端功能实现详解.md)
- [本地开发快速参考](../docs/07-快速参考/本地开发快速参考.md)

---

## 🎯 最佳实践总结

1. **职责分离**：路由薄、规则与流程分层（domain / application / service）
2. **依赖注入**：会话与用户通过 FastAPI `Depends`
3. **异常与日志**：自定义异常 + 全局处理；关键路径打日志
4. **配置单一来源**：`settings.py`
5. **MQTT 与集成**：主逻辑放在 `integrations/`，Worker 只负责连接与线程
6. **路由集中注册**：改动 `router_registry.py`，保持 `main.py` 简洁

---

**维护者**：园区综合能源管理系统团队  
**最后更新**：2026-03-24
