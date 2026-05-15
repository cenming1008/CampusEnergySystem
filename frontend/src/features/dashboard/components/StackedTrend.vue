<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { LineChart } from 'echarts/charts'
import { DataZoomComponent, GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { init, use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'

use([LineChart, GridComponent, TooltipComponent, LegendComponent, DataZoomComponent, CanvasRenderer])

export interface TrendSeries {
  key: string
  name: string
  color: string
  data: number[]
  unit?: string
}

interface Props {
  series: TrendSeries[]
  seriesByRange?: Partial<Record<'today' | 'yest' | 'week' | 'month', TrendSeries[]>>
  title?: string
  subtitle?: string
}
const props = withDefaults(defineProps<Props>(), {
  title: '园区负荷趋势',
  subtitle: '',
  seriesByRange: () => ({})
})

const chartEl = ref<HTMLDivElement | null>(null)
const mode = ref<'abs' | 'pct'>('abs')
const range = ref<'today' | 'yest' | 'week' | 'month'>('today')
const visible = ref<Record<string, boolean>>({})
const cursorIdx = ref(0)
const cursorXPct = ref(0)
const tooltipVisible = ref(false)
let chart: ReturnType<typeof init> | null = null
let resizeObserver: ResizeObserver | null = null

const ranges: { k: 'today' | 'yest' | 'week' | 'month'; n: string }[] = [
  { k: 'today', n: '今日' },
  { k: 'yest', n: '昨日' },
  { k: 'week', n: '本周' },
  { k: 'month', n: '本月' }
]

const activeSeries = computed(() => props.seriesByRange?.[range.value] || props.series)
const visMap = computed<Record<string, boolean>>(() => {
  const out: Record<string, boolean> = {}
  for (const s of activeSeries.value) out[s.key] = visible.value[s.key] ?? true
  return out
})
const visibleSeries = computed(() => activeSeries.value.filter((s) => visMap.value[s.key]))
const pointCount = computed(() => Math.max(0, ...activeSeries.value.map((s) => s.data.length)))

const categoryLabels = computed(() => Array.from({ length: pointCount.value }, (_, index) => {
  const hour = String(index).padStart(2, '0')
  return `${hour}:00`
}))

const normalizedSeries = computed(() => {
  if (mode.value === 'abs') return activeSeries.value
  return activeSeries.value.map((series) => ({
    ...series,
    data: series.data.map((value, index) => {
      const total = activeSeries.value
        .filter((item) => visMap.value[item.key])
        .reduce((sum, item) => sum + (item.data[index] || 0), 0)
      return total > 0 ? (value / total) * 100 : 0
    })
  }))
})

const totalCurve = computed(() => {
  return Array.from({ length: pointCount.value }, (_, index) => (
    normalizedSeries.value
      .filter((series) => visMap.value[series.key])
      .reduce((sum, series) => sum + (series.data[index] || 0), 0)
  ))
})

const stats = computed(() => {
  const arr = totalCurve.value
  const idx = Math.max(0, Math.min(cursorIdx.value, arr.length - 1))
  const cur = arr[idx] || 0
  const peak = arr.length ? Math.max(...arr) : 0
  const valley = arr.length ? Math.min(...arr) : 0
  const avg = arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0
  return { cur, peak, valley, avg, gap: peak - valley }
})

const cursorClockLabel = computed(() => categoryLabels.value[cursorIdx.value] || '--:--')

const tooltipBreakdown = computed(() => {
  const idx = cursorIdx.value
  const visMap_ = visMap.value
  const cursorTotal = activeSeries.value.reduce((sum, s) => sum + (visMap_[s.key] ? (s.data[idx] || 0) : 0), 0)
  return {
    total: cursorTotal,
    rows: activeSeries.value.map((s) => {
      const value = s.data[idx] || 0
      const on = visMap_[s.key]
      return {
        key: s.key,
        name: s.name,
        color: s.color,
        value,
        pct: cursorTotal > 0 && on ? (value / cursorTotal) * 100 : 0,
        visible: on,
      }
    }),
  }
})

const tooltipPlaceRight = computed(() => cursorXPct.value < 50)

function fmt(v: number) {
  return mode.value === 'pct' ? v.toFixed(1) : v.toFixed(0)
}

function resolveCssColor(color: string) {
  if (!color.startsWith('var(')) return color
  const varName = color.slice(4, -1).trim()
  const scope = document.querySelector('.ems-cockpit-v2') || document.documentElement
  const value = getComputedStyle(scope).getPropertyValue(varName).trim()
  return value || color
}

function buildOption(): EChartsOption {
  return {
    backgroundColor: 'transparent',
    color: activeSeries.value.map((series) => resolveCssColor(series.color)),
    animationDurationUpdate: 300,
    grid: { left: 38, right: 16, top: 12, bottom: 28, containLabel: false },
    tooltip: {
      show: false,
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: 'rgba(230,237,245,0.45)', width: 1, type: 'dashed' } },
    },
    axisPointer: {
      show: true,
      type: 'line',
      lineStyle: { color: 'rgba(230,237,245,0.45)', width: 1, type: 'dashed' },
      triggerOn: 'mousemove',
    },
    legend: { show: false },
    dataZoom: [{ type: 'inside', disabled: true }],
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: categoryLabels.value,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisTick: { show: false },
      axisLabel: { color: '#5a6577', fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 10, interval: 3 },
    },
    yAxis: {
      type: 'value',
      max: mode.value === 'pct' ? 100 : undefined,
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)', type: 'dashed' } },
      axisLabel: {
        color: '#5a6577',
        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
        fontSize: 10,
        formatter: (value: number) => mode.value === 'pct' ? `${Math.round(value)}%` : `${Math.round(value)}`,
      },
    },
    series: normalizedSeries.value.map((series) => ({
      name: series.name,
      type: 'line',
      stack: 'total',
      smooth: true,
      showSymbol: false,
      symbolSize: 6,
      emphasis: { focus: 'series' },
      lineStyle: { width: 1.4 },
      areaStyle: { opacity: mode.value === 'pct' ? 0.5 : 0.42 },
      data: visMap.value[series.key] ? series.data : [],
    })),
  }
}

