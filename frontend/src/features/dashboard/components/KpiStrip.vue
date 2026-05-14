<script setup lang="ts">
import { computed } from 'vue'

export type KpiStatus = 'ok' | 'notice' | 'warn' | 'err'

export interface KpiItem {
  label: string
  value: string
  unit?: string
  delta?: string
  deltaDir?: 'up' | 'down'
  sub?: string
  status?: KpiStatus
  spark?: number[]
  sparkColor?: string
}

interface Props {
  items: KpiItem[]
}
const props = defineProps<Props>()
const items = computed(() => props.items || [])

function sparkPath(data: number[], width: number, height: number) {
  if (!data.length) return { line: '', last: [0, 0] as [number, number] }
  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1
  const pts = data.map((d, i) => {
    const x = (i / Math.max(1, data.length - 1)) * width
    const y = height - ((d - min) / range) * (height - 4) - 2
    return [x, y] as [number, number]
  })
  const line = 'M ' + pts.map(p => p.join(',')).join(' L ')
  return { line, last: pts[pts.length - 1] }
}

function statusColor(s?: KpiStatus) {
  if (s === 'notice') return 'var(--notice)'
  if (s === 'warn') return 'var(--warn)'
  if (s === 'err') return 'var(--err)'
  return ''
}

function deltaColor(item: KpiItem) {
  if (item.status === 'err' || item.status === 'warn') return 'var(--err)'
  return item.deltaDir === 'up' ? 'var(--ok)' : 'var(--err)'
}
</script>

<template>
  <div class="kpi-strip">
    <div
      v-for="(item, i) in items"
      :key="i"
      class="kpi"
      :class="[
        item.status && item.status !== 'ok' ? 'has-status' : '',
        item.status === 'notice' ? 'a-glow-notice' : '',
        item.status === 'warn' ? 'a-glow-warn' : '',
        item.status === 'err' ? 'a-glow-err' : ''
      ]"
      :style="item.status && item.status !== 'ok' ? ({ '--sc': statusColor(item.status) } as Record<string, string>) : {}"
    >
      <span v-if="item.status && item.status !== 'ok'" class="corner a-pulse-ring" />
      <div class="row label-row">
        <span class="label">{{ item.label }}</span>
      </div>
      <div class="row value-row">
        <span class="value num">{{ item.value }}</span>
        <span v-if="item.unit" class="unit">{{ item.unit }}</span>
      </div>
      <div class="row bottom-row">
        <div class="delta-wrap">
          <span v-if="item.delta" class="delta mono" :style="{ color: deltaColor(item) }">
            {{ item.deltaDir === 'up' ? '↑' : '↓' }} {{ item.delta }}
          </span>
          <span v-if="item.sub" class="sub">{{ item.sub }}</span>
        </div>
        <svg v-if="item.spark && item.spark.length" width="64" height="22" class="spark">
          <path
            :d="sparkPath(item.spark, 64, 22).line"
            fill="none"
            :stroke="statusColor(item.status) || item.sparkColor || 'var(--accent)'"
            stroke-width="1.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <circle
            :cx="sparkPath(item.spark, 64, 22).last[0]"
            :cy="sparkPath(item.spark, 64, 22).last[1]"
            r="2.2"
            :fill="statusColor(item.status) || item.sparkColor || 'var(--accent)'"
          />
        </svg>
      </div>
    </div>
  </div>
</template>

<style scoped>
.kpi-strip { display: flex; gap: 12px; }
.kpi {
  flex: 1;
  min-width: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
}
.kpi.has-status {
  background: linear-gradient(180deg, color-mix(in srgb, var(--sc) 7%, transparent), var(--surface) 60%);
  border-color: color-mix(in srgb, var(--sc) 35%, transparent);
}
.corner {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 8px;
  height: 8px;
  border-radius: 4px;
  background: var(--sc);
  color: var(--sc);
}
.row { display: flex; align-items: center; }
.label-row { justify-content: space-between; padding-right: 18px; }
.label { font-size: 11px; color: var(--text-mid); letter-spacing: 0.3px; }
.kpi.has-status .label { color: var(--sc); font-weight: 600; }
.value-row { align-items: flex-end; gap: 4px; }
.value { font-size: 30px; font-weight: 600; color: var(--text); line-height: 1; }
.unit { font-size: 12px; color: var(--text-mid); margin-bottom: 4px; }
.bottom-row { justify-content: space-between; margin-top: 2px; }
.delta-wrap { display: flex; align-items: center; gap: 6px; font-size: 11px; min-width: 0; }
.delta { font-weight: 600; }
.sub { color: var(--text-dim); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.spark { display: block; flex: 0 0 auto; }
</style>
