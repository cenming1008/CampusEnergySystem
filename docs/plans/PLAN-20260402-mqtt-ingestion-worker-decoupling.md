# PLAN-20260402-mqtt-ingestion-worker-decoupling

> 状态：健康语义分层验收通过，待阶段收口判断 | 负责人：验收线程 | 更新时间：2026-04-02

---

## 背景

当前总控判断，“把 MQTT 采集从 API 进程里拆出去”不属于当前主主题“前端视觉体系升级专题”，应作为新主题独立推进。

本轮探索已审视以下范围：

- `app/services/mqtt_worker.py`
- `app/integrations/mqtt/processor.py`
- `app/application/telemetry_ingestion.py`
- `app/application/device_reporting.py`
- `app/services/alarm_service.py`
- `app/core/database.py`
- `app/core/lifecycle.py`
- `app/main.py`
- `app/core/settings.py`
- `app/api/endpoints/health.py`
- `app/api/endpoints/devices/health.py`
- `docker-compose.yml`
- `docker-compose.dev.yml`
- `docker-compose.prod.yml`
- `run.py`
- `scripts/python/replay_mqtt_failures.py`
- `scripts/shell/start.sh`
- `scripts/shell/restart_backend.sh`

核心判断不是“当前完全没有 worker”，而是“当前 MQTT 订阅已经是后台线程，但它仍然附着在 API 进程生命周期内，消息处理、告警、进程内健康状态与 WebSocket 广播都没有形成独立运行边界”。

---

## 目标

- 明确当前 MQTT 采集链路分别落在哪个进程和哪一层。
- 判断当前是否适合拆出独立采集进程。
- 锁定最小可执行的拆分路径，避免直接升级成过重的服务化改造。

## 规范收敛结论

### 1. 当前主题

- 本主题正式命名为：`MQTT 采集进程解耦专题`
- 当前执行依据为本 PLAN，不再继续使用“前端视觉体系升级专题”作为本轮执行入口

### 2. 第一阶段拆分形态

- 第一阶段正式锁定为：`独立 MQTT ingest worker`
- 第一阶段不直接升级为独立 ingest service

### 3. API / worker 职责边界

- API 进程保留：
  - HTTP API
  - WebSocket 连接管理与广播
  - MQTT 发布能力（设备控制发布）
  - 接入健康查询、失败记录查询、人工重放入口
  - 系统健康检查与监控接口
- MQTT worker 进程承担：
  - MQTT 订阅
  - payload 解析与设备解析
  - 幂等 / 去重 / 失败留痕
  - 遥测入库
  - 告警检测
  - 接入健康状态更新

### 4. 第一阶段桥接与健康口径

- 第一阶段允许使用现有 Redis 作为 worker -> API 的实时事件桥接
- worker 独立健康状态与 API 汇总口径纳入第一阶段范围，不允许继续只依赖 API 进程内 `runtime_state["mqtt"]`

### 5. 第一阶段禁止扩张项

- 不直接新建完整 ingest service
- 不顺手重做告警模型、设备模型或时序模型
- 不顺手改 MQTT topic、Broker 部署或控制命令链路
- 不把前端实时展示改造拉进第一阶段实现

## 关键结论

### 1. 当前职责落点

当前链路分布如下：

1. MQTT 订阅：
   - `app/core/lifecycle.py` 在 FastAPI `lifespan.startup()` 中调用 `start_mqtt_background()`
   - `app/services/mqtt_worker.py` 使用 `paho-mqtt` 在 API 进程内启动后台线程订阅主题
2. 消息解析 / 去重 / 设备解析：
   - `app/integrations/mqtt/processor.py`
3. 遥测入库 / 遥测健康更新 / 告警检测：
   - `app/application/telemetry_ingestion.py`
   - `app/application/device_reporting.py`
   - `app/services/alarm_service.py`
4. WebSocket 广播：
   - `app/core/lifecycle.py` 中 `mqtt_to_ws_callback()`
   - 通过 `asyncio.run_coroutine_threadsafe(manager.broadcast(...), _event_loop)` 回调到 API 事件循环
5. 健康状态：
   - `app/core/runtime_state.py` 维护进程内状态
   - `app/api/endpoints/health.py` 直接读当前进程内 `runtime_state`

结论：当前 MQTT 采集、消息解析、遥测入库、告警检测和广播推送，虽然在代码层分了模块，但运行时仍然绑定在 API 进程内。

