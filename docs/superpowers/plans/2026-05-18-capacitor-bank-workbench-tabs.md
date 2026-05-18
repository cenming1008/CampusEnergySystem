# 电容补偿控制器工作台五 Tab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将电容补偿控制器监控页升级为五 Tab 工作台：运行监视、曲线分析、远程控制、参数设置、事件记录，并把现有控制台能力迁入同一设备页面。

**Architecture:** 前端只改 Vue 页面和组合式状态，不改后端接口。`useDeviceMonitorPage` 保持监控数据入口，同时接入 `useCapacitorBankControlConsole` 的控制数据和动作；`CompensationMonitorView.vue` 负责五 Tab 编排；新增轻量工作台 tab 类型和局部布局，复用现有监控/控制组件。旧 `/device-console/:id` 路由先保留兼容，但监控页不再跳转到它。

**Tech Stack:** Vue 3 `<script setup>`、TypeScript、Element Plus、Vitest、Vue Test Utils、vue-tsc。

**所有命令工作目录均为 `/Users/todo/CampusEnergySystem/frontend`。**

---

## 文件结构

- Modify: `frontend/src/features/device-monitor/composables/useDeviceMonitorPage.ts`
  - 增加 `compensationWorkbenchTab` 状态。
  - 在电容补偿控制器路径接入 `useCapacitorBankControlConsole`。
  - 暴露远程控制、参数设置、日志和写入弹窗所需字段与 handler。
- Modify: `frontend/src/features/device-monitor/components/compensation/types.ts`
  - 增加 `CompensationWorkbenchTab` 类型和 tab option 类型。
- Modify: `frontend/src/features/device-monitor/views/CompensationMonitorView.vue`
  - 从长页面改为五 Tab 工作台。
  - 移除跳转控制台入口，改为切换到 `远程控制` tab。
  - 复用现有监控组件和控制组件。
- Modify: `frontend/src/features/device-monitor/components/compensation/CompensationHeader.vue`
  - 将 console entry 支持改为通用 action label，不再固定“控制台”语义。
- Modify: `frontend/src/views/DeviceManager.vue`
  - 电容补偿控制器“控制台”入口改为进入 `/devices/:id/monitor?tab=remote-control`，保留一个入口体验。
- Modify: `frontend/src/views/__tests__/DeviceManager.test.ts`
- Modify: `frontend/src/features/device-monitor/components/compensation/__tests__/CompensationHeader.test.ts`
- Modify: `frontend/src/views/__tests__/DeviceMonitor.test.ts`
- Create: `frontend/src/features/device-monitor/views/__tests__/CompensationMonitorView.test.ts`

---

## Task 1: 锁定工作台 Tab 类型和头部入口语义

**Files:**
- Modify: `frontend/src/features/device-monitor/components/compensation/types.ts`
- Modify: `frontend/src/features/device-monitor/components/compensation/CompensationHeader.vue`
- Modify: `frontend/src/features/device-monitor/components/compensation/__tests__/CompensationHeader.test.ts`

- [ ] **Step 1: 更新头部测试，先让“控制台”旧语义失败**

修改 `frontend/src/features/device-monitor/components/compensation/__tests__/CompensationHeader.test.ts`：

```ts
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import CompensationHeader from '../CompensationHeader.vue'

const model = {
  title: '补偿控制器',
  serial: 'CAP-001',
  location: '配电房',
  deviceStatus: '离线',
  deviceStatusTone: 'danger' as const,
  tags: [{ label: '手动', tone: 'warning' as const }],
}

describe('CompensationHeader', () => {
  it('uses the provided workbench action label for the secondary entry', () => {
    const wrapper = mount(CompensationHeader, {
      props: {
        model,
        toggleActionLabel: '停用设备',
        toggleButtonType: 'danger',
        canControlDevices: true,
        showConsoleEntry: true,
        consoleEntryLabel: '远程控制',
      },
      global: {
        stubs: {
          'el-icon': { template: '<span class="icon-probe"><slot /></span>' },
          ArrowLeft: true,
          Refresh: true,
          SwitchButton: true,
          Setting: { template: '<i class="setting-icon-probe" />' },
        },
      },
    })

    const actionButton = wrapper.find('button[aria-label="远程控制"]')

    expect(actionButton.exists()).toBe(true)
    expect(actionButton.attributes('title')).toBe('远程控制')
    expect(actionButton.text()).toContain('远程控制')
    expect(actionButton.text()).not.toContain('控制台')
    expect(actionButton.find('.setting-icon-probe').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test:unit -- src/features/device-monitor/components/compensation/__tests__/CompensationHeader.test.ts`

