# PLAN-20260327-application-layer-convergence

> 状态：未开始 | 负责人：待定 | 更新时间：2026-03-27

---

## 1. 背景与问题

当前项目已经存在 `app/application/`，但在 `devices/data`、`analysis`、`reports` 三条主路径上，主业务路径并未真正统一走 application use case。

基于探索线程已给出的函数级证据，当前问题集中体现在以下三个方面：

### 1.1 endpoint 过重

- [app/api/endpoints/devices/data.py](/Users/todo/MineEnergySystem/app/api/endpoints/devices/data.py) `report_device_data`
  - 当前同时承担 HTTP 适配、`ensure_device_access(...)`、调用 use case、`audit_log(...)`、异常转换。
  - 典型问题：权限前置和审计仍停留在 endpoint。
- [app/api/endpoints/devices/data.py](/Users/todo/MineEnergySystem/app/api/endpoints/devices/data.py) `get_device_data`
  - 当前在 endpoint 直接做访问控制，再调用 use case。
- [app/api/endpoints/devices/data.py](/Users/todo/MineEnergySystem/app/api/endpoints/devices/data.py) `get_device_statistics`
  - 当前在 endpoint 做访问控制，并承担统计入口的响应包装。
- [app/api/endpoints/analysis.py](/Users/todo/MineEnergySystem/app/api/endpoints/analysis.py) `analyze_device`
  - 当前在 endpoint 做访问控制，application 仅被动接收。
- [app/api/endpoints/reports.py](/Users/todo/MineEnergySystem/app/api/endpoints/reports.py) `export_csv`
  - 当前在 endpoint 按 `report_type` 分发、决定表头、调用不同 use case、写 CSV、返回流响应。
  - 典型问题：主流程分发和导出装配都未收口到 application。

### 1.2 application 过薄

- [app/application/device_reporting.py](/Users/todo/MineEnergySystem/app/application/device_reporting.py) `report_device_data_use_case`
  - 当前只是透传到 `DeviceService.report_device_data(...)`。
- [app/application/device_reporting.py](/Users/todo/MineEnergySystem/app/application/device_reporting.py) `get_device_data_use_case`
  - 当前只是透传到 `DeviceService.get_device_data(...)`。
- [app/application/device_reporting.py](/Users/todo/MineEnergySystem/app/application/device_reporting.py) `get_device_statistics_use_case`
  - 当前只是透传到 `DeviceService.get_device_statistics(...)`。
- [app/application/analysis.py](/Users/todo/MineEnergySystem/app/application/analysis.py) `analyze_device_use_case`
  - 当前只是透传到 `AnalysisService.analyze_device(...)`。
- [app/application/reporting.py](/Users/todo/MineEnergySystem/app/application/reporting.py)
  - 当前边界不一致：部分 use case 只是查询包装，部分又直接承担查询编排，但仍未形成统一的导出用例入口。

### 1.3 service 越界

- [app/services/device_service.py](/Users/todo/MineEnergySystem/app/services/device_service.py) `report_device_data`
  - 当前负责取设备、规范化 payload、再调用 `EnergyService.save_energy_data(...)`，已形成跨 service 编排。
- [app/services/energy_service.py](/Users/todo/MineEnergySystem/app/services/energy_service.py) `save_energy_data`
  - 当前同时负责校验、保存、碳排计算、提交事务、刷新对象和日志记录。
  - 典型问题：service 同时承担事务协调和多步骤副作用。
- [app/services/analysis_service.py](/Users/todo/MineEnergySystem/app/services/analysis_service.py) `analyze_device`
  - 当前直接返回贴近接口层的响应字典。
  - 典型问题：输出 DTO 装配停留在 service，而非 application。

结论不是“没有 application 层”，而是“application 层存在但过薄，主路径没有真正收口”。本轮计划的目标是让这三条主路径形成清晰、稳定、可验证的 `endpoint -> application -> service/repository` 调用链。

---

## 2. 目标

- 只收敛 `devices/data`、`analysis`、`reports` 三条主路径，不扩展到全项目。
- 让目标 endpoint 只保留 HTTP 协议适配、参数解析、Depends 注入、调用 application use case 和返回 HTTP response。
- 让 application 层成为三条主路径的真正用例入口，承担前置校验、跨 service 协调、主流程编排、DTO / 导出装配、必要事务协调和运行态可见性收口。
- 让 service 回收为稳定的领域能力与查询能力提供者，不再承担 endpoint 级协议适配，也不再承担多个 service 之间的总流程编排。
- 保持已有主接口路径兼容，不因为 application 收敛而引入大规模接口重命名或前端改造。

