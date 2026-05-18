<script setup lang="ts">
import { computed } from 'vue'
import type { PropType } from 'vue'
import type { DeviceAlarmRecord } from '@/api/deviceMonitor'

const props = defineProps({
  rows: {
    type: Array as PropType<DeviceAlarmRecord[]>,
    default: () => [],
  },
  actionId: {
    type: Number as PropType<number | null>,
    default: null,
  },
})

defineEmits<{
  resolve: [row: DeviceAlarmRecord]
}>()

const SUMMARY_LIMIT = 50

const visibleRows = computed(() => props.rows.slice(0, SUMMARY_LIMIT))
const unresolvedCount = computed(() => props.rows.filter(row => !row.is_resolved).length)

function severityLabel(severity?: string) {
  if (severity === 'critical') return '严重'
  if (severity === 'warning') return '警告'
  if (severity === 'info') return '提示'
  return severity || '未知'
}

function severityClass(severity?: string) {
  if (severity === 'critical') return 'alarm-summary-item--critical'
  if (severity === 'warning') return 'alarm-summary-item--warning'
  return 'alarm-summary-item--info'
}

function formatTime(value?: string | null) {
  if (!value) return '--:--'
  return new Date(value).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}
</script>

<template>
  <section class="alarm-summary-panel">
    <div class="alarm-summary-panel__head">
      <div>
        <h3>告警记录</h3>
        <span>{{ rows.length }} 条记录</span>
      </div>
      <strong :class="{ 'is-clear': unresolvedCount === 0 }">
        {{ unresolvedCount }} 未处理
      </strong>
    </div>

    <div
      v-if="visibleRows.length"
      class="alarm-summary-list"
    >
      <article
        v-for="row in visibleRows"
        :key="row.id"
        class="alarm-summary-item"
        :class="severityClass(row.severity)"
      >
        <div class="alarm-summary-item__body">
          <div class="alarm-summary-item__title">
            <span>{{ row.message }}</span>
          </div>
          <p>
            {{ formatTime(row.timestamp) }}
            <i />
            {{ severityLabel(row.severity) }}
          </p>
        </div>
        <el-button
          v-if="!row.is_resolved"
          class="alarm-summary-item__action"
          :loading="actionId === row.id"
          @click="$emit('resolve', row)"
        >
          处理
        </el-button>
        <span
          v-else
          class="alarm-summary-item__state"
        >
          已处理
        </span>
      </article>
    </div>

    <div
      v-else
      class="alarm-summary-empty"
    >
      当前暂无告警记录
    </div>
  </section>
</template>

<style scoped>
.alarm-summary-panel {
  padding: 16px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.96), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
}

.alarm-summary-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.alarm-summary-panel__head h3 {
  margin: 0;
  font-size: 15px;
  color: #f5f7fb;
}

.alarm-summary-panel__head span {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #8ea0bc;
}

.alarm-summary-panel__head strong {
  flex: 0 0 auto;
  padding: 4px 8px;
  border-radius: 8px;
  color: #fbbf24;
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.36);
  font-size: 12px;
  line-height: 1;
}

.alarm-summary-panel__head strong.is-clear {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.34);
}

.alarm-summary-list {
  display: grid;
  gap: 8px;
  max-height: clamp(280px, 42vh, 560px);
  overflow-y: auto;
  padding-right: 6px;
  scrollbar-width: auto;
  scrollbar-color: rgba(74, 96, 128, 0.6) transparent;
}

.alarm-summary-list::-webkit-scrollbar {
  width: 8px;
}

.alarm-summary-list::-webkit-scrollbar-thumb {
  background: rgba(74, 96, 128, 0.6);
  border-radius: 4px;
}

.alarm-summary-list::-webkit-scrollbar-track {
  background: transparent;
}

.alarm-summary-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 10px;
  background: rgba(9, 18, 30, 0.62);
  border: 1px solid rgba(48, 67, 91, 0.7);
}

.alarm-summary-item--critical {
  border-left: 3px solid #ef4444;
}

.alarm-summary-item--warning {
  border-left: 3px solid #f59e0b;
}

.alarm-summary-item--info {
  border-left: 3px solid #3b82f6;
}

.alarm-summary-item__body {
  min-width: 0;
}

.alarm-summary-item__title {
  color: #f3f6fb;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.45;
}

.alarm-summary-item__title span {
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.alarm-summary-item p {
  display: flex;
  align-items: center;
  gap: 7px;
  margin: 5px 0 0;
  color: #8ea0bc;
  font-size: 12px;
}

.alarm-summary-item p i {
  width: 3px;
  height: 3px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.7;
}

.alarm-summary-item__action {
  height: 28px;
  min-width: 54px;
  padding: 0 10px;
  border-radius: 7px;
  color: #fbbf24;
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.38);
  font-weight: 700;
}

.alarm-summary-item__state {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  min-width: 54px;
  padding: 0 10px;
  border-radius: 7px;
  color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.34);
  font-size: 12px;
  font-weight: 700;
}

.alarm-summary-empty {
  padding: 14px 0 2px;
  color: #8ea0bc;
  font-size: 12px;
}
</style>
