<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { PropType } from 'vue'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'
import { useECharts } from '@/shared/composables/useECharts'
import MiniSparkline from './MiniSparkline.vue'

const props = defineProps({
  telemetry: {
    type: Object as PropType<CompensationCapacitorBankTelemetry | null>,
    default: null,
  },
  history: {
    type: Array as PropType<CompensationCapacitorBankTelemetry[]>,
    default: () => [],
  },
})

type Status = 'ok' | 'warn' | 'crit' | 'na'
type ViewMode = 'grid' | 'combined'

interface SubSeries {
  label: string
  data: Array<number | null>
  color: string
}

interface MetricSpec {
  key: string
  title: string
  sub: string
  unit: string
  series: SubSeries[]
  domain?: [number, number]
  refValue?: number
  currentValues: Array<string>
  status: Status
  delta: string
}

const viewMode = ref<ViewMode>('grid')

function num(v: number | null | undefined, digits = 1): string {
  return typeof v === 'number' && Number.isFinite(v) ? v.toFixed(digits) : '—'
}

function avg3(a?: number | null, b?: number | null, c?: number | null): number | null {
  const vs = [a, b, c].filter((v): v is number => typeof v === 'number' && Number.isFinite(v))
  return vs.length ? vs.reduce((s, v) => s + v, 0) / vs.length : null
}

function sum3(a?: number | null, b?: number | null, c?: number | null): number | null {
  const vs = [a, b, c].filter((v): v is number => typeof v === 'number' && Number.isFinite(v))
  return vs.length ? vs.reduce((s, v) => s + v, 0) : null
}

function maxOf(values: Array<number | null>): number | null {
  const vs = values.filter((v): v is number => v !== null)
  return vs.length ? Math.max(...vs) : null
}

function imbalancePct(a?: number | null, b?: number | null, c?: number | null): number | null {
  const m = avg3(a, b, c)
  if (m == null || m === 0) return null
  const vs = [a, b, c].filter((v): v is number => typeof v === 'number')
  const dev = Math.max(...vs.map((v) => Math.abs(v - m)))
  return (dev / m) * 100
}

