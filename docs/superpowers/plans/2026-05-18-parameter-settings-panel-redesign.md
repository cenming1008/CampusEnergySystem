# 参数设置面板重设计 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把电容补偿设备工作台「参数设置」标签页的「参数管理」只读面板与「参数修改」可写面板合并为单一面板，每个参数只出现一次，采用分区长表布局并重设计容量展开详情。

**Architecture:** 新建一个 `ControlConsoleParametersPanel.vue` 组件，汇总现有两个面板的全部 props（`sectionView` / `readonlySummaryView` / `writeSectionView` / `canWriteParameters` / `editableParameterCards`）与 `open-write-dialog` 事件。它渲染统一头部条 + 4 个分组的全宽表格（参数 / 当前值 / 操作）+ 可折叠的容量展开详情。两个消费方（`CompensationMonitorView.vue`、`DeviceControlConsole.vue`）改为渲染一个面板。旧的 `ControlConsoleReadonlyParamsPanel.vue`、`ControlConsoleWritableParamsPanel.vue`、`ControlConsoleParameterSection.vue` 删除。数据层（`viewMapping.ts`、`capacitorBankControlProfile.ts`）不变。

**Tech Stack:** Vue 3 (`<script setup lang="ts">`)、TypeScript、Vitest + `@vue/test-utils`。

**设计依据：** `docs/superpowers/specs/2026-05-18-parameter-settings-panel-redesign-design.md`

**测试命令：** 所有命令在 `frontend/` 目录下执行。单文件：`npx vitest run <path>`；全量：`npm run test:unit`；构建：`npm run build`。

---

### Task 0: 为会话前的遗留改动打底提交

工作区当前带有会话前的未提交改动（电容工作台标签页相关），且这些文件与本次重设计要改的文件重叠。先把它们单独提交成一个基线 commit，使本次重设计的 diff 干净可审。

**Files:**
- 仅 git 操作，不改代码。

- [ ] **Step 1: 查看遗留改动范围**

Run: `git status --short && git diff --stat`
Expected: 列出 `frontend/src/...` 下若干 `M` 文件与 1 个 `??`（`CompensationThreePhasePanel.test.ts`）。确认这些都不是本计划新增的文件。

- [ ] **Step 2: 提交遗留改动作为基线**

```bash
git add frontend/
git commit -m "chore(monitor): checkpoint in-progress workbench changes"
```

- [ ] **Step 3: 确认工作区干净**

Run: `git status --short`
Expected: 无输出（工作区干净）。

---

### Task 1: 新建合并后的 `ControlConsoleParametersPanel` 组件

**Files:**
- Create: `frontend/src/features/device-control/components/ControlConsoleParametersPanel.vue`
- Test: `frontend/src/features/device-control/components/__tests__/ControlConsoleParametersPanel.test.ts`

- [ ] **Step 1: 写失败测试**

创建 `frontend/src/features/device-control/components/__tests__/ControlConsoleParametersPanel.test.ts`：

