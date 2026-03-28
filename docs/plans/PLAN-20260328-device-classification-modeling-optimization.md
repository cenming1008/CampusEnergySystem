# PLAN-20260328-device-classification-modeling-optimization

> 状态：进行中 | 负责人：待定 | 更新时间：2026-03-28

---

## 1. 背景与问题

本计划基于探索线程已落库的 [PLAN-20260328-device-classification-modeling-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-audit.md) 收敛，不重复做一遍探索。

当前 CampusEnergySystem 在“设备分类、计量对象、点位对象、多能源对象分层”这一主题上，已经具备统一设备台账、统一设备类型注册表、统一能耗宽表和统一接入链路，但距离 EMS（MyEMS）式“能源类别 + 仪表对象 + 点位对象 + 业务对象 + 关系表”分层建模仍有明显差距。

探索线程已经确认的主要差距是：

- 当前没有独立能源类别表，主要依赖 `EnergyType` 枚举和静态 options。
- 当前没有独立仪表对象层，表计主要仍通过 `device_type=*_meter` 这类设备类型表达。
- 当前没有独立点位对象层，采集值主要通过 `EnergyData` 宽表字段和 payload 字段承载。
- 当前没有业务对象分表，主设备对象 `Device` 同时承担业务设备、计量设备、能源类型标签和部分计量配置语义。
- 当前没有关系表挂接层，主要仍是 `Device -> EnergyData` 直接关联。

这意味着当前系统在本主题上更接近“基础设备台账级 + 统一接入展示级之间的过渡状态”，而不是专业 EMS 的分层对象建模级。

本轮之所以需要从探索升级为正式计划，是因为当前已经出现三类会直接影响后续扩展的结构性问题：

- `Device` 的职责边界过宽，设备对象、计量对象、能源类别对象混在一起。
- `EnergyData` 统一宽表中的专属字段语义不清，空字段与“该对象无此语义”混淆。
- 前后端仍按“设备类型标签 + 宽表字段”消费对象语义，如果不先做第一批治理，后续无论补 meter、point、报表还是多能源分析，都会继续混层。

当前还存在已被探索线程确认的不一致点，本轮需要显式纳入计划：

- `docs/02-功能使用/统一设备管理指南.md` 写“内置 11 种设备类型”，代码注册表实际为 10 种。
- 用户输入中的 `frontend/src/views/DeviceManagement.vue` 在仓库中不存在，实际文件为 `frontend/src/views/DeviceManager.vue`。
- 当前 `current-status.md`、`handoff.md` 顶部规范块仍主要围绕 2026-03-27 的多能源主题，本轮需要以本 PLAN 为准，定点覆盖设备分类与对象分层建模相关的规范块。

---

## 2. 目标

- 明确本轮是“CampusEnergySystem 设备分类、计量对象、点位对象与多能源分层建模优化”的第一批收敛，不是全体系重建。
- 收敛 `Device`、`energy_type`、`device_category`、`device_type` 的职责边界，明确“设备对象 / 计量对象 / 能源类别对象”的第一批分层规则，并补齐文档与接口语义说明。
- 对当前统一宽表，特别是 `EnergyData` 中的可空专属字段做第一批语义治理，明确哪些字段属于公共层、哪些字段属于专属层、哪些字段本轮只保留兼容不扩张。
- 为后端线程定义最小可执行的“计量对象 / 点位对象”过渡策略，优先形成稳定接口语义和对象分层说明，而不是立即做全量 schema 重构。
- 为前端线程定义最小可执行的联调边界，让 `device.ts`、`energy.ts`、`DeviceManager.vue`、`EnergyManagement.vue` 明确哪些字段语义可继续依赖、哪些字段需要准备兼容新增。
- 让正式 PLAN、`current-status.md`、`handoff.md` 三者对本轮范围、非目标、后端边界、前端边界保持一致。

后端线程本轮的落点：

- 对象边界说明
- 宽表字段语义治理
- 设备 / 能源接口语义收敛
- 最小兼容策略与验证

前端线程本轮的落点：

- API 层联调准备
- 设备语义 / 计量语义 / 字段兼容说明的最小消费
- 页面保持最小适配，不做结构性改版

---

## 3. 非目标

- 不做全量数据库 schema 重构，不在本轮引入完整的 `meter / offline meter / virtual meter / point / relation table` 全套新表体系。
- 不做前端设备管理页、多能源页、驾驶舱页面的大改版，不把本轮扩张成 UI / 交互重构。
- 不展开到告警、预测、控制、调度优化、碳排核算细则、费用结算细则等设备分类建模之外的业务主题。
- 不做 `Device` / `EnergyData` 的推翻式重写。
- 不一次性补齐所有对象关系层和专业 EMS 全量建模能力。
- 不把本轮解释成“专业 EMS 对象建模级已完成”。

