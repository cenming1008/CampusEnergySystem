<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { CompensationPqPoint } from '../types'

const props = defineProps({
  point: { type: Object as PropType<CompensationPqPoint>, default: () => ({ p: null, q: null }) },
  history: { type: Array as PropType<Array<[number, number]>>, default: () => [] },
})

const W = 380
const H = 240
const CX = W / 2
const CY = H / 2
const SCALE = Math.min(W * 0.42, H * 0.42)
const P_MAX = 400
const Q_MAX = 200

function toXY(p: number, q: number): [number, number] {
  return [CX + (p / P_MAX) * SCALE, CY - (q / Q_MAX) * SCALE]
}

const hasPoint = computed(() => props.point.p !== null && props.point.q !== null)

const current = computed(() => {
  if (!hasPoint.value) return null
  return toXY(props.point.p as number, props.point.q as number)
})

const historyPath = computed(() => {
  if (props.history.length < 2) return ''
  return props.history
    .map((pt, i) => {
      const [x, y] = toXY(pt[0], pt[1])
      return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`
    })
    .join(' ')
})

const pfLines = [
  { pf: 0.9, color: '#f59e0b' },
  { pf: 0.95, color: '#34d399' },
]

const pfLineGeometry = computed(() =>
  pfLines.map((l) => {
    const ang = Math.acos(l.pf)
    const x1 = CX + Math.cos(ang) * SCALE
    const yLag = CY - Math.sin(ang) * SCALE
    const yLead = CY + Math.sin(ang) * SCALE
    return { ...l, x1, yLag, yLead }
  }),
)
</script>

<template>
  <section class="pq-card">
    <header class="rt-card-head">
      <span class="rt-card-title"><span class="rt-accent" />P-Q 运行象限 <span class="rt-sub">补偿轨迹</span></span>
      <div class="pq-legend">
        <span><i class="sw" style="background:#34d399;opacity:.5" />目标区</span>
        <span><i class="sw" style="background:#22d3ee" />当前点</span>
      </div>
    </header>

    <div class="pq-body">
      <svg :viewBox="`0 0 ${W} ${H}`" preserveAspectRatio="xMidYMid meet" class="pq-svg">
        <defs>
          <radialGradient id="pqGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#22d3ee" stop-opacity="0.8" />
            <stop offset="100%" stop-color="#22d3ee" stop-opacity="0" />
          </radialGradient>
          <radialGradient id="pqTarget" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#34d399" stop-opacity="0.18" />
            <stop offset="100%" stop-color="#34d399" stop-opacity="0" />
          </radialGradient>
        </defs>

        <rect x="0" y="0" :width="W" :height="CY" fill="#0e1828" fill-opacity="0.4" />
        <circle v-for="r in [0.33, 0.66, 1]" :key="r" :cx="CX" :cy="CY" :r="SCALE * r" fill="none" stroke="#1f2c41" stroke-dasharray="2 3" />

        <path
          :d="`M ${CX} ${CY} L ${CX + SCALE * 0.95} ${CY - SCALE * 0.31} A ${SCALE} ${SCALE} 0 0 0 ${CX + SCALE * 0.95} ${CY + SCALE * 0.31} Z`"
          fill="url(#pqTarget)"
        />

        <g v-for="l in pfLineGeometry" :key="l.pf" :stroke="l.color" stroke-opacity="0.35" stroke-dasharray="3 4">
          <line :x1="CX" :y1="CY" :x2="l.x1" :y2="l.yLag" />
          <line :x1="CX" :y1="CY" :x2="l.x1" :y2="l.yLead" />
          <text :x="l.x1 + 3" :y="l.yLag - 2" :fill="l.color" fill-opacity="0.7" font-size="9">PF {{ l.pf }}</text>
        </g>

        <line x1="14" :y1="CY" :x2="W - 14" :y2="CY" stroke="#2a3a55" />
        <line :x1="CX" y1="14" :x2="CX" :y2="H - 14" stroke="#2a3a55" />
        <text :x="W - 6" :y="CY - 5" fill="#9aa7bd" font-size="9" text-anchor="end">+P kW</text>
        <text :x="CX + 6" y="20" fill="#9aa7bd" font-size="9">+Q 感性</text>
        <text :x="CX + 6" :y="H - 6" fill="#9aa7bd" font-size="9">-Q 容性</text>

        <path
          v-if="historyPath"
          data-test="pq-history-path"
          :d="historyPath"
          fill="none"
          stroke="#22d3ee"
          stroke-opacity="0.35"
          stroke-width="1.2"
          stroke-dasharray="2 2"
        />

        <g v-if="current" data-test="pq-current-point">
          <circle :cx="current[0]" :cy="current[1]" r="16" fill="url(#pqGlow)" />
          <circle :cx="current[0]" :cy="current[1]" r="5" fill="#22d3ee" stroke="#07101c" stroke-width="2" />
          <g :transform="`translate(${current[0] + 10}, ${current[1] - 10})`">
            <rect x="0" y="0" width="86" height="28" rx="5" fill="#0b1623" stroke="#22d3ee" stroke-opacity="0.5" />
            <text x="6" y="11" fill="#9aa7bd" font-size="8">当前运行点</text>
            <text x="6" y="22" fill="#67e8f9" font-size="10" font-weight="600">
              P {{ point.p }} · Q {{ (point.q as number) > 0 ? '+' : '' }}{{ point.q }}
            </text>
          </g>
        </g>
        <circle :cx="CX" :cy="CY" r="2" fill="#5e6c83" />
      </svg>

      <div v-if="!hasPoint" class="pq-empty">等待实时遥测（有功 / 无功功率）</div>
    </div>
  </section>
</template>

<style scoped>
.pq-card {
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
.pq-legend {
  display: flex;
  gap: 10px;
  font-size: 11px;
  color: #5e6c83;
}
.pq-legend span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.pq-legend .sw {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}
.pq-body {
  position: relative;
  flex: 1;
  min-height: 0;
  padding: 8px 12px 10px;
}
.pq-svg {
  width: 100%;
  height: 100%;
  display: block;
}
.pq-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(11, 22, 35, 0.82);
  color: #9aa7bd;
  font-size: 12px;
}
</style>
