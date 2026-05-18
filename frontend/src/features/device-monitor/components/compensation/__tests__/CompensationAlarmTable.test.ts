import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import type { DeviceAlarmRecord } from '@/api/deviceMonitor'
import CompensationAlarmTable from '../CompensationAlarmTable.vue'

function makeAlarm(id: number): DeviceAlarmRecord {
  return {
    id,
    device_id: 1,
    message: `告警 ${id}`,
    severity: id % 2 === 0 ? 'warning' : 'info',
    source: 'device_native',
    timestamp: '2026-05-18T08:00:00+08:00',
    is_resolved: false,
  }
}

function mountTable(rows: DeviceAlarmRecord[]) {
  return mount(CompensationAlarmTable, {
    props: { rows },
    global: {
      stubs: {
        'el-select': {
          props: ['modelValue', 'placeholder'],
          emits: ['update:modelValue', 'change'],
          methods: {
            handleChange(event: Event) {
              const rawValue = (event.target as HTMLSelectElement).value
              const numericValue = Number(rawValue)
              this.$emit('update:modelValue', Number.isNaN(numericValue) ? rawValue : numericValue)
              this.$emit('change')
            },
          },
          template: `
            <select
              :aria-label="placeholder"
              :value="modelValue"
              @change="handleChange"
            >
              <slot />
            </select>
          `,
        },
        'el-segmented': {
          props: ['modelValue', 'options', 'ariaLabel'],
          emits: ['update:modelValue', 'change'],
          template: `
            <div :aria-label="ariaLabel">
              <button
                v-for="option in options"
                :key="option"
                class="page-size-option"
                type="button"
                @click="$emit('update:modelValue', option); $emit('change')"
              >
                {{ option }}
              </button>
            </div>
          `,
        },
        'el-option': {
          props: ['label', 'value'],
          template: '<option :value="value">{{ label }}</option>',
        },
        'el-table': {
          props: ['data'],
          template: `
            <div>
              <div v-for="row in data" :key="row.id" class="alarm-row">
                {{ row.message }}
                <slot :row="row" />
              </div>
            </div>
          `,
        },
        'el-table-column': {
          name: 'ElTableColumn',
          props: ['label', 'prop', 'width', 'minWidth', 'align'],
          template: '<div class="table-column-probe" :data-label="label" />',
        },
        'el-tag': { template: '<span><slot /></span>' },
        'el-button': { template: '<button><slot /></button>' },
        'el-pagination': {
          props: ['pageSize', 'total'],
          template: '<div class="pagination-probe">{{ pageSize }}/{{ total }}</div>',
        },
      },
    },
  })
}

describe('CompensationAlarmTable', () => {
  it('defaults to 50 alarms per page and allows switching to 10 or 100 rows from the header selector', async () => {
    const wrapper = mountTable(Array.from({ length: 55 }, (_, index) => makeAlarm(index + 1)))

    expect(wrapper.findAll('.alarm-row')).toHaveLength(50)
    expect(wrapper.find('.pagination-probe').text()).toBe('50/55')

    await wrapper.findAll('.page-size-option').find((button) => button.text() === '10')?.trigger('click')
    expect(wrapper.findAll('.alarm-row')).toHaveLength(10)
    expect(wrapper.find('.pagination-probe').text()).toBe('10/55')

    await wrapper.findAll('.page-size-option').find((button) => button.text() === '100')?.trigger('click')
    expect(wrapper.findAll('.alarm-row')).toHaveLength(55)
    expect(wrapper.find('.pagination-probe').exists()).toBe(false)
  })

  it('renders redesigned severity pills with semantic tone classes', () => {
    const wrapper = mountTable([
      { ...makeAlarm(1), severity: 'critical' },
      { ...makeAlarm(2), severity: 'warning' },
      { ...makeAlarm(3), severity: 'info' },
    ])
    const vm = wrapper.vm as unknown as {
      severityLabel: (severity?: string) => string
      severityToneClass: (severity?: string) => string
    }

    expect(vm.severityLabel('critical')).toBe('紧急')
    expect(vm.severityLabel('warning')).toBe('警告')
    expect(vm.severityLabel('info')).toBe('信息')
    expect(vm.severityToneClass('critical')).toBe('severity-pill--critical')
    expect(vm.severityToneClass('warning')).toBe('severity-pill--warning')
    expect(vm.severityToneClass('info')).toBe('severity-pill--info')
  })

  it('maps operation states to compact action styling', () => {
    const wrapper = mountTable([makeAlarm(1)])
    const vm = wrapper.vm as unknown as {
      actionLabel: (row: DeviceAlarmRecord) => string
      actionToneClass: (row: DeviceAlarmRecord) => string
    }

    expect(vm.actionLabel(makeAlarm(1))).toBe('处理')
    expect(vm.actionToneClass(makeAlarm(1))).toBe('alarm-action-pill--pending')
    expect(vm.actionLabel({ ...makeAlarm(2), is_resolved: true })).toBe('已处理')
    expect(vm.actionToneClass({ ...makeAlarm(2), is_resolved: true })).toBe('alarm-action-pill--resolved')
  })

  it('omits source and status columns from the alarm records table', () => {
    const wrapper = mountTable([makeAlarm(1)])
    const columns = wrapper.findAllComponents({ name: 'ElTableColumn' })
    const labels = columns.map(column => column.props('label'))

    expect(labels).toContain('级别')
    expect(labels).toContain('操作')
    expect(labels).not.toContain('来源')
    expect(labels).not.toContain('状态')
  })
})
