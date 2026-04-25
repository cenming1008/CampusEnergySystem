# 2026-04-24 Energy Management Handoff

## 主题
- `能源管理与能耗分析合并`

## 交接结论
- `/energy` 已成为能源主题唯一前端主入口。
- `/energy/overview` 已成为能源管理页面统一聚合读取入口。
- 原 `/analysis/overview` 主页面消费链路已从前端移除；`/analysis/{device_id}` 单设备分析仍保留。

## 关键契约
- `GET /energy/overview`：
  - `top_n`: `3-20`
  - `granularity`: `hour/day`
  - `device_id` 与 `location_id` 同时存在时取交集。
- 合并分析字段：
  - `trend.granularity`
  - `trend.points`
  - `comparison.current/previous/ratio/mix`
  - `ranking.regions/buildings/devices`
  - `anomaly.missing_data/consecutive_failures/unresolved_alarms`
  - `insights: string[]`
- 兼容字段仍保留：
  - `trend.items`
  - `comparison.period_over_period`
  - `ranking.areas`
  - `anomaly.summary/items`

## 下一棒
- 若通过，建议本主题以“阶段完成；后续组件拆分另开主题”收口。
- `/analysis/overview` 兼容代理已明确不做：当前仍处开发阶段且无已知外部消费者，统一收敛到 `/energy/overview`。

## 已验证
- `./venv/bin/python -m pytest tests/test_analysis_service.py tests/test_endpoint_application_convergence.py tests/test_application_use_cases.py -q` 通过：`27 passed, 1 warning`。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run test:unit -- src/views/__tests__/EnergyManagement.test.ts` 通过：`1 file / 2 tests passed`。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run typecheck` 通过。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run build` 通过；仅保留 Vite 大 chunk 提示。
- `git diff --check -- <本轮触碰文件>` 通过。
- 旧入口残留搜索已确认：生产代码中无 `EnergyAnalysis`、`/forecast` 路由/菜单、`getAnalysisOverview` 或 `@/api/analysis` 调用残留；仅测试断言和文档/注释保留历史说明。

## 注意事项
- 当前工作区存在大量非本主题既有改动，验收时只聚焦能源合并相关文件。
- 若后续发现仓库外仍调用 `/analysis/overview`，再单独按兼容需求立项。