```ts
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ControlConsoleParametersPanel from '../ControlConsoleParametersPanel.vue'
import type {
  ControlConsoleReadonlySectionView,
  ControlConsoleReadonlySummaryView,
  ControlConsoleWriteSectionView,
} from '@/features/device-control/viewMapping'
import type { CapacitorBankControlParameterMeta } from '@/features/device-control/capacitorBankControlProfile'

const sectionView: ControlConsoleReadonlySectionView = {
  title: '只读参数快照',
  sectionLabel: '只读参数',
  tone: 'readonly',
  tags: [{ text: '最新参数', tone: 'success' }],
  metaText: '来源：telemetry · 快照：2026-05-18 16:31:38',
  showCapacityExpansion: true,
}

const readonlySummaryView: ControlConsoleReadonlySummaryView = {
  sourceStatusText: '最新参数',
  sourceStatusTone: 'success',
  sourceMeta: '来源：telemetry · 快照：2026-05-18 16:31:38',
  summaryItems: [{ label: '投入功率因数', value: '0.90' }],
  capacityExpansionItems: [
    { label: 'A相分补', value: '12.0 kvar / 12.0 kvar' },
    { label: '公补 1-8', value: '30.0 kvar / 60.0 kvar' },
  ],
  groupedParameters: [
    {
      key: 'strategy',
      label: '投切策略',
      items: [
        { key: 'switch_on_power_factor', label: '投入功率因数', description: '投入判定。', currentValue: '0.90', register: '0xD2', readWrite: '读/写' },
      ],
    },
    {
      key: 'circuits',
      label: '回路配置',
      items: [
        { key: 'common_output_circuit_count', label: '共补输出回路', description: '共补路数。', currentValue: '12', register: '0xD6', readWrite: '读/写' },
      ],
    },
    {
      key: 'protection',
      label: '保护门限',
      items: [
        { key: 'overvoltage_threshold', label: '过压保护门限', description: '过压门限。', currentValue: '250 V', register: '0xDD', readWrite: '读/写' },
      ],
    },
    {
      key: 'device',
      label: '通讯参数',
      items: [
        { key: 'baud_rate', label: '通讯速率', description: '波特率。', currentValue: '9600 bps', register: '0xE2', readWrite: '读/写' },
      ],
    },
  ],
}

function buildWriteSectionView(
  overrides: Partial<ControlConsoleWriteSectionView> = {},
): ControlConsoleWriteSectionView {
  return {
    title: '参数修改',
    sectionLabel: '参数修改',
    tone: 'writable',
    description: '提交前需二次确认。',
    tags: [],
    writeStatusText: '当前禁止写入',
    writeStatusTone: 'warning',
    capabilityStatusText: '支持参数写入',
    capabilityStatusTone: 'success',
    roleSummaryText: '管理员，可发起受控写入',
    alert: { title: '写入入口已锁定', message: '当前设备离线，暂不开放参数写入。', tone: 'warning' },
    ...overrides,
  }
}

const editableParameterCards: Array<CapacitorBankControlParameterMeta & { currentValue: string }> = [
  { key: 'switch_on_power_factor', group: 'strategy', label: '投入功率因数', register: '0xD2', readWrite: '读/写', description: '投入判定。', editable: true, currentValue: '0.90' },
  { key: 'overvoltage_threshold', group: 'protection', label: '过压保护门限', register: '0xDD', readWrite: '读/写', description: '过压门限。', editable: true, currentValue: '250 V' },
]

function mountPanel(
  options: { canWriteParameters?: boolean; writeSectionView?: ControlConsoleWriteSectionView } = {},
) {
  return mount(ControlConsoleParametersPanel, {
    props: {
      sectionView,
      readonlySummaryView,
      writeSectionView: options.writeSectionView ?? buildWriteSectionView(),
      canWriteParameters: options.canWriteParameters ?? false,
      editableParameterCards,
    },
  })
}

describe('ControlConsoleParametersPanel', () => {
  it('renders a unified header with snapshot and write status', () => {
    const wrapper = mountPanel()
    const header = wrapper.get('[data-test="params-header"]')
    expect(header.text()).toContain('最新参数')
    expect(header.text()).toContain('来源：telemetry · 快照：2026-05-18 16:31:38')
    expect(header.text()).toContain('当前禁止写入')
    expect(header.text()).toContain('管理员，可发起受控写入')
    expect(wrapper.get('[data-test="params-alert"]').text()).toContain('当前设备离线，暂不开放参数写入。')
  })

  it('does not render the legacy duplicated summary cards', () => {
    const wrapper = mountPanel()
    expect(wrapper.find('.readonly-summary-card').exists()).toBe(false)
  })

  it('renders all four parameter groups as sectioned tables', () => {
    const wrapper = mountPanel()
    expect(wrapper.findAll('[data-test="param-group-card"]')).toHaveLength(4)
    expect(wrapper.text()).toContain('投切策略')
    expect(wrapper.text()).toContain('回路配置')
    expect(wrapper.text()).toContain('保护门限')
    expect(wrapper.text()).toContain('通讯参数')
    expect(wrapper.text()).toContain('投入功率因数')
    expect(wrapper.text()).toContain('250 V')
  })

  it('shows an edit button for writable params and a pending marker otherwise', () => {
    const wrapper = mountPanel()
    expect(wrapper.findAll('[data-test="param-edit-button"]')).toHaveLength(2)
    expect(wrapper.findAll('[data-test="param-write-pending"]')).toHaveLength(2)
  })

  it('disables the edit button and emits nothing when writing is locked', async () => {
    const wrapper = mountPanel({ canWriteParameters: false })
    const button = wrapper.get('[data-test="param-edit-button"]')
    expect((button.element as HTMLButtonElement).disabled).toBe(true)
    await button.trigger('click')
    expect(wrapper.emitted('open-write-dialog')).toBeUndefined()
  })

  it('emits open-write-dialog with the parameter key when writing is allowed', async () => {
    const wrapper = mountPanel({
      canWriteParameters: true,
      writeSectionView: buildWriteSectionView({
        writeStatusText: '当前允许写入',
        writeStatusTone: 'success',
        alert: null,
      }),
    })
    const button = wrapper.get('[data-test="param-edit-button"]')
    expect((button.element as HTMLButtonElement).disabled).toBe(false)
    await button.trigger('click')
    expect(wrapper.emitted('open-write-dialog')?.[0]).toEqual(['switch_on_power_factor'])
    expect(wrapper.find('[data-test="params-alert"]').exists()).toBe(false)
  })

  it('renders capacity expansion split into phase rows and a common grid, toggleable', async () => {
    const wrapper = mountPanel()
    const slots = wrapper.findAll('[data-test="capacity-slot"]')
    expect(slots).toHaveLength(4)
    expect(slots[0].text()).toContain('A1')
    expect(slots[0].text()).toContain('12.0 kvar')
    expect(slots[2].text()).toContain('1路')
    expect(slots[2].text()).toContain('30.0 kvar')
    await wrapper.get('[data-test="toggle-capacity"]').trigger('click')
    expect(wrapper.findAll('[data-test="capacity-slot"]')).toHaveLength(0)
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npx vitest run src/features/device-control/components/__tests__/ControlConsoleParametersPanel.test.ts`
Expected: FAIL — 报错找不到 `../ControlConsoleParametersPanel.vue`。