function updateChart() {
  if (!chart) return
  chart.setOption(buildOption(), true)
}

function toggle(key: string) {
  visible.value = { ...visMap.value, [key]: !visMap.value[key] }
}

function onChartMove(e: MouseEvent) {
  if (!chartEl.value || !chart) return
  const rect = chartEl.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const width = rect.width || 1
  // grid runs from left=38 to right=width-16 in echarts pixels
  const gridLeft = 38
  const gridRight = width - 16
  const innerW = Math.max(1, gridRight - gridLeft)
  const ratio = Math.max(0, Math.min(1, (x - gridLeft) / innerW))
  const count = Math.max(1, pointCount.value)
  cursorIdx.value = Math.max(0, Math.min(count - 1, Math.round(ratio * (count - 1))))
  cursorXPct.value = (x / width) * 100
  tooltipVisible.value = x >= gridLeft && x <= gridRight
}

function onChartLeave() {
  tooltipVisible.value = false
}

onMounted(async () => {
  await nextTick()
  if (!chartEl.value) return
  chart = init(chartEl.value, undefined, { renderer: 'canvas' })
  chartEl.value.addEventListener('mousemove', onChartMove)
  chartEl.value.addEventListener('mouseleave', onChartLeave)
  resizeObserver = new ResizeObserver(() => {
    chart?.resize()
  })
  resizeObserver.observe(chartEl.value)
  updateChart()
})