Expected: FAIL，旧默认 label 或按钮查找不符合新断言。

- [ ] **Step 3: 增加 tab 类型**

在 `frontend/src/features/device-monitor/components/compensation/types.ts` 末尾追加：

```ts
export type CompensationWorkbenchTab =
  | 'runtime'
  | 'curves'
  | 'remote-control'
  | 'parameter-settings'
  | 'event-records'

export interface CompensationWorkbenchTabOption {
  label: string
  value: CompensationWorkbenchTab
  tone?: 'normal' | 'warning' | 'danger'
}
```

- [ ] **Step 4: 调整头部入口默认文案**

在 `frontend/src/features/device-monitor/components/compensation/CompensationHeader.vue` 中把 `consoleEntryLabel` 默认值改为更通用的文案：

```ts
consoleEntryLabel: {
  type: String,
  default: '远程控制',
},
```

模板结构保持不变，继续使用 `@open-console` 事件，避免扩大组件 API 改名范围。

- [ ] **Step 5: 运行测试确认通过**

Run: `npm run test:unit -- src/features/device-monitor/components/compensation/__tests__/CompensationHeader.test.ts`

Expected: PASS。

---

## Task 2: 在 page model 中加入五 Tab 状态和控制台数据

**Files:**
- Modify: `frontend/src/features/device-monitor/composables/useDeviceMonitorPage.ts`
- Modify: `frontend/src/features/device-control/useCapacitorBankControlConsole.ts`
- Test: `frontend/src/views/__tests__/DeviceMonitor.test.ts`

- [ ] **Step 1: 增加测试，断言 query tab 可进入远程控制**

在 `frontend/src/views/__tests__/DeviceMonitor.test.ts` 中新增用例，放在补偿设备相关 describe 内：

```ts
import { vi } from 'vitest'

it('opens capacitor-bank workbench on remote-control tab from query', async () => {
  routeParams.id = '8'
  routeQuery.tab = 'remote-control'
  mockOverview.archive = {
    id: 8,
    name: '无功补偿控制器',
    sn: 'CAP-001',
    device_type: 'compensation',
    device_subtype: 'capacitor_bank_controller',
    archive_status: 'active',
  }

  const wrapper = mountDeviceMonitor()
  await flushPromises()

  const page = wrapper.findComponent({ name: 'CompensationMonitorView' }).props('page') as {
    compensationWorkbenchTab: string
  }
  expect(page.compensationWorkbenchTab).toBe('remote-control')
})
```

如果当前测试文件没有 `routeQuery` mock，则先在已有 route mock 附近补：

```ts
const routeQuery: Record<string, string> = {}
vi.mock('vue-router', () => ({
  useRoute: () => ({ params: routeParams, query: routeQuery }),
  useRouter: () => ({ push: routerPushMock }),
}))
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test:unit -- src/views/__tests__/DeviceMonitor.test.ts`

Expected: FAIL，`compensationWorkbenchTab` 尚未暴露。

- [ ] **Step 3: 修改 `useDeviceMonitorPage.ts` 引入控制台组合式**

在 imports 中加入：

```ts
import { useCapacitorBankControlConsole } from '@/features/device-control/useCapacitorBankControlConsole'
import type { CompensationWorkbenchTab, CompensationWorkbenchTabOption } from '@/features/device-monitor/components/compensation/types'
```

在已有 `compensationTrendTab` 附近增加：

