import type { CompensationCapacitorBankControlCapabilities, CompensationCapacitorBankControlProfile } from '@/api/compensation'
import type { DeviceControlLog, MonitorOverview } from '@/api/deviceMonitor'
import {
  capacitorBankControlGroupLabels,
  capacitorBankControlParameterMeta,
  formatCapacitorBankControlValue,
  getCapacitorBankControlParameterMeta,
  type CapacitorBankControlParameterMeta,
} from '@/features/device-control/capacitorBankControlProfile'

export interface ControlConsoleOverviewItem {
  label: string
  value: string
}

export interface ControlConsoleActionCard {
  key: 'toggle_device' | 'reset_alarm' | 'switch_control_mode'
  title: string
  actionLabel: string
  enabled: boolean
  iconKey: 'switch' | 'refresh' | 'setting'
  disabledReason?: string
}

export interface ControlConsoleCapacityExpansionItem {
  label: string
  value: string
}

export interface ControlConsoleParameterRow {
  key: string
  label: string
  description: string
  currentValue: string
  register: string
  readWrite: string
}

export interface ControlConsoleParameterGroup {
  key: string
  label: string
  items: ControlConsoleParameterRow[]
}

export interface ControlConsoleReadonlySummaryView {
  summaryItems: Array<{ label: string; value: string }>
  capacityExpansionItems: ControlConsoleCapacityExpansionItem[]
  groupedParameters: ControlConsoleParameterGroup[]
  sourceStatusText: string
  sourceStatusTone: 'success' | 'warning' | 'info'
  sourceMeta: string
}

export interface ControlConsoleReadonlySectionView {
  title: string
  sectionLabel: string
  tone: 'readonly'
  tags: Array<{ text: string; tone: 'success' | 'warning' | 'info' }>
  metaText: string
  showCapacityExpansion: boolean
}

const readonlyParameterGroupOrder = ['strategy', 'circuits', 'protection', 'device']

export interface ControlConsoleWriteSectionView {
  title: string
  sectionLabel: string
  tone: 'writable'
  description: string
  tags: Array<{ text: string; tone: 'success' | 'warning' | 'info' }>
  writeStatusText: string
  writeStatusTone: 'success' | 'warning'
  capabilityStatusText: string
  capabilityStatusTone: 'success' | 'info'
  roleSummaryText: string
  alert: {
    title: string
    message: string
    tone: 'warning' | 'danger'
  } | null
}

export interface ControlConsoleLogEntry {
  id: number
  title: string
  statusText: string
  statusTone: 'success' | 'warning' | 'danger' | 'info'
  createdAtText: string
  operatorText: string
  reason?: string
  sourceText: string
}

export interface ControlConsoleLogView {
  latestLogText: string
  latestLogStatusTone: 'success' | 'warning' | 'danger' | 'info' | null
  latestLogStatusLabel: string
  latestTimeoutAlertText: string | null
  entries: ControlConsoleLogEntry[]
}

function sourceStatusText(status?: string) {
  if (status === 'fresh') return '最新参数'
  if (status === 'stale') return '参数可能过期'
  if (status === 'empty') return '暂无参数'
  return '状态未知'
}

function sourceStatusTone(status?: string): 'success' | 'warning' | 'info' {
  if (status === 'fresh') return 'success'
  if (status === 'stale') return 'warning'
  return 'info'
}

