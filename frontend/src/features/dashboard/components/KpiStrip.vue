<script setup lang="ts">
defineProps<{
  currentLoad: number
  onlineCount: number
  totalCount: number
  alarmCount: number
  todayEnergy: number
  monthlyEnergy: number
  shift: string
}>()

function fmt(v: number, d = 1) {
  return Number.isFinite(v) ? v.toFixed(d) : '0.0'
}
</script>

<template>
  <div class="kpi-strip">
    <div class="kpi-tile kpi-tile--load">
      <span class="kpi-tile__label">实时负荷</span>
      <div class="kpi-tile__value">
        <strong>{{ fmt(currentLoad) }}</strong>
        <span class="kpi-tile__unit">kW</span>
      </div>
      <span class="kpi-tile__sub">{{ shift }}</span>
    </div>

    <div class="kpi-tile kpi-tile--device">
      <span class="kpi-tile__label">在线设备</span>
      <div class="kpi-tile__value">
        <strong>{{ onlineCount }}</strong>
        <span class="kpi-tile__unit">/ {{ totalCount }}</span>
      </div>
      <span class="kpi-tile__sub">在线率 {{ totalCount > 0 ? Math.round((onlineCount / totalCount) * 100) : 0 }}%</span>
    </div>

    <div class="kpi-tile" :class="alarmCount > 0 ? 'kpi-tile--alarm' : 'kpi-tile--safe'">
      <span class="kpi-tile__label">活跃告警</span>
      <div class="kpi-tile__value">
        <strong>{{ alarmCount }}</strong>
        <span class="kpi-tile__unit">条</span>
      </div>
      <span class="kpi-tile__sub">{{ alarmCount > 0 ? '需立即处理' : '系统稳定' }}</span>
    </div>

    <div class="kpi-tile kpi-tile--energy">
      <span class="kpi-tile__label">今日能耗</span>
      <div class="kpi-tile__value">
        <strong>{{ fmt(todayEnergy) }}</strong>
        <span class="kpi-tile__unit">kWh</span>
      </div>
      <span class="kpi-tile__sub">电 / 水 / 气 / 冷 / 热</span>
    </div>

    <div class="kpi-tile kpi-tile--monthly">
      <span class="kpi-tile__label">月度能耗</span>
      <div class="kpi-tile__value">
        <strong>{{ fmt(monthlyEnergy) }}</strong>
        <span class="kpi-tile__unit">kWh</span>
      </div>
      <span class="kpi-tile__sub">自然月累计</span>
    </div>
  </div>
</template>

<style scoped>
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
}

.kpi-tile {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px 16px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-bottom: 2px solid var(--kpi-accent, rgba(255,255,255,0.1));
  transition: background 0.18s ease;
}

.kpi-tile:hover {
  background: rgba(255, 255, 255, 0.06);
}

.kpi-tile--load   { --kpi-accent: #38bdf8; }
.kpi-tile--device { --kpi-accent: #34d399; }
.kpi-tile--alarm  { --kpi-accent: #f87171; }
.kpi-tile--safe   { --kpi-accent: #34d399; }
.kpi-tile--energy { --kpi-accent: #a78bfa; }
.kpi-tile--monthly { --kpi-accent: #fb923c; }

.kpi-tile__label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.46);
}

.kpi-tile__value {
  display: flex;
  align-items: baseline;
  gap: 5px;
  line-height: 1;
}

.kpi-tile__value strong {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -0.04em;
  color: #f0f6ff;
}

.kpi-tile__unit {
  font-size: 13px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.5);
}

.kpi-tile__sub {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.38);
  margin-top: 2px;
}

.kpi-tile--alarm .kpi-tile__value strong {
  color: #fca5a5;
}

.kpi-tile--safe .kpi-tile__value strong {
  color: #86efac;
}
</style>
