<script setup lang="ts">
defineProps<{
  stats: Array<{ label: string; value: string }>
}>()
</script>

<template>
  <section class="glass-card trend-panel">
    <div class="trend-panel__head">
      <div class="trend-panel__title-block">
        <span class="card-eyebrow">Park Load Trend</span>
        <span class="card-title">园区负荷趋势</span>
      </div>
      <div class="trend-stats">
        <div
          v-for="item in stats"
          :key="item.label"
          class="trend-stat"
        >
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>
    </div>

    <div class="trend-chart-area">
      <slot name="chart" />
    </div>
  </section>
</template>

<style scoped>
.trend-panel {
  padding: 14px 14px 10px;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.trend-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.trend-panel__title-block {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.card-eyebrow {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: rgba(255, 255, 255, 0.38);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.trend-stats {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.trend-stat {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 1px;
  padding: 5px 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.05);
  min-width: 64px;
}

.trend-stat span {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: rgba(255, 255, 255, 0.4);
}

.trend-stat strong {
  font-size: 12px;
  font-weight: 600;
  color: #cce4ff;
  letter-spacing: -0.01em;
}

.trend-chart-area {
  flex: 1 1 auto;
  min-height: 220px;
  width: 100%;
}
</style>
