<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { echarts } from '@/shared/lib/echarts'
import type { CarbonSummary, EnergyStatistics, EnergyTypeInfo } from '@/api/energy'
import {
  formatMetricValue,
} from '../formatters'
import { typeColorMap } from '../energyDisplay'

defineOptions({ name: 'EnergyOverviewTab' })

interface MetricItem {
  label: string
  value: string
  unit: string
  accent: string
}

interface MixItem {
  key: string
  label: string
  unit: string
  value: number
  color: string
  percent: number
}

const props = defineProps<{
  overviewMetrics: MetricItem[]
  totalEnergyConsumption: number
  energyMixItems: MixItem[]
  visibleEnergyTypes: EnergyTypeInfo[]
  statistics: Record<string, EnergyStatistics>
  carbonSummary: CarbonSummary | null
  hasSteamRuntimePresence: boolean
  currentEnergyInfo: Partial<EnergyTypeInfo>
  currentStats: Partial<EnergyStatistics>
  focusHighlights: Array<{ label: string; value: string }>
  detailDeviceId?: number
  detailDeviceName: string
}>()

const emit = defineEmits<{
  (event: 'refresh-detail'): void
  (event: 'clear-device'): void
}>()

const comparisonChartRef = ref<HTMLElement | null>(null)
const carbonChartRef = ref<HTMLElement | null>(null)
let comparisonChart: echarts.ECharts | null = null
let carbonChart: echarts.ECharts | null = null

function renderComparisonChart() {
  if (!comparisonChart || !comparisonChartRef.value) return
  const data = props.visibleEnergyTypes.map(type => ({
    name: type.label,
    value: props.statistics[type.value]?.total_consumption || 0,
    unit: type.unit
  })).filter(item => item.value > 0)

  comparisonChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: 'rgba(22,33,51,0.96)',
      borderColor: 'rgba(255,255,255,0.12)',
      textStyle: {
        color: '#e6edf5',
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: 12,
      },
    },
    legend: { show: false },
    series: [{
      name: '能源消耗',
      type: 'pie',
      radius: ['42%', '72%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 6,
        borderColor: 'rgba(9,14,23,0.8)',
        borderWidth: 2
      },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#f0f6ff' },
        itemStyle: { shadowBlur: 14, shadowColor: 'rgba(59,130,246,0.28)' }
      },
      labelLine: { show: false },
      // 按介质名称取 token 色，避免 Object.values 顺序不稳定
      data: data.map((d) => {
        const meta = props.visibleEnergyTypes.find((t) => t.label === d.name)
        return { ...d, itemStyle: { color: typeColorMap[meta?.value || ''] } }
      }),
    }]
  })
}

function renderCarbonChart() {
  if (!carbonChart || !carbonChartRef.value || !props.carbonSummary) return

  const data = Object.entries(props.carbonSummary.by_energy_type).map(([type, info]) => {
    if (type === 'steam' && !props.hasSteamRuntimePresence) return null
    const typeInfo = props.visibleEnergyTypes.find(t => t.value === type)
    return {
      name: typeInfo?.label || type,
      value: info.carbon_emission
    }
  }).filter((item): item is { name: string; value: number } => Boolean(item && item.value > 0))

  // 碳排=热色系（红）
  const HEAT = '#EF4444'
  const HEAT_BRIGHT = '#F87171'
  carbonChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(22,33,51,0.96)',
      borderColor: 'rgba(255,255,255,0.12)',
      textStyle: {
        color: '#e6edf5',
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: 12,
      },
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map(d => d.name),
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisLabel: { color: 'rgba(255,255,255,0.45)', fontSize: 11, fontFamily: 'JetBrains Mono, monospace' },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      name: 'kg CO₂',
      nameTextStyle: { color: 'rgba(255,255,255,0.35)', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'dashed' } },
      axisLabel: { color: 'rgba(255,255,255,0.4)', fontSize: 10, fontFamily: 'JetBrains Mono, monospace' }
    },
    series: [{
      name: '碳排放',
      type: 'bar',
      data: data.map(d => d.value),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: HEAT },
          { offset: 1, color: 'rgba(239,68,68,0.3)' }
        ]),
        borderRadius: [6, 6, 0, 0]
      },
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: HEAT_BRIGHT },
            { offset: 1, color: 'rgba(239,68,68,0.5)' }
          ])
        }
      }
    }]
  })
}

