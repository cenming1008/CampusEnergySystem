import type { CompensationCapacitorBankRemoteCommandRequest } from '@/api/compensation'

export function buildControlModeRemoteCommand(
  currentModeLabel?: string | null,
): CompensationCapacitorBankRemoteCommandRequest {
  const normalized = `${currentModeLabel || ''}`.trim()
  const switchingToAuto = normalized.includes('手动')

  return {
    action: 'manual_switch',
    manual_mode: switchingToAuto ? 'auto' : 'manual',
    phase: 'COMMON',
    switch_action: 'none',
    reason: `控制台控制模式切换 -> ${switchingToAuto ? '自动模式' : '手动模式'}`,
  }
}
