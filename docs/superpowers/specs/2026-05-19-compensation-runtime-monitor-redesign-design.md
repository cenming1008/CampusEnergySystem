# 补偿控制器运行监视模块重设计

日期：2026-05-19
范围：电容补偿设备（`capacitor_bank_controller`）工作台「运行监视」标签页主区 + 其右侧栏 UI 重设计

## 背景与问题

「运行监视」标签页（`CompensationMonitorView.vue` 的 `runtime` 分支）当前由三块纵向堆叠组成：

- `CompensationRealtimeOverview.vue`：无功功率小卡 + 功率因数 Hero + 累计告警次数条 + 标志位条。
- `CompensationDetailPanel.vue`：回路状态 / 三相量测分页。
- `ControlConsoleRemotePanel.vue`：远程控制。

来自 Claude Design 的重设计稿（`monitor.html` 及其 `app.jsx` / `panels.jsx` / `charts.jsx` / `styles.css`）针对的痛点：

1. **主次不清**：累计告警次数卡片视觉权重接近核心 KPI，抢戏。
2. **缺少电气语境**：没有 P-Q 象限图、电容器组拓扑这类专业可视化。
3. **回路状态**用密集小格表达，扫视效率低。
4. **三相状态**散在量测分页，缺少指标×相位的矩阵化总览。

## 设计目标

- 在现有 `MonitorViewShell` 响应式壳内重现设计稿的栅格结构与暗色青/绿视觉。
- 引入三大新可视化：PF 实时趋势（带目标带）、P-Q 运行象限图、设备健康度评分。
- 把逐回路投切状态重做成「电容器组拓扑示意」，把三相状态重做成「指标×相位矩阵」。
- 保持「无 mock 数据」原则：所有可视化基于真实遥测，数据缺失时优雅降级。

非目标：

- 不改动「历史曲线」「参数设置」「事件记录」三个标签页。
- 不改动非工作台分支（SVG / 通用设备视图），其继续复用 `CompensationRealtimeOverview` / `CompensationDetailPanel`。
- 不采用设计稿的 1600×960 固定画布缩放方案（与应用壳冲突）。
- 不改动后端 API、数据层 composable 的网络请求逻辑；新增的派生计算（健康度等）在前端 viewMapping / composable 层完成。
- 不重做设备头条（已由 `#header` 槽的 `CompensationHeader` 承担）。

## 选定方案：新建 `runtime/` 子目录组件

为重设计的运行监视标签页新建一组聚焦组件，置于 `frontend/src/features/device-monitor/components/compensation/runtime/`。`CompensationMonitorView.vue` 的 `runtime` 分支换用新组件；其它三个标签页与非工作台分支保持引用旧组件，故旧组件不删除、无死代码。

已评估并排除的替代方案：

- **改造现有 `CompensationRealtimeOverview` / `CompensationDetailPanel`**：这两个组件被非工作台分支复用，改造会牵连 SVG/通用设备视图，blast radius 大，且组件已偏大。
- **单一大组件 `CompensationRuntimeBoard.vue`**：SVG 图表 + 表格 + 抽屉混在一个文件，过大、难测难读。

## 布局

`runtime` 分支主区在 `MonitorViewShell` 的 `#main` 内重现设计稿栅格，保持响应式，矮视口允许滚动：

- **Hero 行**（3 栏，窄屏降为 1 栏）：PF 趋势卡 │ P-Q 运行象限卡 │ 设备健康度卡。
- **拓扑行**（整宽）：电容器组拓扑。
- **底部行**（2 栏，窄屏降为 1 栏）：三相状态矩阵 │ 远程控制。

`#side` 侧栏：仅当 `capacitor_bank_controller` 且当前为 `runtime` 标签时，渲染设计稿视觉的「未处理告警栏」+「控制参数摘要」；其它标签页保留现有侧栏（事件时间线 / 告警汇总 / 控制摘要 / 设备档案）。该条件化逻辑加在 `CompensationMonitorView.vue` 的 `#side` 模板中，复用现有 `shouldShowSideTraceability()` 同类的标签判断。

配色采用设计稿暗色青/绿调（底 `#07101c`、卡片 `#121d2e`、青 `#22d3ee`、绿 `#34d399`、琥珀 `#f59e0b`、红 `#ef4444`），所有样式 `scoped` 限定在新组件内，不外溢其它视图。

## 组件结构

新建组件均放在 `components/compensation/runtime/`：

### `CompensationRuntimeBoard.vue`
运行监视主区容器，组合 Hero 行 / 拓扑行 / 底部行，接收 `page: DeviceMonitorPageModel`，向下分发 props。`CompensationMonitorView.vue` 的 `runtime` 分支由「三块组件」替换为单个 `<CompensationRuntimeBoard :page="page" />`。

