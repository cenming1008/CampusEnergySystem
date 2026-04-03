# PLAN-20260329-frontend-visual-system-upgrade

> 状态：进行中（第一轮最小视觉闭环已阶段验收通过，可进入阶段收口判断） | 负责人：待定 | 更新时间：2026-03-29

---

## 背景

当前总控判断，“CampusEnergySystem 前端页面视觉升级任务”不属于当前主主题“前端架构收敛专题探索”，应作为新主题独立推进。

本轮探索已审视以下范围：

- `frontend/src/layout/Layout.vue`
- `frontend/src/views/Dashboard.vue`
- `frontend/src/views/CampusScene.vue`
- `frontend/src/views/DeviceMonitor.vue`
- `frontend/src/views/EnergyManagement.vue`
- `frontend/src/views/AlarmCenter.vue`
- `frontend/src/shared/`
- `frontend/src/features/`
- `frontend/src/assets/`
- `frontend/src/main.ts`

核心判断不是“单页面不好看”，而是“项目已有零散暗色高质感尝试，但缺少统一视觉系统，导致页面气质分裂、卡片层级不一致、标题区语言不统一、驾驶舱感没有被系统化复用”。

---

## 目标

- 将本任务明确为“前端视觉体系升级专题”，而不是若干单页面 UI 修补。
- 给规范线程和前端线程提供第一轮最小闭环入口，不直接展开完整 UI 重做。
- 先锁“哪些页面适合驾驶舱风格、哪些页面应保留后台管理风格”，避免风格误扩张。

## 规范收敛结论

### 1. 当前主题

- 本主题正式命名为：`前端视觉体系升级专题`
- 当前主问题是“视觉系统问题”，不是“单页面不好看”
- 当前执行依据为本 PLAN，不再继续使用“前端架构收敛专题探索”作为本轮视觉升级执行入口

### 2. 第一轮代表页

- 第一轮代表页继续锁定为：`frontend/src/views/Dashboard.vue`
- 第一轮只围绕该代表页推进，不新增第二个代表页

### 3. 页面分层原则

- 驾驶舱页升级候选：
  - `Dashboard.vue`
  - `CampusScene.vue`
  - 可选的 `DeviceMonitor.vue`
- 后台页只做视觉收敛，不做驾驶舱化：
  - `AlarmCenter.vue`
  - 设备管理 / 系统设置 / 用户管理 / 审计 / 报表等偏管理页

补充边界：

- 第一轮虽然允许把 `DeviceMonitor.vue` 视为驾驶舱候选，但不纳入并行改造。
- `EnergyManagement.vue` 本轮不作为第一轮驾驶舱候选执行入口，避免范围漂移。

### 4. 第一轮允许动作

- 只围绕 `Dashboard.vue` 做视觉系统第一轮最小闭环。
- 允许在代表页内吸收参考视觉语言，但必须服务园区综合能源业务语境。
- 不机械照抄参考页面结构。
- 若需补共享视觉基础，只允许补与代表页直接相关的最小视觉基础。

### 5. 第一轮最小视觉基础

- 暗色主题 token
- 卡片层级
- 标题区样式
- 状态色 / 图表色
- 基础留白与栅格节奏

### 6. 第一轮禁止扩张项

- 不直接进入 `CampusScene.vue`、`DeviceMonitor.vue`、`EnergyManagement.vue`、`AlarmCenter.vue` 的并行改造
- 不把后台管理页整体驾驶舱化
- 不把本轮扩成完整设计系统重建
- 不先做：
  - 全局 Layout 重做
  - Element Plus 全量换皮
  - 全部页面统一改版
  - 纯展示化大屏改造

### 7. 线程路径

- 当前线程路径固定为：`规范 -> 前端 -> 验收`
- 第一轮默认不并行拉入其他线程

## 关键结论

### 1. 当前问题定义

当前主问题更适合定义为“缺少统一视觉系统”，不是“某一页单独不好看”。

### 2. 已存在的视觉雏形

当前已有可复用雏形，但仍是零散状态：

- `Dashboard.vue`
- `CampusScene.vue`
- `shared/ui/MetricCard.vue`
- `shared/ui/StatTile.vue`

这些说明当前不是从零设计，而是缺少统一语言与复用落点。

### 3. 页面分层边界

- 驾驶舱页升级强调主视觉、信息密度、指标层级和园区能源态势表达。
- 后台页视觉收敛强调管理可读性、操作效率与统一风格，不追求驾驶舱化展示编排。

## 第一轮最小闭环建议

第一轮建议只做：

1. 锁定 `Dashboard.vue` 为代表页。
2. 锁定一套最小视觉基础：
   - 暗色主题 token
   - 卡片层级
   - 标题区样式
   - 状态色 / 图表色
   - 基础留白与栅格节奏
3. 只允许代表页吸收统一视觉语言，不并行改 `CampusScene.vue`、`DeviceMonitor.vue`、`EnergyManagement.vue`、`AlarmCenter.vue`。

## 非目标

- 本轮不改前端代码。
- 不直接产出最终 UI。
- 不做完整设计系统重建。
- 不把所有页面一轮全部驾驶舱化。
- 不先重做 `Layout.vue`。
- 不同步推进前端架构专题第二轮。
- 不直接进入 `CampusScene.vue`、`DeviceMonitor.vue`、`EnergyManagement.vue`、`AlarmCenter.vue` 的并行改造。
- 不机械照抄参考页面结构。

