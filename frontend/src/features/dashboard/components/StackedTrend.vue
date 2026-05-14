<script setup lang="ts">
import { computed, ref } from 'vue'

export interface TrendSeries {
  key: string
  name: string
  color: string
  data: number[]
  unit?: string
}

interface Props {
  series: TrendSeries[]
  title?: string
  subtitle?: string
}
const props = withDefaults(defineProps<Props>(), {
  title: '园区负荷趋势',
  subtitle: ''
})

const N = computed(() => props.series[0]?.data.length || 0)
const mode = ref<'abs' | 'pct'>('abs')
const range = ref<'today' | 'yest' | 'week' | 'month'>('today')
const visible = ref<Record<string, boolean>>({})
const hoverIdx = ref<number | null>(null)

// initialize visibility
const visMap = computed<Record<string, boolean>>(() => {
  const out: Record<string, boolean> = {}
  for (const s of props.series) {
    out[s.key] = visible.value[s.key] ?? true
  }
  return out
})

const W = 900
const H = 300
const pad = { l: 38, r: 16, t: 8, b: 24 }
const innerW = W - pad.l - pad.r
const innerH = H - pad.t - pad.b

const visSeries = computed(() => props.series.filter(s => visMap.value[s.key]))

const stack = computed(() => visSeries.value.map(s => s.data))

const stackEff = computed(() => {
  if (mode.value !== 'pct') return stack.value
  return stack.value.map(arr => arr.map((_, j) => {
    const total = stack.value.reduce((a, c) => a + (c[j] || 0), 0) || 1
    return ((arr[j] || 0) / total) * 100
  }))
})

const cum = computed(() => {
  const eff = stackEff.value
  if (eff.length === 0) return [] as number[][]
  const n = eff[0].length
  return eff.map((_, i) => {
    return Array.from({ length: n }, (_, j) => eff.slice(0, i + 1).reduce((a, c) => a + (c[j] || 0), 0))
  })
})

const maxY = computed(() => {
  if (cum.value.length === 0) return 1
  if (mode.value === 'pct') return 100
  return Math.max(...cum.value[cum.value.length - 1]) * 1.08 || 1
})

function xAt(i: number) {
  const n = N.value
  return pad.l + (n <= 1 ? 0 : (i / (n - 1)) * innerW)
}
function yAt(v: number) {
  return pad.t + innerH - (v / maxY.value) * innerH
}

const cursorIdx = computed(() => {
  if (hoverIdx.value != null) return hoverIdx.value
  return Math.max(0, Math.min(N.value - 1, Math.floor(N.value * 0.625)))
})

const areaPaths = computed(() => {
  const c = cum.value
  if (c.length === 0) return [] as { d: string; color: string; key: string }[]
  const n = N.value
  return c.map((top, i) => {
    const bottom = i === 0 ? Array(n).fill(0) : c[i - 1]
    let p = `M ${xAt(0)},${yAt(top[0])}`
    for (let k = 1; k < n; k++) p += ` L ${xAt(k)},${yAt(top[k])}`
    for (let k = n - 1; k >= 0; k--) p += ` L ${xAt(k)},${yAt(bottom[k])}`
    p += ' Z'
    return { d: p, color: visSeries.value[i].color, key: visSeries.value[i].key }
  })
})

const cursorTotal = computed(() => {
  return props.series.reduce((a, s) => a + (visMap.value[s.key] ? (s.data[cursorIdx.value] || 0) : 0), 0)
})

const cursorBreak = computed(() => {
  const t = cursorTotal.value
  return props.series.map(s => ({
    name: s.name,
    color: s.color,
    value: s.data[cursorIdx.value] || 0,
    visible: !!visMap.value[s.key],
    pct: t > 0 ? ((s.data[cursorIdx.value] || 0) / t) * 100 : 0
  }))
})

const totalCurve = computed(() => {
  if (cum.value.length === 0) return Array(N.value).fill(0)
  return cum.value[cum.value.length - 1]
})

const stats = computed(() => {
  const arr = totalCurve.value
  const cur = arr[cursorIdx.value] || 0
  const peak = arr.length ? Math.max(...arr) : 0
  const valley = arr.length ? Math.min(...arr) : 0
  const avg = arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0
  return { cur, peak, valley, avg, gap: peak - valley }
})

const hourTicks = [0, 4, 8, 12, 16, 20, 24]
const ranges: { k: 'today' | 'yest' | 'week' | 'month'; n: string }[] = [
  { k: 'today', n: '今日' }, { k: 'yest', n: '昨日' }, { k: 'week', n: '本周' }, { k: 'month', n: '本月' }
]

function onMove(e: MouseEvent) {
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const x = e.clientX - rect.left
  const ratio = Math.max(0, Math.min(1, x / rect.width))
  hoverIdx.value = Math.round(ratio * (N.value - 1))
}

function toggle(key: string) {
  visible.value = { ...visMap.value, [key]: !visMap.value[key] }
}

