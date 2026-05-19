<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { DeviceAlarmRecord } from '@/api/deviceMonitor'

const props = defineProps({
  rows: { type: Array as PropType<DeviceAlarmRecord[]>, default: () => [] },
  actionId: { type: Number as PropType<number | null>, default: null },
})

const emit = defineEmits<{
  (e: 'resolve', row: DeviceAlarmRecord): void
  (e: 'view-all'): void
}>()

const unresolved = computed(() => props.rows.filter((r) => !r.is_resolved))

function sevClass(severity: string | undefined): string {
  if (severity === 'critical') return 'crit'
  if (severity === 'warning') return 'warn'
  return 'info'
}

function sevLabel(severity: string | undefined): string {
  if (severity === 'critical') return '严重'
  if (severity === 'warning') return '警告'
  return '提示'
}

function timeText(timestamp: string): string {
  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) return '--:--'
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}
</script>

<template>
  <section class="rail-card">
    <header class="rt-card-head">
      <span class="rt-card-title"><span class="rt-accent" />未处理告警</span>
      <span class="rail-count">{{ unresolved.length }} 待处理</span>
    </header>
    <div class="rail-body">
      <div v-if="unresolved.length === 0" class="rail-empty">暂无未处理告警</div>
      <div
        v-for="alarm in unresolved"
        :key="alarm.id"
        class="rail-item"
        data-test="alarm-rail-item"
      >
        <span class="rail-sev" :class="sevClass(alarm.severity)" />
        <div class="rail-content">
          <div class="rail-row">
            <span class="rail-title">{{ alarm.message }}</span>
            <span class="rail-time">{{ timeText(alarm.timestamp) }}</span>
          </div>
          <div class="rail-foot">
            <span class="rail-tag" :class="sevClass(alarm.severity)">{{ sevLabel(alarm.severity) }}</span>
            <button
              type="button"
              class="rail-resolve"
              data-test="alarm-resolve"
              :disabled="actionId === alarm.id"
              @click="emit('resolve', alarm)"
            >{{ actionId === alarm.id ? '处理中…' : '处理' }}</button>
          </div>
        </div>
      </div>
    </div>
    <footer
      v-if="rows.length > 0"
      class="rail-footer"
      data-test="alarm-view-all"
      @click="emit('view-all')"
    >查看全部 {{ rows.length }} 条记录 →</footer>
  </section>
</template>

<style scoped>
.rail-card {
  display: flex;
  flex-direction: column;
  background: #121d2e;
  border: 1px solid #1f2c41;
  border-radius: 10px;
  min-height: 0;
  flex: 1;
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
.rail-count {
  font-size: 10px;
  padding: 1px 7px;
  border-radius: 999px;
  background: rgba(245, 158, 11, 0.16);
  color: #f59e0b;
}
.rail-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
.rail-empty {
  padding: 18px 14px;
  text-align: center;
  font-size: 12px;
  color: #5e6c83;
}
.rail-item {
  display: flex;
  gap: 9px;
  padding: 9px 14px;
  border-bottom: 1px solid #1f2c41;
}
.rail-sev {
  width: 3px;
  border-radius: 2px;
  flex-shrink: 0;
}
.rail-sev.crit { background: #ef4444; }
.rail-sev.warn { background: #f59e0b; }
.rail-sev.info { background: #22d3ee; }
.rail-content {
  flex: 1;
  min-width: 0;
}
.rail-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}
.rail-title {
  font-size: 11px;
  color: #e5edf7;
  font-weight: 500;
}
.rail-time {
  font-size: 10px;
  color: #5e6c83;
  font-variant-numeric: tabular-nums;
}
.rail-foot {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}
.rail-tag {
  font-size: 9px;
  padding: 1px 5px;
  border-radius: 3px;
}
.rail-tag.crit { background: rgba(239, 68, 68, 0.15); color: #fda4af; }
.rail-tag.warn { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.rail-tag.info { background: rgba(34, 211, 238, 0.15); color: #67e8f9; }
.rail-resolve {
  margin-left: auto;
  padding: 2px 9px;
  border-radius: 5px;
  background: #182538;
  border: 1px solid #2a3a55;
  color: #9aa7bd;
  font: inherit;
  font-size: 10px;
  cursor: pointer;
}
.rail-resolve:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.rail-footer {
  border-top: 1px solid #1f2c41;
  padding: 8px 14px;
  text-align: center;
  font-size: 10px;
  color: #22d3ee;
  cursor: pointer;
  user-select: none;
  transition: color 0.15s ease;
}
.rail-footer:hover {
  color: #67e8f9;
}
</style>
