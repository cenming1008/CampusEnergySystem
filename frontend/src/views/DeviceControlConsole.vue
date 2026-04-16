<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Lock, Monitor, Refresh, Setting, SwitchButton } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { toggleDeviceStatus } from '@/api/device'
import {
  getDeviceMonitorControlLogs,
  getDeviceMonitorOverview,
  type DeviceControlLog,
  type MonitorOverview,
} from '@/api/deviceMonitor'
import {
  getCompensationCapacitorBankControlProfile,
  sendCompensationCapacitorBankRemoteCommand,
  writeCompensationCapacitorBankControlProfile,
  type CompensationCapacitorBankControlProfile,
} from '@/api/compensation'
import { resolveCompensationSubtype } from '@/shared/compensationDevices'
import { usePermissions } from '@/shared/composables/usePermissions'
import {
  capacitorBankEditableParameterMeta,
  capacitorBankControlGroupLabels,
  getCapacitorBankControlEditableValue,
  getCapacitorBankEditableParameterMeta,
  getCapacitorBankControlParameterMeta,
  capacitorBankControlParameterMeta,
  formatCapacitorBankControlValue,
} from '@/features/device-control/capacitorBankControlProfile'

const route = useRoute()
const router = useRouter()
const { canManageDevices, canControlDevices, currentRole, isAdmin } = usePermissions()
const REFRESH_INTERVAL_MS = 5000

const deviceId = computed(() => Number(route.params.id))
const loading = ref(false)
const toggleSubmitting = ref(false)
const writeSubmitting = ref(false)
const writeDialogVisible = ref(false)
const overview = ref<MonitorOverview | null>(null)
const controlProfile = ref<CompensationCapacitorBankControlProfile | null>(null)
const controlLogs = ref<DeviceControlLog[]>([])
const loadError = ref('')
let refreshTimer: ReturnType<typeof setInterval> | null = null
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
const manualSwitchForm = ref<{
  manual_mode: 'manual' | 'auto'
  phase: 'A' | 'B' | 'C' | 'COMMON'
  switch_action: 'none' | 'on' | 'off'
}>({
  manual_mode: 'manual',
  phase: 'A',
  switch_action: 'on',
})

const archive = computed(() => overview.value?.archive)
const runtimeStatus = computed(() => overview.value?.runtime_status)
const compensationSubtype = computed(() => resolveCompensationSubtype(
  archive.value?.device_type,
  archive.value?.device_subtype,
) || '')
const isCapacitorBankController = computed(() => compensationSubtype.value === 'capacitor_bank_controller')
const controlCapabilities = computed(() => controlProfile.value?.capabilities)
const canToggleRemotely = computed(() =>
  Boolean(canControlDevices.value)
  && runtimeStatus.value?.is_online !== false
  && controlCapabilities.value?.supports_remote_control === true,
)
const canRunRemoteAction = computed(() =>
  Boolean(canControlDevices.value)
  && runtimeStatus.value?.is_online !== false
  && controlCapabilities.value?.supports_remote_control === true,
)
const canRunManualSwitch = computed(() => canRunRemoteAction.value)
const canWriteParameters = computed(() =>
  Boolean(isAdmin.value)
  && runtimeStatus.value?.is_online !== false
  && controlCapabilities.value?.supports_write === true
  && ['fresh', 'stale'].includes(controlProfile.value?.source_status || ''),
)
const deviceActive = computed(() => runtimeStatus.value?.is_active ?? false)
const latestControlLog = computed(() => controlLogs.value[0] || null)
const latestTimeoutLog = computed(() =>
  controlLogs.value.find((item) => normalizeControlResult(item.result) === 'timeout') || null,
)
const selectedWriteMeta = computed(() => (
  selectedParameterKey.value ? getCapacitorBankEditableParameterMeta(selectedParameterKey.value) || null : null
))
const writeDisabledReason = computed(() => {
  if (!isAdmin.value) return '仅管理员可执行参数写入。'
  if (runtimeStatus.value?.is_online === false) return '当前设备离线，暂不开放参数写入。'
  if (controlCapabilities.value?.supports_write !== true) {
    return controlCapabilities.value?.write_status_message || '参数写入能力未开通。'
  }
  if (!['fresh', 'stale'].includes(controlProfile.value?.source_status || '')) {
    return '当前设备尚未完成真实参数回读，暂不允许下发参数写入。'
  }
  return ''
})
const writeRiskNotice = computed(() => {
  if (controlProfile.value?.source_status === 'stale') {
    return '当前参数快照已过期，系统仍允许受控写入；提交前请先确认现场状态，并在写入后等待回读/回执复核。'
  }
  return ''
})
const protocolSummaryText = computed(() => {
  if (!controlCapabilities.value) return ''
  return [
    `${controlCapabilities.value.command_message_type} -> ${controlCapabilities.value.control_topic_template}`,
    `${controlCapabilities.value.receipt_message_type} <- ${controlCapabilities.value.receipt_topic}`,
    `超时阈值 ${controlCapabilities.value.receipt_timeout_seconds}s`,
  ].join(' · ')
})

const overviewItems = computed(() => [
  { label: '设备名称', value: archive.value?.name || '--' },
  { label: '设备编码', value: archive.value?.sn || '--' },
  { label: '在线状态', value: runtimeStatus.value?.is_online ? '在线' : '离线' },
  { label: '最近通讯时间', value: formatDateTime(runtimeStatus.value?.last_message_at) },
  { label: '参数回读状态', value: sourceStatusText(controlProfile.value?.source_status) },
  { label: '当前告警摘要', value: `${runtimeStatus.value?.unresolved_alarm_count ?? 0} 条未处理` },
])

const groupedParameters = computed(() => {
  const groups = new Map<string, typeof capacitorBankControlParameterMeta>()
  for (const item of capacitorBankControlParameterMeta) {
    const existing = groups.get(item.group)
    if (existing) {
      existing.push(item)
    } else {
      groups.set(item.group, [item])
    }
  }
  return Array.from(groups.entries()).map(([key, items]) => ({
    key,
    label: capacitorBankControlGroupLabels[key as keyof typeof capacitorBankControlGroupLabels],
    items,
  }))
})