- [ ] **Step 3: 创建组件**

创建 `frontend/src/features/device-control/components/ControlConsoleParametersPanel.vue`：

```vue
<script setup lang="ts">
import { computed, ref } from 'vue'
import type {
  ControlConsoleReadonlySectionView,
  ControlConsoleReadonlySummaryView,
  ControlConsoleWriteSectionView,
} from '@/features/device-control/viewMapping'
import type { CapacitorBankControlParameterMeta } from '@/features/device-control/capacitorBankControlProfile'

const props = defineProps<{
  sectionView: ControlConsoleReadonlySectionView
  readonlySummaryView: ControlConsoleReadonlySummaryView
  writeSectionView: ControlConsoleWriteSectionView
  canWriteParameters: boolean
  editableParameterCards: Array<CapacitorBankControlParameterMeta & { currentValue: string }>
}>()

const emit = defineEmits<{
  (e: 'open-write-dialog', parameterKey: string): void
}>()

const capacityExpanded = ref(true)

const snapshotTag = computed(() => props.sectionView.tags[0] ?? null)

const editableKeySet = computed(
  () => new Set(props.editableParameterCards.map((item) => String(item.key))),
)

const writeDisabledReason = computed(
  () => props.writeSectionView.alert?.message
    || props.writeSectionView.roleSummaryText
    || '当前不可写入',
)

const phaseCapacityItems = computed(() =>
  props.readonlySummaryView.capacityExpansionItems.filter((item) => item.label.includes('相')),
)

const commonCapacitySlots = computed(() =>
  props.readonlySummaryView.capacityExpansionItems
    .filter((item) => !item.label.includes('相'))
    .flatMap((item) => capacitySlots(item)),
)

function capacitySlotLabel(groupLabel: string, index: number) {
  const range = groupLabel.match(/(\d+)\s*-\s*(\d+)/)
  if (range) return `${Number(range[1]) + index}路`
  const phase = groupLabel.match(/^([ABC])相/)
  if (phase) return `${phase[1]}${index + 1}`
  return `${index + 1}路`
}

function capacitySlots(item: { label: string; value: string }) {
  return item.value
    .split('/')
    .map((value) => value.trim())
    .filter(Boolean)
    .map((value, index) => ({
      key: `${item.label}-${index}`,
      label: capacitySlotLabel(item.label, index),
      value,
    }))
}

function isEditable(parameterKey: string) {
  return editableKeySet.value.has(parameterKey)
}
</script>

<template>
  <div class="params-panel">
    <header
      class="params-header"
      data-test="params-header"
    >
      <div class="params-header__col">
        <span
          v-if="snapshotTag"
          class="params-badge"
          :class="`params-badge--${snapshotTag.tone}`"
        >
          {{ snapshotTag.text }}
        </span>
        <small>{{ readonlySummaryView.sourceMeta }}</small>
      </div>
      <div class="params-header__col params-header__col--right">
        <span
          class="params-badge"
          :class="`params-badge--${writeSectionView.writeStatusTone}`"
        >
          {{ writeSectionView.writeStatusText }}
        </span>
        <small>{{ writeSectionView.roleSummaryText }}</small>
      </div>
    </header>
    <p
      v-if="writeSectionView.alert"
      class="params-alert"
      data-test="params-alert"
    >
      {{ writeSectionView.alert.message }}
    </p>

    <section
      v-for="group in readonlySummaryView.groupedParameters"
      :key="group.key"
      class="param-section"
      data-test="param-group-card"
    >
      <header class="param-section__head">
        <h4>{{ group.label }}</h4>
        <span>{{ group.items.length }} 个参数</span>
      </header>
      <table class="param-table">
        <thead>
          <tr>
            <th>参数</th>
            <th>当前值</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in group.items"
            :key="item.key"
            data-test="param-row"
          >
            <td :title="item.description">{{ item.label }}</td>
            <td class="param-table__value">{{ item.currentValue }}</td>
            <td>
              <button
                v-if="isEditable(item.key)"
                type="button"
                class="param-edit-button"
                data-test="param-edit-button"
                :disabled="!canWriteParameters"
                :title="canWriteParameters ? '修改参数' : writeDisabledReason"
                @click="emit('open-write-dialog', item.key)"
              >
                修改
              </button>
              <span
                v-else
                class="param-write-pending"
                data-test="param-write-pending"
              >
                写入待开通
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section
      v-if="sectionView.showCapacityExpansion"
      class="capacity-panel"
    >
      <header class="capacity-panel__head">
        <strong>容量展开详情</strong>
        <button
          type="button"
          class="capacity-toggle"
          data-test="toggle-capacity"
          @click="capacityExpanded = !capacityExpanded"
        >
          {{ capacityExpanded ? '收起' : '展开' }}
        </button>
      </header>
      <div
        v-if="capacityExpanded"
        class="capacity-body"
      >
        <div
          v-if="phaseCapacityItems.length"
          class="capacity-group"
        >
          <span class="capacity-group__title">分相补偿</span>
          <div
            v-for="item in phaseCapacityItems"
            :key="item.label"
            class="capacity-phase-row"
          >
            <span class="capacity-phase-row__label">{{ item.label }}</span>
            <div class="capacity-slot-grid">
              <div
                v-for="slot in capacitySlots(item)"
                :key="slot.key"
                class="capacity-slot"
                data-test="capacity-slot"
              >
                <small>{{ slot.label }}</small>
                <strong>{{ slot.value }}</strong>
              </div>
            </div>
          </div>
        </div>
        <div
          v-if="commonCapacitySlots.length"
          class="capacity-group"
        >
          <span class="capacity-group__title">公共补偿</span>
          <div class="capacity-slot-grid capacity-slot-grid--common">
            <div
              v-for="slot in commonCapacitySlots"
              :key="slot.key"
              class="capacity-slot"
              data-test="capacity-slot"
            >
              <small>{{ slot.label }}</small>
              <strong>{{ slot.value }}</strong>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.params-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.params-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid rgba(48, 70, 95, 0.72);
  background: rgba(12, 22, 38, 0.7);
}

.params-header__col {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.params-header__col--right {
  justify-content: flex-end;
}

.params-header__col small {
  color: #8da2bf;
  font-size: 11px;
  line-height: 1.5;
}

.params-badge {
  flex: 0 0 auto;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  border: 1px solid transparent;
}

.params-badge--success {
  color: #86efac;
  background: rgba(34, 197, 94, 0.12);
  border-color: rgba(34, 197, 94, 0.32);
}

.params-badge--warning {
  color: #fcd34d;
  background: rgba(251, 191, 36, 0.12);
  border-color: rgba(251, 191, 36, 0.32);
}

.params-badge--info {
  color: #93c5fd;
  background: rgba(96, 165, 250, 0.12);
  border-color: rgba(96, 165, 250, 0.32);
}

.params-alert {
  margin: 0;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(251, 191, 36, 0.32);
  background: rgba(251, 191, 36, 0.08);
  color: #fcd34d;
  font-size: 12px;
  line-height: 1.5;
}

.param-section {
  border: 1px solid rgba(44, 65, 89, 0.7);
  border-radius: 10px;
  background: rgba(12, 22, 38, 0.7);
  overflow: hidden;
}

.param-section__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 9px 14px;
  border-bottom: 1px solid rgba(44, 65, 89, 0.7);
}

.param-section__head h4 {
  margin: 0;
  font-size: 13px;
  color: #c8d8ee;
}

.param-section__head span {
  color: #6a84a2;
  font-size: 11px;
}

.param-table {
  width: 100%;
  border-collapse: collapse;
}

.param-table th {
  text-align: left;
  padding: 7px 14px;
  font-size: 11px;
  font-weight: 500;
  color: #6a84a2;
  background: rgba(8, 17, 30, 0.4);
  border-bottom: 1px solid rgba(33, 52, 74, 0.6);
}

.param-table th:last-child,
.param-table td:last-child {
  text-align: right;
  width: 96px;
}

.param-table td {
  padding: 8px 14px;
  font-size: 12px;
  color: #91a5c2;
  border-bottom: 1px solid rgba(33, 52, 74, 0.6);
}

.param-table tbody tr:last-child td {
  border-bottom: none;
}

.param-table__value {
  color: #f7fbff;
  font-weight: 600;
}

.param-edit-button {
  min-height: 26px;
  padding: 0 12px;
  border-radius: 7px;
  border: 1px solid rgba(245, 158, 11, 0.42);
  background: rgba(120, 53, 15, 0.18);
  color: #fde68a;
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.param-edit-button:hover:not(:disabled) {
  background: rgba(120, 53, 15, 0.3);
  border-color: rgba(245, 158, 11, 0.62);
}

.param-edit-button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.param-write-pending {
  color: #4b6282;
  font-size: 11px;
}

.capacity-panel {
  border: 1px solid rgba(48, 70, 95, 0.72);
  border-radius: 12px;
  background: rgba(12, 22, 38, 0.64);
  overflow: hidden;
}

.capacity-panel__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
}

.capacity-panel__head strong {
  color: #f7fbff;
  font-size: 13px;
}

.capacity-toggle {
  border: 1px solid rgba(71, 100, 135, 0.5);
  background: transparent;
  color: #93a7c4;
  font: inherit;
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 6px;
  cursor: pointer;
}

.capacity-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0 14px 14px;
}

.capacity-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.capacity-group__title {
  color: #6ddbd0;
  font-size: 11px;
  font-weight: 700;
}

.capacity-phase-row {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 10px;
  align-items: center;
}

.capacity-phase-row__label {
  color: #91a5c2;
  font-size: 11px;
}

.capacity-slot-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 6px;
}

.capacity-slot-grid--common {
  grid-template-columns: repeat(8, minmax(0, 1fr));
}

.capacity-slot {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid rgba(48, 70, 95, 0.62);
  background: rgba(8, 17, 30, 0.42);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.capacity-slot small {
  color: #6ddbd0;
  font-size: 10px;
}

.capacity-slot strong {
  color: #f7fbff;
  font-size: 12px;
}

@media (max-width: 1100px) {
  .capacity-slot-grid--common {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .params-header__col--right {
    justify-content: flex-start;
  }

  .capacity-slot-grid,
  .capacity-slot-grid--common {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .capacity-phase-row {
    grid-template-columns: 1fr;
  }
}
</style>
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npx vitest run src/features/device-control/components/__tests__/ControlConsoleParametersPanel.test.ts`
Expected: PASS — 7 个用例全部通过。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/features/device-control/components/ControlConsoleParametersPanel.vue frontend/src/features/device-control/components/__tests__/ControlConsoleParametersPanel.test.ts
git commit -m "feat(device-control): add merged parameters panel"
```

---

### Task 2: 在 `CompensationMonitorView` 中接入合并面板

**Files:**
- Modify: `frontend/src/features/device-monitor/views/CompensationMonitorView.vue`（import 块第 3、5 行；模板 201-223 行）
- Test: `frontend/src/features/device-monitor/views/__tests__/CompensationMonitorView.test.ts`（stub 第 191-192 行；用例 224、228-234 行）

- [ ] **Step 1: 更新视图测试（先改测试，使其针对新结构失败）**

在 `frontend/src/features/device-monitor/views/__tests__/CompensationMonitorView.test.ts` 中：

把这两行 stub：

```ts
        ControlConsoleReadonlyParamsPanel: namedStub('readonly-params-stub', '只读参数'),
        ControlConsoleWritableParamsPanel: namedStub('writable-params-stub', '可写参数'),