### 2. 当前运行边界

当前不是独立进程 worker，而是：

- API 进程内的后台 MQTT 线程
- 订阅线程收到消息后，直接在同一进程内调用消息处理和数据库写入
- 再通过回调把广播任务投递回 API 进程事件循环

`docker-compose*.yml` 里也只有：

- `backend`
- `db`
- `redis`
- `mqtt`

没有独立 `mqtt-worker` / `ingest-worker` 服务。

### 3. 当前最强耦合点

当前最强耦合不是单个函数调用，而是以下 5 类运行时耦合共同存在：

1. 生命周期耦合：
   - MQTT 订阅跟随 FastAPI `lifespan` 启停
2. WebSocket 广播耦合：
   - worker 线程必须拿到 API 事件循环和 `socket_manager`
3. 健康检查耦合：
   - `/health` 返回的 MQTT 状态来自当前 API 进程内 `runtime_state`
4. 数据库 / 处理耦合：
   - `processor.py` 直接使用全局 `engine` 开 `Session`
   - 去重、失败留痕、入库、告警和接入健康都在同一条同步处理链里
5. 部署与运维耦合：
   - `Dockerfile` / `run.py` / compose 只定义了一个后端入口
   - `restart_backend.sh`、`start.sh` 默认把 MQTT 消费视为 backend 的一部分

### 4. 当前最阻塞扩容与故障隔离的点

最阻塞后续扩容、故障隔离和问题定位的点有两个：

1. MQTT 订阅和 API 进程绑定
   - 一旦 API 重启，MQTT 消费也重启
   - 无法独立扩容或独立观察消费端故障
2. WebSocket 广播直接绑定 MQTT 消费线程
   - 这使“消费进程”和“前端实时推送进程”难以分开

补充风险：

- `settings.workers` 允许大于 1；若未来提高 API worker 数，当前 `lifespan` 逻辑会有每个 worker 都启动 MQTT 订阅线程的潜在风险。

### 5. 拆分形态判断

当前更适合的不是一步到位的“单独 ingest service”，而是：

- 先做“进程边界清理 + 启动解耦”
- 再落成“独立 MQTT ingest worker 进程”

原因：

- 当前消息解析、入库、告警、幂等、失败重放已经形成比较清晰的消费链，具备先抽成独立 worker 的条件。
- 但 WebSocket 广播、健康检查、启动入口和部署方式还没有解耦到适合直接变成独立服务。
- 因此第一阶段不宜过早引入新服务边界、独立 API 或更复杂的服务发现。

## 推荐线程路径

- 当前线程路径固定为：`规范 -> 后端 -> 验收`

## 最小拆分路径建议

第一阶段建议只做“独立 worker 进程 + API 进程停掉内嵌 MQTT 消费”，不直接做独立 ingest service。

建议边界如下：

### API 进程保留

- HTTP API
- WebSocket 连接管理
- MQTT 发布能力（设备控制发布）
- 接入健康查询、失败记录查询、人工重放入口
- 系统健康检查与监控接口

### MQTT worker 进程承担

- MQTT 订阅
- payload 解析与设备解析
- 幂等 / 去重 / 失败留痕
- 遥测入库
- 告警检测
- 接入健康状态更新

### 第一阶段最小技术路径

1. 先抽独立 worker 启动入口
   - 复用现有 `mqtt_worker.py` 与 `integrations/mqtt/processor.py`
   - 但不再通过 FastAPI `lifespan` 启动
2. 增加运行开关
   - API 进程显式关闭内嵌 MQTT 消费
   - worker 进程显式开启 MQTT 消费
3. 将实时广播从“直接回调 WebSocket”改成“事件桥接”
   - 第一优先建议用已有 Redis 做最小桥接
   - worker 发布 `telemetry_update` / 后续可扩展 `alarm_*` 事件
   - API 进程只负责订阅桥接事件并推给 WebSocket
4. 调整 compose / 启动脚本
   - 新增 `mqtt-ingest-worker` 服务
   - backend 与 worker 共享同一镜像、同一配置源，但 command 分离
5. 最后再独立 worker 健康状态
   - 不再只依赖 API 进程内 `runtime_state["mqtt"]`
   - worker 自己暴露存活/状态，或把状态写入共享存储后由 API 汇总