const editableParameterCards = computed(() =>
  capacitorBankEditableParameterMeta.map((item) => ({
    ...item,
    currentValue: formatCapacitorBankControlValue(controlProfile.value, item),
  })),
)

const manualModeOptions = [
  { label: '手动模式', value: 'manual' as const },
  { label: '自动模式', value: 'auto' as const },
]

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

const actionCards = computed(() => [
  {
    title: '启停 / 使能',
    icon: SwitchButton,
    hint: canToggleRemotely.value
      ? `当前设备${deviceActive.value ? '运行中，可执行停用' : '已停用，可执行启用'}`
      : controlCapabilities.value?.remote_control_status_message || '远程控制能力待接入',
    actionLabel: deviceActive.value ? '停用设备' : '启用设备',
    enabled: canToggleRemotely.value,
    handler: handleToggleDevice,
  },
  {
    title: '报警复位',
    icon: Refresh,
    hint: canRunRemoteAction.value ? '向控制主题发送报警复位命令，设备/网关执行后应通过 control_receipt 回执。' : controlCapabilities.value?.remote_control_status_message || '远程控制能力待接入',
    actionLabel: '立即复位',
    enabled: canRunRemoteAction.value,
    handler: () => handleRemoteCommand('reset_alarm'),
  },
  {
    title: '控制模式切换',
    icon: Setting,
    hint: canRunRemoteAction.value ? '向控制主题发送控制模式切换命令，结果由 control_receipt 回执确认。' : controlCapabilities.value?.remote_control_status_message || '远程控制能力待接入',
    actionLabel: '切换模式',
    enabled: canRunRemoteAction.value,
    handler: () => handleRemoteCommand('switch_control_mode'),
  },
])

const summaryItems = computed(() =>
  capacitorBankControlParameterMeta
    .filter((item) => item.summary)
    .map((item) => ({
      label: item.label,
      value: formatCapacitorBankControlValue(controlProfile.value, item),
    })),
)

const writeLogs = computed(() => controlLogs.value)