```ts
const compensationWorkbenchTabs: CompensationWorkbenchTabOption[] = [
  { label: '运行监视', value: 'runtime' },
  { label: '曲线分析', value: 'curves' },
  { label: '远程控制', value: 'remote-control', tone: 'danger' },
  { label: '参数设置', value: 'parameter-settings', tone: 'warning' },
  { label: '事件记录', value: 'event-records' },
]

function normalizeWorkbenchTab(value: unknown): CompensationWorkbenchTab {
  const raw = Array.isArray(value) ? value[0] : value
  if (raw === 'curves') return 'curves'
  if (raw === 'remote-control') return 'remote-control'
  if (raw === 'parameter-settings') return 'parameter-settings'
  if (raw === 'event-records') return 'event-records'
  return 'runtime'
}

const compensationWorkbenchTab = ref<CompensationWorkbenchTab>(
  normalizeWorkbenchTab(route.query.tab),
)
```

在权限计算后接入控制台组合式：

```ts
const capacitorBankControlConsole = useCapacitorBankControlConsole({
  deviceId,
  canManageDevices,
  canControlDevices,
  currentRole,
  isAdmin,
  enableLifecycle: false,
})
```

同时在 `frontend/src/features/device-control/useCapacitorBankControlConsole.ts` 的 input 类型中加入：

```ts
enableLifecycle?: boolean
```

调用 `useControlConsoleData` 时传入：

```ts
const data = useControlConsoleData({
  deviceId: input.deviceId,
  enableLifecycle: input.enableLifecycle,
})
```

- [ ] **Step 4: 给电容补偿控制器加载控制台数据**

在 `loadPage` 中已有：

```ts
if (compensation.compensationSubtype.value === 'capacitor_bank_controller') {
  extraTasks.push(compensation.loadCapBankTelemetry(), compensation.loadCapBankControlProfile())
  compensation.compensationSvgProfile.value = null
}
```

改为追加控制台加载：

```ts
if (compensation.compensationSubtype.value === 'capacitor_bank_controller') {
  extraTasks.push(
    compensation.loadCapBankTelemetry(),
    compensation.loadCapBankControlProfile(),
    capacitorBankControlConsole.loadPage(),
  )
  compensation.compensationSvgProfile.value = null
}
```

在 `refreshCompensationPanelData` 的电容控制器分支也追加：

```ts
tasks.push(capacitorBankControlConsole.loadPage())
```

- [ ] **Step 5: 暴露 page model 字段**

在 `return reactive({ ... })` 中加入：

```ts
compensationWorkbenchTabs,
compensationWorkbenchTab,
capacitorBankControlConsole,
```

并展开常用字段，避免模板里长链条过多：

```ts
controlConsoleLoadError: capacitorBankControlConsole.loadError,
controlConsoleProfileWarning: capacitorBankControlConsole.profileWarning,
controlConsoleWriteDialogVisible: capacitorBankControlConsole.writeDialogVisible,
controlConsoleControlProfile: capacitorBankControlConsole.controlProfile,
controlConsoleWriteForm: capacitorBankControlConsole.writeForm,
controlConsoleManualSwitchForm: capacitorBankControlConsole.manualSwitchForm,
controlConsoleWriteSubmitting: capacitorBankControlConsole.writeSubmitting,
controlConsoleToggleSubmitting: capacitorBankControlConsole.toggleSubmitting,
controlConsoleCurrentControlModeLabel: capacitorBankControlConsole.currentControlModeLabel,
controlConsoleCanRunManualSwitch: capacitorBankControlConsole.canRunManualSwitch,
controlConsoleManualSwitchDisabledReason: capacitorBankControlConsole.manualSwitchDisabledReason,
controlConsoleCanWriteParameters: capacitorBankControlConsole.canWriteParameters,
controlConsoleSelectedWriteMeta: capacitorBankControlConsole.selectedWriteMeta,
controlConsoleEditableParameterCards: capacitorBankControlConsole.editableParameterCards,
controlConsoleManualPhaseOptions: capacitorBankControlConsole.manualPhaseOptions,
controlConsoleManualSwitchActionOptions: capacitorBankControlConsole.manualSwitchActionOptions,
controlConsoleManualCommonGroupOptions: capacitorBankControlConsole.manualCommonGroupOptions,
controlConsoleActionCards: capacitorBankControlConsole.actionCards,
controlConsoleReadonlySectionView: capacitorBankControlConsole.readonlySectionView,
controlConsoleReadonlySummaryView: capacitorBankControlConsole.readonlySummaryView,
controlConsoleWriteSectionView: capacitorBankControlConsole.writeSectionView,
controlConsoleLogView: capacitorBankControlConsole.logView,
handleControlConsoleManualSwitchCommand: capacitorBankControlConsole.handleManualSwitchCommand,
openControlConsoleWriteDialog: capacitorBankControlConsole.openWriteDialog,
submitControlConsoleParameterWrite: capacitorBankControlConsole.submitParameterWrite,
handleControlConsoleActionCard: capacitorBankControlConsole.handleActionCard,
```