```

替换为一行：

```ts
        ControlConsoleParametersPanel: namedStub('params-panel-stub', '参数面板'),
```

把 “keeps the remote control module out of non-runtime workbench tabs” 用例中的这一行：

```ts
    expect(wrapper.find('.readonly-params-stub').exists()).toBe(true)
```

改为：

```ts
    expect(wrapper.find('.params-panel-stub').exists()).toBe(true)
```

把整个 “shows readonly and writable parameter panels on the parameter-settings tab” 用例：

```ts
  it('shows readonly and writable parameter panels on the parameter-settings tab', () => {
    const { wrapper } = mountView('parameter-settings')

    expect(wrapper.find('.readonly-params-stub').exists()).toBe(true)
    expect(wrapper.find('.writable-params-stub').exists()).toBe(true)
    expect(wrapper.find('.remote-panel-stub').exists()).toBe(false)
  })
```

替换为：

```ts
  it('shows the merged parameters panel on the parameter-settings tab', () => {
    const { wrapper } = mountView('parameter-settings')

    expect(wrapper.find('.params-panel-stub').exists()).toBe(true)
    expect(wrapper.findAll('.params-panel-stub')).toHaveLength(1)
    expect(wrapper.find('.remote-panel-stub').exists()).toBe(false)
  })
