<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useECharts } from '@/shared/composables/useECharts'
import type {
  CompensationCapacitorBankControlProfile,
  CompensationCapacitorBankTelemetry,
} from '@/api/compensation'
import {
  buildHarmonicSpectrumView,
  getHarmonicSpectrumYAxisMax,
} from './viewMapping'
import type {
  HarmonicSpectrumKind,
  HarmonicSpectrumPhase,
} from './types'

const props = defineProps<{
  telemetry: CompensationCapacitorBankTelemetry | null | undefined
  controlProfile: CompensationCapacitorBankControlProfile | null | undefined
}>()

const chart = useECharts()
const activeKind = ref<HarmonicSpectrumKind>('voltage')
const activePhase = ref<HarmonicSpectrumPhase>('a')
const multiPhase = ref(false)

const kindOptions = [
  { label: '电压谐波', value: 'voltage' },
  { label: '电流谐波', value: 'current' },
]
const phaseOptions = [
  { label: 'A相', value: 'a' },
  { label: 'B相', value: 'b' },
  { label: 'C相', value: 'c' },
  { label: '三相', value: 'all' },
]

function handlePhaseChange(value: string) {
  if (value === 'all') {
    multiPhase.value = true
  } else {
    multiPhase.value = false
    activePhase.value = value as HarmonicSpectrumPhase
  }
}

const phaseSegmentedValue = computed(() => (multiPhase.value ? 'all' : activePhase.value))

const PHASES: HarmonicSpectrumPhase[] = ['a', 'b', 'c']
const PHASE_COLORS: Record<HarmonicSpectrumPhase, string> = {
  a: '#60a5fa',
  b: '#22d3ee',
  c: '#a78bfa',
}

const model = computed(() =>
  buildHarmonicSpectrumView({
    activeKind: activeKind.value,
    activePhase: activePhase.value,
    telemetry: props.telemetry,
    controlProfile: props.controlProfile,
  }),
)

const multiPhaseModels = computed(() =>
  PHASES.map((phase) => ({
    phase,
    model: buildHarmonicSpectrumView({
      activeKind: activeKind.value,
      activePhase: phase,
      telemetry: props.telemetry,
      controlProfile: props.controlProfile,
    }),
  })),
)

function formatNumber(value: number | null | undefined, digits = 1) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return '暂无数据'
  return Number(value).toFixed(digits)
}

