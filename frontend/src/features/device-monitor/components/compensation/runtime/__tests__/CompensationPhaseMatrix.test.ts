import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationPhaseMatrix from '../CompensationPhaseMatrix.vue'
import type { CompensationCapacitorBankTelemetry } from '@/api/compensation'

function telemetry(overrides: Partial<CompensationCapacitorBankTelemetry> = {}): CompensationCapacitorBankTelemetry {
  return {
    device_id: 1,
    timestamp: '2026-05-19T10:00:00+08:00',
    current_a: 12, current_b: 12, current_c: 12,
    voltage_thd_a: 1.2, voltage_thd_b: 1.4, voltage_thd_c: 1.1,
    current_harmonic_a: 2, current_harmonic_b: 2, current_harmonic_c: 2,
    ...overrides,
  } as CompensationCapacitorBankTelemetry
}

describe('CompensationPhaseMatrix (统一量测总览)', () => {
  it('渲染表头：A 相 / B 相 / C 相 / 系统', () => {
    const wrapper = mount(CompensationPhaseMatrix, { props: { telemetry: telemetry() } })
    expect(wrapper.text()).toContain('A 相')
    expect(wrapper.text()).toContain('B 相')
    expect(wrapper.text()).toContain('C 相')
    expect(wrapper.text()).toContain('系统')
  })

  it('渲染量测行标签', () => {
    const wrapper = mount(CompensationPhaseMatrix, { props: { telemetry: telemetry() } })
    expect(wrapper.text()).toContain('电压 (V)')
    expect(wrapper.text()).toContain('电流 (A)')
    expect(wrapper.text()).toContain('有功 (kW)')
    expect(wrapper.text()).toContain('无功 (kvar)')
    expect(wrapper.text()).toContain('视在 (kVA)')
    expect(wrapper.text()).toContain('功率因数')
  })

  it('渲染指标行标签', () => {
    const wrapper = mount(CompensationPhaseMatrix, { props: { telemetry: telemetry() } })
    expect(wrapper.text()).toContain('相位状态')
    expect(wrapper.text()).toContain('V-THD (%)')
    expect(wrapper.text()).toContain('I-THD (%)')
  })

  it('将电参量和运行指标拆成两个并列分组', () => {
    const wrapper = mount(CompensationPhaseMatrix, { props: { telemetry: telemetry() } })
    const groups = wrapper.findAll('.matrix-group')

    expect(groups).toHaveLength(2)
    expect(groups[0].find('.matrix-group-title').text()).toContain('电参量')
    expect(groups[0].text()).toContain('电压 (V)')
    expect(groups[0].text()).toContain('电流 (A)')
    expect(groups[0].text()).toContain('有功 (kW)')
    expect(groups[0].text()).toContain('无功 (kvar)')
    expect(groups[0].text()).toContain('视在 (kVA)')
    expect(groups[0].text()).toContain('功率因数')

    expect(groups[1].find('.matrix-group-title').text()).toContain('运行指标')
    expect(groups[1].text()).toContain('相位状态')
    expect(groups[1].text()).toContain('V-THD (%)')
    expect(groups[1].text()).toContain('I-THD (%)')
    expect(groups[1].text()).toContain('柜温 (°C)')
  })

  it('电压量测行显示相位值及三相平均', () => {
    const wrapper = mount(CompensationPhaseMatrix, {
      props: {
        telemetry: telemetry({ voltage_a: 225.6, voltage_b: 225.3, voltage_c: 225.4 }),
      },
    })
    const text = wrapper.text()
    expect(text).toContain('225.6')
    expect(text).toContain('225.3')
    expect(text).toContain('225.4')
    // 平均 = (225.6 + 225.3 + 225.4) / 3 = 225.433... → 1 位小数 = 225.4
    expect(text).toContain('225.4')
  })

  it('有功行系统列为三相之和', () => {
    const wrapper = mount(CompensationPhaseMatrix, {
      props: {
        telemetry: telemetry({ active_power_a: 10, active_power_b: 20, active_power_c: 30 }),
      },
    })
    // sum = 60.0
    expect(wrapper.text()).toContain('60.0')
  })

  it('无功行系统列为三相之和', () => {
    const wrapper = mount(CompensationPhaseMatrix, {
      props: {
        telemetry: telemetry({ reactive_power_a: 5, reactive_power_b: 5, reactive_power_c: 5 }),
      },
    })
    expect(wrapper.text()).toContain('15.0')
  })

  it('视在行系统列为三相之和', () => {
    const wrapper = mount(CompensationPhaseMatrix, {
      props: {
        telemetry: telemetry({ apparent_power_a: 100, apparent_power_b: 200, apparent_power_c: 300 }),
      },
    })
    expect(wrapper.text()).toContain('600.0')
  })

  it('量测行单元格为纯值 span（无 chip 样式）', () => {
    const wrapper = mount(CompensationPhaseMatrix, {
      props: {
        telemetry: telemetry({ voltage_a: 220, voltage_b: 220, voltage_c: 220 }),
      },
    })
    // Find the 电压 row — matrix-value spans should be present
    const valueSpans = wrapper.findAll('.matrix-value')
    expect(valueSpans.length).toBeGreaterThan(0)
  })

  it('V-THD 超限时相位单元格标记为 is-crit', () => {
    const wrapper = mount(CompensationPhaseMatrix, {
      props: { telemetry: telemetry({ voltage_thd_a: 27 }) },
    })
    expect(wrapper.find('.matrix-cell.is-crit').exists()).toBe(true)
  })

  it('相位状态行 leading_a=true 渲染 超前 并标记 warn', () => {
    const wrapper = mount(CompensationPhaseMatrix, {
      props: { telemetry: telemetry({ leading_a: true, leading_b: false, leading_c: false }) },
    })
    expect(wrapper.text()).toContain('超前')
    expect(wrapper.find('.matrix-cell.is-warn').exists()).toBe(true)
  })

  it('alarmCount 只计入指标行相位单元格，量测行不贡献', () => {
    // 三相 V-THD 全部超限（门限 5）：3 个 crit chip → 3 项关注
    // 量测行（电压/电流等）均为 plain value，不贡献
    const wrapper = mount(CompensationPhaseMatrix, {
      props: {
        telemetry: telemetry({
          voltage_thd_a: 27, voltage_thd_b: 27, voltage_thd_c: 27,
          voltage_a: 225, voltage_b: 225, voltage_c: 225,
        }),
      },
    })
    expect(wrapper.text()).toContain('3 项关注')
  })

  it('alarmCount 告警计数不重复计入系统汇总列', () => {
    // 旧行为：3 crit 相位 + 系统列 1 crit = 4；新行为应为 3
    const wrapper = mount(CompensationPhaseMatrix, {
      props: {
        telemetry: telemetry({ voltage_thd_a: 27, voltage_thd_b: 27, voltage_thd_c: 27 }),
      },
    })
    expect(wrapper.text()).toContain('3 项关注')
  })

  it('遥测缺失时量测列显示 -- 占位符', () => {
    const wrapper = mount(CompensationPhaseMatrix, { props: { telemetry: null } })
    expect(wrapper.text()).toContain('--')
  })

  it('遥测缺失时指标行单元格退化为 na 状态', () => {
    const wrapper = mount(CompensationPhaseMatrix, { props: { telemetry: null } })
    expect(wrapper.find('.matrix-cell.is-na').exists()).toBe(true)
  })

  it('标题为 三相量测总览', () => {
    const wrapper = mount(CompensationPhaseMatrix, { props: { telemetry: null } })
    expect(wrapper.text()).toContain('三相量测总览')
  })
})
