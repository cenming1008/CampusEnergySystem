# Current Status

## 当前总目标
- 推进 application 层收敛，让主业务路径真正统一走 application use case
- 明确本轮是主路径收敛，不是全系统重构
- 为后端线程和前端线程输出可直接执行、可联调、可回滚的实施计划

---

## 当前阶段
- [x] 分析中
- [x] 探索完成
- [x] 规范已落地
- [x] 后端已实施
- [x] 前端已完成多能源依赖审计与最小适配
- [x] 2026-03-28｜设备分类与对象分层建模优化：验收已执行
- [x] 多能源数据业务逻辑探索完成
- [x] 多能源数据业务优化：规范收敛完成
- [x] 多能源数据业务优化：后端第一批已实施
- [x] 2026-03-28｜设备分类与对象分层建模优化：规范收敛完成
- [x] 2026-03-28｜设备分类与对象分层建模优化：前端依赖审计与最小适配完成

---

## 本次目标
- 只聚焦 `devices/data`、`analysis`、`reports` 三条主路径
- 以 application use case 收口主流程，而不是继续让 endpoint 或 service 承担总编排
- 在保持接口兼容前提下完成最小有效收敛，并同步更新 `current-status.md` / `handoff.md`
- 基于多能源探索结论形成第一批正式实施计划
- 为后端线程和前端线程明确多能源数据业务优化的执行边界与联调边界
- 基于 [PLAN-20260328-device-classification-modeling-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-audit.md) 收敛正式实施计划
- 为后端线程和前端线程明确“设备对象 / 计量对象 / 点位对象 / 能源类别对象”第一批收敛边界

## 发现的问题
- [app/api/endpoints/devices/data.py](/Users/todo/MineEnergySystem/app/api/endpoints/devices/data.py) 中 `report_device_data`、`get_device_data`、`get_device_statistics` 仍在 endpoint 直接承担权限前置、审计或响应包装。
- [app/api/endpoints/analysis.py](/Users/todo/MineEnergySystem/app/api/endpoints/analysis.py) `analyze_device` 仍在 endpoint 做访问控制，application 尚未成为真正入口。
- [app/api/endpoints/reports.py](/Users/todo/MineEnergySystem/app/api/endpoints/reports.py) `export_csv` 仍在 endpoint 直接做报表分发、表头定义和 CSV 装配。
- [app/application/device_reporting.py](/Users/todo/MineEnergySystem/app/application/device_reporting.py) 与 [app/application/analysis.py](/Users/todo/MineEnergySystem/app/application/analysis.py) 仍以透传为主。
- [app/services/device_service.py](/Users/todo/MineEnergySystem/app/services/device_service.py) `report_device_data`、[app/services/energy_service.py](/Users/todo/MineEnergySystem/app/services/energy_service.py) `save_energy_data`、[app/services/analysis_service.py](/Users/todo/MineEnergySystem/app/services/analysis_service.py) `analyze_device` 存在用例级编排或接口级 DTO 装配上浮。

## 最近结论
### 探索线程
- 当前问题不是“没有 application 目录”，而是“application use case 过薄、endpoint 过重、service 职责上浮”。
- 第一批只应收敛三条主路径：`devices/data`、`analysis`、`reports`。

### 规范线程
- 已新增 [PLAN-20260327-application-layer-convergence.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-application-layer-convergence.md)。
- 已将后端实施边界、前端联调边界和回滚原则写回 `current-status.md` / `handoff.md`，后续线程可直接按计划执行。
- 已新增 [PLAN-20260328-device-classification-modeling-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-optimization.md)。
- 当前设备分类与对象分层建模主题，如与 2026-03-27 主题规范块存在不一致，以 2026-03-28 正式 PLAN 为准。

### 前端线程
- 已按 [PLAN-20260328-device-classification-modeling-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-optimization.md) 和 [PLAN-20260328-device-classification-modeling-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-audit.md) 完成前端依赖审计。
- 当前受影响最大的前端消费点不是“接口拿不到数据”，而是仍按旧理解消费 `device_type / device_category / energy_type / unit / total_consumption / current_power` 这些字段。
- 已完成的最小适配只落在允许范围内：
  - `frontend/src/api/device.ts` 补齐后端已存在的 `location_id / updated_at` 类型
  - `frontend/src/views/DeviceManager.vue` 的降级设备类型列表补齐到注册表当前 10 种，避免接口失败时前端继续使用过期分类
- 本轮没有重构设备管理页、多能源页、驾驶舱；`Dashboard.vue`、`CampusScene.vue`、`EnergyManagement.vue` 中的对象语义和口径风险只做记录，不扩张为页面改版。