---

## 4. 范围

### 4.1 允许修改的目录、模块、接口和页面

- `app/models/`
- `app/domain/`
- `app/core/device_registry.py`
- `app/services/device_service.py`
- `app/services/energy_service.py`
- `app/repositories/device_repository.py`
- `app/repositories/energy_repository.py`
- `app/application/device_reporting.py`
- `app/application/energy_management.py`
- `app/api/endpoints/devices/`
- `app/api/endpoints/energy/`
- `frontend/src/api/device.ts`
- `frontend/src/api/energy.ts`
- `frontend/src/views/DeviceManager.vue`
- `frontend/src/views/EnergyManagement.vue`
- `docs/plans/`
- `docs/05-架构与设计/`

### 4.2 本轮优先收敛的主路径

- `Device`、`device_type`、`device_category`、`energy_type` 的对象边界和派生边界
- `device_registry`、请求 schema、落库模型之间的一致性
- `EnergyData` 宽表专属字段的公共层 / 专属层 / 兼容层划分
- 设备 API / 能源 API 的第一批对象语义说明
- 前端 `device.ts`、`energy.ts`、`DeviceManager.vue`、`EnergyManagement.vue` 的最小消费约束

### 4.3 明确不改动的系统边界

- 告警系统
- 预测系统
- 设备控制链路
- 调度优化
- 碳排核算细则
- 费用结算细则
- 全量 meter / point / relation schema 体系
- 驾驶舱页面大改版

---

## 5. 实施步骤

### 阶段 1：计划收敛与对象边界确认

目标：
- 固定“设备对象 / 计量对象 / 能源类别对象 / 点位对象”第一批边界。
- 明确当前 CampusEnergySystem 与 EMS（MyEMS）式分层建模的差距，并把差距收敛成第一批可执行范围。

实施要点：
- 以后端线程为主，先基于现有 `Device`、`EnergyData`、`device_registry` 和接口模型，明确哪些职责继续保留在当前对象，哪些职责本轮只做语义约束，不做落表。
- 明确“计量对象 / 点位对象”本轮只做到接口语义和文档层收敛，还是需要最小 DTO / schema 支撑；如探索证据不足，则只做语义层收敛。

独立验收：
- 已形成第一批对象分层规则。
- 已明确本轮不进入完整 meter / point / relation schema 重建。

### 阶段 2：后端第一批对象语义与接口收敛

目标：
- 让后端在不推翻底座的前提下，先把对象语义、派生边界和宽表字段语义收紧。

实施要点：
- 收敛 `Device` 与 `device_type / device_category / energy_type` 的职责边界，避免继续把更多 meter 语义硬塞进 `Device`。
- 对 `EnergyData` 中可空专属字段做第一批公共层 / 专属层 / 兼容层语义治理。
- 校正 `device_registry`、请求 schema、payload 规范化、落库模型之间的能力不一致。
- 对设备 API、能耗 API 的对象语义补齐说明字段或兼容字段策略，但不做大规模路径重命名。

独立验收：
- `Device` / `EnergyData` / `device_registry` 的第一批语义约束已落地。
- 接口保持兼容，没有发散成 schema 推翻式改造。

### 阶段 3：前端最小联调适配

目标：
- 让前端可以按新语义理解设备对象和能耗对象，但不扩大为页面重构。

实施要点：
- `frontend/src/api/device.ts`、`frontend/src/api/energy.ts` 优先补齐对象语义、计量语义、兼容字段说明。
- `frontend/src/views/DeviceManager.vue`、`frontend/src/views/EnergyManagement.vue` 只做最小消费适配，不调整整体页面结构。
- 前端优先消费“兼容新增字段”或“语义说明字段”，不要假设后端已经完成完整 meter / point 对象建模。

独立验收：
- 前端已完成最小联调准备或最小适配。
- 没有扩大成设备页、多能源页、驾驶舱全面改版。

### 阶段 4：验证与文档回写

目标：
- 让后端边界、前端边界、剩余风险和兼容策略在文档中闭环。

实施要点：
- 后端线程完成后补充测试或静态核对结果。
- 前端线程完成后回写联调依赖字段和剩余风险。
- 规范线程同步更新 `current-status.md`、`handoff.md`、本 PLAN 的进度记录。

独立验收：
- PLAN、`current-status.md`、`handoff.md` 三者内容一致。
- 已显式记录未纳入本轮的事项与剩余风险。

### 阶段 5：收尾与剩余风险确认

目标：
- 在不扩大范围的前提下确认哪些差距继续保留到下一轮。

