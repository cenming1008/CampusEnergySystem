import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DeviceMatrix from '../DeviceMatrix.vue'
import AlertTrack from '../AlertTrack.vue'
import DashboardStatusBar from '../DashboardStatusBar.vue'

const { routerPushMock } = vi.hoisted(() => ({
  routerPushMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: routerPushMock,
  }),
}))

describe('dashboard interactions', () => {
  it('opens a device monitor when a concrete matrix item is clicked', async () => {
    routerPushMock.mockReset()
    const wrapper = mount(DeviceMatrix, {
      props: {
        groups: [{
          name: '电',
          color: 'var(--m-elec)',
          items: [{ deviceId: 12, n: '一号电表', s: 'on', v: '—', u: 'kW' }],
        }],
      },
    })

    await wrapper.find('.item').trigger('click')

    expect(routerPushMock).toHaveBeenCalledWith({ name: 'DeviceMonitor', params: { id: 12 } })
  })

  it('opens the filtered device list when an aggregate matrix item is clicked', async () => {
    routerPushMock.mockReset()
    const wrapper = mount(DeviceMatrix, {
      props: {
        groups: [{
          name: '水气',
          color: 'var(--m-water)',
          items: [{ category: 'water-gas', n: '水气设备', s: 'notice', v: '—', u: '' }],
        }],
      },
    })

    await wrapper.find('.item').trigger('click')

    expect(routerPushMock).toHaveBeenCalledWith({ path: '/devices', query: { category: 'water-gas' } })
  })

  it('opens alarm detail rows and emits ack without triggering row navigation', async () => {
    routerPushMock.mockReset()
    const wrapper = mount(AlertTrack, {
      props: {
        alerts: [{ id: 7, sev: 'warn', title: '冷站异常', time: '刚刚', ack: false }],
      },
    })

    await wrapper.find('.ack-btn').trigger('click')
    expect(wrapper.emitted('ack')).toEqual([[7]])
    expect(routerPushMock).not.toHaveBeenCalled()

    await wrapper.find('.row').trigger('click')
    expect(routerPushMock).toHaveBeenCalledWith({ path: '/alarms', query: { id: 7 } })
  })

  it('removes the version badge and marks demo data in the status bar', () => {
    const wrapper = mount(DashboardStatusBar, {
      props: {
        isMock: true,
        time: '12:30:00',
      },
    })

    expect(wrapper.text()).not.toContain('PARK · EMS · v4.2')
    expect(wrapper.text()).toContain('演示数据')
  })

  it('emits exitDemo when the demo mode action is clicked', async () => {
    const wrapper = mount(DashboardStatusBar, {
      props: {
        isMock: true,
        time: '12:30:00',
      },
    })

    await wrapper.get('.demo-exit').trigger('click')

    expect(wrapper.emitted('exitDemo')).toEqual([[]])
  })
})
