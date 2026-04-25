# PLAN-20260424 能源管理与能耗分析合并

## 目标
- 将 `/energy` 与 `/forecast` 两个能源主题入口合并为一个 `/energy` 页面。
- 菜单统一为「能源管理」，通过 Tab 承载总览、趋势与对比、排行与异常、数据录入。
- 后端以 `/energy/overview` 作为统一聚合入口，合并原 `/analysis/overview` 的趋势、对比、排行、异常与洞察字段。
- `/analysis/overview` 不再作为前端主页面接口；`/analysis/{device_id}` 单设备分析继续保留。

## 范围
- 前端：
  - `frontend/src/views/EnergyManagement.vue`
  - `frontend/src/api/energy.ts`
  - `frontend/src/router/index.ts`
  - `frontend/src/layout/Layout.vue`
  - 删除旧 `frontend/src/views/EnergyAnalysis.vue`
  - 删除旧 `frontend/src/api/analysis.ts`
- 后端：
  - `app/api/endpoints/energy/data.py`
  - `app/api/endpoints/energy/shared.py`
  - `app/application/analysis.py`
  - `app/services/analysis_service.py`
  - `app/services/energy_service.py`
- 测试：
  - `tests/test_analysis_service.py`
  - `tests/test_application_use_cases.py`
  - `tests/test_endpoint_application_convergence.py`
  - `frontend/src/views/__tests__/EnergyManagement.test.ts`

## 契约
- `GET /energy/overview` 参数：
  - `start_time`
  - `end_time`
  - `device_id`
  - `location_id`
  - `energy_type`
  - `top_n`，范围 `3-20`，默认 `5`
  - `granularity`，`hour/day`，默认 `day`
  - `include_analysis`，默认 `true`
- `device_id` 与 `location_id` 同时存在时，分析范围取交集。
- `trend` 返回兼容旧字段 `items`，同时新增：
  - `granularity`
  - `points: [{ timestamp, value, load? }]`
- `comparison` 返回兼容旧字段，同时新增：
  - `current`
  - `previous`
  - `ratio`
  - `mix: [{ energy_type, share }]`
- `ranking` 返回兼容旧 `areas`，同时新增：
  - `regions`
  - `buildings`
  - `devices`
- `anomaly` 返回兼容旧 `summary/items`，同时新增：
  - `missing_data`
  - `consecutive_failures`
  - `unresolved_alarms`
- `insights` 在 `/energy/overview` 输出为字符串数组。

## 非目标
- 不删除 `/analysis/{device_id}` 单设备分析接口。
- 不为 `/analysis/overview` 提供 deprecated 代理；当前仍处开发阶段且无已知外部消费者，统一收敛到 `/energy/overview`。
- 不重做能源统计、碳排核算或 EnergyData 表结构。
- 不扩张煤矿专属语义。
- 不处理仓库内与本主题无关的既有未提交改动。

## 当前进展
- [x] `/energy/overview` 已透传 `device_id/location_id/energy_type/top_n/granularity`。
- [x] `AnalysisService` 已支持显式 `granularity` 与设备/位置交集过滤。
- [x] `EnergyService.get_analysis_overview()` 已作为能源总览聚合入口复用 analysis service。
- [x] `/energy/overview` 已输出合并后的新分析字段，并保留旧 analysis 形态兼容字段。
- [x] `/forecast` 路由与菜单已移除，菜单文案改为「能源管理」。
- [x] `EnergyManagement.vue` 已作为 4 Tab 容器消费合并接口，新增粒度与 Top N 控制。
- [x] 旧 `EnergyAnalysis.vue` 与 `api/analysis.ts` 已删除。

## 验收标准
- 后端目标测试通过：
  - `./venv/bin/python -m pytest tests/test_analysis_service.py tests/test_endpoint_application_convergence.py tests/test_application_use_cases.py -q`
- 前端目标测试与类型检查通过：
  - `cd frontend && npm run test:unit -- src/views/__tests__/EnergyManagement.test.ts`
  - `cd frontend && npm run typecheck`
- 构建通过：
  - `cd frontend && npm run build`
- 仓库内不再有旧 `EnergyAnalysis`、`/forecast` 主入口或 `getAnalysisOverview` 调用残留。

## 风险
- `/analysis/overview` 已按开发阶段破坏性清理处理；当前无已知外部消费者，不提供 deprecated 代理。若后续发现仓库外调用，再单独按兼容需求立项。
- 当前页面仍保留大量既有能源页样式与图表逻辑，后续可再单独拆组件，但本轮不做大重构。
- 当前存在大量非本主题既有工作区改动，本轮只对能源合并相关文件负责。