- [ ] **Step 6: 运行测试确认通过**

Run: `npm run test:unit -- src/views/__tests__/DeviceMonitor.test.ts`

Expected: PASS。

---

## Task 3: 让控制台组合式可嵌入监控页

**Files:**
- Modify: `frontend/src/features/device-control/useCapacitorBankControlConsole.ts`
- Modify: `frontend/src/features/device-control/useControlConsoleData.ts`
- Test: `frontend/src/features/device-control/__tests__/useControlConsoleData.test.ts`

- [ ] **Step 1: 增加测试，验证关闭生命周期时不自动加载**

在 `frontend/src/features/device-control/__tests__/useControlConsoleData.test.ts` 新增：

```ts
it('does not auto load when enableLifecycle is false', async () => {
  const scope = effectScope()
  const deviceId = ref(8)
  scope.run(() => useControlConsoleData({
    deviceId: computed(() => deviceId.value),
    enableLifecycle: false,
  }))
  await flushPromises()
  expect(getDeviceMonitorOverviewMock).not.toHaveBeenCalled()
  scope.stop()
})
```

- [ ] **Step 2: 运行测试确认现有行为**

Run: `npm run test:unit -- src/features/device-control/__tests__/useControlConsoleData.test.ts`

Expected: PASS 或 FAIL；若已经 PASS，说明 data 层已支持，本任务继续补外层组合式签名。

- [ ] **Step 3: 扩展 `useCapacitorBankControlConsole` 入参**

在 `frontend/src/features/device-control/useCapacitorBankControlConsole.ts` 的 input 类型中加入：

```ts
enableLifecycle?: boolean
```

调用 `useControlConsoleData` 时传入：

```ts
const data = useControlConsoleData({
  deviceId: input.deviceId,
  enableLifecycle: input.enableLifecycle,
})
```

- [ ] **Step 4: 确认 `DeviceControlConsole.vue` 不受影响**

不改 `frontend/src/views/DeviceControlConsole.vue` 的调用，默认 `enableLifecycle` 为空，仍自动加载和轮询。

- [ ] **Step 5: 运行控制台测试**

Run: `npm run test:unit -- src/features/device-control/__tests__/useControlConsoleData.test.ts src/views/__tests__/DeviceControlConsole.test.ts`

Expected: PASS。

---

## Task 4: 将 `CompensationMonitorView.vue` 改为五 Tab 工作台

**Files:**
- Modify: `frontend/src/features/device-monitor/views/CompensationMonitorView.vue`
- Test: `frontend/src/features/device-monitor/views/__tests__/CompensationMonitorView.test.ts`

- [ ] **Step 1: 创建视图测试，先失败**

创建 `frontend/src/features/device-monitor/views/__tests__/CompensationMonitorView.test.ts`：

