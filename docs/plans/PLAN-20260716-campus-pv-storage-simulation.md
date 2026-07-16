# PLAN-20260716 园区光储协同仿真与 EMS 控制

## 目标

- 完成系统级储能仿真、MQTT 遥测、控制回执、规则 EMS、日前优化和收益对比。

## 前置门禁

### 主题切换门禁

- 条件：后端可靠性阶段 2A 已通过，或已由规则角色明确暂停并归档。
- 当前判定：**已满足**。用户已批准暂停阶段 2A，规则角色已在 `docs/plans/daily/2026-07/` 保存主题切换时的待恢复快照。
- 作用范围：Task 2 纯领域模型只依赖本门禁，不依赖持久化准入门禁。

### 持久化准入门禁

- 条件：offline SQL、fresh PostgreSQL、migration-built existing 和 runtime-sync existing 四条 migration 路径均通过。
- 当前判定：**未满足**。offline SQL 实测失败，fresh 和两类 existing database 路径缺少 fixture 与通过证据。
- 作用范围：Task 3 以及所有依赖数据库模型、migration、fixture 或持久化路径的下游任务同时依赖主题切换门禁和本门禁。

2026-07-16 实测证据（从仓库根目录运行，先激活项目虚拟环境）：

- `python -m pytest tests/test_backend_tooling_contracts.py`：`13 passed`。
- 未设置 `DATABASE_URL` 时，`python -m alembic upgrade head --sql` 在加载 `Settings` 时失败，错误为 `database_url field required`。
- 使用脱敏示例 `DATABASE_URL='postgresql+psycopg2://USER:PASSWORD@HOST:5432/DB_NAME' python -m alembic upgrade head --sql` 后，执行到 revision `20260412_0003` 的 `_has_column()`，在 `result.fetchone()` 处失败：`AttributeError: 'NoneType' object has no attribute 'fetchone'`。该 URL 仅表达命令格式，不是可用凭据。
- 仓库现状未提供 fresh、migration-built existing、runtime-sync existing 三类 PostgreSQL migration fixture，无法给出三条路径的通过证据。

门禁裁决：

- Task 2 的纯领域模型因主题切换门禁已满足而具备准入条件，但不得触碰数据库模型、migration 或持久化实现。
- Task 3 及所有依赖数据库模型、migration、fixture 或持久化路径的后续任务因持久化准入门禁未满足而保持阻塞。
- 解除阻塞前必须恢复后端可靠性阶段 2A，取得 offline SQL、fresh PostgreSQL、migration-built existing 和 runtime-sync existing 四条路径的完整通过证据。

## 非目标

- 不实现电化学、PCS 底层控制、配电网潮流或真实厂商协议。
- 本计划不修复后端可靠性阶段 2A，不修改现有数据库模型或 Alembic migration。
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

## 实施顺序与角色

1. Task 1，规则角色：完成主题迁移、固定契约和持久化门禁记录；规格审查与质量审查均通过，正式完成。
2. Task 2，后端角色：仅实现不依赖 ORM、数据库或 migration 的纯领域模型及其测试。
3. Task 3，后端角色：持久化模型与迁移；当前阻塞，必须等待阶段 2A 门禁恢复并通过。
4. 后续遥测、控制闭环、规则 EMS、日前优化与收益对比任务按依赖顺序实施；凡依赖持久化者均继承 Task 3 阻塞。
5. 每个阶段结束后由验收角色核对固定契约、测试证据、非目标和剩余风险。

## 验收阶段

- A：仿真遥测
- B：控制与规则闭环
- C：日前优化与收益证据

### 阶段 A 验收

- 系统级仿真在确定输入下可重复运行，功率与 SOC 状态演化满足固定符号约定和边界约束。
- MQTT 遥测能够被既有接入链消费，且每条仿真数据均带有 `data_source=simulated`。
- 储能设备身份严格使用固定 `device_category` 和 `device_subtype`。
- 若涉及持久化，必须先补齐并通过全部迁移门禁证据。

### 阶段 B 验收

- 控制命令、设备执行与回执状态可追踪，不能以入队状态替代执行成功。
- 规则 EMS 在可重复场景中形成遥测、决策、命令、回执的闭环证据。
- 越界 SOC、无效功率、过期命令和执行失败具有明确拒绝或失败语义。

### 阶段 C 验收

- 日前优化输入、约束、目标函数和输出时序可复核。
- 至少与不配置储能或等价基准策略比较，并固定电价、负荷、光伏和设备参数口径。
- 收益结论同时给出成本构成、时间范围、基准差值和可重复生成证据。

## 风险

- 当前 Alembic 链 offline SQL 失败，且三类 PostgreSQL fixture 缺失；任何提前落库都可能扩大不可复现 schema。
- 仓库已有 `storage_telemetry` 运行时 metadata 痕迹，但盘点确认其没有正式 migration 承载，不能据此声明持久化已就绪。
- 功率符号、SOC 时序边界或控制回执状态若在不同层重复定义，可能造成仿真、接口与展示语义漂移。
- 收益结果对电价、效率、容量、退化成本和基准策略敏感，必须保留完整假设，避免只展示有利结果。

## 当前状态

- Task 1：规格审查与质量审查均通过，正式完成。
- Task 2：主题切换门禁已满足；其纯领域实现具备准入条件。
- Task 3 及依赖持久化任务：阻塞。
- 验收阶段 A、B、C：尚未开始。