const metrics = computed<MetricSpec[]>(() => {
  const t = props.telemetry
  const h = props.history

  const va = h.map((r) => r.voltage_a ?? null)
  const vb = h.map((r) => r.voltage_b ?? null)
  const vc = h.map((r) => r.voltage_c ?? null)
  const ia = h.map((r) => r.current_a ?? null)
  const ib = h.map((r) => r.current_b ?? null)
  const ic = h.map((r) => r.current_c ?? null)
  const pfHist = h.map((r) => avg3(r.power_factor_a, r.power_factor_b, r.power_factor_c))
  const qHist = h.map((r) => sum3(r.reactive_power_a, r.reactive_power_b, r.reactive_power_c))
  const pHist = h.map((r) => sum3(r.active_power_a, r.active_power_b, r.active_power_c))
  const thduA = h.map((r) => r.voltage_thd_a ?? null)
  const thduB = h.map((r) => r.voltage_thd_b ?? null)
  const thduC = h.map((r) => r.voltage_thd_c ?? null)
  const thdiA = h.map((r) => r.current_harmonic_a ?? null)
  const thdiB = h.map((r) => r.current_harmonic_b ?? null)
  const thdiC = h.map((r) => r.current_harmonic_c ?? null)
  const tempHist = h.map((r) => r.temperature ?? null)

  const voltImb = t ? imbalancePct(t.voltage_a, t.voltage_b, t.voltage_c) : null
  const currImb = t ? imbalancePct(t.current_a, t.current_b, t.current_c) : null
  const pfNow = t ? avg3(t.power_factor_a, t.power_factor_b, t.power_factor_c) : null
  const qNow = t ? sum3(t.reactive_power_a, t.reactive_power_b, t.reactive_power_c) : null
  const pNow = t ? sum3(t.active_power_a, t.active_power_b, t.active_power_c) : null
  const tempNow = t?.temperature ?? null
  const maxThdu = maxOf([t?.voltage_thd_a ?? null, t?.voltage_thd_b ?? null, t?.voltage_thd_c ?? null])
  const maxThdi = maxOf([t?.current_harmonic_a ?? null, t?.current_harmonic_b ?? null, t?.current_harmonic_c ?? null])

  return [
    {
      key: 'voltage',
      title: '三相电压',
      sub: '相电压 · L-N',
      unit: 'V',
      currentValues: [num(t?.voltage_a, 1), num(t?.voltage_b, 1), num(t?.voltage_c, 1)],
      status: voltImb == null ? 'na' : voltImb < 2 ? 'ok' : 'warn',
      delta: voltImb == null ? '—' : `不平衡 ${voltImb.toFixed(1)}%`,
      series: [
        { label: 'A', data: va, color: '#3d8bff' },
        { label: 'B', data: vb, color: '#22d3ee' },
        { label: 'C', data: vc, color: '#a78bfa' },
      ],
    },
    {
      key: 'current',
      title: '三相电流',
      sub: '负载电流',
      unit: 'A',
      currentValues: [num(t?.current_a, 1), num(t?.current_b, 1), num(t?.current_c, 1)],
      status: currImb == null ? 'na' : currImb < 5 ? 'ok' : 'warn',
      delta: currImb == null ? '—' : `不平衡 ${currImb.toFixed(1)}%`,
      series: [
        { label: 'A', data: ia, color: '#3d8bff' },
        { label: 'B', data: ib, color: '#22d3ee' },
        { label: 'C', data: ic, color: '#a78bfa' },
      ],
    },
    {
      key: 'pf',
      title: '功率因数 PF',
      sub: '三相均值',
      unit: '',
      currentValues: [num(pfNow, 3)],
      status: pfNow == null ? 'na' : pfNow >= 0.95 ? 'ok' : 'warn',
      delta: pfNow == null ? '—' : pfNow >= 0.95 ? '达标' : `差 ${(0.95 - pfNow).toFixed(3)}`,
      domain: [0.8, 1.0],
      refValue: 0.95,
      series: [{ label: 'PF', data: pfHist, color: '#34d399' }],
    },
    {
      key: 'q',
      title: '无功功率 Q',
      sub: 'kVar · 三相合计',
      unit: 'kVar',
      currentValues: [num(qNow, 1)],
      status: qNow == null ? 'na' : Math.abs(qNow) <= 50 ? 'ok' : 'warn',
      delta: qNow == null ? '—' : `残余 ${qNow.toFixed(0)}`,
      series: [{ label: 'Q', data: qHist, color: '#22d3ee' }],
    },
    {
      key: 'p',
      title: '有功功率 P',
      sub: 'kW · 三相合计',
      unit: 'kW',
      currentValues: [num(pNow, 1)],
      status: pNow == null ? 'na' : 'ok',
      delta: pNow == null ? '—' : `当前 ${pNow.toFixed(0)} kW`,
      series: [{ label: 'P', data: pHist, color: '#3d8bff' }],
    },
    {
      key: 'thdu',
      title: 'THDu',
      sub: '电压总畸变',
      unit: '%',
      currentValues: [num(t?.voltage_thd_a, 2), num(t?.voltage_thd_b, 2), num(t?.voltage_thd_c, 2)],
      status: maxThdu == null ? 'na' : maxThdu < 5 ? 'ok' : 'warn',
      delta: maxThdu == null ? '—' : maxThdu < 5 ? `余量 ${(5 - maxThdu).toFixed(2)}%` : `越限 ${(maxThdu - 5).toFixed(2)}%`,
      domain: [0, 5],
      refValue: 5,
      series: [
        { label: 'A', data: thduA, color: '#3d8bff' },
        { label: 'B', data: thduB, color: '#22d3ee' },
        { label: 'C', data: thduC, color: '#a78bfa' },
      ],
    },
    {
      key: 'thdi',
      title: 'THDi',
      sub: '电流总畸变',
      unit: '%',
      currentValues: [num(t?.current_harmonic_a, 2), num(t?.current_harmonic_b, 2), num(t?.current_harmonic_c, 2)],
      status: maxThdi == null ? 'na' : maxThdi < 8 ? 'ok' : 'warn',
      delta: maxThdi == null ? '—' : maxThdi < 8 ? `余量 ${(8 - maxThdi).toFixed(2)}%` : `超 ${(maxThdi - 8).toFixed(2)}%`,
      domain: [0, 12],
      refValue: 8,
      series: [
        { label: 'A', data: thdiA, color: '#3d8bff' },
        { label: 'B', data: thdiB, color: '#22d3ee' },
        { label: 'C', data: thdiC, color: '#a78bfa' },
      ],
    },
    {
      key: 'temp',
      title: '柜温',
      sub: '机芯温度',
      unit: '℃',
      currentValues: [num(tempNow, 1)],
      status: tempNow == null ? 'na' : tempNow < 55 ? 'ok' : tempNow < 65 ? 'warn' : 'crit',
      delta: tempNow == null ? '—' : tempNow < 55 ? '正常' : tempNow < 65 ? '偏高' : '越限',
      domain: [25, 70],
      refValue: 65,
      series: [{ label: '温度', data: tempHist, color: '#a78bfa' }],
    },
  ]
})