## 非目标

- 本轮不改代码。
- 不直接改数据库 schema。
- 不直接改前端。
- 不一步到位拆成全新 ingest service。
- 不在本轮重做消息模型、告警模型或设备模型。
- 不顺手改 MQTT topic、Broker 部署或控制命令链路。

## 风险与拍板点

- 若直接拆 worker，但不先处理 WebSocket 广播桥接，API 实时推送会断。
- 若继续让 `/health` 只读 API 进程内状态，拆分后会出现“API healthy 但 worker 已死”的假健康。
- 若未来启用多 API workers，而仍不拆消费边界，存在重复订阅和重复消费风险。
- `app/api/endpoints/devices/health.py` 与 `scripts/python/replay_mqtt_failures.py` 目前都直接调用 `process_payload_dict()`；拆分后仍需保留这类运维入口的兼容路径。

需要拍板：

- 当前无需新增拍板；第一阶段拆分形态、Redis 事件桥接与 worker 独立健康状态均已锁定。
- 仅当后端线程证明第一阶段必须引入新的独立服务边界、额外持久层或前端适配时，再升级为新一轮拍板。

---

## 后端实现结果

- `app/core/lifecycle.py` 已移除 API `lifespan` 中的 MQTT 消费启动；API 启动后只负责 Redis bridge 订阅与 WebSocket 广播。
- `scripts/python/run_mqtt_ingest_worker.py` 已提供独立 MQTT ingest worker 启动入口，继续复用现有消费、解析、入库与告警链路。
- `app/services/mqtt_realtime_bridge.py` 已形成最小 `worker -> API` 实时桥接：
  - worker 侧发布实时事件到 Redis，并写入 worker 心跳
  - API 侧订阅 Redis 频道并广播到 WebSocket 客户端
- `app/api/endpoints/health.py` 已汇总并区分：
  - API 进程内 `mqtt_bridge`
  - Redis 心跳中的 `mqtt_worker`
- `docker-compose.yml`、`docker-compose.prod.yml` 已纳入 `mqtt_ingest_worker` 服务。
- `scripts/shell/start.sh`、`scripts/shell/start_dev_env.sh`、`scripts/shell/restart_backend.sh`、`scripts/shell/status.sh`、`bin/fast_start_dev.sh` 已纳入独立 worker 的启动、重启、状态查看或开发提示。

## 验收结论

### 阶段结论

- 第一阶段最小闭环已成立，可进入阶段收口判断。
- 本轮验收通过，不需要打回后端、探索或规范。

### 通过依据

- API 已不再承担 MQTT 消费主职责，`app/core/lifecycle.py` 中只保留 Redis bridge 订阅任务。
- 独立 worker 已可单独启动并运行，入口为 `scripts/python/run_mqtt_ingest_worker.py`。
- Redis bridge 仍保持在最小 `worker -> API` 实时桥接范围内，没有扩成完整 ingest service。
- `/health` 已能区分 `mqtt_bridge` 与 `mqtt_worker`，worker 掉线时不会再出现“API 假健康”。
- `docker-compose.dev.yml` 仍只承载中间件，符合既有开发定位，不构成本轮缺漏。

### 验证记录

- `python3 -m compileall app/core/lifecycle.py app/core/runtime_state.py app/api/endpoints/health.py app/services/mqtt_realtime_bridge.py app/services/mqtt_worker.py scripts/python/run_mqtt_ingest_worker.py`
- `PYTHONPATH=. venv/bin/pytest -q tests/test_mqtt_realtime_bridge.py tests/test_health_endpoint.py tests/test_websocket_auth.py tests/test_monitoring_access.py`
- 结果：`11 passed`

### 当前剩余风险

- worker 健康当前依赖 Redis 心跳汇总；若未来需要更细颗粒度观测或独立运维面板，应新开后续主题。
- `app/api/endpoints/devices/health.py` 与 `scripts/python/replay_mqtt_failures.py` 仍复用现有处理链，本轮未改变其契约；若未来继续服务化，需要单独验证运维兼容性。
- 本轮仍停留在“独立 worker”阶段，不应被误读为“完整 ingest service 已完成”。

## 阶段收口结论

### 1. 第一阶段结论

