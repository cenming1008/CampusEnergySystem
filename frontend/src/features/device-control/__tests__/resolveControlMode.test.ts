import { describe, expect, it } from 'vitest'

import { resolveControlModeFromLog, resolveControlModeLabel } from '../resolveControlMode'

describe('resolveControlModeLabel', () => {
  it('prefers live monitor mode over stale profile or control logs', () => {
    expect(resolveControlModeLabel({
      device_id: 16,
      terminal_assignment_scheme: '自动模式',
      source_status: 'fresh',
      is_stale: false,
      split_capacity_expansion: { phase_a_groups: [], phase_b_groups: [], phase_c_groups: [] },
      common_capacity_expansion: { common_1_groups: [], common_2_groups: [], common_3_groups: [] },
      capabilities: {
        supports_read: true,
        supports_write: true,
        supports_remote_control: true,
        write_status_message: '',
        remote_control_status_message: '',
        protocol_version: 'campus-control.v1',
        command_message_type: 'control_command',
        receipt_message_type: 'control_receipt',
        control_topic_template: 'campus/control/{device_code}',
        receipt_topic: 'campus/telemetry',
        receipt_timeout_seconds: 120,
        supported_results: ['accepted', 'running', 'success'],
      },
    }, [], {
      value: '手动',
      source: 'telemetry',
      state: 'live',
    })).toBe('手动')
  })

  it('prefers control profile when terminal assignment already shows manual mode', () => {
    expect(resolveControlModeLabel({
      device_id: 16,
      terminal_assignment_scheme: '手动模式',
      source_status: 'fresh',
      is_stale: false,
      split_capacity_expansion: { phase_a_groups: [], phase_b_groups: [], phase_c_groups: [] },
      common_capacity_expansion: { common_1_groups: [], common_2_groups: [], common_3_groups: [] },
      capabilities: {
        supports_read: true,
        supports_write: true,
        supports_remote_control: true,
        write_status_message: '',
        remote_control_status_message: '',
        protocol_version: 'campus-control.v1',
        command_message_type: 'control_command',
        receipt_message_type: 'control_receipt',
        control_topic_template: 'campus/control/{device_code}',
        receipt_topic: 'campus/telemetry',
        receipt_timeout_seconds: 120,
        supported_results: ['accepted', 'running', 'success'],
      },
    }, [])).toBe('手动')
  })

  it('falls back to the latest successful control-mode switch log when profile is still generic', () => {
    expect(resolveControlModeLabel({
      device_id: 16,
      terminal_assignment_scheme: '方案1',
      source_status: 'fresh',
      is_stale: false,
      split_capacity_expansion: { phase_a_groups: [], phase_b_groups: [], phase_c_groups: [] },
      common_capacity_expansion: { common_1_groups: [], common_2_groups: [], common_3_groups: [] },
      capabilities: {
        supports_read: true,
        supports_write: true,
        supports_remote_control: true,
        write_status_message: '',
        remote_control_status_message: '',
        protocol_version: 'campus-control.v1',
        command_message_type: 'control_command',
        receipt_message_type: 'control_receipt',
        control_topic_template: 'campus/control/{device_code}',
        receipt_topic: 'campus/telemetry',
        receipt_timeout_seconds: 120,
        supported_results: ['accepted', 'running', 'success'],
      },
    }, [
      {
        id: 1,
        device_id: 16,
        action: 'manual_switch',
        target_status: true,
        created_at: '2026-04-22T11:13:19',
        result: 'success',
        reason: '控制台控制模式切换 -> 手动模式 | 设备回执成功: 已按协议手动投切: COMMON 相 保持',
      },
    ])).toBe('手动')
  })

  it('treats numeric terminal scheme values as non-display mode fields', () => {
    expect(resolveControlModeLabel({
      device_id: 16,
      terminal_assignment_scheme: '0',
      source_status: 'fresh',
      is_stale: false,
      split_capacity_expansion: { phase_a_groups: [], phase_b_groups: [], phase_c_groups: [] },
      common_capacity_expansion: { common_1_groups: [], common_2_groups: [], common_3_groups: [] },
      capabilities: {
        supports_read: true,
        supports_write: true,
        supports_remote_control: true,
        write_status_message: '',
        remote_control_status_message: '',
        protocol_version: 'campus-control.v1',
        command_message_type: 'control_command',
        receipt_message_type: 'control_receipt',
        control_topic_template: 'campus/control/{device_code}',
        receipt_topic: 'campus/telemetry',
        receipt_timeout_seconds: 120,
        supported_results: ['accepted', 'running', 'success'],
      },
    }, [
      {
        id: 1,
        device_id: 16,
        action: 'manual_switch',
        target_status: true,
        created_at: '2026-04-22T11:13:19',
        result: 'success',
        reason: '控制台控制模式切换 -> 自动模式 | 设备回执成功: 已切回自动模式',
      },
    ])).toBe('自动')
  })

  it('does not trust accepted-only logs as current mode', () => {
    expect(resolveControlModeLabel(null, [
      {
        id: 1,
        device_id: 16,
        action: 'manual_switch',
        target_status: true,
        created_at: '2026-04-22T11:13:19',
        result: 'accepted',
        reason: '控制台控制模式切换 -> 手动模式',
      },
    ])).toBe('自动')
  })

  it('ignores successful logs unrelated to control-mode switching', () => {
    expect(resolveControlModeFromLog({
      id: 1,
      device_id: 16,
      action: 'reset_alarm',
      target_status: true,
      created_at: '2026-04-22T11:13:19',
      result: 'success',
      reason: '控制台报警复位',
    })).toBe('')
  })
})
