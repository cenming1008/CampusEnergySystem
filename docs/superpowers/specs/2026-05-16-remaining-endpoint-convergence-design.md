# 补齐剩余 endpoint 收敛 — 设计文档

- 日期：2026-05-16
- 主题：把仍残留在 endpoint 层的编排逻辑下沉到 `app/application/` use case 层
- 执行依据：`app/application/README.md` 的分层口径；后端规范收敛主线

## 1. 背景

后端正在把 HTTP endpoint 的编排逻辑逐步下沉到 `app/application/` 的 use case 层。
口径：endpoint 只负责 HTTP 关注点（参数解析、`Depends` 注入、`HTTPException`、状态码、
`StreamingResponse`），多 service 编排、权限前置、审计、响应 DTO 装配进入 `application` 层。

第一批主路径（`devices/data`、`devices/management`、`devices/monitoring` overview、
`analysis`、`reports`、`energy/overview`、`campus`、`locations`、`maintenance`、
`inspection`、telemetry 接入、部分 users）已完成收敛。

对剩余 endpoint 做了一轮全面盘点，确认大多数 endpoint 已经够薄，只有两处仍残留
该下沉的编排逻辑。本设计只收敛这两处。

## 2. 范围

收敛对象：

1. `app/api/endpoints/auth.py` 的 `login` / `refresh` / `logout`
2. `app/api/endpoints/devices/ingestion_health.py` 的 `replay_mqtt_ingestion_record`

明确不在范围内：其余 endpoint（`alarms`、`audit`、`device_groups`、`fdd`、
`compensation_*`、`storage`、`monitoring` 非 overview、`data_cleanup/*`、
`energy/data` 非 overview、`energy/carbon`、`users`、`frontend_errors`、`health`）
经盘点已够薄或属于平凡处理，本轮不动。

## 3. 硬约束（不变量）

- API 路径不变、HTTP 方法不变、响应字段与结构不变、行为不变。
- 审计事件完全一致：`auth.login` / `auth.refresh` / `auth.logout` / `mqtt.replay_record`，
  包括 action、target、outcome、reason 以及全部附加 kwargs。
- 异常类型与消息文本不变：`AuthenticationException`、`ResourceNotFoundException`、
  `ValidationException`，消息文案逐字保留。
- 登录流程的步骤顺序不变（见 4.1 的限流说明）。
- `HTTPException`、`Request`、`Depends`、`OAuth2PasswordRequestForm`、
  `success_response` 等 HTTP 关注点继续留在 endpoint 层。

## 4. 设计

### 4.1 Part A — `auth.py` → 新建 `app/application/auth.py`

新增三个 use case：

- `login_use_case(session, username, password, enforce_rate_limit) -> dict`
- `refresh_access_token_use_case(session, refresh_token) -> dict`
- `logout_use_case(session, current_user) -> dict`

下沉内容：用户 ORM 查询、账号锁定判定、密码校验、登录失败计数
（`UserService.register_login_failure`）、停用判定、登录成功登记
（`UserService.register_login_success`）、refresh token 解码与类型/版本校验、
会话轮换（`UserService.rotate_refresh_session`）、令牌生成、审计日志。

endpoint 收敛后只保留：`APIRouter`、`Depends`、`OAuth2PasswordRequestForm`、
`RefreshTokenRequest` 请求体、`Request`，以及调用 use case 并返回结果。

**限流处理（关键设计点）**

当前 `login` 的步骤顺序：

1. 查用户
2. 若已锁定 → 审计 + 抛 `AuthenticationException`
3. 强制登录限流（`_enforce_auth_login_rate_limit(request)`，依赖 `Request`）
4. 校验密码

限流位于锁定判定之后，且依赖 `Request`（HTTP 关注点）。

采用方案：endpoint 构造一个捕获 `Request` 的无参闭包
`enforce_rate_limit: Callable[[], None]`，作为参数传入 `login_use_case`；
use case 在原步骤 3 的位置调用它。`Request` 不进入 application 层，调用顺序不变。

否决的备选：

- 把限流提到 use case 调用之前 → 改变“先判锁定再限流”的顺序，属行为变更。
- 把 `Request` 对象传进 use case → HTTP 关注点泄漏进 application 层，违反分层口径。

`logout` 逻辑最薄（`UserService.revoke_user_tokens` + 审计），但为 auth 主线内聚，
一并放入新文件。

### 4.2 Part B — `ingestion_health.py` replay → 并入 `app/application/telemetry_ingestion.py`

新增 use case：

- `replay_mqtt_ingestion_record_use_case(session, record_id, operator_username) -> dict`

下沉内容：`MqttReliabilityService.get_record_by_id`、记录存在性校验、状态校验
（仅 `FAILED` / `DEAD_LETTER` 允许重放）、`raw_payload` 存在性校验、
`parse_payload`、`process_payload_dict`、`MqttReliabilityService.mark_replayed`、
`session.commit()`、`audit_log("mqtt.replay_record", ...)`，以及组装返回 data dict。

endpoint 收敛后只保留：路由声明、`Depends`，调用 use case 并用
`success_response(data=...)` 包装。

replay 属于 MQTT 接入链路工作流，放进既有 `telemetry_ingestion.py`，
不新建文件。

### 4.3 导出与文档

- 两组 use case 加入 `app/application/__init__.py` 的 import 与 `__all__`。
- 更新 `app/application/README.md`：
  - 第 2 节目录结构加入 `auth.py`。
  - 第 3 节补一节 auth 主线 use case 说明。
  - 第 4 节推荐调用链补 `/auth/login` 与 replay 链路。
  - 第 8 节边界现状更新为已收敛 auth 与 ingestion replay。

## 5. 测试

- 沿用 `tests/test_endpoint_application_convergence.py` 与 `tests/test_layer_exports.py`
  的既有模式补边界测试：确认新 use case 可从 `app.application` 导出，确认 endpoint
  不再直接做 ORM 查询 / 多步编排。
- 跑既有相关测试确认无回归：
  - auth：登录、刷新、登出、账号锁定、限流相关测试。
  - replay：`tests/test_ingestion_reliability.py` 及 MQTT 重放相关测试。
- 验证标准：相关测试全部通过，无新增 warning 之外的失败。

## 6. 成功标准

- `auth.py` 与 `ingestion_health.py` 的目标 handler 收敛为薄入口，无 ORM 查询、
  无多步编排。
- 新增 `app/application/auth.py`，三个 auth use case 可用并导出。
- `replay_mqtt_ingestion_record_use_case` 进入 `telemetry_ingestion.py` 并导出。
- 第 3 节全部硬约束成立。
- 第 5 节测试全部通过。
- `app/application/README.md` 与文档同步。

## 7. 风险

- 限流闭包注入是本设计唯一的非平凡改动点；若闭包构造或调用时机出错会改变登录顺序，
  需在测试中覆盖“锁定优先于限流”的顺序。
- replay use case 内含 `session.commit()`，下沉后需确认 commit 时机与事务边界
  与原 endpoint 完全一致。
