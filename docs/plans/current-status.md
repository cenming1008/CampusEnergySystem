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
- [x] 验收已执行
- [x] 多能源数据业务逻辑探索完成
- [x] 多能源数据业务优化：规范收敛完成
- [x] 多能源数据业务优化：后端第一批已实施

---

## 本次目标
- 只聚焦 `devices/data`、`analysis`、`reports` 三条主路径
- 以 application use case 收口主流程，而不是继续让 endpoint 或 service 承担总编排
- 在保持接口兼容前提下完成最小有效收敛，并同步更新 `current-status.md` / `handoff.md`
- 基于多能源探索结论形成第一批正式实施计划
- 为后端线程和前端线程明确多能源数据业务优化的执行边界与联调边界

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

### 后端线程
- 已按 [PLAN-20260327-multi-energy-data-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-multi-energy-data-optimization.md) 完成第一批多能源后端收敛：
  - `EnergyData` 相关统计不再直接把累计量 `consumption` 求和，`statistics` / `overview` 改为按时段首末差值计算周期消耗，瞬时量 `flow_rate` 单独统计均值 / 峰值。
  - 已补充电 / 水 / 气 / 热 / 冷 / 蒸汽的第一批业务语义、累计单位、瞬时单位和统计口径说明，并通过 `/energy/types`、`/energy/overview`、`/analysis/{device_id}` 暴露兼容新增字段。
  - `/energy/carbon/summary` 已改为基于能耗时段差值的展示级碳排估算，并明确 `display_estimate` / `is_accounting_grade=false` 边界；原始 `carbon_emissions` 明细接口继续保留兼容。
  - `analysis` 已支持多能源语义字段，保留 `current_power` / `today_energy` 兼容字段，同时新增 `energy_type`、`today_consumption_unit`、`current_value_unit` 等说明字段。
  - `reports` 已新增 `multi_energy_summary` CSV 导出类型，用于按能源类型导出周期消耗、瞬时统计和展示级碳排估算；原有 `energy_detail` / `carbon_emission` / `alarm_history` 保持可用。
- 本轮未做数据库 schema 改造，未改前端页面，未扩张到告警 / 预测 / 控制链路。

### 验收线程
- 已按验收线程要求复核 `docs/guides/*`、`docs/plans/*`、`handoff.md`、本轮多能源相关后端 / 前端代码与测试证据。
- 验收结论：本轮技术实现已基本达到“第一批多能源数据业务优化”目标，但暂不建议正式收口。
- 当前最大缺口不是继续开发主功能，而是“正式 PLAN 进度记录仍停留在未开始，和 current-status / handoff / 实际代码状态不一致”，尚未形成严格意义上的文档闭环。
- 前端已完成联调准备与最小适配，但 `Dashboard.vue`、`EnergyManagement.vue` 仍保留跨能源混算和展示边界未消费的存量页面逻辑；该项属于已识别风险，不视为本轮新增开发项。

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

### 后端线程
- [x] 只在 `devices/data`、`analysis`、`reports` 三条主路径内实施 application 收敛
- [x] 让 endpoint 只保留 HTTP 适配，application 接管编排，service 回收越界职责
- [x] 补充或更新与三条主路径直接相关的测试
- [x] 实施后回写计划进度、验证结果与剩余风险
- [x] 按多能源正式计划先处理口径、单位、碳排边界和 analysis / reports 第一批收敛
- [x] 保持最小兼容实现，没有扩张为全模型重构、全碳核算重写或全报表重构
- [ ] 下一轮如需继续推进，只在展示级碳排、单位换算落库和更细分能源指标上增量收敛

### 前端线程
- [x] 已完成 `energy`、`analysis`、`reports`、`carbon` 相关前端调用链审计，并明确高风险页面与字段依赖
- [x] 已补齐 API 层多能源兼容字段类型，优先让前端通过数据层理解新口径，不扩大为页面重构
- [x] 已为 `reports/export_csv` 接入 `multi_energy_summary` 最小前端入口，沿用现有 blob 下载逻辑
- [x] 保持现有页面结构与交互不变，没有顺手扩张为驾驶舱或多能源页改版
- [ ] 待后端真实联调环境就绪后，按新口径复测驾驶舱、多能源页和报表页的展示一致性