### 后端线程
- 已按 [PLAN-20260328-device-classification-modeling-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-optimization.md) 完成设备分类、计量对象、点位对象与多能源分层建模的第一批后端收敛：
  - `app/core/device_registry.py` 已成为第一批对象语义兼容层，`DeviceTypeConfig` 现在同时暴露 `object_role`、`metering_role`、`point_kind`、`measurement_subject`、`public_data_fields`、`specialized_fields`、`compatible_aliases` 等元信息，10 种设备类型都已补齐。
  - `app/domain/device_payloads.py` 已补 `describe_device_type_semantics(...)`、`describe_energy_data_fields(...)`，并把 `heat_flow -> flow_rate` 作为统一宽表下的兼容映射收口到 payload 规范化层。
  - `Device` / `EnergyData` 的模型语义说明已回写到 [tables.py](/Users/todo/MineEnergySystem/app/models/tables.py)，明确 `Device` 仍是统一对象，`EnergyData` 仍是宽表，但已区分公共字段、专属字段和兼容层字段。
  - `/devices/types`、`/devices/types/{device_type}`、`/devices/{device_id}/semantic-profile`、`/devices/{device_id}/statistics` 现在会返回第一批对象语义、计量语义和字段层级说明，便于前端联调时区分“设备对象 / 计量对象 / 点位对象 / 能源类别对象”。
  - `/energy/types`、`/energy/overview`、`/energy/statistics` 现在会返回 `supported_device_types`、`data_object_kind`、`point_kind`、`public_fields`、`specialized_fields`、`null_field_rule` 等语义字段，用于说明当前宽表字段边界和对象边界。
  - `/analysis/{device_id}` 在保留旧字段的前提下，新增 `device_type`、`device_category`、`device_object_role`、`metering_role`、`point_kind`、`measurement_subject`、`energy_data_public_fields`、`energy_data_specialized_fields`。
  - `GET /reports/export_csv` 保持原路径不变，但 `energy_detail`、`carbon_emission` 导出已追加设备类型、设备类别、对象语义、点位语义列，作为第一批兼容新增说明列。
- 本轮未做完整 `meter / offline meter / virtual meter / point / relation table` 数据库重建，未改前端页面，未扩张到告警 / 预测 / 控制 / 调度等范围外主题。

### 验收线程
- 已按验收线程要求复核 `docs/guides/*`、`docs/plans/*`、`handoff.md`、本轮 2026-03-28 主题相关后端 / 前端代码与测试证据。
- 验收结论：本轮“设备分类、计量对象、点位对象与多能源分层建模优化”后端第一批实现已落地，但暂不建议正式收口。
- 当前阻塞点有两类：
  - 正式 PLAN 仍停留在“未开始”，`current-status.md` / `handoff.md` / 实际代码状态未完全对齐，属于文档闭环缺口。
  - 前端虽已完成依赖审计与极小适配，但 `frontend/src/api/device.ts`、`frontend/src/api/energy.ts`、`frontend/src/api/telemetry.ts` 仍未承接后端已新增的对象语义字段，联调准备未完全闭环。
- `DeviceManager.vue`、`Dashboard.vue`、`CampusScene.vue`、`EnergyManagement.vue` 仍以旧字段组合猜测对象语义；这部分不是要求本轮做页面重构，但需要前端线程至少补齐 API 类型和联调说明后再收口。

---

## 当前阻塞点
- 探索线程已给出函数级证据，当前无分析阻塞。
- 当前唯一需要控制的是范围：若后端实施时扩散到三条主路径之外，就会偏离本轮目标。

---

## 当前待办

### 规范线程
- [x] 产出正式计划文档
- [x] 回写 `current-status.md` / `handoff.md`
- [x] 将后端 / 前端执行边界写清楚
- [x] 为 `app/application/` 补充详细 README，明确 use case 分工与新增落点规则
- [ ] 等待后端线程按计划实施后回写进度
- [x] 基于多能源探索文档收敛第一批正式实施计划
- [x] 覆盖更新多能源相关的 `handoff.md` / `current-status.md` 规范块
- [x] 已新增 [PLAN-20260328-device-classification-modeling-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-optimization.md)
- [x] 已覆盖更新设备分类与对象分层建模主题对应的规范块
- [x] 当前设备分类与对象分层建模主题以本次 PLAN 为准

### 后端线程
- [x] 只在 `devices/data`、`analysis`、`reports` 三条主路径内实施 application 收敛
- [x] 让 endpoint 只保留 HTTP 适配，application 接管编排，service 回收越界职责
- [x] 补充或更新与三条主路径直接相关的测试
- [x] 实施后回写计划进度、验证结果与剩余风险
- [x] 按多能源正式计划先处理口径、单位、碳排边界和 analysis / reports 第一批收敛
- [x] 保持最小兼容实现，没有扩张为全模型重构、全碳核算重写或全报表重构
- [ ] 下一轮如需继续推进，只在展示级碳排、单位换算落库和更细分能源指标上增量收敛
- [x] 按 [PLAN-20260328-device-classification-modeling-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-optimization.md) 完成 `Device`、`EnergyData`、`device_registry`、设备 / 能源接口的第一批语义收敛
- [x] 通过 registry 元信息、payload 规范化、接口兼容新增字段补齐“设备对象 / 计量对象 / 点位对象 / 能源类别对象”的第一批后端表达
- [x] 保持兼容策略，没有扩张为完整 meter / point / relation schema 重建或全量数据库迁移
- [ ] 下一轮如需继续推进，只在真正需要落库分层的 meter / point schema、前端联调验证后暴露出的消费歧义、以及导出列结构稳定化上增量推进