```ts
import { describe, expect, it } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { reactive, ref } from 'vue'
import CompensationMonitorView from '../CompensationMonitorView.vue'

function createPage(overrides: Record<string, unknown> = {}) {
  return reactive({
    compensationWorkbenchTabs: [
      { label: '运行监视', value: 'runtime' },
      { label: '曲线分析', value: 'curves' },
      { label: '远程控制', value: 'remote-control', tone: 'danger' },
      { label: '参数设置', value: 'parameter-settings', tone: 'warning' },
      { label: '事件记录', value: 'event-records' },
    ],
    compensationWorkbenchTab: ref('runtime'),
    compensationSubtype: 'capacitor_bank_controller',
    isPendingArchiveDevice: false,
    canControlDevices: true,
    deviceId: 8,
    router: { push: vi.fn() },
    loadPage: vi.fn(),
    handleToggleDevice: vi.fn(),
    toggleActionLabel: '停用设备',
    toggleButtonType: 'danger',
    toggleSubmitting: false,
    compensationHeaderModel: {
      title: '无功补偿控制器',
      serial: 'CAP-001',
      location: '配电房',
      deviceStatus: '在线采集',
      deviceStatusTone: 'info',
      tags: [],
    },
    compensationCoreMetric: null,
    compensationPfMetric: null,
    compensationMetrics: [],
    compensationExtendedHint: '',
    compensationCapacitorBankTelemetry: null,
    compensationPowerFactorTrend: [],
    compensationStatusText: '正常补偿',
    compensationStatusTone: 'success',
    compensationAlarmCountMetrics: [],
    isSvgDevice: false,
    compensationDetailTab: ref('circuit'),
    compensationSvgTelemetry: null,
    compensationCircuitProfile: null,
    moduleStatusModel: null,
    compensationMeasurementMetrics: [],
    compensationCapacitorBankControlProfile: null,
    compensationTrendTab: ref('effect'),
    timeRange: ref('6h'),
    compensationTrendTabs: [],
    compensationTrendModel: null,
    timeShortcuts: [],
    chartLoading: false,
    handleRangeChange: vi.fn(),
    alarms: [],
    alarmActionId: null,
    handleResolveAlarm: vi.fn(),
    compensationEvents: [],
    capacitorBankControlSummaryView: { summaryItems: [], capacityExpansionItems: [], hasSummaryData: false },
    compensationProfileItems: [],
    templateDiagnostics: null,
    svgProfileEditVisible: false,
    loadSVGProfile: vi.fn(),
    controlConsoleLoadError: '',
    controlConsoleProfileWarning: '',
    controlConsoleActionCards: [],
    controlConsoleToggleSubmitting: false,
    controlConsoleCurrentControlModeLabel: '自动',
    controlConsoleCanRunManualSwitch: true,
    controlConsoleManualSwitchDisabledReason: '',
    controlConsoleManualPhaseOptions: [],
    controlConsoleManualSwitchActionOptions: [],
    controlConsoleManualCommonGroupOptions: [],
    controlConsoleManualSwitchForm: { phase: 'A', switch_action: 'switch_on', group: 1 },
    handleControlConsoleActionCard: vi.fn(),
    handleControlConsoleManualSwitchCommand: vi.fn(),
    controlConsoleReadonlySectionView: { groups: [] },
    controlConsoleReadonlySummaryView: { items: [], capacityExpansionItems: [], groupedParameters: [] },
    controlConsoleWriteSectionView: { groups: [], disabledReason: '', riskNotice: '' },
    controlConsoleCanWriteParameters: true,
    controlConsoleEditableParameterCards: [],
    openControlConsoleWriteDialog: vi.fn(),
    controlConsoleLogView: { entries: [] },
    controlConsoleWriteDialogVisible: false,
    controlConsoleSelectedWriteMeta: null,
    controlConsoleControlProfile: null,
    controlConsoleWriteForm: { target_value: '', reason: '' },
    controlConsoleWriteSubmitting: false,
    submitControlConsoleParameterWrite: vi.fn(),
    ...overrides,
  })
}

const stubs = {
  MonitorViewShell: { template: '<section><slot name="header" /><slot name="main" /><slot name="side" /></section>' },
  CompensationHeader: { template: '<header><button class="secondary" @click="$emit(\'open-console\')">远程控制</button></header>' },
  CompensationRealtimeOverview: { template: '<div class="runtime-probe">runtime</div>' },
  CompensationDetailPanel: { template: '<div class="detail-probe">detail</div>' },
  CompensationTrendPanel: { template: '<div class="trend-probe">trend</div>' },
  HarmonicSpectrumPanel: { template: '<div class="harmonic-probe">harmonic</div>' },
  ControlConsoleRemotePanel: { template: '<div class="remote-probe">remote</div>' },
  ControlConsoleReadonlyParamsPanel: { template: '<div class="readonly-probe">readonly</div>' },
  ControlConsoleWritableParamsPanel: { template: '<div class="writable-probe">writable</div>' },
  ControlConsoleLogPanel: { template: '<div class="log-probe">logs</div>' },
  ControlConsoleWriteDialog: { template: '<div />' },
}

describe('CompensationMonitorView workbench', () => {
  it('renders the five workbench tabs', () => {
    const wrapper = shallowMount(CompensationMonitorView, { props: { page: createPage() }, global: { stubs } })
    expect(wrapper.text()).toContain('运行监视')
    expect(wrapper.text()).toContain('曲线分析')
    expect(wrapper.text()).toContain('远程控制')
    expect(wrapper.text()).toContain('参数设置')
    expect(wrapper.text()).toContain('事件记录')
  })

  it('switches header secondary action to remote-control tab', async () => {
    const page = createPage()
    const wrapper = shallowMount(CompensationMonitorView, { props: { page }, global: { stubs } })
    await wrapper.find('.secondary').trigger('click')
    expect(page.compensationWorkbenchTab).toBe('remote-control')
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test:unit -- src/features/device-monitor/views/__tests__/CompensationMonitorView.test.ts`

