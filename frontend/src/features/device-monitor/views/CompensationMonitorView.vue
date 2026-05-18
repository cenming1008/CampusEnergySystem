<script setup lang="ts">
import ControlConsoleLogPanel from '@/features/device-control/components/ControlConsoleLogPanel.vue'
import ControlConsoleParametersPanel from '@/features/device-control/components/ControlConsoleParametersPanel.vue'
import ControlConsoleRemotePanel from '@/features/device-control/components/ControlConsoleRemotePanel.vue'
import ControlConsoleWriteDialog from '@/features/device-control/components/ControlConsoleWriteDialog.vue'
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

function openControlWorkbench() {
  if (isCapacitorBankController()) {
    switchWorkbenchTab('runtime')
    return
  }

  props.page.router.push(`/device-console/${props.page.deviceId}`)
}

function openParameterWorkbench() {
  switchWorkbenchTab('parameter-settings')
}

function shouldShowSideTraceability() {
  return !(isCapacitorBankController() && props.page.compensationWorkbenchTab === 'event-records')
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
        :show-console-entry="page.compensationSubtype === 'capacitor_bank_controller' && !page.isPendingArchiveDevice"
        console-entry-label="远程控制"
        @back="page.router.push('/devices')"
        @open-console="openControlWorkbench"
        @refresh="page.loadPage(true)"
        @toggle="page.handleToggleDevice"
      />
    </template>

    <template #main>
      <div
        v-if="page.compensationSubtype === 'capacitor_bank_controller'"
        class="comp-workbench"
      >
        <div
          class="comp-workbench__tabs"
          role="tablist"
          aria-label="补偿控制器工作台"
        >
          <button
            v-for="tab in page.compensationWorkbenchTabs"
            :key="tab.value"
            type="button"
            class="comp-workbench__tab"
            :class="[
              `comp-workbench__tab--${tab.tone || 'default'}`,
              { 'is-active': page.compensationWorkbenchTab === tab.value },
            ]"
            role="tab"
            :aria-selected="page.compensationWorkbenchTab === tab.value"
            @click="switchWorkbenchTab(tab.value)"
          >
            {{ tab.label }}
          </button>
        </div>

        <div class="comp-workbench__page">
          <template v-if="page.compensationWorkbenchTab === 'runtime'">
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
              v-model:active-tab="page.compensationDetailTab"
              :svg-telemetry="page.compensationSvgTelemetry"
              :capacitor-bank-telemetry="page.compensationCapacitorBankTelemetry"
              is-capacitor-bank
              :circuit-profile="page.compensationCircuitProfile"
              :module-status="page.moduleStatusModel"
              :measurement-metrics="page.compensationMeasurementMetrics"
            />

            <MonitorInlineAlert
              v-if="page.controlConsoleLoadError"
              title="远程控制暂不可用"
              :message="page.controlConsoleLoadError"
              tone="danger"
            />

            <ControlConsoleRemotePanel
              v-else
              :action-cards="page.controlConsoleActionCards"
              :toggle-submitting="page.controlConsoleToggleSubmitting"
              :current-control-mode-label="page.controlConsoleCurrentControlModeLabel"
              :can-run-manual-switch="page.controlConsoleCanRunManualSwitch"
              :manual-switch-disabled-reason="page.controlConsoleManualSwitchDisabledReason"
              :manual-phase-options="page.controlConsoleManualPhaseOptions"
              :manual-switch-action-options="page.controlConsoleManualSwitchActionOptions"
              :manual-common-group-options="page.controlConsoleManualCommonGroupOptions"
              :manual-phase="page.controlConsoleManualSwitchForm.phase"
              :manual-switch-action="page.controlConsoleManualSwitchForm.switch_action"
              :manual-common-group="page.controlConsoleManualSwitchForm.group"
              @action-card="page.handleControlConsoleActionCard"
              @update:manual-phase="page.controlConsoleManualSwitchForm.phase = $event"
              @update:manual-switch-action="page.controlConsoleManualSwitchForm.switch_action = $event"
              @update:manual-common-group="page.controlConsoleManualSwitchForm.group = $event"
              @manual-switch="page.handleControlConsoleManualSwitchCommand"
            />
          </template>

          <template v-else-if="page.compensationWorkbenchTab === 'curves'">
            <section class="comp-workbench__analysis-block">
              <div class="comp-workbench__analysis-title">实时分析</div>
              <HarmonicSpectrumPanel
                :telemetry="page.compensationCapacitorBankTelemetry"
                :control-profile="page.compensationCapacitorBankControlProfile"
              />
            </section>

            <section class="comp-workbench__analysis-block">
              <div class="comp-workbench__analysis-title">历史数据</div>
              <div
                class="comp-workbench__subtabs"
                role="tablist"
                aria-label="历史数据"
              >
                <button
                  v-for="tab in page.compensationTrendTabs"
                  :key="tab.value"
                  type="button"
                  class="comp-workbench__subtab"
                  :class="{ 'is-active': page.compensationTrendTab === tab.value }"
                  role="tab"
                  :aria-selected="page.compensationTrendTab === tab.value"
                  @click="page.compensationTrendTab = tab.value"
                >
                  {{ tab.label }}
                </button>
              </div>

              <CompensationTrendPanel
                v-model:active-tab="page.compensationTrendTab"
                v-model:time-range="page.timeRange"
                :tabs="[]"
                :model="page.compensationTrendModel"
                :shortcuts="page.timeShortcuts"
                :loading="page.chartLoading"
                @range-change="page.handleRangeChange"
              />
            </section>
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

.comp-workbench__tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px;
  border: 1px solid rgba(58, 76, 102, 0.72);
  border-radius: 8px;
  background: rgba(13, 24, 38, 0.88);
}

.comp-workbench__tab {
  min-height: 34px;
  padding: 0 14px;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: #8ca0ba;
  font: inherit;
  font-size: 13px;
  cursor: pointer;
  transition:
    border-color 0.16s ease,
    background 0.16s ease,
    color 0.16s ease;
}

.comp-workbench__tab:hover {
  border-color: rgba(96, 165, 250, 0.32);
  color: #dbeafe;
}

.comp-workbench__tab.is-active {
  border-color: rgba(96, 165, 250, 0.42);
  background: rgba(37, 99, 235, 0.18);
  color: #eff6ff;
}

.comp-workbench__tab--warning.is-active {
  border-color: rgba(245, 158, 11, 0.48);
  background: rgba(245, 158, 11, 0.16);
  color: #fef3c7;
}

.comp-workbench__tab--danger.is-active {
  border-color: rgba(248, 113, 113, 0.48);
  background: rgba(220, 38, 38, 0.16);
  color: #fee2e2;
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

@media (max-width: 720px) {
  .comp-workbench__tabs {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .comp-workbench__tab {
    width: 100%;
  }
}
</style>
