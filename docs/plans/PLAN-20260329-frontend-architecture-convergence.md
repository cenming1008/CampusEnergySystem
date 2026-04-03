# PLAN-20260329-frontend-architecture-convergence

> 状态：进行中（第一轮代表页闭环已阶段验收通过，可进入阶段收口判断） | 负责人：待定 | 更新时间：2026-03-29

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

## 规范收敛结论

### 1. 当前主题

- 当前主主题保持为“前端架构收敛专题探索”。
- 本专题继续按结构性前端收敛问题推进，不拆成零散页面治理任务。

### 2. 第一轮代表页

- 第一轮只收一个代表页。
- 第一轮代表页确定为 `frontend/src/views/Dashboard.vue`。
- `DeviceMonitor.vue`、`AlarmCenter.vue` 不纳入第一轮实现范围。

### 3. 第一轮允许动作

- 只做“代表页收敛 + 一条最小治理规则”。
- 代表页收敛仅围绕 `Dashboard.vue`：
  - 页面协调层边界收敛
  - 已有 feature/shared/composable 分层继续下沉
  - 必要时做局部子组件、composable 或 page-level orchestrator 拆分
- 第一轮唯一治理规则：
  - 新增复杂逻辑不得继续堆回超大页面
- `frontend/src/stores/useDeviceStore.ts` 默认不补，除非前端线程在代表页收敛中证明它是必需前提。

### 4. 第一轮禁止扩张项

- 不新增第二个代表页。
- 不把第一轮升级成全局架构整治。
- 不并行推进：
  - ESLint 严格化
  - Element Plus 注册方式改造
  - router / main.ts 全局入口重排
- 不产出完整重构方案。

### 5. 优先级锁定

1. 页面过重与分层不彻底
2. 状态层偏轻
3. ESLint 规则放松
4. Element Plus 注册方式

### 6. 线程路径锁定

- 当前线程路径固定为：`规范 -> 前端 -> 验收`
- 第一轮默认不并行拉入其他线程。

## 非目标

- 本轮不修改前端代码。
- 不产出完整重构方案。
- 不在本轮同时处理所有大页面。
- 不把本轮扩成设计系统重建、全量 store 重写或路由体系重构。
- 不新增第二个代表页。
- 不默认补 `frontend/src/stores/useDeviceStore.ts`。
- 不并行推进 ESLint 严格化、Element Plus 注册方式改造、router / main.ts 全局入口重排。

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

第一轮已锁定为：

1. 只收 `Dashboard.vue` 一个代表页。
2. 只验证三件事：
   - 页面协调层与 feature composable 的边界
   - 视图衍生计算是否还能继续下沉
   - 是否必须引入 page-level orchestrator，或必须证明 `useDeviceStore.ts` 是前置条件
3. 只补一条最小治理规则：
   - 不允许继续把新增复杂逻辑直接堆回超大页面

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

- 当前无需新增拍板；第一轮代表页、范围、优先级与线程路径均已锁定。
- 仅当 `Dashboard.vue` 收敛被证明必须依赖 `useDeviceStore.ts` 或已超出第一轮边界时，再升级为新一轮拍板。

## 验收标准

- [x] 已明确本主题独立于“报警链路审计与最小修复路径分析”。
- [x] 已明确当前问题属于“前端架构收敛专题”，不是若干孤立页面修补。
- [x] 已明确哪些分层雏形已存在，哪些问题仍未收敛。
- [x] 已锁定第一轮代表页为 `Dashboard.vue`，且仅允许“代表页收敛 + 一条最小治理规则”。
- [x] 已明确第一轮禁止扩张项、打回条件与验收口径。
- [x] `PLAN`、`current-status.md`、`handoff.md` 三者已对齐。

## 阶段验收结论（2026-03-29）

