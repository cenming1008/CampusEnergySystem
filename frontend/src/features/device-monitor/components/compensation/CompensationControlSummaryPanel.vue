<script setup lang="ts">
import { computed, ref } from 'vue'
import type { PropType } from 'vue'
import type { CompensationProfileItem } from './types'
import { usePanelCollapse } from '@/shared/composables/usePanelCollapse'
import PanelCollapseToggle from '@/shared/components/PanelCollapseToggle.vue'

const props = defineProps({
  summaryItems: {
    type: Array as PropType<CompensationProfileItem[]>,
    default: () => [],
  },
  capacityExpansionItems: {
    type: Array as PropType<CompensationProfileItem[]>,
    default: () => [],
  },
  hasSummaryData: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits<{
  (event: 'open-console'): void
}>()

interface CapacityCircuitGroup {
  label: string
  circuits: CompensationProfileItem[]
}

const { collapsed, toggle } = usePanelCollapse('compensation-monitor:collapse:control-summary', false)
const detailsExpanded = ref(false)

const hiddenSummaryLabels = new Set(['通讯速率'])
const controlSummaryRows = computed(() => {
  const lookup = new Map(props.summaryItems.map(item => [item.label, item.value]))
  const rows: CompensationProfileItem[] = []
  const push = (label: string, value?: string) => {
    if (value && value !== '暂无参数') rows.push({ label, value })
  }

  push('投入功率因数', lookup.get('投入功率因数'))
  push('切除功率因数', lookup.get('切除功率因数'))
  const switchOnDelay = lookup.get('投入延时')
  const switchOffDelay = lookup.get('切除延时')
  if (switchOnDelay || switchOffDelay) {
    push('投入/切除延时', `${switchOnDelay || '--'} / ${switchOffDelay || '--'}`)
  }
  const overvoltage = lookup.get('过压保护门限')
  const temperatureLimit = lookup.get('温度上限门限')
  if (overvoltage || temperatureLimit) {
    push('保护门限', `${overvoltage || '--'} / ${temperatureLimit || '--'}`)
  }

  for (const item of props.summaryItems) {
    if (hiddenSummaryLabels.has(item.label)) continue
    if (rows.some(row => row.label === item.label)) continue
    if (['投入延时', '切除延时', '过压保护门限', '温度上限门限'].includes(item.label)) continue
    if (item.value !== '暂无参数') rows.push(item)
  }

  return rows
})

function parseCapacityTotal(value: string) {
  const matches = value.match(/-?\d+(?:\.\d+)?/g) || []
  return matches.reduce((sum, raw) => sum + Number(raw), 0)
}

function formatCapacityTotal(value: number) {
  return `${value.toFixed(1)} kvar`
}

function parseCapacityValues(value: string) {
  return value.match(/-?\d+(?:\.\d+)?\s*kvar/gi) || []
}

function getCommonCircuitStart(label: string) {
  const range = label.match(/(\d+)\s*-\s*(\d+)/)
  return range ? Number(range[1]) : 1
}

const capacitySummaryItems = computed<CompensationProfileItem[]>(() => {
  const splitTotal = props.capacityExpansionItems
    .filter(item => item.label.includes('分补'))
    .reduce((sum, item) => sum + parseCapacityTotal(item.value), 0)
  const commonTotal = props.capacityExpansionItems
    .filter(item => item.label.includes('公补'))
    .reduce((sum, item) => sum + parseCapacityTotal(item.value), 0)

  return [
    ...(splitTotal > 0 ? [{ label: '分补合计', value: formatCapacityTotal(splitTotal) }] : []),
    ...(commonTotal > 0 ? [{ label: '公补合计', value: formatCapacityTotal(commonTotal) }] : []),
    ...(props.capacityExpansionItems.length
      ? [{ label: '配置完整性', value: `${props.capacityExpansionItems.length} 组已配置` }]
      : []),
  ]
})

const capacityCircuitGroups = computed<CapacityCircuitGroup[]>(() =>
  props.capacityExpansionItems.map(item => {
    const values = parseCapacityValues(item.value)
    const isCommon = item.label.includes('公补')
    const phase = item.label.match(/([ABC])相/)?.[1]
    const start = isCommon ? getCommonCircuitStart(item.label) : 1
    const groupLabel = isCommon ? item.label : `${phase || item.label.replace('分补', '')}相分补`

    return {
      label: groupLabel,
      circuits: values.map((value, index) => ({
        label: isCommon ? `公补回路 ${start + index}` : `${phase || item.label}相回路 ${index + 1}`,
        value,
      })),
    }
  }),
)
</script>

<template>
  <section class="side-panel side-panel--muted control-summary-panel">
    <div class="side-panel__head">
      <div class="control-summary-headline">
        <div class="control-summary-title">
          <h3>控制参数摘要</h3>
          <span class="control-summary-hint">仅展示参数概览</span>
        </div>
        <button
          type="button"
          class="control-summary-console-link"
          aria-label="修改参数"
          title="修改参数"
          @click="emit('open-console')"
        >
          修改参数 →
        </button>
        <PanelCollapseToggle
          :collapsed="collapsed"
          @toggle="toggle"
        />
      </div>
    </div>

    <div
      v-show="!collapsed"
      class="control-summary-body"
    >
      <div
        v-if="hasSummaryData && controlSummaryRows.length"
        class="profile-list"
      >
        <div
          v-for="item in controlSummaryRows"
          :key="item.label"
          class="profile-row"
        >
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>

      <div
        v-if="capacityExpansionItems.length"
        class="capacity-summary"
      >
        <div class="capacity-summary__head">
          <div>
            <strong>容量配置</strong>
            <span>按 JKWF 容量编码与阶梯容量推导</span>
          </div>
          <button
            type="button"
            class="capacity-summary__toggle"
            @click="detailsExpanded = !detailsExpanded"
          >
            {{ detailsExpanded ? '收起明细' : '展开容量明细' }}
          </button>
        </div>

        <div class="capacity-summary-grid">
          <div
            v-for="item in capacitySummaryItems"
            :key="item.label"
            class="capacity-summary-card"
          >
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>

        <div
          v-if="detailsExpanded"
          class="capacity-expansion-list"
        >
          <div
            v-for="group in capacityCircuitGroups"
            :key="group.label"
            class="capacity-circuit-group"
          >
            <span class="capacity-circuit-group__title">{{ group.label }}</span>
            <div class="capacity-circuit-grid">
              <div
                v-for="circuit in group.circuits"
                :key="circuit.label"
                class="capacity-circuit-cell"
              >
                <span>{{ circuit.label }}</span>
                <strong>{{ circuit.value }}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        v-else
        class="control-summary-empty"
      >
        <strong>暂无参数</strong>
        <span>当前设备还没有可回读的 JKWF 参数快照。</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.side-panel {
  padding: 16px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.96), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
}

.side-panel--muted {
  opacity: 0.92;
}

.side-panel__head {
  margin-bottom: 12px;
}

.side-panel__head h3 {
  margin: 0;
  font-size: 15px;
  color: #f5f7fb;
}

.control-summary-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.control-summary-headline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.control-summary-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.control-summary-hint {
  font-size: var(--font-caption);
  color: var(--text-label);
  line-height: 1.4;
}

.control-summary-console-link {
  flex-shrink: 0;
  min-height: var(--touch-target);
  padding: 0;
  border: 0;
  background: transparent;
  color: #60a5fa;
  font-size: var(--font-caption);
  font-weight: 500;
  cursor: pointer;
}

.control-summary-console-link:hover {
  color: #93c5fd;
}

.profile-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.profile-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--divider);
}