async function loadPage() {
  if (!deviceId.value) return
  loading.value = true
  loadError.value = ''
  try {
    const [overviewResponse, profileResponse] = await Promise.all([
      getDeviceMonitorOverview(deviceId.value),
      getCompensationCapacitorBankControlProfile(deviceId.value),
    ])
    overview.value = overviewResponse
    controlProfile.value = profileResponse
    const logs = await getDeviceMonitorControlLogs(deviceId.value, { limit: 10, hours: 168 })
    controlLogs.value = logs.items
    if (resolveCompensationSubtype(
      overviewResponse.archive?.device_type,
      overviewResponse.archive?.device_subtype,
    ) !== 'capacitor_bank_controller') {
      loadError.value = '当前设备不是电容补偿控制器，暂不支持进入控制台。'
    }
  } catch {
    loadError.value = '控制台数据加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function handleToggleDevice() {
  if (!deviceId.value || !canToggleRemotely.value) return
  const nextActive = !deviceActive.value
  const actionLabel = nextActive ? '启用' : '停用'
  try {
    await ElMessageBox.confirm(
      `确定要对 ${archive.value?.name || '当前设备'} 执行【${actionLabel}】指令吗？`,
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
    await toggleDeviceStatus(deviceId.value, nextActive, `控制台${actionLabel}设备`)
    ElMessage.success(`已发送${actionLabel}指令`)
    await loadPage()
  } catch {
    ElMessage.error(`${actionLabel}指令发送失败，请稍后重试`)
  } finally {
    toggleSubmitting.value = false
  }
}

const remoteCommandMeta = {
  reset_alarm: {
    label: '报警复位',
    confirm: '将向设备发送报警复位指令，模拟器会清除当前告警标志位。',
  },
  switch_control_mode: {
    label: '控制模式切换',
    confirm: '将向设备发送控制模式切换指令，模拟器会切换当前控制模式。',
  },
} as const

async function handleRemoteCommand(action: keyof typeof remoteCommandMeta) {
  if (!deviceId.value || !canRunRemoteAction.value) return
  const meta = remoteCommandMeta[action]
  try {
    await ElMessageBox.confirm(
      `${meta.confirm}\n当前登录角色：${roleLabel(currentRole.value)}。`,
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
    const response = await sendCompensationCapacitorBankRemoteCommand(deviceId.value, {
      action,
      reason: `控制台${meta.label}`,
    })
    ElMessage.success(response.message || `${meta.label}指令已发送`)
    await loadPage()
  } catch (error) {
    ElMessage.error(extractErrorMessage(error, `${meta.label}失败，请稍后重试`))
  } finally {
    toggleSubmitting.value = false
  }
}

async function handleManualSwitchCommand() {
  if (!deviceId.value || !canRunManualSwitch.value) return
  const modeText = manualModeOptions.find((item) => item.value === manualSwitchForm.value.manual_mode)?.label || manualSwitchForm.value.manual_mode
  const phaseText = manualPhaseOptions.find((item) => item.value === manualSwitchForm.value.phase)?.label || manualSwitchForm.value.phase
  const actionText = manualSwitchActionOptions.find((item) => item.value === manualSwitchForm.value.switch_action)?.label || manualSwitchForm.value.switch_action

  try {
    await ElMessageBox.confirm(
      [
        '将按 JKWF-LCD 功能码 0x44 发送原生手动控制请求。',
        `模式：${modeText}`,
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
    const response = await sendCompensationCapacitorBankRemoteCommand(deviceId.value, {
      action: 'manual_switch',
      manual_mode: manualSwitchForm.value.manual_mode,
      phase: manualSwitchForm.value.phase,
      switch_action: manualSwitchForm.value.switch_action,
      reason: `控制台手动投切 ${phaseText} ${actionText}`,
    })
    ElMessage.success(response.message || '手动投切指令已发送')
    await loadPage()
  } catch (error) {
    ElMessage.error(extractErrorMessage(error, '手动投切失败，请稍后重试'))
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
  selectedParameterKey.value = parameterKey
  writeForm.value = {
    parameter_key: parameterKey,
    target_value: getCapacitorBankControlEditableValue(controlProfile.value, meta),
    reason: '',
  }
  writeDialogVisible.value = true
}

async function submitParameterWrite() {
  const meta = selectedWriteMeta.value
  if (!meta) return
  const normalizedTargetValue = normalizeWriteTargetValue(meta)
  if (normalizedTargetValue === null) return

  const previousValue = formatCapacitorBankControlValue(controlProfile.value, meta)
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
    const response = await writeCompensationCapacitorBankControlProfile(deviceId.value, {
      parameter_key: writeForm.value.parameter_key,
      target_value: normalizedTargetValue,
      reason: writeForm.value.reason.trim() || undefined,
    })
    ElMessage.success(response.message || '参数写入指令已入队')
    writeDialogVisible.value = false
    await loadPage()
  } catch (error) {
    ElMessage.error(extractErrorMessage(error, '参数写入失败，请稍后重试'))
  } finally {
    writeSubmitting.value = false
  }
}

function goMonitor() {
  router.push(`/devices/${deviceId.value}/monitor`)
}

function sourceStatusText(status?: string) {
  if (status === 'fresh') return '最新参数'
  if (status === 'stale') return '参数可能过期'
  if (status === 'empty') return '暂无参数'
  return '状态未知'
}

function formatCapacitySlotList(values?: number[] | null) {
  if (!values?.length) return '未配置'
  return values.map((value) => `${Number(value).toFixed(1)} kvar`).join(' / ')
}

const capacityExpansionItems = computed(() => {
  const profile = controlProfile.value
  if (!profile) return []
  return [
    { label: 'A相分补', value: formatCapacitySlotList(profile.split_capacity_expansion?.phase_a_groups) },
    { label: 'B相分补', value: formatCapacitySlotList(profile.split_capacity_expansion?.phase_b_groups) },
    { label: 'C相分补', value: formatCapacitySlotList(profile.split_capacity_expansion?.phase_c_groups) },
    { label: '公补 1-8', value: formatCapacitySlotList(profile.common_capacity_expansion?.common_1_groups) },
    { label: '公补 9-16', value: formatCapacitySlotList(profile.common_capacity_expansion?.common_2_groups) },
    { label: '公补 17-24', value: formatCapacitySlotList(profile.common_capacity_expansion?.common_3_groups) },
  ]
})

function formatDateTime(value?: string | null) {
  if (!value) return '暂无记录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (num: number) => String(num).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

function formatWriteTargetValue(meta: NonNullable<typeof selectedWriteMeta.value>, value: string | number | boolean) {
  if (typeof value === 'boolean') {
    return value ? '开启' : '关闭'
  }
  return meta.unit ? `${value} ${meta.unit}` : String(value)
}

function normalizeWriteTargetValue(meta: NonNullable<typeof selectedWriteMeta.value>) {
  const value = writeForm.value.target_value
  if (meta.inputKind === 'boolean') {
    if (typeof value !== 'boolean') {
      ElMessage.warning(`请确认 ${meta.label} 的开关状态`)
      return null
    }
    return value
  }
  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) {
      ElMessage.warning(`请填写 ${meta.label}`)
      return null
    }
    return trimmed
  }
  if (typeof value !== 'number' || Number.isNaN(value)) {
    ElMessage.warning(`请填写有效的 ${meta.label}`)
    return null
  }
  return value
}

function resolveLogTitle(log: DeviceControlLog) {
  if (log.action === 'start') return '启用设备'
  if (log.action === 'stop') return '停用设备'
  if (log.action === 'manual_switch') return '手动投切'
  if (log.action === 'manual_switch_test') return '手动投切测试'
  if (log.action === 'reset_alarm') return '报警复位'
  if (log.action === 'switch_control_mode') return '控制模式切换'
  if (log.action.startsWith('write:')) {
    const meta = getCapacitorBankControlParameterMeta(log.action.slice(6))
    return meta ? `参数写入 · ${meta.label}` : `参数写入 · ${log.action.slice(6)}`
  }
  return log.action
}

function normalizeControlResult(result?: string | null) {
  const normalized = String(result || '').trim().toLowerCase()
  if (['accepted', 'running', 'success', 'failed', 'timeout', 'rejected'].includes(normalized)) {
    return normalized
  }
  return 'failed'
}

function resolveLogStatusText(log: DeviceControlLog) {
  const normalized = normalizeControlResult(log.result)
  if (normalized === 'accepted') return '已入队'
  if (normalized === 'running') return '设备执行中'
  if (normalized === 'success') return '执行成功'
  if (normalized === 'timeout') return '设备回执超时'
  if (normalized === 'rejected') return '设备拒绝执行'
  return '执行失败'
}

function resolveLogTagType(log: DeviceControlLog) {
  const normalized = normalizeControlResult(log.result)
  if (normalized === 'success') return 'success'
  if (normalized === 'accepted' || normalized === 'running') return 'warning'
  if (normalized === 'timeout' || normalized === 'failed' || normalized === 'rejected') return 'danger'
  return 'info'
}

function extractErrorMessage(error: unknown, fallback: string) {
  if (
    typeof error === 'object'
    && error
    && 'response' in error
    && typeof error.response === 'object'
    && error.response
    && 'data' in error.response
  ) {
    const responseData = error.response.data as { detail?: string; message?: string }
    if (typeof responseData.detail === 'string' && responseData.detail) return responseData.detail
    if (typeof responseData.message === 'string' && responseData.message) return responseData.message
  }
  if (error instanceof Error && error.message) return error.message
  return fallback
}

function roleLabel(role: string) {
  if (role === 'admin') return '管理员'
  if (role === 'operator') return '操作员'
  if (role === 'maintainer') return '运维员'
  return '访客'
}

watch(() => route.params.id, () => {
  void loadPage()
})

onMounted(() => {
  void loadPage()
  refreshTimer = setInterval(() => {
    void loadPage()
  }, REFRESH_INTERVAL_MS)
})

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<template>
  <div
    v-loading="loading"
    class="console-page"
  >
    <!-- Header -->
    <div class="console-head">
      <div class="console-head__left">
        <el-button
          :icon="ArrowLeft"
          text
          @click="router.push('/devices')"
        >
          返回设备台账
        </el-button>
        <div>
          <div class="console-head__title-row">
            <h2>{{ archive?.name || '补偿控制台' }}</h2>
            <span
              class="status-dot"
              :class="{ 'status-dot--online': runtimeStatus?.is_online }"
            />
            <span class="status-dot-label">{{ runtimeStatus?.is_online ? '在线' : '离线' }}</span>
          </div>
          <p>{{ archive?.sn || '--' }} · {{ archive?.location || '未配置安装位置' }}</p>
        </div>
      </div>
      <div class="console-head__actions">
        <el-button
          :icon="Monitor"
          @click="goMonitor"
        >
          前往监控页
        </el-button>
        <el-button
          :icon="Refresh"
          @click="loadPage"
        >
          刷新
        </el-button>
      </div>
    </div>

    <div
      v-if="loadError"
      class="console-alert"
    >
      <strong>控制台暂不可用</strong>
      <span>{{ loadError }}</span>
    </div>

    <template v-else-if="isCapacitorBankController">
      <div class="console-body">
        <!-- Left: main panels -->
        <div class="console-main">
          <!-- Section 1: 设备概览 -->
          <section class="console-panel console-panel--blue">
            <div class="console-panel__head">
              <h3>设备概览</h3>
              <span>确认设备身份、在线状态与最新通讯情况后再进行控制或参数核对。</span>
            </div>
            <div class="overview-grid">
              <div
                v-for="item in overviewItems"
                :key="item.label"
                class="overview-card"
              >
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
          </section>

          <!-- Section 2: 远程控制 -->
          <section class="console-panel console-panel--amber">
            <div class="console-panel__head">
              <h3>远程控制</h3>
              <span>{{ controlCapabilities?.remote_control_status_message || '远程控制链路尚未接入。' }}</span>
            </div>
            <div class="remote-actions">
              <button
                v-for="card in actionCards"
                :key="card.title"
                class="remote-card"
                :class="card.enabled ? 'remote-card--enabled' : 'remote-card--locked'"
                type="button"
                :disabled="!card.enabled || toggleSubmitting"
                @click="card.handler?.()"
              >
                <div class="remote-card__top">
                  <span class="remote-card__icon-wrap">
                    <component
                      :is="card.icon"
                      class="remote-card__icon"
                    />
                  </span>
                  <component
                    :is="Lock"
                    v-if="!card.enabled"
                    class="remote-card__lock-icon"
                  />
                </div>
                <strong>{{ card.title }}</strong>
                <span>{{ card.hint }}</span>
              </button>
            </div>
            <div class="manual-switch-box">
              <div class="manual-switch-box__head">
                <strong>协议手动控制</strong>
                <span>按 JKWF-LCD `0x44` 原生语义下发：手动/自动、相位、投切动作。</span>
              </div>
              <div class="manual-switch-row">
                <label class="manual-switch-label">模式</label>
                <el-select
                  v-model="manualSwitchForm.manual_mode"
                  :disabled="!canRunManualSwitch || toggleSubmitting"
                  class="manual-switch-select"
                >
                  <el-option
                    v-for="item in manualModeOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
                <label class="manual-switch-label">相位</label>
                <el-select
                  v-model="manualSwitchForm.phase"
                  :disabled="!canRunManualSwitch || toggleSubmitting"
                  class="manual-switch-select"
                >
                  <el-option
                    v-for="item in manualPhaseOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
                <label class="manual-switch-label">动作</label>
                <el-select
                  v-model="manualSwitchForm.switch_action"
                  :disabled="!canRunManualSwitch || toggleSubmitting"
                  class="manual-switch-select"
                >
                  <el-option
                    v-for="item in manualSwitchActionOptions"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
                <el-button
                  type="warning"
                  :loading="toggleSubmitting"
                  :disabled="!canRunManualSwitch"
                  @click="handleManualSwitchCommand"
                >
                  发送 0x44 手动控制
                </el-button>
              </div>
            </div>
            <div class="capability-note">
              <el-tag
                :type="controlCapabilities?.supports_remote_control ? 'success' : 'info'"
                effect="dark"
              >
                {{ controlCapabilities?.supports_remote_control ? '已开通远程控制' : '远程控制待开通' }}
              </el-tag>
              <div class="capability-note__text">
                <small>
                  当前登录角色：{{ roleLabel(currentRole) }}
                  · {{ canControlDevices ? '可执行远程控制' : '没有远程控制权限' }}
                  · 最近结果：{{ latestControlLog ? `${resolveLogTitle(latestControlLog)} / ${resolveLogStatusText(latestControlLog)} / ${formatDateTime(latestControlLog.created_at)}` : '暂无记录' }}
                </small>
                <small v-if="protocolSummaryText">{{ protocolSummaryText }}</small>
              </div>
            </div>
          </section>

          <!-- Section 3: 参数管理 -->
          <section class="console-panel console-panel--teal">
            <div class="console-panel__head">
              <h3>参数管理</h3>
              <span>{{ controlCapabilities?.write_status_message || '当前仅开放只读参数展示。' }}</span>
            </div>

            <!-- Sub-zone A: 只读快照 -->
            <div class="param-zone param-zone--readonly">
              <div class="param-zone__head">
                <span class="param-zone__label">只读参数快照</span>
                <div class="param-zone__head-right">
                  <el-tag
                    :type="controlProfile?.source_status === 'fresh' ? 'success' : controlProfile?.source_status === 'stale' ? 'warning' : 'info'"
                    effect="dark"
                    size="small"
                  >
                    {{ sourceStatusText(controlProfile?.source_status) }}
                  </el-tag>
                  <small>来源：{{ controlProfile?.source || '未上报' }} · 快照：{{ formatDateTime(controlProfile?.snapshot_timestamp || controlProfile?.updated_at) }}</small>
                </div>
              </div>
              <div class="summary-strip">
                <div
                  v-for="item in summaryItems"
                  :key="item.label"
                  class="summary-chip"
                >
                  <span>{{ item.label }}</span>
                  <strong>{{ item.value }}</strong>
                </div>
              </div>
              <div
                v-if="capacityExpansionItems.length"
                class="capacity-expansion-panel"
              >
                <div class="capacity-expansion-panel__head">
                  <strong>容量展开详情</strong>
                  <span>按容量编码与阶梯容量展开每一路实际配置</span>
                </div>
                <div class="capacity-expansion-grid">
                  <div
                    v-for="item in capacityExpansionItems"
                    :key="item.label"
                    class="capacity-expansion-card"
                  >
                    <span>{{ item.label }}</span>
                    <strong>{{ item.value }}</strong>
                  </div>
                </div>
              </div>
              <div class="param-groups">
                <section
                  v-for="group in groupedParameters"
                  :key="group.key"
                  class="param-group"
                >
                  <header class="param-group__head">
                    <h4>{{ group.label }}</h4>
                    <span>协议参数只读快照</span>
                  </header>
                  <div class="param-table">
                    <div class="param-table__row param-table__row--head">
                      <span>参数 / 说明</span>
                      <span>当前值</span>
                      <span class="param-table__meta-col">寄存器 · 读写</span>
                    </div>
                    <div
                      v-for="item in group.items"
                      :key="item.key"
                      class="param-table__row"
                    >
                      <div class="param-table__label">
                        <strong>{{ item.label }}</strong>
                        <small>{{ item.description }}</small>
                      </div>
                      <span class="param-table__value">{{ formatCapacitorBankControlValue(controlProfile, item) }}</span>
                      <div class="param-table__meta param-table__meta-col">
                        <span>{{ item.register }}</span>
                        <small>{{ item.readWrite }}</small>
                      </div>
                    </div>
                  </div>
                </section>
              </div>
            </div>

            <!-- Sub-zone B: 受控写入 -->
            <div
              class="param-zone param-zone--writable"
              :class="{ 'param-zone--locked': !canWriteParameters }"
            >
              <div class="param-zone__head">
                <span class="param-zone__label">受控写入入口</span>
                <div class="param-zone__head-right">
                  <el-tag
                    :type="canWriteParameters ? 'success' : 'warning'"
                    effect="dark"
                    size="small"
                  >
                    {{ canWriteParameters ? '当前允许写入' : '当前禁止写入' }}
                  </el-tag>
                  <el-tag
                    :type="controlCapabilities?.supports_write ? 'success' : 'info'"
                    effect="dark"
                    size="small"
                  >
                    {{ controlCapabilities?.supports_write ? '支持参数写入' : '参数写入待开通' }}
                  </el-tag>
                </div>
              </div>
              <p class="param-zone__desc">
                当前已按协议范围开放全部可写参数，提交前仍需二次确认；设备端结果仍需等待回读或回执核对。
                当前账号参数权限：{{ isAdmin ? '管理员，可发起受控写入' : canManageDevices ? '可查看档案，不可写入' : '仅查看' }}
              </p>
              <div
                v-if="writeDisabledReason"
                class="console-inline-alert"
              >
                <strong>写入入口已锁定</strong>
                <span>{{ writeDisabledReason }}</span>
              </div>
              <div
                v-else-if="writeRiskNotice"
                class="console-inline-alert console-inline-alert--soft"
              >
                <strong>写入前确认</strong>
                <span>{{ writeRiskNotice }}</span>
              </div>
              <div class="editable-grid">
                <button
                  v-for="item in editableParameterCards"
                  :key="item.key"
                  class="editable-card"
                  type="button"
                  :disabled="!canWriteParameters"
                  @click="openWriteDialog(String(item.key))"
                >
                  <span>{{ item.label }}</span>
                  <strong>{{ item.currentValue }}</strong>
                  <small>{{ item.description }}</small>
                  <em>{{ canWriteParameters ? '修改参数' : '当前不可写入' }}</em>
                </button>
              </div>
            </div>
          </section>
        </div>

        <!-- Right: logs sidebar -->
        <aside class="console-sidebar">
          <section class="console-panel console-panel--neutral">
            <div class="console-panel__head">
              <h3>写入日志 / 结果</h3>
              <span>最近控制记录</span>
            </div>
            <div
              v-if="latestTimeoutLog"
              class="console-inline-alert"
            >
              <strong>检测到设备回执超时</strong>
              <span>{{ resolveLogTitle(latestTimeoutLog) }} 在 {{ formatDateTime(latestTimeoutLog.created_at) }} 发起后未在约定时间内收到回执，请结合现场状态复核。</span>
            </div>
            <div
              v-if="!writeLogs.length"
              class="empty-box"
            >
              <strong>暂无写入日志</strong>
              <span>当前还没有控制记录，可先尝试启用/停用设备验证远程控制链路。</span>
            </div>
            <div
              v-else
              class="log-timeline"
            >
              <div
                v-for="log in writeLogs"
                :key="log.id"
                class="log-entry"
              >
                <div class="log-entry__track">
                  <span
                    class="log-entry__dot"
                    :class="`log-entry__dot--${resolveLogTagType(log)}`"
                  />
                  <span class="log-entry__line" />
                </div>
                <div class="log-entry__content">
                  <div class="log-entry__top">
                    <strong>{{ resolveLogTitle(log) }}</strong>
                    <el-tag
                      :type="resolveLogTagType(log)"
                      effect="dark"
                      size="small"
                    >
                      {{ resolveLogStatusText(log) }}
                    </el-tag>
                  </div>
                  <span>{{ formatDateTime(log.created_at) }} · {{ log.operator || '未知操作人' }}</span>
                  <small v-if="log.reason">{{ log.reason }}</small>
                  <small class="log-entry__source">{{ log.command_source || 'api' }}</small>
                </div>
              </div>
            </div>
          </section>
        </aside>
      </div>
    </template>

    <el-dialog
      v-model="writeDialogVisible"
      width="560px"
      :close-on-click-modal="false"
      title="参数写入"
    >
      <template v-if="selectedWriteMeta">
        <div class="dialog-intro">
          <strong>{{ selectedWriteMeta.label }}</strong>
          <span>{{ selectedWriteMeta.description }}</span>
        </div>
        <div class="dialog-current">
          <span>当前快照值</span>
          <strong>{{ formatCapacitorBankControlValue(controlProfile, selectedWriteMeta) }}</strong>
        </div>
        <el-form label-position="top">
          <el-form-item label="目标值">
            <el-switch
              v-if="selectedWriteMeta.inputKind === 'boolean'"
              v-model="writeForm.target_value"
              inline-prompt
              active-text="开启"
              inactive-text="关闭"
            />
            <el-select
              v-else-if="selectedWriteMeta.inputKind === 'select'"
              v-model="writeForm.target_value"
              style="width: 100%"
            >
              <el-option
                v-for="item in selectedWriteMeta.options || []"
                :key="String(item.value)"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-input
              v-else-if="selectedWriteMeta.inputKind === 'text'"
              v-model="writeForm.target_value"
              placeholder="请输入参数值"
            />
            <el-input-number
              v-else
              v-model="writeForm.target_value"
              :min="selectedWriteMeta.min"
              :max="selectedWriteMeta.max"
              :step="selectedWriteMeta.step || 1"
              :precision="selectedWriteMeta.step && selectedWriteMeta.step < 1 ? Math.round(-Math.log10(selectedWriteMeta.step)) : 0"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="写入说明（选填）">
            <el-input
              v-model="writeForm.reason"
              type="textarea"
              :rows="3"
              maxlength="120"
              show-word-limit
              placeholder="例如：联调验证 / 现场调优 / 告警阈值收敛"
            />
          </el-form-item>
        </el-form>
        <div class="console-inline-alert console-inline-alert--soft">
          <strong>风险提示</strong>
          <span>接口当前仅表示 accepted 入队；提交后请结合设备回读、控制日志与现场反馈确认实际执行结果。</span>
        </div>
      </template>
      <template #footer>
        <div class="dialog-actions">
          <el-button @click="writeDialogVisible = false">取消</el-button>
          <el-button
            type="warning"
            :loading="writeSubmitting"
            @click="submitParameterWrite"
          >
            确认写入
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
/* ─── Base ─────────────────────────────────────────────────── */

.console-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  color: #dbe5f4;
}

/* ─── Header ────────────────────────────────────────────────── */

.console-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 18px 24px;
  border-radius: 16px;
  border: 1px solid rgba(52, 72, 99, 0.88);
  background: linear-gradient(180deg, rgba(18, 31, 49, 0.98), rgba(11, 21, 35, 0.98));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

.console-head__left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.console-head__title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.console-head__title-row h2 {
  margin: 0;
  font-size: 22px;
  color: #f7fbff;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4b5563;
  flex-shrink: 0;
}

.status-dot--online {
  background: #4ade80;
  box-shadow: 0 0 7px rgba(74, 222, 128, 0.55);
}

.status-dot-label {
  font-size: 12px;
  color: #8ea0bc;
}

.console-head__left > div > p {
  margin: 5px 0 0;
  color: #8ea5c1;
  font-size: 13px;
}

.console-head__actions {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
}

/* ─── Alert ──────────────────────────────────────────────────── */

.console-alert {
  padding: 16px 20px;
  border-radius: 16px;
  border: 1px solid rgba(196, 88, 88, 0.55);
  background: linear-gradient(180deg, rgba(18, 31, 49, 0.98), rgba(11, 21, 35, 0.98));
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.console-alert strong {
  color: #ffd5d5;
}

.console-alert span {
  color: #ffb4b4;
  font-size: 13px;
}

/* ─── Two-column body ─────────────────────────────────────────── */

.console-body {
  display: grid;
  grid-template-columns: 1fr min(320px, 30%);
  gap: 20px;
  align-items: start;
}

.console-main {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.console-sidebar {
  position: sticky;
  top: 20px;
}

/* ─── Panels ─────────────────────────────────────────────────── */

.console-panel {
  padding: 20px 24px;
  border-radius: 16px;
  border: 1px solid rgba(52, 72, 99, 0.88);
  background: linear-gradient(180deg, rgba(18, 31, 49, 0.98), rgba(11, 21, 35, 0.98));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
  position: relative;
}

/* Left accent bar */
.console-panel::before {
  content: '';
  position: absolute;
  top: 16px;
  bottom: 16px;
  left: 0;
  width: 3px;
  border-radius: 0 2px 2px 0;
}

.console-panel--blue {
  background-image:
    linear-gradient(180deg, rgba(96, 165, 250, 0.04) 0%, transparent 70%),
    linear-gradient(180deg, rgba(18, 31, 49, 0.98), rgba(11, 21, 35, 0.98));
}
.console-panel--blue::before { background: #60a5fa; }

.console-panel--amber {
  background-image:
    linear-gradient(180deg, rgba(251, 191, 36, 0.05) 0%, transparent 70%),
    linear-gradient(180deg, rgba(18, 31, 49, 0.98), rgba(11, 21, 35, 0.98));
}
.console-panel--amber::before { background: #fbbf24; }

.console-panel--teal {
  background-image:
    linear-gradient(180deg, rgba(45, 212, 191, 0.04) 0%, transparent 70%),
    linear-gradient(180deg, rgba(18, 31, 49, 0.98), rgba(11, 21, 35, 0.98));
}
.console-panel--teal::before { background: #2dd4bf; }

.console-panel--neutral::before { background: rgba(110, 130, 160, 0.45); }

.console-panel__head {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.console-panel__head h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.console-panel--blue  .console-panel__head h3 { color: #93c5fd; }
.console-panel--amber .console-panel__head h3 { color: #fde68a; }
.console-panel--teal  .console-panel__head h3 { color: #5eead4; }
.console-panel--neutral .console-panel__head h3 { color: #cbd5e1; }

.console-panel__head > span {
  color: #8ca0ba;
  font-size: 12px;
  line-height: 1.5;
  text-align: right;
}

/* ─── Overview grid ──────────────────────────────────────────── */

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}

.overview-card {
  padding: 14px;
  border-radius: 12px;
  border: 1px solid rgba(48, 70, 95, 0.72);
  background: rgba(19, 34, 53, 0.7);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.overview-card span {
  color: #91a5c2;
  font-size: 12px;
}

.overview-card strong {
  color: #f7fbff;
  line-height: 1.5;
  font-size: 14px;
}

/* ─── Remote control cards ───────────────────────────────────── */

.remote-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.remote-card {
  min-height: 150px;
  padding: 18px 20px;
  border-radius: 12px;
  border: 1px solid rgba(48, 70, 95, 0.6);
  background: rgba(19, 34, 53, 0.7);
  text-align: left;
  color: #a7b7cb;
  display: flex;
  flex-direction: column;
  gap: 0;
  transition: border-color 0.18s ease;
}

.remote-card--locked {
  cursor: not-allowed;
  opacity: 0.45;
  filter: grayscale(0.3);
}

.remote-card--enabled {
  cursor: pointer;
  opacity: 1;
  border-color: rgba(251, 191, 36, 0.4);
  background: rgba(19, 34, 53, 0.7);
}

.remote-card--enabled:hover {
  border-color: rgba(251, 191, 36, 0.65);
}

.remote-card--enabled:active {
  border-color: rgba(251, 191, 36, 0.5);
}

.remote-card__top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

/* Icon badge wrapper */
.remote-card__icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(48, 70, 95, 0.55);
  border: 1px solid rgba(48, 70, 95, 0.8);
  flex-shrink: 0;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.remote-card--enabled .remote-card__icon-wrap {
  background: rgba(120, 80, 10, 0.38);
  border-color: rgba(251, 191, 36, 0.28);
}

.remote-card__icon {
  width: 18px;
  height: 18px;
  color: #4b6282;
  transition: color 0.2s ease;
}

.remote-card--enabled .remote-card__icon {
  color: #fbbf24;
}

.remote-card__lock-icon {
  width: 14px;
  height: 14px;
  color: #4b5e75;
  opacity: 0.7;
}

.remote-card strong {
  display: block;
  margin-bottom: 4px;
}

.remote-card--enabled strong {
  color: #fde68a;
}

.remote-card--locked strong {
  color: #8ca0ba;
}

.remote-card span {
  font-size: 12px;
  line-height: 1.6;
  color: #8ca0ba;
}

.manual-switch-box {
  margin-top: 20px;
  padding: 16px 18px 18px;
  border-radius: 14px;
  border: 1px solid rgba(251, 191, 36, 0.28);
  background: rgba(14, 26, 42, 0.55);
  display: flex;
  flex-direction: column;
  gap: 14px;
  position: relative;
}

/* Amber hairline divider above the box */
.manual-switch-box::before {
  content: '';
  position: absolute;
  top: -11px;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(251, 191, 36, 0.22) 20%,
    rgba(251, 191, 36, 0.22) 80%,
    transparent 100%
  );
}

.manual-switch-box__head {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(251, 191, 36, 0.15);
}

.manual-switch-box__head strong {
  color: #fde68a;
  font-size: 12px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.manual-switch-box__head span {
  color: #7a90ab;
  font-size: 11.5px;
  font-family: 'JetBrains Mono', 'Menlo', monospace;
}

.manual-switch-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.manual-switch-label {
  color: #8ca0ba;
  font-size: 12px;
  white-space: nowrap;
  flex-shrink: 0;
}

.manual-switch-select {
  flex: 1;
  min-width: 120px;
  max-width: 220px;
}

.manual-switch-row .el-button {
  margin-left: auto;
  flex-shrink: 0;
}

/* Element Plus dark-theme overrides (scoped to manual-switch-box) */
.manual-switch-box :deep(.el-select .el-input__wrapper) {
  background: rgba(14, 26, 42, 0.75);
  box-shadow: 0 0 0 1px rgba(48, 70, 95, 0.7) inset;
}

.manual-switch-box :deep(.el-select .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(251, 191, 36, 0.4) inset;
}

.manual-switch-box :deep(.el-select .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px rgba(251, 191, 36, 0.65) inset;
}

.manual-switch-box :deep(.el-input__inner) {
  color: #d4e0f0;
}

/* ─── Capability note ────────────────────────────────────────── */

.capability-note {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(14, 26, 42, 0.5);
  border: 1px solid rgba(48, 70, 95, 0.5);
  flex-wrap: wrap;
}

.capability-note__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.capability-note small {
  color: #7a90ab;
  font-size: 11px;
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.capability-note__text small:last-child {
  color: #5a7090;
  font-size: 10.5px;
}

/* ─── Param zones ────────────────────────────────────────────── */

.param-zone {
  margin-top: 20px;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid transparent;
}

.param-zone__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.param-zone__head-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.param-zone__head-right small {
  color: #7a90ab;
  font-size: 11px;
}

.param-zone__label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.param-zone--readonly {
  background: rgba(30, 58, 90, 0.2);
  border-color: rgba(96, 165, 250, 0.2);
}

.param-zone--readonly .param-zone__label { color: #60a5fa; }

.param-zone--writable {
  background: rgba(90, 58, 12, 0.2);
  border-color: rgba(251, 191, 36, 0.22);
}

.param-zone--writable .param-zone__label { color: #fbbf24; }

.param-zone--locked {
  opacity: 0.75;
  border-style: dashed;
}

.param-zone__desc {
  margin: 0 0 12px;
  color: #8ca0ba;
  font-size: 12px;
  line-height: 1.7;
}

/* ─── Summary strip ──────────────────────────────────────────── */

.summary-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}

.summary-chip {
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid rgba(48, 70, 95, 0.72);
  background: rgba(14, 26, 42, 0.6);
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.summary-chip span {
  color: #91a5c2;
  font-size: 11px;
}

.summary-chip strong {
  color: #f7fbff;
  font-size: 14px;
  line-height: 1.4;
}

.capacity-expansion-panel {
  margin-bottom: 16px;
  padding: 14px;
  border-radius: 12px;
  border: 1px solid rgba(48, 70, 95, 0.72);
  background: rgba(12, 22, 38, 0.64);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.capacity-expansion-panel__head {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.capacity-expansion-panel__head strong {
  color: #f7fbff;
  font-size: 13px;
}

.capacity-expansion-panel__head span {
  color: #8ca0ba;
  font-size: 11px;
}

.capacity-expansion-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.capacity-expansion-card {
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid rgba(55, 73, 96, 0.58);
  background: rgba(16, 28, 44, 0.68);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.capacity-expansion-card span {
  color: #91a5c2;
  font-size: 11px;
}

.capacity-expansion-card strong {
  color: #f7fbff;
  font-size: 12px;
  line-height: 1.5;
}

/* ─── Param groups & table ───────────────────────────────────── */

.param-groups {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.param-group {
  border: 1px solid rgba(44, 65, 89, 0.7);
  border-radius: 12px;
  background: rgba(12, 22, 38, 0.7);
  overflow: hidden;
}

.param-group__head {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(44, 65, 89, 0.7);
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.param-group__head h4 {
  margin: 0;
  font-size: 13px;
  color: #c8d8ee;
}

.param-group__head span {
  color: #6a84a2;
  font-size: 11px;
}

.param-table {
  display: flex;
  flex-direction: column;
}

.param-table__row {
  display: grid;
  grid-template-columns: 1fr 160px 120px;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(33, 52, 74, 0.6);
  align-items: center;
}

.param-table__row:last-child {
  border-bottom: none;
}

.param-table__row--head {
  background: rgba(20, 36, 57, 0.9);
  color: #6a84a2;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.param-table__label {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.param-table__label strong {
  color: #eef5ff;
  font-size: 13px;
}

.param-table__label small {
  color: #7a90ab;
  font-size: 11px;
  line-height: 1.5;
}

.param-table__value {
  color: #c8d8ee;
  font-size: 13px;
  line-height: 1.5;
}

.param-table__meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.param-table__meta span {
  color: #8ca0ba;
  font-size: 12px;
}

.param-table__meta small {
  color: #5d7699;
  font-size: 11px;
}

/* ─── Inline alert ───────────────────────────────────────────── */

.console-inline-alert {
  margin-bottom: 14px;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid rgba(170, 122, 36, 0.4);
  background: rgba(73, 48, 14, 0.22);
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.console-inline-alert strong {
  color: #fcd34d;
  font-size: 13px;
}

.console-inline-alert span {
  color: #d8c08a;
  font-size: 12px;
  line-height: 1.6;
}

.console-inline-alert--soft {
  margin-top: 0;
  margin-bottom: 0;
}

/* ─── Editable param cards ───────────────────────────────────── */

.editable-grid {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.editable-card {
  padding: 14px;
  border-radius: 12px;
  border: 1px solid rgba(48, 70, 95, 0.72);
  background: rgba(19, 34, 53, 0.75);
  color: #dbe5f4;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 7px;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.editable-card:not(:disabled):hover {
  border-color: rgba(251, 191, 36, 0.5);
  box-shadow: 0 2px 12px rgba(251, 191, 36, 0.07);
}

.editable-card:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.editable-card span {
  color: #91a5c2;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.editable-card strong {
  color: #f8fbff;
  font-size: 16px;
}

.editable-card small {
  color: #7a90ab;
  font-size: 11px;
  line-height: 1.5;
}

.editable-card em {
  margin-top: auto;
  font-style: normal;
  color: #fbbf24;
  font-size: 11px;
}

.editable-card:disabled em {
  color: #4b6282;
}

/* ─── Log timeline ───────────────────────────────────────────── */

.empty-box {
  min-height: 120px;
  border-radius: 12px;
  border: 1px dashed rgba(70, 91, 117, 0.65);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 8px;
  color: #90a4c2;
  text-align: center;
  padding: 12px;
}

.empty-box strong {
  color: #cbd5e1;
}

.log-timeline {
  display: flex;
  flex-direction: column;
}

.log-entry {
  display: flex;
  gap: 12px;
  padding-bottom: 16px;
}

.log-entry__track {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 16px;
  padding-top: 3px;
}

.log-entry__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid currentColor;
  background: transparent;
  flex-shrink: 0;
}

.log-entry__dot--success { color: #4ade80; }
.log-entry__dot--warning { color: #fbbf24; }
.log-entry__dot--danger  { color: #f87171; }
.log-entry__dot--info    { color: #60a5fa; }

.log-entry__line {
  flex: 1;
  width: 1px;
  background: rgba(52, 72, 100, 0.55);
  margin-top: 5px;
}

.log-entry:last-child .log-entry__line {
  display: none;
}

.log-entry__content {
  flex: 1;
  min-width: 0;
  padding-bottom: 4px;
}

.log-entry__top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 4px;
}

.log-entry__top strong {
  color: #eef5ff;
  font-size: 13px;
  line-height: 1.4;
}

.log-entry__content > span,
.log-entry__content > small {
  display: block;
  color: #7a90ab;
  font-size: 11px;
  margin-top: 3px;
  line-height: 1.5;
}

.log-entry__source {
  color: #4b6282 !important;
  margin-top: 5px !important;
}

/* ─── Dialog ─────────────────────────────────────────────────── */

.dialog-intro,
.dialog-current {
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid rgba(48, 70, 95, 0.82);
  background: rgba(19, 34, 53, 0.88);
  margin-bottom: 14px;
}

.dialog-intro strong,
.dialog-current strong {
  display: block;
  color: #eef5ff;
}

.dialog-intro span,
.dialog-current span {
  display: block;
  margin-top: 6px;
  color: #8ca0ba;
  font-size: 12px;
  line-height: 1.6;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
}

/* ─── Responsive ─────────────────────────────────────────────── */

@media (max-width: 1100px) {
  .console-body {
    grid-template-columns: 1fr;
  }

  .console-sidebar {
    position: static;
  }

  .console-head,
  .console-panel__head {
    flex-direction: column;
    align-items: flex-start;
  }

  .console-panel__head > span {
    text-align: left;
  }

  .capability-note {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 800px) {
  .param-table__row {
    grid-template-columns: 1fr 120px;
  }

  .param-table__meta-col {
    display: none;
  }
}
</style>
