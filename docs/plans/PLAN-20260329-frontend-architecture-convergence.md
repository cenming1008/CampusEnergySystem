# PLAN-20260329-frontend-architecture-convergence

> 状态：进行中（探索完成，待规范 / 前端接棒） | 负责人：待定 | 更新时间：2026-03-29

---

## 背景

当前总控判断，“CampusEnergySystem 前端架构问题”不属于当前主主题“报警链路审计与最小修复路径分析”，应作为新主题独立推进。

探索线程已对以下范围完成定向审计：

- `frontend/src/views/Dashboard.vue`
- `frontend/src/views/DeviceMonitor.vue`
- `frontend/src/views/AlarmCenter.vue`
- `frontend/src/router/index.ts`
- `frontend/src/main.ts`
- `frontend/eslint.config.js`
- `frontend/src/utils/request.ts`
- `frontend/src/stores/`
- `frontend/src/features/`
- `frontend/src/shared/`

探索结论不是“前端完全没有分层”，而是：

1. `features/`、`shared/`、`stores/` 已经出现真实分层雏形。
2. 但核心页面、入口注册、状态沉淀和 lint 治理没有一起继续收敛。
3. 结果表现为“少量页面极重 + 一部分能力已抽离 + 一部分关键状态层仍为空或未定型”的混合状态。

因此本轮更适合定义为“前端架构收敛专题”，而不是若干孤立页面修修补补。

---

## 目标

- 明确当前问题是“前端分层已起步但未收敛完成”，而不是单纯几个页面代码太长。
- 为规范线程和前端线程提供一个正式 PLAN 和第一轮最小闭环入口。
- 锁定结构性问题与实现细节的边界，避免前端线程直接扩成大重构。

## 非目标

- 本轮不修改前端代码。
- 不产出完整重构方案。
- 不在本轮同时处理所有大页面。
- 不把本轮扩成设计系统重建、全量 store 重写或路由体系重构。

## 范围

涉及目录或模块：

- `frontend/src/views/`
- `frontend/src/router/index.ts`
- `frontend/src/main.ts`
- `frontend/eslint.config.js`
- `frontend/src/utils/request.ts`
- `frontend/src/stores/`
- `frontend/src/features/`
- `frontend/src/shared/`
- `docs/plans/`

明确不改动：

- 后端告警主题代码
- 非前端主题的实现代码
- 业务接口契约

## 关键结论

### 1. 任务定义

当前问题更适合定义为“整体前端分层仍未完成”，而不只是“局部页面过重”。

原因：

- `Dashboard.vue` 约 2125 行，已引入多个 feature/shared composable，但页面本身仍承载大量计算属性、图表组装和展示编排。
- `DeviceMonitor.vue` 约 980 行，仍以页面脚本直接承接接口调用、图表渲染、告警处理、控制操作和筛选逻辑。
- `AlarmCenter.vue` 只有约 279 行，更像局部页面，不足以单独代表整个架构问题。

这说明：

- “大页面过重”是表象。
- “核心页面没拆透、状态层未沉淀、入口治理未跟上”才是结构性问题。

### 2. 已存在的分层雏形

当前已经存在真实可复用的雏形，不应误判为从零开始：

- `features/dashboard/composables/*`
- `features/alarm/composables/useAlarmPolling.ts`
- `shared/composables/usePermissions.ts`
- `shared/composables/useCrudDialog.ts`
- `shared/composables/useCrudSubmit.ts`
- `shared/composables/useECharts.ts`
- `shared/ui/StatTile.vue`
- `stores/useAuthStore.ts`
- `stores/useSocketStore.ts`

这些都说明：

- feature/shared 分层方向已经被团队接受
- composable 抽离已开始
- shared 权限、CRUD、图表工具已具备基础复用能力

### 3. 仍未收敛完成的结构性问题

- 核心页面未拆透：
  - `Dashboard.vue` 仍是超重入口页
  - `DeviceMonitor.vue` 仍混合页面协调、数据加载、图表和交互处理
- 状态层偏轻：
  - `useDeviceStore.ts` 当前为空文件，说明关键设备监控/设备选择状态并未沉淀到稳定 store 层