本轮完成后的预期状态：

- `devices/data`：权限前置、审计、主流程编排和响应口径收敛到 application。
- `analysis`：访问校验和结果 DTO 装配收敛到 application。
- `reports`：报表类型分发、导出行 DTO、文件 payload 组装收敛到 application。

---

## 3. 非目标

- 不做全项目 application 化。
- 不做数据库 schema 重构。
- 不做 repository 层整体重写。
- 不做前端页面大改版。
- 不做接口路径大规模重命名。
- 不做权限系统整体重构。
- 不做监控系统整体重构。
- 不顺手统一所有 service 命名。
- 不新增一套复杂抽象框架或 application 基类体系。
- 不处理本轮主路径之外的“顺手优化”。
- 不扩展到 `monitoring`、`telemetry_ingestion`、`forecasting` 等非目标模块。
- 不顺手统一全项目异常体系、日志体系或 repository 风格。

---

## 4. 范围

### 4.1 允许修改的目录和文件

- `app/application/`
- `app/api/endpoints/devices/data.py`
- `app/api/endpoints/analysis.py`
- `app/api/endpoints/reports.py`
- 与上述三条主路径直接相关的 services / schemas / tests
- `docs/plans/current-status.md`
- `docs/plans/handoff.md`

第一批优先关注文件：

- `app/application/device_reporting.py`
- `app/application/analysis.py`
- `app/application/reporting.py`
- `app/services/device_service.py`
- `app/services/energy_service.py`
- `app/services/analysis_service.py`

### 4.2 明确禁止扩张的范围

- `app/api/endpoints/` 其他非目标端点
- `monitoring/`
- `telemetry_ingestion`
- `forecasting`
- 数据库模型与迁移
- 前端页面、路由和状态改造
- 权限系统整体设计
- 监控与审计基础设施整体改造

如实施过程中发现主路径之外的问题，默认记录到计划或 handoff，不在本轮顺手处理。

---

## 5. 实施步骤

### 阶段 1：现状收敛

目标：
- 固定三条主路径的入口、关联 application 文件、关联 service 文件和最小测试范围。
- 在实现前明确 endpoint、application、service 的职责边界，避免边改边扩。

实施要点：
- 以后端线程为主，先为三条路径列出当前调用链和待迁移职责。
- 不在本阶段引入新抽象，只确认“哪些职责必须迁走，哪些能力继续保留”。

独立验收：
- 三条主路径的职责迁移清单已形成，并与本计划保持一致。

### 阶段 2：建立 application use case 边界

目标：
- 让 `device_reporting`、`analysis`、`reporting` 三个 application 模块具备清晰 use case 入口，而不是纯透传。

实施要点：
- `devices/data`：application 接管权限前置、审计、必要埋点、返回 DTO / 响应口径。
- `analysis`：application 接管访问校验、主流程编排、分析结果 DTO 装配。
- `reports`：application 接管 `report_type` 分发、导出头部定义、行 DTO 装配、导出 payload 构造。
- 不把 application 演化为另一个“大而全 service”；application 只编排，不下沉 ORM 细节。

独立验收：
- 三条主路径都存在可识别的 application use case 入口。
- application 不再只是单层透传。

### 阶段 3：endpoint 收敛

目标：
- 让目标 endpoint 只保留 HTTP 协议适配。

实施要点：
- `app/api/endpoints/devices/data.py` 不再直接做权限前置、审计和主流程编排。
- `app/api/endpoints/analysis.py` 不再直接做设备访问前置。
- `app/api/endpoints/reports.py` 不再直接按报表类型分发并装配 CSV 主体。
- endpoint 继续保留：参数解析、Depends 注入、HTTP 异常映射、StreamingResponse / response 返回。

独立验收：
- 目标 endpoint 不再直接编排多个 service。
- 目标 endpoint 不再直接承担主事务流程。

### 阶段 4：service 职责回收

目标：
- 让 `device_service`、`energy_service`、`analysis_service` 回收为稳定领域能力提供者。

实施要点：
- `DeviceService.report_device_data` 收缩为设备相关能力，不再承担跨 service 总调度。
- `EnergyService.save_energy_data` 尽量回收到保存与计算能力，不再独占整条用例事务编排。
- `AnalysisService.analyze_device` 聚焦分析计算，不直接承担接口级响应结构装配。
- 仅在主路径所需范围内做最小回收，不顺手改动其他 service。

独立验收：
- service 中明显的用例级编排职责已回收到 application。
- service 仍保持对现有调用的兼容性或通过最小改动保持稳定。

### 阶段 5：测试与联调说明

目标：
- 为三条主路径补齐最小验证，给前端线程明确联调边界。

