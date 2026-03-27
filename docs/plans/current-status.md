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
- [x] 前端已完成依赖审计

---

## 本次目标
- 只聚焦 `devices/data`、`analysis`、`reports` 三条主路径
- 以 application use case 收口主流程，而不是继续让 endpoint 或 service 承担总编排
- 在保持接口兼容前提下完成最小有效收敛，并同步更新 `current-status.md` / `handoff.md`

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
- 已按计划完成三条主路径的第一批 application 收敛：
  - `devices/data`：endpoint 不再直接做访问控制和审计，application 接管权限前置、payload 编排、审计收口。
  - `analysis`：endpoint 不再直接做设备访问前置，application 接管访问校验与响应 DTO 装配。
  - `reports`：endpoint 不再直接做 `report_type` 分发和 CSV 主体装配，application 接管报表分发与导出 payload 组装。
- 已新增 [app/services/report_service.py](/Users/todo/MineEnergySystem/app/services/report_service.py) 作为稳定查询服务，避免 application 直接承载 ORM 报表查询细节。
- 已保持接口路径、请求参数、主要返回字段和 CSV 主要结构兼容；本轮没有做数据库 schema 变更。

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
- [ ] 等待后端线程按计划实施后回写进度

### 后端线程
- [x] 只在 `devices/data`、`analysis`、`reports` 三条主路径内实施 application 收敛
- [x] 让 endpoint 只保留 HTTP 适配，application 接管编排，service 回收越界职责
- [x] 补充或更新与三条主路径直接相关的测试
- [x] 实施后回写计划进度、验证结果与剩余风险

### 前端线程
- [x] 仅为 `devices/data`、`analysis`、`reports` 相关接口变化做联调准备与最小适配
- [x] 默认保持现有页面结构，不提前做页面重构
- [x] 若发现返回字段变化，先核对 `handoff.md`，不自行扩张为前端改版任务

---

## 修改文件
- frontend/src/api/telemetry.ts
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
- docs/plans/current-status.md
- docs/plans/handoff.md

---

## 验证结果
- 已阅读规范入口：`docs/guides/README.md`、`docs/guides/文档体系规范.md`、`docs/guides/变更计划规范.md`、`docs/guides/backend-guidelines.md`、`docs/plans/README.md`、`docs/plans/TEMPLATE.md`。
- 已阅读协作文档：`docs/plans/current-status.md`、`docs/plans/handoff.md`。
- 已核对探索线程写回的函数级证据，并复核 `devices/data`、`analysis`、`reports` 当前实现。
- 已执行 `python3 -m compileall -q app tests`，编译通过。
- 已执行 `./venv/bin/python -m unittest tests.test_application_use_cases tests.test_reports_integration tests.test_layer_exports tests.test_endpoint_application_convergence`，21 个测试通过。
- 已执行 `./venv/bin/python -c "import app.main; print('ok')"`，主应用导入通过。
- 目标 endpoint 最小可用性已通过单测验证：
  - `devices/data` endpoint 只委托 application
  - `analysis` endpoint 只委托 application
  - `reports/export_csv` 通过集成测试验证导出行为仍可用
- 前端已完成三条主路径依赖审计：
  - `devices/data` / `analysis`：`frontend/src/api/telemetry.ts`、`frontend/src/features/dashboard/composables/useDashboardRealtime.ts`、`frontend/src/views/CampusScene.vue`
  - `reports`：`frontend/src/api/report.ts`、`frontend/src/views/Report.vue`
- 已做最小前端适配：
  - `telemetry.ts` 增加 wrapped / unwrapped 返回兼容与数值字段归一化
  - `report.ts` / `Report.vue` 增加与后端文件命名规则更接近的导出文件名兜底
- 已执行 `cd frontend && npm run build`，构建通过

---

## 剩余风险
- 若后端线程把本轮任务理解成“全项目分层重构”，范围会失控。
- 若前端线程提前按猜测调整字段或页面，会放大联调成本。
- 若实施后不回写计划和 handoff，后续线程容易再次回到各自理解的状态。
- `DeviceService.report_device_data` 这一旧 helper 仍保留在 service 中作为兼容能力，但主路径已不再通过它编排；若后续要继续收敛，可在下一轮逐步降级其直接使用面。
- `reports` 主路径已收口到 application，但报表行查询仍分散在 `ReportService` 与 `EnergyRepository` 两层，属于当前计划允许的最小兼容方案，不在本轮继续下探 repository 重构。
- 前端当前没有直接调用 `POST /devices/{device_id}/data` 或 `GET /devices/{device_id}/statistics`；真正受影响的是把 `GET /devices/{device_id}/data` 当历史趋势源的页面，以及直接消费 `/analysis/{device_id}` 原始字段的页面。
- `Dashboard.vue` 与 `CampusScene.vue` 仍在前端自行拼区域排行、在线状态和总负荷口径；这类页面如果后续要切到稳定驾驶舱口径，仍需后端补 application 层统一聚合接口。
- `Report.vue` 仍依赖浏览器按 blob 下载成功来判断导出成功，且当前 axios 拦截器不暴露 `Content-Disposition`；若后端后续调整下载头或流式错误语义，需要再做一轮前端联调确认。
