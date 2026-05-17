<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useECharts } from '@/shared/composables/useECharts'
import { usePanelCollapse } from '@/shared/composables/usePanelCollapse'
import PanelCollapseToggle from '@/shared/components/PanelCollapseToggle.vue'
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

const { collapsed, toggle } = usePanelCollapse('compensation-monitor:collapse:harmonic', true)

watch(collapsed, (isCollapsed) => {
  if (!isCollapsed) nextTick(() => chart.resize())
})

const kindOptions = [
  { label: '电压谐波', value: 'voltage' },
  { label: '电流谐波', value: 'current' },
]
const phaseOptions = [
  { label: 'A相', value: 'a' },
  { label: 'B相', value: 'b' },
  { label: 'C相', value: 'c' },
]

const model = computed(() =>
  buildHarmonicSpectrumView({
    activeKind: activeKind.value,
    activePhase: activePhase.value,
    telemetry: props.telemetry,
    controlProfile: props.controlProfile,
  }),
)

function formatNumber(value: number | null | undefined, digits = 1) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return '暂无数据'
  return Number(value).toFixed(digits)
}

async function renderChart() {
  // 门限线固定，y轴保持静态范围
  const staticMax = getHarmonicSpectrumYAxisMax(activeKind.value)

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
    grid: { left: 48, right: 24, top: 30, bottom: 34 },
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
              label: { color: '#fbbf24', formatter: '门限' },
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
        <div class="panel-title-row">
          <h3>高次谐波频谱</h3>
          <PanelCollapseToggle :collapsed="collapsed" @toggle="toggle" />
        </div>
        <span>展示最新采样的 2~31 次谐波分布。</span>
      </div>
      <div v-show="!collapsed" class="spectrum-panel__controls">
        <el-segmented
          :model-value="activeKind"
          :options="kindOptions"
          size="small"
          @change="activeKind = $event as HarmonicSpectrumKind"
        />
        <el-segmented
          :model-value="activePhase"
          :options="phaseOptions"
          size="small"
          @change="activePhase = $event as HarmonicSpectrumPhase"
        />
      </div>
    </div>

    <div v-show="!collapsed" class="spectrum-panel__summary">
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

    <div v-show="!collapsed" class="spectrum-panel__chart-wrap">
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
  padding: 18px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.96), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.spectrum-panel__head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
}

.spectrum-panel__head h3 {
  margin: 0 0 6px;
  font-size: 16px;
  color: #e2ecfb;
}

.spectrum-panel__head span,
.spectrum-panel__summary {
  color: #9fb0ca;
  font-size: 13px;
}

.spectrum-panel__controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.spectrum-panel__controls :deep(.el-segmented) {
  --el-segmented-bg-color: rgba(7, 15, 26, 0.7);
  --el-segmented-item-selected-bg-color: rgba(59, 130, 246, 0.28);
  --el-segmented-item-selected-color: #eaf4ff;
  --el-segmented-item-hover-bg-color: rgba(96, 165, 250, 0.16);
  --el-segmented-item-hover-color: #dbeafe;
  border: 1px solid rgba(72, 96, 130, 0.72);
  border-radius: 8px;
  padding: 2px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.spectrum-panel__controls :deep(.el-segmented__item) {
  color: #9fb1ca;
  border-radius: 6px;
}

.spectrum-panel__controls :deep(.el-segmented__item-selected) {
  box-shadow: 0 0 0 1px rgba(96, 165, 250, 0.35);
}

.spectrum-panel__summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px;
  margin: 16px 0 8px;
}

.spectrum-panel__chart-wrap {
  position: relative;
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
  font-size: 13px;
  letter-spacing: 0.5px;
  background: rgba(13, 22, 35, 0.35);
  border-radius: 12px;
}

@media (max-width: 720px) {
  .spectrum-panel__head {
    flex-direction: column;
  }

  .spectrum-panel__controls {
    justify-content: flex-start;
  }
}

.panel-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
</style>
