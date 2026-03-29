# Handoff

## 当前主题
- 当前主主题：报警链路审计与最小修复路径分析
- 当前执行依据：
  - [PLAN-20260329-alarm-pipeline-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260329-alarm-pipeline-audit.md)

---

## 探索结论
### 当前任务
- 探索线程已完成 MQTT 遥测、报警检测、报警接口、权限边界和 WebSocket 推送链路审计；下一棒应先交规范，再交后端。

### 当前结论
- 当前主问题不是 MQTT 断链，而是“系统只有报警事件记录，没有稳定的告警生命周期模型”。
- 去重失效、处理接口权限不一致、WebSocket 不推告警事件，是同一主问题及其相邻缺口叠加出来的多处子症状。
- 当前 `Alarm` 表只能表达“某时刻创建了一条报警记录，以及后来是否被人工标记处理”，不能稳定表达“持续异常 / 恢复 / 当前状态”。
- 当前 WebSocket 只广播 `telemetry_update`，不会推送 `alarm_created` / `alarm_resolved` / `alarm_updated`。

---

## 探索 -> 规范
### 当前任务
- 规范线程先锁定本主题名称、生命周期术语、最小 schema 边界，以及本轮是否纳入告警实时事件。

### 当前仍有行动价值的信息
- `AlarmService.should_create_alarm()` 当前以带实时值的 `message` 去重，持续异常值一旦变化就会反复建新记录。
- `GET /alarms` 用 `location_scope` 过滤，但 `resolve-all` / `resolve/{alarm_id}` 缺对象级权限校验。
- `Alarm` 当前更像事件表，不是生命周期实例表。
- `TelemetryBroadcastData.power` 取值为 `record.flow_rate`，说明遥测广播映射也存在责任散落问题，但这不是本轮第一优先级主因。

### 仅允许的下一步
- 锁定以下术语：
  - 报警事件记录
  - 持续异常实例
  - 恢复
  - 已处理
- 明确本轮是“兼容扩展现有 Alarm 模型”还是允许轻量 schema 扩展。
- 明确 WebSocket 告警事件是否纳入本轮最小修复。

### 禁止扩张
- 不把本轮扩成前端告警中心改版。
- 不跳过生命周期建模，直接在 message 文案层修补去重。
- 不在未锁边界前推倒重做 MQTT 或告警全链路。

## 规范结论
### 当前任务
- 规范线程已锁定术语、生命周期最小定义、轻量 schema 边界与线程路径，当前可直接交后端线程。

### 当前结论
- `Alarm` 本轮按“告警生命周期实例”理解，不再继续按“单次报警事件流水”理解。
- “恢复”是系统状态变化；“已处理”是人工动作；二者必须分离。
- “活跃告警”是仍在持续异常中的实例，不等同于“未处理告警”。
- 本轮允许对现有 `Alarm` 做轻量 schema 扩展，但不新建完整事件流水表。
- 本轮明确不纳入 WebSocket 告警事件，也不进入前端告警中心改版。

### 后端最低语义目标
- 让同一设备、同一类别、同一来源的持续异常，在未恢复前只对应一个活跃实例。
- 让后端至少能解释：
  - 首次触发
  - 持续中
  - 已恢复
  - 已处理
- 让对象级权限在查询与处理接口上保持一致。

## 规范 -> 后端
### 当前任务
- 后端线程按最小修复路径处理主问题闭环，不做顺手重构。

### 当前仍有行动价值的信息
- 优先级 1：
  - 稳定告警判重键
  - 让持续异常不会因实时值变化反复生成新报警
- 优先级 2：
  - 让查询与处理接口权限边界一致
- 优先级 3：
  - 用最小兼容方式表达恢复与人工处理分离
- 当前 MQTT 遥测到报警检测并未断链，重点不是“接通”，而是“收敛生命周期和职责边界”。

### 仅允许的下一步
- 只做最小闭环：
  - 去重逻辑
  - 生命周期最小表达
  - 处理接口对象级权限
  - 现有 `Alarm` 的轻量 schema 扩展
- 保持兼容，不扩大接口影响范围，除非 PLAN 明确更新。

### 禁止扩张
- 不直接重构整个告警中心或监控页。
- 不顺手改无关 MQTT / 设备监控聚合逻辑，除非它阻塞主问题闭环。
- 不把 `is_resolved` 临时补丁继续扩大成更深语义混乱。
- 不补 WebSocket 告警事件。
- 不新建完整告警事件流水或完整状态机体系。

### 打回条件
- 发现要修复去重或恢复逻辑时，必须新增生命周期字段或状态定义，但规范未拍板。
- 发现 WebSocket 告警事件需要前端同步契约，已超出纯后端闭环。
- 发现仅靠轻量 schema 扩展无法表达最小生命周期、必须引入新表或 breaking change。
- 发现真实根因已转移到前端消费层，而不是后端事件与权限层。

## 后端 -> 验收
### 当前任务
- 后端线程已完成最小修复，现交验收核对是否真正解决主问题，而不是只压住一个子症状。

