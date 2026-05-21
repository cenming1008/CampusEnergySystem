<script setup lang="ts">
import { computed } from 'vue'
import ControlConsoleLogPanel from '@/features/device-control/components/ControlConsoleLogPanel.vue'
import ControlConsoleParametersPanel from '@/features/device-control/components/ControlConsoleParametersPanel.vue'
import ControlConsoleWriteDialog from '@/features/device-control/components/ControlConsoleWriteDialog.vue'
import CompensationRuntimeBoard from '@/features/device-monitor/components/compensation/runtime/CompensationRuntimeBoard.vue'
import CompensationAlarmRail from '@/features/device-monitor/components/compensation/runtime/CompensationAlarmRail.vue'
import CompensationParamSummary from '@/features/device-monitor/components/compensation/runtime/CompensationParamSummary.vue'
import CompensationAlarmSummaryPanel from '@/features/device-monitor/components/compensation/CompensationAlarmSummaryPanel.vue'
import CompensationAlarmTable from '@/features/device-monitor/components/compensation/CompensationAlarmTable.vue'
import CompensationControlSummaryPanel from '@/features/device-monitor/components/compensation/CompensationControlSummaryPanel.vue'
import CompensationDetailPanel from '@/features/device-monitor/components/compensation/CompensationDetailPanel.vue'
import CompensationDeviceProfile from '@/features/device-monitor/components/compensation/CompensationDeviceProfile.vue'
import CompensationEventTimeline from '@/features/device-monitor/components/compensation/CompensationEventTimeline.vue'
import CompensationHeader from '@/features/device-monitor/components/compensation/CompensationHeader.vue'
import CompensationRealtimeOverview from '@/features/device-monitor/components/compensation/CompensationRealtimeOverview.vue'
import CompensationSvgProfileEditDialog from '@/features/device-monitor/components/compensation/CompensationSvgProfileEditDialog.vue'
import CompensationTrendPanel from '@/features/device-monitor/components/compensation/CompensationTrendPanel.vue'
import CompensationDiagnosticsCollapsible from '@/features/device-monitor/components/compensation/CompensationDiagnosticsCollapsible.vue'
import CompensationCurveAnalysisAside from '@/features/device-monitor/components/compensation/curves/CompensationCurveAnalysisAside.vue'
import CompensationCurveWorkspace from '@/features/device-monitor/components/compensation/curves/CompensationCurveWorkspace.vue'
import HarmonicSpectrumPanel from '@/features/device-monitor/components/compensation/HarmonicSpectrumPanel.vue'
import MonitorInlineAlert from '@/shared/components/MonitorInlineAlert.vue'
import MonitorSectionPanel from '@/shared/components/MonitorSectionPanel.vue'
import MonitorViewShell from './MonitorViewShell.vue'
import type { DeviceMonitorPageModel } from '@/features/device-monitor/composables/useDeviceMonitorPage'

const props = defineProps<{
  page: DeviceMonitorPageModel
}>()

function isCapacitorBankController() {
  return props.page.compensationSubtype === 'capacitor_bank_controller'
}

function switchWorkbenchTab(tab: DeviceMonitorPageModel['compensationWorkbenchTab']) {
  props.page.compensationWorkbenchTab = tab
}

function openParameterWorkbench() {
  switchWorkbenchTab('parameter-settings')
}

function shouldShowSideTraceability() {
  return !(isCapacitorBankController() && props.page.compensationWorkbenchTab === 'event-records')
}

const runtimeParamItems = computed(() =>
  props.page.capacitorBankControlSummaryView.summaryItems.map((item) => ({
    label: item.label,
    value: item.value,
  })),
)