function formatDateTime(value?: string | null) {
  if (!value) return '暂无记录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (num: number) => String(num).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

function formatCapacitySlotList(values?: number[] | null) {
  if (!values?.length) return '未配置'
  return values.map((value) => `${Number(value).toFixed(1)} kvar`).join(' / ')
}

function normalizeControlResult(result?: string | null) {
  const normalized = String(result || '').trim().toLowerCase()
  if (['accepted', 'running', 'success', 'failed', 'timeout', 'rejected'].includes(normalized)) {
    return normalized
  }
  return 'failed'
}

function resolveLogTitle(log: DeviceControlLog) {
  if (log.action === 'start') return '启用设备'
  if (log.action === 'stop') return '停用设备'
  if (log.action === 'manual_switch' && log.reason?.includes('控制模式切换')) return '控制模式切换'
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

function resolveLogStatusText(log: DeviceControlLog) {
  const normalized = normalizeControlResult(log.result)
  if (normalized === 'accepted') return '已入队'
  if (normalized === 'running') return '设备执行中'
  if (normalized === 'success') return '已处理'
  if (normalized === 'timeout') return '设备回执超时'
  if (normalized === 'rejected') return '设备拒绝执行'
  return '执行失败'
}

function resolveLogStatusTone(log: DeviceControlLog): 'success' | 'warning' | 'danger' | 'info' {
  const normalized = normalizeControlResult(log.result)
  if (normalized === 'success') return 'success'
  if (normalized === 'accepted' || normalized === 'running') return 'warning'
  if (normalized === 'timeout' || normalized === 'failed' || normalized === 'rejected') return 'danger'
  return 'info'
}

function roleSummaryText(isAdmin: boolean, canManageDevices: boolean) {
  if (isAdmin) return '管理员，可发起受控写入'
  if (canManageDevices) return '可查看档案，不可写入'
  return '仅查看'
}

export function buildControlConsoleOverviewItems(input: {
  archive?: MonitorOverview['archive'] | null
  runtimeStatus?: MonitorOverview['runtime_status'] | null
  profileSourceStatus?: CompensationCapacitorBankControlProfile['source_status']
}) {
  return [
    { label: '设备名称', value: input.archive?.name || '--' },
    { label: '设备编码', value: input.archive?.sn || '--' },
    { label: '在线状态', value: input.runtimeStatus?.is_online ? '在线' : '离线' },
    { label: '最近通讯时间', value: formatDateTime(input.runtimeStatus?.last_message_at) },
    { label: '参数回读状态', value: sourceStatusText(input.profileSourceStatus) },
    { label: '当前告警摘要', value: `${input.runtimeStatus?.unresolved_alarm_count ?? 0} 条未处理` },
  ] satisfies ControlConsoleOverviewItem[]
}

export function buildControlConsoleActionCards(input: {
  deviceActive: boolean
  canToggleRemotely: boolean
  canRunRemoteAction: boolean
  currentControlModeLabel: string
  disabledReason?: string
  remoteCommands?: CompensationCapacitorBankControlCapabilities['remote_commands']
}) {
  const remoteCommand = (action: string) => input.remoteCommands?.find((item) => item.action === action)
  const isRemoteCommandEnabled = (action: string) => {
    const capability = remoteCommand(action)
    return input.canRunRemoteAction && (capability ? capability.supported !== false : true)
  }
  const remoteDisabledReason = (action: string) => {
    const capability = remoteCommand(action)
    if (capability?.supported === false) return capability.disabled_reason || input.disabledReason
    return input.disabledReason
  }

  return [
    {
      key: 'toggle_device',
      title: '启停 / 使能',
      iconKey: 'switch',
      actionLabel: input.deviceActive ? '停用设备' : '启用设备',
      enabled: input.canToggleRemotely,
      disabledReason: input.canToggleRemotely ? undefined : input.disabledReason,
    },
    {
      key: 'reset_alarm',
      title: '报警复位',
      iconKey: 'refresh',
      actionLabel: '立即复位',
      enabled: isRemoteCommandEnabled('reset_alarm'),
      disabledReason: isRemoteCommandEnabled('reset_alarm') ? undefined : remoteDisabledReason('reset_alarm'),
    },
    {
      key: 'switch_control_mode',
      title: '控制模式切换',
      iconKey: 'setting',
      actionLabel: `切到${input.currentControlModeLabel === '手动' ? '自动' : '手动'}`,
      enabled: isRemoteCommandEnabled('switch_control_mode'),
      disabledReason: isRemoteCommandEnabled('switch_control_mode') ? undefined : remoteDisabledReason('switch_control_mode'),
    },
  ] satisfies ControlConsoleActionCard[]
}

export function buildControlConsoleReadonlySummaryView(input: {
  profile?: CompensationCapacitorBankControlProfile | null
}) {
  const profile = input.profile
  const summaryItems = capacitorBankControlParameterMeta
    .filter((item) => item.summary)
    .map((item) => ({
      label: item.label,
      value: formatCapacitorBankControlValue(profile, item),
    }))

  const capacityExpansionItems = profile ? [
    { label: 'A相分补', value: formatCapacitySlotList(profile.phase_a_capacity_steps_kvar || profile.split_capacity_expansion?.phase_a_groups) },
    { label: 'B相分补', value: formatCapacitySlotList(profile.phase_b_capacity_steps_kvar || profile.split_capacity_expansion?.phase_b_groups) },
    { label: 'C相分补', value: formatCapacitySlotList(profile.phase_c_capacity_steps_kvar || profile.split_capacity_expansion?.phase_c_groups) },
    { label: '公补 1-8', value: formatCapacitySlotList(profile.common_1_capacity_steps_kvar || profile.common_capacity_expansion?.common_1_groups) },
    { label: '公补 9-16', value: formatCapacitySlotList(profile.common_2_capacity_steps_kvar || profile.common_capacity_expansion?.common_2_groups) },
    { label: '公补 17-24', value: formatCapacitySlotList(profile.common_3_capacity_steps_kvar || profile.common_capacity_expansion?.common_3_groups) },
  ] : []

  const groups = new Map<string, CapacitorBankControlParameterMeta[]>()
  for (const item of capacitorBankControlParameterMeta) {
    const existing = groups.get(item.group)
    if (existing) {
      existing.push(item)
    } else {
      groups.set(item.group, [item])
    }
  }

  const groupedParameters: ControlConsoleParameterGroup[] = []
  for (const key of readonlyParameterGroupOrder) {
    const items = groups.get(key)
    if (!items?.length) continue
    groupedParameters.push({
      key,
      label: capacitorBankControlGroupLabels[key as keyof typeof capacitorBankControlGroupLabels],
      items: items.map((item) => ({
        key: String(item.key),
        label: item.label,
        description: item.description,
        currentValue: formatCapacitorBankControlValue(profile, item),
        register: item.register,
        readWrite: item.readWrite,
      })),
    })
  }

  return {
    summaryItems,
    capacityExpansionItems,
    groupedParameters,
    sourceStatusText: sourceStatusText(profile?.source_status),
    sourceStatusTone: sourceStatusTone(profile?.source_status),
    sourceMeta: `来源：${profile?.source || '未上报'} · 快照：${formatDateTime(profile?.snapshot_timestamp || profile?.updated_at)}`,
  } satisfies ControlConsoleReadonlySummaryView
}

export function buildControlConsoleReadonlySectionView(input: {
  summaryView: ControlConsoleReadonlySummaryView
}) {
  return {
    title: '只读参数快照',
    sectionLabel: '只读参数',
    tone: 'readonly',
    tags: [
      {
        text: input.summaryView.sourceStatusText,
        tone: input.summaryView.sourceStatusTone,
      },
    ],
    metaText: input.summaryView.sourceMeta,
    showCapacityExpansion: input.summaryView.capacityExpansionItems.length > 0,
  } satisfies ControlConsoleReadonlySectionView
}

export function buildControlConsoleWriteSectionView(input: {
  canWriteParameters: boolean
  capabilities?: CompensationCapacitorBankControlCapabilities | null
  isAdmin: boolean
  canManageDevices: boolean
  writeDisabledReason?: string
  writeRiskNotice?: string
}) {
  return {
    title: '参数修改',
    sectionLabel: '参数修改',
    tone: 'writable',
    description: '当前仅开放真实网关 UAT 已确认编码的低风险参数，提交前仍需二次确认；设备端结果仍需等待回读或回执核对。',
    tags: [
      {
        text: input.canWriteParameters ? '当前允许写入' : '当前禁止写入',
        tone: input.canWriteParameters ? 'success' : 'warning',
      },
      {
        text: input.capabilities?.supports_write ? '支持参数写入' : '参数写入待开通',
        tone: input.capabilities?.supports_write ? 'success' : 'info',
      },
    ],
    writeStatusText: input.canWriteParameters ? '当前允许写入' : '当前禁止写入',
    writeStatusTone: input.canWriteParameters ? 'success' : 'warning',
    capabilityStatusText: input.capabilities?.supports_write ? '支持参数写入' : '参数写入待开通',
    capabilityStatusTone: input.capabilities?.supports_write ? 'success' : 'info',
    roleSummaryText: roleSummaryText(input.isAdmin, input.canManageDevices),
    alert: input.writeDisabledReason
      ? {
          title: '写入入口已锁定',
          message: input.writeDisabledReason,
          tone: 'warning',
        }
      : input.writeRiskNotice
        ? {
            title: '写入前确认',
            message: input.writeRiskNotice,
            tone: 'warning',
          }
        : null,
  } satisfies ControlConsoleWriteSectionView
}

export function buildControlConsoleLogView(input: {
  logs: DeviceControlLog[]
}) {
  const latestLog = input.logs[0] || null
  const latestTimeoutLog = input.logs.find((item) => normalizeControlResult(item.result) === 'timeout') || null
  const entries = input.logs.map((log) => ({
    id: log.id,
    title: resolveLogTitle(log),
    statusText: resolveLogStatusText(log),
    statusTone: resolveLogStatusTone(log),
    createdAtText: formatDateTime(log.created_at),
    operatorText: log.operator || '未知操作人',
    reason: log.reason || undefined,
    sourceText: log.command_source || 'api',
  }))

  return {
    latestLogText: latestLog
      ? `${resolveLogStatusText(latestLog)} · ${formatDateTime(latestLog.created_at)}`
      : '暂无记录',
    latestLogStatusTone: latestLog ? resolveLogStatusTone(latestLog) : null,
    latestLogStatusLabel: latestLog ? resolveLogTitle(latestLog) : '',
    latestTimeoutAlertText: latestTimeoutLog
      ? `${resolveLogTitle(latestTimeoutLog)} 在 ${formatDateTime(latestTimeoutLog.created_at)} 发起后未在约定时间内收到回执，请结合现场状态复核。`
      : null,
    entries,
  } satisfies ControlConsoleLogView
}
