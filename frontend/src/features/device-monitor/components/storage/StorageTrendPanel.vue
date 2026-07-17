<script setup lang="ts">
import { computed, watch } from 'vue'
import { useECharts } from '@/shared/composables/useECharts'
import type { StorageTelemetry } from '@/api/storage'

type TrendTab = 'soc' | 'power' | 'temperature' | 'energy'

const props = defineProps<{
  history: StorageTelemetry[]
  loading: boolean
  timeRange: [Date, Date] | null
}>()

const emit = defineEmits<{
  'update:timeRange': [value: [Date, Date] | null]
  'range-change': []
}>()

const chart = useECharts()

const tabs = [
  { label: 'SOC', value: 'soc' as TrendTab },
  { label: '充放电功率', value: 'power' as TrendTab },
  { label: '温度', value: 'temperature' as TrendTab },
  { label: '今日能量', value: 'energy' as TrendTab },
]

const activeTab = defineModel<TrendTab>('activeTab', { default: 'soc' })

const timeShortcuts = [
  { text: '近 1 小时', value: () => buildRange(1) },
  { text: '近 6 小时', value: () => buildRange(6) },
  { text: '近 24 小时', value: () => buildRange(24) },
  { text: '近 7 天', value: () => buildRange(24 * 7) },
]

function buildRange(hours: number): [Date, Date] {
  const end = new Date()
  return [new Date(end.getTime() - hours * 60 * 60 * 1000), end]
}