### 验收线程
- [x] 已完成探索 / 规范 / 后端 / 前端四类产出统一验收
- [ ] 暂不建议将本轮标记为“正式收口”
- [ ] 建议先回到规范线程补齐 [PLAN-20260327-multi-energy-data-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-multi-energy-data-optimization.md) 的进度记录、状态与验收结果，再由验收线程做一次最终确认

---

## 修改文件
- app/application/README.md
- frontend/src/api/telemetry.ts
- frontend/src/api/energy.ts
- frontend/src/api/report.ts
- frontend/src/views/Report.vue
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
- 前端已完成三条主路径依赖审计：
  - `devices/data` / `analysis`：`frontend/src/api/telemetry.ts`、`frontend/src/features/dashboard/composables/useDashboardRealtime.ts`、`frontend/src/views/CampusScene.vue`
  - `reports`：`frontend/src/api/report.ts`、`frontend/src/views/Report.vue`
- 已做最小前端适配：
  - `telemetry.ts` 增加 wrapped / unwrapped 返回兼容与数值字段归一化
  - `energy.ts` 补齐多能源新增语义字段、单位字段、碳排边界字段的类型定义
  - `report.ts` / `Report.vue` 增加与后端文件命名规则更接近的导出文件名兜底，并补上 `multi_energy_summary` 最小入口
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
- 前端当前没有直接调用 `POST /devices/{device_id}/data` 或 `GET /devices/{device_id}/statistics`；真正受影响的是把 `GET /devices/{device_id}/data` 当历史趋势源的页面，以及直接消费 `/analysis/{device_id}` 原始字段的页面。
- `Dashboard.vue` 与 `CampusScene.vue` 仍在前端自行拼区域排行、在线状态和总负荷口径；这类页面如果后续要切到稳定驾驶舱口径，仍需后端补 application 层统一聚合接口。
- `Report.vue` 仍依赖浏览器按 blob 下载成功来判断导出成功，且当前 axios 拦截器不暴露 `Content-Disposition`；若后端后续调整下载头或流式错误语义，需要再做一轮前端联调确认。
- 多能源前端当前最显著的业务风险不是“字段拿不到”，而是“旧页面仍可能按旧语义理解新字段”：
  - `useDashboardEnergyStats.ts` / `Dashboard.vue` 仍把不同能源的 `total_consumption` 直接合并成“今日总能耗 / 本月总能耗”，存在跨单位混算风险。
  - `EnergyManagement.vue` 仍把 `overview.statistics[*].total_consumption` 直接用于跨能源对比和总览展示，对 `cross_energy_mix_allowed`、`consumption_unit`、`consumption_stat_basis` 还没有展示级约束。
  - `EnergyManagement.vue` 的碳排展示和碳排计算器仍以“可展示结果”为主，尚未根据 `is_accounting_grade`、`boundary`、`note` 做更明确的核算边界提示。
- 本轮前端只完成了静态依赖审计和最小兼容接入；后端若在真实联调中继续调整 `total_consumption` 语义、单位字段或 `multi_energy_summary` 列结构，仍需再做一次前端定向确认。
- 验收视角补充：
  - 当前代码、`current-status.md`、`handoff.md` 对“第一批后端已实施、前端完成最小适配”的表述基本一致，但正式 PLAN 的状态与进度记录仍未同步更新，属于文档闭环缺口。
  - 前端页面层仍存在已知跨能源混算与展示边界未消费问题，不过规范与交接已明确其属于“本轮故意未做 / 待真实联调后再定向处理”的范围内风险。
  - 因此，本轮更接近“实现完成、验收发现文档闭环缺口”，而不是“业务功能未实现”。

---

## 2026-03-27 验收线程