### 前端线程
- [x] 已完成 `frontend/src/api/device.ts`、`frontend/src/api/energy.ts`、`frontend/src/api/report.ts`、`frontend/src/api/telemetry.ts`、`frontend/src/views/DeviceManager.vue`、`frontend/src/views/EnergyManagement.vue`、`frontend/src/views/Report.vue`、`frontend/src/views/Dashboard.vue`、`frontend/src/views/CampusScene.vue`、`frontend/src/features/dashboard/composables/useDashboardEnergyStats.ts`、`frontend/src/features/dashboard/composables/useDashboardRealtime.ts` 的设备分类与对象语义依赖审计
- [x] 已确认本轮输入中的 `DeviceManagement.vue` 实际文件为 `frontend/src/views/DeviceManager.vue`，审计与改动均以实际文件为准
- [x] 已完成最小适配：
  - `frontend/src/api/device.ts` 承接后端现有 `location_id / updated_at`
  - `frontend/src/views/DeviceManager.vue` 的设备类型降级列表补齐到当前注册表 10 种
- [x] 已保持现有页面结构与交互不变，没有扩张为设备页、多能源页、驾驶舱整体重构
- [ ] 待后端线程补齐“设备分类与对象分层建模第一批后端收敛”专门交接块后，再做真实联调确认
- [ ] 若后端后续只做兼容新增字段，前端优先走 API 类型和最小消费点适配，不扩张为架构治理

### 验收线程
- [x] 已完成探索 / 规范 / 后端 / 前端四类产出统一验收
- [ ] 暂不建议将本轮标记为“正式收口”
- [ ] 建议先回到规范线程补齐 [PLAN-20260328-device-classification-modeling-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-optimization.md) 的状态、进度记录与验收结果
- [ ] 建议再交回前端线程补齐 `device.ts`、`energy.ts`、`telemetry.ts` 对对象语义兼容新增字段的类型承接与联调说明，再由验收线程做最终确认

---

## 修改文件
- app/application/README.md
- frontend/src/api/telemetry.ts
- frontend/src/api/device.ts
- frontend/src/api/energy.ts
- frontend/src/api/report.ts
- frontend/src/views/Report.vue
- frontend/src/views/DeviceManager.vue
- app/application/__init__.py
- app/application/device_reporting.py
- app/application/analysis.py
- app/application/reporting.py
- app/api/endpoints/devices/data.py
- app/api/endpoints/analysis.py
- app/api/endpoints/reports.py
- app/services/analysis_service.py
- app/services/report_service.py
- app/services/__init__.py
- tests/test_application_use_cases.py
- tests/test_reports_integration.py
- tests/test_endpoint_application_convergence.py
- docs/plans/PLAN-20260327-multi-energy-data-optimization.md
- docs/plans/PLAN-20260328-device-classification-modeling-optimization.md
- docs/plans/current-status.md
- docs/plans/handoff.md

### 本轮后端变更（多能源第一批）
- app/domain/energy_rules.py
- app/services/energy_service.py
- app/services/analysis_service.py
- app/application/analysis.py
- app/application/reporting.py
- app/api/endpoints/energy/shared.py
- app/api/endpoints/energy/data.py
- app/api/endpoints/energy/carbon.py
- app/api/endpoints/reports.py
- tests/test_energy_domain.py
- tests/test_application_use_cases.py
- tests/test_reports_integration.py
- tests/test_energy_endpoint_semantics.py
- docs/plans/current-status.md
- docs/plans/handoff.md

### 本轮后端变更（设备分类与对象分层第一批）
- app/core/device_registry.py
- app/domain/device_payloads.py
- app/models/tables.py
- app/services/device_service.py
- app/services/energy_service.py
- app/services/analysis_service.py
- app/repositories/energy_repository.py
- app/services/report_service.py
- app/application/device_reporting.py
- app/application/analysis.py
- app/application/reporting.py
- app/api/endpoints/devices/__init__.py
- app/api/endpoints/devices/management.py
- app/api/endpoints/devices/shared.py
- app/api/endpoints/energy/data.py
- app/api/endpoints/energy/shared.py
- tests/test_device_domain.py
- tests/test_device_endpoint_semantics.py
- tests/test_energy_endpoint_semantics.py
- tests/test_application_use_cases.py
- docs/plans/current-status.md
- docs/plans/handoff.md

### 本轮验收更新
- docs/plans/current-status.md
- docs/plans/handoff.md

---

## 验证结果
- 已阅读规范入口：`docs/guides/README.md`、`docs/guides/文档体系规范.md`、`docs/guides/变更计划规范.md`、`docs/guides/backend-guidelines.md`、`docs/plans/README.md`、`docs/plans/TEMPLATE.md`。
- 已阅读协作文档：`docs/plans/current-status.md`、`docs/plans/handoff.md`。
- 已核对探索线程写回的函数级证据，并复核 `devices/data`、`analysis`、`reports` 当前实现。
- 已为 `app/application/` 新增详细 README，内容基于当前目录、当前导出符号和三条已收敛主路径整理，不额外扩写未实施能力。
- 已执行 `python3 -m compileall -q app tests`，编译通过。
- 已执行 `./venv/bin/python -m unittest tests.test_application_use_cases tests.test_reports_integration tests.test_layer_exports tests.test_endpoint_application_convergence`，21 个测试通过。
- 已执行 `./venv/bin/python -c "import app.main; print('ok')"`，主应用导入通过。
- 目标 endpoint 最小可用性已通过单测验证：
  - `devices/data` endpoint 只委托 application
  - `analysis` endpoint 只委托 application
  - `reports/export_csv` 通过集成测试验证导出行为仍可用