```

- [ ] **Step 2: 运行视图测试确认失败**

Run: `npx vitest run src/features/device-monitor/views/__tests__/CompensationMonitorView.test.ts`
Expected: FAIL — `.params-panel-stub` 不存在（视图仍渲染旧的两个面板）。

- [ ] **Step 3: 更新 import**

在 `frontend/src/features/device-monitor/views/CompensationMonitorView.vue` 中，删除第 3 行与第 5 行：

```ts
import ControlConsoleReadonlyParamsPanel from '@/features/device-control/components/ControlConsoleReadonlyParamsPanel.vue'
```

```ts
import ControlConsoleWritableParamsPanel from '@/features/device-control/components/ControlConsoleWritableParamsPanel.vue'
```

在第 2 行（`ControlConsoleLogPanel` 的 import）之后新增一行：

```ts
import ControlConsoleParametersPanel from '@/features/device-control/components/ControlConsoleParametersPanel.vue'
```

- [ ] **Step 4: 替换模板中的两个面板**

把当前 201-223 行的两个 `MonitorSectionPanel` 块：

```vue
            <MonitorSectionPanel
              shell="console"
              accent="teal"
              title="参数管理"
            >
              <ControlConsoleReadonlyParamsPanel
                :section-view="page.controlConsoleReadonlySectionView"
                :readonly-summary-view="page.controlConsoleReadonlySummaryView"
              />
            </MonitorSectionPanel>

            <MonitorSectionPanel
              shell="console"
              accent="amber"
              title="参数修改"
            >
              <ControlConsoleWritableParamsPanel
                :write-section-view="page.controlConsoleWriteSectionView"
                :can-write-parameters="page.controlConsoleCanWriteParameters"
                :editable-parameter-cards="page.controlConsoleEditableParameterCards"
                @open-write-dialog="page.openControlConsoleWriteDialog"
              />
            </MonitorSectionPanel>
