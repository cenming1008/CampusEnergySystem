# 无功功率控制器监控页排版优化 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按运维巡检优先级重排无功功率补偿控制器监控页，告警面板上移、接入诊断降级折叠、回路状态前移，并为次要面板引入折叠收纳能力。

**Architecture:** 改动集中在前端 `frontend/` 的补偿监控视图与面板组件层。容器排版调整在 `CompensationMonitorView.vue`；折叠能力由一个共享组合式 `usePanelCollapse` + 一个共享按钮组件 `PanelCollapseToggle` 提供，各目标面板自管 `collapsed` 状态并按 `localStorage` 持久化；接入诊断用补偿页局部包装组件折叠，不改共享组件本身。后端、API、数据模型不动。

**Tech Stack:** Vue 3 (`<script setup>`)、TypeScript、Element Plus、ECharts、Vitest、vue-tsc。

**所有命令的工作目录为 `frontend/`（即 `/Users/todo/CampusEnergySystem/frontend`）。**

---

## 设计要点速查

主区面板顺序（上→下）：实时概览 → 实时详查 → 历史趋势 → 高次谐波频谱 → 告警记录表。
右栏面板顺序（上→下）：运行事件 → 运行状态 → 控制参数摘要 → 设备档案 → 接入诊断。

折叠默认态与 `localStorage` key：

| 面板 | 组件 | storage key | 默认 |
|---|---|---|---|
| 历史趋势 | `CompensationTrendPanel` | `compensation-monitor:collapse:trend` | 展开 |
| 高次谐波频谱 | `HarmonicSpectrumPanel` | `compensation-monitor:collapse:harmonic` | 折叠 |
| 实时详查 | `CompensationDetailPanel` | `compensation-monitor:collapse:detail` | 展开 |
| 控制参数摘要 | `CompensationControlSummaryPanel` | `compensation-monitor:collapse:control-summary` | 展开 |
| 设备档案 | `CompensationDeviceProfile` | `compensation-monitor:collapse:device-profile` | 折叠 |
| 接入诊断 | `CompensationDiagnosticsCollapsible`（新） | `compensation-monitor:collapse:diagnostics` | 折叠 |

---

## Task 1: 折叠组合式 usePanelCollapse

**Files:**
- Create: `frontend/src/shared/composables/usePanelCollapse.ts`
- Test: `frontend/src/shared/composables/__tests__/usePanelCollapse.test.ts`

- [ ] **Step 1: 写失败测试**

创建 `frontend/src/shared/composables/__tests__/usePanelCollapse.test.ts`：

```ts
import { describe, expect, it, beforeEach } from 'vitest'
import { nextTick } from 'vue'
import { usePanelCollapse } from '../usePanelCollapse'

describe('usePanelCollapse', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('无存储记录时取默认值', () => {
    expect(usePanelCollapse('k:a', true).collapsed.value).toBe(true)
    expect(usePanelCollapse('k:b', false).collapsed.value).toBe(false)
  })

  it('读取已存储的折叠状态，覆盖默认值', () => {
    localStorage.setItem('k:c', '1')
    expect(usePanelCollapse('k:c', false).collapsed.value).toBe(true)
    localStorage.setItem('k:d', '0')
    expect(usePanelCollapse('k:d', true).collapsed.value).toBe(false)
  })

  it('toggle 翻转状态并写入 localStorage', async () => {
    const panel = usePanelCollapse('k:e', false)
    panel.toggle()
    await nextTick()
    expect(panel.collapsed.value).toBe(true)
    expect(localStorage.getItem('k:e')).toBe('1')
    panel.toggle()
    await nextTick()
    expect(localStorage.getItem('k:e')).toBe('0')
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test:unit -- src/shared/composables/__tests__/usePanelCollapse.test.ts`
Expected: FAIL，提示无法解析 `../usePanelCollapse`。

- [ ] **Step 3: 实现 usePanelCollapse**

创建 `frontend/src/shared/composables/usePanelCollapse.ts`：