### 本次目标
- 对“电 / 热 / 气 / 冷 / 碳排放数据业务优化”相关的探索、规范、后端、前端四类产出做统一验收。
- 判断本轮是否满足第一批多能源数据业务优化的收口条件，并把验收结论写回协作文档。

### 发现的问题
- [PLAN-20260327-multi-energy-data-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-multi-energy-data-optimization.md) 顶部状态仍为“未开始”，进度记录也只保留规范线程建计划时的信息，未反映后端已实施、前端已做最小适配、验收已执行的实际状态。
- [frontend/src/views/Dashboard.vue](/Users/todo/MineEnergySystem/frontend/src/views/Dashboard.vue) 与 [frontend/src/features/dashboard/composables/useDashboardEnergyStats.ts](/Users/todo/MineEnergySystem/frontend/src/features/dashboard/composables/useDashboardEnergyStats.ts) 仍把多能源 `total_consumption` 直接混算为单一总能耗。
- [frontend/src/views/EnergyManagement.vue](/Users/todo/MineEnergySystem/frontend/src/views/EnergyManagement.vue) 仍未消费 `cross_energy_mix_allowed`、`is_accounting_grade` 等边界字段，页面层展示口径尚未通过真实联调复核。

### 验收结论
- 探索线程结论、规范线程 PLAN、后端第一批实现、前端最小适配和现有交接文档已经能互相对应，说明本轮主功能实现基本闭环。
- 但由于正式 PLAN 进度未更新，文档层尚未达到“计划、状态面板、交接、代码、验证结果完全一致”的收口要求。
- 验收判断：暂不正式收口，优先补齐文档闭环；后端和前端当前不需要继续扩大实现范围。

### 修改文件
- docs/plans/current-status.md
- docs/plans/handoff.md

### 验证结果
- 已按要求阅读 `docs/guides/README.md`、`docs/guides/文档体系规范.md`、`docs/guides/变更计划规范.md`、`docs/plans/README.md`、`docs/plans/current-status.md`、`docs/plans/handoff.md`、[PLAN-20260327-multi-energy-data-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-multi-energy-data-audit.md)、[PLAN-20260327-multi-energy-data-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-multi-energy-data-optimization.md)。
- 已复核后端关键实现：`app/domain/energy_rules.py`、`app/services/energy_service.py`、`app/services/analysis_service.py`、`app/application/analysis.py`、`app/application/reporting.py`、`app/api/endpoints/energy/data.py`、`app/api/endpoints/energy/carbon.py`、`app/api/endpoints/reports.py`。
- 已复核前端最小适配：`frontend/src/api/energy.ts`、`frontend/src/api/telemetry.ts`、`frontend/src/api/report.ts`、`frontend/src/views/Report.vue`，并核对高风险存量页面。
- 已执行 `python3 -m compileall -q app tests`，通过。
- 已执行 `./venv/bin/python -m unittest tests.test_energy_domain tests.test_application_use_cases tests.test_reports_integration tests.test_energy_endpoint_semantics`，29 个测试通过。
- 已执行 `cd frontend && npm run build`，通过。

### 剩余风险
- 当前未闭环的核心问题是正式 PLAN 进度和状态未同步更新，这会让后续线程在“本轮是否已完成”上产生歧义。
- 前端页面层的跨能源混算与碳排展示边界提示仍未做真实联调确认，但该风险已被前端线程识别并写入交接，属于本轮可接受但需显式保留的剩余风险。
- 若下一步继续推进，应优先由规范线程补齐计划进度闭环；之后如真实联调暴露展示偏差，再交回前端线程做定向微调，而不是回到后端扩大主功能。

### 需要交接给谁
- 优先交回规范线程：补齐正式 PLAN 的状态、进度记录和验收结果，使计划文档与 current-status / handoff / 实际实现一致。
- 若规范线程补齐后仍需真实联调修正展示，再交前端线程按已识别风险做最小页面适配。

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

### 修改文件补充
- docs/plans/PLAN-20260327-multi-energy-data-audit.md
- docs/plans/PLAN-20260327-multi-energy-data-optimization.md
- docs/plans/current-status.md
- docs/plans/handoff.md
