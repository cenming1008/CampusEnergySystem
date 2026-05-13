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

function stateTagText(state?: MonitorMetricCard['state']) {
  if (state === 'live') return '实时'
  if (state === 'mock') return '估算'
  if (state === 'missing') return '缺测'
  return ''
}

function isUnavailable(item: MonitorMetricCard) {
  return item.state === 'missing' || item.value === null || item.value === undefined
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
      :class="{ 'is-unavailable': isUnavailable(item) }"
    >
      <div class="device-metric-card__head">
        <span class="device-metric-card__label">{{ item.label }}</span>
        <span
          v-if="stateTagText(item.state)"
          class="device-metric-card__tag"
          :class="`device-metric-card__tag--${item.state}`"
        >
          {{ stateTagText(item.state) }}
        </span>
      </div>

      <div class="device-metric-card__value">
        <strong>{{ formatValue(item) }}</strong>
        <small v-if="item.unit && !isUnavailable(item)">{{ item.unit }}</small>
      </div>
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
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.95), rgba(13, 22, 35, 0.98));
  border: 1px dashed rgba(72, 96, 130, 0.68);
  border-radius: 12px;
}

.device-metric-card {
  min-width: 0;
  min-height: 124px;
  padding: 16px 16px 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 18px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.95), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-top: 3px solid rgba(59, 130, 246, 0.25);
  border-radius: 12px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.device-metric-card__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;
}

.device-metric-card__label {
  min-width: 0;
  color: #8ea0bc;
  font-size: 12px;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.device-metric-card__tag {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  border: 1px solid rgba(72, 96, 130, 0.68);
  background: rgba(7, 15, 26, 0.48);
  color: #9fb1ca;
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
  flex: 0 0 auto;
}

.device-metric-card__tag--live {
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(34, 197, 94, 0.12);
  color: #4ade80;
}

.device-metric-card__tag--mock {
  border-color: rgba(251, 191, 36, 0.3);
  background: rgba(251, 191, 36, 0.12);
  color: #fbbf24;
}

.device-metric-card__tag--missing {
  border-color: rgba(251, 113, 133, 0.32);
  background: rgba(251, 113, 133, 0.12);
  color: #fb7185;
}

.device-metric-card__value {
  display: flex;
  align-items: baseline;
  gap: 5px;
  min-width: 0;
}

.device-metric-card__value strong {
  min-width: 0;
  color: #f5f7fb;
  font-size: 24px;
  line-height: 1;
  font-family: 'DIN Alternate', 'DIN', 'SFMono-Regular', monospace;
  overflow-wrap: anywhere;
}

.device-metric-card__value small {
  color: #7f93b2;
  font-size: 11px;
}

.device-metric-card.is-unavailable {
  border-top-color: rgba(100, 116, 139, 0.24);
}

.device-metric-card.is-unavailable .device-metric-card__value strong {
  color: #a8b6ca;
}

@media (min-width: 1920px) {
  .device-metric-grid {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }
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
