# PLAN-20260329-alarm-pipeline-audit

> 状态：进行中（后端最小闭环已阶段验收通过，可进入阶段收口判断） | 负责人：待定 | 更新时间：2026-03-29

---

## 背景

当前总控判断，“CampusEnergySystem 报警逻辑问题”不属于当前主主题“命名迁移分层治理”，应作为新主题单独推进。

探索线程已完成对以下链路的定向审计：

- `app/application/telemetry_ingestion.py`
- `app/application/device_reporting.py`
- `app/services/alarm_service.py`
- `app/api/endpoints/alarms.py`
- `app/services/mqtt_worker.py`
- `app/integrations/mqtt/processor.py`
- `app/models/tables.py`
- `app/core/database.py`

本轮探索确认：当前报警问题不是一个单点 bug，而是“遥测接入 -> 阈值检测 -> 报警事件创建 -> 报警生命周期表达 -> 权限处理 -> 实时推送”这条链路只做到了第一层事件落库，尚未形成稳定的告警生命周期模型。

因此会同时出现几类子症状：

1. MQTT 遥测到报警检测并未断链，但调用责任分散，事务边界和广播边界不清。
2. 当前去重依赖 `message` 全串匹配；消息中直接拼接实时值，持续异常时极易反复生成新报警。
3. 报警查询接口有位置范围约束，但 `resolve-all` / `resolve/{alarm_id}` 没有对象级权限过滤。
4. `Alarm` 表更像“报警事件记录”，不能稳定表达“持续异常 / 恢复 / 已处理中的当前状态”。
5. WebSocket 当前只广播 `telemetry_update`，不广播报警创建 / 处理事件；前端只能靠轮询或其他聚合接口感知告警变化。

---

## 目标

- 先完成报警链路审计收敛，锁定当前主问题、子症状边界与最小修复路径。
- 为规范线程和后端线程提供可直接执行的正式 PLAN。
- 明确哪些问题属于同一主问题下的不同表现，哪些属于独立但相关的次级问题。

## 规范收敛结论

### 1. 术语与对象边界

- `Alarm` 在本轮按“告警生命周期实例”理解，不再继续按“单次报警事件流水”理解。
- “报警事件记录”本轮只作为派生视角存在：
  - 首次触发是实例开始
  - 人工处理是实例上的运维动作
  - 恢复是实例上的系统状态变化
- “持续异常实例”是本轮最小核心对象：
  - 同一设备
  - 同一告警类别
  - 同一来源
  - 在未恢复前视为同一个活跃实例
- “恢复”与“已处理”必须分离：
  - 恢复：异常条件已经解除
  - 已处理：人工确认、备注或关闭动作
- “活跃告警”指异常仍在持续的实例，不等同于“未处理告警”。
- “未处理告警”指尚未被人工处理的实例；它可以仍在持续，也可以已经恢复但还未处理。

### 2. 生命周期最小定义

- `triggered`
  - 首次检测到异常，创建一个 `Alarm` 实例。
- `active`
  - 异常仍在持续，后续遥测只更新该实例的最近观测，不重复插入新行。
- `recovered`
  - 系统检测到异常条件解除，实例退出活跃状态。
- `handled`
  - 人工处理维度，不替代 `recovered`，可附加在 `active` 或 `recovered` 实例上。

本轮不引入完整状态机；后端只需保证以上四个语义可解释、可区分。

### 3. 轻量 schema 结论

- 本轮建议允许对现有 `Alarm` 做轻量 schema 扩展。
- 扩展方向应以兼容现有表为前提，不新建第二张生命周期主表。
- 最小建议字段：
  - 稳定实例键：如 `instance_key`
  - 最近一次仍异常的时间：如 `last_seen_at`
  - 系统恢复时间：如 `recovered_at`
- 现有 `is_resolved / resolved_at / resolved_by / handling_note` 本轮收敛为“人工处理维度”，不再同时承担“系统已恢复”语义。

## 非目标

- 本轮不直接修改代码。
- 不顺手重构 MQTT 接入、设备监控聚合或 WebSocket 框架。
- 不把当前主题扩成前端告警中心改版。
- 不在未锁定生命周期模型前直接推倒现有 `Alarm` 表。
- 不补 WebSocket 告警事件。
- 不扩成完整告警状态机或告警中心产品重构。