function isRuntimeTab() {
  return (
    props.page.compensationSubtype === 'capacitor_bank_controller'
    && props.page.compensationWorkbenchTab === 'runtime'
  )
}
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
        :tabs="page.compensationSubtype === 'capacitor_bank_controller' ? page.compensationWorkbenchTabs : []"
        :active-tab="page.compensationWorkbenchTab"
        @back="page.router.push('/devices')"
        @refresh="page.loadPage(true)"
        @tab-change="switchWorkbenchTab"
        @toggle="page.handleToggleDevice"
      />
    </template>

    <template #main>
      <div
        v-if="page.compensationSubtype === 'capacitor_bank_controller'"
        class="comp-workbench"
      >
        <div class="comp-workbench__page">
          <template v-if="page.compensationWorkbenchTab === 'runtime'">
            <CompensationRuntimeBoard :page="page" />
          </template>

          <template v-else-if="page.compensationWorkbenchTab === 'curves'">
            <CompensationCurveWorkspace
              :telemetry="page.compensationCapacitorBankTelemetry"
              :history="page.compensationCapacitorBankTelemetryHistory"
              :control-profile="page.compensationCapacitorBankControlProfile"
            />
          </template>

          <template v-else-if="page.compensationWorkbenchTab === 'parameter-settings'">
            <MonitorInlineAlert
              v-if="page.controlConsoleProfileWarning"
              title="参数档案暂时不可用"
              :message="page.controlConsoleProfileWarning"
              tone="warning"
            />

            <MonitorSectionPanel
              shell="console"
              accent="teal"
              title="参数设置"
            >
              <ControlConsoleParametersPanel
                :section-view="page.controlConsoleReadonlySectionView"
                :readonly-summary-view="page.controlConsoleReadonlySummaryView"
                :write-section-view="page.controlConsoleWriteSectionView"
                :can-write-parameters="page.controlConsoleCanWriteParameters"
                :editable-parameter-cards="page.controlConsoleEditableParameterCards"
                @open-write-dialog="page.openControlConsoleWriteDialog"
              />
            </MonitorSectionPanel>
          </template>

          <template v-else-if="page.compensationWorkbenchTab === 'event-records'">
            <CompensationAlarmTable
              :rows="page.alarms"
              :action-id="page.alarmActionId"
              @resolve="page.handleResolveAlarm"
            />

            <ControlConsoleLogPanel :log-view="page.controlConsoleLogView" />

            <CompensationEventTimeline :events="page.compensationEvents" />

            <CompensationDiagnosticsCollapsible
              v-if="page.templateDiagnostics"
              :diagnostics="page.templateDiagnostics"
            />
          </template>
        </div>
      </div>

      <template v-else>
        <CompensationRealtimeOverview
          :core-metric="page.compensationCoreMetric"
          :pf-metric="page.compensationPfMetric"
          :metrics="page.compensationMetrics"
          :extended-hint="page.compensationExtendedHint"
          :capacitor-bank-telemetry="page.compensationCapacitorBankTelemetry"
          :pf-trend="page.compensationPowerFactorTrend"
          :status-text="page.compensationStatusText"
          :status-tone="page.compensationStatusTone"
          :alarm-counts="page.compensationAlarmCountMetrics"
        />

        <CompensationDetailPanel
          v-if="page.isSvgDevice"
          v-model:active-tab="page.compensationDetailTab"
          :svg-telemetry="page.compensationSvgTelemetry"
          :capacitor-bank-telemetry="page.compensationCapacitorBankTelemetry"
          :is-capacitor-bank="false"
          :circuit-profile="page.compensationCircuitProfile"
          :module-status="page.moduleStatusModel"
          :measurement-metrics="page.compensationMeasurementMetrics"
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
    </template>

    <template #side>
      <template v-if="isRuntimeTab()">
        <CompensationAlarmRail
          :rows="page.alarms"
          :action-id="page.alarmActionId"
          @resolve="page.handleResolveAlarm"
          @view-all="switchWorkbenchTab('event-records')"
        />
        <CompensationParamSummary
          :items="runtimeParamItems"
          @edit="openParameterWorkbench"
        />
        <CompensationDeviceProfile
          :items="page.compensationProfileItems"
          :editable="page.isSvgDevice && page.canControlDevices"
          @edit="page.svgProfileEditVisible = true"
        />
      </template>
      <template v-else-if="page.compensationSubtype === 'capacitor_bank_controller' && page.compensationWorkbenchTab === 'curves'">
        <CompensationCurveAnalysisAside
          :telemetry="page.compensationCapacitorBankTelemetry"
          :history="page.compensationCapacitorBankTelemetryHistory"
          :control-profile="page.compensationCapacitorBankControlProfile"
          :alarms="page.alarms"
          :events="page.compensationEvents"
          :time-range="page.timeRange"
        />
      </template>
      <template v-else>
        <CompensationEventTimeline
          v-if="shouldShowSideTraceability()"
          :events="page.compensationEvents"
        />
        <CompensationAlarmSummaryPanel
          :rows="page.alarms"
          :action-id="page.alarmActionId"
          @resolve="page.handleResolveAlarm"
        />
        <CompensationControlSummaryPanel
          v-if="page.compensationSubtype === 'capacitor_bank_controller'"
          :summary-items="page.capacitorBankControlSummaryView.summaryItems"
          :capacity-expansion-items="page.capacitorBankControlSummaryView.capacityExpansionItems"
          :has-summary-data="page.capacitorBankControlSummaryView.hasSummaryData"
          @open-console="openParameterWorkbench"
        />
        <CompensationDeviceProfile
          :items="page.compensationProfileItems"
          :editable="page.isSvgDevice && page.canControlDevices"
          @edit="page.svgProfileEditVisible = true"
        />
        <CompensationDiagnosticsCollapsible
          v-if="page.templateDiagnostics && shouldShowSideTraceability()"
          :diagnostics="page.templateDiagnostics"
        />
      </template>
    </template>
  </MonitorViewShell>

  <CompensationSvgProfileEditDialog
    v-if="page.isSvgDevice"
    v-model="page.svgProfileEditVisible"
    :device-id="page.deviceId"
    :profile="page.compensationSvgProfile"
    @saved="page.loadSVGProfile"
  />

  <ControlConsoleWriteDialog
    v-if="page.compensationSubtype === 'capacitor_bank_controller'"
    v-model="page.controlConsoleWriteDialogVisible"
    :selected-write-meta="page.controlConsoleSelectedWriteMeta"
    :control-profile="page.controlConsoleControlProfile"
    :target-value="page.controlConsoleWriteForm.target_value"
    :reason="page.controlConsoleWriteForm.reason"
    :write-submitting="page.controlConsoleWriteSubmitting"
    @update:target-value="page.controlConsoleWriteForm.target_value = $event"
    @update:reason="page.controlConsoleWriteForm.reason = $event"
    @submit="page.submitControlConsoleParameterWrite"
  />
</template>

<style scoped>
.comp-workbench {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
}

.comp-workbench__page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.comp-workbench__analysis-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.comp-workbench__analysis-title {
  color: #d7e3f4;
  font-size: 13px;
  font-weight: 700;
}

.comp-workbench__subtabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-width: 0;
}

.comp-workbench__subtab {
  min-height: 32px;
  padding: 0 12px;
  border: 1px solid rgba(58, 76, 102, 0.72);
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.72);
  color: #9fb0c8;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.comp-workbench__subtab.is-active {
  border-color: rgba(96, 165, 250, 0.42);
  background: rgba(37, 99, 235, 0.2);
  color: #eff6ff;
}

</style>
