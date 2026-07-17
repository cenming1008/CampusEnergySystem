# PLAN-20260716 园区光储协同仿真与 EMS 控制

## 目标

- 完成系统级储能仿真、MQTT 遥测、控制回执、规则 EMS、日前优化和收益对比。

## 前置门禁

### 主题切换门禁

- 条件：后端可靠性阶段 2A 全部验收通过并完成治理交还。
- 当前判定：**已满足**。阶段 2A 已完成静态根基线、三路径一致性、开发库重建、启动只校验和阻断式 CI workflow 配置验收；Task 9 已将园区光储恢复为唯一主主题。
- 历史与验收证据保存在 `docs/plans/daily/2026-07/` 和 `docs/plans/backend-reliability-phase2a-acceptance.md`。

### 持久化准入门禁

- 条件：静态根 migration、fresh、offline、roundtrip、启动只校验、开发库重建和 CI workflow 阻断配置均有验收证据。
- 当前判定：**已满足**。三条路径各得到 628 个 schema objects，规范化指纹共同 SHA-256 为 `9f52eafa4140a7328074fa3c6fa4414fe3107a5fa49cbca23a34de60b5acf42c`；`campus_energy` 已重建到 `20260716_0001`。
- 储能 migration 固定使用 `revision = "20260716_0002"`、`down_revision = "20260716_0001"`。
- 根基线已经拥有基础 `storage_telemetry` 表；Task 3 仅新增 storage profile、dispatch 和已批准的 telemetry 扩展，不得重建基础表。

门禁裁决：

- Task 2 的纯领域模型已在主题切换门禁范围内完成并通过规格与质量审查，未触碰数据库模型、migration 或持久化实现。
- Task 3 已按 TDD 完成并通过持久化验收；`20260716_0002` 三路径均为 682 个 schema objects，规范化指纹一致。
- Task 4 已解除持久化依赖，下一角色为后端储能角色，继续接入扩展仿真遥测。

## 非目标

- 不实现电化学、PCS 底层控制、配电网潮流或真实厂商协议。
- 不修改已验收的 `20260716_0001` 根基线。Task 3 只允许按批准边界修改或新增 storage 模型与 `20260716_0002` migration，不得重建基础 `storage_telemetry`，不得扩张其他设备类型的模型或 migration。
- 不把“命令已入队”视为“设备执行成功”，控制闭环必须保留独立回执语义。

## 范围

- 系统级光伏、负荷与电池储能功率、能量和 SOC 仿真。
- 仿真遥测经既有 MQTT 接入链进入园区 EMS，并保留模拟数据来源标记。
- 储能控制命令、执行回执和规则 EMS 闭环。
- 日前调度优化、基准策略对比及收益证据。
- 与储能设备相关的公共数据、专属遥测、参数快照、控制与回执分层。

## 固定契约

- `device_category=storage`
- `device_subtype=battery_energy_storage_system`
- 正功率充电，负功率放电。
- 仿真数据必须标记 `data_source=simulated`。

补充约束：

- 功率符号约定必须在领域模型、MQTT payload、持久化、API 和前端展示中保持一致。
- SOC、SOH、充放电功率等储能专属字段进入专属遥测层；通用可比较字段才进入公共层。
- 控制命令与执行回执分层留痕，回执必须能区分已接收、执行中、成功和失败。
- 后续前后端并行前，必须在本 PLAN 或专门契约文档中锁定 topic、payload、状态集、API 和空值语义。

## Task 2 最小验收契约

### 单位与额定参数

- SOC 单位为百分比，取值范围为 `0-100`。
- 功率单位为 `kW`，正功率充电、负功率放电。
- 能量单位为 `kWh`，时间输入单位为秒。
- 额定容量、额定充放电功率、SOC 上下限、充电效率 `ηc`、放电效率 `ηd` 和爬坡率均为 `StorageAssetConfig` 的显式可配置参数，不得在领域模型中硬编码。
- 本阶段默认验收场景 / 基准配置使用额定容量 `500 kWh`、额定充放电功率 `250 kW`、SOC 硬边界 `10%-90%`；这些数值不是领域模型固定常量。
- 效率必须在 `(0, 1]`，爬坡率必须为有限正数。

### 状态演化与饱和

- 先将秒换算为小时：`Δt_h = seconds / 3600`。
- 充电时 `P >= 0`：`ΔE = P * ηc * Δt_h`。
- 放电时 `P < 0`：`ΔE = P / ηd * Δt_h`，因此 `ΔE` 为负。
- 每一步先应用爬坡约束 `|P_t - P_(t-1)| <= ramp_rate_kw_per_s * seconds`，再应用 `StorageAssetConfig` 中的额定功率约束，最后按配置中的 SOC 上下限对实际功率和能量变化进行饱和；默认验收场景相应使用 `250 kW` 和 `10%-90%`。
- 边界饱和后必须返回实际应用功率和新 SOC；不得只截断 SOC 而保留一个物理上未执行的请求功率。

### 错误契约

- 任一非有限输入，包括 `NaN`、正无穷或负无穷，抛出 `ValueError`。
- `seconds <= 0` 抛出 `ValueError`。
- 非法配置抛出 `ValueError`，至少包括非正容量、非正额定功率、SOC 边界次序错误、初始 SOC 越界、效率不在 `(0, 1]`、爬坡率非有限或非正。

### 确定性测试样例