- 已完成多能源第一批后端验证：
  - `python3 -m compileall -q app tests` 通过
  - `./venv/bin/python -m unittest tests.test_energy_domain tests.test_application_use_cases tests.test_reports_integration tests.test_energy_endpoint_semantics`，29 个测试通过
  - `./venv/bin/python -c "import app.main; print('ok')"` 通过
  - `tests.test_energy_endpoint_semantics` 已验证 `/energy/types`、`/energy/overview`、`/energy/carbon/factors` 的新增语义字段和边界字段
  - `tests.test_reports_integration` 已验证新增 `multi_energy_summary` 导出类型仍走原有 CSV 下载路径
- 已完成 2026-03-28 设备分类与对象分层建模主题后端验证：
  - `python3 -m compileall -q app tests` 通过
  - `./venv/bin/python -m unittest tests.test_device_domain tests.test_device_endpoint_semantics tests.test_energy_domain tests.test_application_use_cases tests.test_reports_integration tests.test_energy_endpoint_semantics`，38 个测试通过
  - `./venv/bin/python -c "import app.main; print('ok')"` 通过
  - `tests.test_device_domain` 已验证设备类型语义、宽表字段边界和 `heat_flow -> flow_rate` 兼容映射
  - `tests.test_device_endpoint_semantics` 已验证 `/devices/types` 与 `/devices/{device_id}/semantic-profile` 的第一批对象语义输出
  - `tests.test_energy_endpoint_semantics` 已验证 `/energy/types`、`/energy/overview` 的 `supported_device_types`、`field_boundary_rule`、`device_object_boundary`
  - `tests.test_application_use_cases` 与 `tests.test_reports_integration` 已验证 `analysis` 兼容新增语义字段和 `energy_detail` / `carbon_emission` 导出语义列追加
- 前端已完成三条主路径依赖审计：
  - `devices/data` / `analysis`：`frontend/src/api/telemetry.ts`、`frontend/src/features/dashboard/composables/useDashboardRealtime.ts`、`frontend/src/views/CampusScene.vue`
  - `reports`：`frontend/src/api/report.ts`、`frontend/src/views/Report.vue`
- 已做最小前端适配：
  - `telemetry.ts` 增加 wrapped / unwrapped 返回兼容与数值字段归一化
  - `energy.ts` 补齐多能源新增语义字段、单位字段、碳排边界字段的类型定义
  - `report.ts` / `Report.vue` 增加与后端文件命名规则更接近的导出文件名兜底，并补上 `multi_energy_summary` 最小入口
- 已完成 2026-03-28 设备分类与对象分层建模主题前端审计：
  - `device.ts`：确认前端仍直接依赖 `device_type / device_category / energy_type / unit / rated_capacity / location` 这组薄标签字段
  - `DeviceManager.vue`：确认新增设备时只选择 `device_type`，其余语义全部默认由后端派生；并已把降级设备类型列表补齐到 10 种
  - `EnergyManagement.vue`：确认页面仍按 `energy_type + unit + total_consumption` 消费对象语义，没有独立计量对象 / 点位对象语义层
  - `Dashboard.vue` / `CampusScene.vue` / `useDashboardRealtime.ts`：确认仍通过 `device_type / energy_type / current_power / rated_capacity / location` 组合猜测设备和计量语义
  - `Report.vue` / `report.ts`：当前报表下载链路对本主题无额外 breaking change，但仍依赖 blob 下载行为稳定
- 已做 2026-03-28 主题最小前端适配：
  - `frontend/src/api/device.ts` 补齐 `location_id / updated_at`
  - `frontend/src/views/DeviceManager.vue` 将降级设备类型列表扩展为与当前注册表一致的 10 种
- 已执行 `cd frontend && npm run build`，构建通过

---