// === large-chart selection ===
const selectedKey = ref('voltage')

function selectMetric(key: string) {
  selectedKey.value = key
}

const chart = useECharts()
const xLabels = computed(() =>
  props.history.map((row, i) => {
    if (!row?.timestamp) return `${i}`
    const d = new Date(row.timestamp)
    if (Number.isNaN(d.getTime())) return `${i}`
    return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  }),
)

const combinedSelectedMetrics = computed(() => {
  const metric = metrics.value.find((m) => m.key === selectedKey.value) ?? metrics.value[0]
  return metric ? [metric] : []
})

const combinedSeriesEmpty = computed(() =>
  combinedSelectedMetrics.value.every((m) =>
    m.series.every((s) => s.data.every((v) => v == null)),
  ),
)

async function renderCombinedChart() {
  if (viewMode.value !== 'combined') return
  const selected = combinedSelectedMetrics.value
  const yAxis = selected.slice(0, 2).map((m, i) => ({
    type: 'value' as const,
    name: m.unit || m.title,
    position: (i === 0 ? 'left' : 'right') as 'left' | 'right',
    min: m.domain?.[0],
    max: m.domain?.[1],
    axisLine: { lineStyle: { color: '#314055' } },
    axisLabel: { color: '#8ea0bc', fontSize: 11 },
    nameTextStyle: { color: '#8ea0bc', fontSize: 11 },
    splitLine: {
      lineStyle: { color: i === 0 ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0)' },
    },
  }))

  const series: any[] = []
  selected.forEach((m, mi) => {
    const axisIdx = Math.min(mi, 1)
    m.series.forEach((sub) => {
      series.push({
        name: selected.length > 1 ? `${m.title} · ${sub.label}` : sub.label,
        type: 'line',
        smooth: true,
        showSymbol: false,
        yAxisIndex: axisIdx,
        data: sub.data,
        lineStyle: { color: sub.color, width: 2 },
        itemStyle: { color: sub.color },
      })
    })
  })

  await chart.setOptions(
    {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(11, 19, 30, 0.96)',
        borderColor: '#314055',
        textStyle: { color: '#dfe8f5' },
      },
      legend: {
        show: series.length > 1,
        textStyle: { color: '#9fb1ca', fontSize: 11 },
        top: 4,
      },
      grid: { left: 12, right: 16, top: 36, bottom: 8, containLabel: true },
      xAxis: {
        type: 'category',
        data: xLabels.value,
        axisLine: { lineStyle: { color: '#314055' } },
        axisLabel: { color: '#8ea0bc', fontSize: 11 },
      },
      yAxis,
      series,
    },
    { notMerge: true },
  )
}

watch([viewMode, selectedKey, () => props.history], () => {
  void renderCombinedChart()
}, { deep: true })

watch(() => chart.chartRef.value, async () => {
  if (!chart.chartRef.value) return
  await chart.initChart()
  await renderCombinedChart()
})
</script>