- 验收范围：
  - 只核对 `Dashboard.vue` 第一轮代表页收敛是否成立
  - 只核对新增 [useDashboardViewModel.ts](/Users/todo/MineEnergySystem/frontend/src/features/dashboard/composables/useDashboardViewModel.ts) 与 [useDashboardCharts.ts](/Users/todo/MineEnergySystem/frontend/src/features/dashboard/composables/useDashboardCharts.ts) 是否让 feature/shared/composable 边界更清楚
  - 不把 `DeviceMonitor.vue`、`AlarmCenter.vue`、`router/index.ts`、`main.ts`、`eslint.config.js`、`useDeviceStore.ts` 纳入本轮必改范围
- 验收结果：本轮“前端架构收敛专题”第一轮代表页闭环已成立，可进入阶段收口。
- 已确认：
  - [Dashboard.vue](/Users/todo/MineEnergySystem/frontend/src/views/Dashboard.vue) 当前脚本层主要承担状态接线、初始化加载、设备切换与 composable 编排，更接近页面协调层，而不是继续内嵌大量衍生视图模型与图表监听细节。
  - [useDashboardViewModel.ts](/Users/todo/MineEnergySystem/frontend/src/features/dashboard/composables/useDashboardViewModel.ts) 已承接总览卡片、区域排行、设备焦点、告警语义、时段标签等衍生视图模型。
  - [useDashboardCharts.ts](/Users/todo/MineEnergySystem/frontend/src/features/dashboard/composables/useDashboardCharts.ts) 已承接图表初始化、配置生成与监听编排，避免继续堆回页面脚本。
  - 本轮改动仍只围绕 `Dashboard.vue` 一个代表页推进，未扩到 `DeviceMonitor.vue`、`AlarmCenter.vue`、`router/index.ts`、`main.ts`、`eslint.config.js` 或 `useDeviceStore.ts`。
  - 第一轮最小治理规则已被遵守：新增复杂逻辑未继续堆回超大页面，而是继续向 feature composable 下沉。
  - 已执行 `cd frontend && npm run build`，通过。
- 当前不阻止阶段收口的剩余风险：
  - `Dashboard.vue` 模板和样式体量仍大，但这属于后续继续收敛的空间，不构成第一轮代表页闭环失败。
  - `useDeviceStore.ts` 仍为空，说明状态层仍有空档，但当前尚未证明它是第一轮闭环前提。
  - ESLint、Element Plus 注册方式、`router / main.ts` 入口治理仍未处理，但都属于本轮明确冻结项。
- 当前阶段结论：
  - 阶段结论：通过。
  - 主题结论：第一轮最小闭环成立，可进入阶段收口；是否继续推进第二轮应在收口后另行决定。

## 进度记录

- 2026-03-29：探索线程完成前端入口、超大页面、feature/shared/stores/lint 现状审计，确认本任务不属于当前报警主题。
- 2026-03-29：探索线程确认本轮更适合定义为“前端架构收敛专题”，建议先以 `Dashboard.vue` 作为代表页建立第一轮最小闭环。
- 2026-03-29：规范线程根据已拍板结果锁定当前主题、第一轮代表页、允许动作、禁止扩张项、打回条件与 `规范 -> 前端 -> 验收` 路径。
- 2026-03-29：前端线程完成 `Dashboard.vue` 第一轮代表页收敛，新增 `useDashboardViewModel.ts` 与 `useDashboardCharts.ts`；验收线程复核文件边界与构建结果，确认第一轮最小闭环成立，可进入阶段收口。

## 相关文档

- [docs/plans/current-status.md](/Users/todo/MineEnergySystem/docs/plans/current-status.md)
- [docs/plans/handoff.md](/Users/todo/MineEnergySystem/docs/plans/handoff.md)
- [frontend/src/views/Dashboard.vue](/Users/todo/MineEnergySystem/frontend/src/views/Dashboard.vue)
- [frontend/src/views/DeviceMonitor.vue](/Users/todo/MineEnergySystem/frontend/src/views/DeviceMonitor.vue)
- [frontend/src/views/AlarmCenter.vue](/Users/todo/MineEnergySystem/frontend/src/views/AlarmCenter.vue)
