<script setup lang="ts">
import { computed, type PropType } from 'vue'
import type {
  CompensationCapacitorBankTelemetry,
  CompensationSvgTelemetry,
} from '@/api/compensation'
import type { CompensationMetric } from './types'
import CompensationMetricStrip from './CompensationMetricStrip.vue'

const props = defineProps({
  svgTelemetry: {
    type: Object as PropType<CompensationSvgTelemetry | null>,
    default: null,
  },
  capacitorBankTelemetry: {
    type: Object as PropType<CompensationCapacitorBankTelemetry | null>,
    default: null,
  },
  isCapacitorBank: {
    type: Boolean,
    default: false,
  },
  measurementMetrics: {
    type: Array as PropType<CompensationMetric[]>,
    default: () => [],
  },
})

// 优先展示 JKWF-LCD 数据，回退到 SVG 数据
const activeData = computed(() => props.capacitorBankTelemetry ?? props.svgTelemetry)
const showPower = computed(() => props.isCapacitorBank || !!props.capacitorBankTelemetry)

function fmt(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined) return '--'
  return Number(value).toFixed(digits)
}

function subtitle(): string {
  if (props.capacitorBankTelemetry) return '当前三相电压、电流与功率分布'
  if (props.svgTelemetry) return '当前三相电气量与补偿输出'
  return '当前实时快照'
}

const phaseRows = computed(() => {
  const d = activeData.value
  const cb = props.capacitorBankTelemetry
  return [
    { phase: 'A', accent: '#60a5fa', voltage: d?.voltage_a, current: d?.current_a, activePower: cb?.active_power_a, reactivePower: cb?.reactive_power_a, apparentPower: cb?.apparent_power_a, powerFactor: cb?.power_factor_a },
    { phase: 'B', accent: '#fbbf24', voltage: d?.voltage_b, current: d?.current_b, activePower: cb?.active_power_b, reactivePower: cb?.reactive_power_b, apparentPower: cb?.apparent_power_b, powerFactor: cb?.power_factor_b },
    { phase: 'C', accent: '#f87171', voltage: d?.voltage_c, current: d?.current_c, activePower: cb?.active_power_c, reactivePower: cb?.reactive_power_c, apparentPower: cb?.apparent_power_c, powerFactor: cb?.power_factor_c },
  ]
})
</script>

<template>
  <section class="threephase-panel">
    <div class="threephase-panel__head">
      <h3>三相电气快照</h3>
      <span>{{ subtitle() }}</span>
    </div>

    <div
      v-if="measurementMetrics.length"
      class="threephase-panel__measurements"
    >
      <span class="threephase-panel__section-label">母线测量值</span>
      <CompensationMetricStrip
        :items="measurementMetrics"
        :columns="6"
      />
    </div>

    <div
      class="phase-table"
      :class="{ 'phase-table--full': showPower }"
    >
      <div class="phase-table__head">
        <span>相</span>
        <span>电压 (V)</span>
        <span>电流 (A)</span>
        <template v-if="showPower">
          <span>有功 (kW)</span>
          <span>无功 (kvar)</span>
          <span>视在 (kVA)</span>
          <span>功率因数</span>
        </template>
      </div>
      <div
        v-for="row in phaseRows"
        :key="row.phase"
        class="phase-table__row"
        :style="{ '--phase-accent': row.accent }"
      >
        <span class="phase-table__phase">{{ row.phase }} 相</span>
        <span>{{ fmt(row.voltage) }}</span>
        <span>{{ fmt(row.current) }}</span>
        <template v-if="showPower">
          <span>{{ fmt(row.activePower) }}</span>
          <span>{{ fmt(row.reactivePower) }}</span>
          <span>{{ fmt(row.apparentPower) }}</span>
          <span>{{ fmt(row.powerFactor, 3) }}</span>
        </template>
      </div>
    </div>
  </section>
</template>

<style scoped>
.threephase-panel {
  padding: 18px 20px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.95), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
}

.threephase-panel__head {
  margin-bottom: 16px;
}

.threephase-panel__head h3 {
  margin: 0;
  font-size: 15px;
  color: #f5f7fb;
}

.threephase-panel__head span {
  display: block;
  margin-top: 4px;
  color: #8ea0bc;
  font-size: 12px;
}

.threephase-panel__measurements {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.threephase-panel__section-label {
  font-size: 12px;
  color: #8ea0bc;
}

.phase-table {
  background: rgba(22, 36, 55, 0.6);
  border: 1px solid rgba(53, 72, 97, 0.5);
  border-radius: 10px;
  overflow: hidden;
}

.phase-table__head,
.phase-table__row {
  display: grid;
  grid-template-columns: 56px repeat(2, 1fr);
  align-items: center;
}

.phase-table--full .phase-table__head,
.phase-table--full .phase-table__row {
  grid-template-columns: 56px repeat(6, 1fr);
}

.phase-table__head {
  padding: 8px 12px;
  background: rgba(30, 48, 70, 0.8);
  font-size: var(--font-caption);
  color: var(--text-label);
  font-weight: 600;
  text-align: right;
}

.phase-table__head span:first-child {
  text-align: left;
}

.phase-table__row {
  padding: 10px 12px;
  font-size: 13px;
  color: #e2ecf9;
  text-align: right;
  border-top: 1px solid rgba(41, 57, 77, 0.4);
  border-left: 3px solid var(--phase-accent, transparent);
  font-family: 'DIN Alternate', 'DIN', 'SFMono-Regular', monospace;
  font-variant-numeric: tabular-nums;
}

.phase-table__phase {
  text-align: left;
  color: var(--phase-accent, #7f93b2);
}
</style>