<template>
  <section class="metric-grid">
    <div class="metric-grid__head">
      <div class="metric-grid__title-wrap">
        <div class="metric-grid__title"><span class="rt-accent" />历史趋势 · 全指标</div>
        <div class="metric-grid__sub">
          {{ viewMode === 'grid' ? '小图同屏对比' : '点击下方指标切换单指标大图' }}
        </div>
      </div>
      <div class="metric-grid__toggle" role="tablist" aria-label="趋势视图">
        <button
          type="button"
          class="metric-grid__toggle-btn"
          :class="{ 'is-active': viewMode === 'grid' }"
          role="tab"
          :aria-selected="viewMode === 'grid'"
          @click="viewMode = 'grid'"
        >
          网格
        </button>
        <button
          type="button"
          class="metric-grid__toggle-btn"
          :class="{ 'is-active': viewMode === 'combined' }"
          role="tab"
          :aria-selected="viewMode === 'combined'"
          @click="viewMode = 'combined'"
        >
          大图
        </button>
      </div>
    </div>

    <div v-if="viewMode === 'grid'" class="metric-grid__cards">
      <div
        v-for="card in metrics"
        :key="card.key"
        class="metric-card"
        :class="[`metric-card--${card.status}`]"
      >
        <div class="metric-card__head">
          <div class="metric-card__title-wrap">
            <div class="metric-card__title">{{ card.title }}</div>
            <div class="metric-card__sub">{{ card.sub }}</div>
          </div>
          <span class="metric-card__status-dot" :class="[`metric-card__status-dot--${card.status}`]" />
        </div>
        <div class="metric-card__values">
          <div
            v-for="(v, i) in card.currentValues"
            :key="i"
            class="metric-card__value"
          >
            <span
              class="metric-card__value-dot"
              :style="{ background: card.series[i]?.color || card.series[0]?.color || '#3d8bff' }"
            />
            <span class="mono">{{ v }}</span>
            <span v-if="card.unit && i === card.currentValues.length - 1" class="metric-card__unit">
              {{ card.unit }}
            </span>
          </div>
        </div>
        <div class="metric-card__spark">
          <div
            v-for="(series, i) in card.series"
            :key="series.label"
            class="metric-card__spark-layer"
            :style="i > 0 ? { position: 'absolute', inset: 0 } : null"
          >
            <MiniSparkline
              :data="series.data"
              :color="series.color"
              :height="56"
              :domain="card.domain"
              :ref-value="i === 0 ? card.refValue ?? null : null"
              :area="i === 0"
            />
          </div>
        </div>
        <div class="metric-card__foot">
          <div class="metric-card__legend">
            <span v-for="series in card.series" :key="series.label" class="metric-card__legend-item">
              <span class="metric-card__legend-dot" :style="{ background: series.color }" />
              {{ series.label }}
            </span>
          </div>
          <span class="metric-card__delta" :class="[`metric-card__delta--${card.status}`]">
            {{ card.delta }}
          </span>
        </div>
      </div>
    </div>

    <div v-else class="metric-grid__combined">
      <div class="metric-grid__chips" role="group" aria-label="选择指标">
        <button
          v-for="m in metrics"
          :key="m.key"
          type="button"
          class="metric-grid__chip"
          :class="{ 'is-active': selectedKey === m.key }"
          :aria-pressed="selectedKey === m.key"
          @click="selectMetric(m.key)"
        >
          <span
            class="metric-grid__chip-dot"
            :style="{ background: m.series[0]?.color || '#3d8bff' }"
          />
          {{ m.title }}
          <span v-if="m.unit" class="metric-grid__chip-unit">{{ m.unit }}</span>
        </button>
      </div>
      <div
        v-if="combinedSeriesEmpty"
        class="metric-grid__empty"
      >
        暂无历史采样数据
      </div>
      <div
        v-show="!combinedSeriesEmpty"
        :ref="chart.chartRef"
        class="metric-grid__chart"
      />
    </div>
  </section>
</template>

<style scoped>
.metric-grid {
  background: #121d2e;
  border: 1px solid #1f2c41;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.metric-grid__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 9px 14px;
  border-bottom: 1px solid #1f2c41;
}

.metric-grid__title-wrap { min-width: 0; }

.metric-grid__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #e5edf7;
}

.rt-accent {
  width: 3px;
  height: 12px;
  border-radius: 2px;
  background: #22d3ee;
  flex: 0 0 auto;
}

