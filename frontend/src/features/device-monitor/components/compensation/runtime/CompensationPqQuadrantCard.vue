<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { CompensationPqModel, CompensationPqReferenceLine } from '../types'

const props = defineProps({
  model: {
    type: Object as PropType<CompensationPqModel>,
    default: () => ({
      point: { p: null, q: null },
      history: [],
      axis: { pMax: 400, qMax: 200 },
      referenceLines: [],
      targetPowerFactor: null,
    }),
  },
})

const W = 380
const H = 240
const CX = W / 2
const CY = H / 2
const SCALE = Math.min(W * 0.42, H * 0.42)

function toXY(p: number, q: number): [number, number] {
  const pMax = props.model.axis.pMax > 0 ? props.model.axis.pMax : 400
  const qMax = props.model.axis.qMax > 0 ? props.model.axis.qMax : 200
  return [CX + (p / pMax) * SCALE, CY - (q / qMax) * SCALE]
}

const hasPoint = computed(() => props.model.point.p !== null && props.model.point.q !== null)

const current = computed(() => {
  if (!hasPoint.value) return null
  return toXY(props.model.point.p as number, props.model.point.q as number)
})

const historyPath = computed(() => {
  if (props.model.history.length < 2) return ''
  return props.model.history
    .map((pt, i) => {
      const [x, y] = toXY(pt[0], pt[1])
      return `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`
    })
    .join(' ')
})

function lineColor(line: CompensationPqReferenceLine): string {
  return line.role === 'target' ? '#34d399' : '#f59e0b'
}

const pfLineGeometry = computed(() =>
  props.model.referenceLines
    .filter((line) => line.powerFactor > 0 && line.powerFactor < 1)
    .map((line) => {
      const ang = Math.acos(line.powerFactor)
      const pMax = props.model.axis.pMax > 0 ? props.model.axis.pMax : 400
      const qMax = props.model.axis.qMax > 0 ? props.model.axis.qMax : 200
      const k = (pMax / qMax) * Math.tan(ang)
      const norm = Math.sqrt(1 + k * k)
      const x1 = CX + SCALE / norm
      const yLag = CY - (k * SCALE) / norm
      const yLead = CY + (k * SCALE) / norm
      return { ...line, color: lineColor(line), x1, yLag, yLead }
    }),
)

const targetZonePath = computed(() => {
  const t = pfLineGeometry.value.find((l) => l.role === 'target')
  if (!t) return ''
  return `M ${CX} ${CY} L ${t.x1.toFixed(1)} ${t.yLag.toFixed(1)} L ${t.x1.toFixed(1)} ${t.yLead.toFixed(1)} Z`
})
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

        <path :d="targetZonePath" fill="url(#pqTarget)" />

        <g v-for="l in pfLineGeometry" :key="`${l.role}-${l.powerFactor}`" :stroke="l.color" stroke-opacity="0.35" stroke-dasharray="3 4">
          <line :x1="CX" :y1="CY" :x2="l.x1" :y2="l.yLag" />
          <line :x1="CX" :y1="CY" :x2="l.x1" :y2="l.yLead" />
          <text :x="l.x1 + 3" :y="l.yLag - 2" :fill="l.color" fill-opacity="0.7" font-size="9">{{ l.label }}</text>
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
              P {{ model.point.p }} · Q {{ (model.point.q as number) > 0 ? '+' : '' }}{{ model.point.q }}
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