.profile-row:last-child {
  border-bottom: none;
}

.profile-row span {
  color: var(--text-label);
  font-size: var(--font-caption);
}

.profile-row strong {
  color: #dfe8f5;
  font-size: var(--font-caption);
  text-align: right;
  max-width: 60%;
  line-height: 1.5;
  word-break: break-word;
}

.control-summary-empty {
  min-height: 92px;
  border: 1px dashed rgba(63, 82, 107, 0.72);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 6px;
  color: #8ea0bc;
  text-align: center;
  padding: 12px;
}

.control-summary-empty strong {
  color: #eef4ff;
}

.capacity-summary {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed rgba(93, 115, 145, 0.35);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.capacity-summary__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}

.capacity-summary__head strong {
  color: #edf3ff;
  font-size: 13px;
}

.capacity-summary__head span {
  display: block;
  margin-top: 3px;
  color: var(--text-label);
  font-size: var(--font-caption);
}

.capacity-summary__toggle {
  flex: 0 0 auto;
  padding: 0;
  border: 0;
  background: transparent;
  color: #60a5fa;
  font-size: var(--font-caption);
  font-weight: 700;
  cursor: pointer;
}

.capacity-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.capacity-summary-card {
  padding: 10px;
  border-radius: 10px;
  background: rgba(9, 18, 30, 0.62);
  border: 1px solid rgba(48, 67, 91, 0.7);
}

.capacity-summary-card span {
  display: block;
  color: var(--text-label);
  font-size: var(--font-caption);
  margin-bottom: 5px;
}

.capacity-summary-card strong {
  color: #f5f7fb;
  font-size: 13px;
  line-height: 1.45;
}

.capacity-expansion-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.capacity-circuit-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(60, 79, 103, 0.6);
  background: rgba(18, 28, 42, 0.82);
}

.capacity-circuit-group__title {
  color: var(--text-label);
  font-size: var(--font-caption);
  font-weight: 700;
}

.capacity-circuit-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.capacity-circuit-cell {
  min-width: 0;
  padding: 8px;
  border-radius: 8px;
  background: rgba(7, 15, 25, 0.58);
  border: 1px solid rgba(50, 70, 96, 0.58);
}

.capacity-circuit-cell span {
  display: block;
  margin-bottom: 4px;
  color: var(--text-label);
  font-size: 11px;
  line-height: 1.35;
}

.capacity-circuit-cell strong {
  color: #f5f7fb;
  font-size: var(--font-caption);
  line-height: 1.5;
}

.control-summary-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
