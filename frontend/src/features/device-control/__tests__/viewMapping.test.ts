import { describe, expect, it } from 'vitest'
import {
  buildControlConsoleActionCards,
  buildControlConsoleLogView,
  buildControlConsoleOverviewItems,
  buildControlConsoleReadonlySectionView,
  buildControlConsoleReadonlySummaryView,
  buildControlConsoleWriteSectionView,
} from '../viewMapping'

const baseProfile = {
  device_id: 2,
  source_status: 'fresh' as const,
  is_stale: false,
  source: 'telemetry',
  snapshot_timestamp: '2026-04-22T18:10:00',
  updated_at: '2026-04-22T18:09:59',
  switch_on_power_factor: 92,
  switch_off_power_factor: 100,
  switch_on_delay_seconds: 10,
  switch_off_delay_seconds: 8,
  overvoltage_threshold: 245,
  temperature_upper_limit: 55,
  baud_rate: 9600,
  phase_a_capacity_steps_kvar: [5, 5, 10],
  phase_b_capacity_steps_kvar: [5, 5, 10],
  phase_c_capacity_steps_kvar: [10, 10],
  common_1_capacity_steps_kvar: [10, 10, 20],
  common_2_capacity_steps_kvar: [20, 20],
  common_3_capacity_steps_kvar: [30],
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
    control_topic_template: 'campus/control/{device_code}',
    receipt_topic: 'campus/telemetry',
    receipt_timeout_seconds: 120,
    supported_results: ['accepted', 'running', 'success', 'failed', 'timeout', 'rejected'],
  },
}

describe('device control view mapping', () => {
  it('builds overview items from archive, runtime and profile status', () => {
    expect(buildControlConsoleOverviewItems({
      archive: {
        id: 2,
        name: '设备-CAP-001',
        sn: 'CAP-001',
        device_type: 'capacitor_bank_controller',
      },
      runtimeStatus: {
        device_id: 2,
        code: 'running',
        label: '运行中',
        is_active: true,
        is_online: true,
        unresolved_alarm_count: 1,
        last_message_at: '2026-04-22T18:03:47',
      },
      profileSourceStatus: 'stale',
    })).toEqual([
      { label: '设备名称', value: '设备-CAP-001' },
      { label: '设备编码', value: 'CAP-001' },
      { label: '在线状态', value: '在线' },
      { label: '最近通讯时间', value: '2026-04-22 18:03:47' },
      { label: '参数回读状态', value: '参数可能过期' },
      { label: '当前告警摘要', value: '1 条未处理' },
    ])
  })

  it('builds remote action cards with correct enabled state and mode switch label', () => {
    expect(buildControlConsoleActionCards({
      deviceActive: true,
      canToggleRemotely: true,
      canRunRemoteAction: false,
      currentControlModeLabel: '手动',
    })).toEqual([
      {
        key: 'toggle_device',
        title: '启停 / 使能',
        iconKey: 'switch',
        actionLabel: '停用设备',
        enabled: true,
      },
      {
        key: 'reset_alarm',
        title: '报警复位',
        iconKey: 'refresh',
        actionLabel: '立即复位',
        enabled: false,
      },
      {
        key: 'switch_control_mode',
        title: '控制模式切换',
        iconKey: 'setting',
        actionLabel: '切到自动',
        enabled: false,
      },
    ])
  })

  it('builds readonly summary view for control profile snapshots', () => {
    const view = buildControlConsoleReadonlySummaryView({ profile: baseProfile })

    expect(view.sourceStatusText).toBe('最新参数')
    expect(view.sourceStatusTone).toBe('success')
    expect(view.sourceMeta).toContain('来源：telemetry')
    expect(view.summaryItems.map((item) => item.label)).toEqual([
      '投入功率因数',
      '切除功率因数',
      '投入延时',
      '切除延时',
      '过压保护门限',
      '温度上限门限',
      '通讯速率',
    ])
    expect(view.capacityExpansionItems).toContainEqual({
      label: 'A相分补',
      value: '5.0 kvar / 5.0 kvar / 10.0 kvar',
    })
    expect(view.groupedParameters[0]?.items[0]).toMatchObject({
      label: '投入功率因数',
      register: '0xD2',
      readWrite: '读/写',
    })
  })

  it('builds readonly section view from summary metadata', () => {
    const summaryView = buildControlConsoleReadonlySummaryView({ profile: baseProfile })
    const view = buildControlConsoleReadonlySectionView({ summaryView })

    expect(view).toMatchObject({
      title: '只读参数快照',
      sectionLabel: '只读参数',
      tone: 'readonly',
      metaText: summaryView.sourceMeta,
      showCapacityExpansion: true,
    })
    expect(view.tags).toContainEqual({
      text: '最新参数',
      tone: 'success',
    })
  })

  it('builds write section status texts from permissions and capabilities', () => {
    expect(buildControlConsoleWriteSectionView({
      canWriteParameters: false,
      capabilities: baseProfile.capabilities,
      isAdmin: false,
      canManageDevices: true,
      writeDisabledReason: '仅管理员可执行参数写入。',
    })).toEqual({
      title: '参数修改',
      sectionLabel: '参数修改',
      tone: 'writable',
      description: '当前已按协议范围开放全部可写参数，提交前仍需二次确认；设备端结果仍需等待回读或回执核对。',
      tags: [
        { text: '当前禁止写入', tone: 'warning' },
        { text: '支持参数写入', tone: 'success' },
      ],
      writeStatusText: '当前禁止写入',
      writeStatusTone: 'warning',
      capabilityStatusText: '支持参数写入',
      capabilityStatusTone: 'success',
      roleSummaryText: '可查看档案，不可写入',
      alert: {
        title: '写入入口已锁定',
        message: '仅管理员可执行参数写入。',
        tone: 'warning',
      },
    })
  })

  it('builds log view entries and timeout alert', () => {
    const view = buildControlConsoleLogView({
      logs: [
        {
          id: 10,
          device_id: 2,
          action: 'switch_control_mode',
          target_status: true,
          result: 'success',
          operator: 'admin',
          reason: '控制模式切换 -> 自动模式',
          command_source: 'mqtt',
          created_at: '2026-04-22T18:01:00',
        },
        {
          id: 11,
          device_id: 2,
          action: 'reset_alarm',
          target_status: true,
          result: 'timeout',
          operator: 'admin',
          reason: '控制台报警复位',
          command_source: 'api',
          created_at: '2026-04-22T18:02:00',
        },
      ],
    })

    expect(view.latestLogStatusLabel).toBe('控制模式切换')
    expect(view.latestLogText).toBe('执行成功 · 2026-04-22 18:01:00')
    expect(view.latestTimeoutAlertText).toContain('报警复位 在 2026-04-22 18:02:00')
    expect(view.entries[1]).toMatchObject({
      title: '报警复位',
      statusText: '设备回执超时',
      statusTone: 'danger',
      sourceText: 'api',
    })
  })
})
