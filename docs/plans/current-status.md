# Current Status

## 当前总目标
- 当前主主题：`能源管理与能耗分析合并`
- 当前总目标：合并 `/energy` 与 `/forecast` 两个能源主页面，统一为 `/energy`「能源管理」，并把原 `/analysis/overview` 分析字段整合进 `/energy/overview`。
- 当前执行依据：
  - /Users/todo/CampusEnergySystem/docs/plans/PLAN-20260424-energy-management-analysis-convergence.md

---

## 当前阶段
- [x] 规则角色已确认本主题符合园区 EMS 主线：多能源接入、分层计量、分项分析、告警联动与驾驶舱展示。
- [x] 后端已完成 `/energy/overview` 扩参：`device_id`、`location_id`、`energy_type`、`top_n`、`granularity`、`include_analysis`。
- [x] 后端已完成 `device_id` 与 `location_id` 同时生效时取交集的分析范围过滤。
- [x] 后端已通过 `EnergyService.get_analysis_overview()` 复用 `AnalysisService.get_energy_analysis_overview()`，避免复制趋势、排行、异常、洞察计算逻辑。
- [x] `/energy/overview` 已输出合并后的新字段：`trend.points`、`comparison.current/previous/ratio/mix`、`ranking.regions`、`anomaly.missing_data/consecutive_failures/unresolved_alarms`、字符串数组 `insights`，同时保留旧 analysis 形态兼容字段。
- [x] 前端已移除 `/forecast` 路由与菜单项，`/energy` 菜单文案已统一为「能源管理」。
- [x] 前端已删除旧 `EnergyAnalysis.vue` 与 `api/analysis.ts`。
- [x] `EnergyManagement.vue` 已作为 4 Tab 容器消费合并后的 `/energy/overview`，并增加趋势粒度与 Top N 控制。
- [x] 已补前后端回归测试。

## 当前阻塞
- 当前无代码阻塞。

## 当前待办
- [x] 执行最终构建与差异检查。
- [x] 根据验证结果执行本主题阶段验收与 daily 快照归档。

## 当前验证结论
- `./venv/bin/python -m pytest tests/test_analysis_service.py tests/test_endpoint_application_convergence.py tests/test_application_use_cases.py -q` 通过：`27 passed, 1 warning`。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run test:unit -- src/views/__tests__/EnergyManagement.test.ts` 通过：`1 file / 2 tests passed`。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run typecheck` 通过。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run build` 通过；仅保留 Vite 大 chunk 提示。
- `git diff --check -- <本轮触碰文件>` 通过。
- 旧入口残留搜索已确认：生产代码中无 `EnergyAnalysis`、`/forecast` 路由/菜单、`getAnalysisOverview` 或 `@/api/analysis` 调用残留；仅测试断言和文档/注释保留历史说明。

## 当前验收判断
- 当前可判定：后端合并接口、前端路由菜单精简、能源管理 Tab 消费合并接口已达到本轮目标。
- `/analysis/overview` 兼容代理已明确不做：当前仍处开发阶段且无已知外部消费者，统一收敛到 `/energy/overview`。
- 建议本主题按“阶段完成；后续如需组件拆分另开主题”收口。

## 当前剩余风险
- `EnergyManagement.vue` 仍是较大的页面文件，本轮只做合并与最小交互补齐，不扩张为组件化重构。
- 当前工作区存在大量非本主题既有改动，本轮验收只覆盖能源合并相关文件。