const cursorClockLabel = computed(() => {
  const minutes = Math.round((cursorIdx.value / Math.max(1, N.value)) * 24 * 60)
  const hh = String(Math.floor(minutes / 60)).padStart(2, '0')
  const mm = String(minutes % 60).padStart(2, '0')
  return `${hh}:${mm}`
})

const placeTooltipRight = computed(() => {
  if (N.value <= 1) return true
  return (cursorIdx.value / (N.value - 1)) < 0.5
})

function fmt(v: number) {
  return mode.value === 'pct' ? v.toFixed(1) : v.toFixed(0)
}
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
          v-for="s in series"
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

    <div class="chart-wrap" @mousemove="onMove" @mouseleave="hoverIdx = null">
      <svg :viewBox="`0 0 ${W} ${H}`" preserveAspectRatio="none" class="chart-svg">
        <line
          v-for="t in [0, 0.25, 0.5, 0.75, 1]"
          :key="`g${t}`"
          :x1="pad.l" :x2="W - pad.r"
          :y1="pad.t + innerH * t" :y2="pad.t + innerH * t"
          :stroke="'rgba(255,255,255,0.06)'"
          :stroke-dasharray="t === 1 ? '0' : '2 4'"
        />
        <text
          v-for="t in [0, 0.25, 0.5, 0.75, 1]"
          :key="`yl${t}`"
          :x="pad.l - 6" :y="pad.t + innerH * t + 3"
          text-anchor="end"
          font-size="9"
          fill="var(--text-dim)"
          font-family="var(--mono)"
        >{{ mode === 'pct' ? `${Math.round((1 - t) * 100)}%` : Math.round(maxY * (1 - t)) }}</text>
        <text
          v-for="h in hourTicks"
          :key="`xt${h}`"
          :x="pad.l + (h / 24) * innerW" :y="H - 6"
          text-anchor="middle"
          font-size="9"
          fill="var(--text-dim)"
          font-family="var(--mono)"
        >{{ String(h).padStart(2, '0') }}:00</text>
        <path
          v-for="a in areaPaths"
          :key="a.key"
          :d="a.d"
          :fill="a.color"
          fill-opacity="0.55"
          :stroke="a.color"
          stroke-width="1"
          stroke-opacity="0.9"
        />
        <line
          v-if="N > 0"
          :x1="xAt(cursorIdx)" :x2="xAt(cursorIdx)"
          :y1="pad.t" :y2="pad.t + innerH"
          stroke="var(--text)"
          stroke-opacity="0.4"
          stroke-dasharray="3 3"
        />
        <circle
          v-if="cum.length > 0"
          :cx="xAt(cursorIdx)"
          :cy="yAt(cum[cum.length - 1][cursorIdx])"
          r="4"
          fill="var(--bg)"
          stroke="var(--accent)"
          stroke-width="2"
        />
      </svg>
      <div
        v-if="N > 0"
        class="tooltip"
        :style="placeTooltipRight
          ? { left: `calc(${(xAt(cursorIdx) / W) * 100}% + 14px)` }
          : { right: `calc(${100 - (xAt(cursorIdx) / W) * 100}% + 14px)` }"
      >
        <div class="tt-head">
          <span class="mono">{{ cursorClockLabel }}</span>
          <span class="mono total">{{ cursorTotal.toFixed(0) }} {{ mode === 'pct' ? '%' : 'kW' }}</span>
        </div>
        <div
          v-for="b in cursorBreak"
          :key="b.name"
          class="tt-row"
          :class="{ off: !b.visible }"
        >
          <span class="dot" :style="{ background: b.color }" />
          <span class="nm">{{ b.name }}</span>
          <span class="vl mono">{{ b.value.toFixed(1) }}</span>
          <span class="pc mono">{{ b.visible ? b.pct.toFixed(1) + '%' : '—' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stacked-trend {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.head { display: flex; align-items: baseline; justify-content: space-between; }
.head-left { display: flex; align-items: baseline; gap: 12px; }
.title { font-size: 13px; font-weight: 600; color: var(--text); }
.subtitle { font-size: 11px; color: var(--text-dim); }
.head-right { display: flex; gap: 12px; }
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
  gap: 22px;
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
.chart-wrap { position: relative; }
.chart-svg { width: 100%; height: 300px; display: block; }
.tooltip {
  position: absolute;
  top: 8px;
  background: var(--surface-hi);
  border: 1px solid var(--border-hi);
  border-radius: 6px;
  padding: 8px 10px;
  min-width: 180px;
  pointer-events: none;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}
.tt-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; }
.tt-head .mono { font-size: 11px; color: var(--text); font-weight: 600; }
.tt-head .total { color: var(--accent); font-weight: 600; }
.tt-row {
  display: grid;
  grid-template-columns: 7px 1fr 50px 40px;
  align-items: center;
  gap: 6px;
  padding: 3px 0;
  font-size: 11px;
}
.tt-row.off { opacity: 0.4; }
.tt-row .dot { width: 7px; height: 7px; border-radius: 2px; }
.tt-row .nm { color: var(--text-mid); }
.tt-row .vl { color: var(--text); text-align: right; }
.tt-row .pc { color: var(--text-dim); font-size: 10px; text-align: right; }
</style>
