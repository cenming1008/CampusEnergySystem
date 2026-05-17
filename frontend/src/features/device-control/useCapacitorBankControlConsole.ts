import { computed, type ComputedRef } from 'vue'
import {
  filterCapacitorBankWritableParameterMeta,
  formatCapacitorBankControlValue,
} from '@/features/device-control/capacitorBankControlProfile'
import {
  buildControlConsoleActionCards,
  buildControlConsoleLogView,
  buildControlConsoleOverviewItems,
  buildControlConsoleReadonlySectionView,
  buildControlConsoleReadonlySummaryView,
  buildControlConsoleWriteSectionView,
} from '@/features/device-control/viewMapping'
import { useControlConsoleActions } from '@/features/device-control/useControlConsoleActions'
import { useControlConsoleData } from '@/features/device-control/useControlConsoleData'

export function useCapacitorBankControlConsole(input: {
  deviceId: ComputedRef<number>
  canManageDevices: ComputedRef<boolean>
  canControlDevices: ComputedRef<boolean>
  currentRole: ComputedRef<string>
  isAdmin: ComputedRef<boolean>
}) {
  const data = useControlConsoleData({
    deviceId: input.deviceId,
  })
  const actions = useControlConsoleActions({
    deviceId: input.deviceId,
    canManageDevices: input.canManageDevices,
    canControlDevices: input.canControlDevices,
    currentRole: input.currentRole,
    isAdmin: input.isAdmin,
    archive: data.archive,
    runtimeStatus: data.runtimeStatus,
    controlProfile: data.controlProfile,
    controlCapabilities: data.controlCapabilities,
    controlLogs: data.controlLogs,
    monitorControlMode: computed(() => data.overview.value?.compensation_monitor?.control_mode),
    loadPage: data.loadPage,
  })

  const overviewItems = computed(() => buildControlConsoleOverviewItems({
    archive: data.archive.value,
    runtimeStatus: data.runtimeStatus.value,
    profileSourceStatus: data.controlProfile.value?.source_status,
  }))
  const editableParameterCards = computed(() =>
    filterCapacitorBankWritableParameterMeta(data.controlCapabilities.value).map((item) => ({
      ...item,
      currentValue: formatCapacitorBankControlValue(data.controlProfile.value, item),
    })),
  )
  const actionCards = computed(() => buildControlConsoleActionCards({
    deviceActive: actions.deviceActive.value,
    canToggleRemotely: actions.canToggleRemotely.value,
    canRunRemoteAction: actions.canRunRemoteAction.value,
    currentControlModeLabel: actions.currentControlModeLabel.value,
    disabledReason: actions.remoteActionDisabledReason.value,
    remoteCommands: data.controlCapabilities.value?.remote_commands,
  }))
  const readonlySummaryView = computed(() => buildControlConsoleReadonlySummaryView({
    profile: data.controlProfile.value,
  }))
  const readonlySectionView = computed(() => buildControlConsoleReadonlySectionView({
    summaryView: readonlySummaryView.value,
  }))
  const writeSectionView = computed(() => buildControlConsoleWriteSectionView({
    canWriteParameters: actions.canWriteParameters.value,
    capabilities: data.controlCapabilities.value,
    isAdmin: input.isAdmin.value,
    canManageDevices: input.canManageDevices.value,
    writeDisabledReason: actions.writeDisabledReason.value,
    writeRiskNotice: actions.writeRiskNotice.value,
  }))
  const logView = computed(() => buildControlConsoleLogView({
    logs: data.controlLogs.value,
  }))

  return {
    loading: data.loading,
    toggleSubmitting: actions.toggleSubmitting,
    writeSubmitting: actions.writeSubmitting,
    writeDialogVisible: actions.writeDialogVisible,
    controlProfile: data.controlProfile,
    loadError: data.loadError,
    profileWarning: data.profileWarning,
    writeForm: actions.writeForm,
    manualSwitchForm: actions.manualSwitchForm,
    archive: data.archive,
    runtimeStatus: data.runtimeStatus,
    isCapacitorBankController: data.isCapacitorBankController,
    controlCapabilities: data.controlCapabilities,
    currentControlModeLabel: actions.currentControlModeLabel,
    canRunManualSwitch: actions.canRunManualSwitch,
    manualSwitchDisabledReason: actions.manualSwitchDisabledReason,
    canWriteParameters: actions.canWriteParameters,
    selectedWriteMeta: actions.selectedWriteMeta,
    overviewItems,
    editableParameterCards,
    manualPhaseOptions: actions.manualPhaseOptions,
    manualSwitchActionOptions: actions.manualSwitchActionOptions,
    actionCards,
    readonlySectionView,
    readonlySummaryView,
    writeSectionView,
    logView,
    loadPage: data.loadPage,
    handleManualSwitchCommand: actions.handleManualSwitchCommand,
    openWriteDialog: actions.openWriteDialog,
    submitParameterWrite: actions.submitParameterWrite,
    handleActionCard: actions.handleActionCard,
  }
}