实施要点：
- 确认“计量对象 / 点位对象”如果本轮只完成接口语义和文档层收敛，则必须明确禁止后续线程半途扩成全量 schema 重建。
- 确认文档与代码不一致项是否已修正，若未修正则显式记录。

独立验收：
- 已明确本轮完成边界。
- 已明确下一轮才处理的对象关系层和 schema 层事项。

---

## 6. 风险与回滚

### 风险 1：对象边界治理半途扩成 schema 重建

- 表现：后端在收敛 `Device` 和 `EnergyData` 语义时，半途扩成 `meter / point / relation` 全量新表设计与迁移。
- 应对：本轮只允许先做对象语义、接口语义和兼容字段策略，不做全量数据库落地。
- 回滚边界：若已开始牵动数据库结构迁移，立即收缩回“文档约束 + 接口语义 + 兼容字段”层。

### 风险 2：前后端对对象语义理解不一致

- 表现：后端认为某字段已转为计量语义，前端仍按设备台账字段理解，导致联调偏差。
- 应对：优先通过兼容新增字段和 `handoff.md` 说明保持双边语义一致。
- 回滚边界：若页面已受影响，优先恢复旧字段语义兼容，再逐步引入新语义。

### 风险 3：宽表语义治理引发接口兼容破坏

- 表现：对 `EnergyData` 专属字段做治理时，直接删除、改名或改变字段返回含义，影响现有页面和报表。
- 应对：本轮只允许“语义说明 + 兼容新增 + 禁止扩张”，不做激进删改。
- 回滚边界：如出现字段兼容问题，优先恢复原返回，并把新语义通过附加字段或文档说明暴露。

### 风险 4：探索结论与现有协作文档不一致

- 表现：`current-status.md`、`handoff.md` 仍保留上一主题的规范块，后续线程按旧块执行。
- 应对：本轮已以本 PLAN 为准，定点覆盖规范负责的内容块。
- 回滚边界：若仍发现冲突，优先缩小更新面，只保留和本主题直接相关的规范块。

总回滚原则：

- 若第一批优化未完成，优先保持兼容，不继续扩张范围。
- 若“计量对象 / 点位对象”本轮只完成接口语义和文档层收敛，则禁止后端线程半途扩成全量 schema 重建。
- 回滚以“对象边界 / 宽表语义 / 接口语义 / 前端最小适配”分阶段收缩，不做全局推翻。

---

## 7. 验收标准

- [ ] 设备对象、计量对象、能源类别对象的第一批边界已在正式 PLAN、状态面板和 handoff 中一致定义。
- [ ] 已明确记录当前 CampusEnergySystem 与 EMS（MyEMS）在“能源类别 / 仪表对象 / 点位对象 / 业务对象 / 关系表”上的主要差距。
- [ ] 后端线程实施范围未扩张到非目标模块。
- [ ] 前端线程已完成最小联调准备或最小适配。
- [ ] `Device` / `EnergyData` / 相关接口的第一批语义说明已补齐，并通过测试或静态核对。
- [ ] 已明确哪些字段属于公共层、哪些字段属于专属层、哪些字段本轮只保留兼容不扩张。
- [ ] `current-status.md`、`handoff.md`、正式 PLAN 三者内容一致。
- [ ] 已明确记录剩余风险与未纳入本轮的事项。

---

## 8. 进度记录

- 2026-03-28：规范线程基于 [PLAN-20260328-device-classification-modeling-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-audit.md) 收敛正式实施计划，状态由 `未开始` 修正为 `进行中`。
- 2026-03-28：规范已收敛，范围锁定为“设备对象 / 计量对象 / 点位对象 / 能源类别对象”的第一批边界治理，不进入完整 `meter / point / relation` schema 重建。
- 2026-03-28：后端第一批已实施，已完成 `Device`、`EnergyData`、`device_registry`、设备 / 能源接口的第一批语义收敛，并保持接口兼容。
- 2026-03-28：前端已完成依赖审计与最小适配，范围控制在 `device.ts`、`energy.ts`、`DeviceManager.vue`、`EnergyManagement.vue`。
- 2026-03-28：验收已执行，但暂不正式收口；原因是前端对后端新增对象语义兼容字段的真实联调确认仍未完成，正式 PLAN 与实际实现已对齐，但收口条件尚未全部满足。

---

## 相关文档

- [PLAN-20260328-device-classification-modeling-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-audit.md)
- [current-status.md](/Users/todo/MineEnergySystem/docs/plans/current-status.md)
- [handoff.md](/Users/todo/MineEnergySystem/docs/plans/handoff.md)
- [docs/05-架构与设计/系统总体架构说明.md](/Users/todo/MineEnergySystem/docs/05-架构与设计/系统总体架构说明.md)
