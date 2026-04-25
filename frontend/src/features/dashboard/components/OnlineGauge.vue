<script setup lang="ts">
defineProps<{
  onlineCount: number
  offlineCount: number
  totalCount: number
  onlineRate: number
}>()
</script>

<template>
  <section class="glass-card gauge-card">
    <div class="card-head">
      <span class="card-eyebrow">Campus Device Pulse</span>
      <span class="card-title">设备启用总览</span>
    </div>

    <div class="gauge-body">
      <div class="gauge-chart-wrap">
        <slot name="chart" />
      </div>

      <div class="gauge-stats">
        <div class="gauge-stat">
          <div class="gauge-stat__label">
            <span class="gauge-stat__dot gauge-stat__dot--online" />
            <span>启用设备</span>
          </div>
          <div class="gauge-stat__value">
            <strong>{{ onlineCount }}</strong>
            <small>台</small>
          </div>
        </div>

        <div class="gauge-stat" :class="{ 'gauge-stat--warn': offlineCount > 0 }">
          <div class="gauge-stat__label">
            <span class="gauge-stat__dot gauge-stat__dot--offline" />
            <span>停用设备</span>
          </div>
          <div class="gauge-stat__value">
            <strong>{{ offlineCount }}</strong>
            <small>台</small>
          </div>
        </div>

        <div class="gauge-stat gauge-stat--total">
          <div class="gauge-stat__label">
            <span>设备总数</span>
          </div>
          <div class="gauge-stat__value">
            <strong>{{ totalCount }}</strong>
            <small>台</small>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.gauge-card {
  padding: 14px;
}

.card-head {
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin-bottom: 10px;
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

.gauge-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.gauge-chart-wrap {
  width: 100%;
  height: 150px;
  flex-shrink: 0;
}

.gauge-stats {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.gauge-stat {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.04);
  transition: background 0.15s ease;
}

.gauge-stat--warn {
  background: rgba(248, 113, 113, 0.07);
  border-color: rgba(248, 113, 113, 0.15);
}

.gauge-stat--total {
  background: rgba(255, 255, 255, 0.05);
}

.gauge-stat__label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
}

.gauge-stat__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.gauge-stat__dot--online { background: #34d399; box-shadow: 0 0 6px rgba(52, 211, 153, 0.5); }
.gauge-stat__dot--offline { background: #f87171; box-shadow: 0 0 6px rgba(248, 113, 113, 0.4); }

.gauge-stat__value {
  display: flex;
  align-items: baseline;
  gap: 3px;
}

.gauge-stat__value strong {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: #eef5ff;
}

.gauge-stat--warn .gauge-stat__value strong {
  color: #fca5a5;
}

.gauge-stat__value small {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.42);
}
</style>