### `CompensationPfTrendCard.vue`
- Props：`pfTrend: CompensationPowerFactorTrend`、当前 `p`/`q`/`pf` 数值、`timeRange`。
- 内容：PF 大数字 + 较上一区间 Δ；目标带 sparkline（目标 PF 来自 `fallbackCompensation.targetPowerFactor`）；底部 P / Q / S 三个统计。
- 时间范围切换（10 分钟 / 1 小时 / 24 小时）复用 `page.timeRange` 与 `page.handleRangeChange`，不新建独立状态。
- 降级：`pfTrend.values.length < 2` 时隐藏 sparkline，仅显示大数字与统计；P/Q/S 取自 `realtime`，缺失显示 `--`。

### `CompensationPqQuadrantCard.vue`
- Props：当前 `p`（`realtime.flow_rate`）、`q`（`realtime.reactive_power`）、可选 `history: Array<[number, number]>`。
- 内容：四象限 SVG，画坐标轴、PF 等值线（0.9 / 0.95）、目标区扇形、当前运行点（带标注 P/Q）。
- 降级：无成对 P-Q 历史时 `history` 为空，只画当前运行点 + 目标区 + 等值线，不画轨迹；`p` 或 `q` 缺失时整卡显示「等待实时遥测」空状态。

### `CompensationHealthCard.vue`
- Props：`model: CompensationHealthModel`（见数据层）。
- 内容：总分（0–100）+ 状态评级文字 + 6 维条形图。
- 每维颜色按阈值：≥90 绿 / ≥70 青 / ≥50 琥珀 / <50 红。
- 降级：某维数据缺失时该维显示「待采集」、不计入总分；全部缺失时整卡显示空状态。

### `CompensationBankTopology.vue`
- Props：`telemetry: CompensationCapacitorBankTelemetry | null`、`circuitProfile`（路数配置）。
- 内容：母线 + 引下线示意，按 A 相分补 / B 相分补 / C 相分补 / 公补 1-8 / 9-16 / 17-24 分 6 条母线；每条母线下每个回路一个色块（投入 / 切除 / 未配置）。
- 回路状态经现有 `circuitStateUtils.toBits()` 由 `circuit_state_phase_*` / `circuit_state_common_*` 8-bit mask 解码；路数经 `resolvedConfiguredCounts()` 由 `circuitProfile` 求得。
- 设计稿的「等待 / 故障」逐回路态在遥测中不存在 —— 降为每回路 投入 / 切除 / 未配置 三态；相级告警（`overvoltage_alarm_a/b/c`、`temp_alarm` 等）以相标签上的告警角标体现。
- 底部汇总条：投运路数 / 补偿容量 / 投运率（由 `moduleStatusModel` 与 profile 求得）。
- 点击任一回路 → `emit('pick', circuit)`，由 `CompensationRuntimeBoard` 持有选中态并渲染抽屉。

### `CompensationPhaseMatrix.vue`
- Props：`telemetry: CompensationCapacitorBankTelemetry | null`。
- 内容：表格，行为指标（相位/超前状态、电流幅值、V-THD、I-THD、柜内温度），列为 A 相 / B 相 / C 相 / 系统。
- 每个单元格语义着色（正常 / 异常 / 超限 / 无数据），由对应遥测字段与告警标志判定；「系统」列聚合三相最严重态。
- 降级：缺测字段单元格显示 `--` 并标无数据样式。

### `CompensationCircuitDrawer.vue`
- Props：`circuit`（被点击回路的相位 / 序号 / 容量 / 当前状态）、`canControl`。
- 内容：抽屉式右滑面板，分三段——当前参数（回路状态等可派生信息）、投切动作历史、操作按钮。
- 投切动作历史：后端无逐回路动作历史接口，渲染该设备与此回路相关的控制事件（从 `page.compensationEvents` 过滤），无则显示空状态「暂无该回路的投切记录」。
- 操作：「立即投入 / 立即切除」复用现有手动投切指令 `page.handleControlConsoleManualSwitchCommand`，按抽屉对应的相位/级数预填表单；`canControl` 为假时按钮置灰。

### `CompensationAlarmRail.vue`
- Props：`rows`（`page.alarms`）、`actionId`。
- 内容：设计稿样式的未处理告警列表（严重度色条 + 标题 + 描述 + 时间 + 分类标签），底部「查看全部」。
- emit `resolve` 复用 `page.handleResolveAlarm`。