.metric-grid__sub {
  font-size: 11px;
  color: #5e6c83;
  margin-top: 3px;
  padding-left: 11px;
}

.metric-grid__toggle {
  display: inline-flex;
  background: #0b1623;
  border: 1px solid #1f2c41;
  border-radius: 6px;
  padding: 2px;
  flex-shrink: 0;
}

.metric-grid__toggle-btn {
  background: transparent;
  border: none;
  padding: 3px 11px;
  font-size: 11px;
  color: #9aa7bd;
  cursor: pointer;
  border-radius: 4px;
  font: inherit;
}

.metric-grid__toggle-btn.is-active {
  background: rgba(34, 211, 238, 0.13);
  color: #e5edf7;
}

.metric-grid__cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  padding: 12px 14px 14px;
}

@media (max-width: 900px) {
  .metric-grid__cards { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}

@media (max-width: 900px) {
  .metric-grid__cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

.metric-card {
  background: #0b1623;
  border: 1px solid #1f2c41;
  border-radius: 6px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.metric-card--warn { border-color: rgba(251, 191, 36, 0.45); }
.metric-card--crit { border-color: rgba(248, 113, 113, 0.5); }

.metric-card__head { display: flex; justify-content: space-between; align-items: flex-start; }
.metric-card__title-wrap { min-width: 0; }
.metric-card__title {
  font-size: 12px;
  font-weight: 600;
  color: #e5edf7;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.metric-card__sub {
  font-size: 10px;
  color: #5e6c83;
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.metric-card__status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-top: 6px;
}
.metric-card__status-dot--ok { background: #34d399; }
.metric-card__status-dot--warn { background: #fbbf24; }
.metric-card__status-dot--crit { background: #f87171; }
.metric-card__status-dot--na { background: #5d7197; }

.metric-card__values {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.metric-card__value {
  display: flex;
  align-items: baseline;
  gap: 3px;
  font-size: 15px;
  font-weight: 600;
  color: #e5edf7;
  font-variant-numeric: tabular-nums;
}

.metric-card__value-dot {
  width: 5px;
  height: 5px;
  border-radius: 2px;
  align-self: center;
  margin-right: 4px;
}

.metric-card__unit { font-size: 10px; color: #5e6c83; }

.mono {
  font-family: inherit;
  font-feature-settings: normal;
}

.metric-card__spark {
  position: relative;
  height: 56px;
  margin-top: 4px;
}

.metric-card__spark-layer { position: relative; }

.metric-card__foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 9.5px;
  color: #5e6c83;
}

.metric-card__legend { display: flex; gap: 8px; }
.metric-card__legend-item { display: inline-flex; align-items: center; gap: 3px; }
.metric-card__legend-dot { width: 5px; height: 5px; border-radius: 2px; display: inline-block; }

.metric-card__delta { font-weight: 500; }
.metric-card__delta--ok { color: #34d399; }
.metric-card__delta--warn { color: #fbbf24; }
.metric-card__delta--crit { color: #f87171; }
.metric-card__delta--na { color: #5e6c83; }

/* combined-mode */
.metric-grid__combined {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 14px 14px;
}

.metric-grid__chips { display: flex; flex-wrap: wrap; gap: 8px; }

.metric-grid__chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 9px;
  border-radius: 5px;
  border: 1px solid #1f2c41;
  background: #0b1623;
  color: #9aa7bd;
  font: inherit;
  font-size: 11px;
  cursor: pointer;
  transition: border-color 0.16s, background 0.16s, color 0.16s;
}

.metric-grid__chip:hover { border-color: rgba(34, 211, 238, 0.36); color: #dbeafe; }

.metric-grid__chip.is-active {
  border-color: rgba(34, 211, 238, 0.42);
  background: rgba(34, 211, 238, 0.1);
  color: #e5edf7;
}

.metric-grid__chip-dot { width: 7px; height: 7px; border-radius: 2px; display: inline-block; }
.metric-grid__chip-unit { color: #5e6c83; margin-left: 2px; font-size: 10px; }

.metric-grid__empty {
  height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #5e6c83;
  font-size: 12px;
}

.metric-grid__chart {
  width: 100%;
  height: 320px;
}
</style>
