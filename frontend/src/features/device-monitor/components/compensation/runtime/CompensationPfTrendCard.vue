<script lang="ts">
let pfGradientUid = 0
</script>

<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { CompensationPowerFactorTrend } from '../types'

const areaGradientId = `pfAreaGrad-${++pfGradientUid}`

const props = defineProps({
  pf: { type: Number as PropType<number | null>, default: null },
  p: { type: Number as PropType<number | null>, default: null },
  q: { type: Number as PropType<number | null>, default: null },
  pfTrend: {
    type: Object as PropType<CompensationPowerFactorTrend>,
    default: () => ({ values: [], timestamps: [], target: null }),
  },
  timeRangeKey: { type: String as PropType<'10m' | '1h' | '24h'>, default: '1h' },
})

const emit = defineEmits<{ (e: 'range-change', value: '10m' | '1h' | '24h'): void }>()

const ranges: Array<{ key: '10m' | '1h' | '24h'; label: string }> = [
  { key: '10m', label: '10 分钟' },
  { key: '1h', label: '1 小时' },
  { key: '24h', label: '24 小时' },
]

const W = 400
const H = 80
const MIN = 0.85
const MAX = 1.0
const PAD = { l: 2, r: 24, t: 6, b: 10 }

const hasSpark = computed(() => props.pfTrend.values.length >= 2)

const activeRangeLabel = computed(() => ranges.find((item) => item.key === props.timeRangeKey)?.label || '1 小时')

const yTicks = [
  { label: '1.00', value: 1.0 },
  { label: '0.95', value: 0.95 },
  { label: '0.90', value: 0.9 },
]

const yAxisTicks = computed(() =>
  yTicks.map((tick) => ({
    ...tick,
    top: `${(((MAX - tick.value) / (MAX - MIN)) * 100).toFixed(2)}%`,
  })),
)

const xAxisTicks = computed(() => {
  const timestamps = props.pfTrend.timestamps || []
  if (timestamps.length >= 3) {
    return [
      formatTickTime(timestamps[0]),
      formatTickTime(timestamps[Math.floor((timestamps.length - 1) / 2)]),
      formatTickTime(timestamps[timestamps.length - 1]),
    ]
  }
  if (timestamps.length === 2) return [formatTickTime(timestamps[0]), '中点', formatTickTime(timestamps[1])]
  return ['起点', '中点', '最新']
})

const windowSummary = computed(() => {
  const count = props.pfTrend.values.length
  const timestamps = props.pfTrend.timestamps || []
  const first = timestamps[0]
  const last = timestamps[timestamps.length - 1]
  const timeText = first && last ? `${formatTickTime(first)}-${formatTickTime(last)}` : '等待采样'
  return `${activeRangeLabel.value} · ${count} 点 · ${timeText}`
})

const geometry = computed(() => {
  const data = props.pfTrend.values
  if (data.length < 2) return null
  const w = W - PAD.l - PAD.r
  const h = H - PAD.t - PAD.b
  const points = data.map((d, i) => {
    const x = PAD.l + (i / (data.length - 1)) * w
    const y = PAD.t + h - ((Math.min(MAX, Math.max(MIN, d)) - MIN) / (MAX - MIN)) * h
    return [x, y] as const
  })
  const line = points.map((pt, i) => `${i === 0 ? 'M' : 'L'} ${pt[0].toFixed(2)} ${pt[1].toFixed(2)}`).join(' ')
  const last = points[points.length - 1]
  const area = `${line} L ${last[0].toFixed(2)} ${PAD.t + h} L ${points[0][0].toFixed(2)} ${PAD.t + h} Z`
  const target = props.pfTrend.target
  const band =
    target !== null && isFinite(target) && target > MIN && target < MAX
      ? (() => {
          const yTop = PAD.t // y for PF = MAX (top of the chart)
          const yBot = PAD.t + h - ((target - MIN) / (MAX - MIN)) * h
          return { y: yTop, h: yBot - yTop, bot: yBot }
        })()
      : null
  return { line, area, last, band, w }
})