function initCharts() {
  if (comparisonChartRef.value && !comparisonChart) {
    comparisonChart = echarts.init(comparisonChartRef.value)
  }
  if (carbonChartRef.value && !carbonChart) {
    carbonChart = echarts.init(carbonChartRef.value)
  }
  renderComparisonChart()
  renderCarbonChart()
}

function handleChartResize() {
  comparisonChart?.resize()
  carbonChart?.resize()
}

onMounted(async () => {
  await nextTick()
  initCharts()
  window.addEventListener('resize', handleChartResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleChartResize)
})

watch(
  () => [props.visibleEnergyTypes, props.statistics, props.carbonSummary, props.hasSteamRuntimePresence],
  async () => {
    await nextTick()
    initCharts()
  },
  { deep: true },
)
</script>

<template>
  <div class="energy-overview-tab">
    <div class="kpi-strip">
      <div
        v-for="m in overviewMetrics"
        :key="m.label"
        class="kpi-tile"
        :class="m.accent"
      >
        <p class="kpi-eyebrow">{{ m.label }}</p>
        <div class="kpi-val">
          <strong>{{ m.value }}</strong>
          <span class="kpi-unit">{{ m.unit }}</span>
        </div>
      </div>
    </div>

    <div class="em-stage">
      <section class="em-main">
        <div class="glass-card em-card">
          <div class="card-head">
            <p class="eyebrow">Energy Structure</p>
            <div class="card-title-row">
              <h3 class="card-title">多能源结构</h3>
              <span class="card-badge">总 {{ formatMetricValue(totalEnergyConsumption, 2) }}</span>
            </div>
          </div>
          <div class="structure-body">
            <div ref="comparisonChartRef" class="chart-box" />
            <div class="legend-list">
              <div
                v-for="item in energyMixItems"
                :key="item.key"
                class="legend-row"
              >
                <span
                  class="legend-swatch"
                  :style="{ background: item.color, boxShadow: `0 0 6px ${item.color}66` }"
                />
                <span class="legend-name">{{ item.label }}</span>
                <span class="legend-pct">{{ item.percent.toFixed(1) }}%</span>
                <span class="legend-val">{{ formatMetricValue(item.value, 1) }} {{ item.unit }}</span>
              </div>
              <div v-if="!energyMixItems.length" class="card-empty">暂无多能源结构数据</div>
            </div>
          </div>
        </div>

        <div class="glass-card em-card">
          <div class="card-head">
            <p class="eyebrow">Carbon Snapshot</p>
            <div class="card-title-row">
              <h3 class="card-title">碳排运行态</h3>
              <span class="card-badge card-badge--rose">
                {{ formatMetricValue(carbonSummary?.total_carbon || 0, 2) }} kg CO₂
              </span>
            </div>
          </div>
          <div ref="carbonChartRef" class="chart-box" />
        </div>
      </section>

      <div class="em-center">
        <slot name="center" />
      </div>

      <aside class="em-side">
        <div class="glass-card em-card focus-card">
          <div class="card-head">
            <p class="eyebrow">Current Focus</p>
            <h3 class="card-title">{{ currentEnergyInfo.label || '能源焦点' }}</h3>
          </div>
          <div class="focus-hero">
            <strong class="focus-value">{{ formatMetricValue(currentStats.total_consumption, 2) }}</strong>
            <span class="focus-unit">{{ currentEnergyInfo.unit }}</span>
          </div>
          <div class="focus-metrics">
            <div
              v-for="item in focusHighlights"
              :key="item.label"
              class="focus-metric"
            >
              <span class="focus-metric__label">{{ item.label }}</span>
              <strong class="focus-metric__val">{{ item.value }}</strong>
            </div>
          </div>
        </div>

        <div class="glass-card em-card">
          <div class="card-head">
            <p class="eyebrow">Device Entry</p>
            <h3 class="card-title">设备维度</h3>
          </div>
          <div class="device-state">
            <span>当前焦点设备</span>
            <strong>{{ detailDeviceName }}</strong>
          </div>
          <div class="device-actions">
            <el-button
              size="small"
              type="primary"
              :disabled="!detailDeviceId"
              @click="emit('refresh-detail')"
            >
              刷新明细
            </el-button>
            <el-button size="small" @click="emit('clear-device')">
              系统总览
            </el-button>
          </div>
        </div>
      </aside>
    </div>

  </div>
</template>