### 当前后端已完成
- 已在 [tables.py](/Users/todo/MineEnergySystem/app/models/tables.py) 为 `Alarm` 补齐 `instance_key / last_seen_at / recovered_at`，保留 `is_resolved / resolved_* / handling_note` 作为人工处理维度。
- 已在 [alarm_service.py](/Users/todo/MineEnergySystem/app/services/alarm_service.py) 改为“活跃实例 upsert + 未命中条件时写 `recovered_at`”的最小生命周期实现，不再依赖带实时值的 `message` 去重。
- 已在 [alarms.py](/Users/todo/MineEnergySystem/app/api/endpoints/alarms.py) 让 `GET /alarms`、`resolve-all`、`resolve/{alarm_id}` 统一走 `get_allowed_device_ids()` 对象级权限边界。
- 已在 [database.py](/Users/todo/MineEnergySystem/app/core/database.py) 补 runtime schema sync、索引和生产必需字段校验。
- 已补测试：
  - [test_alarm_service.py](/Users/todo/MineEnergySystem/tests/test_alarm_service.py)
  - [test_alarm_endpoints.py](/Users/todo/MineEnergySystem/tests/test_alarm_endpoints.py)

### 最小验证
- 已验证同一持续异常在数值波动时不会重复插入新活跃告警，而是刷新同一实例的 `last_seen_at`。
- 已验证恢复后会写入 `recovered_at`，且不会自动把人工处理字段一并写掉。
- 已验证人工处理发生在 `is_resolved / resolved_at / resolved_by / handling_note` 维度上，可与 `recovered_at` 区分。
- 已验证 `resolve-all` 与 `resolve/{alarm_id}` 会把对象级权限范围传入服务层。
- 已执行 `PYTHONPATH=. venv/bin/pytest -q tests/test_alarm_service.py tests/test_alarm_endpoints.py`，结果为 `6 passed`。

### 验收关注点
- MQTT 遥测到报警检测链路是否仍然连通。
- 同一持续异常是否仍会因实时值变化重复生成多条未处理报警。
- `GET /alarms`、`resolve-all`、`resolve/{alarm_id}` 的对象级权限边界是否一致。
- `Alarm` 的生命周期语义是否已从“纯事件记录”提升到“至少可解释持续异常与处理状态”。
- 是否已明确本轮不纳入 WebSocket 告警事件，且实现未顺手扩张到前端契约。
- 若要继续追问“活跃告警统计”在设备监控/驾驶舱是否完全一致，请先认定为下一轮兼容消费收敛，而不是本轮未完成。

---

## 验收结论
### 当前任务
- 验收线程已完成本轮“报警后端最小闭环修复”阶段验收，当前结论可直接作为阶段收口依据。

### 当前结论
- 本轮目标已完成：`Alarm` 已按“告警生命周期实例”收敛，持续异常按稳定实例键维持单一活跃实例，恢复与人工处理已分离。
- 权限边界已收敛：`GET /alarms`、`resolve-all`、`resolve/{alarm_id}` 已统一使用 `get_allowed_device_ids()`。
- 非目标已遵守：未进入前端线程，未补 WebSocket 告警事件，未扩成告警中心改版，未推进 MQTT / 广播框架重构，未展开 migration 专题。
- 验证已补齐：已执行 `PYTHONPATH=. venv/bin/pytest -q tests/test_alarm_service.py tests/test_alarm_endpoints.py`，`6 passed`；已执行 `python3 -m compileall app/services/alarm_service.py app/api/endpoints/alarms.py app/models/tables.py app/core/database.py`，通过。
- 当前主题结论：本轮阶段通过，可进入阶段收口。

### 为什么可以进入阶段收口
- 当前剩余风险已经明确落在“旧消费方兼容收敛”“生产 migration 落地”“WebSocket 告警事件补点”这些本轮外议题上，不再构成本轮后端最小闭环未完成。
- 当前不需要继续打回后端追加实现；若后续继续推进，应另开下一轮兼容收敛或部署落地动作。

## 验收 -> 阶段收口
### 当前任务
- 当前实现轮次已完成，下一步只需判断本主题是否停在“后端最小闭环已建立”的阶段，还是继续开下一轮兼容消费收敛。

### 仅允许的下一步
- 可以做阶段收口：确认本轮完成、保留剩余风险、决定是否保留主题继续推进下一轮。
- 若继续推进，只能新开“兼容消费收敛”或“migration 落地”子轮次，不能伪装成本轮未验收通过。

### 禁止扩张
- 不以“阶段收口”为名义打回前端。
- 不把 WebSocket 告警事件、前端告警中心改版、MQTT / 广播框架重构重新塞回本轮。
- 不把全仓旧 `is_resolved` 消费兼容收敛重新定义成本轮后端闭环缺口。

### 再次进入验收条件
- 若后续新开兼容消费收敛或部署落地轮次，需回写新的范围、非目标、验证结果后再进入下一次验收。

## 交给验收
### 当前任务
- 当前轮次已完成后端最小闭环，可直接进入验收。

### 验收关注点
- 正式 PLAN、`current-status.md`、`handoff.md` 是否一致。
- 是否已明确主问题与各子症状的对应关系。
- 是否已按最小修复路径处理，而未扩成告警中心重构。

---

## 每日归档入口

- [2026-03-27 交接快照](./daily/2026-03/2026-03-27-handoff.md)
- [2026-03-28 交接快照](./daily/2026-03/2026-03-28-handoff.md)