const delta = computed(() => {
  const values = props.pfTrend.values
  if (values.length < 2) return null
  return values[values.length - 1] - values[0]
})

const apparentPower = computed(() => {
  if (props.p === null || props.q === null) return null
  return Math.round(Math.sqrt(props.p * props.p + props.q * props.q))
})

function fmt(value: number | null, digits = 0): string {
  return value === null ? '--' : value.toFixed(digits)
}

function formatTickTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--:--'
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}
</script>

<template>
  <section class="pf-card">
    <header class="rt-card-head">
      <span class="rt-card-title"><span class="rt-accent" />功率因数 <span class="rt-sub">实时 · 滞后为正</span></span>
      <div class="pf-tabs">
        <button
          v-for="r in ranges"
          :key="r.key"
          type="button"
          class="pf-tab"
          :class="{ 'is-active': timeRangeKey === r.key }"
          data-test="pf-range-tab"
          @click="emit('range-change', r.key)"
        >{{ r.label }}</button>
      </div>
    </header>

    <div class="pf-body">
      <div class="pf-readout">
        <strong class="pf-big">{{ fmt(pf, 3) }}</strong>
        <span class="pf-unit">PF</span>
        <span
          v-if="delta !== null"
          class="pf-delta"
          :class="delta >= 0 ? 'is-up' : 'is-down'"
        >{{ delta >= 0 ? '▲' : '▼' }} {{ Math.abs(delta).toFixed(3) }}</span>
      </div>

      <div class="pf-spark">
        <div
          v-if="hasSpark && geometry"
          class="pf-plot"
        >
          <div
            class="pf-y-axis"
            data-test="pf-y-axis"
          >
            <span
              v-for="tick in yAxisTicks"
              :key="tick.label"
              :style="{ top: tick.top }"
            >{{ tick.label }}</span>
          </div>
          <svg
            :viewBox="`0 0 ${W} ${H}`"
            preserveAspectRatio="none"
            class="pf-spark-svg"
          >
            <defs>
              <linearGradient :id="areaGradientId" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stop-color="#34d399" stop-opacity="0.35" />
                <stop offset="100%" stop-color="#34d399" stop-opacity="0" />
              </linearGradient>
            </defs>
            <line
              v-for="tick in yAxisTicks"
              :key="tick.label"
              :x1="PAD.l"
              :x2="PAD.l + geometry.w"
              :y1="PAD.t + ((MAX - tick.value) / (MAX - MIN)) * (H - PAD.t - PAD.b)"
              :y2="PAD.t + ((MAX - tick.value) / (MAX - MIN)) * (H - PAD.t - PAD.b)"
              stroke="#38516d"
              stroke-opacity="0.36"
              stroke-width="0.5"
              stroke-dasharray="2 3"
            />
            <rect v-if="geometry.band" data-test="pf-target-band" :x="PAD.l" :y="geometry.band.y" :width="geometry.w" :height="geometry.band.h" fill="#34d399" fill-opacity="0.06" />
            <line v-if="geometry.band" :x1="PAD.l" :x2="PAD.l + geometry.w" :y1="geometry.band.bot" :y2="geometry.band.bot" stroke="#34d399" stroke-opacity="0.25" stroke-dasharray="2 3" />
            <path :d="geometry.area" :fill="`url(#${areaGradientId})`" />
            <path data-test="pf-spark-line" :d="geometry.line" fill="none" stroke="#34d399" stroke-width="1.4" stroke-linejoin="round" stroke-linecap="round" />
            <circle :cx="geometry.last[0]" :cy="geometry.last[1]" r="3" fill="#34d399" />
          </svg>
          <div
            class="pf-x-axis"
            data-test="pf-x-axis"
          >
            <span
              v-for="tick in xAxisTicks"
              :key="tick"
            >{{ tick }}</span>
          </div>
        </div>
        <div v-else class="pf-spark-empty">趋势数据不足</div>
      </div>

      <div
        class="pf-window"
        data-test="pf-window-summary"
      >
        {{ windowSummary }}
      </div>

      <div class="pf-stats">
        <div class="pf-stat"><span class="pf-stat-lbl">有功 P</span><span class="pf-stat-val cyan">{{ fmt(p) }} <i>kW</i></span></div>
        <div class="pf-stat"><span class="pf-stat-lbl">无功 Q</span><span class="pf-stat-val" :class="q !== null && q > 50 ? 'amber' : 'cyan'">{{ q !== null && q > 0 ? '+' : '' }}{{ fmt(q) }} <i>kVar</i></span></div>
        <div class="pf-stat"><span class="pf-stat-lbl">视在 S</span><span class="pf-stat-val">{{ fmt(apparentPower) }} <i>kVA</i></span></div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.pf-card {
  display: flex;
  flex-direction: column;
  background: #121d2e;
  border: 1px solid #1f2c41;
  border-radius: 10px;
  min-height: 0;
}
.rt-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 14px;
  border-bottom: 1px solid #1f2c41;
}
.rt-card-title {
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
}
.rt-sub {
  color: #5e6c83;
  font-weight: 400;
}
.pf-tabs {
  display: flex;
  gap: 2px;
  padding: 3px;
  background: #0b1623;
  border: 1px solid #1f2c41;
  border-radius: 8px;
}
.pf-tab {
  padding: 4px 9px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #9aa7bd;
  font: inherit;
  font-size: 11px;
  cursor: pointer;
}
.pf-tab.is-active {
  background: #182538;
  color: #67e8f9;
  box-shadow: inset 0 0 0 1px rgba(34, 211, 238, 0.25);
}
.pf-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 14px;
  flex: 1;
  min-height: 0;
}
.pf-readout {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}
.pf-big {
  font-size: 44px;
  line-height: 0.95;
  font-weight: 300;
  color: #34d399;
  font-variant-numeric: tabular-nums;
}
.pf-unit {
  color: #9aa7bd;
  padding-bottom: 5px;
}
.pf-delta {
  margin-left: auto;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}
