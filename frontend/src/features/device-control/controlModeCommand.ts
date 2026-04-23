import type { CompensationCapacitorBankRemoteCommandRequest } from '@/api/compensation'

export function buildControlModeRemoteCommand(
  currentModeLabel?: string | null,
): CompensationCapacitorBankRemoteCommandRequest {
  const normalized = `${currentModeLabel || ''}`.trim()
  const switchingToAuto = normalized.includes('手动')

  return {
    action: 'switch_control_mode',
    reason: `控制台控制模式切换 -> ${switchingToAuto ? '自动模式' : '手动模式'}`,
  }
}
