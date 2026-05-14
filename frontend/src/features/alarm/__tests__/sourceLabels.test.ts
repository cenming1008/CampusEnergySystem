import { describe, expect, it } from 'vitest'

import { alarmSourceLabel } from '../sourceLabels'

describe('alarmSourceLabel', () => {
  it('maps stable alarm sources to user-facing labels', () => {
    expect(alarmSourceLabel('device_native')).toBe('设备原生')
    expect(alarmSourceLabel('platform_rule')).toBe('平台规则')
    expect(alarmSourceLabel('platform_comm')).toBe('平台通讯')
  })

  it('keeps unknown sources visible for compatibility', () => {
    expect(alarmSourceLabel('telemetry')).toBe('历史遥测')
    expect(alarmSourceLabel('legacy_source')).toBe('legacy_source')
    expect(alarmSourceLabel(null)).toBe('-')
  })
})
