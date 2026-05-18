# 参数设置面板重设计

日期：2026-05-18
范围：电容补偿设备工作台「参数设置」标签页 UI 重设计

## 背景与问题

「参数设置」标签页当前由两个面板纵向堆叠组成：

- `ControlConsoleReadonlyParamsPanel.vue`（外层 `MonitorSectionPanel` 标题「参数管理」）：顶部 6 张只读参数卡片 + 容量展开详情 + 4 栏分组卡片。
- `ControlConsoleWritableParamsPanel.vue`（外层 `MonitorSectionPanel` 标题「参数修改」）：写入状态条 + 可写参数行网格，点击行打开写入弹窗。

存在三个核心问题：

1. **参数重复展示**：同一组参数（功率因数 / 延时 / 门限等）在「只读卡片」「分组卡片」「参数修改面板」中重复出现 2-3 次。例如「投入功率因数」同时是顶部卡片、投切策略分组的一行、参数修改面板的一行。
2. **容量展开详情可读性差**：A/B/C 相分补 + 公补 1-24 是密集的小格子网格，视觉嘈杂、难以快速扫读。
3. **信息层级与扫读性弱**：三大块纵向堆叠、缺乏主次，4 栏窄卡片让每行参数局促。

## 设计目标

- 每个参数在页面中只出现一次，彻底消除重复。
- 重设计容量展开详情，提升扫读性。
- 建立清晰的信息层级，提升整体扫读性。

非目标：不改动数据层（`viewMapping.ts`、`capacitorBankControlProfile.ts`、profile API）；不改动「远程控制」面板（`ControlConsoleRemotePanel.vue`）。

## 选定方案：分区长表

参数主体采用单列「分区长表」布局——每个参数分组是一个分区标题 + 一张全宽表格，列对齐以最大化扫读性。只读展示与参数修改合并为一个面板，每个参数仅一行，行尾「操作」列承载写入入口。

已评估并排除的替代方案：

- **分组卡片网格（保留 4 栏）**：改动最小，但 4 栏过窄，是当前局促感的根源。
- **主从布局（左导航 + 右明细）**：编辑体验好，但一次只显示一个分组，跨组扫读变差，与目标冲突。

## 组件结构

合并两个面板为单一组件 `ControlConsoleParametersPanel.vue`：

- 新建 `frontend/src/features/device-control/components/ControlConsoleParametersPanel.vue`。
- 删除 `ControlConsoleWritableParamsPanel.vue` 与 `ControlConsoleReadonlyParamsPanel.vue`。
- `ControlConsoleParameterSection.vue` 若重设计后无其他引用，一并删除（实施时确认引用情况）。
- 两个消费方由「两个 `MonitorSectionPanel`」改为「一个 `MonitorSectionPanel`，标题`参数设置`」：
  - `CompensationMonitorView.vue`（当前 201-223 行）。
  - `DeviceControlConsole.vue`（当前 171-186 行）。

新面板 Props（汇总现有两个面板的全部 props，类型不变）：

- `sectionView: ControlConsoleReadonlySectionView`
- `readonlySummaryView: ControlConsoleReadonlySummaryView`
- `writeSectionView: ControlConsoleWriteSectionView`
- `canWriteParameters: boolean`
- `editableParameterCards: Array<CapacitorBankControlParameterMeta & { currentValue: string }>`

Emit：`open-write-dialog(parameterKey: string)`。

数据层（`viewMapping.ts` 的 build 函数、profile 结构）不变。

## 面板布局

自上而下三段：

### 1. 统一头部条

一条 header 取代当前分散的状态信息：

- 左侧：快照状态徽标（最新参数 / 参数可能过期 / 暂无参数，来自 `sectionView.tags`）+ 快照时间 + 来源（来自 `readonlySummaryView.sourceMeta`）。
- 右侧：写入状态徽标（允许写入 / 禁止写入，来自 `writeSectionView`）+ 角色摘要（来自 `writeSectionView.roleSummaryText`）。
- 当 `writeSectionView.alert` 存在（如设备离线锁定写入入口）时，头部条下方一行以 inline alert 样式展示 `alert.message`。
- **删除当前顶部的 6 张只读参数卡片**——其内容是 summary 标记参数，与下方分区长表完全重复。

### 2. 参数分区长表

遍历 `readonlySummaryView.groupedParameters` 的 4 个分组（投切策略 / 回路配置 / 保护门限 / 通讯参数），每个分组渲染：

- 分区标题行：组名 + 「N 个参数」。
- 一张全宽表格，列为 **参数 | 当前值 | 操作**：
  - **参数**：`item.label`，hover 显示 `item.description`。
  - **当前值**：`item.currentValue`，高亮显示。
  - **操作**：根据该参数 key 是否在 `editableParameterCards` 中、以及 `canWriteParameters` 判定：
    - 可写参数 且 `canWriteParameters` 为真 → 「修改」按钮，点击 emit `open-write-dialog(key)`（沿用现有写入弹窗，含范围校验与二次确认）。
    - 可写参数 且 `canWriteParameters` 为假 → 「修改」按钮置灰，tooltip 显示禁止原因（`writeSectionView.alert.message` 或角色限制）。
    - 不在可写集合中的参数 → 弱化文字「写入待开通」。

不设「读写」列、不设「寄存器」列。

### 3. 容量展开详情

当 `sectionView.showCapacityExpansion` 为真时，作为独立分区放在 4 个参数分区之后，可折叠（默认展开）。`readonlySummaryView.capacityExpansionItems` 拆为两组渲染：

- **分相补偿**（A 相分补 / B 相分补 / C 相分补）：每相一行 = 相标签 + 各路容量 chip + 该相合计。
- **公共补偿**（公补 1-8 / 9-16 / 17-24 合并视为公补 1-24）：统一为一个密集均匀网格，每行 8 路，每格显示「N路 + 容量值」，并显示总容量。

每路标签沿用现有 `capacitySlotLabel` 逻辑（相位 → `A1`，区间 → `9路` 等）。

## 响应式

- 分区长表在窄屏下保持表格结构；列宽自适应，必要时「操作」列下移为行内堆叠。
- 容量网格在窄屏下减少每行路数。
- 头部条窄屏下左右两段纵向堆叠。

## 测试

- 新建 `ControlConsoleParametersPanel.test.ts`，覆盖：头部条状态展示、6 张旧卡片不再存在、4 个分区表格渲染、可写/锁定/待开通三种操作态、点击「修改」触发 `open-write-dialog`、容量展开两组渲染。
- 删除 `ControlConsoleReadonlyParamsPanel.test.ts`、`ControlConsoleWritableParamsPanel`（若有）对应测试。
- `viewMapping.test.ts` 数据层测试基本不变。
- `ControlConsoleRemotePanel.test.ts` 不在范围内。

## 清理清单

- 删除顶部 6 张只读参数卡片。
- 删除独立的「参数修改」`MonitorSectionPanel`。
- 删除 `ControlConsoleWritableParamsPanel.vue` 与 `ControlConsoleReadonlyParamsPanel.vue`。
- 确认并按需删除 `ControlConsoleParameterSection.vue`。