Expected: FAIL，视图尚未渲染五个 tab。

- [ ] **Step 3: 添加控制台组件 imports**

在 `CompensationMonitorView.vue` 增加：

```ts
import ControlConsoleRemotePanel from '@/features/device-control/components/ControlConsoleRemotePanel.vue'
import ControlConsoleLogPanel from '@/features/device-control/components/ControlConsoleLogPanel.vue'
import ControlConsoleReadonlyParamsPanel from '@/features/device-control/components/ControlConsoleReadonlyParamsPanel.vue'
import ControlConsoleWritableParamsPanel from '@/features/device-control/components/ControlConsoleWritableParamsPanel.vue'
import ControlConsoleWriteDialog from '@/features/device-control/components/ControlConsoleWriteDialog.vue'
import MonitorInlineAlert from '@/shared/components/MonitorInlineAlert.vue'
import MonitorSectionPanel from '@/shared/components/MonitorSectionPanel.vue'
```

- [ ] **Step 4: 替换 header 的控制台跳转**

把原来的：

```vue
@open-console="page.router.push(`/device-console/${page.deviceId}`)"
```

改为：

```vue
console-entry-label="远程控制"
@open-console="page.compensationWorkbenchTab = 'remote-control'"
```

控制摘要面板的 `@open-console` 也改为：

```vue
@open-console="page.compensationWorkbenchTab = 'parameter-settings'"
```

- [ ] **Step 5: 添加五 Tab 导航模板**

在 `<template #main>` 顶部加入：

```vue
<div
  v-if="page.compensationSubtype === 'capacitor_bank_controller'"
  class="comp-workbench-tabs"
>
  <button
    v-for="tab in page.compensationWorkbenchTabs"
    :key="tab.value"
    type="button"
    class="comp-workbench-tabs__item"
    :class="[
      `comp-workbench-tabs__item--${tab.tone || 'normal'}`,
      { 'is-active': page.compensationWorkbenchTab === tab.value },
    ]"
    @click="page.compensationWorkbenchTab = tab.value"
  >
    {{ tab.label }}
  </button>
</div>
```

- [ ] **Step 6: 拆分五个内容区**

将原主区内容改为按 tab 显示：

