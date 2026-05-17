import { computed, ref, watch, type ComputedRef, type Ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { toggleDeviceStatus } from '@/api/device'
import {
  sendCompensationCapacitorBankRemoteCommand,
  writeCompensationCapacitorBankControlProfile,
  type CompensationCapacitorBankControlCapabilities,
  type CompensationCapacitorBankControlProfile,
} from '@/api/compensation'
import type { CompensationMonitorControlMode, DeviceControlLog } from '@/api/deviceMonitor'
import { buildControlModeRemoteCommand } from '@/features/device-control/controlModeCommand'
import { resolveControlModeLabel } from '@/features/device-control/resolveControlMode'
import {
  formatCapacitorBankControlValue,
  getCapacitorBankControlEditableValue,
  getCapacitorBankEditableParameterMeta,
} from '@/features/device-control/capacitorBankControlProfile'
import {
  extractControlConsoleErrorMessage,
  formatWriteTargetValue,
  notifyInvalidWriteTarget,
  roleLabel,
} from '@/features/device-control/controlConsoleUtils'

const manualPhaseOptions = [
  { label: 'A 相', value: 'A' as const },
  { label: 'B 相', value: 'B' as const },
  { label: 'C 相', value: 'C' as const },
  { label: '共补', value: 'COMMON' as const },
]

const manualSwitchActionOptions = [
  { label: '不投不切', value: 'none' as const },
  { label: '投入', value: 'on' as const },
  { label: '切除', value: 'off' as const },
]

const remoteCommandMeta = {
  reset_alarm: {
    label: '报警复位',
    confirm: '确认发送报警复位指令。',
  },
  switch_control_mode: {
    label: '控制模式切换',
    confirm: '确认切换当前控制模式。',
  },
} as const

export function useControlConsoleActions(input: {
  deviceId: ComputedRef<number>
  canManageDevices: ComputedRef<boolean>
  canControlDevices: ComputedRef<boolean>
  currentRole: ComputedRef<string>
  isAdmin: ComputedRef<boolean>
  archive: ComputedRef<{ name?: string | null } | null | undefined>
  runtimeStatus: ComputedRef<{ is_active?: boolean; is_online?: boolean } | null | undefined>
  controlProfile: Ref<CompensationCapacitorBankControlProfile | null>
  controlCapabilities: ComputedRef<CompensationCapacitorBankControlCapabilities | null | undefined>
  controlLogs: Ref<DeviceControlLog[]>
  monitorControlMode?: ComputedRef<CompensationMonitorControlMode | null | undefined>
  loadPage: () => Promise<void>
}) {
  const toggleSubmitting = ref(false)
  const writeSubmitting = ref(false)
  const writeDialogVisible = ref(false)
  const selectedParameterKey = ref('')
  const writeForm = ref<{
    parameter_key: string
    target_value: string | number | boolean | null
    reason: string
  }>({
    parameter_key: '',
    target_value: null,
    reason: '',
  })

  function draftKey(paramKey: string) {
    return `capbank-draft-${input.deviceId.value}-${paramKey}`
  }

  function saveDraft() {
    const key = writeForm.value.parameter_key
    if (!key) return
    try {
      localStorage.setItem(draftKey(key), JSON.stringify({
        target_value: writeForm.value.target_value,
        reason: writeForm.value.reason,
      }))
    } catch {
      // localStorage 不可用时静默忽略
    }
  }

  function restoreDraft(paramKey: string) {
    try {
      const raw = localStorage.getItem(draftKey(paramKey))
      if (!raw) return null
      return JSON.parse(raw) as { target_value: string | number | boolean | null; reason: string }
    } catch {
      return null
    }
  }

  function clearDraft(paramKey: string) {
    try {
      localStorage.removeItem(draftKey(paramKey))
    } catch {
      // ignore
    }
  }

  watch(writeForm, saveDraft, { deep: true })
  const manualSwitchForm = ref<{
    phase: 'A' | 'B' | 'C' | 'COMMON'
    switch_action: 'none' | 'on' | 'off'
  }>({
    phase: 'A',
    switch_action: 'on',
  })

  const canToggleRemotely = computed(() =>
    Boolean(input.canControlDevices.value)
    && input.runtimeStatus.value?.is_online !== false
    && input.controlCapabilities.value?.supports_remote_control === true,
  )
  const canRunRemoteAction = computed(() =>
    Boolean(input.canControlDevices.value)
    && input.runtimeStatus.value?.is_online !== false
    && input.controlCapabilities.value?.supports_remote_control === true,
  )
  function getRemoteCommandCapability(action: string) {
    return input.controlCapabilities.value?.remote_commands?.find((item) => item.action === action)
  }
  function isRemoteCommandSupported(action: string) {
    const capability = getRemoteCommandCapability(action)
    return capability ? capability.supported !== false : true
  }
  function remoteCommandDisabledReason(action: string) {
    const capability = getRemoteCommandCapability(action)
    if (capability?.supported === false) {
      return capability.disabled_reason || '真实网关暂未确认该远程动作，当前暂不开放。'
    }
    return remoteActionDisabledReason.value || '当前暂不允许执行远程控制'
  }
  function isParameterWritableByGateway(parameterKey: string) {
    const writableKeys = input.controlCapabilities.value?.writable_parameters
    return !writableKeys?.length || writableKeys.includes(parameterKey)
  }
  const remoteActionDisabledReason = computed(() => {
    if (!input.canControlDevices.value) return '无控制权限'
    if (input.runtimeStatus.value?.is_online === false) return '设备离线'
    if (!input.controlCapabilities.value?.supports_remote_control) return '不支持远程控制'
    return undefined
  })
  const currentControlModeLabel = computed(() =>
    resolveControlModeLabel(input.controlProfile.value, input.controlLogs.value, input.monitorControlMode?.value)
  )
  const isManualControlMode = computed(() => currentControlModeLabel.value === '手动')
  const canRunManualSwitch = computed(() => canRunRemoteAction.value && isManualControlMode.value)
  const manualSwitchDisabledReason = computed(() => {
    if (!canRunRemoteAction.value) {
      return input.controlCapabilities.value?.remote_control_status_message || '远程控制能力待接入'
    }
    if (!isManualControlMode.value) {
      return '当前为自动模式，请先在上方切换到手动模式后再执行投切。'
    }
    return ''
  })
  const canWriteParameters = computed(() =>
    Boolean(input.isAdmin.value)
    && input.runtimeStatus.value?.is_online !== false
    && input.controlCapabilities.value?.supports_write === true
    && ['fresh', 'stale'].includes(input.controlProfile.value?.source_status || ''),
  )
  const deviceActive = computed(() => input.runtimeStatus.value?.is_active ?? false)
  const selectedWriteMeta = computed(() => (
    selectedParameterKey.value ? getCapacitorBankEditableParameterMeta(selectedParameterKey.value) || null : null
  ))
  const writeDisabledReason = computed(() => {
    if (!input.isAdmin.value) return '仅管理员可执行参数写入。'
    if (input.runtimeStatus.value?.is_online === false) return '当前设备离线，暂不开放参数写入。'
    if (input.controlCapabilities.value?.supports_write !== true) {
      return input.controlCapabilities.value?.write_status_message || '参数写入能力未开通。'
    }
    if (!['fresh', 'stale'].includes(input.controlProfile.value?.source_status || '')) {
      return '当前设备尚未完成真实参数回读，暂不允许下发参数写入。'
    }
    return ''
  })
  const writeRiskNotice = computed(() => {
    if (input.controlProfile.value?.source_status === 'stale') {
      return '当前参数快照已过期，系统仍允许受控写入；提交前请先确认现场状态，并在写入后等待回读/回执复核。'
    }
    return ''
  })

  async function handleToggleDevice() {
    if (!input.deviceId.value || !canToggleRemotely.value) return
    const nextActive = !deviceActive.value
    const actionLabel = nextActive ? '启用' : '停用'
    try {
      await ElMessageBox.confirm(
        `确定要对 ${input.archive.value?.name || '当前设备'} 执行【${actionLabel}】指令吗？`,
        '远程控制确认',
        {
          confirmButtonText: `立即${actionLabel}`,
          cancelButtonText: '取消',
          type: 'warning',
        },
      )
    } catch {
      return
    }

    toggleSubmitting.value = true
    try {
      await toggleDeviceStatus(input.deviceId.value, nextActive, `控制台${actionLabel}设备`)
      ElMessage.success(`已发送${actionLabel}指令`)
      await input.loadPage()
    } catch {
      ElMessage.error(`${actionLabel}指令发送失败，请稍后重试`)
    } finally {
      toggleSubmitting.value = false
    }
  }

  async function handleRemoteCommand(action: keyof typeof remoteCommandMeta) {
    if (!input.deviceId.value || !canRunRemoteAction.value) return
    if (!isRemoteCommandSupported(action)) {
      ElMessage.warning(remoteCommandDisabledReason(action))
      return
    }
    const meta = remoteCommandMeta[action]
    const request = action === 'switch_control_mode'
      ? buildControlModeRemoteCommand(currentControlModeLabel.value)
      : { action, reason: `控制台${meta.label}` as const }
    try {
      await ElMessageBox.confirm(
        `${meta.confirm}\n当前模式：${currentControlModeLabel.value}。\n当前登录角色：${roleLabel(input.currentRole.value)}。`,
        meta.label,
        {
          confirmButtonText: '确认发送',
          cancelButtonText: '取消',
          type: 'warning',
        },
      )
    } catch {
      return
    }

    toggleSubmitting.value = true
    try {
      const response = await sendCompensationCapacitorBankRemoteCommand(input.deviceId.value, request)
      ElMessage.success(response.message || `${meta.label}指令已发送`)
      await input.loadPage()
    } catch (error) {
      ElMessage.error(extractControlConsoleErrorMessage(error, `${meta.label}失败，请稍后重试`))
    } finally {
      toggleSubmitting.value = false
    }
  }

  async function handleManualSwitchCommand() {
    if (!input.deviceId.value || !canRunManualSwitch.value) return
    const phaseText = manualPhaseOptions.find((item) => item.value === manualSwitchForm.value.phase)?.label || manualSwitchForm.value.phase
    const actionText = manualSwitchActionOptions.find((item) => item.value === manualSwitchForm.value.switch_action)?.label || manualSwitchForm.value.switch_action

    try {
      await ElMessageBox.confirm(
        [
          '将按 JKWF-LCD 功能码 0x44 发送原生手动控制请求。',
          '模式：手动模式',
          `相位：${phaseText}`,
          `动作：${actionText}`,
          '接口当前仅表示 accepted 入队，不代表设备端已执行成功。',
        ].join('\n'),
        '协议手动控制确认',
        {
          confirmButtonText: '确认发送',
          cancelButtonText: '取消',
          type: 'warning',
        },
      )
    } catch {
      return
    }

    toggleSubmitting.value = true
    try {
      const response = await sendCompensationCapacitorBankRemoteCommand(input.deviceId.value, {
        action: 'manual_switch',
        manual_mode: 'manual',
        phase: manualSwitchForm.value.phase,
        switch_action: manualSwitchForm.value.switch_action,
        reason: `控制台手动投切 ${phaseText} ${actionText}`,
      })
      ElMessage.success(response.message || '手动投切指令已发送')
      await input.loadPage()
    } catch (error) {
      ElMessage.error(extractControlConsoleErrorMessage(error, '手动投切失败，请稍后重试'))
    } finally {
      toggleSubmitting.value = false
    }
  }

  function openWriteDialog(parameterKey: string) {
    if (!canWriteParameters.value) {
      ElMessage.warning(writeDisabledReason.value || '当前暂不允许执行参数写入')
      return
    }
    const meta = getCapacitorBankEditableParameterMeta(parameterKey)
    if (!meta) {
      ElMessage.error('未找到对应参数配置')
      return
    }
    if (!isParameterWritableByGateway(parameterKey)) {
      ElMessage.warning('真实网关暂未确认该参数写入编码，当前暂不开放写入。')
      return
    }
    selectedParameterKey.value = parameterKey
    const draft = restoreDraft(parameterKey)
    writeForm.value = {
      parameter_key: parameterKey,
      target_value: draft?.target_value ?? getCapacitorBankControlEditableValue(input.controlProfile.value, meta),
      reason: draft?.reason ?? '',
    }
    writeDialogVisible.value = true
  }

  async function submitParameterWrite() {
    const meta = selectedWriteMeta.value
    if (!meta) return
    const normalizedTargetValue = notifyInvalidWriteTarget(meta, writeForm.value.target_value)
    if (normalizedTargetValue === null) return

    const previousValue = formatCapacitorBankControlValue(input.controlProfile.value, meta)
    const nextValueText = formatWriteTargetValue(meta, normalizedTargetValue)
    if (previousValue === nextValueText) {
      ElMessage.warning('目标值与当前快照一致，无需重复下发')
      return
    }

    try {
      await ElMessageBox.confirm(
        [
          `确定要写入参数【${meta.label}】吗？`,
          `当前值：${previousValue}`,
          `目标值：${nextValueText}`,
          '接口当前只表示 accepted 入队，不代表设备端已执行成功。',
        ].join('\n'),
        '参数写入确认',
        {
          confirmButtonText: '确认写入',
          cancelButtonText: '取消',
          type: 'warning',
        },
      )
    } catch {
      return
    }

    writeSubmitting.value = true
    try {
      const response = await writeCompensationCapacitorBankControlProfile(input.deviceId.value, {
        parameter_key: writeForm.value.parameter_key,
        target_value: normalizedTargetValue,
        reason: writeForm.value.reason.trim() || undefined,
      })
      ElMessage.success(response.message || '参数写入指令已入队')
      clearDraft(writeForm.value.parameter_key)
      writeDialogVisible.value = false
      await input.loadPage()
    } catch (error) {
      ElMessage.error(extractControlConsoleErrorMessage(error, '参数写入失败，请稍后重试'))
    } finally {
      writeSubmitting.value = false
    }
  }

  function handleActionCard(key: 'toggle_device' | 'reset_alarm' | 'switch_control_mode') {
    if (key === 'toggle_device') {
      void handleToggleDevice()
      return
    }
    if (key === 'reset_alarm') {
      void handleRemoteCommand('reset_alarm')
      return
    }
    void handleRemoteCommand('switch_control_mode')
  }

  return {
    toggleSubmitting,
    writeSubmitting,
    writeDialogVisible,
    writeForm,
    manualSwitchForm,
    currentControlModeLabel,
    canRunManualSwitch,
    manualSwitchDisabledReason,
    canWriteParameters,
    selectedWriteMeta,
    writeDisabledReason,
    writeRiskNotice,
    manualPhaseOptions,
    manualSwitchActionOptions,
    handleManualSwitchCommand,
    openWriteDialog,
    submitParameterWrite,
    handleActionCard,
    canToggleRemotely,
    canRunRemoteAction,
    remoteActionDisabledReason,
    deviceActive,
  }
}