- 入口治理偏弱：
  - `main.ts` 仍手工集中注册大量 Element Plus 组件和图标
- lint 治理偏松：
  - `no-unused-vars`
  - `@typescript-eslint/no-unused-vars`
  - `vue/no-mutating-props`
  当前都被关闭

## 推荐线程路径

- 当前推荐：`探索 -> 规范 -> 前端 -> 验收`

原因：

- 这轮不是先缺代码实现，而是先缺“前端架构收敛”边界。
- 需要规范线程先锁：
  - 这是不是架构专题
  - 第一轮只收哪个页面
  - 哪些规则先统一，哪些先不动

## 第一轮最小闭环建议

第一轮不建议先全局统一组件 / composable / store 原则后再动页面，那会过重。

更短闭环是：

1. 先把 `Dashboard.vue` 作为代表性页面收敛入口。
2. 只验证三件事：
   - 页面协调层与 feature composable 的边界
   - 视图衍生计算是否还能继续下沉
   - 是否需要一个稳定的 dashboard/device 级 store 或 page-level orchestrator
3. 同时只补一条最小治理规则：
   - 不允许继续把新增复杂逻辑直接堆回超大页面

原因：

- `Dashboard.vue` 已经有 feature/shared 雏形，最适合验证“继续拆透”而不是“从零设计”。
- `AlarmCenter.vue` 太轻，不足以代表结构性问题。
- `DeviceMonitor.vue` 也适合作为后续第二轮对象，但第一轮先抓一个更高代表性的入口页更稳。

## 优先级判断

本轮优先级建议：

1. 页面过重与分层不彻底
2. 状态管理偏轻
3. ESLint 规则放松
4. Element Plus 注册方式

解释：

- 页面过重和分层不彻底已经直接影响可维护性，是当前主因。
- 状态层偏轻会限制后续继续抽离，是第二优先级。
- ESLint 放松会放大问题，但更像治理闸门，不是当前第一根因。
- Element Plus 手工注册偏重，但目前更像入口样板问题，不是当前最痛点。

## 风险与拍板点

- 风险：若不先锁“结构性问题”和“实现细节”的边界，前端线程容易直接展开大重构。
- 风险：若先全局统一规则、不选代表页，主题会变成长周期抽象治理，短期难闭环。
- 风险：若只盯页面行数，不处理状态沉淀和入口治理，收敛会停在表面。

需要拍板：

- 第一轮是否明确以 `Dashboard.vue` 作为代表页。
- 第一轮是否只做“代表页收敛 + 一条最小治理规则”，而不同时推进 `DeviceMonitor.vue`。

## 验收标准

- [ ] 已明确本主题独立于“报警链路审计与最小修复路径分析”。
- [ ] 已明确当前问题属于“前端架构收敛专题”，不是若干孤立页面修补。
- [ ] 已明确哪些分层雏形已存在，哪些问题仍未收敛。
- [ ] 已明确推荐线程路径和第一轮最小闭环入口。
- [ ] `PLAN`、`current-status.md`、`handoff.md` 三者已对齐。

## 进度记录

- 2026-03-29：探索线程完成前端入口、超大页面、feature/shared/stores/lint 现状审计，确认本任务不属于当前报警主题。
- 2026-03-29：探索线程确认本轮更适合定义为“前端架构收敛专题”，建议先以 `Dashboard.vue` 作为代表页建立第一轮最小闭环。

## 相关文档

- [docs/plans/current-status.md](/Users/todo/MineEnergySystem/docs/plans/current-status.md)
- [docs/plans/handoff.md](/Users/todo/MineEnergySystem/docs/plans/handoff.md)
- [frontend/src/views/Dashboard.vue](/Users/todo/MineEnergySystem/frontend/src/views/Dashboard.vue)
- [frontend/src/views/DeviceMonitor.vue](/Users/todo/MineEnergySystem/frontend/src/views/DeviceMonitor.vue)
- [frontend/src/views/AlarmCenter.vue](/Users/todo/MineEnergySystem/frontend/src/views/AlarmCenter.vue)