## 剩余风险
- 若后端线程把本轮任务理解成“全项目分层重构”，范围会失控。
- 若前端线程提前按猜测调整字段或页面，会放大联调成本。
- 若实施后不回写计划和 handoff，后续线程容易再次回到各自理解的状态。
- 本轮把统计和碳排汇总改成“累计量取时段差值”的口径后，`/energy/statistics`、`/energy/overview`、`/energy/carbon/summary` 的数值会比旧实现更小但更合理；若前端或演示脚本之前默认使用“累计量直接求和”心智，需要按新口径联调。
- `CarbonEmission` 明细表仍保留历史“按单条输入直接乘因子”的存量数据，本轮只把汇总与展示边界收敛为展示级估算，没有做历史数据回填和核算级重算。
- 单位体系本轮只完成“内部标准单位与展示单位说明”收敛，尚未做接入侧异构单位自动换算；如果现场设备上报 `MJ`、`RT`、`Nm³` 等非当前标准单位，仍需后续补归一化。
- `DeviceService.report_device_data` 这一旧 helper 仍保留在 service 中作为兼容能力，但主路径已不再通过它编排；若后续要继续收敛，可在下一轮逐步降级其直接使用面。
- `reports` 主路径已收口到 application，但报表行查询仍分散在 `ReportService` 与 `EnergyRepository` 两层，属于当前计划允许的最小兼容方案，不在本轮继续下探 repository 重构。
- `Device` 仍是统一对象，当前只是通过 `device_registry` 与接口元信息补了“设备对象 / 计量对象 / 点位对象”第一批兼容表达，尚未落成独立 meter / point / relation schema。
- `EnergyData` 仍是统一宽表；`public_fields` / `specialized_fields` / `null_field_rule` 已说明第一批边界，但还没有彻底拆出专属采集模型。
- `reports/export_csv` 的 `energy_detail`、`carbon_emission` 本轮新增了语义说明列；下载协议未变，但若前端或外部脚本依赖固定列顺序，需要按新列头联调确认。
- `GET /analysis/{device_id}`、`GET /devices/{device_id}/statistics`、`GET /energy/overview`、`GET /energy/statistics` 本轮以兼容新增方式补了对象语义字段；旧字段仍保留，但前端不应再把 `device_type / unit / 宽表字段有无` 当成完整对象模型。
- 设备类型数量当前以后端注册表实际 10 种为准；若其他文档仍写 11 种，需要后续由规范线程继续清理历史描述。
- 前端当前没有直接调用 `POST /devices/{device_id}/data` 或 `GET /devices/{device_id}/statistics`；真正受影响的是把 `GET /devices/{device_id}/data` 当历史趋势源的页面，以及直接消费 `/analysis/{device_id}` 原始字段的页面。
- `Dashboard.vue` 与 `CampusScene.vue` 仍在前端自行拼区域排行、在线状态和总负荷口径；这类页面如果后续要切到稳定驾驶舱口径，仍需后端补 application 层统一聚合接口。
- `Report.vue` 仍依赖浏览器按 blob 下载成功来判断导出成功，且当前 axios 拦截器不暴露 `Content-Disposition`；若后端后续调整下载头或流式错误语义，需要再做一轮前端联调确认。
- 多能源前端当前最显著的业务风险不是“字段拿不到”，而是“旧页面仍可能按旧语义理解新字段”：
  - `useDashboardEnergyStats.ts` / `Dashboard.vue` 仍把不同能源的 `total_consumption` 直接合并成“今日总能耗 / 本月总能耗”，存在跨单位混算风险。
  - `EnergyManagement.vue` 仍把 `overview.statistics[*].total_consumption` 直接用于跨能源对比和总览展示，对 `cross_energy_mix_allowed`、`consumption_unit`、`consumption_stat_basis` 还没有展示级约束。
  - `EnergyManagement.vue` 的碳排展示和碳排计算器仍以“可展示结果”为主，尚未根据 `is_accounting_grade`、`boundary`、`note` 做更明确的核算边界提示。
- 本轮前端只完成了静态依赖审计和最小兼容接入；后端若在真实联调中继续调整 `total_consumption` 语义、单位字段或 `multi_energy_summary` 列结构，仍需再做一次前端定向确认。
- 设备分类与对象分层建模主题下，前端当前仍存在以下静默风险：
  - `DeviceManager.vue` 仍把 `device_type` 当作设备对象、计量对象和能源类别对象的主要入口字段，页面本身没有额外对象层区分。
  - `Dashboard.vue` 与 `CampusScene.vue` 仍通过 `device_type / energy_type / rated_capacity / current_power` 组合来猜设备语义和运行语义。
  - `EnergyManagement.vue` 仍把 `EnergyData` 宽表字段直接当成稳定测点语义消费，无法区分“字段暂无值”和“该对象本无此语义字段”。
  - `frontend/src/api/device.ts` 现在虽已补上 `location_id`，但前端页面仍只消费 `location` 字符串，没有进入位置对象语义层。
- 当前 `handoff.md` 中仍缺少“后端 -> 前端｜设备分类与对象分层建模第一批后端收敛”专门块；前端本轮只能基于现有 PLAN、探索审计和实际代码做静态审计，真实联调前仍需后端补齐该块。
- 验收视角补充：
  - 后端代码、`handoff.md` 与 `current-status.md` 对“设备对象 / 计量对象 / 点位对象第一批兼容语义已补到 registry、接口和导出层”的描述基本一致。
  - 但正式 PLAN 仍停留在“未开始”，且前端 API 类型层未承接后端新增的 `object_role / metering_role / point_kind / supported_device_types / energy_data_public_fields` 等语义字段，说明当前不只是文档慢一步，还存在前端联调准备缺口。
  - 因此，本轮状态更准确地说是“后端主功能已完成，但规范进度回写和前端联调准备未完全闭环，暂不建议正式收口”。

---

## 2026-03-28 验收线程