```

替换为单个面板：

```vue
            <MonitorSectionPanel
              shell="console"
              accent="teal"
              title="参数设置"
            >
              <ControlConsoleParametersPanel
                :section-view="page.controlConsoleReadonlySectionView"
                :readonly-summary-view="page.controlConsoleReadonlySummaryView"
                :write-section-view="page.controlConsoleWriteSectionView"
                :can-write-parameters="page.controlConsoleCanWriteParameters"
                :editable-parameter-cards="page.controlConsoleEditableParameterCards"
                @open-write-dialog="page.openControlConsoleWriteDialog"
              />
            </MonitorSectionPanel>
```

- [ ] **Step 5: 运行视图测试确认通过**

Run: `npx vitest run src/features/device-monitor/views/__tests__/CompensationMonitorView.test.ts`
Expected: PASS — 全部用例通过。

- [ ] **Step 6: 提交**

```bash
git add frontend/src/features/device-monitor/views/CompensationMonitorView.vue frontend/src/features/device-monitor/views/__tests__/CompensationMonitorView.test.ts
git commit -m "refactor(monitor): use merged parameters panel in compensation view"
```

---

### Task 3: 在 `DeviceControlConsole` 中接入合并面板

**Files:**
- Modify: `frontend/src/views/DeviceControlConsole.vue`（import 第 8、9 行；模板 167-186 行）

`DeviceControlConsole.vue` 没有对应的视图测试覆盖这两个面板，本任务靠 Task 5 的全量测试 + 构建验证。

- [ ] **Step 1: 更新 import**

在 `frontend/src/views/DeviceControlConsole.vue` 中，删除第 8、9 行：

```ts
import ControlConsoleReadonlyParamsPanel from '@/features/device-control/components/ControlConsoleReadonlyParamsPanel.vue'
import ControlConsoleWritableParamsPanel from '@/features/device-control/components/ControlConsoleWritableParamsPanel.vue'
```

替换为单行：

```ts
import ControlConsoleParametersPanel from '@/features/device-control/components/ControlConsoleParametersPanel.vue'
```

- [ ] **Step 2: 替换模板中的两个面板**

把当前 167-186 行的两个 `MonitorSectionPanel` 块：

```vue
          <MonitorSectionPanel
            shell="console"
            accent="teal"
            title="参数管理"
          >
            <ControlConsoleReadonlyParamsPanel
              :section-view="readonlySectionView"
              :readonly-summary-view="readonlySummaryView"
            />
          </MonitorSectionPanel>

          <MonitorSectionPanel
            shell="console"
            accent="amber"
            title="参数修改"
          >
            <ControlConsoleWritableParamsPanel
              :write-section-view="writeSectionView"
              :can-write-parameters="canWriteParameters"
              :editable-parameter-cards="editableParameterCards"
              @open-write-dialog="openWriteDialog"
            />
          </MonitorSectionPanel>
