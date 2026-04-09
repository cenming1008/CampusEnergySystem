<script setup lang="ts">
defineProps<{
  alarms: Array<{ id: number | string; message: string; time: string }>
}>()
</script>

<template>
  <section class="glass-card alarm-feed-card" :class="{ 'alarm-feed-card--active': alarms.length > 0 }">
    <div class="card-head">
      <span class="card-eyebrow">Pending Alerts</span>
      <span class="card-title">告警信息</span>
      <span v-if="alarms.length > 0" class="alarm-badge">{{ alarms.length }}</span>
    </div>

    <div v-if="alarms.length > 0" class="alarm-list">
      <article
        v-for="alarm in alarms"
        :key="alarm.id"
        class="alarm-item"
      >
        <span class="alarm-item__pulse" />
        <div class="alarm-item__body">
          <strong>{{ alarm.message }}</strong>
          <span>{{ alarm.time }}</span>
        </div>
      </article>
    </div>

    <div v-else class="alarm-ok">
      <span class="alarm-ok__dot" />
      <div>
        <strong>系统运行稳定</strong>
        <span>当前无未处理告警</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.alarm-feed-card {
  padding: 14px;
}

.alarm-feed-card--active {
  background: rgba(248, 113, 113, 0.06);
  border-color: rgba(248, 113, 113, 0.14);
}

.card-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.card-eyebrow {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: rgba(255, 255, 255, 0.38);
  flex-basis: 100%;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: -0.02em;
  flex: 1;
}

.alarm-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: rgba(248, 113, 113, 0.25);
  color: #fca5a5;
  font-size: 11px;
  font-weight: 700;
}

.alarm-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.alarm-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(248, 113, 113, 0.08);
  border: 1px solid rgba(248, 113, 113, 0.15);
}

.alarm-item__pulse {
  width: 7px;
  height: 7px;
  margin-top: 4px;
  border-radius: 50%;
  background: #f87171;
  box-shadow: 0 0 8px rgba(248, 113, 113, 0.6);
  flex-shrink: 0;
  animation: pulse-alarm 1.6s ease-in-out infinite;
}

@keyframes pulse-alarm {
  0%, 100% { opacity: 1; box-shadow: 0 0 8px rgba(248, 113, 113, 0.6); }
  50% { opacity: 0.6; box-shadow: 0 0 16px rgba(248, 113, 113, 0.3); }
}

.alarm-item__body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.alarm-item__body strong {
  font-size: 12px;
  font-weight: 500;
  color: #fde8e8;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.alarm-item__body span {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
}

.alarm-ok {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(52, 211, 153, 0.07);
  border: 1px solid rgba(52, 211, 153, 0.15);
}

.alarm-ok__dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #34d399;
  box-shadow: 0 0 10px rgba(52, 211, 153, 0.5);
  flex-shrink: 0;
  animation: pulse-ok 2.4s ease-in-out infinite;
}

@keyframes pulse-ok {
  0%, 100% { box-shadow: 0 0 10px rgba(52, 211, 153, 0.5); }
  50% { box-shadow: 0 0 18px rgba(52, 211, 153, 0.25); }
}

.alarm-ok > div {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.alarm-ok strong {
  font-size: 12px;
  font-weight: 600;
  color: #a7f3d0;
}

.alarm-ok span {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.38);
}
</style>
