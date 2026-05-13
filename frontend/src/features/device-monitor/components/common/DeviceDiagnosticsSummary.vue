<script setup lang="ts">
import { computed } from 'vue'
import type { MonitorDiagnosticsSummary, RuntimeStatus } from '@/api/deviceMonitor'

const props = defineProps<{
  runtimeStatus?: RuntimeStatus
  diagnosticsSummary?: MonitorDiagnosticsSummary
}>()

function formatIngestionStatus(status?: string | null) {
  if (status === 'online') return '在线采集'
  if (status === 'degraded') return '采集波动'
  if (status === 'offline') return '离线'
  return '未知'
}

function formatDateTime(value?: string | null) {
  if (!value) return '暂无数据'
  const date = new Date(value)
  const pad = (n: number) => `${n}`.padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

const managementStatus = computed(() => {
  if (!props.runtimeStatus) return '未知'
  return props.runtimeStatus.is_active ? '启用' : '停用'
})

const communicationStatus = computed(() => {
  const isOnline = props.diagnosticsSummary?.is_online ?? props.runtimeStatus?.is_online
  if (isOnline === undefined) return '未知'
  return isOnline ? '在线采集' : '离线'
})

const items = computed(() => [
  { label: '管理状态', value: managementStatus.value },
  { label: '通讯状态', value: communicationStatus.value },
  {
    label: '采集状态',
    value: formatIngestionStatus(props.diagnosticsSummary?.ingestion_status || props.runtimeStatus?.ingestion_status),
  },
  { label: '未处理告警', value: `${props.runtimeStatus?.unresolved_alarm_count ?? 0} 条` },
  { label: '最近消息', value: formatDateTime(props.diagnosticsSummary?.last_message_at || props.runtimeStatus?.last_message_at) },
  { label: '最近成功入库', value: formatDateTime(props.diagnosticsSummary?.last_success_at || props.runtimeStatus?.last_success_at) },
])
</script>

<template>
  <section class="device-diagnostics-summary">
    <div
      v-for="item in items"
      :key="item.label"
      class="device-diagnostics-summary__item"
    >
      <span>{{ item.label }}</span>
      <strong>{{ item.value }}</strong>
    </div>
  </section>
</template>

<style scoped>
.device-diagnostics-summary {
  padding: 16px;
  display: grid;
  gap: 12px;
  background: #131d2b;
  border: 1px solid #243244;
  border-radius: 14px;
}

.device-diagnostics-summary__item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}

.device-diagnostics-summary__item span {
  color: #8ea0bc;
}

.device-diagnostics-summary__item strong {
  color: #f8fafc;
  text-align: right;
  font-weight: 600;
}
</style>
