<script setup lang="ts">
import type { MonitorMetricCard } from '@/api/deviceMonitor'

defineProps<{
  metrics: MonitorMetricCard[]
}>()

function formatValue(item: MonitorMetricCard) {
  if (item.state === 'missing' || item.value === null || item.value === undefined) return '--'
  if (typeof item.value === 'number') return Number(item.value).toFixed(item.precision ?? 1)
  return String(item.value)
}
</script>

<template>
  <div class="device-metric-grid">
    <div
      v-if="metrics.length === 0"
      class="device-metric-grid__empty"
    >
      暂无指标数据
    </div>
    <div
      v-for="item in metrics"
      :key="item.key"
      class="device-metric-card"
    >
      <span class="device-metric-card__label">{{ item.label }}</span>
      <strong>{{ formatValue(item) }}</strong>
      <small>{{ item.unit || '' }}</small>
    </div>
  </div>
</template>

<style scoped>
.device-metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.device-metric-grid__empty {
  grid-column: 1 / -1;
  padding: 24px;
  color: #8ea0bc;
  text-align: center;
  background: #131d2b;
  border: 1px dashed #2f3d52;
  border-radius: 8px;
}

.device-metric-card {
  min-width: 0;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: #131d2b;
  border: 1px solid #243244;
  border-radius: 14px;
}

.device-metric-card__label {
  font-size: 12px;
  color: #8ea0bc;
  overflow-wrap: anywhere;
}

.device-metric-card strong {
  min-width: 0;
  font-size: 24px;
  color: #f8fafc;
  font-family: 'DIN', 'Monaco', monospace;
  overflow-wrap: anywhere;
}

.device-metric-card small {
  min-height: 16px;
  color: #8ea0bc;
}

@media (max-width: 1100px) {
  .device-metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .device-metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>