.pf-delta.is-up { color: #34d399; }
.pf-delta.is-down { color: #f59e0b; }
.pf-spark {
  flex: 1;
  min-height: 84px;
}
.pf-plot {
  position: relative;
  height: 100%;
  min-height: 84px;
  padding: 0 0 16px 26px;
}
.pf-spark-svg {
  width: 100%;
  height: 100%;
  display: block;
}
.pf-y-axis {
  position: absolute;
  inset: 0 auto 16px 0;
  width: 22px;
  color: #6f819d;
  font-size: 9px;
  font-variant-numeric: tabular-nums;
}
.pf-y-axis span {
  position: absolute;
  right: 4px;
  transform: translateY(-50%);
}
.pf-x-axis {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 26px;
  display: flex;
  justify-content: space-between;
  color: #6f819d;
  font-size: 9px;
  font-variant-numeric: tabular-nums;
}
.pf-spark-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #5e6c83;
  font-size: 11px;
}
.pf-window {
  margin-top: -3px;
  color: #6f819d;
  font-size: 10px;
  font-variant-numeric: tabular-nums;
  text-align: right;
}
.pf-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding-top: 6px;
  border-top: 1px solid #1f2c41;
}
.pf-stat-lbl {
  display: block;
  font-size: 10px;
  color: #5e6c83;
}
.pf-stat-val {
  font-size: 14px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  color: #e5edf7;
}
.pf-stat-val i {
  font-size: 11px;
  font-style: normal;
  color: #5e6c83;
}
.pf-stat-val.cyan { color: #67e8f9; }
.pf-stat-val.amber { color: #f59e0b; }
</style>