### 本次目标
- 对“CampusEnergySystem 设备分类、计量对象、点位对象与多能源分层建模优化”相关的探索、规范、后端、前端四类产出做统一验收。
- 判断本轮是否满足第一批对象分层建模优化的收口条件，并把验收结论写回协作文档。

### 发现的问题
- [PLAN-20260328-device-classification-modeling-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-optimization.md) 顶部状态仍为“未开始”，进度记录也只保留规范线程建计划时的信息，未反映后端已实施、前端已完成审计、验收已执行的实际状态。
- [frontend/src/api/device.ts](/Users/todo/MineEnergySystem/frontend/src/api/device.ts) 的 `DeviceTypeConfig` 仍未声明后端已返回的 `object_role`、`metering_role`、`point_kind`、`measurement_subject`、`public_data_fields`、`specialized_fields`、`compatible_aliases` 等字段。
- [frontend/src/api/energy.ts](/Users/todo/MineEnergySystem/frontend/src/api/energy.ts) 仍未承接 `supported_device_types`、`data_object_kind`、`point_kind`、`public_fields`、`specialized_fields`、`field_boundary_rule`、`energy_profiles` 等本轮后端兼容新增字段。
- [frontend/src/api/telemetry.ts](/Users/todo/MineEnergySystem/frontend/src/api/telemetry.ts) 仍未声明后端 `GET /analysis/{device_id}` 已新增的 `device_type`、`device_category`、`device_object_role`、`metering_role`、`point_kind`、`measurement_subject`、`energy_data_public_fields`、`energy_data_specialized_fields`。
- [current-status.md](/Users/todo/MineEnergySystem/docs/plans/current-status.md) 先前“待后端线程补齐专门交接块后再做真实联调确认”的说法已过期，因为 [handoff.md](/Users/todo/MineEnergySystem/docs/plans/handoff.md) 已存在对应的 `后端 -> 前端` 交接块。

### 验收结论
- 探索线程结论、正式 PLAN、后端第一批实现、测试验证、`handoff.md` 中的后端 / 前端交接已能互相对应，说明后端主功能基本闭环。
- 但当前仍有两类收口阻塞：
  - 正式 PLAN 进度未回写，文档闭环不完整。
  - 前端联调准备只完成了审计和极小修补，尚未把后端新增对象语义字段承接到 API 类型层。
- 验收判断：本轮属于“后端主功能已完成，但规范进度回写和前端联调准备未完全闭环”，暂不正式收口。

### 修改文件
- docs/plans/current-status.md
- docs/plans/handoff.md

### 验证结果
- 已按要求阅读 `docs/guides/README.md`、`docs/guides/文档体系规范.md`、`docs/guides/变更计划规范.md`、`docs/plans/README.md`、`docs/plans/current-status.md`、`docs/plans/handoff.md`、[PLAN-20260328-device-classification-modeling-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-audit.md)、[PLAN-20260328-device-classification-modeling-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-optimization.md)。
- 已复核后端关键实现：`app/models/tables.py`、`app/domain/device_payloads.py`、`app/core/device_registry.py`、`app/services/device_service.py`、`app/services/energy_service.py`、`app/services/analysis_service.py`、`app/application/device_reporting.py`、`app/application/analysis.py`、`app/application/reporting.py`、`app/api/endpoints/devices/management.py`、`app/api/endpoints/devices/data.py`、`app/api/endpoints/energy/data.py`、`app/api/endpoints/reports.py`。
- 已复核前端实际文件与最小适配：`frontend/src/api/device.ts`、`frontend/src/api/energy.ts`、`frontend/src/api/report.ts`、`frontend/src/api/telemetry.ts`、`frontend/src/views/DeviceManager.vue`、`frontend/src/views/EnergyManagement.vue`、`frontend/src/views/Dashboard.vue`、`frontend/src/views/CampusScene.vue`、`frontend/src/views/Report.vue`、`frontend/src/features/dashboard/composables/useDashboardEnergyStats.ts`、`frontend/src/features/dashboard/composables/useDashboardRealtime.ts`。
- 已执行 `python3 -m compileall -q app tests`，通过。
- 已执行 `./venv/bin/python -m unittest tests.test_device_domain tests.test_device_endpoint_semantics tests.test_energy_domain tests.test_application_use_cases tests.test_reports_integration tests.test_energy_endpoint_semantics`，38 个测试通过。
- 已执行 `cd frontend && npm run build`，通过。

### 剩余风险
- 当前未闭环的第一问题是正式 PLAN 进度和状态未同步更新，这会让后续线程无法直接判断本轮是否已完成。
- 当前未闭环的第二问题是前端 API 类型层尚未承接对象语义兼容新增字段；这不会阻塞现有页面运行，但会阻塞“前端已完成联调准备”的验收判断。
- `Dashboard.vue`、`CampusScene.vue`、`EnergyManagement.vue` 仍按旧字段组合猜测对象语义，这属于已识别存量风险；验收线程不直接改页面，因为本轮 PLAN 明确禁止页面大改版。
- 若下一步继续推进，应先由规范线程补齐计划进度，再由前端线程补齐最小 API 类型与联调说明；后端当前不需要继续扩大实现范围。