```ts
import { ref, watch } from 'vue'

export function usePanelCollapse(storageKey: string, defaultCollapsed = false) {
  const collapsed = ref(readInitial())

  function readInitial(): boolean {
    try {
      const raw = localStorage.getItem(storageKey)
      if (raw === '1') return true
      if (raw === '0') return false
    } catch {
      // localStorage 不可用（隐私模式等）时回退默认值
    }
    return defaultCollapsed
  }

  watch(collapsed, (value) => {
    try {
      localStorage.setItem(storageKey, value ? '1' : '0')
    } catch {
      // 忽略写入失败
    }
  })

  function toggle() {
    collapsed.value = !collapsed.value
  }

  return { collapsed, toggle }
}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test:unit -- src/shared/composables/__tests__/usePanelCollapse.test.ts`
Expected: PASS，3 个用例全通过。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/shared/composables/usePanelCollapse.ts frontend/src/shared/composables/__tests__/usePanelCollapse.test.ts
git commit -m "feat(monitor): 新增面板折叠组合式 usePanelCollapse"
```

---

## Task 2: 折叠按钮组件 PanelCollapseToggle

**Files:**
- Create: `frontend/src/shared/components/PanelCollapseToggle.vue`
- Test: `frontend/src/shared/components/__tests__/PanelCollapseToggle.test.ts`

- [ ] **Step 1: 写失败测试**

创建 `frontend/src/shared/components/__tests__/PanelCollapseToggle.test.ts`：

```ts
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import PanelCollapseToggle from '../PanelCollapseToggle.vue'

