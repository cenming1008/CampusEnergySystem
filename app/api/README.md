# CampusEnergySystem API 层说明

本文档描述当前 `app/api/` 的职责边界、路由注册方式、鉴权约定以及各业务模块的入口分组。  
它聚焦“现在的实现结构”，不试图逐条复制 OpenAPI 细节；接口字段与示例请以运行中的 `/docs` 为准。

## 1. API 层定位

`app/api/` 是后端的接入层，负责：

- 暴露 HTTP / WebSocket 接口
- 处理鉴权、角色依赖、请求校验
- 将请求转发给 application / service 层
- 统一错误语义与响应结构

当前 API 层已经不再采用“单文件大路由”结构，而是按业务域拆分在 `app/api/endpoints/` 下，并通过集中注册表挂载到应用。

## 2. 当前目录结构

```text
app/api/
├── __init__.py
├── deps.py
├── endpoint_utils.py
├── router_registry.py
├── websocket.py
└── endpoints/
    ├── auth.py
    ├── health.py
    ├── frontend_errors.py
    ├── users.py
    ├── audit.py
    ├── alarms.py
    ├── analysis.py
    ├── fdd.py
    ├── reports.py
    ├── maintenance.py
    ├── locations.py
    ├── device_groups.py
    ├── inspection.py
    ├── devices/
    ├── energy/
    └── data_cleanup/
```

## 3. 路由注册方式

HTTP 路由统一由 [router_registry.py](/Users/todo/MineEnergySystem/app/api/router_registry.py) 注册。

### 3.1 公开路由

当前公开路由包括：

- `health.router`
- `auth.router`
- `frontend_errors.router`

对应能力：

- `/health`、`/health/live`、`/health/ready`、`/metrics`
- `/auth/login`、`/auth/refresh`、`/auth/logout`
- `/frontend-errors`

说明：

- `health` 虽然属于公开挂载，但实际通过 `require_monitoring_access` 控制访问来源或 JWT。
- `frontend-errors` 用于前端异常上报，内置独立限流。

### 3.2 受保护路由

除公开路由外，其余业务路由统一作为受保护路由挂载，并自动注入：

- `Depends(get_current_user)`
- `Depends(ensure_password_change_completed)`

这意味着：

- 默认所有业务接口都要求有效 Bearer Token
- 若用户被标记为 `must_change_password=true`，则必须先完成自助改密后才能访问绝大多数业务接口

## 4. 鉴权与权限控制

核心依赖位于 [deps.py](/Users/todo/MineEnergySystem/app/api/deps.py)。

### 4.1 Token 机制

- 登录使用 `OAuth2PasswordRequestForm`
- Access token 与 refresh token 均为 JWT
- Access token 负载当前包含 `sub`、`ver`、`role`
- refresh token 通过 `/auth/refresh` 轮换
- 登出和强制下线依赖 `token_version` 失效旧令牌

### 4.2 当前用户解析

`get_current_user()` 会：

- 解码 access token
- 校验 token 类型不能为 refresh
- 查询数据库用户
- 校验用户启用状态、锁定状态、`token_version`
- 将用户对象写入 `request.state.current_user`

### 4.3 角色依赖

当前已提供这些角色依赖：

- `ADMIN_ONLY`
- `OPERATOR_OR_ADMIN`
- `MAINTAINER_OR_ADMIN`
- `MAINTAINER_OPERATOR_OR_ADMIN`

### 4.4 监控端点访问控制

`/health` 与 `/metrics` 使用 `require_monitoring_access()` 做二次保护。  
支持按配置限制为：

- `public`
- `internal`
- `jwt`
- `internal_or_jwt`

并支持按角色放行监控查看权限。

## 5. WebSocket

WebSocket 入口位于 [websocket.py](/Users/todo/MineEnergySystem/app/api/websocket.py)，路径为 `/ws`。

当前特性：

- 默认要求通过 query string 传 `access_token` 或 `token`
- `WEBSOCKET_AUTH_MODE=disabled` 时可关闭鉴权
- 连接建立后由 `socket_manager` 统一维护
- MQTT 与业务事件可通过生命周期中的回调广播到 WebSocket 客户端

## 6. 通用约定

### 6.1 返回风格

当前项目存在两类返回风格，并行使用：

- 直接返回 Pydantic / dict / list
- 使用 [response.py](/Users/todo/MineEnergySystem/app/core/response.py) 中的 `success_response()`

这属于当前代码现实，不建议文档假设“所有接口都统一包裹”。

### 6.2 限流

限流能力在 [rate_limit.py](/Users/todo/MineEnergySystem/app/core/rate_limit.py)。

当前已覆盖的典型场景包括：

- 认证登录
- 设备控制
- 设备数据上报
- 报表导出
- 前端异常上报
- 全局 API 请求限流中间件

### 6.3 审计

审计并不只存在于单独的 `/audit` 模块。  
很多关键接口会在业务动作发生时写入审计事件，例如：

- 登录 / 刷新 / 登出
- 用户创建、改密、强制下线
- 关键管理操作

审计查询入口位于 [audit.py](/Users/todo/MineEnergySystem/app/api/endpoints/audit.py)。

## 7. 当前业务路由分组

以下列表描述的是“模块分工”，不是完整字段清单。

### 7.1 认证与可观测性

- `auth.py`：登录、刷新令牌、登出
- `health.py`：健康检查、就绪检查、存活检查、Prometheus 指标
- `frontend_errors.py`：前端运行时错误上报

### 7.2 用户与安全治理

- `users.py`：当前用户信息、自助改密、用户管理、停用启用、角色调整、范围授权、强制改密、强制下线、解锁
- `audit.py`：审计事件查询、搜索、摘要

### 7.3 设备与能源

- `devices/management.py`：设备 CRUD、类型元数据、控制下发
- `devices/data.py`：设备遥测上报、历史数据、统计查询
- `devices/health.py`：设备接入健康状态与概览
- `energy/data.py`：多能源数据查询、写入、统计
- `energy/carbon.py`：碳排放相关能力

### 7.4 运维业务

- `alarms.py`：报警查询、确认、统计
- `maintenance.py`：维护计划与记录
- `inspection.py`：巡检路线、巡检点、计划、任务、记录
- `locations.py`：位置树与位置管理
- `device_groups.py`：设备分组与成员维护
- `data_cleanup/`：数据清理、统计、管理级清理能力

### 7.5 分析与诊断

- `analysis.py`：分析类接口
- `fdd.py`：故障诊断

## 8. 与 application / service 层的关系

当前后端分层已经从“路由直接堆业务逻辑”逐步演进为：

- API 层：接收请求、做鉴权和参数校验
- application 层：编排完整用例
- service 层：封装领域服务和持久化协作
- integrations 层：MQTT 等外部边界

典型链路：

```text
HTTP / WebSocket
  -> app/api/*
  -> app/application/* 或 app/services/*
  -> repositories / models / integrations
```

## 9. 文档维护建议

为了避免再次过期，后续建议 API 文档按下面方式维护：

- 本文件只记录“分层、入口、约定、模块职责”
- 请求字段、响应示例、状态码细节以 `/docs` 为准
- 新增路由模块时，同时更新 `router_registry.py` 和本文件的“业务路由分组”章节
- 若鉴权或监控访问策略变化，优先同步本文件第 4 节
