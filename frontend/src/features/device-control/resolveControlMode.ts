import type { CompensationCapacitorBankControlProfile } from '@/api/compensation'
import type { CompensationMonitorControlMode, DeviceControlLog } from '@/api/deviceMonitor'

function normalizeResult(result?: string | null) {
  const normalized = String(result || '').trim().toLowerCase()
  if (['accepted', 'running', 'success', 'failed', 'timeout', 'rejected'].includes(normalized)) {
    return normalized
  }
  return 'failed'
}

function resolveFromProfile(profile?: CompensationCapacitorBankControlProfile | null) {
  const scheme = profile?.terminal_assignment_scheme?.trim() || ''
  if (scheme.includes('手动')) return '手动'
  if (scheme.includes('自动')) return '自动'
  return ''
}

export function resolveControlModeFromLog(log?: DeviceControlLog | null) {
  if (!log) return ''
  if (normalizeResult(log.result) !== 'success') return ''
  if (log.action !== 'switch_control_mode' && log.action !== 'manual_switch') return ''
  if (!log.reason?.includes('控制模式切换')) return ''
  if (log.reason.includes('手动模式')) return '手动'
  if (log.reason.includes('自动模式')) return '自动'
  return ''
}

export function resolveControlModeLabel(
  profile?: CompensationCapacitorBankControlProfile | null,
  controlLogs: DeviceControlLog[] = [],
  monitorControlMode?: CompensationMonitorControlMode | null,
) {
  const latestLogMode = [...controlLogs]
    .sort((a, b) => {
      const timeDiff = Date.parse(b.created_at || '') - Date.parse(a.created_at || '')
      if (Number.isFinite(timeDiff) && timeDiff !== 0) return timeDiff
      return Number(b.id || 0) - Number(a.id || 0)
    })
    .map((log) => resolveControlModeFromLog(log))
    .find(Boolean)
  if (latestLogMode) return latestLogMode

  if (monitorControlMode?.state === 'live') {
    if (monitorControlMode.value === '手动' || monitorControlMode.value === '自动') {
      return monitorControlMode.value
    }
  }

  const profileMode = resolveFromProfile(profile)
  if (profileMode) return profileMode

  return '自动'
}