### `CompensationParamSummary.vue`
- Props：控制参数键值对（目标 PF / 投切延时 / 灵敏度 / 过压欠压保护 / 温度阈值 / 谐波保护），来源于 `compensationCapacitorBankControlProfile`。
- 内容：设计稿样式的键值列表，「修改 →」入口跳转参数设置标签页（复用现有 `openParameterWorkbench`）。

远程控制复用现有 `ControlConsoleRemotePanel.vue`，仅在 `CompensationRuntimeBoard` 中以新卡片外壳包裹以适配底部行栅格，组件本身与 props 不变。

## 数据层

新增派生计算放在 `useCompensationMonitor.ts` 与 `viewMapping.ts`，不改动网络请求函数：

### 健康度模型
新增类型 `CompensationHealthModel { score: number; rating: string; ratingTone: CompensationTone; breakdown: Array<{ key: string; label: string; value: number | null }> }`（追加到 `components/compensation/types.ts`）。

新增 `buildCompensationHealthModel(...)`（`viewMapping.ts`），6 维各 0–100：

- **通讯链路**：由 `runtime_status.ingestion_status` 与实时数据新鲜度（`isRealtimeFresh`）映射。
- **电压谐波**：由 `voltage_thd_a/b/c` 相对门限（5%）映射，越接近/超门限分越低。
- **电流谐波**：由 `current_harmonic_a/b/c` 相对门限映射。
- **投切动作**：由相级告警标志（`overvoltage_alarm_*` 等）与回路故障迹象映射，无异常为满分。
- **温度**：由 `temperature` 相对温度阈值（55°C）映射。
- **电压稳定**：由 `realtime.voltage` 相对额定区间映射。

某维所需字段全缺 → 该维 `value: null`（视图显示「待采集」）；总分为非空维度的加权平均；全空时 `score` 为 `null`，整卡空状态。评级文字按总分分档（优秀 / 良好 / 关注 / 异常）。

### P-Q 当前点与轨迹
- 当前点：`p = realtime.flow_rate`，`q = realtime.reactive_power`。
- 轨迹：若遥测历史含成对有功/无功则映射为 `Array<[number, number]>`，否则为空数组。

`useCompensationMonitor` 暴露新的 computed：`compensationHealthModel`、`compensationPqPoint`、`compensationPqHistory`，并由 `useDeviceMonitorPage` 透传到 `DeviceMonitorPageModel`，供 `CompensationRuntimeBoard` 通过 `page` 读取。

## 响应式

- Hero 行 3 栏在窄屏（约 ≤1280px）降为 1 栏。
- 底部行 2 栏在窄屏降为 1 栏。
- 拓扑母线在窄屏减少每行回路块数或允许横向滚动。
- 回路抽屉在窄屏占满宽度。
- 侧栏告警列表内部可滚动，控制参数摘要固定高度。

## 测试

- 新建各组件的单元测试（`runtime/__tests__/`）：
  - `CompensationPfTrendCard`：sparkline 在数据 ≥2 点时渲染、<2 点时降级、Δ 计算。
  - `CompensationPqQuadrantCard`：当前点渲染、无轨迹时不画轨迹、P/Q 缺失空状态。
  - `CompensationHealthCard`：6 维渲染、缺测维「待采集」、全空空状态、阈值着色。
  - `CompensationBankTopology`：mask 解码为投/切/未配置、相级告警角标、汇总条数值、点击 emit `pick`。
  - `CompensationPhaseMatrix`：单元格语义着色、系统列聚合、缺测 `--`。
  - `CompensationCircuitDrawer`：参数段渲染、投切历史空状态、`canControl` 置灰、操作触发手动投切。
  - `CompensationAlarmRail` / `CompensationParamSummary`：列表渲染与 emit。
- 数据层：`viewMapping` 测试新增 `buildCompensationHealthModel` 用例（各维正常 / 缺测 / 全空）。
- `CompensationMonitorView` 既有测试更新：`runtime` 分支断言改为新组件，其它标签页断言不变。
- 不在范围：历史曲线 / 参数设置 / 事件记录标签页测试、`ControlConsoleRemotePanel` 测试。

## 清理清单

- `CompensationMonitorView.vue` 的 `runtime` 分支：移除 `CompensationRealtimeOverview` / `CompensationDetailPanel` / `ControlConsoleRemotePanel` 的直接堆叠，改为 `CompensationRuntimeBoard`（`ControlConsoleRemotePanel` 仍在 board 内部被引用）。
- `runtime` 分支不再使用的 import 一并移除。
- `CompensationRealtimeOverview` / `CompensationDetailPanel` 保留（非工作台分支仍引用）。
- 实施时确认：若 `runtime` 分支移除后某旧组件再无任何引用，再行删除并清理其测试。
