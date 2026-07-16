# Handoff

## 当前主题

- `园区光储协同仿真与 EMS 控制`
- 正式 PLAN：`docs/plans/PLAN-20260716-campus-pv-storage-simulation.md`
- Task 1 治理实现已提交，当前处于质量整改 / 复核阶段，尚未验收通过。
- Task 2 只依赖且已满足主题切换门禁；Task 3 及持久化下游还依赖当前未满足的持久化准入门禁。

## 已知信息

- 固定设备身份：`device_category=storage`、`device_subtype=battery_energy_storage_system`。
- 固定功率符号：正功率充电，负功率放电。
- 仿真数据固定标记：`data_source=simulated`。
- 工具契约测试 `tests/test_backend_tooling_contracts.py` 为 13 passed。
- offline SQL 在 revision `20260412_0003` 的 `result.fetchone()` 处失败。
- fresh、migration-built existing、runtime-sync existing 三类 PostgreSQL fixture 缺失，不能声称升级路径通过。
- 前一主题后端可靠性阶段 2A 已由用户批准暂停并归档，待恢复；不是完成状态。

## 两类门禁

- 主题切换门禁：已满足。阶段 2A 经用户批准暂停，主题切换时快照已归档。
- 持久化准入门禁：未满足。offline SQL、fresh PostgreSQL、migration-built existing、runtime-sync existing 尚未全部通过。
- 依赖关系：Task 2 只依赖主题切换门禁；Task 3 及所有持久化下游同时依赖两类门禁。

## 下一棒

### 后端角色：Task 2

- 只实现不依赖 ORM、数据库、migration 或真实 MQTT broker 的纯领域模型及其单元测试。
- 固定 `500 kWh / 250 kW`，SOC 为 `0-100` 百分比且硬边界为 `10%-90%`；功率用 `kW`、能量用 `kWh`、时间输入用秒。
- 正功率充电、负功率放电；令 `Δt_h=seconds/3600`，充电 `ΔE=P*ηc*Δt_h`，放电 `ΔE=P/ηd*Δt_h`。
- 依次应用爬坡、额定功率和 SOC 边界饱和，并返回实际应用功率；非有限输入、`seconds<=0` 或非法配置必须抛出 `ValueError`。
- 确定性样例：`500 kWh`、SOC `50%`、`ηc=0.95`、`100 kW`、`3600 s` 时，新 SOC 为 `69%`；SOC `20%`、下限 `10%`、`ηd=0.95`、请求 `-250 kW`、`3600 s` 时，饱和到 `10%` 且实际功率为 `-47.5 kW`。
- 不新增或修改数据库模型，不创建 migration，不实现 Task 3。
- 若 Task 2 设计需要持久化字段才能成立，应停止并交回规则角色，不得绕过门禁。

### 规则角色：持久化前

- 在 Task 3 前恢复后端可靠性阶段 2A 为主主题或完成等价门禁治理。
- 只有取得 offline SQL、fresh PostgreSQL、migration-built existing 和 runtime-sync existing 全部通过证据后，才可解除持久化阻塞。

### 验收角色

- 先复核 Task 1 本轮质量整改；复核完成前不得写成 Task 1 已验收通过。
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

- 当前先交验收角色复核 Task 1 质量整改；Task 2 已满足其唯一门禁，复核后可交后端执行纯领域模型。
- Task 3 及所有依赖持久化的任务保持阻塞，直到阶段 2A 门禁恢复并通过。