async function renderChart() {
  // 门限线固定，y轴保持静态范围
  const staticMax = getHarmonicSpectrumYAxisMax(activeKind.value)

  if (multiPhase.value) {
    const phaseModels = multiPhaseModels.value
    const orders = phaseModels[0].model.bars.map((bar) => `${bar.order}次`)
    const threshold = phaseModels[0].model.threshold
    const unit = phaseModels[0].model.unit
    const kindLabel = phaseModels[0].model.summary.kindLabel

    await chart.setOptions({
      backgroundColor: 'transparent',
      animation: false,
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(11, 19, 30, 0.96)',
        borderColor: '#314055',
        textStyle: { color: '#dfe8f5' },
        formatter: (params: any) => {
          const arr = Array.isArray(params) ? params : [params]
          if (!arr.length) return ''
          const order = arr[0]?.axisValue || ''
          const lines = arr.map((p: any) => {
            const d = p.data || {}
            const txt = d.placeholder ? '暂无数据' : `${Number(d.value).toFixed(2)} ${unit}`
            return `<span style="color:${p.color}">●</span> ${p.seriesName}: ${txt}`
          })
          return `${order}<br/>${lines.join('<br/>')}`
        },
      },
      legend: {
        show: true,
        textStyle: { color: '#9fb1ca', fontSize: 11 },
        top: 4,
      },
      grid: { left: 12, right: 16, top: 36, bottom: 8, containLabel: true },
      xAxis: {
        type: 'category',
        data: orders,
        axisLine: { lineStyle: { color: '#314055' } },
        axisLabel: { color: '#8ea0bc', fontSize: 10 },
      },
      yAxis: {
        type: 'value',
        name: unit,
        nameTextStyle: { color: '#8ea0bc', padding: [0, 0, 0, 4] },
        axisLabel: { color: '#8ea0bc', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
        min: 0,
        max: staticMax,
      },
      series: phaseModels.map(({ phase, model: m }, idx) => ({
        type: 'bar',
        name: `${phase.toUpperCase()}相 ${kindLabel}`,
        barMaxWidth: 10,
        barGap: '20%',
        itemStyle: {
          color: PHASE_COLORS[phase],
          borderRadius: [3, 3, 0, 0],
        },
        data: m.bars.map((bar) => ({
          ...bar,
          value: bar.placeholder ? staticMax * 0.02 : bar.value,
          itemStyle: {
            color: bar.placeholder
              ? `${PHASE_COLORS[phase]}33`
              : (bar.exceeded ? '#fb7185' : PHASE_COLORS[phase]),
            borderRadius: [3, 3, 0, 0],
          },
        })),
        markLine: idx === 0 && threshold !== null
          ? {
              symbol: 'none',
              animation: false,
              label: { color: '#fbbf24', formatter: '门限', position: 'insideEndBottom' },
              lineStyle: { color: '#fbbf24', type: 'dashed' },
              data: [{ yAxis: threshold }],
            }
          : undefined,
      })),
    }, { notMerge: true })
    return
  }

  await chart.setOptions({
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(11, 19, 30, 0.96)',
      borderColor: '#314055',
      textStyle: { color: '#dfe8f5' },
      formatter: (params: any) => {
        const item = Array.isArray(params) ? params[0] : params
        const data = item?.data
        if (!data) return ''
        if (data.placeholder) {
          return `${data.order}次<br/>暂无数据`
        }
        return `${data.order}次<br/>${model.value.summary.phaseLabel}${model.value.summary.kindLabel}: ${Number(data.value).toFixed(2)} ${model.value.unit}`
      },
    },
    grid: { left: 12, right: 16, top: 32, bottom: 8, containLabel: true },
    xAxis: {
      type: 'category',
      data: model.value.bars.map((bar) => `${bar.order}次`),
      axisLine: { lineStyle: { color: '#314055' } },
      axisLabel: { color: '#8ea0bc', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      name: model.value.unit,
      nameTextStyle: { color: '#8ea0bc', padding: [0, 0, 0, 4] },
      axisLabel: { color: '#8ea0bc', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
      min: 0,
      max: staticMax,
    },
    series: [
      {
        type: 'bar',
        name: model.value.summary.kindLabel,
        barMaxWidth: 18,
        data: model.value.bars.map((bar) => ({
          ...bar,
          value: bar.placeholder ? staticMax * 0.02 : bar.value,
          itemStyle: {
            color: bar.placeholder
              ? 'rgba(96, 165, 250, 0.18)'
              : (bar.exceeded ? '#fb7185' : '#60a5fa'),
            borderRadius: [4, 4, 0, 0],
          },
        })),
        markLine: model.value.threshold !== null
          ? {
              symbol: 'none',
              animation: false,
              label: { color: '#fbbf24', formatter: '门限', position: 'insideEndBottom' },
              lineStyle: { color: '#fbbf24', type: 'dashed' },
              data: [{ yAxis: model.value.threshold }],
            }
          : undefined,
      },
    ],
  }, { notMerge: true })
}

watch(model, () => {
  void renderChart()
}, { deep: true })

watch(multiPhase, () => {
  void renderChart()
})

watch(multiPhaseModels, () => {
  if (multiPhase.value) void renderChart()
}, { deep: true })

watch(() => chart.chartRef.value, async () => {
  if (!chart.chartRef.value) return
  await chart.initChart()
  await renderChart()
})
</script>

<template>
  <section class="spectrum-panel">
    <div class="spectrum-panel__head">
      <div>
        <h3><span class="rt-accent" />高次谐波频谱</h3>
        <span>展示最新采样的 2~31 次谐波分布。</span>
      </div>
      <div class="spectrum-panel__controls">
        <el-segmented
          :model-value="activeKind"
          :options="kindOptions"
          size="small"
          @change="activeKind = $event as HarmonicSpectrumKind"
        />
        <el-segmented
          :model-value="phaseSegmentedValue"
          :options="phaseOptions"
          size="small"
          @change="handlePhaseChange($event as string)"
        />
      </div>
    </div>

    <div v-if="!multiPhase" class="spectrum-panel__summary">
      <span>{{ model.summary.phaseLabel }} {{ model.summary.kindLabel }}</span>
      <span>最高 {{ model.summary.peakOrder ? `${model.summary.peakOrder}次` : '暂无数据' }}</span>
      <span>{{ formatNumber(model.summary.peakValue) }} {{ model.unit }}</span>
      <span>门限 {{ model.threshold === null ? '未配置' : `${formatNumber(model.threshold)} ${model.unit}` }}</span>
      <el-tag
        size="small"
        :type="model.summary.statusTone === 'danger' ? 'danger' : model.summary.statusTone === 'success' ? 'success' : 'info'"
        effect="plain"
      >
        {{ model.summary.statusText }}
      </el-tag>
    </div>
    <div v-else class="spectrum-panel__summary">
      <span
        v-for="entry in multiPhaseModels"
        :key="entry.phase"
        class="spectrum-panel__phase-summary"
      >
        <i :style="{ background: PHASE_COLORS[entry.phase] }" />
        {{ entry.phase.toUpperCase() }}相 · 峰
        {{ entry.model.summary.peakOrder ? `${entry.model.summary.peakOrder}次` : '—' }}
        {{ formatNumber(entry.model.summary.peakValue) }} {{ entry.model.unit }}
      </span>
      <span>
        门限
        {{ multiPhaseModels[0].model.threshold === null ? '未配置'
          : `${formatNumber(multiPhaseModels[0].model.threshold)} ${multiPhaseModels[0].model.unit}` }}
      </span>
    </div>

    <div class="spectrum-panel__chart-wrap">
      <div
        :ref="chart.chartRef"
        class="spectrum-panel__chart"
      />
      <div
        v-if="model.empty"
        class="spectrum-panel__empty-overlay"
      >
        {{ model.emptyText }}
      </div>
    </div>
  </section>
</template>

<style scoped>
.spectrum-panel {
  background: #121d2e;
  border: 1px solid #1f2c41;
  border-radius: 10px;
  min-width: 0;
}

.spectrum-panel__head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding: 9px 14px;
  border-bottom: 1px solid #1f2c41;
}