- 第一阶段“独立 MQTT ingest worker”最小闭环已通过验收。
- 第一阶段已覆盖的内容：
  - API 已脱离内嵌 MQTT 消费
  - Redis `worker -> API` 实时桥接已成立
  - worker 独立健康已纳入 `/health`
  - compose / 启动脚本已纳入独立 worker

### 2. 当前主题是否继续保留

- 当前主题继续保留在 `docs/plans/`，不正式归档。
- 保留原因不是“第一阶段没做完”，而是后续仍可能围绕同一主题进入第二阶段边界锁定。
- 阶段收口时的历史结论是：
  - 第一阶段已完成
  - 当前进入阶段收口
  - 第二阶段尚未启动
- 当前最新状态已更新为：
  - 第一阶段已完成并通过验收
  - 第二阶段边界已锁定
  - 当前待交后端推进第二阶段最小实现

### 3. 第二阶段正式名称与范围

- 第二阶段正式名称锁定为：`worker / bridge 细粒度观测 + replay / 补偿链路验证`
- 第二阶段主目标锁定为：
  - 让 `mqtt_worker`、`mqtt_bridge`、API 三段链路更可观测
  - 让 replay / 补偿链路具备最小可验证闭环
  - 为后续扩容与隔离提供更稳定的运维基础
- 第二阶段范围锁定为：
  - 细化 `mqtt_worker`、`mqtt_bridge`、API 健康与状态口径
  - 增加关键阶段观测点，例如：
    - worker 消费状态
    - bridge 发布 / 订阅状态
    - API 广播状态
  - 为 replay / 补偿链路补最小可验证闭环
  - 为运维 / 故障定位补必要状态字段、日志、健康摘要或测试

### 4. 第二阶段允许动作

- 允许在现有“独立 MQTT ingest worker + Redis bridge + API 广播”架构下，补充更细粒度状态字段、健康摘要、日志与测试。
- 允许围绕 `scripts/python/replay_mqtt_failures.py`、`app/api/endpoints/devices/health.py`、`app/api/endpoints/health.py`、bridge / worker 相关服务补最小兼容性验证与运维可见性。
- 允许补 replay / 补偿链路的最小闭环验证，但前提仍是复用当前 worker 架构，而不是引入新的服务边界。

## 当前聚焦子问题（2026-04-02）

### 1. 子问题定义

- 当前用户决定先放下“第三阶段是否继续推进”的大问题，优先处理一个更具体的新问题：
  - 健康检查和真实业务就绪状态还不完全一致
- 该问题仍属于当前主主题“MQTT 采集进程解耦专题”，不新开主题。

### 2. 当前探索结论

- `GET /health/live` 是纯 liveness。
- `GET /health/ready` 当前只验证数据库连接，仍是极窄的 technical readiness。
- `GET /health` 当前更像“组件状态汇总 + diagnostics 摘要”，并不等于“真实业务已经可对外服务”。
- 目前 `mqtt_worker`、`mqtt_bridge`、`api_realtime` 三段状态大多还停留在：
  - 进程 / 组件是否活着
  - 最近一次阶段事件是否成功
  而不是“关键业务数据流仍在有效流动”。

### 3. 当前最可能缺的业务就绪信号

- worker 已连接 MQTT，但长时间没有有效消费或有效处理
- bridge 订阅仍在，但长时间没有事件流动
- API 广播链可用，但关键遥测事件没有最近成功广播
- replay / 补偿链存在失败、跳过、积压，但当前未进入 readiness 决策
- 设备接入健康已经在 `DeviceIngestionHealth` 中沉淀，但还没有被提升为系统级 business readiness 摘要

### 4. 当前推荐最小落地方向

- 不建议直接收紧现有 `/health/live`
- 不建议把全部业务信号硬塞进 `/health/ready`
- 更适合：
  1. 保留 `/health/live` 作为纯 liveness
  2. 将 `/health/ready` 定义为“系统是否可接流量的技术 readiness”
  3. 在 `/health` 中明确区分：
     - liveness
     - readiness
     - diagnostics / business signals
  4. 如需进一步落地，优先新增“业务就绪摘要”字段，而不是新开重量级端点体系

### 5. 健康语义分层规范结论

- 当前子问题正式收敛为：`健康检查 vs 真实业务就绪状态`
- 当前线程路径锁定为：`规范 -> 后端 -> 验收`

#### liveness

- 只回答“进程是否活着”
- 继续由 `/health/live` 承担
- 不纳入业务语义
- 不承载 worker / bridge / replay / 设备级业务状态