```

替换为单个面板：

```vue
          <MonitorSectionPanel
            shell="console"
            accent="teal"
            title="参数设置"
          >
            <ControlConsoleParametersPanel
              :section-view="readonlySectionView"
              :readonly-summary-view="readonlySummaryView"
              :write-section-view="writeSectionView"
              :can-write-parameters="canWriteParameters"
              :editable-parameter-cards="editableParameterCards"
              @open-write-dialog="openWriteDialog"
            />
          </MonitorSectionPanel>
```

- [ ] **Step 3: 运行类型检查确认无悬空引用**

Run: `npx vue-tsc --noEmit -p tsconfig.app.json` （若该命令不存在，改用 `npm run build` 在 Task 5 一并验证，本步可跳过）
Expected: 无与 `DeviceControlConsole.vue` 相关的报错。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/DeviceControlConsole.vue
git commit -m "refactor(device-control): use merged parameters panel in control console"
```

---

### Task 4: 删除被取代的旧组件与测试

**Files:**
- Delete: `frontend/src/features/device-control/components/ControlConsoleReadonlyParamsPanel.vue`
- Delete: `frontend/src/features/device-control/components/ControlConsoleWritableParamsPanel.vue`
- Delete: `frontend/src/features/device-control/components/__tests__/ControlConsoleReadonlyParamsPanel.test.ts`
- Delete: `frontend/src/features/device-control/components/__tests__/ControlConsoleWritableParamsPanel.test.ts`
- Delete（条件性）: `frontend/src/features/device-control/components/ControlConsoleParameterSection.vue`

