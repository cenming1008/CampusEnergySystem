import { describe, expect, it, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import CompensationDiagnosticsCollapsible from '../CompensationDiagnosticsCollapsible.vue'

const diagnostics = {
  template_key: 'capacitor_bank_controller',
  display_name: '电容补偿控制器',
  overall_status: 'passed',
  metric_coverage: { live: 6, total: 6, missing: 0, missing_keys: [] },
  trend_coverage: { drawable_keys: [], unsupported_keys: [] },
  panel_coverage: { specific_panels: [] },
  ingestion_health: { ingestion_status: 'online' },
} as any

const stubs = {
  'el-icon': { template: '<i><slot /></i>' },
  DeviceTemplateDiagnosticsPanel: { template: '<div class="diag-panel-stub" />' },
}

describe('CompensationDiagnosticsCollapsible', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('默认折叠：显示摘要、隐藏完整诊断面板', () => {
    const wrapper = mount(CompensationDiagnosticsCollapsible, {
      props: { diagnostics },
      global: { stubs },
    })
    expect(wrapper.text()).toContain('接入诊断')
    expect(wrapper.text()).toContain('接入完整')
    expect(wrapper.text()).toContain('6/6')
    expect(wrapper.find('.diag-panel-stub').exists()).toBe(false)
  })

  it('点击折叠按钮后展开，显示完整诊断面板', async () => {
    const wrapper = mount(CompensationDiagnosticsCollapsible, {
      props: { diagnostics },
      global: { stubs },
    })
    await wrapper.find('button').trigger('click')
    expect(wrapper.find('.diag-panel-stub').exists()).toBe(true)
  })
})