.spectrum-panel__head h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  color: #e5edf7;
}

.spectrum-panel__head span,
.spectrum-panel__summary {
  color: #5e6c83;
  font-size: 11px;
}

.spectrum-panel__head h3 + span {
  display: block;
  margin-top: 3px;
  padding-left: 11px;
}

.rt-accent {
  width: 3px;
  height: 12px;
  border-radius: 2px;
  background: #22d3ee;
  flex: 0 0 auto;
}

.spectrum-panel__controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.spectrum-panel__controls :deep(.el-segmented) {
  --el-segmented-bg-color: #0b1623;
  --el-segmented-item-selected-bg-color: rgba(34, 211, 238, 0.13);
  --el-segmented-item-selected-color: #e5edf7;
  --el-segmented-item-hover-bg-color: rgba(34, 211, 238, 0.1);
  --el-segmented-item-hover-color: #dbeafe;
  border: 1px solid #1f2c41;
  border-radius: 6px;
  padding: 2px;
}

.spectrum-panel__controls :deep(.el-segmented__item) {
  color: #9aa7bd;
  border-radius: 4px;
  font-size: 11px;
}

.spectrum-panel__controls :deep(.el-segmented__item-selected) {
  box-shadow: none;
}

.spectrum-panel__summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin: 0;
  padding: 8px 14px 2px;
}

.spectrum-panel__phase-summary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.spectrum-panel__phase-summary i {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  display: inline-block;
}


.spectrum-panel__chart-wrap {
  position: relative;
  padding: 0 14px 14px;
}

.spectrum-panel__chart {
  width: 100%;
  height: 280px;
}

.spectrum-panel__empty-overlay {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  pointer-events: none;
  color: #7f93b2;
  font-size: 12px;
  letter-spacing: 0;
  background: rgba(11, 22, 35, 0.72);
  border-radius: 6px;
}

@media (max-width: 720px) {
  .spectrum-panel__head {
    flex-direction: column;
  }

  .spectrum-panel__controls {
    justify-content: flex-start;
  }
}
</style>
