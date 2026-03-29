# Current Status

## 当前总目标
- 以“报警链路审计与最小修复路径分析”为当前主主题，先完成告警生命周期最小闭环，再交验收判断是否达到阶段完成。
- 让 [PLAN-20260329-alarm-pipeline-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260329-alarm-pipeline-audit.md) 成为当前执行依据，避免后续线程把报警问题误当成单点 bug 或继续依赖聊天接力。

---

## 当前阶段
- [x] 探索线程已确认：本轮“CampusEnergySystem 报警逻辑问题”不属于当前主区原主题“命名迁移分层治理”
- [x] 已建立正式 PLAN：[PLAN-20260329-alarm-pipeline-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260329-alarm-pipeline-audit.md)
- [x] 已完成 MQTT 遥测 -> 报警检测 -> 报警查询 / 处理 -> WebSocket 推送链路审计
- [x] 已确认主问题为“告警生命周期缺失”，不是单纯 MQTT 断链
- [x] 规范线程已锁定主题边界、生命周期术语、最小模型语义与轻量 schema 扩展方向
- [x] 后端线程已完成最小闭环实现：稳定实例键、恢复/处理分离、处理接口对象级权限一致
- [x] 验收线程已复核：本轮“报警后端最小闭环修复”达到阶段完成
- [ ] 当前主题进入阶段收口判断，不直接扩成下一轮实现

---

## 当前阻塞
- 其他消费方仍有旧 `is_resolved` 解释方式，但这属于下一轮兼容收敛，不构成本轮后端最小闭环阻塞。
- WebSocket 当前仍只广播 `telemetry_update`，但本轮已明确不纳入告警事件补点；进入阶段收口时应继续按非目标处理。
- 生产环境若关闭运行时 schema sync，仍需要正式 migration 才能承接 `instance_key / last_seen_at / recovered_at` 新字段；这是部署落地风险，不是本轮闭环阻塞。

## 当前待办
- [x] 判定本轮报警问题应新开主题，而非并入“命名迁移分层治理”
- [x] 建立正式 PLAN，沉淀链路审计结论与最小修复路径
- [x] 规范线程锁定：
  - 主题名
  - 生命周期术语
  - 是否允许轻量 schema 扩展
  - 本轮不纳入告警实时事件
- [x] 后端线程已处理主问题闭环：
  - 稳定去重键
  - 生命周期最小表达
  - 查询 / 处理权限边界一致性
- [x] 验收线程已复核“链路不断、去重稳定、权限一致、生命周期可解释”达到阶段完成
- [ ] 进入阶段收口，判断是否保留本主题继续推进兼容消费收敛，还是结束当前主题

## 当前验证结论
- 已确认 MQTT 遥测到报警检测并未断链：`process_payload_dict()` 调用 `persist_device_data()`，后者进入 `ingest_telemetry_use_case()`，依次执行入库、报警检测和健康状态更新。
- 已确认当前去重逻辑存在高概率失效：`AlarmService.should_create_alarm()` 以 `device_id + message + 未解决 + 最近 5 分钟` 判断重复，而 `message` 直接拼接实时值。
- 已确认权限边界不一致：
  - `GET /alarms` 受 `location_scope` 过滤
  - `resolve-all` / `resolve/{alarm_id}` 仅受角色限制，不校验对象级设备访问范围
- 已确认 `Alarm` 模型目前只能稳定表达“某时刻生成了一条报警事件，以及后来是否被人工标记处理”，不能稳定表达：
  - 持续异常实例
  - 恢复时间 / 恢复事件
  - 当前异常是否仍在持续
  - 同一告警实例的最后观测值
- 已确认本轮术语边界为：
  - `Alarm` 按“告警生命周期实例”理解
  - “恢复”是系统状态变化
  - “已处理”是人工动作
  - “活跃告警”不等同于“未处理告警”
- 已确认本轮允许对 `Alarm` 做轻量 schema 扩展，但不新建完整事件流水，也不纳入 WebSocket 告警事件。
- 已完成 `Alarm` 轻量 schema 扩展：
  - `instance_key`
  - `last_seen_at`
  - `recovered_at`
- 已将去重从“带实时值的 `message`”切换为“同设备 + 同类别 + 同来源的稳定实例键”，持续异常时只更新现有活跃实例，不再重复插入新行。
- 已实现系统恢复表达：当本轮遥测未再命中活跃实例的异常条件时，记录 `recovered_at`，且不复用人工处理字段。
- 已将 `resolve-all` / `resolve/{alarm_id}` 收敛到与 `GET /alarms` 一致的对象级权限边界，统一使用 `get_allowed_device_ids()`。
- 已执行 `PYTHONPATH=. venv/bin/pytest -q tests/test_alarm_service.py tests/test_alarm_endpoints.py`，`6 passed`。
- 已执行 `python3 -m compileall app/services/alarm_service.py app/api/endpoints/alarms.py app/models/tables.py app/core/database.py`，通过。
- 已额外发现遥测广播字段错配：`TelemetryBroadcastData.power` 当前取的是 `record.flow_rate`，说明遥测广播映射与告警/入库责任边界已有松动，但不属于本轮后端闭环范围。
- 验收线程已复核代码、测试与主区文档，确认本轮已达到“报警后端最小闭环修复”的阶段完成，剩余风险均落在本轮外问题，可进入阶段收口。

## 当前剩余风险
- `device_monitor_service`、`campus_service`、报表导出等其他消费方仍主要按 `is_resolved` 解释告警状态；若下一轮要让“活跃 vs 未处理”在更多页面/报表严格一致，需单独做兼容收敛。
- 生产环境若不开 runtime schema sync，本轮新增字段仍需正式 migration 落地，否则会在启动校验阶段失败。
- 本轮只验证了告警服务与端点层，没有补 WebSocket 告警事件，也没有扩到前端告警中心消费。
- `TelemetryBroadcastData.power = record.flow_rate` 的广播映射问题仍在，但当前已确认其不属于本轮告警后端最小闭环缺口。

---

## 每日归档入口

- [2026-03-27 状态快照](./daily/2026-03/2026-03-27-status.md)
- [2026-03-28 状态快照](./daily/2026-03/2026-03-28-status.md)
