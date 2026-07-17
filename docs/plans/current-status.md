# Current Status

## 当前总目标

- 当前主主题：`园区光储协同仿真与 EMS 控制`。
- 当前总目标：Task 13 园区级光储总览与策略对比 API 已通过验收；当前进入 Task 14 原有能耗分析页“光储 EMS”工作区。
- 当前执行依据：`docs/plans/PLAN-20260716-campus-pv-storage-simulation.md` 与 `docs/superpowers/plans/2026-07-16-campus-pv-storage-simulation.md`。
- 收敛设计依据：`docs/superpowers/specs/2026-07-17-single-storage-system-convergence-design.md`；只保留一个储能系统，模拟器未来由厂商网关替换。

## 当前阶段

- [x] Task 1：主题治理、固定契约与迁移门禁记录正式完成。
- [x] Task 2：纯电池领域模型、兼容惰性导出及测试正式完成。
- [x] Task 3：持久化模型、静态 migration 与真实三路径验收完成。
- [x] Task 4：扩展仿真遥测入库、状态映射与监控聚合完成。
- [x] Task 5：可复用 MQTT 储能仿真器、确定性场景与默认关闭门禁完成。
- [x] Task 6：储能控制命令生命周期、分类回执分发与超时收敛完成。
- [x] Task 7：储能资产来源、设备级自动控制门禁及原有储能 API 完成。
- [x] Task 8：安全优先实时规则与 EMS 编排完成。
- [x] Task 9：模拟器命令执行、回执状态机与故障注入完成。
- [x] Task 10：原有储能设备工作台、权限门禁、命令时间线与功率趋势完成。
- [x] Task 11：确定性 96 时段日前 MILP 优化器与开源 CBC 依赖完成。
- [x] Task 12：调度计划原子替换、EMS 安全执行、失败回退、每日任务与嵌套 API 完成。
- [x] Task 13：园区级光储总览、三策略同输入重放、权限与显式响应契约完成。
- [ ] Task 14 及后续：按实施计划依赖顺序等待。

## Task 3 完成证据

- 后端可靠性阶段 2A 全部验收通过并完成治理交还；它现在是已完成依赖和历史证据，不是第二个活跃主主题。
- 实现提交：`aa97e3ad`。
- `20260716_0002` 保持静态、offline-safe，仅创建 `storage_asset_profile`、`storage_dispatch_plan` 并增加八个批准遥测扩展。
- fresh、offline、roundtrip 各 682 个对象，共同 SHA-256 为 `b81c0db6aaef07fad85a7b617b005e99e1aaafee382e06da6f378eea6d4cbaec`。
- 三条路径均位于 `20260716_0002`，均保留 `public.energydata` hypertable，并已核对两张新增表和八个扩展列。
- 全量后端：`740 passed, 5 warnings`；Task 3 变更文件 Ruff 检查通过。
- 实际开发库 `campus_energy` 仍在 `20260716_0001`，尚未应用两张 Task 3 表；临时三路径验收通过不等于开发库已经升级。

## 固定契约

- 储能 migration 链：`20260716_0001 -> 20260716_0002 -> 20260717_0003`；当前 head 为 `20260717_0003`。
- 根基线已经拥有基础 `storage_telemetry`；Task 3 只新增 profile、dispatch 和批准的 telemetry 扩展，不得重建基础表。
- `device_category=storage`，`device_subtype=battery_energy_storage_system`。
- 正功率充电、负功率放电；所有模拟遥测必须标记 `data_source=simulated`。
- MQTT 设备侧状态键继续使用 `bms_state`、`pcs_state`、`grid_connection_state`；Task 4 入库时分别映射到 `bms_status`、`pcs_status`、`grid_status`。
- 原有 `StorageMonitorView` 是唯一设备级储能页面；园区级能力进入现有 `EnergyManagement` 的“光储 EMS”工作区，不新增独立储能页面或路由。
- 自动控制全局和单设备均默认关闭；真实接入只替换设备侧适配器，不修改储能业务 API 与页面。

## Task 4 完成证据

- 实现提交：`0e1fd1bc`。
- 仿真 payload 的目标功率、可充放电功率、三个设备状态、命令来源和 `data_source=simulated` 均可落入专属遥测层。
- `active_power=-120.0` 入库与监控聚合后保持负值，不改变放电符号。
- 监控聚合新增目标功率、可用功率、BMS/PCS/并网状态、命令来源和模拟来源指标。
- 完整环境全量后端：`742 passed, 5 warnings`；Task 4 Ruff 检查通过。

## Task 5 完成证据

