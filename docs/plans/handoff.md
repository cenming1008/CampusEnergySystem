# Handoff

## 当前主题

- `园区光储协同仿真与 EMS 控制`
- 正式 PLAN：`docs/plans/PLAN-20260716-campus-pv-storage-simulation.md`
- 当前处于 Task 1 治理完成、Task 2 待实施、Task 3 持久化阻塞状态。

## 已知信息

- 固定设备身份：`device_category=storage`、`device_subtype=battery_energy_storage_system`。
- 固定功率符号：正功率充电，负功率放电。
- 仿真数据固定标记：`data_source=simulated`。
- 工具契约测试 `tests/test_backend_tooling_contracts.py` 为 13 passed。
- offline SQL 在 revision `20260412_0003` 的 `result.fetchone()` 处失败。
- fresh、migration-built existing、runtime-sync existing 三类 PostgreSQL fixture 缺失，不能声称升级路径通过。
- 前一主题后端可靠性阶段 2A 已由用户批准暂停并归档，待恢复；不是完成状态。

## 下一棒

### 后端角色：Task 2

- 只实现不依赖 ORM、数据库、migration 或真实 MQTT broker 的纯领域模型及其单元测试。
- 固定功率符号、SOC 边界、能量平衡、效率和时间步语义。
- 不新增或修改数据库模型，不创建 migration，不实现 Task 3。
- 若 Task 2 设计需要持久化字段才能成立，应停止并交回规则角色，不得绕过门禁。

### 规则角色：持久化前

- 在 Task 3 前恢复后端可靠性阶段 2A 为主主题或完成等价门禁治理。
- 只有取得 offline SQL、fresh PostgreSQL、migration-built existing 和 runtime-sync existing 全部通过证据后，才可解除持久化阻塞。

### 验收角色

- 对照正式 PLAN 核对 Task 2 是否保持纯领域边界。
- 核对固定契约未漂移，且没有用 ORM metadata 或 runtime sync 偷渡持久化结构。

## 限制条件

- 不实现电化学、PCS 底层控制、配电网潮流或真实厂商协议。
- 不修改后端可靠性阶段 2A 的 models、migrations、部署或运行语义。
- 不把命令入队视为执行成功；后续控制与回执必须分层。
- 前后端并行前必须建立单一 topic、payload、API 和状态契约载体。

## 仍需确认的风险

- Task 2 的领域对象边界和精确输入输出仍需后端角色通过测试锁定。
- `storage_telemetry` 虽在现有 metadata 中出现，但没有正式 migration 承载，Task 3 不能直接假定表已存在。
- 阶段 A 的 MQTT topic/payload、阶段 B 的回执状态集、阶段 C 的基准收益口径尚待后续任务固定。

## 交接结论

- 当前交接给后端角色执行 Task 2 纯领域模型。
- Task 3 及所有依赖持久化的任务保持阻塞，直到阶段 2A 门禁恢复并通过。
