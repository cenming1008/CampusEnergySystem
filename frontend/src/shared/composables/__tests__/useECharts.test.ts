import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { defineComponent, nextTick } from 'vue'
import { mount } from '@vue/test-utils'

const { initMock, resizeMock, disposeMock, setOptionMock } = vi.hoisted(() => ({
  initMock: vi.fn(),
  resizeMock: vi.fn(),
  disposeMock: vi.fn(),
  setOptionMock: vi.fn(),
}))

vi.mock('@/shared/lib/echarts', () => ({
  echarts: {
    init: initMock,
  },
}))

import { useECharts } from '../useECharts'

describe('useECharts', () => {
  let resizeObserverCallback: ResizeObserverCallback | null
  let observeMock: ReturnType<typeof vi.fn>
  let disconnectMock: ReturnType<typeof vi.fn>
  const originalResizeObserver = globalThis.ResizeObserver

  beforeEach(() => {
    vi.useFakeTimers()
    initMock.mockReset()
    resizeMock.mockReset()
    disposeMock.mockReset()
    setOptionMock.mockReset()
    resizeObserverCallback = null
    observeMock = vi.fn()
    disconnectMock = vi.fn()
    initMock.mockReturnValue({
      resize: resizeMock,
      dispose: disposeMock,
      setOption: setOptionMock,
    })

    globalThis.ResizeObserver = vi.fn(function MockResizeObserver(callback: ResizeObserverCallback) {
      resizeObserverCallback = callback
      return {
        observe: observeMock,
        disconnect: disconnectMock,
        unobserve: vi.fn(),
        takeRecords: vi.fn(() => []),
      }
    }) as unknown as typeof ResizeObserver
  })

  afterEach(() => {
    vi.useRealTimers()
    globalThis.ResizeObserver = originalResizeObserver
  })

  it('resizes the chart when the host element size changes without a window resize', async () => {
    const Harness = defineComponent({
      setup() {
        const chart = useECharts()
        return { chartRef: chart.chartRef, initChart: chart.initChart }
      },
      template: '<div ref="chartRef" />',
    })

    const wrapper = mount(Harness)
    await wrapper.vm.initChart()
    await nextTick()

    expect(observeMock).toHaveBeenCalledWith(wrapper.element)

    resizeObserverCallback?.([], {} as ResizeObserver)
    vi.advanceTimersByTime(100)

    expect(resizeMock).toHaveBeenCalledTimes(1)

    wrapper.unmount()
    expect(disconnectMock).toHaveBeenCalled()
  })
})