### 需要交接给谁
- 先交回规范线程：补齐正式 PLAN 的状态、进度记录和验收结果，使计划文档与 `current-status.md` / `handoff.md` / 实际实现一致。
- 再交回前端线程：补齐 `device.ts`、`energy.ts`、`telemetry.ts` 对兼容新增对象语义字段的类型承接，并把“为何页面层本轮不改”写得更明确。
- 当前不建议交回后端线程继续追加主功能。

---

## 2026-03-27 多能源数据业务逻辑探索

### 本次目标
- 审计 `电 / 热 / 气 / 冷 / 碳排放` 五类对象的数据业务逻辑。
- 判断当前实现是否存在业务语义过弱、统计口径不严、单位体系不清、碳排逻辑过粗的问题。
- 为规范线程输出可直接继续收敛 PLAN 的输入，而不是只留聊天结论。

### 发现的问题
- 当前多能源建模主要依赖 `energy_type`、`device_type`、`device_category` 区分，核心时序仍围绕 `consumption` 和 `flow_rate` 两个通用字段运转，能源专属业务语义不足。
- `EnergyData` 模型将 `consumption` 定义为累计量、`flow_rate` 定义为瞬时量，但统计层对 `consumption` 大量直接求和和求平均，累计量 / 瞬时量口径存在混用风险。
- 单位体系目前只有静态映射，尚未形成“内部标准单位 + 入库换算 + 展示单位”的完整规则，冷 / 热 / 气存在单位和量纲混用风险。
- 碳排逻辑当前本质上仍是“固定因子 * consumption”，更适合驾驶舱展示，不适合作为正式核算结论。
- `analysis` 与 `reports` 目前主要是通用分类汇总，对热 / 气 / 冷 / 电没有形成各自业务指标体系，系统整体更接近“基础 EMS 底座”而非强语义多能源业务系统。

### 最近结论
#### 探索线程
- 已新增 [PLAN-20260327-multi-energy-data-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-multi-energy-data-audit.md)。
- 当前系统在多能源层面更接近“基础 EMS 平台底座”：
  - 已具备统一接入、统一存储、统一展示
  - 但尚未具备足够强的电 / 热 / 气 / 冷 / 碳业务语义
- 第一批最值得优化的优先级不是前端改版，而是：
  - 数据口径层
  - 单位与标准化层
  - 碳排核算层
  - 多能源语义层
  - 指标与分析层

### 当前待办补充
#### 规范线程
- [x] 基于 [PLAN-20260327-multi-energy-data-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-multi-energy-data-audit.md) 收敛正式实施计划
- [x] 已新增 [PLAN-20260327-multi-energy-data-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-multi-energy-data-optimization.md)
- [x] 已将后端执行边界和前端联调边界回写到 `handoff.md`

#### 后端线程
- [x] 按 [PLAN-20260327-multi-energy-data-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-multi-energy-data-optimization.md) 执行第一批最小后端收敛
- [x] 保持在口径、单位、碳排边界和 `analysis` / `reports` 第一批收敛范围内，没有扩张为全模型重构、全碳核算重写或全报表系统重构
- [ ] 后续若继续推进，优先处理接入换算、历史碳排重算策略和更细粒度分能源指标，而不是扩大接口重命名范围

#### 前端线程
- [x] 已完成多能源页面、驾驶舱和报表页的前端依赖审计，并识别出跨能源混算、累计量/瞬时量混用和碳排边界表达三类高风险点
- [x] 已按最小代价补齐 API 层兼容字段和 `multi_energy_summary` 导出入口，未扩大为页面重构
- [ ] 待后端真实联调后，再决定是否需要对驾驶舱总能耗卡片、多能源对比图和碳排说明做展示级微调

## 2026-03-28 设备分类与对象分层建模｜前端线程

### 本次目标
- 围绕“设备分类、计量对象、点位对象与多能源分层建模第一批后端收敛”做前端依赖审计、最小适配和交接说明。
- 只处理 `frontend/src/api/device.ts`、`frontend/src/api/energy.ts`、`frontend/src/api/report.ts`、`frontend/src/api/telemetry.ts`、`frontend/src/views/DeviceManager.vue`、`frontend/src/views/EnergyManagement.vue`、`frontend/src/views/Report.vue`、`frontend/src/views/Dashboard.vue`、`frontend/src/views/CampusScene.vue`、`frontend/src/features/dashboard/composables/useDashboardEnergyStats.ts`、`frontend/src/features/dashboard/composables/useDashboardRealtime.ts`。

### 发现的问题
- `DeviceManager.vue` 新建设备时只选择 `device_type`，对 `device_category / energy_type / unit / rated_capacity` 全部默认信任后端派生，说明页面仍按“统一 Device + 类型标签”理解对象语义。
- `frontend/src/api/device.ts` 先前未声明后端已有的 `location_id`，前端仍只以 `location` 字符串消费位置信息。
- `EnergyManagement.vue`、`Dashboard.vue`、`CampusScene.vue` 仍通过 `device_type / energy_type / unit / total_consumption / current_power` 组合推断对象语义，尚未进入独立计量对象 / 点位对象消费模式。
- `DeviceManager.vue` 的降级设备类型列表此前只有 4 种，与当前注册表 10 种设备类型不一致；一旦 `/devices/types` 获取失败，前端会退回过期分类集合。

