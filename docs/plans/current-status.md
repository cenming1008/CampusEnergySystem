# Current Status

## 当前总目标
- 将 `docs/plans/` 当前主主题切换为“前端架构收敛专题探索”，先明确结构性问题、现有分层雏形与第一轮最小闭环入口，不进入代码实现。
- 让 [PLAN-20260329-frontend-architecture-convergence.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260329-frontend-architecture-convergence.md) 成为当前执行依据，避免后续线程把问题误缩成若干局部页面修补。

---

## 当前阶段
- [x] 探索线程已确认：本轮“CampusEnergySystem 前端架构问题”不属于当前主区原主题“报警链路审计与最小修复路径分析”
- [x] 已建立正式 PLAN：[PLAN-20260329-frontend-architecture-convergence.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260329-frontend-architecture-convergence.md)
- [x] 已完成前端入口、超大页面、feature/shared/stores/lint 现状审计
- [x] 已确认当前问题更适合定义为“前端架构收敛专题”，不是若干孤立页面治理任务的简单拼接
- [x] 已确认 feature/shared 分层雏形已存在，但核心页面、状态层、入口治理和 lint 规则仍未收敛完成
- [ ] 待规范线程锁定专题边界、第一轮代表页与最小治理规则
- [ ] 待前端线程按第一轮最小闭环推进，不扩成全局重构

---

## 当前阻塞
- 当前还没有锁定“前端架构收敛专题”的结构性边界；若直接交前端实现，容易扩成多页面并行重构。
- `Dashboard.vue` 已有 feature/shared composable 雏形，但页面层仍承载大量衍生计算、图表组装和协调逻辑；是否继续拆透、拆到哪一层，还需先定边界。
- `useDeviceStore.ts` 当前为空文件，说明关键业务状态尚未沉淀；但是否在第一轮就补 store，需要先拍板。
- ESLint 当前关闭 `no-unused-vars`、`@typescript-eslint/no-unused-vars`、`vue/no-mutating-props`，会放大架构漂移，但不应在第一轮直接升级成全面规则整治。

## 当前待办
- [x] 判定本轮前端架构问题应新开主题，而非并入报警主题
- [x] 建立正式 PLAN，沉淀结构性问题、现有雏形与第一轮入口建议
- [ ] 规范线程锁定：
  - 专题名称
  - 第一轮代表页
  - 结构性问题与实现细节的边界
  - 第一轮是否只补一条最小治理规则
- [ ] 前端线程优先围绕 `Dashboard.vue` 做代表性收敛，不同时展开 `DeviceMonitor.vue`
- [ ] 验收线程复核“代表页收敛是否成立、是否未扩成全局重构”

## 当前验证结论
- 已确认当前问题不是“前端完全没有分层”，而是“整体分层已起步但未收敛完成”。
- 已确认现有分层雏形真实存在：
  - `features/dashboard/composables/*`
  - `features/alarm/composables/useAlarmPolling.ts`
  - `shared/composables/usePermissions.ts`
  - `shared/composables/useCrudDialog.ts`
  - `shared/composables/useCrudSubmit.ts`
  - `shared/composables/useECharts.ts`
  - `shared/ui/StatTile.vue`
  - `stores/useAuthStore.ts`
  - `stores/useSocketStore.ts`
- 已确认结构性问题仍然成立：
  - `Dashboard.vue` 约 2125 行，虽然已引入 feature/shared composable，但页面层仍承载大量展示编排、图表拼装和衍生计算。
  - `DeviceMonitor.vue` 约 980 行，仍由页面直接承接接口调用、图表渲染、告警处理、控制操作和筛选逻辑。
  - `AlarmCenter.vue` 约 279 行，更像局部页面问题，不足以单独代表当前架构专题。
  - `useDeviceStore.ts` 当前为空文件，说明关键设备相关状态尚未形成稳定 store 分层。
  - `main.ts` 仍手工集中注册大量 Element Plus 组件和图标，入口治理偏重。
  - ESLint 当前关闭 `no-unused-vars`、`@typescript-eslint/no-unused-vars`、`vue/no-mutating-props`，治理闸门明显偏松。
- 已确认本轮更适合定义为“前端架构收敛专题”，而不是“若干局部页面治理任务”的简单集合。
- 已确认第一轮最短闭环更适合“先选一个代表性页面做收敛”，建议以 `Dashboard.vue` 作为代表页，而不是先做全局规则统一。

## 当前剩余风险
- 若不先锁定“代表页收敛”边界，前端线程容易同时展开 `Dashboard.vue`、`DeviceMonitor.vue` 和入口治理，导致范围失控。
- 若先从 ESLint 或 Element Plus 注册方式入手，可能会把专题带偏成治理杂项，而不是先解决核心页面和分层不彻底问题。
- `useDeviceStore.ts` 为空说明状态层存在空档，但若第一轮直接引入新 store，也可能把问题提前升级为更重架构重排。
- 当前工作区虽然干净，但主区此前仍保留报警主题内容；若不依赖本轮回写，后续线程容易接错主题。

---

## 每日归档入口

- [2026-03-27 状态快照](./daily/2026-03/2026-03-27-status.md)
- [2026-03-28 状态快照](./daily/2026-03/2026-03-28-status.md)