```vue
<section
  v-if="page.compensationWorkbenchTab === 'runtime'"
  class="comp-workbench-page comp-workbench-page--runtime"
>
  <CompensationRealtimeOverview ... />
  <CompensationDetailPanel ... />
</section>

<section
  v-else-if="page.compensationWorkbenchTab === 'curves'"
  class="comp-workbench-page comp-workbench-page--curves"
>
  <CompensationTrendPanel ... />
  <HarmonicSpectrumPanel ... />
</section>

<section
  v-else-if="page.compensationWorkbenchTab === 'remote-control'"
  class="comp-workbench-page comp-workbench-page--remote"
>
  <MonitorInlineAlert
    v-if="page.controlConsoleLoadError"
    title="远程控制暂不可用"
    :message="page.controlConsoleLoadError"
    tone="danger"
  />
  <ControlConsoleRemotePanel
    v-else
    :action-cards="page.controlConsoleActionCards"
    :toggle-submitting="page.controlConsoleToggleSubmitting"
    :current-control-mode-label="page.controlConsoleCurrentControlModeLabel"
    :can-run-manual-switch="page.controlConsoleCanRunManualSwitch"
    :manual-switch-disabled-reason="page.controlConsoleManualSwitchDisabledReason"
    :manual-phase-options="page.controlConsoleManualPhaseOptions"
    :manual-switch-action-options="page.controlConsoleManualSwitchActionOptions"
    :manual-common-group-options="page.controlConsoleManualCommonGroupOptions"
    :manual-phase="page.controlConsoleManualSwitchForm.phase"
    :manual-switch-action="page.controlConsoleManualSwitchForm.switch_action"
    :manual-common-group="page.controlConsoleManualSwitchForm.group"
    @action-card="page.handleControlConsoleActionCard"
    @update:manual-phase="page.controlConsoleManualSwitchForm.phase = $event"
    @update:manual-switch-action="page.controlConsoleManualSwitchForm.switch_action = $event"
    @update:manual-common-group="page.controlConsoleManualSwitchForm.group = $event"
    @manual-switch="page.handleControlConsoleManualSwitchCommand"
  />
</section>

<section
  v-else-if="page.compensationWorkbenchTab === 'parameter-settings'"
  class="comp-workbench-page comp-workbench-page--params"
>
  <MonitorInlineAlert
    v-if="page.controlConsoleProfileWarning"
    title="参数档案暂时不可用"
    :message="page.controlConsoleProfileWarning"
    tone="warning"
  />
  <MonitorSectionPanel shell="console" accent="teal" title="参数总览">
    <ControlConsoleReadonlyParamsPanel
      :section-view="page.controlConsoleReadonlySectionView"
      :readonly-summary-view="page.controlConsoleReadonlySummaryView"
    />
  </MonitorSectionPanel>
  <MonitorSectionPanel shell="console" accent="amber" title="参数修改">
    <ControlConsoleWritableParamsPanel
      :write-section-view="page.controlConsoleWriteSectionView"
      :can-write-parameters="page.controlConsoleCanWriteParameters"
      :editable-parameter-cards="page.controlConsoleEditableParameterCards"
      @open-write-dialog="page.openControlConsoleWriteDialog"
    />
  </MonitorSectionPanel>
</section>

<section
  v-else
  class="comp-workbench-page comp-workbench-page--events"
>
  <CompensationAlarmTable ... />
  <ControlConsoleLogPanel :log-view="page.controlConsoleLogView" />
</section>
```

保留原 SVG 补偿设备路径：当 `page.compensationSubtype !== 'capacitor_bank_controller'` 时，继续渲染原有顺序。

- [ ] **Step 7: 添加写入弹窗**

在 `CompensationSvgProfileEditDialog` 前加入：

```vue
<ControlConsoleWriteDialog
  v-if="page.compensationSubtype === 'capacitor_bank_controller'"
  v-model="page.controlConsoleWriteDialogVisible"
  :selected-write-meta="page.controlConsoleSelectedWriteMeta"
  :control-profile="page.controlConsoleControlProfile"
  :target-value="page.controlConsoleWriteForm.target_value"
  :reason="page.controlConsoleWriteForm.reason"
  :write-submitting="page.controlConsoleWriteSubmitting"
  @update:target-value="page.controlConsoleWriteForm.target_value = $event"
  @update:reason="page.controlConsoleWriteForm.reason = $event"
  @submit="page.submitControlConsoleParameterWrite"
/>
```

- [ ] **Step 8: 添加基础样式**

在 `<style scoped>` 中加入：

```css
.comp-workbench-tabs {
  display: flex;
  gap: 8px;
  padding: 8px;
  border: 1px solid rgba(58, 76, 102, 0.88);
  border-radius: 10px;
  background: rgba(8, 15, 26, 0.88);
  overflow-x: auto;
}

.comp-workbench-tabs__item {
  flex: 0 0 auto;
  min-width: 92px;
  height: 36px;
  border: 1px solid transparent;
  border-radius: 7px;
  background: rgba(30, 41, 59, 0.86);
  color: #cbd5e1;
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}

.comp-workbench-tabs__item.is-active {
  background: rgba(37, 99, 235, 0.9);
  border-color: rgba(147, 197, 253, 0.45);
  color: #fff;
}

.comp-workbench-tabs__item--danger.is-active {
  background: rgba(124, 45, 18, 0.95);
  border-color: rgba(251, 146, 60, 0.45);
}

.comp-workbench-tabs__item--warning.is-active {
  background: rgba(120, 53, 15, 0.95);
  border-color: rgba(251, 191, 36, 0.45);
}

.comp-workbench-page {
  display: grid;
  gap: 16px;
  min-height: 0;
}

.comp-workbench-page--runtime {
  grid-template-columns: minmax(0, 1.35fr) minmax(380px, 0.9fr);
}

.comp-workbench-page--curves,
.comp-workbench-page--params,
.comp-workbench-page--events {
  grid-template-columns: minmax(0, 1fr);
}
```