- 实现包含 `scripts/python/storage_simulator.py`、储能 Settings 门禁、三份环境模板、入口文档及 12 项聚焦测试。
- 五个固定场景、固定 seed、加速时钟、`--print-only`、双控制主题、功率限幅、模拟回执和优雅停止均已实现。
- `--print-only` 已由测试锁定为不创建 MQTT 客户端；直接使用文档命令执行可输出单条合法 JSON。
- 仿真 payload 固定使用储能分类/子型、正充负放，并强制携带 `data_source=simulated`。
- `STORAGE_EMS_ENABLED` 与 `STORAGE_SIMULATION_ENABLED` 在 Python 和所有环境模板中均默认为 `False`。
- 完整环境全量后端：`754 passed, 7 warnings`；Task 5 变更文件 Ruff 与 `git diff --check` 通过。警告仍来自既有默认密钥与本地 LibreSSL 环境。

## Task 6 完成证据

- 新增独立储能控制命令规格与服务，只支持 `set_active_power`、`set_control_mode`、`stop`。
- 功率有限值、资产充放电边界、manual/rule/day_ahead 来源、auto/manual 模式及单设备单个 pending 命令均有测试固定。
- `DeviceControlLog.command_source=storage-control-api`；结构化 `reason` 保留目标、模式、来源、最新 `data_source` 和可选 `simulation_run_id`。
- MQTT 控制回执按 `device_category` 分发；储能走新状态机，非储能继续走既有电容补偿服务，旧导出路径保留兼容。
- 储能 pending 超时任务每分钟执行，且只更新 `storage-control-api` 日志；终态重复回执幂等，冲突迟到回执仅记录、不反转终态。
- 聚焦与兼容回归：`40 passed, 2 warnings`；完整后端：`767 passed, 2 skipped, 7 warnings`。

## Task 7 完成证据

- `StorageAssetProfile.ems_auto_enabled` 默认关闭；`StorageTelemetry` 与 `StorageDispatchPlan` 增加可选 `simulation_run_id`，调度计划来源默认 `calculated`。
- 静态、offline-safe 的 `20260717_0003` 只新增四列和两个运行标识索引，父 revision 固定为 `20260716_0002`。
- fresh、offline、roundtrip 均为 688 个 schema objects，规范化指纹一致；成功后只清理三个固定临时数据库。
- 原有 `/devices/{id}/storage/*` 增加资产档案、控制能力、人工控制及模拟能力/控制接口；未建立第二套储能 API。
- viewer 可读；maintainer/operator/admin 可在位置范围内控制；设备级自动授权只有管理员可改变，并要求已有档案和新鲜健康遥测。
- 模拟接口默认 404，启用后只发布到独立 simulation topic；配置与生产控制 topic 重叠时返回 503。
- 完整后端：`783 passed, 2 skipped, 7 warnings`；OpenAPI 储能路径生成、Ruff 与差异检查通过。

## Task 8 完成证据

- 新增不可变 `StorageRuleInput` / `StorageRuleDecision` 纯规则，固定优先级为 safety、PV surplus、demand limit、tariff、idle。
- 规则覆盖 5 kW 死区、SOC/温度滞回、最小运行/停止时长和换向待机；正充负放符号保持不变。
- BMS/PCS/并网故障及非有限输入立即返回安全零功率；缺失或超过 5 分钟的关键遥测由 EMS 层拒绝自动计算。
- EMS 同时检查全局 `STORAGE_EMS_ENABLED`、设备级 `ems_auto_enabled`、auto 模式、pending 与目标差值，只复用 Task 6 控制服务下发。
- 园区负荷/光伏继续读取公共 `EnergyData`；峰平谷时段复用现有项目配置，没有新增第二套电价时间表。
- 60 秒任务只在全局开关开启时注册；每轮只选择设备级已授权档案，单设备异常独立回滚，不中断其他设备。
- 聚焦测试 `24 passed, 2 warnings`；完整后端 `801 passed, 2 skipped, 7 warnings`，Ruff 与差异检查通过。

## Task 9 完成证据

- 实现提交：`6254dd8a`。
- 模拟器按 `accepted -> running -> success` 执行储能功率命令，实际功率连续三个步长满足 `max(2.5 kW, 目标功率 2%)` 容差后才进入成功终态。
- SOC 上下限、过温和 PCS 故障具有明确拒绝或归零语义；`communication_loss` 丢弃遥测与回执，使平台现有超时任务按标准契约收敛。
- `set_active_power`、`set_control_mode` 和 `stop` 共用同一在途命令状态；终态按 `command_id` 缓存，重复投递只复发完全相同的终态回执。
- 每个模拟器实例生成一个 UUID `simulation_run_id`，其遥测与回执均携带该标识和 `data_source=simulated`。
- 场景、速度和固定故障集合只接受 simulation topic；仿真门禁默认关闭，真实控制 topic 明确拒绝 simulator-only 动作。
- 聚焦测试 `19 passed`；完整后端 `811 passed, 2 skipped, 7 warnings`；Task 9 变更文件 Ruff 与差异检查通过。

