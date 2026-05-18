import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import ControlConsoleWritableParamsPanel from '../ControlConsoleWritableParamsPanel.vue'
import type { ControlConsoleWriteSectionView } from '@/features/device-control/viewMapping'
import type { CapacitorBankControlParameterMeta } from '@/features/device-control/capacitorBankControlProfile'

const SectionStub = defineComponent({
  props: {
    title: { type: String, default: '' },
    description: { type: String, default: '' },
  },
  template: `
    <section class="section-stub">
      <h3>{{ title }}</h3>
      <p v-if="description">{{ description }}</p>
      <slot name="alert" />
      <slot />
    </section>
  `,
})

const writeSectionView: ControlConsoleWriteSectionView = {
  title: '参数修改',
  sectionLabel: '参数修改',
  tone: 'writable',
  description: '当前仅开放真实网关 UAT 已确认编码的低风险参数，提交前仍需二次确认；设备端结果仍需等待回读或回执核对。',
  tags: [
    { text: '当前禁止写入', tone: 'warning' },
    { text: '支持参数写入', tone: 'success' },
  ],
  writeStatusText: '当前禁止写入',
  writeStatusTone: 'warning',
  capabilityStatusText: '支持参数写入',
  capabilityStatusTone: 'success',
  roleSummaryText: '管理员，可发起受控写入',
  alert: {
    title: '写入入口已锁定',
    message: '当前设备离线，暂不开放参数写入。',
    tone: 'warning',
  },
}

const editableParameterCards: Array<CapacitorBankControlParameterMeta & { currentValue: string }> = [
  {
    key: 'switch_on_power_factor',
    label: '投入功率因数',
    currentValue: '0.98',
    description: '功率因数低于该值时，控制器进入投入判定。',
    group: 'strategy',
    register: '0xD2',
    readWrite: '读/写',
    summary: true,
    editable: true,
    unit: '',
  },
]

function mountPanel(canWriteParameters = false) {
  return mount(ControlConsoleWritableParamsPanel, {
    props: {
      writeSectionView,
      canWriteParameters,
      editableParameterCards,
    },
    global: {
      stubs: {
        ControlConsoleParameterSection: SectionStub,
      },
    },
  })
}

describe('ControlConsoleWritableParamsPanel', () => {
  it('renders a compact write status and parameter rows without long explanatory blocks', async () => {
    const wrapper = mountPanel(false)

    expect(wrapper.find('.write-status-strip').text()).toContain('当前禁止写入')
    expect(wrapper.find('.write-status-strip').text()).toContain('当前设备离线，暂不开放参数写入。')
    expect(wrapper.findAll('.editable-row')).toHaveLength(1)
    expect(wrapper.text()).toContain('投入功率因数')
    expect(wrapper.text()).toContain('0.98')
    expect(wrapper.text()).toContain('当前不可写入')
    expect(wrapper.text()).not.toContain('参数修改')
    expect(wrapper.text()).not.toContain('当前仅开放真实网关 UAT')
    expect(wrapper.text()).not.toContain('写入入口已锁定')

    const emitSpy = vi.spyOn(wrapper.vm, '$emit')
    await wrapper.get('.editable-row').trigger('click')
    expect(emitSpy).not.toHaveBeenCalled()
  })
})
