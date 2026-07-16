# Handoff

## 当前主题

- `园区光储协同仿真与 EMS 控制`
- 正式 PLAN：`docs/plans/PLAN-20260716-campus-pv-storage-simulation.md`
- Task 1 规格审查与质量审查均通过，正式完成。
- Task 2 规格审查与质量审查均通过，正式完成；Task 3 及持久化下游仍依赖当前未满足的持久化准入门禁。

## 已知信息

- 固定设备身份：`device_category=storage`、`device_subtype=battery_energy_storage_system`。
- 固定功率符号：正功率充电，负功率放电。
- 仿真数据固定标记：`data_source=simulated`。
- Task 2 实现文件：`app/domain/storage_simulation.py`；兼容性修复：`app/domain/__init__.py`；测试：`tests/test_storage_simulation_domain.py`。
- Task 2 按 TDD 完成有效 RED-GREEN 循环；最终核心测试 `77 passed`，协调者相关回归复验 `136 passed`，三个变更文件 Ruff 检查通过。
- 无 `DATABASE_URL` 的隔离子进程导入 `StorageAssetConfig` 通过。
- 工具契约测试 `tests/test_backend_tooling_contracts.py` 为 13 passed。
- offline SQL 在 revision `20260412_0003` 的 `result.fetchone()` 处失败。
- fresh、migration-built existing、runtime-sync existing 三类 PostgreSQL fixture 缺失，不能声称升级路径通过。
- 前一主题后端可靠性阶段 2A 已由用户批准暂停并归档，待恢复；不是完成状态。

## 两类门禁

- 主题切换门禁：已满足。阶段 2A 经用户批准暂停，主题切换时快照已归档。
- 持久化准入门禁：未满足。offline SQL、fresh PostgreSQL、migration-built existing、runtime-sync existing 尚未全部通过。
- 依赖关系：Task 2 已在主题切换门禁范围内完成；Task 3 及所有持久化下游仍同时依赖两类门禁，不得提前启动。

## 下一棒

### Task 2 已验收完成

- 纯领域模型、兼容惰性导出和单元测试已完成，规格审查与质量审查均通过。
- 验收证据为核心 `77 passed`、协调者相关复验 `136 passed`、Ruff 通过和无 `DATABASE_URL` 隔离导入通过。
- 未新增或修改数据库模型，未创建 migration，未实现 Task 3。

### 规则 / 后端可靠性阶段 2A：持久化前

- 下一步恢复后端可靠性阶段 2A 为主主题或完成等价迁移门禁治理。
- 只有取得 offline SQL、fresh PostgreSQL、migration-built existing 和 runtime-sync existing 全部通过证据后，才可解除持久化阻塞。
- 门禁通过后才交后端执行 Task 3；当前不得交后端开始持久化实现。

## 限制条件

- 不实现电化学、PCS 底层控制、配电网潮流或真实厂商协议。
- 不修改后端可靠性阶段 2A 的 models、migrations、部署或运行语义。
- 不把命令入队视为执行成功；后续控制与回执必须分层。
- 前后端并行前必须建立单一 topic、payload、API 和状态契约载体。

## 仍需确认的风险

- `storage_telemetry` 虽在现有 metadata 中出现，但没有正式 migration 承载，Task 3 不能直接假定表已存在。
- 阶段 A 的 MQTT topic/payload、阶段 B 的回执状态集、阶段 C 的基准收益口径尚待后续任务固定。

## 交接结论

- Task 2 已正式完成并收口。
- 当前交规则 / 后端可靠性阶段 2A 恢复迁移门禁治理；只有门禁通过后才交后端执行 Task 3。
- Task 3 及所有依赖持久化的任务保持阻塞，直到阶段 2A 门禁恢复并通过。
