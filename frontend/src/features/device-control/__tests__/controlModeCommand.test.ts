import { describe, expect, it } from 'vitest'

import { buildControlModeRemoteCommand } from '../controlModeCommand'

describe('buildControlModeRemoteCommand', () => {
  it('builds a switch_control_mode payload for switching to manual mode', () => {
    expect(buildControlModeRemoteCommand('自动')).toEqual({
      action: 'switch_control_mode',
      reason: '控制台控制模式切换 -> 手动模式',
    })
  })

  it('builds a switch_control_mode payload for switching back to auto mode', () => {
    expect(buildControlModeRemoteCommand('手动')).toEqual({
      action: 'switch_control_mode',
      reason: '控制台控制模式切换 -> 自动模式',
    })
  })
})
