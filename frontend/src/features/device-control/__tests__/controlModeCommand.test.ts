import { describe, expect, it } from 'vitest'

import { buildControlModeRemoteCommand } from '../controlModeCommand'

describe('buildControlModeRemoteCommand', () => {
  it('builds a manual_switch payload for switching to manual mode', () => {
    expect(buildControlModeRemoteCommand('自动')).toEqual({
      action: 'manual_switch',
      manual_mode: 'manual',
      phase: 'COMMON',
      switch_action: 'none',
      reason: '控制台控制模式切换 -> 手动模式',
    })
  })

  it('builds a manual_switch payload for switching back to auto mode', () => {
    expect(buildControlModeRemoteCommand('手动')).toEqual({
      action: 'manual_switch',
      manual_mode: 'auto',
      phase: 'COMMON',
      switch_action: 'none',
      reason: '控制台控制模式切换 -> 自动模式',
    })
  })
})