#### readiness

- 只回答“当前实例是否适合接流量 / 对外服务”
- 继续定义为技术 readiness，不做完整业务评分
- `/health/ready` 只允许纳入少数强信号：
  - 数据库可用
  - Redis 可用
  - worker 心跳新鲜
  - bridge 在线
- 当前暂不把“最近存在有效处理”纳入 readiness 判定
- 原因：
  - 该信号强依赖流量场景与时间窗口
  - 在低流量或夜间空闲时段容易把“无新事件”误判为 not_ready
  - 它更适合作为 diagnostics / business signals 暴露，而不是基础就绪闸门

#### diagnostics / business signals

- 放在 `/health` 主摘要中，而不是全部进入 `/health/ready`
- `/health` 应承担：
  - 组件状态汇总
  - diagnostics 摘要
  - business signals 可见性
- 可以包括：
  - `mqtt_worker` 最近连接 / 消费 / 处理 / 发布
  - `mqtt_bridge` 最近订阅 / 最近事件
  - `api_realtime` 最近广播类型 / 时间 / 失败
  - replay 成功 / 失败 / 跳过摘要
  - 设备级 success_rate、consecutive_failures、last_failure_reason
- 这些信息应“可见”，但不全部参与 ready / not_ready 判定

### 6. 当前子问题最小落地边界

- 本轮后端最小落地只允许：
  - 明确 `/health/live`、`/health/ready`、`/health` 三层返回语义
  - 把 readiness 收敛为少数强技术信号
  - 把 diagnostics / business signals 留在 `/health` 摘要中
  - 如有必要，仅补最小业务摘要字段，不新开复杂端点体系
- 本轮禁止：
  - 把 replay / 补偿、设备 success_rate、告警恢复全部拉进 readiness 判定
  - 把这个子问题扩成完整 observability 平台建设
  - 新开主题
  - 重新讨论 worker / bridge 第一、二阶段已通过的内容

### 5. 当前推荐线程路径

- 当前子问题推荐路径：`探索 -> 规范 -> 后端 -> 验收`

### 6. 本轮后端最小落地结果

- `/health/live` 保持纯 liveness，只回答“进程是否活着”。
- `/health/ready` 已收敛为技术 readiness，只由以下强技术信号驱动：
  - 数据库可用
  - Redis 可用
  - worker 心跳新鲜
  - bridge 在线
- `/health` 已明确承载三层摘要：
  - `semantics`
  - `diagnostics`
  - `business_signals`
- 以下信号已明确留在 diagnostics / business signals，而未进入 readiness 判定：
  - `recent_valid_processing`
  - replay 成功 / 失败 / 跳过摘要
  - 设备 success_rate / consecutive_failures / last_failure_reason

### 7. 本轮验收结论

- 当前子问题最小闭环已成立，可进入阶段收口判断。
- 本轮验收通过，不需要打回后端、探索或规范。

#### 通过依据

- `liveness / readiness / diagnostics / business signals` 三层语义已在 `app/api/endpoints/health.py` 中清楚分层。
- `/health/live` 仍保持纯 liveness，没有混入业务语义。
- `/health/ready` 仍只由少数强技术信号驱动，没有演化成业务评分器。
- diagnostics / business signals 仍保留在 `/health` 摘要中，没有反向塞回 readiness。
- “最近有效处理”这类强依赖流量窗口的信号已明确排除在 readiness 之外。
- 当前改动仍严格停留在 MQTT 解耦主题边界内，没有误扩成完整服务化或 observability 平台建设。

#### 验证记录

- `python3 -m compileall app/api/endpoints/health.py tests/test_health_endpoint.py`
- `PYTHONPATH=. venv/bin/pytest -q tests/test_health_endpoint.py tests/test_mqtt_realtime_bridge.py tests/test_runtime_controls.py tests/test_monitoring_access.py`
- 结果：`20 passed`

#### 当前剩余风险

- 当前 readiness 仍是技术 readiness，不等于完整业务 readiness；验收时不应把“低流量时段没有新处理”误判为 not ready。
- 若后续把 replay、设备 success_rate、告警恢复等继续塞进 readiness，就会重新把健康检查推向业务评分器。
- 当前验证仍以单测与摘要输出为主，尚未做更长链路的真实流量演练。


### 5. 第二阶段禁止扩张项

