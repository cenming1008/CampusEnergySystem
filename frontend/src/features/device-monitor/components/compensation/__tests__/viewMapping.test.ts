import { describe, expect, it } from 'vitest'
import {
  buildCompensationBaseStatusItems,
  buildCompensationExtendedHint,
  buildCompensationHeaderView,
  buildCompensationModuleStatusView,
  buildCompensationOverviewMetrics,
  buildCompensationProfileItems,
  buildCapacitorBankControlSummaryView,
  buildCompensationSemanticView,
  buildCompensationStatusItems,
  buildCompensationTrendView,
  describeCompensationSource,
} from '../viewMapping'
import type { CompensationMonitor } from '@/api/deviceMonitor'

describe('compensation view mapping', () => {
  it('prefers backend svg circuit summary over profile module count fallback', () => {
    const monitor: CompensationMonitor = {
      subtype: 'svg',
      control_mode: {
        value: '自动',
        source: 'telemetry',
        state: 'live',
      },
      circuit_summary: {
        running_count: 6,
        total_count: 12,
        has_realtime_state: true,
        source: 'telemetry',
        state: 'live',
      },
      profile_status: null,
      key_metrics: {
        capacity_utilization: {
          value: 50,
          source: 'telemetry',
          state: 'live',
        },
        cabinet_temperature: {
          value: 36.5,
          source: 'telemetry',
          state: 'live',
        },
        compensation_level: {
          value: 6,
          source: 'telemetry',
          state: 'live',
        },
      },
      capabilities_summary: {
        supports_read: true,
        supports_write: false,
        supports_remote_control: false,
      },
    }

    const view = buildCompensationSemanticView({
      subtype: 'svg',
      monitor,
      svgProfileModuleCount: 8,
      canControlDevices: true,
      isOnline: true,
    })

    expect(view.totalModuleCount).toBe(12)
    expect(view.runningModuleCount).toBe(6)
  })

  it('does not default target power factor when no profile value is available', () => {
    const view = buildCompensationSemanticView({
      subtype: 'capacitor_bank_controller',
      monitor: null,
      canControlDevices: true,
      isOnline: true,
    })

    expect(view.targetPowerFactor).toBeNull()
  })

  it('uses control profile target power factor when provided', () => {
    const view = buildCompensationSemanticView({
      subtype: 'capacitor_bank_controller',
      monitor: null,
      targetPowerFactor: 95,
      canControlDevices: true,
      isOnline: true,
    })

    expect(view.targetPowerFactor).toBe(0.95)
  })

  it('renders configured fallback source text for capacitor bank circuit summary', () => {
    expect(describeCompensationSource('circuit_summary', 'configured_fallback', 'capacitor_bank_controller'))
      .toBe('当前无回路回读，按配置总回路展示')
  })

  it('renders profile source text for capacitor bank semantic fields', () => {
    expect(describeCompensationSource('circuit_summary', 'profile', 'capacitor_bank_controller'))
      .toBe('参数快照回读')
    expect(describeCompensationSource('capacity_utilization', 'profile', 'capacitor_bank_controller'))
      .toBe('按参数快照回读换算')
    expect(describeCompensationSource('control_mode', 'profile', 'capacitor_bank_controller'))
      .toBe('参数回读')
  })

  it('falls back to svg telemetry control mode only when backend semantics are absent', () => {
    const view = buildCompensationSemanticView({
      subtype: 'svg',
      monitor: null,
      svgTelemetryAutoMode: false,
      canControlDevices: true,
      isOnline: true,
    })

    expect(view.controlMode).toBe('手动')
    expect(view.controlModeState).toBe('live')
  })

  it('builds stable base status items for capacitor bank pages', () => {
    const items = buildCompensationBaseStatusItems({
      isSvgDevice: false,
      subtypeLabel: '电容补偿控制器',
      deviceStatus: '运行中',
      isActive: true,
      isOnline: true,
      ingestionStatus: '采集中',
      ingestionTone: 'success',
      controlMode: '自动',
      controlModeSource: '参数回读',
      controlSource: 'EMS 自动策略',
      capacityUsageSource: '按投切回路回读换算',
      capacityUsageState: 'live',
      cabinetTemperature: 38.2,
      cabinetTemperatureSource: '实时采集',
      latestSampleText: '2026-04-22 17:30:00',
      canControlDevices: true,
      switchPermission: true,
      profileSourceStatus: 'fresh',
      runningModuleCount: 6,
      totalModuleCount: 24,
    })

    expect(items.some((item) => item.label === '平台启用状态' && item.value === '已启用')).toBe(true)
    expect(items.some((item) => item.label === '内部运行状态' && item.value === '运行中')).toBe(true)
    expect(items.some((item) => item.label === '在线状态')).toBe(false)
    expect(items.some((item) => item.label === '回路投入率来源' && item.value === '按投切回路回读换算')).toBe(true)
    expect(items.some((item) => item.label === '参数快照' && item.value === '最新参数')).toBe(true)
    expect(items.some((item) => item.label === '回路状态' && item.value === '6 / 24 回路投入')).toBe(true)
  })

  it('deduplicates offline status rows in capacitor bank base status items', () => {
    const items = buildCompensationBaseStatusItems({
      isSvgDevice: false,
      subtypeLabel: '电容补偿控制器',
      deviceStatus: '离线',
      isActive: true,
      isOnline: false,
      ingestionStatus: '离线',
      ingestionTone: 'danger',
      controlMode: '自动',
      controlModeSource: '参数回读',
      controlSource: 'EMS 自动策略',
      capacityUsageSource: '按投切回路回读换算',
      capacityUsageState: 'live',
      cabinetTemperature: 38.2,
      cabinetTemperatureSource: '实时采集',
      latestSampleText: '2026-04-22 17:30:00',
      canControlDevices: true,
      switchPermission: false,
      profileSourceStatus: 'fresh',
      runningModuleCount: 0,
      totalModuleCount: 24,
    })

    expect(items.some((item) => item.label === '内部运行状态')).toBe(false)
    expect(items.some((item) => item.label === '在线状态')).toBe(false)
    expect(items.filter((item) => item.value === '离线')).toHaveLength(1)
    expect(items.some((item) => item.label === '采集状态' && item.value === '离线')).toBe(true)
  })

  it('builds header tags from control mode and compensation status', () => {
    const header = buildCompensationHeaderView({
      title: '补偿器1',
      serial: 'CAP-001',
      location: '配电房',
      deviceStatus: '运行中',
      isOnline: true,
      controlMode: '自动',
      controlModeState: 'live',
      compensationStatusText: '正常补偿',
      compensationStatusTone: 'success',
    })

    expect(header.tags).toEqual([
      { label: '自动', tone: 'info' },
      { label: '正常补偿', tone: 'success' },
    ])
  })

  it('deduplicates compensation header status when it matches device status', () => {
    const header = buildCompensationHeaderView({
      title: '补偿器1',
      serial: 'CAP-001',
      location: '配电房',
      deviceStatus: '离线',
      isOnline: false,
      controlMode: '自动',
      controlModeState: 'live',
      compensationStatusText: '离线',
      compensationStatusTone: 'neutral',
    })

    expect(header.deviceStatus).toBe('离线')
    expect(header.tags).toEqual([
      { label: '自动', tone: 'info' },
    ])
  })

  it('builds overview metrics with formatted capacity usage and temperature tone', () => {
    const overview = buildCompensationOverviewMetrics({
      isSvgDevice: false,
      reactivePowerValue: '-28.0',
      reactivePowerHint: '实时采集值',
      reactivePowerMissing: false,
      powerFactorValue: '0.95',
      powerFactorHint: '目标 PF 0.98',
      powerFactorMissing: false,
      voltageValue: '389.0',
      voltageMissing: false,
      currentValue: '43.0',
      currentMissing: false,
      activePowerValue: '26.0',
      activePowerMissing: false,
      capacityUsageValue: 25,
      capacityUsageSource: '按投切回路回读换算',
      capacityUsageState: 'live',
      controlMode: '手动',
      controlModeSource: 'Win 端控制模式',
      controlModeState: 'live',
      cabinetTemperatureValue: '41.2',
      cabinetTemperature: 41.2,
      cabinetTemperatureSource: '实时采集',
      cabinetTemperatureHealthText: '温度告警',
      cabinetTemperatureHealthHint: '实时温度告警位',
      cabinetTemperatureHealthTone: 'danger',
    })

    expect(overview.metrics.find((item) => item.key === 'capacityUsage')?.value).toBe('25.0')
    expect(overview.metrics.find((item) => item.key === 'capacityUsage')?.label).toBe('回路投入率')
    expect(overview.metrics.find((item) => item.key === 'cabinetTemperature')?.tone).toBe('danger')
    expect(overview.metrics.find((item) => item.key === 'cabinetTemperature')?.hint).toContain('温度告警')
  })

  it('builds capacitor bank module status view from circuit summary', () => {
    const moduleStatus = buildCompensationModuleStatusView({
      subtype: 'capacitor_bank_controller',
      isSvgDevice: false,
      unitLabel: '回路',
      fallbackRunningModuleCount: 4,
      fallbackTotalModuleCount: 24,
      capacitorBankCircuitSummary: {
        totalCount: 12,
        runningCount: 5,
        hasRealtimeState: true,
      },
    })

    expect(moduleStatus.title).toBe('回路投切状态')
    expect(moduleStatus.runningModuleCount).toBe(5)
    expect(moduleStatus.totalModuleCount).toBe(12)
    expect(moduleStatus.moduleStates.filter((state) => state === 'running')).toHaveLength(5)
    expect(moduleStatus.hint).toContain('最新回路投切寄存器回读')
  })

  it('builds svg module status view with alarm and fault markers', () => {
    const moduleStatus = buildCompensationModuleStatusView({
      subtype: 'svg',
      isSvgDevice: true,
      unitLabel: '模块',
      fallbackRunningModuleCount: 2,
      fallbackTotalModuleCount: 4,
      svgTelemetry: {
        module_fault: true,
        overtemp_fault: true,
      },
    })

    expect(moduleStatus.title).toBe('模块运行状态')
    expect(moduleStatus.moduleStates).toEqual(['running', 'running', 'alarm', 'fault'])
  })

  it('builds extended hint from non-live semantic sources and capacitor bank extras', () => {
    const hint = buildCompensationExtendedHint({
      capacityUsageSource: '按额定容量估算',
      capacityUsageState: 'mock',
      controlModeSource: '参数回读',
      controlModeState: 'mock',
      cabinetTemperature: null,
      isSvgDevice: false,
    })

    expect(hint).toContain('容量利用率来源：按额定容量估算。')
    expect(hint).toContain('控制模式当前来源：参数回读。')
    expect(hint).toContain('柜内温度当前缺测')
    expect(hint).toContain('JKWF-LCD 专属快照与历史曲线')
  })

  it('builds svg-specific status items from svg telemetry', () => {
    const items = buildCompensationStatusItems({
      isSvgDevice: true,
      subtypeLabel: 'SVG',
      deviceStatus: '运行中',
      isActive: true,
      isOnline: true,
      ingestionStatus: '在线采集',
      ingestionTone: 'success',
      unresolvedAlarmCount: 2,
      controlMode: '自动',
      controlModeSource: 'Win 端控制模式',
      controlSource: 'EMS 自动策略',
      capacityUsageSource: '遥测回读',
      capacityUsageState: 'live',
      cabinetTemperature: 38.2,
      cabinetTemperatureSource: '实时采集',
      latestSampleText: '2026-04-22 17:30:00',
      canControlDevices: true,
      switchPermission: true,
      profileSourceStatus: 'fresh',
      svgTelemetry: {
        breaker_status: true,
        module_status: false,
        fan_status: true,
        run_status: true,
        stop_status: false,
        local_mode: false,
        comm_status: true,
        overtemp_fault: true,
        current_fault_code: 'E-01',
        current_alarm_code: 'A-02',
        cabinet_temp: 39.5,
        module_temp: 58.4,
        igbt_temp: 61.2,
        heatsink_temp: 45.3,
      },
    })

    expect(items.some((item) => item.label === '未处理告警' && item.value === '2 条')).toBe(true)
    expect(items.some((item) => item.label === '当前故障' && item.value.includes('过温'))).toBe(true)
    expect(items.some((item) => item.label === '故障代码' && item.value === 'E-01')).toBe(true)
  })

  it('builds capacitor-bank-specific status items from cap telemetry', () => {
    const items = buildCompensationStatusItems({
      isSvgDevice: false,
      subtypeLabel: '电容补偿控制器',
      deviceStatus: '运行中',
      isActive: true,
      isOnline: true,
      ingestionStatus: '在线采集',
      ingestionTone: 'success',
      unresolvedAlarmCount: 0,
      controlMode: '自动',
      controlModeSource: '参数回读',
      controlSource: 'EMS 自动策略',
      capacityUsageSource: '按投切回路回读换算',
      capacityUsageState: 'live',
      cabinetTemperature: 35.1,
      cabinetTemperatureSource: '实时采集',
      latestSampleText: '2026-04-22 17:30:00',
      canControlDevices: true,
      switchPermission: true,
      profileSourceStatus: 'fresh',
      runningModuleCount: 6,
      totalModuleCount: 24,
      capacitorBankTelemetry: {
        frequency: 49.98,
        temperature: 35.1,
        temp_alarm: true,
        leading_a: true,
        overvoltage_alarm_b: true,
      },
    })

    expect(items.some((item) => item.label === '频率 / 温度' && item.value.includes('49.98 Hz / 35.1'))).toBe(true)
    expect(items.some((item) => item.label === '当前标志' && item.value.includes('A超前'))).toBe(true)
    expect(items.some((item) => item.label === '回路状态' && item.value === '6 / 24 回路投入')).toBe(true)
  })

  it('builds profile items from base archive and svg profile fields', () => {
    const items = buildCompensationProfileItems({
      archive: {
        id: 1,
        name: '补偿器1',
        sn: 'CAP-001',
        device_type: 'svg',
        energy_type: 'electricity',
        location: '1#配电房',
        rated_capacity: 500,
        description: '用于功率因数优化',
      },
      categoryLabel: '补偿设备',
      subtypeLabel: 'SVG',
      svgProfile: {
        model_number: 'SVG-500',
        rated_voltage: 400,
        module_count: 10,
        software_version: 'v1.2.3',
        distribution_room: '1#配电房',
        asset_number: 'ASSET-001',
      },
    })

    expect(items[0]).toEqual({ label: '设备名称', value: '补偿器1' })
    expect(items.some((item) => item.label === '额定容量' && item.value === '500 kVar')).toBe(true)
    expect(items.some((item) => item.label === '产品型号' && item.value === 'SVG-500')).toBe(true)
    expect(items.some((item) => item.label === '模块数量' && item.value === '10 组')).toBe(true)
  })

  it('builds capacitor bank control summary view from profile snapshot', () => {
    const view = buildCapacitorBankControlSummaryView({
      profile: {
        device_id: 16,
        switch_on_power_factor: 95,
        switch_off_power_factor: 0.99,
        switch_on_delay_seconds: 10,
        switch_off_delay_seconds: null,
        overvoltage_threshold: 252.5,
        temperature_upper_limit: 65,
        source_status: 'fresh',
        is_stale: false,
        capabilities: {
          supports_read: true,
          supports_write: true,
          supports_remote_control: true,
          write_status_message: 'ok',
          remote_control_status_message: 'ok',
          protocol_version: 'v1',
          command_message_type: 'control',
          receipt_message_type: 'receipt',
          control_topic_template: 'campus/control/{device_id}',
          receipt_topic: 'campus/telemetry',
          receipt_timeout_seconds: 30,
          supported_results: ['accepted', 'success'],
        },
        phase_a_capacity_steps_kvar: [10, 20],
        common_capacity_expansion: {
          common_1_groups: [30, 40],
          common_2_groups: [],
          common_3_groups: [],
        },
        split_capacity_expansion: {
          phase_a_groups: [10, 20],
          phase_b_groups: [],
          phase_c_groups: [],
        },
      },
    })

    expect(view.summaryItems.some((item) => item.label === '投入功率因数' && item.value === '0.95')).toBe(true)
    expect(view.summaryItems.some((item) => item.label === '投入延时' && item.value === '10 秒')).toBe(true)
    expect(view.hasSummaryData).toBe(true)
    expect(view.capacityExpansionItems.some((item) => item.label === 'A相分补' && item.value === '10.0 kvar / 20.0 kvar')).toBe(true)
    expect(view.capacityExpansionItems.some((item) => item.label === '公补 1-8' && item.value === '30.0 kvar / 40.0 kvar')).toBe(true)
  })

  it('returns empty-like control summary state when no profile is available', () => {
    const view = buildCapacitorBankControlSummaryView({
      profile: null,
    })

    expect(view.hasSummaryData).toBe(false)
    expect(view.summaryItems.every((item) => item.value === '暂无参数')).toBe(true)
    expect(view.capacityExpansionItems).toEqual([])
  })

  it('builds effect trend view with real time axis and q/pf summaries', () => {
    const model = buildCompensationTrendView({
      subtype: 'svg',
      isSvgDevice: true,
      activeTab: 'effect',
      timeRange: [new Date('2026-04-22T17:00:00'), new Date('2026-04-22T18:00:00')],
      trendPoints: [
        { timestamp: '2026-04-22T17:10:00', reactive_power: -28.4, power_factor: 0.96 },
        { timestamp: '2026-04-22T17:20:00', reactive_power: -25.1, power_factor: 0.98 },
      ],
      realtime: {
        device_id: 1,
        reactive_power: -25.1,
        power_factor: 0.98,
      },
      archive: {
        id: 1,
        name: '补偿器1',
        sn: 'CAP-001',
        device_type: 'svg',
        rated_capacity: 500,
      },
      fallbackCompensation: {
        targetPowerFactor: 0.98,
      },
      svgTelemetryHistory: [],
      capacitorBankTelemetryHistory: [],
      svgTelemetry: null,
      capacitorBankTelemetry: null,
    })

    expect(model.xAxisType).toBe('time')
    expect(model.legend).toEqual(['无功功率 Q', '功率因数 PF'])
    expect(model.summary.some((item) => item.label === '当前 PF' && item.value === '0.98')).toBe(true)
    expect(model.empty).toBe(false)
  })

  it('prefers capacitor-bank dedicated history for effect trend when available', () => {
    const model = buildCompensationTrendView({
      subtype: 'capacitor_bank_controller',
      isSvgDevice: false,
      activeTab: 'effect',
      timeRange: [new Date('2026-04-22T20:00:00'), new Date('2026-04-22T21:00:00')],
      trendPoints: [
        { timestamp: '2026-04-22T20:55:00', reactive_power: 9, power_factor: 0.91 },
      ],
      realtime: {
        device_id: 16,
        reactive_power: 27,
        power_factor: 0.91,
      },
      archive: {
        id: 16,
        name: '补偿器1',
        sn: 'CAP-001',
        device_type: 'capacitor_bank_controller',
        rated_capacity: 500,
      },
      fallbackCompensation: {
        targetPowerFactor: 0.98,
      },
      svgTelemetryHistory: [],
      capacitorBankTelemetryHistory: [
        {
          device_id: 16,
          timestamp: '2026-04-22T20:10:00',
          reactive_power_a: 3,
          reactive_power_b: 4,
          reactive_power_c: 5,
          power_factor_a: 0.90,
          power_factor_b: 0.93,
          power_factor_c: 0.96,
        },
      ],
      svgTelemetry: null,
      capacitorBankTelemetry: {
        device_id: 16,
        timestamp: '2026-04-22T20:10:00',
      },
    })

    expect(model.series[0]?.data).toEqual([['2026-04-22T20:10:00', 12]])
    expect(model.series[1]?.data).toEqual([['2026-04-22T20:10:00', 0.93]])
    expect(model.hint).toContain('电容控制器专属历史')
    expect(model.empty).toBe(false)
  })

  it('splits capacitor-bank phase power trends into active, reactive, and power-factor views', () => {
    const baseInput = {
      subtype: 'capacitor_bank_controller' as const,
      isSvgDevice: false,
      timeRange: [new Date('2026-04-22T20:00:00'), new Date('2026-04-22T21:00:00')] as [Date, Date],
      trendPoints: [],
      realtime: {
        device_id: 16,
      },
      archive: {
        id: 16,
        name: '补偿器1',
        sn: 'CAP-001',
        device_type: 'capacitor_bank_controller',
      },
      fallbackCompensation: {
        targetPowerFactor: 0.98,
      },
      svgTelemetryHistory: [],
      capacitorBankTelemetryHistory: [
        {
          device_id: 16,
          timestamp: '2026-04-22T20:10:00',
          active_power_a: 11,
          active_power_b: 12,
          active_power_c: 13,
          reactive_power_a: 3,
          reactive_power_b: 4,
          reactive_power_c: 5,
          power_factor_a: 0.90,
          power_factor_b: 0.93,
          power_factor_c: 0.96,
        },
      ],
      svgTelemetry: null,
      capacitorBankTelemetry: {
        device_id: 16,
        timestamp: '2026-04-22T20:10:00',
        active_power_a: 11,
        active_power_b: 12,
        active_power_c: 13,
        reactive_power_a: 3,
        reactive_power_b: 4,
        reactive_power_c: 5,
        power_factor_a: 0.90,
        power_factor_b: 0.93,
        power_factor_c: 0.96,
      },
    }

    const active = buildCompensationTrendView({ ...baseInput, activeTab: 'phase_active_power' })
    const reactive = buildCompensationTrendView({ ...baseInput, activeTab: 'phase_reactive_power' })
    const pf = buildCompensationTrendView({ ...baseInput, activeTab: 'phase_power_factor' })

    expect(active.legend).toEqual(['A相有功', 'B相有功', 'C相有功'])
    expect(active.axes).toEqual([{ name: 'kW' }])
    expect(active.series[0]?.data).toEqual([['2026-04-22T20:10:00', 11]])

    expect(reactive.legend).toEqual(['A相无功', 'B相无功', 'C相无功'])
    expect(reactive.axes).toEqual([{ name: 'kvar' }])
    expect(reactive.series[2]?.data).toEqual([['2026-04-22T20:10:00', 5]])

    expect(pf.legend).toEqual(['A相PF', 'B相PF', 'C相PF'])
    expect(pf.axes).toEqual([{ name: 'PF', min: 0.8, max: 1 }])
    expect(pf.series[1]?.data).toEqual([['2026-04-22T20:10:00', 0.93]])
  })

  it('builds capacitor-bank switching trend with decoded bit counts', () => {
    const model = buildCompensationTrendView({
      subtype: 'capacitor_bank_controller',
      isSvgDevice: false,
      activeTab: 'switching',
      timeRange: [new Date('2026-04-22T17:00:00'), new Date('2026-04-22T18:00:00')],
      trendPoints: [],
      realtime: {
        device_id: 16,
      },
      archive: {
        id: 16,
        name: '补偿器1',
        sn: 'CAP-001',
        device_type: 'capacitor_bank_controller',
      },
      fallbackCompensation: {
        targetPowerFactor: 0.98,
      },
      svgTelemetryHistory: [],
      capacitorBankTelemetryHistory: [
        {
          device_id: 16,
          timestamp: '2026-04-22T17:10:00',
          circuit_state_phase_a: 3,
          circuit_state_common_1: 7,
        },
      ],
      svgTelemetry: null,
      capacitorBankTelemetry: {
        device_id: 16,
        timestamp: '2026-04-22T17:10:00',
        circuit_state_phase_a: 3,
        circuit_state_common_1: 7,
      },
    })

    expect(model.legend).toContain('A相投入路数')
    expect(model.series[0]?.data).toEqual([['2026-04-22T17:10:00', 2]])
    expect(model.series[3]?.data).toEqual([['2026-04-22T17:10:00', 3]])
    expect(model.empty).toBe(false)
  })

  it('uses a 45-55 Hz axis for capacitor-bank frequency trend', () => {
    const model = buildCompensationTrendView({
      subtype: 'capacitor_bank_controller',
      isSvgDevice: false,
      activeTab: 'health',
      timeRange: [new Date('2026-04-22T17:00:00'), new Date('2026-04-22T18:00:00')],
      trendPoints: [],
      realtime: {
        device_id: 16,
      },
      archive: {
        id: 16,
        name: '补偿器1',
        sn: 'CAP-001',
        device_type: 'capacitor_bank_controller',
      },
      fallbackCompensation: {
        targetPowerFactor: 0.98,
      },
      svgTelemetryHistory: [],
      capacitorBankTelemetryHistory: [
        {
          device_id: 16,
          timestamp: '2026-04-22T17:10:00',
          temperature: 35,
          frequency: 49.98,
        },
      ],
      svgTelemetry: null,
      capacitorBankTelemetry: {
        device_id: 16,
        timestamp: '2026-04-22T17:10:00',
        frequency: 49.98,
      },
    })

    expect(model.axes[1]).toMatchObject({ name: 'Hz', min: 45, max: 55, position: 'right' })
  })
})
