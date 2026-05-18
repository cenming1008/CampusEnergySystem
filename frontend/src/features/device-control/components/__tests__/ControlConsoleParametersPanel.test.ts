import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ControlConsoleParametersPanel from '../ControlConsoleParametersPanel.vue'
import type {
  ControlConsoleReadonlySectionView,
  ControlConsoleReadonlySummaryView,
  ControlConsoleWriteSectionView,
} from '@/features/device-control/viewMapping'
import type { CapacitorBankControlParameterMeta } from '@/features/device-control/capacitorBankControlProfile'

const sectionView: ControlConsoleReadonlySectionView = {
  title: '只读参数快照',
  sectionLabel: '只读参数',
  tone: 'readonly',
  tags: [{ text: '最新参数', tone: 'success' }],
  metaText: '来源：telemetry · 快照：2026-05-18 16:31:38',
  showCapacityExpansion: true,
}

const readonlySummaryView: ControlConsoleReadonlySummaryView = {
  sourceStatusText: '最新参数',
  sourceStatusTone: 'success',
  sourceMeta: '来源：telemetry · 快照：2026-05-18 16:31:38',
  summaryItems: [{ label: '投入功率因数', value: '0.90' }],
  capacityExpansionItems: [
    { label: 'A相分补', value: '12.0 kvar / 12.0 kvar' },
    { label: '公补 1-8', value: '30.0 kvar / 60.0 kvar' },
  ],
  groupedParameters: [
    {
      key: 'strategy',
      label: '投切策略',
      items: [
        { key: 'switch_on_power_factor', label: '投入功率因数', description: '投入判定。', currentValue: '0.90', register: '0xD2', readWrite: '读/写' },
      ],
    },
    {
      key: 'circuits',
      label: '回路配置',
      items: [
        { key: 'common_output_circuit_count', label: '共补输出回路', description: '共补路数。', currentValue: '12', register: '0xD6', readWrite: '读/写' },
      ],
    },
    {
      key: 'protection',
      label: '保护门限',
      items: [
        { key: 'overvoltage_threshold', label: '过压保护门限', description: '过压门限。', currentValue: '250 V', register: '0xDD', readWrite: '读/写' },
      ],
    },
    {
      key: 'device',
      label: '通讯参数',
      items: [
        { key: 'baud_rate', label: '通讯速率', description: '波特率。', currentValue: '9600 bps', register: '0xE2', readWrite: '读/写' },
      ],
    },
  ],
}

function buildWriteSectionView(
  overrides: Partial<ControlConsoleWriteSectionView> = {},
): ControlConsoleWriteSectionView {
  return {
    title: '参数修改',
    sectionLabel: '参数修改',
    tone: 'writable',
    description: '提交前需二次确认。',
    tags: [],
    writeStatusText: '当前禁止写入',
    writeStatusTone: 'warning',
    capabilityStatusText: '支持参数写入',
    capabilityStatusTone: 'success',
    roleSummaryText: '管理员，可发起受控写入',
    alert: { title: '写入入口已锁定', message: '当前设备离线，暂不开放参数写入。', tone: 'warning' },
    ...overrides,
  }
}

const editableParameterCards: Array<CapacitorBankControlParameterMeta & { currentValue: string }> = [
  { key: 'switch_on_power_factor', group: 'strategy', label: '投入功率因数', register: '0xD2', readWrite: '读/写', description: '投入判定。', editable: true, currentValue: '0.90' },
  { key: 'overvoltage_threshold', group: 'protection', label: '过压保护门限', register: '0xDD', readWrite: '读/写', description: '过压门限。', editable: true, currentValue: '250 V' },
]

function mountPanel(
  options: { canWriteParameters?: boolean; writeSectionView?: ControlConsoleWriteSectionView } = {},
) {
  return mount(ControlConsoleParametersPanel, {
    props: {
      sectionView,
      readonlySummaryView,
      writeSectionView: options.writeSectionView ?? buildWriteSectionView(),
      canWriteParameters: options.canWriteParameters ?? false,
      editableParameterCards,
    },
  })
}

describe('ControlConsoleParametersPanel', () => {
  it('renders a unified header with snapshot and write status', () => {
    const wrapper = mountPanel()
    const header = wrapper.get('[data-test="params-header"]')
    expect(header.text()).toContain('最新参数')
    expect(header.text()).toContain('来源：telemetry · 快照：2026-05-18 16:31:38')
    expect(header.text()).toContain('当前禁止写入')
    expect(header.text()).toContain('管理员，可发起受控写入')
    expect(wrapper.get('[data-test="params-alert"]').text()).toContain('当前设备离线，暂不开放参数写入。')
  })

  it('does not render the legacy duplicated summary cards', () => {
    const wrapper = mountPanel()
    expect(wrapper.find('.readonly-summary-card').exists()).toBe(false)
  })

  it('renders all four parameter groups as sectioned tables', () => {
    const wrapper = mountPanel()
    expect(wrapper.findAll('[data-test="param-group-card"]')).toHaveLength(4)
    expect(wrapper.text()).toContain('投切策略')
    expect(wrapper.text()).toContain('回路配置')
    expect(wrapper.text()).toContain('保护门限')
    expect(wrapper.text()).toContain('通讯参数')
    expect(wrapper.text()).toContain('投入功率因数')
    expect(wrapper.text()).toContain('250 V')
  })

  it('shows an edit button for writable params and a pending marker otherwise', () => {
    const wrapper = mountPanel()
    expect(wrapper.findAll('[data-test="param-edit-button"]')).toHaveLength(2)
    expect(wrapper.findAll('[data-test="param-write-pending"]')).toHaveLength(2)
  })

  it('disables the edit button and emits nothing when writing is locked', async () => {
    const wrapper = mountPanel({ canWriteParameters: false })
    const button = wrapper.get('[data-test="param-edit-button"]')
    expect((button.element as HTMLButtonElement).disabled).toBe(true)
    await button.trigger('click')
    expect(wrapper.emitted('open-write-dialog')).toBeUndefined()
  })

  it('emits open-write-dialog with the parameter key when writing is allowed', async () => {
    const wrapper = mountPanel({
      canWriteParameters: true,
      writeSectionView: buildWriteSectionView({
        writeStatusText: '当前允许写入',
        writeStatusTone: 'success',
        alert: null,
      }),
    })
    const button = wrapper.get('[data-test="param-edit-button"]')
    expect((button.element as HTMLButtonElement).disabled).toBe(false)
    await button.trigger('click')
    expect(wrapper.emitted('open-write-dialog')?.[0]).toEqual(['switch_on_power_factor'])
    expect(wrapper.find('[data-test="params-alert"]').exists()).toBe(false)
  })

  it('renders capacity expansion split into phase rows and a common grid, toggleable', async () => {
    const wrapper = mountPanel()
    const slots = wrapper.findAll('[data-test="capacity-slot"]')
    expect(slots).toHaveLength(4)
    expect(slots[0].text()).toContain('A1')
    expect(slots[0].text()).toContain('12.0 kvar')
    expect(slots[2].text()).toContain('1路')
    expect(slots[2].text()).toContain('30.0 kvar')
    await wrapper.get('[data-test="toggle-capacity"]').trigger('click')
    expect(wrapper.findAll('[data-test="capacity-slot"]')).toHaveLength(0)
  })
})