function formatAxisLabel(timestamp: string) {
  const date = new Date(timestamp)
  const [start, end] = props.timeRange || buildRange(1)
  const crossesDay = start.getDate() !== end.getDate()
    || start.getMonth() !== end.getMonth()
  const pad = (n: number) => `${n}`.padStart(2, '0')
  return crossesDay
    ? `${pad(date.getMonth() + 1)}/${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
    : `${pad(date.getHours())}:${pad(date.getMinutes())}`
}

const SERIES_CONFIGS: Record<TrendTab, {
  axes: Array<{ name: string; min?: number; max?: number }>
  series: Array<{ name: string; color: string; key: keyof StorageTelemetry; area?: boolean }>
}> = {
  soc: {
    axes: [{ name: '%', min: 0, max: 100 }],
    series: [{ name: 'SOC', color: '#38bdf8', key: 'soc', area: true }],
  },
  power: {
    axes: [{ name: 'kW' }],
    series: [
      { name: '实际功率', color: '#4ade80', key: 'active_power', area: true },
      { name: '目标功率', color: '#38bdf8', key: 'target_active_power' },
      { name: '可充功率', color: '#fbbf24', key: 'available_charge_power' },
      { name: '可放功率', color: '#fb7185', key: 'available_discharge_power' },
    ],
  },
  temperature: {
    axes: [{ name: '°C' }],
    series: [
      { name: '最高温', color: '#fb7185', key: 'cell_temp_max' },
      { name: '平均温', color: '#fbbf24', key: 'cell_temp_avg' },
      { name: '最低温', color: '#60a5fa', key: 'cell_temp_min' },
    ],
  },
  energy: {
    axes: [{ name: 'kWh' }],
    series: [
      { name: '今日充电量', color: '#38bdf8', key: 'charge_energy_today' },
      { name: '今日放电量', color: '#4ade80', key: 'discharge_energy_today' },
    ],
  },
}

const currentConfig = computed(() => SERIES_CONFIGS[activeTab.value ?? 'soc'])

const hasLegend = computed(() => currentConfig.value.series.length > 1)

const summaryItems = computed(() => {
  if (!props.history.length) return []
  const cfg = currentConfig.value.series[0]
  if (!cfg) return []
  const values = props.history
    .map(r => r[cfg.key] as number | null | undefined)
    .filter((v): v is number => v != null)
  if (!values.length) return []
  const latest = values[values.length - 1]
  const peak = Math.max(...values)
  const valley = Math.min(...values)
  const avg = values.reduce((a, b) => a + b, 0) / values.length
  return [
    { label: '当前', value: `${latest.toFixed(1)}` },
    { label: '峰值', value: `${peak.toFixed(1)}` },
    { label: '均值', value: `${avg.toFixed(1)}` },
    { label: '谷值', value: `${valley.toFixed(1)}` },
  ]
})

async function renderChart() {
  const records = props.history
  const cfg = currentConfig.value

  if (!records.length) {
    await chart.setOptions({
      title: {
        text: '暂无历史数据',
        left: 'center',
        top: 'center',
        textStyle: { color: '#7f93b2', fontSize: 15, fontWeight: 400 },
      },
      xAxis: { show: false, type: 'category', data: [] },
      yAxis: { show: false, type: 'value' },
      series: [],
    }, { notMerge: true })
    return
  }

  const labels = records.map(r => formatAxisLabel(r.timestamp))

  await chart.setOptions({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(11, 19, 30, 0.96)',
      borderColor: '#314055',
      textStyle: { color: '#dfe8f5' },
    },
    legend: { show: false },
    grid: { left: 56, right: 56, top: 30, bottom: 30 },
    xAxis: {
      type: 'category',
      data: labels,
      axisLine: { lineStyle: { color: '#314055' } },
      axisLabel: { color: '#8ea0bc', fontSize: 11 },
    },
    yAxis: cfg.axes.map((axis) => ({
      type: 'value',
      name: axis.name,
      min: axis.min,
      max: axis.max,
      nameGap: 10,
      nameTextStyle: { color: '#8ea0bc', padding: [0, 0, 0, 6] },
      axisLabel: { color: '#8ea0bc', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
    })),
    series: cfg.series.map((s) => ({
      name: s.name,
      type: 'line',
      smooth: true,
      showSymbol: false,
      data: records.map(r => (r[s.key] as number | null | undefined) ?? null),
      lineStyle: { color: s.color, width: 2.6 },
      itemStyle: { color: s.color },
      areaStyle: s.area
        ? {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: `${s.color}55` },
                { offset: 1, color: `${s.color}00` },
              ],
            },
          }
        : undefined,
    })),
  }, { notMerge: true })
}

watch(() => [props.history, activeTab.value], () => {
  void renderChart()
}, { deep: true })

watch(() => chart.chartRef.value, async () => {
  if (!chart.chartRef.value) return
  await chart.initChart()
  await renderChart()
})
</script>

<template>
  <section class="trend-panel">
    <div class="trend-panel__head">
      <div class="trend-panel__intro">
        <h3>历史趋势</h3>
      </div>
      <div class="trend-panel__toolbar">
        <div class="trend-panel__tab-wrapper">
          <div class="trend-panel__tab-switcher">
            <el-segmented
              v-model="activeTab"
              :options="tabs.map(t => ({ label: t.label, value: t.value }))"
              size="small"
            />
          </div>
        </div>
        <div class="trend-panel__range-picker">
          <el-date-picker
            :model-value="timeRange"
            type="datetimerange"
            unlink-panels
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            range-separator="至"
            :shortcuts="timeShortcuts"
            @update:model-value="emit('update:timeRange', $event)"
            @change="emit('range-change')"
          />
        </div>
      </div>
    </div>

    <div class="trend-panel__summary">
      <span
        v-for="item in summaryItems"
        :key="item.label"
      >
        {{ item.label }} {{ item.value }}
      </span>
    </div>

    <div
      v-if="hasLegend"
      class="trend-panel__legend"
    >
      <span
        v-for="(s, i) in currentConfig.series"
        :key="s.name"
        class="trend-panel__legend-item"
      >
        <i :style="{ background: s.color }" />
        {{ s.name }}
      </span>
    </div>

    <div
      :ref="chart.chartRef"
      v-loading="loading"
      class="trend-panel__chart"
    />
  </section>
</template>

<style scoped>
.trend-panel {
  padding: 18px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.96), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.trend-panel__head {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.trend-panel__head h3 {
  margin: 0;
  font-size: 16px;
  color: #f5f7fb;
}

.trend-panel__toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
  width: 100%;
  min-width: 0;
}

.trend-panel__tab-wrapper {
  flex: 0 1 auto;
  min-width: 0;
}

.trend-panel__tab-switcher {
  overflow-x: auto;
  padding-bottom: 2px;
  scrollbar-width: none;
}

.trend-panel__tab-switcher::-webkit-scrollbar { display: none; }

.trend-panel__tab-switcher :deep(.el-segmented) {
  white-space: nowrap;
  min-width: max-content;
  --el-segmented-bg-color: rgba(7, 15, 26, 0.7);
  --el-segmented-item-selected-bg-color: rgba(34, 197, 94, 0.22);
  --el-segmented-item-selected-color: #dcfce7;
  --el-segmented-item-hover-bg-color: rgba(74, 222, 128, 0.14);
  --el-segmented-item-hover-color: #bbf7d0;
  border: 1px solid rgba(72, 96, 130, 0.72);
  border-radius: 8px;
  padding: 2px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.trend-panel__tab-switcher :deep(.el-segmented__group) {
  flex-wrap: nowrap;
}

.trend-panel__tab-switcher :deep(.el-segmented__item) {
  color: #9fb1ca;
  border-radius: 6px;
}

.trend-panel__tab-switcher :deep(.el-segmented__item-selected) {
  box-shadow: 0 0 0 1px rgba(74, 222, 128, 0.3);
}

.trend-panel__range-picker {
  flex: 0 1 420px;
  min-width: min(100%, 320px);
}

.trend-panel__range-picker :deep(.el-date-editor) {
  width: 100%;
}

.trend-panel__range-picker :deep(.el-input__wrapper),
.trend-panel__range-picker :deep(.el-date-editor.el-input__wrapper) {
  background: rgba(7, 15, 26, 0.72);
  border: 1px solid rgba(72, 96, 130, 0.72);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.trend-panel__range-picker :deep(.el-range-input),
.trend-panel__range-picker :deep(.el-range-separator) {
  color: #dbeafe;
}

.trend-panel__range-picker :deep(.el-range__icon) {
  color: #7f93b2;
}

.trend-panel__summary {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 14px 0 8px;
  color: #cad6eb;
  font-size: 12px;
}

.trend-panel__legend {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 14px;
  margin-bottom: 6px;
  color: #9fb1ca;
  font-size: 12px;
}

.trend-panel__legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  line-height: 1;
}

.trend-panel__legend-item i {
  width: 18px;
  height: 3px;
  border-radius: 999px;
  box-shadow: 0 0 8px currentColor;
}

.trend-panel__chart {
  width: 100%;
  height: 360px;
}

@media (max-width: 900px) {
  .trend-panel__toolbar {
    justify-content: flex-start;
  }

  .trend-panel__tab-switcher,
  .trend-panel__range-picker {
    flex-basis: 100%;
  }

  .trend-panel__range-picker {
    min-width: 0;
  }
}

@media (max-width: 900px) {
  .trend-panel { padding: 16px; }
  .trend-panel__chart { height: 320px; }
}
</style>