## 范围

涉及目录或模块：

- `app/application/telemetry_ingestion.py`
- `app/application/device_reporting.py`
- `app/services/alarm_service.py`
- `app/api/endpoints/alarms.py`
- `app/services/mqtt_worker.py`
- `app/integrations/mqtt/processor.py`
- `app/models/tables.py`
- `app/core/database.py`
- `docs/plans/`

明确不改动：

- 前端页面实现
- 命名迁移主题残余工作
- 非报警相关的能源建模主题

## 关键结论

### 1. 主问题

当前主问题是：系统只有“基于遥测生成报警事件记录”的能力，还没有“告警实例生命周期”的稳定建模。

这会同时导致：

- 去重不稳定
- 持续异常与恢复无法表达
- 处理动作只能粗暴地把历史记录标记为 `is_resolved`
- WebSocket 无法推送真正的报警状态变化

### 2. 同一主问题下的子症状

- `AlarmService.should_create_alarm()` 以 `device_id + message + 未解决 + 最近 5 分钟` 去重，而 `message` 包含实时读数，持续异常值一旦变化就会绕过去重。
- `Alarm` 模型只有 `message / severity / category / source / timestamp / is_resolved / resolved_*`，没有告警实例键、开始时间、恢复时间、当前状态、最后观测值等字段。
- `check_and_create_alarm()` 只会“发现异常就插入事件”，不会：
  - 标记某个告警实例仍在持续
  - 记录恢复
  - 合并同一持续异常

### 3. 独立但相关的问题

- 权限边界问题：
  - `GET /alarms` 使用 `get_allowed_device_ids()` 做位置范围过滤
  - `POST /alarms/resolve-all` 与 `POST /alarms/resolve/{alarm_id}` 只做角色校验，没有设备级 / 位置级对象权限过滤
- 实时推送问题：
  - MQTT 链路最终只返回 `TelemetryBroadcastMessage(type="telemetry_update")`
  - 系统没有 `alarm_created` / `alarm_resolved` / `alarm_updated` 广播事件
- 遥测广播字段错配问题：
  - `ingest_telemetry_use_case()` 中 `TelemetryBroadcastData.power` 当前取的是 `record.flow_rate`
  - 这更像遥测广播映射错误，不是本轮主因，但说明职责边界确实散了

## 推荐线程路径

- 当前推荐：`探索 -> 规范 -> 后端 -> 验收`
- 若规范确认 WebSocket 事件契约需要新增，再升级为：`探索 -> 规范 -> 后端 + 前端 -> 验收`

原因：

- 当前核心问题主要在后端生命周期建模、权限边界与事件推送契约。
- 是否新增告警实时事件、是否扩 `Alarm` 模型、是否允许兼容字段或新增状态字段，先要规范锁边界。

## 最小修复路径

1. 规范线程先锁定主题与边界：
   - 主题名
   - “报警事件记录”与“告警生命周期实例”的术语区别
   - 本轮允许轻量 schema 扩展，但只限现有 `Alarm` 的兼容扩展
2. 后端线程第一步只修主问题闭环：
   - 稳定告警判重键，不再直接以带实时值的 message 去重
   - 明确持续异常、恢复、人工处理三类状态的最小表达
   - 为 `resolve-all` / `resolve/{alarm_id}` 补对象级权限校验
3. 本轮不进入 WebSocket 告警事件补点，实时事件契约保留为后续议题。
4. 验收线程按“链路不断、去重稳定、权限一致、生命周期可解释、未扩成告警中心改版”做阶段验收。

## 风险与拍板点

- 风险：直接修 message 文案而不修告警实例键，会继续出现持续异常重复告警。
- 风险：直接在现有 `is_resolved` 上叠逻辑，可能把“恢复”和“已处理”继续混为一体。
- 风险：若先补 WebSocket 事件、后补生命周期模型，容易把前端适配建立在不稳定事件语义上。
- 风险：若 `resolve-all` 继续无对象级权限，运维角色可能处理到其位置范围外的报警。

需要拍板：

- 当前无需人类额外拍板 WebSocket 范围：本轮已明确不纳入。
- 仅当后端发现轻量扩展不足以表达最小生命周期、必须引入新表或 breaking change 时，再升级拍板。

