<script setup lang="ts">
defineProps<{
  todayEnergy: number
  monthlyEnergy: number
}>()

function fmt(v: number, d = 1) {
  return Number.isFinite(v) ? v.toFixed(d) : '0.0'
}
</script>

<template>
  <section class="glass-card energy-mix-card">
    <div class="card-head">
      <span class="card-eyebrow">Energy Mix</span>
      <span class="card-title">能源介质占比</span>
    </div>

    <div class="pie-wrap">
      <slot name="chart" />
    </div>

    <div class="energy-totals">
      <div class="energy-total-item">
        <span>今日能耗</span>
        <div class="energy-total-item__value">
          <strong>{{ fmt(todayEnergy) }}</strong>
          <small>kWh</small>
        </div>
      </div>
      <div class="energy-total-divider" />
      <div class="energy-total-item">
        <span>月度能耗</span>
        <div class="energy-total-item__value">
          <strong>{{ fmt(monthlyEnergy) }}</strong>
          <small>kWh</small>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.energy-mix-card {
  padding: 14px;
  min-height: 0;
}

.card-head {
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin-bottom: 8px;
}

.card-eyebrow {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: rgba(255, 255, 255, 0.38);
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.pie-wrap {
  flex: 1 1 auto;
  min-height: 160px;
  width: 100%;
}

.energy-totals {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.energy-total-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.energy-total-item span {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.44);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.energy-total-item__value {
  display: flex;
  align-items: baseline;
  gap: 3px;
}

.energy-total-item__value strong {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: #eef5ff;
}

.energy-total-item__value small {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.42);
}

.energy-total-divider {
  width: 1px;
  height: 28px;
  background: rgba(255, 255, 255, 0.08);
}
</style>