watch([() => props.series, mode, range, visible], () => {
  cursorIdx.value = Math.min(cursorIdx.value, Math.max(0, pointCount.value - 1))
  updateChart()
}, { deep: true })

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
  if (chartEl.value) {
    chartEl.value.removeEventListener('mousemove', onChartMove)
    chartEl.value.removeEventListener('mouseleave', onChartLeave)
  }
  if (chart) {
    chart.dispose()
    chart = null
  }
})
</script>

<template>
  <div class="stacked-trend">
    <div class="head">
      <div class="head-left">
        <span class="title">{{ title }}</span>
        <span v-if="subtitle" class="subtitle mono">{{ subtitle }}</span>
      </div>
      <div class="head-right">
        <div class="mode-toggle">
          <button
            v-for="t in [{ k: 'abs', n: '绝对值' }, { k: 'pct', n: '百分比' }]"
            :key="t.k"
            type="button"
            :class="{ active: mode === t.k }"
            @click="mode = t.k as 'abs' | 'pct'"
          >{{ t.n }}</button>
        </div>
        <div class="range-tabs">
          <button
            v-for="t in ranges"
            :key="t.k"
            type="button"
            :class="{ active: range === t.k }"
            @click="range = t.k"
          >{{ t.n }}</button>
        </div>
      </div>
    </div>

    <div class="stats-row">
      <div v-for="s in [
        { label: '当前', value: stats.cur, color: 'var(--accent)' },
        { label: '峰值', value: stats.peak, color: 'var(--warn)' },
        { label: '谷值', value: stats.valley, color: 'var(--accent-2)' },
        { label: '均值', value: stats.avg, color: 'var(--text-mid)' },
        { label: '峰谷差', value: stats.gap, color: 'var(--m-heat)' }
      ]" :key="s.label" class="stat">
        <span class="stat-label">{{ s.label }}</span>
        <div class="stat-value-row">
          <span class="stat-value mono" :style="{ color: s.color }">{{ fmt(s.value) }}</span>
          <span class="stat-unit">{{ mode === 'pct' ? '%' : 'kW' }}</span>
        </div>
      </div>
      <div class="legend">
        <span class="cursor-clock mono">@ {{ cursorClockLabel }}</span>
        <button
          v-for="s in activeSeries"
          :key="s.key"
          type="button"
          class="chip"
          :class="{ on: visMap[s.key] }"
          :style="visMap[s.key] ? {
            background: `color-mix(in srgb, ${s.color} 10%, transparent)`,
            borderColor: `color-mix(in srgb, ${s.color} 33%, transparent)`
          } : {}"
          @click="toggle(s.key)"
        >
          <span class="chip-dot" :style="{ background: visMap[s.key] ? s.color : 'var(--text-dim)' }" />
          <span class="chip-name">{{ s.name }}</span>
          <span class="chip-val mono">{{ (s.data[cursorIdx] || 0).toFixed(0) }}</span>
        </button>
      </div>
    </div>

    <div class="chart-host">
      <div ref="chartEl" class="chart-wrap" />
      <div
        v-show="tooltipVisible && tooltipBreakdown.rows.length"
        class="trend-tooltip"
        :class="tooltipPlaceRight ? 'place-right' : 'place-left'"
        :style="tooltipPlaceRight
          ? { left: `calc(${cursorXPct}% + 14px)` }
          : { right: `calc(${100 - cursorXPct}% + 14px)` }"
      >
        <div class="tt-head">
          <span class="tt-time mono">{{ cursorClockLabel }}</span>
          <span class="tt-total mono">{{ tooltipBreakdown.total.toFixed(0) }} kW</span>
        </div>
        <div
          v-for="row in tooltipBreakdown.rows"
          :key="row.key"
          class="tt-row"
          :class="{ off: !row.visible }"
        >
          <span class="tt-dot" :style="{ background: row.color }" />
          <span class="tt-name">{{ row.name }}</span>
          <span class="tt-val mono">{{ row.value.toFixed(1) }}</span>
          <span class="tt-pct mono">{{ row.visible ? `${row.pct.toFixed(1)}%` : '—' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stacked-trend {
  display: flex;
  flex-direction: column;
  gap: var(--card-gap);
}
.head { display: flex; align-items: baseline; justify-content: space-between; gap: var(--card-gap); }
.head-left { display: flex; align-items: baseline; gap: 12px; min-width: 0; }
.title { font-size: 13px; font-weight: 600; color: var(--text); white-space: nowrap; }
.subtitle { font-size: 11px; color: var(--text-dim); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.head-right { display: flex; gap: var(--card-gap); flex-wrap: wrap; justify-content: flex-end; }
.mode-toggle { display: flex; border: 1px solid var(--border); border-radius: 5px; overflow: hidden; }
.mode-toggle button {
  padding: 4px 10px; font-size: 11px;
  background: transparent;
  color: var(--text-mid);
  border: none;
  cursor: pointer;
  font-family: inherit;
}
.mode-toggle button.active {
  background: rgba(77, 208, 196, 0.10);
  color: var(--accent);
}
.range-tabs { display: flex; gap: 4px; }
.range-tabs button {
  padding: 3px 10px; font-size: 11px;
  border-radius: 4px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-mid);
  cursor: pointer;
  font-family: inherit;
}
.range-tabs button.active {
  border-color: var(--accent);
  background: rgba(77, 208, 196, 0.10);
  color: var(--accent);
}
.stats-row {
  display: flex;
  gap: clamp(12px, 1.4vw, 22px);
  padding: 8px 0 10px;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
  align-items: center;
}
.stat { display: flex; flex-direction: column; gap: 2px; }
.stat-label { font-size: 10px; color: var(--text-dim); letter-spacing: 0.4px; }
.stat-value-row { display: flex; align-items: baseline; gap: 4px; }
.stat-value { font-size: 16px; font-weight: 600; }
.stat-unit { font-size: 10px; color: var(--text-dim); }
.legend { margin-left: auto; display: flex; gap: 4px; align-items: center; flex-wrap: wrap; }
.cursor-clock {
  font-size: 10px;
  color: var(--text-dim);
  letter-spacing: 0.4px;
  padding: 4px 8px;
  border-radius: 4px;
  margin-right: 4px;
  background: var(--surface-hi);
  border: 1px solid var(--border);
}
.chip {
  display: flex; align-items: center; gap: 5px;
  padding: 4px 9px;
  border-radius: 4px;
  cursor: pointer;
  background: transparent;
  border: 1px solid var(--border);
  font-family: inherit;
  opacity: 0.45;
}
.chip.on { opacity: 1; }
.chip-dot { width: 8px; height: 8px; border-radius: 2px; }
.chip-name { font-size: 11px; color: var(--text); }
.chip-val { font-size: 10px; color: var(--text-dim); }
.chart-host {
  position: relative;
  width: 100%;
}
.chart-wrap {
  position: relative;
  width: 100%;
  height: clamp(240px, 19vw, 320px);
  min-height: 220px;
}
.trend-tooltip {
  position: absolute;
  top: 8px;
  min-width: 188px;
  padding: 8px 10px;
  border-radius: 6px;
  background: var(--surface-hi);
  border: 1px solid var(--border-hi);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  pointer-events: none;
  z-index: 10;
}
.tt-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 6px;
}
.tt-time { font-size: 11px; color: var(--text); font-weight: 600; }
.tt-total { font-size: 11px; color: var(--accent); font-weight: 600; }
.tt-row {
  display: grid;
  grid-template-columns: 7px 1fr auto 40px;
  align-items: center;
  column-gap: 6px;
  padding: 3px 0;
  font-size: 11px;
}
.tt-row.off { opacity: 0.4; }
.tt-dot { width: 7px; height: 7px; border-radius: 2px; }
.tt-name { color: var(--text-mid); }
.tt-val { color: var(--text); font-variant-numeric: tabular-nums; text-align: right; }
.tt-pct { color: var(--text-dim); font-size: 10px; text-align: right; }
</style>
