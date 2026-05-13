<script setup lang="ts">
import CompensationAlarmTable from '@/features/device-monitor/components/compensation/CompensationAlarmTable.vue'
import CompensationDeviceProfile from '@/features/device-monitor/components/compensation/CompensationDeviceProfile.vue'
import CompensationEventTimeline from '@/features/device-monitor/components/compensation/CompensationEventTimeline.vue'
import DeviceTemplateDiagnosticsPanel from '@/features/device-monitor/components/common/DeviceTemplateDiagnosticsPanel.vue'
import StorageHeader from '@/features/device-monitor/components/storage/StorageHeader.vue'
import StorageRealtimeOverview from '@/features/device-monitor/components/storage/StorageRealtimeOverview.vue'
import StorageStatusPanel from '@/features/device-monitor/components/storage/StorageStatusPanel.vue'
import StorageTrendPanel from '@/features/device-monitor/components/storage/StorageTrendPanel.vue'
import MonitorViewShell from './MonitorViewShell.vue'
import type { DeviceMonitorPageModel } from '@/features/device-monitor/composables/useDeviceMonitorPage'

defineProps<{
  page: DeviceMonitorPageModel
}>()
</script>

<template>
  <MonitorViewShell>
    <template #header>
      <StorageHeader
        :title="page.archive?.name || '储能设备'"
        :serial="page.archive?.sn || '--'"
        :location="page.archive?.location || '未设置位置'"
        :runtime-label="page.storageRuntimeStatus?.label || '状态未知'"
        :runtime-code="page.storageRuntimeStatus?.code || 'unknown'"
        :run-state="page.runStateRaw"
        :is-online="page.storageRuntimeStatus?.is_online ?? false"
        @back="page.router.push('/devices')"
        @refresh="page.loadPage(true)"
      />
    </template>

    <template #main>
      <StorageRealtimeOverview
        :soc-value="page.socValue"
        :soc-state="page.socState"
        :power-value="page.powerValue"
        :power-state="page.powerState"
        :power-direction="page.powerDirection"
        :metrics="page.storageOverviewMetrics"
      />

      <StorageTrendPanel
        v-model:active-tab="page.storageTrendTab"
        v-model:time-range="page.timeRange"
        :history="page.storageTelemetryHistory"
        :loading="page.chartLoading"
        @range-change="page.handleRangeChange"
      />

      <CompensationAlarmTable
        :rows="page.alarms"
        :action-id="page.alarmActionId"
        @resolve="page.handleResolveAlarm"
      />
    </template>

    <template #side>
      <DeviceTemplateDiagnosticsPanel
        v-if="page.templateDiagnostics"
        :diagnostics="page.templateDiagnostics"
      />
      <StorageStatusPanel
        :run-state="page.runStateRaw"
        :run-state-label="page.runStateLabel"
        :control-mode="page.storageControlModeLabel"
        :soh="page.storageTelemetry?.soh != null ? `${Number(page.storageTelemetry.soh).toFixed(1)} %` : '--'"
        :cycle-count="page.storageTelemetry?.cycle_count != null ? `${page.storageTelemetry.cycle_count} 次` : '--'"
        :cell-temp-max="page.storageTelemetry?.cell_temp_max != null ? `${Number(page.storageTelemetry.cell_temp_max).toFixed(1)} °C` : '--'"
        :cell-temp-min="page.storageTelemetry?.cell_temp_min != null ? `${Number(page.storageTelemetry.cell_temp_min).toFixed(1)} °C` : '--'"
        :cell-temp-avg="page.storageTelemetry?.cell_temp_avg != null ? `${Number(page.storageTelemetry.cell_temp_avg).toFixed(1)} °C` : '--'"
        :fault-code="page.storageTelemetry?.fault_code != null ? String(page.storageTelemetry.fault_code) : '--'"
        :alarm-code="page.storageTelemetry?.alarm_code != null ? String(page.storageTelemetry.alarm_code) : '--'"
        :ingestion-status="page.storageIngestionStatusLabel"
        :ingestion-tone="page.storageIngestionTone"
        :unresolved-alarm-count="page.storageRuntimeStatus?.unresolved_alarm_count ?? 0"
        :latest-sample-text="page.storageLatestSampleText"
      />
      <CompensationEventTimeline :events="page.compensationEvents" />
      <CompensationDeviceProfile :items="page.compensationProfileItems" />
    </template>
  </MonitorViewShell>
</template>
