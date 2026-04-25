<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { echarts } from '@/shared/lib/echarts'
import type {
  AnalysisEnergyCategoryComparisonItem,
  AnalysisSubItemComparisonItem,
  AnalysisTrendItem,
} from '@/api/energy'
import {
  formatMetricValue,
  formatPercent,
  formatSignedPercent,
  formatTimestamp,
} from '../formatters'

defineOptions({ name: 'EnergyTrendComparisonTab' })

const props = defineProps<{
  granularity: string
  trendItems: AnalysisTrendItem[]
  periodComparison: {
    current_total_consumption: number
    previous_total_consumption: number
    delta_consumption: number
    change_rate: number | null
    consumption_stat_basis: string
  } | null
  energyCategoryComparison: AnalysisEnergyCategoryComparisonItem[]
  subItemComparison: AnalysisSubItemComparisonItem[]
  statBasisText: string
}>()

const trendChartRef = ref<HTMLElement | null>(null)
let trendChart: echarts.ECharts | null = null

function renderTrendChart() {
  if (!trendChart || !trendChartRef.value) return
  const xAxis = props.trendItems.map(item => formatTimestamp(item.timestamp, props.granularity))
  const consumption = props.trendItems.map(item => Number((item.total_consumption || 0).toFixed(2)))
  const load = props.trendItems.map(item => Number((item.total_load || 0).toFixed(2)))

  trendChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0,0,0,0.8)',
      borderColor: '#5eead4',
      textStyle: { color: '#f0f6ff' }
    },
    legend: {
      data: ['周期能耗', '负荷'],
      textStyle: { color: 'rgba(255,255,255,0.55)' },
      top: 0
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '18%', containLabel: true },
    xAxis: {
      type: 'category',
      data: xAxis,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisLabel: { color: 'rgba(255,255,255,0.45)', fontSize: 10 }
    },
    yAxis: [
      {
        type: 'value',
        name: '能耗',
        nameTextStyle: { color: 'rgba(255,255,255,0.35)', fontSize: 10 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'dashed' } },
        axisLabel: { color: 'rgba(255,255,255,0.4)', fontSize: 10 }
      },
      {
        type: 'value',
        name: '负荷',
        nameTextStyle: { color: 'rgba(255,255,255,0.35)', fontSize: 10 },
        splitLine: { show: false },
        axisLabel: { color: 'rgba(255,255,255,0.4)', fontSize: 10 }
      }
    ],
    series: [
      {
        name: '周期能耗',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: consumption,
        lineStyle: { color: '#63d6ff', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(99,214,255,0.28)' },
            { offset: 1, color: 'rgba(99,214,255,0.02)' }
          ])
        }
      },
      {
        name: '负荷',
        type: 'line',
        smooth: true,
        showSymbol: false,
        yAxisIndex: 1,
        data: load,
        lineStyle: { color: '#78f0b8', width: 2 }
      }
    ]
  }, true)
}

function initChart() {
  if (trendChartRef.value && !trendChart) {
    trendChart = echarts.init(trendChartRef.value)
  }
  renderTrendChart()
}

function handleChartResize() {
  trendChart?.resize()
}

onMounted(async () => {
  await nextTick()
  initChart()
  window.addEventListener('resize', handleChartResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleChartResize)
})

watch(
  () => [props.trendItems, props.granularity],
  async () => {
    await nextTick()
    initChart()
  },
  { deep: true },
)
</script>

<template>
  <div class="energy-trend-comparison-tab">
    <div class="glass-card em-card">
      <div class="card-head">
        <p class="eyebrow">Trend</p>
        <div class="card-title-row">
          <h3 class="card-title">周期趋势</h3>
          <el-tag type="info" effect="plain">
            {{ granularity === 'hour' ? '小时粒度' : '天粒度' }}
          </el-tag>
        </div>
      </div>
      <div v-if="trendItems.length" ref="trendChartRef" class="chart-box chart-box--wide" />
      <el-empty v-else description="当前统计窗口暂无趋势数据" />
      <div class="basis-note">{{ statBasisText }}</div>
    </div>

    <div class="glass-card em-card">
      <div class="card-head">
        <p class="eyebrow">Period Comparison</p>
        <h3 class="card-title">周期对比</h3>
      </div>
      <div v-if="periodComparison" class="period-comparison">
        <div class="period-card">
          <span>当前周期</span>
          <strong>{{ formatMetricValue(periodComparison.current_total_consumption, 1) }}</strong>
        </div>
        <div class="period-card">
          <span>上一周期</span>
          <strong>{{ formatMetricValue(periodComparison.previous_total_consumption, 1) }}</strong>
        </div>
        <div class="period-card">
          <span>环比</span>
          <strong :class="['trend-change', { 'trend-change--up': (periodComparison.change_rate || 0) > 0 }]">
            {{ formatSignedPercent(periodComparison.change_rate) }}
          </strong>
        </div>
      </div>
      <el-empty v-else description="暂无周期对比数据" />

      <div v-if="energyCategoryComparison.length" class="comparison-list">
        <div
          v-for="item in energyCategoryComparison"
          :key="item.energy_category"
          class="comparison-item"
        >
          <div class="comparison-row">
            <span>{{ item.label }}</span>
            <strong>{{ formatPercent(item.ratio) }}</strong>
          </div>
          <div class="comparison-meta">
            <span>{{ formatMetricValue(item.total_consumption, 1) }} 周期能耗</span>
            <span>{{ formatMetricValue(item.avg_load, 1) }} 平均负荷</span>
          </div>
          <div class="comparison-bar">
            <span :style="{ width: `${Math.max(item.ratio * 100, 4)}%` }" />
          </div>
        </div>
      </div>
    </div>

    <div v-if="subItemComparison.length" class="glass-card em-card">
      <div class="card-head">
        <p class="eyebrow">Sub Items</p>
        <h3 class="card-title">分项对比</h3>
      </div>
      <div class="subitem-list">
        <div
          v-for="item in subItemComparison"
          :key="item.sub_item"
          class="subitem-item"
        >
          <div class="subitem-row">
            <strong>{{ item.label }}</strong>
            <span>{{ formatMetricValue(item.total_consumption, 1) }}</span>
          </div>
          <span class="subitem-meta">
            {{ item.device_count }} 台设备 · {{ item.energy_categories.join(' / ') || '未覆盖' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