## 验收标准

- [x] 已明确本主题独立于“命名迁移分层治理”，并以本 PLAN 作为执行依据。
- [x] 已明确主问题是“告警生命周期缺失”，而非单点 MQTT 断链。
- [x] 已明确去重失效根因与最小修复方向。
- [x] 已明确查询与处理接口的权限边界不一致点。
- [x] 已明确当前 `Alarm` 模型能表达什么、不能表达什么。
- [x] 已锁定“恢复”与“已处理”分离的最小生命周期语义。
- [x] 已明确本轮允许对 `Alarm` 做轻量 schema 扩展，但不纳入 WebSocket 告警事件。

## 阶段验收结论（2026-03-29）

- 验收范围：
  - `Alarm` 生命周期实例最小语义是否成立
  - 持续异常是否按稳定实例键维持单一活跃实例
  - 恢复与人工处理是否已分离
  - `GET /alarms`、`resolve-all`、`resolve/{alarm_id}` 的对象级权限边界是否一致
  - 本轮是否保持在“后端最小闭环”范围内，未扩成前端、WebSocket 或 migration 专题
- 验收结果：本轮“报警后端最小闭环修复”已达到阶段完成，可进入阶段收口。
- 已确认：
  - `Alarm` 已按“告警生命周期实例”收敛，字段补齐为 `instance_key / last_seen_at / recovered_at`，人工处理维度保留为 `is_resolved / resolved_at / resolved_by / handling_note`。
  - `AlarmService` 已按稳定实例键处理活跃告警，持续异常数值波动时只刷新同一实例，不再重复插入多条活跃告警。
  - 系统恢复通过 `recovered_at` 表达，人工处理通过 `resolve_*` 与 `handling_note` 表达，二者已可区分、可解释。
  - `GET /alarms`、`resolve-all`、`resolve/{alarm_id}` 已统一走 `get_allowed_device_ids()`，对象级权限边界一致。
  - 已执行 `PYTHONPATH=. venv/bin/pytest -q tests/test_alarm_service.py tests/test_alarm_endpoints.py`，结果为 `6 passed`。
  - 已执行 `python3 -m compileall app/services/alarm_service.py app/api/endpoints/alarms.py app/models/tables.py app/core/database.py`，通过。
- 当前不阻止阶段收口的剩余风险：
  - 其他消费方仍沿用旧 `is_resolved` 解释方式，属于下一轮兼容收敛议题。
  - 生产环境若关闭 runtime schema sync，仍需正式 migration，属于部署落地议题。
  - WebSocket 告警事件仍未补，属于本轮明确非目标。
- 当前阶段结论：
  - 阶段结论：通过。
  - 主题结论：可进入阶段收口；暂不扩张到前端、实时事件或 migration 专题。

## 进度记录

- 2026-03-29：探索线程完成报警链路审计，确认本任务不属于当前“命名迁移分层治理”主题，建议升级为独立正式 PLAN。
- 2026-03-29：探索线程确认当前主问题为“告警生命周期缺失”，去重失效、权限不一致和实时推送缺失是该主问题及其相邻缺口的组合表现。
- 2026-03-29：规范线程锁定本轮术语边界、最小生命周期定义与轻量 schema 扩展方向；明确本轮只交后端闭环，不纳入 WebSocket 告警事件与前端告警中心改版。
- 2026-03-29：后端线程完成稳定实例键、恢复/处理分离、对象级权限边界统一与运行时 schema sync；验收线程复核代码、测试与主区文档，确认“报警后端最小闭环修复”阶段通过，可进入阶段收口。

## 相关文档

- [docs/plans/current-status.md](/Users/todo/MineEnergySystem/docs/plans/current-status.md)
- [docs/plans/handoff.md](/Users/todo/MineEnergySystem/docs/plans/handoff.md)
- [app/application/telemetry_ingestion.py](/Users/todo/MineEnergySystem/app/application/telemetry_ingestion.py)
- [app/services/alarm_service.py](/Users/todo/MineEnergySystem/app/services/alarm_service.py)
- [app/api/endpoints/alarms.py](/Users/todo/MineEnergySystem/app/api/endpoints/alarms.py)