## Task 10 完成证据

- 实现提交：`a83cbc49`。
- 原有 `StorageMonitorView` 内完成数据来源、目标/实际/可用功率、BMS/PCS/并网状态、人工控制、管理员自动授权和命令时间线；未新增页面或路由。
- viewer 与 pending 状态均禁止冲突控制；`accepted` 只表示已接收，后续状态来自控制日志刷新或 WebSocket 事件。
- 储能工作台及页面相关回归 `27 passed`；typecheck、build 和变更文件 ESLint 通过。
- 前端全量 `365 passed, 4 failed`；四项均为本任务未修改的既有基线失败（`EnergyManagement` 三项、`DeviceTrendPanel` 一项）。

## Task 11 完成证据

- 实现提交：`48b91c90`。
- `PuLP 3.3.0` 与内置开源 CBC 已固定；没有引入 Gurobi 等商业运行时。
- 96 时段模型覆盖充放电互斥、15%-85% SOC、终端 SOC、非负电网购电、需量削峰和固定种子可复现性。
- 非 96 时段、非有限值、无效效率和初始 SOC 直接拒绝；不可行模型转换为带 solver status 的领域异常。
- 聚焦测试 `6 passed`；完整后端 `817 passed, 2 skipped, 7 warnings`；Ruff 与干净 Python 3.12 依赖检查通过。

## Task 12 完成证据

- 实现提交：`b10991d5`。
- 优化成功后才在单事务中原子替换同一设备日期的完整 96 行；优化失败完全保留上一有效计划。
- 实时 EMS 优先读取当前计划槽位，再应用 SOC、温度、设备状态、通信与人工接管安全边界；无有效计划回退 Task 8 规则。
- 新增 current、generate、status 三条原储能嵌套 API；viewer 可读，maintainer/operator/admin 可生成。
- 每日计划任务复用既有 `STORAGE_DAILY_DISPATCH_TIME`，且只随全局储能 EMS 门禁注册。
- 聚焦 `29 passed`，储能回归 `57 passed`，完整后端 `829 passed, 2 skipped, 7 warnings`；Ruff 与 OpenAPI 生成通过。

## Task 13 完成证据

- 实现提交：`e0508eed`。
- 新增 `/energy/storage/overview` 与 `/energy/storage/comparison`；显式设备先走既有访问校验，系统聚合按位置范围设备集合过滤。
- 总览聚合负荷、光伏、电网、储能和容量加权 SOC，并返回目标/实际偏差、当前计划状态、求解状态、来源、运行标识与输入时效；缺失计划时不伪造规则回退。
- 基线、规则、日前三策略只重放同一个不可变 96 时段输入；返回 `scenario_key`、seed、initial SOC 和输入 SHA-256，成本构成、峰值、自用率、弃光、外送、吞吐、等效循环和终端 SOC 均由原序列计算。
- 没有真实执行证据的跨策略 `plan_execution_rate` 显式为 `null`，重放物理可执行率单列为 `feasible_slot_rate`。
- 聚焦 `15 passed, 2 warnings`，完整后端 `842 passed, 2 skipped, 7 warnings`；Ruff、两条 OpenAPI 响应模型与差异检查通过。未新增 migration，未修改前端。

## 当前待办

1. 前端角色按 TDD 执行 Task 14，只在现有 `EnergyManagement` 页面增加“光储 EMS”工作区，不新增路由或第二套储能页面。
2. 前端通过 Task 13 两条只读聚合 API 和既有设备调度生成 API 展示能流、目标/实际、来源、计划状态与三策略指标；不得伪造优化成功或回退状态。
3. 保持 `data_source=simulated/real` 持续可见，缺失值显示 `--`，跨策略 `plan_execution_rate=null` 不得展示为 100% 执行成功。
4. 正常 MQTT 与依赖计划表的运行联调前，显式升级并复核 `campus_energy` 到 `20260717_0003`。

## 当前验收判断

- 阶段 2A：完成并归入历史依赖。
- 园区光储：唯一活跃主主题。
- Task 3：通过并正式完成。
- Task 4：通过并正式完成。
- Task 5：通过并正式完成。
- Task 6：通过并正式完成。
- Task 7：通过并正式完成。
- Task 8：通过并正式完成。
- Task 9：通过并正式完成。
- Task 10：通过并正式完成。
- Task 11：通过并正式完成。
- Task 12：通过并正式完成。
- Task 13：通过并正式完成。
- Task 14：已解除依赖，尚未开始。
- 下一接手角色：前端角色。
