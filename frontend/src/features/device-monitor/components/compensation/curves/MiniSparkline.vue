<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  data: Array<number | null | undefined>
  color?: string
  height?: number
  domain?: [number, number]
  refValue?: number | null
  refColor?: string
  area?: boolean
}>(), {
  color: '#3d8bff',
  height: 40,
  domain: undefined,
  refValue: null,
  refColor: '#f87171',
  area: true,
})

const WIDTH = 160

const sanitized = computed(() =>
  props.data.map((v) => (typeof v === 'number' && Number.isFinite(v) ? v : null)),
)

const geometry = computed(() => {
  const values = sanitized.value
  const valid = values.filter((v): v is number => v !== null)
  if (valid.length < 2) return null
  const h = props.height
  let min: number
  let max: number
  if (props.domain) {
    ;[min, max] = props.domain
  } else {
    min = Math.min(...valid)
    max = Math.max(...valid)
    if (max - min < 1e-6) {
      const pad = Math.abs(max) * 0.05 || 1
      min -= pad
      max += pad
    }
  }
  const span = max - min || 1
  const lastIndex = values.length - 1
  const toY = (v: number) => 2 + (1 - (v - min) / span) * (h - 4)

  const segments: string[] = []
  let cur: string[] = []
  values.forEach((v, i) => {
    const x = (i / lastIndex) * WIDTH
    if (v === null) {
      if (cur.length > 1) segments.push(cur.join(' '))
      cur = []
      return
    }
    cur.push(`${x.toFixed(2)},${toY(v).toFixed(2)}`)
  })
  if (cur.length > 1) segments.push(cur.join(' '))
  const refY = props.refValue != null ? toY(props.refValue) : null
  const lastVal = valid[valid.length - 1]
  const lastY = toY(lastVal)
  return { segments, refY, lastY, lastX: WIDTH }
})
</script>

<template>
  <svg
    v-if="geometry"
    :viewBox="`0 0 ${WIDTH} ${height}`"
    preserveAspectRatio="none"
    class="mini-spark"
    :style="{ height: `${height}px` }"
  >
    <polyline
      v-if="area && geometry.segments.length"
      :points="`0,${height} ${geometry.segments[geometry.segments.length - 1]} ${WIDTH},${height}`"
      :fill="color"
      fill-opacity="0.12"
      stroke="none"
    />
    <polyline
      v-for="(seg, i) in geometry.segments"
      :key="i"
      :points="seg"
      fill="none"
      :stroke="color"
      stroke-width="1.5"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <line
      v-if="geometry.refY != null"
      x1="0"
      :x2="WIDTH"
      :y1="geometry.refY"
      :y2="geometry.refY"
      :stroke="refColor"
      stroke-width="1"
      stroke-dasharray="3 3"
      opacity="0.6"
    />
    <circle
      :cx="geometry.lastX"
      :cy="geometry.lastY"
      r="2"
      :fill="color"
    />
  </svg>
  <div
    v-else
    class="mini-spark mini-spark--empty"
    :style="{ height: `${height}px` }"
  >
    暂无数据
  </div>
</template>

<style scoped>
.mini-spark {
  display: block;
  width: 100%;
}

.mini-spark--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #5d7197;
  font-size: 10px;
  letter-spacing: 0.5px;
}
</style>
