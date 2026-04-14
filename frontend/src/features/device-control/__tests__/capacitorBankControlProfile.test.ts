import { describe, expect, it } from 'vitest'
import {
  capacitorBankEditableParameterMeta,
  formatCapacitorBankControlValue,
  getCapacitorBankControlEditableValue,
  getCapacitorBankControlParameterMeta,
} from '../capacitorBankControlProfile'

describe('capacitorBankControlProfile helpers', () => {
  it('only exposes the controlled low-risk editable parameters', () => {
    expect(capacitorBankEditableParameterMeta.map((item) => item.key)).toEqual([
      'switch_on_power_factor',
      'switch_off_power_factor',
      'switch_on_delay_seconds',
      'switch_off_delay_seconds',
      'overvoltage_threshold',
      'temperature_upper_limit',
    ])
  })

  it('converts stored power factor snapshots to editable decimal values', () => {
    const meta = getCapacitorBankControlParameterMeta('switch_on_power_factor')
    expect(meta).toBeTruthy()
    expect(getCapacitorBankControlEditableValue({
      device_id: 16,
      source_status: 'fresh',
      is_stale: false,
      capabilities: {
        supports_read: true,
        supports_write: true,
        supports_remote_control: true,
        write_status_message: '',
        remote_control_status_message: '',
        protocol_version: 'campus-control.v1',
        command_message_type: 'control_command',
        receipt_message_type: 'control_receipt',
        control_topic_template: 'campus/control/{device_id}',
        receipt_topic: 'campus/telemetry',
        receipt_timeout_seconds: 120,
        supported_results: ['accepted', 'running', 'success', 'failed', 'timeout', 'rejected'],
      },
      switch_on_power_factor: 95,
    }, meta!)).toBe(0.95)
  })

  it('formats boolean control values for read-only display', () => {
    const meta = getCapacitorBankControlParameterMeta('current_polarity_identification_enabled')
    expect(meta).toBeTruthy()
    expect(formatCapacitorBankControlValue({
      device_id: 16,
      source_status: 'fresh',
      is_stale: false,
      capabilities: {
        supports_read: true,
        supports_write: true,
        supports_remote_control: true,
        write_status_message: '',
        remote_control_status_message: '',
        protocol_version: 'campus-control.v1',
        command_message_type: 'control_command',
        receipt_message_type: 'control_receipt',
        control_topic_template: 'campus/control/{device_id}',
        receipt_topic: 'campus/telemetry',
        receipt_timeout_seconds: 120,
        supported_results: ['accepted', 'running', 'success', 'failed', 'timeout', 'rejected'],
      },
      current_polarity_identification_enabled: true,
    }, meta!)).toBe('开启')
  })
})