- 不升级成完整 ingest service
- 不引入新的重量级基础设施
- 不把 topic 治理、Broker 重构、前端改造一起拉进来
- 不扩成完整 observability 平台建设
- 不把第二阶段写成长期架构大全
- 不把“第二阶段启动”误解为自动批准更多实时链路服务化拆分

### 6. 第二阶段验收口径

- `mqtt_worker`、`mqtt_bridge`、API 三段状态是否比第一阶段更可区分
- replay / 补偿链路是否已经能被明确验证
- 当前改动是否仍然保持在“独立 worker”架构下
- 是否没有误扩成完整服务化

### 7. 当前不自动批准的事项

- 不自动批准完整 ingest service 拆分

---

## 第二阶段后端实现结果

- `app/core/runtime_state.py` 已支持服务级 `meta` 信息，并新增 `api_realtime` 状态面。
- `scripts/python/run_mqtt_ingest_worker.py` 已把 worker 连接、消费、处理、发布结果写入 worker 心跳 `meta`。
- `app/services/mqtt_realtime_bridge.py` 已细化 bridge 与 API 广播状态：
  - `mqtt_bridge` 记录最近订阅频道、最近桥接事件类型 / 时间
  - `api_realtime` 记录最近广播类型 / 时间，以及广播成功 / 失败状态
- `app/api/endpoints/health.py` 已对外汇总 `mqtt_worker`、`mqtt_bridge`、`api_realtime` 三段状态。
- `scripts/python/replay_mqtt_failures.py` 已输出 JSON 摘要，区分 `replayed`、`failed_*`、`skipped_*`，并且只有真正产出遥测事件时才记为 replay 成功。

## 第二阶段验收结论

### 阶段结论

- 第二阶段最小闭环已成立，可进入阶段收口判断。
- 本轮验收通过，不需要打回后端、探索或规范。

### 通过依据

- `/health` 已能同时区分 `mqtt_worker`、`mqtt_bridge`、`api_realtime` 三段状态，不再停留在第一阶段的粗粒度口径。
- `mqtt_worker` 心跳 `meta` 已能看出最近连接、最近消费、最近处理、最近发布等关键阶段。
- `mqtt_bridge` 与 `api_realtime` 已分别记录桥接订阅 / 收到事件 / 广播成功或失败的最近状态。
- replay / 补偿脚本输出已具备明确验证价值，且只有真正产出有效遥测事件时才记为成功。
- 当前改动仍严格停留在“独立 worker + Redis bridge + API 广播”架构下，没有误扩成完整 ingest service 或 observability 平台建设。

### 验证记录

- `python3 -m compileall app/core/runtime_state.py app/services/mqtt_worker.py app/services/mqtt_realtime_bridge.py app/api/endpoints/health.py scripts/python/run_mqtt_ingest_worker.py scripts/python/replay_mqtt_failures.py`
- `PYTHONPATH=. venv/bin/pytest -q tests/test_runtime_controls.py tests/test_mqtt_realtime_bridge.py tests/test_health_endpoint.py tests/test_replay_mqtt_failures.py tests/test_monitoring_access.py tests/test_websocket_auth.py tests/test_mqtt_reliability_service.py`
- 结果：`28 passed`

### 当前剩余风险

- 第二阶段验证目前仍以单测与脚本级输出为主，尚未做真实 Redis + MQTT + API 三进程长链路演练。
- worker 健康与 replay 摘要虽已更可观测，但若继续扩到独立运维面板、更细指标或新持久化，就会超出当前主题边界。
- 当前仍停留在“独立 worker”架构增强阶段，不应被误读为“完整 ingest service / 完整观测体系已完成”。
- 不自动批准更多实时链路服务化
- 不自动批准新的持久化桥接或更重基础设施方案

## 后续线程默认路径

- 当前默认路径：`规范 -> 后端 -> 验收`
- 当前第二阶段已经锁定边界，可直接按本 PLAN 交由后端线程推进。

## 进度补记

- 2026-04-02：规范线程完成阶段收口判断，确认第一阶段通过但主题暂不归档；第二阶段尚未启动，后续若继续推进必须重新锁定范围后再交后端。
- 2026-04-02：规范线程已完成第二阶段边界锁定，将后续推进范围正式收敛为“worker / bridge 细粒度观测 + replay / 补偿链路验证”。
