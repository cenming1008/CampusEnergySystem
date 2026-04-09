import { computed, watch, type ComputedRef } from 'vue'
import type { Device } from '@/api/device'
import type { EnergyStatistics } from '@/api/energy'
import { useECharts } from '@/shared/composables/useECharts'

interface TrendTooltipParam {
  axisValue: string
  value: number
  dataIndex: number
}

export function useDashboardCharts(options: {
  currentDevice: ComputedRef<Device | undefined>
  energyTrendData: { times: string[]; values: number[] }
  warningThreshold: ComputedRef<number>
  displayPower: ComputedRef<number>
  /** Override the value shown in the gauge (defaults to displayPower) */
  gaugeValue?: ComputedRef<number>
  /** Unit suffix shown in gauge detail, e.g. '%' */
  gaugeUnit?: string
  /** Upper bound of the gauge scale (defaults to 100) */
  gaugeMax?: number
  energyStats: Record<string, EnergyStatistics>
}) {
  const mainChart = useECharts()
  const gaugeChart = useECharts()
  const pieChart = useECharts()

  const _gaugeMax = options.gaugeMax ?? 100

  const renderGauge = async (value: number) => {
    await gaugeChart.setOptions({
      series: [{
        type: 'gauge',
        radius: '90%',
        startAngle: 220,
        endAngle: -40,
        min: 0,
        max: _gaugeMax,
        progress: {
          show: true,
          width: 12,
          roundCap: true,
          itemStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 1, y2: 0,
              colorStops: [
                { offset: 0, color: '#5eead4' },
                { offset: 1, color: '#7ab8ff' }
              ]
            }
          }
        },
        axisLine: {
          lineStyle: { width: 12, color: [[1, 'rgba(255,255,255,0.1)']] },
          roundCap: true
        },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        pointer: { show: false },
        title: { show: false },
        detail: {
          fontSize: 42,
          fontWeight: 'bold',
          fontFamily: 'DIN, Monaco, monospace',
          color: '#fff',
          offsetCenter: [0, '10%'],
          formatter: (currentValue: number) =>
            options.gaugeUnit
              ? `${currentValue.toFixed(0)}${options.gaugeUnit}`
              : currentValue.toFixed(1)
        },
        data: [{ value: Math.min(value, _gaugeMax) }]
      }]
    })
  }

  const renderMainChart = async () => {
    const { times, values } = options.energyTrendData
    const deviceName = options.currentDevice.value?.name || '设备'

    await mainChart.setOptions({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(0,0,0,0.8)',
        borderColor: '#5eead4',
        textStyle: { color: '#fff' },
        formatter: (params: TrendTooltipParam[]) => {
          const point = params[0]
          return `<div style="padding:5px">
            <div style="color:#8892b0">${point.axisValue}</div>
            <div style="color:#5eead4;font-size:16px;font-weight:bold">${point.value} kW</div>
            <div style="color:#7dd3fc;font-size:12px;margin-top:4px">预警阈值 ${options.warningThreshold.value.toFixed(1)} kW</div>
          </div>`
        }
      },
      grid: { left: 58, right: 24, top: 42, bottom: 42 },
      xAxis: {
        type: 'category',
        data: times.length ? times : ['--'],
        axisLine: { lineStyle: { color: '#1e3a5f' } },
        axisLabel: { color: '#8ba0bd', fontSize: 11, interval: 'auto' },
        splitLine: { show: false }
      },
      yAxis: {
        type: 'value',
        name: '负荷 (kW)',
        nameTextStyle: { color: '#8ba0bd', fontSize: 11, padding: [0, 0, 6, 0] },
        axisLine: { show: false },
        axisLabel: { color: '#8892b0', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
      },
      series: [
        {
          name: deviceName,
          type: 'line',
          data: values.length ? values : [0],
          smooth: true,
          showSymbol: true,
          symbolSize: (_value: number, params: { dataIndex: number }) => (params.dataIndex === values.length - 1 ? 8 : 0),
          lineStyle: { width: 2.5, color: '#5eead4' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(94,234,212,0.24)' },
                { offset: 1, color: 'rgba(94,234,212,0)' }
              ]
            }
          },
          markLine: {
            symbol: 'none',
            label: {
              color: '#f7b267',
              formatter: '预警阈值'
            },
            lineStyle: {
              color: '#f7b267',
              type: 'dashed',
              opacity: 0.8
            },
            data: [{ yAxis: options.warningThreshold.value }]
          },
          markPoint: {
            symbolSize: 44,
            label: {
              color: '#e5eefc',
              fontSize: 10
            },
            itemStyle: {
              color: '#16324f',
              borderColor: '#5eead4',
              borderWidth: 1
            },
            data: [
              { type: 'max', name: '峰值' },
              { type: 'min', name: '谷值' }
            ]
          }
        }
      ]
    }, { notMerge: true })
  }

  const renderPieChart = async () => {
    const data = [
      { value: options.energyStats.electricity?.total_consumption || 0, name: '电力', itemStyle: { color: '#5eead4' } },
      { value: options.energyStats.water?.total_consumption || 0, name: '水', itemStyle: { color: '#7ab8ff' } },
      { value: options.energyStats.gas?.total_consumption || 0, name: '燃气', itemStyle: { color: '#f7b267' } },
      { value: options.energyStats.heat?.total_consumption || 0, name: '热力', itemStyle: { color: '#fb7185' } },
      { value: options.energyStats.cooling?.total_consumption || 0, name: '冷气', itemStyle: { color: '#b794f6' } }
    ].filter((item) => item.value > 0)
    const total = data.reduce((sum, item) => sum + item.value, 0)
    const hasDistributionData = total > 0

    if (data.length === 0) {
      data.push({ value: 1, name: '暂无有效数据', itemStyle: { color: '#1e3a5f' } })
    }

    await pieChart.setOptions({
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(0,0,0,0.7)',
        borderColor: '#5eead4',
        formatter: '{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        right: 0,
        top: 'center',
        textStyle: { color: '#9fb0c7', fontSize: 11 },
        itemWidth: 12,
        itemHeight: 12,
        formatter: (name: string) => {
          const item = data.find((entry) => entry.name === name)
          if (!item || !hasDistributionData) return name
          const ratio = total > 0 ? (item.value / total) * 100 : 0
          return `${name}  ${ratio.toFixed(1)}%`
        }
      },
      graphic: !hasDistributionData
        ? {
            type: 'text',
            left: 'center',
            top: '46%',
            style: {
              text: '当前时段暂无有效数据\n请检查采集状态或切换时间范围',
              fill: '#7f8ea7',
              textAlign: 'center',
              lineHeight: 18,
              fontSize: 12
            }
          }
        : [
            {
              type: 'text',
              left: '35%',
              top: '43%',
              style: {
                text: '总能耗',
                fill: '#8ea2bc',
                textAlign: 'center',
                fontSize: 12
              }
            },
            {
              type: 'text',
              left: '35%',
              top: '50%',
              style: {
                text: total.toFixed(1),
                fill: '#f7fbff',
                textAlign: 'center',
                fontSize: 22,
                fontWeight: 700
              }
            },
            {
              type: 'text',
              left: '35%',
              top: '58%',
              style: {
                text: 'kWh',
                fill: '#8ea2bc',
                textAlign: 'center',
                fontSize: 11
              }
            }
          ],
      series: [{
        type: 'pie',
        radius: ['50%', '75%'],
        center: ['35%', '50%'],
        label: { show: false },
        itemStyle: { borderColor: '#0a1628', borderWidth: 2 },
        emphasis: {
          itemStyle: { shadowBlur: 12, shadowColor: 'rgba(0,242,254,0.22)' }
        },
        data
      }]
    })
  }

  const initCharts = async () => {
    await Promise.all([
      mainChart.initChart(),
      gaugeChart.initChart(),
      pieChart.initChart()
    ])

    await renderGauge(options.gaugeValue?.value ?? options.displayPower.value)
    await renderPieChart()
    await renderMainChart()
  }

  const trendChartSource = computed(() => ({
    deviceName: options.currentDevice.value?.name || '设备',
    threshold: options.warningThreshold.value,
    times: [...options.energyTrendData.times],
    values: [...options.energyTrendData.values]
  }))

  const pieChartSource = computed(() => [
    options.energyStats.electricity?.total_consumption || 0,
    options.energyStats.water?.total_consumption || 0,
    options.energyStats.gas?.total_consumption || 0,
    options.energyStats.heat?.total_consumption || 0,
    options.energyStats.cooling?.total_consumption || 0
  ])

  const _gaugeSource = computed(() => options.gaugeValue?.value ?? options.displayPower.value)
  watch(_gaugeSource, (value) => {
    void renderGauge(Math.abs(value))
  })

  watch(trendChartSource, () => {
    void renderMainChart()
  }, { deep: true })

  watch(pieChartSource, () => {
    void renderPieChart()
  }, { deep: true })

  return {
    gaugeChart,
    initCharts,
    mainChart,
    pieChart
  }
}
