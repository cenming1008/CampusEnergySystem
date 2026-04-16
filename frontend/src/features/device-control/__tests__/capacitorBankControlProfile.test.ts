import { describe, expect, it } from 'vitest'
import {
  capacitorBankEditableParameterMeta,
  formatCapacitorBankControlValue,
  getCapacitorBankControlEditableValue,
  getCapacitorBankControlParameterMeta,
} from '../capacitorBankControlProfile'

const baseProfile = {
  device_id: 16,
  source_status: 'fresh' as const,
  is_stale: false,
  split_capacity_expansion: {
    phase_a_groups: [],
    phase_b_groups: [],
    phase_c_groups: [],
  },
  common_capacity_expansion: {
    common_1_groups: [],
    common_2_groups: [],
    common_3_groups: [],
  },
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
}

describe('capacitorBankControlProfile helpers', () => {
  it('exposes the full protocol write range to the control console', () => {
    expect(capacitorBankEditableParameterMeta.map((item) => item.key)).toEqual([
      'switch_on_power_factor',
      'switch_off_power_factor',
      'switch_on_delay_seconds',
      'switch_off_delay_seconds',
      'common_output_circuit_count',
      'split_output_circuit_count',
      'common_capacity_code',
      'split_capacity_code',
      'common_step_capacity_kvar',
      'split_step_capacity_kvar',
      'ct_primary_current',
      'overvoltage_threshold',
      'voltage_harmonic_threshold',
      'current_harmonic_threshold',
      'temperature_upper_limit',
      'alarm_drive_event',
      'baud_rate',
      'terminal_assignment_scheme',
      'current_polarity_identification_enabled',
    ])
  })

  it('converts stored power factor snapshots to editable decimal values', () => {
    const meta = getCapacitorBankControlParameterMeta('switch_on_power_factor')
    expect(meta).toBeTruthy()
    expect(getCapacitorBankControlEditableValue({
      ...baseProfile,
      switch_on_power_factor: 95,
    }, meta!)).toBe(0.95)
  })

  it('formats boolean control values for read-only display', () => {
    const meta = getCapacitorBankControlParameterMeta('current_polarity_identification_enabled')
    expect(meta).toBeTruthy()
    expect(formatCapacitorBankControlValue({
      ...baseProfile,
      current_polarity_identification_enabled: true,
    }, meta!)).toBe('开启')
  })
})