## 风险与拍板点

- 若不先锁“驾驶舱页”和“后台页”的风格边界，前端线程容易把所有页面一起做成展示型界面。
- 若第一轮先从 `Layout.vue` 或 token 抽象开始，容易变成长周期设计治理，短期没有代表性结果。
- 若直接拉 `CampusScene.vue` 起步，容易受其当前 3D/荧光场景语言牵引，反而不利于建立整个产品主视觉。

需要拍板：

- 当前无需新增拍板；主题名、第一轮代表页、页面分层原则和第一轮最小视觉基础均已锁定。
- 仅当第一轮被证明必须扩到第二个代表页，或必须先动全局 Layout / Element Plus，才升级为新一轮拍板。

## 验收标准

- [x] 已明确本主题独立于“前端架构收敛专题探索”。
- [x] 已明确当前问题属于“前端视觉体系升级专题”，不是单页面改好看。
- [x] 已明确驾驶舱页升级与后台页视觉收敛的页面分层。
- [x] 已明确第一轮代表页仍为 `Dashboard.vue`。
- [x] 已明确第一轮最小视觉基础与禁止扩张项。
- [x] `PLAN`、`current-status.md`、`handoff.md` 三者已对齐。

## 阶段验收结论（2026-03-29）

- 验收范围：
  - 只验收 `Dashboard.vue` 第一轮最小视觉闭环
  - 辅助核对 `StatTile.vue` 与 `useDashboardCharts.ts` 是否让最小视觉基础落地
  - 不把 `CampusScene.vue`、`DeviceMonitor.vue`、`EnergyManagement.vue`、`AlarmCenter.vue`、`Layout.vue`、Element Plus 全量换皮或全站统一改版纳入本轮必改范围
- 验收结果：本轮“前端视觉体系升级专题”第一轮最小视觉闭环已成立，可进入阶段收口。
- 已确认：
  - [Dashboard.vue](/Users/todo/MineEnergySystem/frontend/src/views/Dashboard.vue) 已形成较稳定的园区驾驶舱主视觉语言，不只是局部美化：标题区、主指标卡、glass card 层级、状态色、图表色与留白节奏彼此一致。
  - 页面级暗色视觉 token 已落在 `Dashboard.vue`，包括背景层、表面层、边框、阴影、高亮色、状态色与文本层级，足以支撑代表页统一气质。
  - [StatTile.vue](/Users/todo/MineEnergySystem/frontend/src/shared/ui/StatTile.vue) 已接入同一套卡片材质、边框、阴影与状态色 token，说明最小视觉基础已开始具备复用能力。
  - [useDashboardCharts.ts](/Users/todo/MineEnergySystem/frontend/src/features/dashboard/composables/useDashboardCharts.ts) 已同步收敛图表色板与预警色，代表页的图表语言与卡片/状态语言保持一致。
  - 本轮仍只围绕 `Dashboard.vue` 一个代表页推进，未扩到 `CampusScene.vue`、`DeviceMonitor.vue`、`EnergyManagement.vue`、`AlarmCenter.vue`、`Layout.vue` 或全局入口层。
  - 当前视觉方向仍服务园区综合能源业务语境，未被改成纯展示化大屏或脱离业务的概念页。
  - 已执行 `cd frontend && npm run build`，通过。
- 当前不阻止阶段收口的剩余风险：
  - 当前视觉 token 仍主要内聚在代表页与局部共享卡片，尚未证明可直接推广到更多页面。
  - 后台页边界虽已锁定，但尚未经过第二个页面的实证验证。
  - 全局 Layout、Element Plus 与全站视觉入口仍未动，这些属于后续轮次候选，不构成本轮失败。
- 当前阶段结论：
  - 阶段结论：通过。
  - 主题结论：第一轮最小视觉闭环成立，可进入阶段收口；后续是否继续推进更多页面需另行判断。

## 进度记录

- 2026-03-29：探索线程完成前端视觉审计，确认本任务不属于当前“前端架构收敛专题探索”主题，建议升级为独立正式 PLAN。
- 2026-03-29：探索线程确认当前主问题为“缺少统一视觉系统”，不是单页面不好看，建议先以 `Dashboard.vue` 为代表页建立最小视觉闭环。
- 2026-03-29：规范线程根据已拍板结果锁定正式主题名、页面分层原则、第一轮代表页、第一轮最小视觉基础与 `规范 -> 前端 -> 验收` 路径。
- 2026-03-29：前端线程完成 `Dashboard.vue` 第一轮最小视觉闭环，补齐代表页 token、卡片层级、标题区样式、状态色与图表色；验收线程复核文件边界、视觉基础落点与构建结果，确认第一轮闭环成立，可进入阶段收口。

## 相关文档

- [docs/plans/current-status.md](/Users/todo/MineEnergySystem/docs/plans/current-status.md)
- [docs/plans/handoff.md](/Users/todo/MineEnergySystem/docs/plans/handoff.md)
- [frontend/src/views/Dashboard.vue](/Users/todo/MineEnergySystem/frontend/src/views/Dashboard.vue)
- [frontend/src/views/CampusScene.vue](/Users/todo/MineEnergySystem/frontend/src/views/CampusScene.vue)
- [frontend/src/views/AlarmCenter.vue](/Users/todo/MineEnergySystem/frontend/src/views/AlarmCenter.vue)
