<script setup lang="ts">
import { useDeviceMonitorPage } from '@/features/device-monitor/composables/useDeviceMonitorPage'
import CompensationMonitorView from '@/features/device-monitor/views/CompensationMonitorView.vue'
import GenericMonitorView from '@/features/device-monitor/views/GenericMonitorView.vue'
import MonitorScaleShell from '@/features/device-monitor/views/MonitorScaleShell.vue'
import StorageMonitorView from '@/features/device-monitor/views/StorageMonitorView.vue'

const page = useDeviceMonitorPage()
</script>

<template>
  <div
    v-loading="page.loading"
    class="monitor-page"
  >
    <el-alert
      v-if="page.isPendingArchiveDevice"
      class="pending-archive-alert"
      type="warning"
      show-icon
      :closable="false"
      title="请先补全设备档案"
      description="该设备由 MQTT 首包自动登记，目前只有 sn/device_code。补全名称、类型、位置和容量后，系统才会写入业务遥测并开放监控/控制。"
    />

    <MonitorScaleShell>
      <CompensationMonitorView
        v-if="page.isCompensationDevice"
        :page="page"
      />
      <StorageMonitorView
        v-else-if="page.isStorageDevice"
        :page="page"
      />
      <GenericMonitorView
        v-else
        :page="page"
      />
    </MonitorScaleShell>
  </div>
</template>

<style scoped>
.monitor-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

/* ─── Large screens ──────────────────────────────────────────── */

@media (min-width: 1920px) {
  .monitor-page {
    gap: 20px;
  }
}

@media (min-width: 2400px) {
  .monitor-page {
    gap: 24px;
  }
}
</style>
