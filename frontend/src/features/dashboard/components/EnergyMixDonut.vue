<script setup lang="ts">
import { computed } from 'vue'

export interface MixItem {
  name: string
  value: number     // percentage (0-100)
  kwh: number
  color: string
}

interface Props {
  items: MixItem[]
  totalKwh?: number
  deltaPct?: number      // negative = ↓ vs yesterday
}
const props = defineProps<Props>()

const items = computed(() => props.items || [])
const total = computed(() => items.value.reduce((a, b) => a + b.value, 0) || 1)

const R = 56
const r = 38
const cx = 70
const cy = 70

const arcs = computed(() => {
  let a0 = -Math.PI / 2
  return items.value.map(it => {
    const a1 = a0 + (it.value / total.value) * Math.PI * 2
    const large = it.value / total.value > 0.5 ? 1 : 0
    const x0 = cx + R * Math.cos(a0), y0 = cy + R * Math.sin(a0)
    const x1 = cx + R * Math.cos(a1), y1 = cy + R * Math.sin(a1)
    const xi0 = cx + r * Math.cos(a0), yi0 = cy + r * Math.sin(a0)
    const xi1 = cx + r * Math.cos(a1), yi1 = cy + r * Math.sin(a1)
    const d = `M ${x0} ${y0} A ${R} ${R} 0 ${large} 1 ${x1} ${y1} L ${xi1} ${yi1} A ${r} ${r} 0 ${large} 0 ${xi0} ${yi0} Z`
    a0 = a1
    return { d, color: it.color, name: it.name }
  })
})

const centerLabel = computed(() => {
  const v = props.totalKwh ?? items.value.reduce((a, b) => a + b.kwh, 0)
  if (v >= 1000) return `${(v / 1000).toFixed(1)}k`
  return v.toFixed(0)
})

const deltaText = computed(() => {
  if (props.deltaPct == null) return ''
  const sign = props.deltaPct < 0 ? '↓' : '↑'
  return `${sign} ${Math.abs(props.deltaPct).toFixed(1)}% vs 昨日`
})

const deltaColor = computed(() => (props.deltaPct ?? 0) < 0 ? 'var(--accent)' : 'var(--warn)')
</script>

<template>
  <div class="card">
    <div class="card-head">
      <div class="title-block">
        <span class="title">能源介质占比</span>
        <span class="subtitle">今日累计</span>
      </div>
    </div>
    <div class="body">
      <svg width="140" height="140" class="donut">
        <path v-for="(a, i) in arcs" :key="i" :d="a.d" :fill="a.color" />
        <text :x="cx" :y="cy - 6" text-anchor="middle" font-size="20" fill="var(--text)" font-weight="700" font-family="var(--mono)">{{ centerLabel }}</text>
        <text :x="cx" :y="cy + 8" text-anchor="middle" font-size="9" fill="var(--text-dim)" font-family="var(--mono)">kWh 今日</text>
        <text v-if="deltaText" :x="cx" :y="cy + 22" text-anchor="middle" font-size="8" :fill="deltaColor" font-family="var(--mono)">{{ deltaText }}</text>
      </svg>
      <div class="legend">
        <div v-for="(it, i) in items" :key="i" class="lrow">
          <span class="ld" :style="{ background: it.color }" />
          <span class="ln">{{ it.name }}</span>
          <span class="lp mono">{{ it.value.toFixed(0) }}%</span>
          <span class="lk mono">{{ it.kwh.toLocaleString() }}</span>
          <span class="lu mono">kWh</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  flex: 0 0 280px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  box-sizing: border-box;
}
.card-head { margin-bottom: 12px; }
.title-block { display: flex; align-items: baseline; gap: 10px; }
.title { font-size: 13px; font-weight: 600; color: var(--text); letter-spacing: 0.2px; }
.subtitle { font-size: 11px; color: var(--text-dim); }
.body { display: flex; align-items: center; gap: 12px; }
.donut { flex: 0 0 auto; }
.legend { flex: 1; display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.lrow {
  display: grid;
  grid-template-columns: 8px 1fr 36px 52px 24px;
  align-items: center;
  column-gap: 6px;
}
.ld { width: 8px; height: 8px; border-radius: 2px; }
.ln { font-size: 11px; color: var(--text-mid); }
.lp { font-size: 11px; color: var(--text); text-align: right; font-weight: 600; }
.lk { font-size: 10px; color: var(--text-dim); text-align: right; }
.lu { font-size: 9px; color: var(--text-dim); }
</style>