- [ ] **Step 9: 运行视图测试确认通过**

Run: `npm run test:unit -- src/features/device-monitor/views/__tests__/CompensationMonitorView.test.ts`

Expected: PASS。

---

## Task 5: 设备台账入口改为同页 Tab

**Files:**
- Modify: `frontend/src/views/DeviceManager.vue`
- Modify: `frontend/src/views/__tests__/DeviceManager.test.ts`

- [ ] **Step 1: 更新测试，先失败**

把 `frontend/src/views/__tests__/DeviceManager.test.ts` 中：

```ts
expect(routerPushMock).toHaveBeenCalledWith('/device-console/16')
```

改为：

```ts
expect(routerPushMock).toHaveBeenCalledWith('/devices/16/monitor?tab=remote-control')
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test:unit -- src/views/__tests__/DeviceManager.test.ts`

Expected: FAIL，当前仍跳转 `/device-console/16`。

- [ ] **Step 3: 修改跳转**

在 `frontend/src/views/DeviceManager.vue` 中找到控制台跳转函数，将：

```ts
router.push(`/device-console/${row.id}`)
```

改为：

```ts
router.push(`/devices/${row.id}/monitor?tab=remote-control`)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test:unit -- src/views/__tests__/DeviceManager.test.ts`

Expected: PASS。

---

## Task 6: 回归测试和类型检查

**Files:**
- No source changes unless verification reveals a specific failure.

- [ ] **Step 1: 跑补偿监控相关测试**

Run:

```bash
npm run test:unit -- src/features/device-monitor/views/__tests__/CompensationMonitorView.test.ts src/views/__tests__/DeviceMonitor.test.ts src/features/device-monitor/components/compensation/__tests__/CompensationHeader.test.ts
```

Expected: PASS。

- [ ] **Step 2: 跑控制台相关测试**

Run:

```bash
npm run test:unit -- src/views/__tests__/DeviceControlConsole.test.ts src/features/device-control/__tests__/useControlConsoleData.test.ts src/features/device-control/__tests__/useControlConsoleActions.test.ts src/features/device-control/__tests__/viewMapping.test.ts
```

Expected: PASS。

- [ ] **Step 3: 跑类型检查**

Run:

```bash
npm run typecheck
```

Expected: PASS。

- [ ] **Step 4: 如有本地服务，做浏览器验收**

Run:

```bash
npm run dev
```

打开电容补偿控制器监控页，检查：

- 顶部存在 `运行监视 / 曲线分析 / 远程控制 / 参数设置 / 事件记录`。
- 点击 `远程控制` 后显示远程控制面板，不跳转 `/device-console/:id`。
- 点击 `参数设置` 后显示只读参数、可写参数和写入弹窗入口。
- 点击 `事件记录` 后看到告警表、控制日志、接入诊断相关信息。
- 页面主体没有明显长页面滚动，长表格/日志在组件内部滚动。

- [ ] **Step 5: 提交实现**

```bash
git add frontend/src/features/device-monitor frontend/src/features/device-control frontend/src/views
git commit -m "feat(monitor): 合并电容补偿控制器五 tab 工作台"
```

---

## 自查

- Spec 覆盖：五个一级 tab、监控/控制同页、远程控制与参数设置分离、曲线分析局部切换、事件记录集中承载、权限/确认保留均有任务覆盖。
- 非目标：未要求后端、MQTT、数据库和控制语义变更。
- 风险：`CompensationMonitorView.vue` 可能在 Task 4 变大；实现时若模板明显过长，应在同目录拆出轻量子组件，但不要改变本计划的五 Tab 边界。
