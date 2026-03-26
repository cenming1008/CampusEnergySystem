import { nextTick, onUnmounted, ref, shallowRef } from 'vue'
import { echarts, type ECharts, type EChartsCoreOption, type SetOptionOpts } from '@/shared/lib/echarts'

interface UseEChartsOptions {
  autoResize?: boolean
}

export function useECharts(options: UseEChartsOptions = {}) {
  const { autoResize = true } = options

  const chartRef = ref<HTMLElement | null>(null)
  const chart = shallowRef<ECharts | null>(null)
  let resizeTimer: ReturnType<typeof setTimeout> | null = null

  const initChart = async () => {
    await nextTick()

    if (!chartRef.value) return null

    chart.value?.dispose()
    chart.value = echarts.init(chartRef.value)

    return chart.value
  }

  const ensureChart = async () => {
    if (chart.value) return chart.value
    return initChart()
  }

  const setOptions = async (option: EChartsCoreOption, opts?: SetOptionOpts) => {
    const instance = await ensureChart()
    if (!instance) return

    instance.setOption(option, opts)
  }

  const resize = () => {
    if (!chart.value) return

    if (resizeTimer) {
      clearTimeout(resizeTimer)
    }

    resizeTimer = setTimeout(() => {
      chart.value?.resize()
    }, 100)
  }

  const dispose = () => {
    if (resizeTimer) {
      clearTimeout(resizeTimer)
      resizeTimer = null
    }

    chart.value?.dispose()
    chart.value = null
  }

  const handleWindowResize = () => {
    resize()
  }

  if (autoResize && typeof window !== 'undefined') {
    window.addEventListener('resize', handleWindowResize)
  }

  onUnmounted(() => {
    if (autoResize && typeof window !== 'undefined') {
      window.removeEventListener('resize', handleWindowResize)
    }

    dispose()
  })

  return {
    chart,
    chartRef,
    initChart,
    setOptions,
    resize,
    dispose
  }
}
