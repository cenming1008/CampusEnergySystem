<script setup lang="ts">
import CompensationAlarmTable from '@/features/device-monitor/components/compensation/CompensationAlarmTable.vue'
import CompensationCircuitStatePanel from '@/features/device-monitor/components/compensation/CompensationCircuitStatePanel.vue'
import CompensationControlSummaryPanel from '@/features/device-monitor/components/compensation/CompensationControlSummaryPanel.vue'
import CompensationDeviceProfile from '@/features/device-monitor/components/compensation/CompensationDeviceProfile.vue'
import CompensationEventTimeline from '@/features/device-monitor/components/compensation/CompensationEventTimeline.vue'
import CompensationHeader from '@/features/device-monitor/components/compensation/CompensationHeader.vue'
import CompensationRealtimeOverview from '@/features/device-monitor/components/compensation/CompensationRealtimeOverview.vue'
import CompensationStatusSummary from '@/features/device-monitor/components/compensation/CompensationStatusSummary.vue'
import CompensationSvgProfileEditDialog from '@/features/device-monitor/components/compensation/CompensationSvgProfileEditDialog.vue'
import CompensationThreePhasePanel from '@/features/device-monitor/components/compensation/CompensationThreePhasePanel.vue'
import CompensationTrendPanel from '@/features/device-monitor/components/compensation/CompensationTrendPanel.vue'
import DeviceTemplateDiagnosticsPanel from '@/features/device-monitor/components/common/DeviceTemplateDiagnosticsPanel.vue'
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

      <CompensationThreePhasePanel
        v-if="page.isSvgDevice || page.compensationSubtype === 'capacitor_bank_controller'"
        :svg-telemetry="page.compensationSvgTelemetry"
        :capacitor-bank-telemetry="page.compensationCapacitorBankTelemetry"
        :is-capacitor-bank="page.compensationSubtype === 'capacitor_bank_controller'"
      />

      <CompensationCircuitStatePanel
        v-if="page.compensationSubtype === 'capacitor_bank_controller'"
        :capacitor-bank-telemetry="page.compensationCapacitorBankTelemetry"
        :configured-split-circuit-count="page.compensationCapacitorBankControlProfile?.split_output_circuit_count ?? undefined"
        :configured-common-circuit-count="page.compensationCapacitorBankControlProfile?.common_output_circuit_count ?? undefined"
        :phase-a-circuit-total-count="page.compensationCapacitorBankControlProfile?.phase_a_circuit_total_count ?? undefined"
        :phase-b-circuit-total-count="page.compensationCapacitorBankControlProfile?.phase_b_circuit_total_count ?? undefined"
        :phase-c-circuit-total-count="page.compensationCapacitorBankControlProfile?.phase_c_circuit_total_count ?? undefined"
        :common1-circuit-total-count="page.compensationCapacitorBankControlProfile?.common_1_circuit_total_count ?? undefined"
        :common2-circuit-total-count="page.compensationCapacitorBankControlProfile?.common_2_circuit_total_count ?? undefined"
        :common3-circuit-total-count="page.compensationCapacitorBankControlProfile?.common_3_circuit_total_count ?? undefined"
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
      <CompensationStatusSummary :items="page.compensationStatusItems" />
      <CompensationEventTimeline :events="page.compensationEvents" />
      <CompensationControlSummaryPanel
        v-if="page.compensationSubtype === 'capacitor_bank_controller'"
        :summary-items="page.capacitorBankControlSummaryView.summaryItems"
        :capacity-expansion-items="page.capacitorBankControlSummaryView.capacityExpansionItems"
        :has-summary-data="page.capacitorBankControlSummaryView.hasSummaryData"
      />
      <CompensationDeviceProfile
        :items="page.compensationProfileItems"
        :editable="page.isSvgDevice && page.canControlDevices"
        @edit="page.svgProfileEditVisible = true"
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
