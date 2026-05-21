<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = withDefaults(defineProps<{
  baseWidth?: number
  minScale?: number
  maxScale?: number
}>(), {
  baseWidth: 1680,
  minScale: 0.6,
  maxScale: 1.22,
})

const shellRef = ref<HTMLElement | null>(null)
const canvasRef = ref<HTMLElement | null>(null)
const scale = ref(1)
const shellHeight = ref(0)

let shellObserver: ResizeObserver | null = null
let canvasObserver: ResizeObserver | null = null

const canvasStyle = computed(() => ({
  width: `${props.baseWidth}px`,
  transform: `translateX(-50%) scale(${scale.value})`,
}))

const shellStyle = computed(() => ({
  minHeight: shellHeight.value ? `${shellHeight.value}px` : undefined,
}))

function clampScale(value: number) {
  return Math.min(props.maxScale, Math.max(props.minScale, value))
}

function updateHeight() {
  const canvas = canvasRef.value
  if (!canvas) return

  shellHeight.value = Math.ceil(canvas.scrollHeight * scale.value)
}

function updateScale() {
  const shell = shellRef.value
  if (!shell) return

  scale.value = clampScale(shell.clientWidth / props.baseWidth)
  updateHeight()
}

function scheduleMeasure() {
  void nextTick(updateScale)
}

onMounted(() => {
  scheduleMeasure()
  window.addEventListener('resize', scheduleMeasure)

  if ('ResizeObserver' in window) {
    shellObserver = new ResizeObserver(scheduleMeasure)
    canvasObserver = new ResizeObserver(updateHeight)
    if (shellRef.value) shellObserver.observe(shellRef.value)
    if (canvasRef.value) canvasObserver.observe(canvasRef.value)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', scheduleMeasure)
  shellObserver?.disconnect()
  canvasObserver?.disconnect()
})

watch(() => [props.baseWidth, props.minScale, props.maxScale], scheduleMeasure)
</script>

<template>
  <div
    ref="shellRef"
    class="monitor-scale-shell"
    :style="shellStyle"
  >
    <div
      ref="canvasRef"
      class="monitor-scale-shell__canvas"
      :style="canvasStyle"
    >
      <slot />
    </div>
  </div>
</template>

<style scoped>
.monitor-scale-shell {
  position: relative;
  width: 100%;
  min-width: 0;
}

.monitor-scale-shell__canvas {
  position: absolute;
  top: 0;
  left: 50%;
  transform-origin: top center;
}
</style>