实施要点：
- 补充或更新与 `devices/data`、`analysis`、`reports` 直接相关的测试。
- 至少覆盖：主路径可用、旧接口路径兼容、application 收口后的主要返回口径不回归。
- 前端线程只做联调准备和最小适配，不提前做页面重构。
- 若返回字段需要调整，必须在 `handoff.md` 明确写出。

独立验收：
- 对应测试通过。
- handoff 已补充联调接口、兼容要求和剩余风险。

### 阶段 6：文档回写

目标：
- 让范围、决策、风险和剩余问题不只停留在代码里。

实施要点：
- 后端线程实施后更新本计划的“进度记录”。
- 同步更新 `docs/plans/current-status.md` 和 `docs/plans/handoff.md`。
- 若实施范围收缩或局部取消，必须直接回写计划，不只在聊天里说明。

独立验收：
- PLAN、`current-status.md`、`handoff.md` 三者口径一致。

---

## 6. 风险与回滚

### 风险 1：application 改造不完整，形成“双重编排”

- 表现：endpoint 已迁出一部分职责，但 service 仍保留完整旧编排，导致职责重复。
- 应对：每条主路径按阶段单独收敛，先保证单路径闭环，再进入下一条。
- 回滚边界：若某条路径 application 收口未完成，优先保留原有可用链路，不继续扩大到下一模块。

### 风险 2：接口兼容被意外破坏

- 表现：返回结构、异常语义或导出文件格式发生无计划变化，影响前端现有调用。
- 应对：endpoint 路径保持不变，字段变化默认禁止；如确需调整，必须先写入 `handoff.md`。
- 回滚边界：优先回滚 DTO / response 装配改动，保留旧接口语义。

### 风险 3：service 回收过度，牵连非目标模块

- 表现：为了“看起来更统一”，把相关 service 或 repository 做了大面积重构。
- 应对：只处理三条主路径直接命中的函数，不顺手修改无关调用点。
- 回滚边界：若发现改动开始波及非目标模块，立即停止，保留已完成的 application 收口，不再继续下探。

### 风险 4：报表导出路径改造后测试覆盖不足

- 表现：CSV 内容、列顺序、文件名或过滤逻辑出现回归。
- 应对：对 `reports` 路径增加针对报表类型和导出 payload 的最小测试。
- 回滚边界：若 application 导出装配不稳定，优先保留 endpoint 返回兼容，再收缩实现范围。

总回滚原则：

- 若 application 改造不完整，优先保持兼容，不继续扩张范围。
- 回滚以主路径为单位进行，不做全局回滚。
- 回滚时优先恢复可用链路和接口兼容，后续再重新收敛。

---

## 7. 验收标准

- [ ] `devices/data`、`analysis`、`reports` 三条主路径已明确统一走 application use case。
- [ ] 目标 endpoint 不再直接编排多个 service。
- [ ] 目标 endpoint 不再直接承担业务权限前置、审计或主要导出装配。
- [ ] `app/application/device_reporting.py`、`app/application/analysis.py`、`app/application/reporting.py` 中已存在明确 use case，而非单纯透传。
- [ ] 对应 service 职责已明显收缩，不再兼做用例级编排或接口级响应装配。
- [ ] 原有主要接口路径保持兼容，未做大规模路径重命名。
- [ ] 与三条主路径直接相关的测试已补充或更新并通过。
- [ ] `docs/plans/handoff.md` 已补充联调说明、兼容要求和剩余风险。
- [ ] 实施范围未扩散到 `monitoring`、`telemetry_ingestion`、`forecasting`、数据库 schema 或前端大改版。

---

## 8. 进度记录

- 2026-03-27：已完成规范线程计划落地，状态为“未开始”；范围锁定为 `devices/data`、`analysis`、`reports` 三条主路径。
- 2026-03-27：已根据探索线程函数级证据确认主要问题为 endpoint 过重、application 透传、service 越界。
- 2026-03-27：已明确本轮非目标和回滚边界；后续若实施范围变化，必须直接回写本计划。

---

## 相关文档

- [AGENTS.md](/Users/todo/MineEnergySystem/AGENTS.md)
- [docs/guides/backend-guidelines.md](/Users/todo/MineEnergySystem/docs/guides/backend-guidelines.md)
- [docs/guides/变更计划规范.md](/Users/todo/MineEnergySystem/docs/guides/变更计划规范.md)
- [docs/plans/current-status.md](/Users/todo/MineEnergySystem/docs/plans/current-status.md)
- [docs/plans/handoff.md](/Users/todo/MineEnergySystem/docs/plans/handoff.md)