- [ ] **Step 1: 确认旧面板无其他引用**

Run: `grep -rn "ControlConsoleReadonlyParamsPanel\|ControlConsoleWritableParamsPanel" frontend/src`
Expected: 仅命中即将删除的 4 个文件自身（组件文件与各自测试文件中的 import / 文件名）。若命中其他文件，先把那些引用改到 `ControlConsoleParametersPanel` 再继续。

- [ ] **Step 2: 删除旧面板与其测试**

```bash
git rm frontend/src/features/device-control/components/ControlConsoleReadonlyParamsPanel.vue \
       frontend/src/features/device-control/components/ControlConsoleWritableParamsPanel.vue \
       frontend/src/features/device-control/components/__tests__/ControlConsoleReadonlyParamsPanel.test.ts \
       frontend/src/features/device-control/components/__tests__/ControlConsoleWritableParamsPanel.test.ts
```

- [ ] **Step 3: 判断 `ControlConsoleParameterSection.vue` 是否还有引用**

Run: `grep -rn "ControlConsoleParameterSection" frontend/src`
Expected: 无输出（旧面板删除后已无引用）。

若无输出 → 执行下一步删除；若仍有命中（非本计划已删文件）→ 跳过删除，保留该组件。

- [ ] **Step 4: 删除无引用的 `ControlConsoleParameterSection.vue`**

```bash
git rm frontend/src/features/device-control/components/ControlConsoleParameterSection.vue
```

- [ ] **Step 5: 运行受影响范围的测试**

Run: `npx vitest run src/features/device-control src/features/device-monitor/views`
Expected: PASS — 无因删除文件导致的 import 失败。

- [ ] **Step 6: 提交**

```bash
git add -A frontend/src/features/device-control/components
git commit -m "chore(device-control): remove superseded parameter panels"
```

---

### Task 5: 全量验证

**Files:**
- 无代码改动（仅验证；若发现问题则回到对应任务修复并提交）。

- [ ] **Step 1: 运行全量单元测试**

Run: `npm run test:unit`
Expected: PASS — 全部测试通过，无引用 `ControlConsoleReadonlyParamsPanel` / `ControlConsoleWritableParamsPanel` 的残留失败。

- [ ] **Step 2: 运行生产构建**

Run: `npm run build`
Expected: 构建成功，无 TypeScript 报错、无未解析的 import。

- [ ] **Step 3: 浏览器验证（关键路径）**

启动 dev server，进入电容补偿设备的「实时监控 → 参数设置」标签页，确认：
- 仅有一个「参数设置」面板，顶部不再有 6 张只读参数卡片，底部不再有独立「参数修改」面板。
- 头部条显示快照状态 + 时间 + 来源、写入状态 + 角色；设备离线时显示锁定原因。
- 4 个分区表格（投切策略 / 回路配置 / 保护门限 / 通讯参数）每个参数一行；可写参数显示「修改」按钮（离线时置灰），不可写参数显示「写入待开通」。
- 容量展开详情拆为「分相补偿」「公共补偿」两组，可折叠。
- 同样进入 `DeviceControlConsole` 控制台页面，确认参数设置区域渲染一致、无报错。

若浏览器环境不可用，明确说明未做浏览器验证，并以单测 + 构建结果为准。

---

## 验证清单（实施完成后自检）

- [ ] 每个参数在「参数设置」标签页只出现一次（无只读卡片 / 分组 / 修改面板三处重复）。
- [ ] 容量展开详情拆为分相补偿与公共补偿两组，可折叠。
- [ ] 旧组件 `ControlConsoleReadonlyParamsPanel.vue`、`ControlConsoleWritableParamsPanel.vue` 已删除。
- [ ] `ControlConsoleParameterSection.vue` 在确认无引用后已删除（或保留并说明原因）。
- [ ] `npm run test:unit` 与 `npm run build` 均通过。
