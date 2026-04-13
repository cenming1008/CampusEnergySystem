<script setup lang="ts">
import { Warning } from '@element-plus/icons-vue'
import type { PropType } from 'vue'
import type { DeviceAlarmRecord } from '@/api/deviceMonitor'

defineProps({
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

function severityTagType(severity?: string) {
  if (severity === 'critical') return 'danger'
  if (severity === 'warning') return 'warning'
  if (severity === 'info') return 'primary'
  return 'info'
}

function formatTime(value?: string | null) {
  if (!value) return '暂无数据'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}
</script>

<template>
  <section class="alarm-panel">
    <div class="alarm-panel__head">
      <div>
        <h3>告警记录</h3>
        <span>仅保留与补偿器当前运行相关的告警信息</span>
      </div>
    </div>

    <el-table
      :data="rows"
      class="dark-table"
      empty-text="当前暂无补偿器告警记录"
    >
      <el-table-column
        prop="timestamp"
        label="时间"
        min-width="170"
      >
        <template #default="{ row }">
          {{ formatTime(row.timestamp) }}
        </template>
      </el-table-column>
      <el-table-column
        prop="message"
        label="告警内容"
        min-width="280"
      />
      <el-table-column
        prop="severity"
        label="级别"
        width="110"
      >
        <template #default="{ row }">
          <el-tag :type="severityTagType(row.severity)">
            {{ row.severity || 'info' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="is_resolved"
        label="状态"
        width="110"
      >
        <template #default="{ row }">
          <el-tag :type="row.is_resolved ? 'success' : 'danger'">
            {{ row.is_resolved ? '已处理' : '未处理' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        label="操作"
        width="120"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            v-if="!row.is_resolved"
            type="warning"
            link
            :icon="Warning"
            :loading="actionId === row.id"
            @click="$emit('resolve', row)"
          >
            处理
          </el-button>
          <span
            v-else
            class="muted-text"
          >
            已关闭
          </span>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<style scoped>
.alarm-panel {
  padding: 18px;
  background: linear-gradient(180deg, rgba(18, 32, 50, 0.96), rgba(13, 22, 35, 0.98));
  border: 1px solid rgba(53, 72, 97, 0.88);
  border-radius: 16px;
}

.alarm-panel__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}

.alarm-panel__head h3 {
  margin: 0;
  font-size: 16px;
  color: #f5f7fb;
}

.alarm-panel__head span {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #8ea0bc;
}

.muted-text {
  color: #8ea0bc;
  font-size: 12px;
}

:deep(.dark-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(14, 24, 37, 0.92);
  --el-table-border-color: #243244;
  --el-table-row-hover-bg-color: rgba(22, 33, 48, 0.92);
  --el-table-text-color: #dbe6f5;
  --el-table-header-text-color: #8ea0bc;
}
</style>