1. **充电效率样例**：容量 `500 kWh`、初始 SOC `50%`、`ηc=0.95`、请求功率 `100 kW`、持续 `3600 s`，且爬坡配置不构成限制。应有 `ΔE=100*0.95*1=95 kWh`，实际功率 `100 kW`，新 SOC 为 `69%`。
2. **SOC 下限饱和样例**：容量 `500 kWh`、初始 SOC `20%`、下限 `10%`、`ηd=0.95`、请求功率 `-250 kW`、持续 `3600 s`，且爬坡配置不构成限制。最多只能减少 `50 kWh`，因此新 SOC 饱和为 `10%`，实际功率应调整为 `-47.5 kW`，而不是保留请求值 `-250 kW`。

### Task 2 实现与验收证据

- 实现文件：`app/domain/storage_simulation.py`；纯领域兼容性修复：`app/domain/__init__.py`；测试文件：`tests/test_storage_simulation_domain.py`。
- 按 TDD 完成 RED-GREEN 循环：先由缺失模块、环境温度与边界换向行为、额定功率硬限与无数据库配置隔离导入测试形成有效 RED，再以最小实现恢复 GREEN。
- 最终核心测试：`tests/test_storage_simulation_domain.py` 为 `77 passed`。
- 协调者相关回归复验：相关领域、设备域和公开导出兼容测试合计 `136 passed`。
- 三个变更文件 Ruff 检查通过；移除子进程 `DATABASE_URL` 后，`from app.domain.storage_simulation import StorageAssetConfig` 导入通过。
- Task 2 规格审查与质量审查均通过，正式完成；该结论不解除持久化准入门禁。

## Task 3 实现与验收证据

- 实现提交：`aa97e3ad`。
- 新增 `StorageAssetProfile`、`StorageDispatchPlan`，并为基础 `storage_telemetry` 增加八个批准扩展；未重建根基线已有表。
- TDD RED 已分别由缺失 migration 文件和缺失模型导入触发，随后 focused contract tests 恢复 GREEN。
- offline SQL 可完整生成；fresh、offline、roundtrip 三条真实 TimescaleDB 2.17.2 路径各得到 682 个 schema objects，规范化指纹共同为 `b81c0db6aaef07fad85a7b617b005e99e1aaafee382e06da6f378eea6d4cbaec`。
- 三条路径均位于 `20260716_0002`，均保留 `public.energydata` hypertable，并包含两张新增表和八个批准扩展列。
- 全量后端验证为 `740 passed, 5 warnings`；Task 3 变更文件 Ruff 检查通过。警告均为既有默认密钥及本地 LibreSSL 环境提示。

## 实施顺序与角色

1. Task 1，规则角色：完成主题迁移、固定契约和持久化门禁记录；规格审查与质量审查均通过，正式完成。
2. Task 2，后端角色：纯领域模型、兼容惰性导出及其测试已完成，规格审查与质量审查均通过。
3. Task 3，后端储能角色：持久化模型与 migration 已完成并通过验收。
4. Task 4，后端储能角色：接入扩展仿真遥测，并明确 MQTT 状态字段到持久化状态列的映射。
5. 后续控制闭环、规则 EMS、日前优化与收益对比任务按依赖顺序实施。
6. 每个阶段结束后由验收角色核对固定契约、测试证据、非目标和剩余风险。

## 验收阶段

- A：仿真遥测
- B：控制与规则闭环
- C：日前优化与收益证据

### 阶段 A 验收

- 系统级仿真在确定输入下可重复运行，功率与 SOC 状态演化满足固定符号约定和边界约束。
- MQTT 遥测能够被既有接入链消费，且每条仿真数据均带有 `data_source=simulated`。
- 储能设备身份严格使用固定 `device_category` 和 `device_subtype`。
- 若涉及持久化，必须继续保持 migration contract、offline SQL 和 PostgreSQL 路径验证为绿色。

### 阶段 B 验收

- 控制命令、设备执行与回执状态可追踪，不能以入队状态替代执行成功。
- 规则 EMS 在可重复场景中形成遥测、决策、命令、回执的闭环证据。
- 越界 SOC、无效功率、过期命令和执行失败具有明确拒绝或失败语义。

### 阶段 C 验收

- 日前优化输入、约束、目标函数和输出时序可复核。
- 至少与不配置储能或等价基准策略比较，并固定电价、负荷、光伏和设备参数口径。
- 收益结论同时给出成本构成、时间范围、基准差值和可重复生成证据。

## 风险

- Task 3 若重复创建基线已有的 `storage_telemetry`，会造成 migration 冲突；实现必须只添加 profile、dispatch 和批准的 telemetry 扩展。
- 新 migration 必须固定接在 `20260716_0001` 后，并继续保持 offline-safe，不能重新引入动态 metadata 或在线检查。
- Task 3 验收使用固定临时数据库；实际开发库 `campus_energy` 仍在 `20260716_0001`。启动依赖新表或新列的运行链路前，必须显式升级到 `20260716_0002` 并复核表、列和 hypertable，不得把临时路径通过等同于开发库已升级。
- 功率符号、SOC 时序边界或控制回执状态若在不同层重复定义，可能造成仿真、接口与展示语义漂移。
- 收益结果对电价、效率、容量、退化成本和基准策略敏感，必须保留完整假设，避免只展示有利结果。

## 当前状态

- Task 1：规格审查与质量审查均通过，正式完成。
- Task 2：规格审查与质量审查均通过，正式完成。
- Task 3：持久化模型、静态 migration 与真实三路径验收通过，正式完成。
- Task 4：已解除依赖，尚未开始。
- 验收阶段 A、B、C：尚未开始。
- 下一角色：后端储能角色，按 TDD 执行 Task 4。
