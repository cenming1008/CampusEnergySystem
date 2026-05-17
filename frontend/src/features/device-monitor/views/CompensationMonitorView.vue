<script setup lang="ts">
import CompensationAlarmTable from '@/features/device-monitor/components/compensation/CompensationAlarmTable.vue'
import CompensationControlSummaryPanel from '@/features/device-monitor/components/compensation/CompensationControlSummaryPanel.vue'
import CompensationDetailPanel from '@/features/device-monitor/components/compensation/CompensationDetailPanel.vue'
import CompensationDeviceProfile from '@/features/device-monitor/components/compensation/CompensationDeviceProfile.vue'
import CompensationEventTimeline from '@/features/device-monitor/components/compensation/CompensationEventTimeline.vue'
import CompensationHeader from '@/features/device-monitor/components/compensation/CompensationHeader.vue'
import CompensationRealtimeOverview from '@/features/device-monitor/components/compensation/CompensationRealtimeOverview.vue'
import CompensationStatusSummary from '@/features/device-monitor/components/compensation/CompensationStatusSummary.vue'
import CompensationSvgProfileEditDialog from '@/features/device-monitor/components/compensation/CompensationSvgProfileEditDialog.vue'
import CompensationTrendPanel from '@/features/device-monitor/components/compensation/CompensationTrendPanel.vue'
import CompensationDiagnosticsCollapsible from '@/features/device-monitor/components/compensation/CompensationDiagnosticsCollapsible.vue'
import HarmonicSpectrumPanel from '@/features/device-monitor/components/compensation/HarmonicSpectrumPanel.vue'
import MonitorViewShell from './MonitorViewShell.vue'
import type { DeviceMonitorPageModel } from '@/features/device-monitor/composables/useDeviceMonitorPage'

defineProps<{
  page: DeviceMonitorPageModel
}>()
</script>

<template>
  <MonitorViewShell>
    <template #header>
      <CompensationHeader
        :model="page.compensationHeaderModel"
        :toggle-action-label="page.toggleActionLabel"
        :toggle-button-type="page.toggleButtonType"
        :toggle-submitting="page.toggleSubmitting"
        :can-control-devices="page.canControlDevices && !page.isPendingArchiveDevice"
        :show-console-entry="page.compensationSubtype === 'capacitor_bank_controller' && !page.isPendingArchiveDevice"
        @back="page.router.push('/devices')"
        @open-console="page.router.push(`/device-console/${page.deviceId}`)"
        @refresh="page.loadPage(true)"
        @toggle="page.handleToggleDevice"
      />
    </template>

    <template #main>
      <CompensationRealtimeOverview
        :core-metric="page.compensationCoreMetric"
        :pf-metric="page.compensationPfMetric"
        :metrics="page.compensationMetrics"
        :module-status="page.moduleStatusModel"
        :extended-hint="page.compensationExtendedHint"
      />

      <CompensationDetailPanel
        v-if="page.isSvgDevice || page.compensationSubtype === 'capacitor_bank_controller'"
        v-model:active-tab="page.compensationDetailTab"
        :svg-telemetry="page.compensationSvgTelemetry"
        :capacitor-bank-telemetry="page.compensationCapacitorBankTelemetry"
        :is-capacitor-bank="page.compensationSubtype === 'capacitor_bank_controller'"
        :circuit-profile="page.compensationCircuitProfile"
      />

      <CompensationTrendPanel
        v-model:active-tab="page.compensationTrendTab"
        v-model:time-range="page.timeRange"
        :tabs="page.compensationTrendTabs"
        :model="page.compensationTrendModel"
        :shortcuts="page.timeShortcuts"
        :loading="page.chartLoading"
        @range-change="page.handleRangeChange"
      />

      <HarmonicSpectrumPanel
        v-if="page.compensationSubtype === 'capacitor_bank_controller'"
        :telemetry="page.compensationCapacitorBankTelemetry"
        :control-profile="page.compensationCapacitorBankControlProfile"
      />

      <CompensationAlarmTable
        :rows="page.alarms"
        :action-id="page.alarmActionId"
        @resolve="page.handleResolveAlarm"
      />
    </template>

    <template #side>
      <CompensationEventTimeline :events="page.compensationEvents" />
      <CompensationStatusSummary :items="page.compensationStatusItems" />
      <CompensationControlSummaryPanel
        v-if="page.compensationSubtype === 'capacitor_bank_controller'"
        :summary-items="page.capacitorBankControlSummaryView.summaryItems"
        :capacity-expansion-items="page.capacitorBankControlSummaryView.capacityExpansionItems"
        :has-summary-data="page.capacitorBankControlSummaryView.hasSummaryData"
        @open-console="page.router.push(`/device-console/${page.deviceId}`)"
      />
      <CompensationDeviceProfile
        :items="page.compensationProfileItems"
        :editable="page.isSvgDevice && page.canControlDevices"
        @edit="page.svgProfileEditVisible = true"
      />
      <CompensationDiagnosticsCollapsible
        v-if="page.templateDiagnostics"
        :diagnostics="page.templateDiagnostics"
      />
    </template>
  </MonitorViewShell>

  <CompensationSvgProfileEditDialog
    v-if="page.isSvgDevice"
    v-model="page.svgProfileEditVisible"
    :device-id="page.deviceId"
    :profile="page.compensationSvgProfile"
    @saved="page.loadSVGProfile"
  />
</template>