describe('PanelCollapseToggle', () => {
  it('点击时派发 toggle 事件', async () => {
    const wrapper = mount(PanelCollapseToggle, {
      props: { collapsed: false },
      global: { stubs: { 'el-icon': { template: '<i><slot /></i>' } } },
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('toggle')).toHaveLength(1)
  })

  it('折叠态 aria-expanded 为 false，展开态为 true', () => {
    const collapsedWrapper = mount(PanelCollapseToggle, {
      props: { collapsed: true },
      global: { stubs: { 'el-icon': { template: '<i><slot /></i>' } } },
    })
    expect(collapsedWrapper.find('button').attributes('aria-expanded')).toBe('false')

    const expandedWrapper = mount(PanelCollapseToggle, {
      props: { collapsed: false },
      global: { stubs: { 'el-icon': { template: '<i><slot /></i>' } } },
    })
    expect(expandedWrapper.find('button').attributes('aria-expanded')).toBe('true')
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test:unit -- src/shared/components/__tests__/PanelCollapseToggle.test.ts`
Expected: FAIL，提示无法解析 `../PanelCollapseToggle.vue`。

- [ ] **Step 3: 实现 PanelCollapseToggle.vue**

创建 `frontend/src/shared/components/PanelCollapseToggle.vue`：

```vue
<script setup lang="ts">
import { ArrowDownBold, ArrowUpBold } from '@element-plus/icons-vue'

defineProps<{ collapsed: boolean }>()
defineEmits<{ (e: 'toggle'): void }>()
</script>

<template>
  <button
    type="button"
    class="panel-collapse-toggle"
    :aria-expanded="collapsed ? 'false' : 'true'"
    :title="collapsed ? '展开' : '收起'"
    @click="$emit('toggle')"
  >
    <el-icon>
      <component :is="collapsed ? ArrowDownBold : ArrowUpBold" />
    </el-icon>
  </button>
</template>

<style scoped>
.panel-collapse-toggle {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  padding: 0;
  border: 1px solid rgba(72, 96, 130, 0.6);
  border-radius: 7px;
  background: rgba(7, 15, 26, 0.6);
  color: #9fb1ca;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s, background 0.15s;
}

.panel-collapse-toggle:hover {
  color: #dbeafe;
  border-color: rgba(96, 165, 250, 0.55);
  background: rgba(96, 165, 250, 0.12);
}
</style>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test:unit -- src/shared/components/__tests__/PanelCollapseToggle.test.ts`
Expected: PASS，2 个用例全通过。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/shared/components/PanelCollapseToggle.vue frontend/src/shared/components/__tests__/PanelCollapseToggle.test.ts
git commit -m "feat(monitor): 新增面板折叠按钮 PanelCollapseToggle"
```

---

## Task 3: 6 指标条补入「电网频率」

`buildCompensationOverviewMetrics` 当前产出的 `metrics` 数组里含 `capacityUsage`（标签「回路投入率」）。该指标值同时被 `CompensationRealtimeOverview` 的 Hero 进度条复用，因此**保留它在数组中**，仅在指标条渲染时过滤掉它，并新增 `gridFrequency` 指标补满 6 格。

**Files:**
- Modify: `frontend/src/features/device-monitor/components/compensation/viewMapping.ts`
- Modify: `frontend/src/features/device-monitor/composables/useCompensationMonitor.ts`
- Modify: `frontend/src/features/device-monitor/components/compensation/CompensationRealtimeOverview.vue`
- Test: `frontend/src/features/device-monitor/components/compensation/__tests__/viewMapping.test.ts`

- [ ] **Step 1: 改测试，加电网频率断言（先失败）**

在 `viewMapping.test.ts` 的用例 `builds overview metrics with formatted capacity usage and temperature tone`（约 222 行）中，给 `buildCompensationOverviewMetrics({...})` 的入参对象**追加两个字段**（放在 `cabinetTemperatureHealthTone: 'danger',` 之后）：

```ts
      gridFrequencyValue: '50.02',
      gridFrequencyMissing: false,
```

并在该用例的断言区（`expect(overview.metrics.find(...capacityUsage...))` 那几行之后）追加：

```ts
    expect(overview.metrics.find((item) => item.key === 'gridFrequency')?.value).toBe('50.02')
    expect(overview.metrics.find((item) => item.key === 'gridFrequency')?.label).toBe('电网频率')
    expect(overview.metrics.find((item) => item.key === 'gridFrequency')?.unit).toBe('Hz')
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test:unit -- src/features/device-monitor/components/compensation/__tests__/viewMapping.test.ts`
Expected: FAIL — TS 报 `buildCompensationOverviewMetrics` 入参缺少类型字段 / `gridFrequency` 指标未找到。

- [ ] **Step 3: 给 viewMapping.ts 的入参类型加字段**

在 `viewMapping.ts` 中找到 `buildCompensationOverviewMetrics` 用的入参 interface（即第 126 行附近、含 `capacityUsageValue: number` / `controlMode: string` / `cabinetTemperature...` 的 `CompensationOverviewMetricsInput`）。在该 interface 内、`cabinetTemperature` 相关字段之后追加：

```ts
  gridFrequencyValue: string
  gridFrequencyMissing: boolean
```

- [ ] **Step 4: 在 metrics 数组插入 gridFrequency 指标**

在 `viewMapping.ts` 的 `buildCompensationOverviewMetrics` 函数里，`metrics` 数组中 `key: 'capacityUsage'` 那个对象**之后、`key: 'controlMode'` 对象之前**，插入：

```ts
      {
        key: 'gridFrequency',
        label: '电网频率',
        value: input.gridFrequencyValue,
        unit: 'Hz',
        hint: input.gridFrequencyMissing ? '电网频率未采集' : '当前电网频率测量值',
        state: input.gridFrequencyMissing ? 'missing' : 'live',
      },
```

- [ ] **Step 5: 运行测试确认通过**

Run: `npm run test:unit -- src/features/device-monitor/components/compensation/__tests__/viewMapping.test.ts`
Expected: PASS。

- [ ] **Step 6: 在 useCompensationMonitor 接入电网频率数据**

在 `useCompensationMonitor.ts` 中，`compensationOverviewView` 这个 `computed`（约 272 行）之前，新增电网频率取值（SVG 与电容设备的遥测对象都有 `frequency` 字段）：

```ts
  const gridFrequencyTelemetryValue = computed<number | null | undefined>(() =>
    isSvgDevice.value
      ? compensationSvgTelemetry.value?.frequency
      : compensationCapacitorBankTelemetry.value?.frequency,
  )
```

然后在 `compensationOverviewView` 的 `buildCompensationOverviewMetrics({...})` 入参对象末尾（`cabinetTemperatureHealthTone: ...,` 之后）追加：

```ts
      gridFrequencyValue: displayValueWithState(gridFrequencyTelemetryValue.value, '暂无数据', 2),
      gridFrequencyMissing: gridFrequencyTelemetryValue.value == null,
```

- [ ] **Step 7: 指标条渲染过滤 capacityUsage**

在 `CompensationRealtimeOverview.vue` 的 `<script setup>` 中，`isWaitingForTelemetry` 这个 `computed` 之后，新增：

```ts
const stripMetrics = computed(() =>
  props.metrics.filter((item) => item.key !== 'capacityUsage'),
)
```

把模板里指标条的 `v-for`（`<div v-for="item in metrics"` 那行，约 185 行）改为：

```html
      <div
        v-for="item in stripMetrics"
        :key="item.key"
```

（`capacityUsagePct` / `capacityUsageLabel` 仍按 `props.metrics.find(...capacityUsage...)` 取值，不要改动——Hero 进度条依赖它。）

- [ ] **Step 8: 类型检查 + 跑相关测试**

Run: `npm run typecheck`
Expected: 无新增报错。

Run: `npm run test:unit -- src/features/device-monitor/components/compensation/__tests__/viewMapping.test.ts src/features/device-monitor/components/compensation/__tests__/CompensationRealtimeOverview.test.ts`
Expected: PASS。

- [ ] **Step 9: 提交**

```bash
git add frontend/src/features/device-monitor/components/compensation/viewMapping.ts frontend/src/features/device-monitor/composables/useCompensationMonitor.ts frontend/src/features/device-monitor/components/compensation/CompensationRealtimeOverview.vue frontend/src/features/device-monitor/components/compensation/__tests__/viewMapping.test.ts
git commit -m "feat(monitor): 指标条以电网频率替换重复的回路投入率"
```

---

## Task 4: 历史趋势面板接入折叠

**Files:**
- Modify: `frontend/src/features/device-monitor/components/compensation/CompensationTrendPanel.vue`

- [ ] **Step 1: 引入折叠能力**

在 `CompensationTrendPanel.vue` 的 `<script setup>` 顶部 import 区追加：

```ts
import { usePanelCollapse } from '@/shared/composables/usePanelCollapse'
import PanelCollapseToggle from '@/shared/components/PanelCollapseToggle.vue'
```

在 `<script setup>` 内、`const chart = useECharts()` 之后追加：

```ts
const { collapsed, toggle } = usePanelCollapse('compensation-monitor:collapse:trend', false)
```

- [ ] **Step 2: 头部加折叠按钮，正文按折叠态隐藏**

把模板里的 `.trend-panel__intro` 块改为（标题与按钮同一行）：

```html
      <div class="trend-panel__intro">
        <div class="panel-title-row">
          <h3>历史趋势</h3>
          <PanelCollapseToggle :collapsed="collapsed" @toggle="toggle" />
        </div>
        <span v-if="model.hint">{{ model.hint }}</span>
      </div>
```

给 `.trend-panel__toolbar` 那个 `<div>` 加 `v-show="!collapsed"`：

```html
      <div
        v-show="!collapsed"
        class="trend-panel__toolbar"
      >
```

给 `.trend-panel__summary`、`.trend-panel__legend`、`.trend-panel__chart` 三个块都加 `v-show="!collapsed"`（`.trend-panel__legend` 已有 `v-if="model.legend.length"`，改为同时保留 `v-if` 并加 `v-show="!collapsed"`）。

- [ ] **Step 3: 加标题行样式**

在 `<style scoped>` 末尾追加：

```css
.panel-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
```

- [ ] **Step 4: 类型检查**

Run: `npm run typecheck`
Expected: 无新增报错。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/features/device-monitor/components/compensation/CompensationTrendPanel.vue
git commit -m "feat(monitor): 历史趋势面板支持折叠"
```

---

## Task 5: 高次谐波频谱面板接入折叠（默认折叠）

**Files:**
- Modify: `frontend/src/features/device-monitor/components/compensation/HarmonicSpectrumPanel.vue`

- [ ] **Step 1: 引入折叠能力**

在 `HarmonicSpectrumPanel.vue` 的 `<script setup>` import 区追加：

```ts
import { usePanelCollapse } from '@/shared/composables/usePanelCollapse'
import PanelCollapseToggle from '@/shared/components/PanelCollapseToggle.vue'
```

在 `const activePhase = ref<HarmonicSpectrumPhase>('a')` 之后追加：

```ts
const { collapsed, toggle } = usePanelCollapse('compensation-monitor:collapse:harmonic', true)
```

- [ ] **Step 2: 头部加折叠按钮，正文按折叠态隐藏**

把模板里 `.spectrum-panel__head` 内第一个 `<div>`（含 `<h3>高次谐波频谱</h3>`）改为：

```html
      <div>
        <div class="panel-title-row">
          <h3>高次谐波频谱</h3>
          <PanelCollapseToggle :collapsed="collapsed" @toggle="toggle" />
        </div>
        <span>展示最新采样的 2~31 次谐波分布。</span>
      </div>
```

给 `.spectrum-panel__controls`、`.spectrum-panel__summary`、`.spectrum-panel__chart-wrap` 三个块都加 `v-show="!collapsed"`。

- [ ] **Step 3: 加标题行样式**

在 `<style scoped>` 末尾追加：

```css
.panel-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
```

- [ ] **Step 4: 类型检查**

Run: `npm run typecheck`
Expected: 无新增报错。

注意：本面板默认折叠，图表容器以 `v-show` 在折叠态保留于 DOM。`useECharts` 对 `chartRef` 装有 `ResizeObserver`，展开时容器尺寸由 0 变为实际值会触发 `resize()`，图表自动重排。Task 11 的 dev server 走查需确认首次展开后频谱图正常显示。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/features/device-monitor/components/compensation/HarmonicSpectrumPanel.vue
git commit -m "feat(monitor): 高次谐波频谱面板支持折叠（默认折叠）"
```

---

## Task 6: 实时详查面板接入折叠

**Files:**
- Modify: `frontend/src/features/device-monitor/components/compensation/CompensationDetailPanel.vue`

- [ ] **Step 1: 引入折叠能力**

在 `CompensationDetailPanel.vue` 的 `<script setup>` import 区追加：

```ts
import { usePanelCollapse } from '@/shared/composables/usePanelCollapse'
import PanelCollapseToggle from '@/shared/components/PanelCollapseToggle.vue'
```

在 `const resolvedTab = computed(...)` 之后追加：

```ts
const { collapsed, toggle } = usePanelCollapse('compensation-monitor:collapse:detail', false)
```

- [ ] **Step 2: 头部加折叠按钮，正文按折叠态隐藏**

把模板里 `.detail-panel__intro` 块改为：

```html
      <div class="detail-panel__intro">
        <div class="panel-title-row">
          <h3>实时详查</h3>
          <PanelCollapseToggle :collapsed="collapsed" @toggle="toggle" />
        </div>
        <span>三相电气量与回路投切状态</span>
      </div>
```

给 `.detail-panel__tab-switcher` 那个 `<div>` 现有的 `v-if="showCircuitTab"` 之外，再加 `v-show="!collapsed"`：

```html
      <div
        v-if="showCircuitTab"
        v-show="!collapsed"
        class="detail-panel__tab-switcher"
      >
```

给 `.detail-panel__body` 那个 `<div>` 加 `v-show="!collapsed"`。

- [ ] **Step 3: 加标题行样式**

在 `<style scoped>` 末尾追加：

```css
.panel-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
```

- [ ] **Step 4: 类型检查 + 跑相关测试**

Run: `npm run typecheck`
Expected: 无新增报错。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/features/device-monitor/components/compensation/CompensationDetailPanel.vue
git commit -m "feat(monitor): 实时详查面板支持折叠"
```

---

## Task 7: 控制参数摘要面板接入折叠

**Files:**
- Modify: `frontend/src/features/device-monitor/components/compensation/CompensationControlSummaryPanel.vue`

- [ ] **Step 1: 引入折叠能力**

在 `CompensationControlSummaryPanel.vue` 的 `<script setup>` import 区追加（该文件目前只 import 了类型，新增值导入）：

```ts
import { usePanelCollapse } from '@/shared/composables/usePanelCollapse'
import PanelCollapseToggle from '@/shared/components/PanelCollapseToggle.vue'
```

在 `const emit = defineEmits(...)` 之后追加：

```ts
const { collapsed, toggle } = usePanelCollapse('compensation-monitor:collapse:control-summary', false)
```

- [ ] **Step 2: 头部加折叠按钮，正文按折叠态隐藏**

把模板里 `.control-summary-title` 块改为（在标题与提示文字之外，把折叠按钮放进 headline 行）。具体：`.control-summary-headline` 内部当前是 `.control-summary-title` + `el-button`。在 `el-button` 之后追加折叠按钮：

```html
        <PanelCollapseToggle :collapsed="collapsed" @toggle="toggle" />
```

给 `v-if="hasSummaryData"` 的 `.profile-list`、`v-if="capacityExpansionItems.length"` 的 `.capacity-expansion-list`、`v-else` 的 `.control-summary-empty` 三个块都追加 `v-show="!collapsed"`（保留各自原有的 `v-if` / `v-else`）。

- [ ] **Step 3: 类型检查**

Run: `npm run typecheck`
Expected: 无新增报错。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/features/device-monitor/components/compensation/CompensationControlSummaryPanel.vue
git commit -m "feat(monitor): 控制参数摘要面板支持折叠"
```

---

## Task 8: 设备档案面板接入折叠（默认折叠）

**Files:**
- Modify: `frontend/src/features/device-monitor/components/compensation/CompensationDeviceProfile.vue`

- [ ] **Step 1: 引入折叠能力**

在 `CompensationDeviceProfile.vue` 的 `<script setup>` import 区追加：

```ts
import { usePanelCollapse } from '@/shared/composables/usePanelCollapse'
import PanelCollapseToggle from '@/shared/components/PanelCollapseToggle.vue'
```

在 `const emit = defineEmits(...)` 之后追加：

```ts
const { collapsed, toggle } = usePanelCollapse('compensation-monitor:collapse:device-profile', true)
```

- [ ] **Step 2: 头部加折叠按钮，正文按折叠态隐藏**

把模板里 `.side-panel__head` 块改为（标题、编辑按钮、折叠按钮同一行）：

```html
    <div class="side-panel__head">
      <h3>设备档案</h3>
      <div class="side-panel__head-actions">
        <button
          v-if="editable"
          class="edit-btn"
          @click="emit('edit')"
        >
          <el-icon><Edit /></el-icon>
          编辑
        </button>
        <PanelCollapseToggle :collapsed="collapsed" @toggle="toggle" />
      </div>
    </div>
```

给 `.profile-list` 那个 `<div>` 加 `v-show="!collapsed"`。

- [ ] **Step 3: 加 head-actions 样式**

在 `<style scoped>` 末尾追加：

```css
.side-panel__head-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
```

- [ ] **Step 4: 类型检查**

Run: `npm run typecheck`
Expected: 无新增报错。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/features/device-monitor/components/compensation/CompensationDeviceProfile.vue
git commit -m "feat(monitor): 设备档案面板支持折叠（默认折叠）"
```

---

## Task 9: 接入诊断局部折叠包装组件

`DeviceTemplateDiagnosticsPanel` 是跨设备类型共享组件，不直接改它。新建补偿页专用的局部折叠包装：折叠时只显示标题与一行摘要（状态 + 指标覆盖），展开时内嵌完整诊断面板（内嵌时用 `:deep()` 抹掉其自带卡片外框与头部，沿用 `CompensationDetailPanel` 内嵌子面板的既有写法）。

**Files:**
- Create: `frontend/src/features/device-monitor/components/compensation/CompensationDiagnosticsCollapsible.vue`
- Test: `frontend/src/features/device-monitor/components/compensation/__tests__/CompensationDiagnosticsCollapsible.test.ts`

- [ ] **Step 1: 写失败测试**

创建 `frontend/src/features/device-monitor/components/compensation/__tests__/CompensationDiagnosticsCollapsible.test.ts`：

```ts
import { describe, expect, it, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationDiagnosticsCollapsible from '../CompensationDiagnosticsCollapsible.vue'

const diagnostics = {
  template_key: 'capacitor_bank_controller',
  display_name: '电容补偿控制器',
  overall_status: 'passed',
  metric_coverage: { live: 6, total: 6, missing: 0, missing_keys: [] },
  trend_coverage: { drawable_keys: [], unsupported_keys: [] },
  panel_coverage: { specific_panels: [] },
  ingestion_health: { ingestion_status: 'online' },
} as any

const stubs = {
  'el-icon': { template: '<i><slot /></i>' },
  DeviceTemplateDiagnosticsPanel: { template: '<div class="diag-panel-stub" />' },
}

describe('CompensationDiagnosticsCollapsible', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('默认折叠：显示摘要、隐藏完整诊断面板', () => {
    const wrapper = mount(CompensationDiagnosticsCollapsible, {
      props: { diagnostics },
      global: { stubs },
    })
    expect(wrapper.text()).toContain('接入诊断')
    expect(wrapper.text()).toContain('接入完整')
    expect(wrapper.text()).toContain('6/6')
    expect(wrapper.find('.diag-panel-stub').exists()).toBe(false)
  })

  it('点击折叠按钮后展开，显示完整诊断面板', async () => {
    const wrapper = mount(CompensationDiagnosticsCollapsible, {
      props: { diagnostics },
      global: { stubs },
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.find('.diag-panel-stub').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm run test:unit -- src/features/device-monitor/components/compensation/__tests__/CompensationDiagnosticsCollapsible.test.ts`
Expected: FAIL，无法解析 `../CompensationDiagnosticsCollapsible.vue`。

- [ ] **Step 3: 实现 CompensationDiagnosticsCollapsible.vue**

创建 `frontend/src/features/device-monitor/components/compensation/CompensationDiagnosticsCollapsible.vue`：

```vue
<script setup lang="ts">
import { computed } from 'vue'
import type { MonitorTemplateDiagnostics } from '@/api/deviceMonitor'
import DeviceTemplateDiagnosticsPanel from '@/features/device-monitor/components/common/DeviceTemplateDiagnosticsPanel.vue'
import PanelCollapseToggle from '@/shared/components/PanelCollapseToggle.vue'
import { usePanelCollapse } from '@/shared/composables/usePanelCollapse'

const props = defineProps<{
  diagnostics: MonitorTemplateDiagnostics
}>()

const { collapsed, toggle } = usePanelCollapse('compensation-monitor:collapse:diagnostics', true)

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    passed: '接入完整',
    partial: '部分接入',
    missing: '指标缺失',
    offline: '采集离线',
  }
  return map[props.diagnostics.overall_status] || '部分接入'
})

const summaryText = computed(() => {
  const coverage = props.diagnostics.metric_coverage
  return `${statusLabel.value} · ${coverage.live}/${coverage.total} 指标覆盖`
})
</script>

<template>
  <section class="diagnostics-collapsible">
    <div class="diagnostics-collapsible__head">
      <div class="diagnostics-collapsible__title">
        <h3>接入诊断</h3>
        <span>{{ summaryText }}</span>
      </div>
      <PanelCollapseToggle
        :collapsed="collapsed"
        @toggle="toggle"
      />
    </div>

    <div
      v-show="!collapsed"
      class="diagnostics-collapsible__body"
    >
      <DeviceTemplateDiagnosticsPanel :diagnostics="diagnostics" />
    </div>
  </section>
</template>

<style scoped>
.diagnostics-collapsible {
  padding: 16px;
  background: #131d2b;
  border: 1px solid #243244;
  border-radius: 14px;
}

.diagnostics-collapsible__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.diagnostics-collapsible__title {
  min-width: 0;
}

.diagnostics-collapsible__title h3 {
  margin: 0;
  font-size: 15px;
  color: #f5f7fb;
}

.diagnostics-collapsible__title span {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #8ea0bc;
}

.diagnostics-collapsible__body {
  margin-top: 14px;
}

/* 内嵌完整诊断面板时抹掉其自带卡片外框与重复头部 */
.diagnostics-collapsible__body :deep(.template-diagnostics) {
  padding: 0;
  border: none;
  border-radius: 0;
  background: transparent;
}

.diagnostics-collapsible__body :deep(.template-diagnostics__header) {
  display: none;
}
</style>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm run test:unit -- src/features/device-monitor/components/compensation/__tests__/CompensationDiagnosticsCollapsible.test.ts`
Expected: PASS，2 个用例全通过。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/features/device-monitor/components/compensation/CompensationDiagnosticsCollapsible.vue frontend/src/features/device-monitor/components/compensation/__tests__/CompensationDiagnosticsCollapsible.test.ts
git commit -m "feat(monitor): 新增接入诊断局部折叠包装组件"
```

---

## Task 10: 重排监控页面板顺序 + 实时详查默认 tab

**Files:**
- Modify: `frontend/src/features/device-monitor/views/CompensationMonitorView.vue`
- Modify: `frontend/src/features/device-monitor/composables/useDeviceMonitorPage.ts:68`

- [ ] **Step 1: 实时详查默认 tab 改为回路状态**

在 `useDeviceMonitorPage.ts` 第 68 行，把：

```ts
  const compensationDetailTab = ref<'three-phase' | 'circuit'>('three-phase')
```

改为：

```ts
  const compensationDetailTab = ref<'three-phase' | 'circuit'>('circuit')
```

说明：`CompensationDetailPanel` 的 `resolvedTab` 计算属性对非电容设备恒返回 `'three-phase'`（`showCircuitTab ? props.activeTab : 'three-phase'`），故该默认值对 SVG 等非电容设备无影响。

- [ ] **Step 2: 重排主区面板**

在 `CompensationMonitorView.vue` 中，把 `<template #main>` 内组件顺序改为：实时概览 → 实时详查 → 历史趋势 → 高次谐波频谱 → 告警记录表。即把 `CompensationDetailPanel` 整块移到 `CompensationRealtimeOverview` 之后、`CompensationTrendPanel` 之前。`<template #main>` 改为：

```html
    <template #main>
      <CompensationRealtimeOverview
        :core-metric="page.compensationCoreMetric"
        :pf-metric="page.compensationPfMetric"
        :metrics="page.compensationMetrics"
        :module-status="page.moduleStatusModel"
        :extended-hint="page.compensationExtendedHint"
      />

      <CompensationDetailPanel
        v-if="page.isSvgDevice || page.compensationSubtype === 'capacitor_bank_controller'"
        v-model:active-tab="page.compensationDetailTab"
        :svg-telemetry="page.compensationSvgTelemetry"
        :capacitor-bank-telemetry="page.compensationCapacitorBankTelemetry"
        :is-capacitor-bank="page.compensationSubtype === 'capacitor_bank_controller'"
        :circuit-profile="page.compensationCircuitProfile"
      />

      <CompensationTrendPanel
        v-model:active-tab="page.compensationTrendTab"
        v-model:time-range="page.timeRange"
        :tabs="page.compensationTrendTabs"
        :model="page.compensationTrendModel"
        :shortcuts="page.timeShortcuts"
        :loading="page.chartLoading"
        @range-change="page.handleRangeChange"
      />

      <HarmonicSpectrumPanel
        v-if="page.compensationSubtype === 'capacitor_bank_controller'"
        :telemetry="page.compensationCapacitorBankTelemetry"
        :control-profile="page.compensationCapacitorBankControlProfile"
      />

      <CompensationAlarmTable
        :rows="page.alarms"
        :action-id="page.alarmActionId"
        @resolve="page.handleResolveAlarm"
      />
    </template>
```

- [ ] **Step 3: 重排右栏面板**

把 `<template #side>` 内组件顺序改为：运行事件 → 运行状态 → 控制参数摘要 → 设备档案 → 接入诊断。其中接入诊断改用 Task 9 的包装组件。`<template #side>` 改为：

```html
    <template #side>
      <CompensationEventTimeline :events="page.compensationEvents" />
      <CompensationStatusSummary :items="page.compensationStatusItems" />
      <CompensationControlSummaryPanel
        v-if="page.compensationSubtype === 'capacitor_bank_controller'"
        :summary-items="page.capacitorBankControlSummaryView.summaryItems"
        :capacity-expansion-items="page.capacitorBankControlSummaryView.capacityExpansionItems"
        :has-summary-data="page.capacitorBankControlSummaryView.hasSummaryData"
        @open-console="page.router.push(`/device-console/${page.deviceId}`)"
      />
      <CompensationDeviceProfile
        :items="page.compensationProfileItems"
        :editable="page.isSvgDevice && page.canControlDevices"
        @edit="page.svgProfileEditVisible = true"
      />
      <CompensationDiagnosticsCollapsible
        v-if="page.templateDiagnostics"
        :diagnostics="page.templateDiagnostics"
      />
    </template>
```

- [ ] **Step 4: 调整 import**

在 `CompensationMonitorView.vue` 的 `<script setup>` import 区，把：

```ts
import DeviceTemplateDiagnosticsPanel from '@/features/device-monitor/components/common/DeviceTemplateDiagnosticsPanel.vue'
```

改为：

```ts
import CompensationDiagnosticsCollapsible from '@/features/device-monitor/components/compensation/CompensationDiagnosticsCollapsible.vue'
```

（其余 import 不变。）

- [ ] **Step 5: 类型检查**

Run: `npm run typecheck`
Expected: 无新增报错。

- [ ] **Step 6: 提交**

```bash
git add frontend/src/features/device-monitor/views/CompensationMonitorView.vue frontend/src/features/device-monitor/composables/useDeviceMonitorPage.ts
git commit -m "feat(monitor): 按运维巡检优先级重排补偿监控页面板"
```

---

## Task 11: 全量校验与 dev server 走查

**Files:** 无（仅验证）

- [ ] **Step 1: 类型检查**

Run: `npm run typecheck`
Expected: 无报错。

- [ ] **Step 2: 跑设备监控相关单测**

Run: `npm run test:unit -- src/features/device-monitor src/shared/composables/__tests__/usePanelCollapse.test.ts src/shared/components/__tests__/PanelCollapseToggle.test.ts`
Expected: 全部 PASS。

- [ ] **Step 3: Lint**

Run: `npm run lint`
Expected: 无新增报错（已有历史告警可忽略）。

- [ ] **Step 4: dev server 走查**

启动 `npm run dev`，浏览器打开电容补偿控制器监控页（如 `localhost:3000/devices/12/monitor`），逐项确认：

- 主区面板顺序：实时概览 → 实时详查 → 历史趋势 → 高次谐波频谱 → 告警记录表。
- 右栏面板顺序：运行事件 → 运行状态 → 控制参数摘要 → 设备档案 → 接入诊断。
- 进入页面时「实时详查」默认显示「回路状态」tab。
- 实时概览底部 6 指标条为：母线电压 / 线电流 / 有功功率 / 电网频率 / 控制模式 / 柜内温度，不再出现「回路投入率」；无功 Hero 进度条的「回路投入率」仍正常显示。
- 高次谐波频谱、设备档案、接入诊断默认折叠；历史趋势、控制参数摘要、实时详查默认展开。
- 点击各面板折叠按钮可正常收起/展开；展开高次谐波频谱后频谱图正常铺满（无 0 尺寸残留）。
- 折叠任意面板后刷新页面，折叠状态保持。
- 接入诊断折叠态显示「接入完整 · 6/6 指标覆盖」一行摘要；展开后为完整诊断内容且无双层卡片边框。

- [ ] **Step 5: 抽查其他设备类型未受影响**

打开一个 SVG 补偿设备或非补偿设备的监控页，确认其排版正常、`DeviceTemplateDiagnosticsPanel` 行为如旧（其他监控页未引用补偿包装组件，应无变化）。

---

## 自查记录

- **Spec 覆盖**：主区/右栏重排（Task 10）、接入诊断降级折叠（Task 9 + 10）、回路状态前移（Task 6 + Task 10 Step 1）、指标条去重补电网频率（Task 3）、折叠机制与 localStorage 持久化（Task 1/2 + 各面板 Task）、接入诊断局部处理决策（Task 9）——均有对应任务。
- **类型一致性**：折叠组合式统一返回 `{ collapsed, toggle }`；`PanelCollapseToggle` 统一 `collapsed` prop + `toggle` 事件；`buildCompensationOverviewMetrics` 新增入参字段 `gridFrequencyValue` / `gridFrequencyMissing` 在 Task 3 的类型定义、调用方、测试三处一致。
- **无占位符**：所有步骤含可执行代码与命令。