### 修改文件
- frontend/src/api/device.ts
- frontend/src/views/DeviceManager.vue
- docs/plans/current-status.md
- docs/plans/handoff.md

### 验证结果
- 已阅读 [PLAN-20260328-device-classification-modeling-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-optimization.md)、[PLAN-20260328-device-classification-modeling-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-audit.md)、`current-status.md`、`handoff.md` 现有相关块。
- 已核对前端受影响文件与后端设备接口、注册表、请求模型之间的真实对应关系。
- 已完成最小前端适配：
  - `frontend/src/api/device.ts` 增加 `location_id / updated_at`
  - `frontend/src/views/DeviceManager.vue` 的默认设备类型列表补齐到 10 种
- 已执行 `cd frontend && npm run build`，构建通过。

### 剩余风险
- 本轮没有看到后端线程专门写出的“设备分类与对象分层建模第一批后端收敛”交接块；当前判断仍以静态代码和正式 PLAN 为主，属于预估性联调结论。
- `DeviceManager.vue`、`EnergyManagement.vue`、`Dashboard.vue`、`CampusScene.vue` 仍主要消费旧标签语义，本轮只记录风险，不扩张为页面重构。
- 若后端下一步仅通过兼容新增字段暴露对象语义，前端仍需再做一轮 API 类型补齐和最小消费确认。

### 修改文件补充
- docs/plans/PLAN-20260327-multi-energy-data-audit.md
- docs/plans/PLAN-20260327-multi-energy-data-optimization.md
- docs/plans/current-status.md
- docs/plans/handoff.md

---

## 2026-03-28｜设备分类与对象分层建模审计（探索）

### 当前阶段
- 设备分类与对象分层建模审计：已完成探索文档沉淀，待规范线程收敛为实施计划。

### 本次目标
- 审计当前 `Device`、`EnergyData`、设备类型注册表、设备/能耗接口与前端页面在“设备对象、计量对象、点位对象、对象关系与多能源扩展建模”上的实际状态。
- 对照 EMS（MyEMS）式“能源类别 + 仪表对象 + 点位对象 + 业务对象 + 关系表”分层思路，判断当前系统处于什么层级。
- 为规范线程输出可直接继续收敛的输入，不把关键结论只留在聊天记录里。

### 发现的问题
- 当前系统不是没有设备分类能力，而是主要停留在 `device_type + device_category + energy_type` 的薄分类层；`Device` 同时承担业务设备、计量设备和能源类型标签语义。
- 当前没有独立计量对象层雏形：未发现 `meter / virtual meter / offline meter` 等正式模型，表计主要通过 `water_meter / gas_meter / heat_meter / cooling_meter / steam_meter` 这类 `device_type` 表达。
- 当前没有独立点位对象层雏形：能源采集值主要通过 `EnergyData` 宽表字段和上报 payload 承载，没有独立 `point / telemetry_point / measurement_point` 模型。
- `EnergyData` 仍是统一宽表，`voltage / current / pressure / temperature / supply_temp / return_temp / heat_flow / quality_index` 等异构字段共表存储，空字段与“本来无意义字段”混淆。
- `app/core/device_registry.py` 中声明的 `irradiance / wind_speed / soc / charging_status` 等字段，实际未被 `app/api/endpoints/devices/shared.py`、`app/domain/device_payloads.py`、`app/models/tables.py` 承接，存在“注册表定义”和“真实承载能力”不一致问题。
- 文档与代码存在不一致：
  - `docs/02-功能使用/统一设备管理指南.md` 写内置 11 种设备类型，但代码注册表实际为 10 种。
  - 输入指定的 `frontend/src/views/DeviceManagement.vue` 在仓库中不存在，实际文件为 `frontend/src/views/DeviceManager.vue`。

### 当前待办
#### 规范线程
- 基于 [PLAN-20260328-device-classification-modeling-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-audit.md) 收敛正式 PLAN。
- 已新增 [PLAN-20260328-device-classification-modeling-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-optimization.md)。
- 当前设备分类与对象分层建模主题以该 PLAN 为准。
- 第一批优先聚焦：
  - 设备对象 / 计量对象 / 能源类型对象边界治理
  - 宽表可空字段与专属字段语义治理
  - 点位 / 测点建模与扩展字段治理
- 明确非目标，避免一开始扩成数据库全量重构或全系统对象重建。

#### 后端线程
- 待规范线程确定计划后，再按最小范围处理对象边界和 schema / registry 一致性问题。
- 本轮不要提前扩张到告警、预测、控制、权限、认证、LSTM、MQTT 可靠性、碳排细则、费用结算细则等范围外模块。

#### 前端线程
- 待后端对象语义和接口口径明确后，再评估 `DeviceManager.vue` 与 `EnergyManagement.vue` 是否需要按新对象层次做最小联调适配。
- 本轮不做前端通用 UI 重构，也不提前用页面逻辑猜测 meter / point 语义。

### 修改文件
- docs/plans/PLAN-20260328-device-classification-modeling-audit.md
- docs/plans/current-status.md
- docs/plans/handoff.md
