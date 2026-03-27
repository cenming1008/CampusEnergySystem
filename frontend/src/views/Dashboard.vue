<script setup lang="ts">
import { onMounted, watch, computed, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import { useSocketStore } from '@/stores/useSocketStore'
import { useAuthStore } from '@/stores/useAuthStore'
import { useAlarmPolling } from '@/features/alarm/composables/useAlarmPolling'
import { useDashboardClock } from '@/features/dashboard/composables/useDashboardClock'
import { useDashboardDeviceSelection } from '@/features/dashboard/composables/useDashboardDeviceSelection'
import { useDashboardEnergyStats } from '@/features/dashboard/composables/useDashboardEnergyStats'
import { useDashboardRealtime } from '@/features/dashboard/composables/useDashboardRealtime'
import { useECharts } from '@/shared/composables/useECharts'
import { usePermissions } from '@/shared/composables/usePermissions'
import StatTile from '@/shared/ui/StatTile.vue'

interface TrendTooltipParam {
  axisValue: string
  value: number
  dataIndex: number
}

// --- 状态定义 ---
const socketStore = useSocketStore()
const authStore = useAuthStore()
const { latestMessage, isConnected } = storeToRefs(socketStore)
const { hasScopedAccess } = usePermissions()
const { alarmCount, alarmList } = useAlarmPolling({ interval: 10000 })
const { currentTime, currentDate } = useDashboardClock()
const { currentDevice, currentDeviceId, deviceList, selectableDevices, totalDevices, onlineDevices, loadDeviceList } = useDashboardDeviceSelection()
const { energyStats, todayEnergy, monthlyEnergy, loadEnergyStats } = useDashboardEnergyStats()
const {
  displayCurrent,
  displayEnergy,
  displayPower,
  energyTrendData,
  loading: realtimeLoading,
  realTimeData,
  loadDeviceData
} = useDashboardRealtime({
  currentDeviceId,
  deviceList,
  latestMessage
})

// 图表实例
const mainChart = useECharts()
const gaugeChart = useECharts()
const pieChart = useECharts()

// 系统概览
const overview = computed(() => ({
  totalDevices: totalDevices.value,
  onlineDevices: onlineDevices.value,
  alarmCount: alarmCount.value
}))

// 计算属性
const onlineRate = computed(() => {
  if (totalDevices.value === 0) return 0
  return Math.round((onlineDevices.value / totalDevices.value) * 100)
})

const overviewCards = computed(() => [
  {
    label: '园区设备',
    value: overview.value.totalDevices,
    caption: '已接入设备与表计',
    tone: 'cyan' as const
  },
  {
    label: '在线率',
    value: `${onlineRate.value}%`,
    caption: `${overview.value.onlineDevices} 台在线`,
    tone: 'green' as const
  },
  {
    label: '覆盖区域',
    value: regionRankings.value.length,
    caption: regionRankings.value.length ? '已形成区域能耗视图' : '待补充区域映射',
    tone: 'blue' as const
  },
  {
    label: '活动告警',
    value: overview.value.alarmCount,
    caption: overview.value.alarmCount ? '待处理异常需复核' : '当前无未处理告警',
    tone: 'red' as const
  }
])

const regionRankings = computed(() => {
  const regions = new Map<string, { score: number; total: number; online: number }>()

  for (const device of deviceList.value) {
    const region = device.location?.trim() || '未分区'
    const current = regions.get(region) || { score: 0, total: 0, online: 0 }
    const capacity = Number(device.rated_capacity || 0)

    current.total += 1
    if (device.is_active) current.online += 1
    current.score += capacity > 0 ? capacity : (device.is_active ? 1.2 : 0.6)
    regions.set(region, current)
  }

  return Array.from(regions.entries())
    .map(([name, stats], index) => ({
      name,
      rank: index + 1,
      score: stats.score,
      total: stats.total,
      online: stats.online,
      hasCapacity: stats.score >= stats.total
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)
    .map((item, index) => ({ ...item, rank: index + 1 }))
})

const trendValues = computed(() => energyTrendData.values.map(value => Math.abs(Number(value) || 0)))
const averageLoad = computed(() => {
  if (!trendValues.value.length) return 0
  return trendValues.value.reduce((sum, value) => sum + value, 0) / trendValues.value.length
})
const peakLoad = computed(() => trendValues.value.length ? Math.max(...trendValues.value) : 0)
const warningThreshold = computed(() => {
  const base = Math.max(peakLoad.value, Math.abs(displayPower.value))
  return Number((base > 0 ? base * 0.9 : 1).toFixed(1))
})
const trendCurrentValue = computed(() => trendValues.value.at(-1) || 0)
const hasEnergyDistributionData = computed(() => [
  energyStats.electricity?.total_consumption || 0,
  energyStats.water?.total_consumption || 0,
  energyStats.gas?.total_consumption || 0,
  energyStats.heat?.total_consumption || 0,
  energyStats.cooling?.total_consumption || 0,
].some(value => value > 0))

const shiftLabel = computed(() => {
  const hour = new Date().getHours()
  if (hour >= 8 && hour < 18) return '白天时段'
  if (hour >= 18 && hour < 23) return '晚间时段'
  return '夜间时段'
})

const runtimeTone = computed(() => isConnected.value ? 'green' as const : 'red' as const)
const dashboardScopeHint = computed(() => {
  if (!authStore.locationScope) {
    return '当前驾驶舱展示的是当前账号可访问的全部园区设备与能耗汇总。'
  }
  return `当前驾驶舱已按位置范围 ${authStore.locationScope} 过滤，统计结果不代表全部园区全量数据。`
})

const selectedDeviceSummary = computed(() => ({
  name: currentDevice.value?.name || '暂无设备',
  type: currentDevice.value?.device_type || '未选择',
  energyType: currentDevice.value?.energy_type || '未知',
  status: currentDevice.value?.is_active ? '在线运行' : '离线待机'
}))

const selectedDeviceLabel = computed(() => {
  if (!currentDevice.value) return '未选择设备'
  const location = currentDevice.value.location?.trim()
  return location ? `${currentDevice.value.name} · ${location}` : currentDevice.value.name
})

const selectableDeviceCount = computed(() => selectableDevices.value.length)
const selectedDeviceStatusTone = computed(() => currentDevice.value?.is_active ? 'online' : 'offline')

const focusMetrics = computed(() => [
  { label: '实时功率', value: `${displayPower.value.toFixed(1)} kW` },
  { label: '母线电压', value: `${realTimeData.voltage.toFixed(1)} V` },
  { label: 'A相电流', value: `${displayCurrent.value.toFixed(1)} A` },
  { label: '今日用电', value: `${displayEnergy.value.toFixed(1)} kWh` }
])

const selectDevice = (deviceId?: number) => {
  if (typeof deviceId !== 'number' || deviceId === currentDeviceId.value) return
  currentDeviceId.value = deviceId
}

const trendHighlights = computed(() => [
  { label: '当前值', value: `${trendCurrentValue.value.toFixed(1)} kW` },
  { label: '峰值', value: `${peakLoad.value.toFixed(1)} kW` },
  { label: '均值', value: `${averageLoad.value.toFixed(1)} kW` },
  { label: '阈值', value: `${warningThreshold.value.toFixed(1)} kW` }
])

const resolveAlarmLevel = (message: string) => {
  if (/中断|离线|断开|故障/.test(message)) {
    return { label: '严重', tone: 'critical', action: '立即排查通讯与设备状态' }
  }

  if (/异常|超限|过高|偏高|偏低/.test(message)) {
    return { label: '重要', tone: 'warning', action: '检查负荷阈值与现场参数' }
  }

  return { label: '提醒', tone: 'notice', action: '建议关注后续趋势变化' }
}

const formatAlarmTime = (timestamp: string) => {
  const diffMinutes = Math.max(0, Math.round((Date.now() - new Date(timestamp).getTime()) / 60000))
  if (diffMinutes < 1) return '刚刚'
  if (diffMinutes < 60) return `${diffMinutes} 分钟前`

  const diffHours = Math.round(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours} 小时前`
  return new Date(timestamp).toLocaleString('zh-CN', { hour12: false })
}

const latestAlarmItems = computed(() => (
  alarmList.value.slice(0, 4).map(alarm => {
    const level = resolveAlarmLevel(alarm.message)
    const deviceName = deviceList.value.find(device => device.id === alarm.device_id)?.name || `设备 ${alarm.device_id}`

    return {
      id: alarm.id,
      message: alarm.message,
      deviceName,
      time: formatAlarmTime(alarm.timestamp),
      ...level
    }
  })
))

const selectedDeviceAlarmItems = computed(() => {
  if (!currentDevice.value?.id) return latestAlarmItems.value.slice(0, 3)

  return alarmList.value
    .filter(alarm => alarm.device_id === currentDevice.value?.id)
    .slice(0, 3)
    .map(alarm => {
      const level = resolveAlarmLevel(alarm.message)
      return {
        id: alarm.id,
        message: alarm.message,
        deviceName: currentDevice.value?.name || `设备 ${alarm.device_id}`,
        time: formatAlarmTime(alarm.timestamp),
        ...level
      }
    })
})

const scadaStatusCards = computed(() => [
  {
    label: '今日总能耗',
    value: `${todayEnergy.value.toFixed(1)} kWh`,
    meta: '覆盖电/水/气/冷/热',
    tone: 'cyan'
  },
  {
    label: '本月总能耗',
    value: `${monthlyEnergy.value.toFixed(1)} kWh`,
    meta: '按自然月累计',
    tone: 'purple'
  },
  {
    label: '实时负荷',
    value: `${displayPower.value.toFixed(1)} kW`,
    meta: `峰值 ${peakLoad.value.toFixed(1)} kW`,
    tone: 'blue'
  },
  {
    label: '在线设备',
    value: `${onlineDevices.value}/${totalDevices.value || 0}`,
    meta: `在线率 ${onlineRate.value}%`,
    tone: 'green'
  },
  {
    label: '活动告警',
    value: String(alarmCount.value),
    meta: alarmCount.value ? '需要人工复核' : '当前稳定',
    tone: alarmCount.value ? 'red' : 'blue'
  },
  {
    label: '通讯状态',
    value: isConnected.value ? '正常' : '中断',
    meta: `当前时段 ${shiftLabel.value}`,
    tone: runtimeTone.value
  }
])

const selectedDeviceProfile = computed(() => [
  { label: '设备类型', value: selectedDeviceSummary.value.type },
  { label: '能源介质', value: selectedDeviceSummary.value.energyType },
  { label: '运行状态', value: selectedDeviceSummary.value.status },
  { label: '预警阈值', value: `${warningThreshold.value.toFixed(1)} kW` }
])

const deviceBoardItems = computed(() => selectableDevices.value.slice(0, 12))

// --- 初始化 ---
onMounted(async () => {
  socketStore.connect()
  
  // 等待 DOM 渲染完成
  await nextTick()
  
  // 初始化图表
  await initCharts()
  
  // 加载数据
  await loadDeviceList()
  await loadDeviceData()
  await loadEnergyStats()
})

const initCharts = async () => {
  await Promise.all([
    mainChart.initChart(),
    gaugeChart.initChart(),
    pieChart.initChart()
  ])

  await renderGauge(0)
  await renderPieChart()
  // 主图表会在 loadPowerTrend 后渲染
}

// --- 图表渲染 ---
const renderGauge = async (value: number) => {
  const option = {
    series: [{
      type: 'gauge',
      radius: '90%',
      startAngle: 220,
      endAngle: -40,
      min: 0,
      max: 100,
      progress: {
        show: true,
        width: 12,
        roundCap: true,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: '#00f2fe' },
              { offset: 1, color: '#4facfe' }
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
        formatter: (v: number) => v.toFixed(1)
      },
      data: [{ value: Math.min(value, 100) }]
    }]
  }
  await gaugeChart.setOptions(option)
}

const renderMainChart = async () => {
  const { times, values } = energyTrendData

  
  // 获取当前设备名称
  const deviceName = currentDevice.value?.name || '设备'
  
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0,0,0,0.8)',
      borderColor: '#00f2fe',
      textStyle: { color: '#fff' },
      formatter: (params: TrendTooltipParam[]) => {
        const p = params[0]
        return `<div style="padding:5px">
          <div style="color:#8892b0">${p.axisValue}</div>
          <div style="color:#00f2fe;font-size:16px;font-weight:bold">${p.value} kW</div>
          <div style="color:#7dd3fc;font-size:12px;margin-top:4px">预警阈值 ${warningThreshold.value.toFixed(1)} kW</div>
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
        symbolSize: (_value: number, params: { dataIndex: number }) => params.dataIndex === (values.length - 1) ? 8 : 0,
        lineStyle: { width: 2.5, color: '#00f2fe' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(0,242,254,0.28)' },
              { offset: 1, color: 'rgba(0,242,254,0)' }
            ]
          }
        },
        markLine: {
          symbol: 'none',
          label: {
            color: '#f59e0b',
            formatter: '预警阈值'
          },
          lineStyle: {
            color: '#f59e0b',
            type: 'dashed',
            opacity: 0.8
          },
          data: [{ yAxis: warningThreshold.value }]
        },
        markPoint: {
          symbolSize: 44,
          label: {
            color: '#e5eefc',
            fontSize: 10
          },
          itemStyle: {
            color: '#16324f',
            borderColor: '#00f2fe',
            borderWidth: 1
          },
          data: [
            { type: 'max', name: '峰值' },
            { type: 'min', name: '谷值' }
          ]
        }
      }
    ]
  }
  await mainChart.setOptions(option, { notMerge: true })
}

const renderPieChart = async () => {
  const data = [
    { value: energyStats.electricity?.total_consumption || 0, name: '电力', itemStyle: { color: '#00f2fe' } },
    { value: energyStats.water?.total_consumption || 0, name: '水', itemStyle: { color: '#4facfe' } },
    { value: energyStats.gas?.total_consumption || 0, name: '燃气', itemStyle: { color: '#f093fb' } },
    { value: energyStats.heat?.total_consumption || 0, name: '热力', itemStyle: { color: '#ff6b6b' } },
    { value: energyStats.cooling?.total_consumption || 0, name: '冷气', itemStyle: { color: '#a78bfa' } }
  ].filter(d => d.value > 0)
  
  if (data.length === 0) {
    data.push({ value: 1, name: '暂无有效数据', itemStyle: { color: '#1e3a5f' } })
  }
  
  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0,0,0,0.7)',
      borderColor: '#00f2fe',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: '#9fb0c7', fontSize: 11 },
      itemWidth: 10,
      itemHeight: 10
    },
    graphic: data.length === 1 && data[0].name === '暂无有效数据' ? {
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
    } : undefined,
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
  }
  await pieChart.setOptions(option)
}

watch(() => realTimeData.power, (value) => {
  renderGauge(Math.abs(value))
})

watch(energyTrendData, () => {
  renderMainChart()
}, { deep: true })

watch(energyStats, () => {
  renderPieChart()
}, { deep: true })

watch(currentDeviceId, (deviceId, previousId) => {
  if (!deviceId || deviceId === previousId) return
  void loadDeviceData()
})
</script>

<template>
  <div class="big-screen">
    <!-- 顶部标题栏 -->
    <header class="header">
      <div class="header-left">
        <div class="title-box">
          <div class="title-icon">
            <svg
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M13 3L4 14h7v7l9-11h-7V3z" />
            </svg>
          </div>
          <div class="title-text">
            <h1>园区综合能源管理系统</h1>
            <span>Campus Energy Management System</span>
          </div>
        </div>
      </div>
      
      <div class="header-center">
        <div class="time-box">
          <div class="time">
            {{ currentTime }}
          </div>
          <div class="date">
            {{ currentDate }}
          </div>
          <div class="time-meta">
            当前时段：{{ shiftLabel }} · 数据轮询 10s
          </div>
        </div>
      </div>
      
      <div class="header-right">
        <div
          class="status-box"
          :class="{ online: isConnected }"
        >
          <span class="status-dot" />
          <span class="status-text">{{ isConnected ? '系统运行中' : '连接断开' }}</span>
        </div>
        <el-tag
          v-if="hasScopedAccess"
          size="small"
          type="warning"
          effect="dark"
        >
          范围受限视图
        </el-tag>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="main">
      <!-- 左侧面板 -->
      <aside class="panel-left">
        <el-alert
          :title="dashboardScopeHint"
          :type="hasScopedAccess ? 'warning' : 'info'"
          :closable="false"
          show-icon
          class="scope-alert"
        />
        <div class="card">
          <div class="card-header">
            <span class="card-title">园区总览卡片</span>
            <span class="card-subtitle">Campus Overview</span>
          </div>
          <div class="card-body">
            <div class="stat-grid stat-grid--compact">
              <StatTile
                v-for="item in overviewCards"
                :key="item.label"
                :tone="item.tone"
                :label="item.label"
                :value="item.value"
                :caption="item.caption"
              />
            </div>
          </div>
        </div>

        <div class="card flex-1">
          <div class="card-header">
            <span class="card-title">告警概览</span>
            <span class="card-subtitle">Alarm Overview</span>
          </div>
          <div class="card-body">
            <div
              v-if="latestAlarmItems.length"
              class="alarm-list"
            >
              <div
                v-for="alarm in latestAlarmItems"
                :key="alarm.id"
                class="alarm-item"
                :class="alarm.tone"
              >
                <div class="alarm-main">
                  <div class="alarm-title-row">
                    <span class="alarm-device">{{ alarm.deviceName }}</span>
                    <span class="alarm-level">{{ alarm.label }}</span>
                  </div>
                  <p class="alarm-message">
                    {{ alarm.message }}
                  </p>
                </div>
                <div class="alarm-side">
                  <span class="alarm-time">{{ alarm.time }}</span>
                  <span class="alarm-action">{{ alarm.action }}</span>
                </div>
              </div>
            </div>
            <div
              v-else
              class="device-empty"
            >
              当前没有未处理告警，园区运行稳定。
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <span class="card-title">能源介质占比</span>
            <span class="card-subtitle">Energy Mix</span>
          </div>
          <div class="card-body">
            <div
              v-if="hasEnergyDistributionData"
              :ref="pieChart.chartRef"
              class="chart-container chart-container--pie"
            />
            <div
              v-else
              class="distribution-empty"
            >
              <strong>当前暂无有效占比数据</strong>
              <p>请检查采集链路、时间范围或等待更多能耗数据入库后再查看。</p>
            </div>
          </div>
        </div>
      </aside>

      <!-- 中间面板 -->
      <section class="panel-center">
        <div class="ops-strip">
          <div
            v-for="item in scadaStatusCards"
            :key="item.label"
            class="ops-strip__item"
            :class="`ops-strip__item--${item.tone}`"
          >
            <span class="ops-strip__label">{{ item.label }}</span>
            <strong class="ops-strip__value">{{ item.value }}</strong>
            <span class="ops-strip__meta">{{ item.meta }}</span>
          </div>
        </div>

        <div class="card chart-card chart-card--primary">
          <div class="card-header">
            <span class="card-title">园区负荷趋势</span>
            <span class="card-subtitle">Load Trend</span>
          </div>
          <div class="card-body chart-card__body">
            <div class="trend-summary">
              <div
                v-for="item in trendHighlights"
                :key="item.label"
                class="trend-summary__item"
              >
                <span class="trend-summary__label">{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
            <div
              :ref="mainChart.chartRef"
              class="chart-container chart-container--trend"
            />
          </div>
        </div>

        <div class="device-section">
          <div class="card device-focus-card">
            <div class="card-header">
              <span class="card-title">重点设备卡片</span>
              <span class="card-subtitle">Key Device Console</span>
            </div>
            <div class="card-body">
              <div class="focus-strip">
                <div class="focus-copy">
                  <span class="focus-eyebrow">当前监测对象</span>
                  <h2>{{ selectedDeviceSummary.name }}</h2>
                  <div class="focus-meta">
                    <span>{{ selectedDeviceSummary.type }}</span>
                    <span>{{ selectedDeviceSummary.energyType }}</span>
                    <span :class="{ online: currentDevice?.is_active }">{{ selectedDeviceSummary.status }}</span>
                  </div>
                </div>
                <div class="focus-numbers">
                  <div
                    v-for="item in selectedDeviceProfile"
                    :key="item.label"
                    class="focus-number"
                  >
                    <span class="focus-number__label">{{ item.label }}</span>
                    <strong>{{ item.value }}</strong>
                  </div>
                </div>
              </div>

              <div class="focus-dual-panel">
                <div class="card gauge-card">
                  <div class="card-header gauge-card__header">
                    <div>
                      <span class="card-title">实时监测面板</span>
                      <div class="gauge-card__caption">
                        选择设备后，状态灯、趋势和监测值将同步刷新
                      </div>
                    </div>
                    <el-tag
                      size="small"
                      type="info"
                      effect="dark"
                    >
                      可选 {{ selectableDeviceCount }} 台
                    </el-tag>
                  </div>
                  <div class="card-body gauge-body">
                    <div class="gauge-toolbar">
                      <div class="gauge-toolbar__meta">
                        <span class="gauge-toolbar__label">监测设备</span>
                        <strong>{{ selectedDeviceLabel }}</strong>
                        <span class="gauge-toolbar__hint">通过右侧设备监控列表或下方快速切换区切换监测对象</span>
                      </div>
                      <el-tag
                        size="small"
                        type="info"
                        effect="dark"
                        :class="{ 'is-loading': realtimeLoading.device }"
                      >
                        {{ realtimeLoading.device ? '数据切换中' : '实时联动中' }}
                      </el-tag>
                    </div>
                    <div
                      v-if="deviceBoardItems.length"
                      class="device-quick-switch"
                    >
                      <button
                        v-for="device in deviceBoardItems.slice(0, 6)"
                        :key="device.id"
                        type="button"
                        class="device-chip"
                        :class="{ active: device.id === currentDeviceId, offline: !device.is_active }"
                        @click="selectDevice(device.id)"
                      >
                        <span class="device-chip__dot" />
                        <span class="device-chip__label">{{ device.name }}</span>
                      </button>
                    </div>
                    <div class="gauge-console">
                      <div class="gauge-wrapper">
                        <div
                          :ref="gaugeChart.chartRef"
                          class="gauge-chart"
                        />
                        <div class="gauge-label">
                          kW
                        </div>
                      </div>
                      <div class="gauge-readout">
                        <div class="readout-head">
                          <span
                            class="signal-dot"
                            :class="selectedDeviceStatusTone"
                          />
                          <span>{{ selectedDeviceSummary.status }}</span>
                        </div>
                        <div class="readout-value">
                          {{ displayPower.toFixed(1) }}<small>kW</small>
                        </div>
                        <div class="readout-caption">
                          当前负荷
                        </div>
                      </div>
                    </div>
                    <div class="gauge-stats">
                      <div
                        v-for="item in focusMetrics"
                        :key="item.label"
                        class="gauge-stat"
                      >
                        <span class="label">{{ item.label }}</span>
                        <span class="value">{{ item.value }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="card event-card">
                  <div class="card-header">
                    <span class="card-title">联动事件</span>
                    <span class="card-subtitle">Selected Device Alarms</span>
                  </div>
                  <div class="card-body">
                    <div
                      v-if="selectedDeviceAlarmItems.length"
                      class="event-list"
                    >
                      <div
                        v-for="alarm in selectedDeviceAlarmItems"
                        :key="alarm.id"
                        class="event-item"
                        :class="alarm.tone"
                      >
                        <div class="event-item__head">
                          <span class="event-item__name">{{ alarm.deviceName }}</span>
                          <span class="event-item__time">{{ alarm.time }}</span>
                        </div>
                        <p class="event-item__message">
                          {{ alarm.message }}
                        </p>
                        <div class="event-item__footer">
                          <span class="event-item__level">{{ alarm.label }}</span>
                          <span class="event-item__action">{{ alarm.action }}</span>
                        </div>
                      </div>
                    </div>
                    <div
                      v-else
                      class="device-empty"
                    >
                      当前选中对象没有活动告警，趋势面板将优先显示实时负荷变化。
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 右侧面板 -->
      <aside class="panel-right">
        <div class="card">
          <div class="card-header">
            <span class="card-title">设备监控列表</span>
            <span class="card-subtitle">SCADA Device Board</span>
          </div>
          <div class="card-body">
            <div class="device-board-header">
              <div class="device-board-header__item">
                <span>在线</span>
                <strong>{{ onlineDevices }}</strong>
              </div>
              <div class="device-board-header__item">
                <span>总数</span>
                <strong>{{ totalDevices }}</strong>
              </div>
              <div class="device-board-header__item">
                <span>当前</span>
                <strong>{{ currentDevice?.name || '--' }}</strong>
              </div>
            </div>
            <div
              v-if="deviceBoardItems.length"
              class="device-list scada-device-list"
            >
              <button
                v-for="device in deviceBoardItems"
                :key="device.id"
                class="device-item device-item--button"
                :class="{ active: device.id === currentDeviceId, offline: !device.is_active }"
                type="button"
                @click="selectDevice(device.id)"
              >
                <span class="device-status" />
                <div class="device-copy">
                  <span class="device-name">{{ device.name }}</span>
                  <span class="device-location">{{ device.location || '未标注位置' }}</span>
                </div>
                <span class="device-type">{{ device.energy_type || device.device_type }}</span>
              </button>
            </div>
            <div
              v-else
              class="device-empty"
            >
              暂无设备或表计数据接入
            </div>
          </div>
        </div>

        <div class="card flex-1">
          <div class="card-header">
            <span class="card-title">各区域能耗排行</span>
            <span class="card-subtitle">Regional Ranking</span>
          </div>
          <div class="card-body">
            <div
              v-if="regionRankings.length"
              class="energy-list"
            >
              <div
                v-for="item in regionRankings"
                :key="item.name"
                class="energy-row ranking-row"
              >
                <span class="ranking-index">{{ item.rank }}</span>
                <div class="energy-copy">
                  <span class="energy-name">{{ item.name }}</span>
                  <span class="energy-meta">{{ item.online }}/{{ item.total }} 台在线</span>
                </div>
                <span class="energy-value">
                  {{ item.hasCapacity ? `${item.score.toFixed(1)} kW` : `${item.total} 台` }}
                </span>
              </div>
            </div>
            <div
              v-else
              class="device-empty"
            >
              暂无区域设备数据可用于排行
            </div>
          </div>
        </div>
      </aside>
    </main>
  </div>
</template>

<style scoped>
/* ========== 基础布局 ========== */
.big-screen {
  width: 100%;
  min-height: 100vh;
  background: #0f1724;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow-x: auto;
  overflow-y: auto;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.scope-alert {
  margin-bottom: 16px;
}

/* ========== 顶部标题栏 ========== */
.header {
  min-height: 76px;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  z-index: 10;
  background: #111a28;
  border-bottom: 1px solid rgba(72, 95, 132, 0.32);
}

.title-box {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  width: 42px;
  height: 42px;
  background: #1d2938;
  border: 1px solid rgba(91, 113, 148, 0.3);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.title-icon svg {
  width: 20px;
  height: 20px;
  color: #7dd3fc;
}

.title-text h1 {
  font-size: 22px;
  font-weight: 700;
  margin: 0;
  color: #f8fafc;
  letter-spacing: 0.02em;
}

.title-text span {
  font-size: 11px;
  color: #8697af;
  letter-spacing: 0.04em;
}

.time-box {
  text-align: center;
}

.time-box .time {
  font-size: 30px;
  font-weight: 700;
  font-family: 'DIN', 'Monaco', monospace;
  color: #f8fafc;
  letter-spacing: 0.08em;
}

.time-box .date {
  font-size: 13px;
  color: #94a3b8;
  margin-top: 2px;
}

.time-meta {
  margin-top: 4px;
  font-size: 11px;
  color: #7f90a8;
}

.status-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: rgba(127, 29, 29, 0.18);
  border: 1px solid rgba(239,68,68,0.22);
  border-radius: 999px;
  transition: all 0.3s;
}

.status-box.online {
  background: rgba(20, 83, 45, 0.18);
  border-color: rgba(34,197,94,0.22);
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #ef4444;
  border-radius: 50%;
}

.status-box.online .status-dot {
  background: #22c55e;
}

.status-text {
  font-size: 12px;
  color: #ef4444;
  font-weight: 600;
}

.status-box.online .status-text {
  color: #86efac;
}

/* ========== 主内容区 ========== */
.main {
  flex: 1;
  display: grid;
  grid-template-columns: 300px 1fr 320px;
  gap: 16px;
  padding: 16px;
  width: min(100%, 1680px);
  margin: 0 auto;
  position: relative;
  z-index: 10;
  min-height: 600px;
  align-items: start;
}

/* ========== 通用卡片样式 ========== */
.card {
  position: relative;
  background: #131d2b;
  border: 1px solid #243244;
  border-radius: 14px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: none;
}

.card-header {
  padding: 14px 16px;
  border-bottom: 1px solid #223042;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #e5edf7;
}

.card-subtitle {
  font-size: 10px;
  color: #6f8199;
  letter-spacing: 0.06em;
  opacity: 0.8;
}

.card-body {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.flex-1 { flex: 1; }

/* ========== 左侧面板 ========== */
.panel-left {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.stat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.stat-grid--compact {
  grid-template-columns: 1fr;
}

.energy-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.energy-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #162130;
  border: 1px solid #243244;
  border-radius: 12px;
}

.ranking-row {
  min-height: 52px;
}

.ranking-index {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #cfe2f7;
  background: #1b2838;
  border: 1px solid #314055;
  flex: 0 0 auto;
}

.energy-icon {
  font-size: 18px;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1b2838;
}

.energy-copy {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.energy-name {
  font-size: 13px;
  color: #dbe6f5;
}

.energy-meta {
  font-size: 11px;
  color: #6f819e;
}

.energy-icon.cyan { color: #38bdf8; }
.energy-icon.blue { color: #60a5fa; }
.energy-icon.pink { color: #f59e0b; }
.energy-icon.red { color: #ef4444; }
.energy-icon.purple { color: #a78bfa; }

.energy-value {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  font-family: 'DIN', 'Monaco', monospace;
}

/* ========== 中间面板 ========== */
.panel-center {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.ops-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.ops-strip__item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 88px;
  padding: 14px;
  border: 1px solid #243244;
  background: #131d2b;
  border-radius: 12px;
}

.ops-strip__item::before {
  content: '';
  width: 32px;
  height: 3px;
  border-radius: 999px;
  background: currentColor;
  opacity: 0.8;
}

.ops-strip__label {
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #8fa1bb;
}

.ops-strip__value {
  font-size: 24px;
  line-height: 1.1;
  color: #f8fafc;
  font-family: 'DIN', 'Monaco', monospace;
}

.ops-strip__meta {
  font-size: 11px;
  color: #7f92ad;
}

.ops-strip__item--cyan { color: #38bdf8; }
.ops-strip__item--green { color: #22c55e; }
.ops-strip__item--red { color: #ef4444; }
.ops-strip__item--purple { color: #a78bfa; }
.ops-strip__item--blue { color: #60a5fa; }

.chart-card--primary .card-body {
  gap: 16px;
}

.trend-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.trend-summary__item {
  padding: 12px 14px;
  background: #162130;
  border: 1px solid #243244;
  border-radius: 12px;
}

.trend-summary__label {
  display: block;
  font-size: 12px;
  color: #8ea0bc;
}

.trend-summary__item strong {
  display: block;
  margin-top: 6px;
  font-size: 20px;
  color: #f8fafc;
  font-family: 'DIN', 'Monaco', monospace;
}

.device-section {
  display: block;
  width: 100%;
  min-width: 0;
}

.device-focus-card > .card-body {
  gap: 16px;
}

.focus-strip {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: stretch;
  padding: 18px;
  border-radius: 14px;
  background: #131d2b;
  border: 1px solid #243244;
  box-shadow: none;
}

.focus-dual-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(260px, 0.8fr);
  gap: 16px;
  align-items: stretch;
  width: 100%;
  min-width: 0;
}

.focus-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.focus-eyebrow {
  font-size: 11px;
  color: #8da2bd;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.focus-copy h2 {
  margin: 8px 0;
  font-size: 28px;
  line-height: 1.2;
  color: #f8fbff;
}

.focus-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.focus-meta span {
  padding: 5px 10px;
  border-radius: 999px;
  background: #1a2636;
  color: #9bb0c9;
  font-size: 11px;
}

.focus-meta .online {
  color: #86efac;
  background: rgba(20, 83, 45, 0.28);
}

.focus-numbers {
  display: grid;
  grid-template-columns: repeat(2, minmax(120px, 1fr));
  gap: 12px;
  min-width: 0;
}

.focus-number {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 14px;
  border-radius: 12px;
  background: #162130;
  border: 1px solid #243244;
}

.focus-number__label {
  font-size: 12px;
  color: #8396b2;
}

.focus-number strong {
  margin-top: 8px;
  font-size: 22px;
  line-height: 1;
  color: #fff;
  font-family: 'DIN', 'Monaco', monospace;
}

.gauge-card .card-body {
  gap: 18px;
}

.gauge-wrapper {
  position: relative;
  width: min(180px, 100%);
  height: 170px;
  flex: 0 0 auto;
  margin: 0 auto;
}

.gauge-chart {
  width: 100%;
  height: 100%;
}

.gauge-label {
  position: absolute;
  bottom: 25px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 14px;
  color: #94a3b8;
}

.gauge-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.gauge-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: #162130;
  border-radius: 10px;
  border: 1px solid #243244;
}

.gauge-stat .label {
  font-size: 13px;
  color: #95a7c3;
}

.gauge-stat .value {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  font-family: 'DIN', 'Monaco', monospace;
}

.gauge-stat .value small {
  font-size: 12px;
  color: #8892b0;
  margin-left: 3px;
}

.gauge-card__header {
  align-items: flex-start;
}

.gauge-card__caption {
  margin-top: 6px;
  font-size: 11px;
  color: #7d8fa8;
}

.gauge-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 16px;
}

.gauge-console {
  display: grid;
  grid-template-columns: minmax(160px, 190px) minmax(0, 1fr);
  gap: 16px;
  align-items: center;
  width: 100%;
  min-width: 0;
}

.gauge-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  padding: 14px;
  border-radius: 12px;
  background: #162130;
  border: 1px solid #243244;
}

.gauge-toolbar__meta {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.gauge-toolbar__label {
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #8fa1ba;
}

.gauge-toolbar__meta strong {
  color: #f8fafc;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gauge-toolbar__hint {
  font-size: 11px;
  color: #7d8fa8;
}

.device-quick-switch {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.device-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid #243244;
  background: #162130;
  color: #cfe1f5;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.device-chip:hover {
  border-color: #35608d;
  background: #192638;
}

.device-chip.active {
  border-color: rgba(56, 189, 248, 0.45);
  background: #1a2b3f;
}

.device-chip.offline {
  color: #94a3b8;
}

.device-chip__dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #22c55e;
  flex: 0 0 auto;
}

.device-chip.offline .device-chip__dot {
  background: #ef4444;
}

.device-chip__label {
  max-width: 140px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 12px;
}

.gauge-readout {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  min-height: 140px;
  border-radius: 12px;
  background: #162130;
  border: 1px solid #243244;
}

.readout-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #90a4c0;
}

.signal-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #ef4444;
}

.signal-dot.online {
  background: #22c55e;
}

.signal-dot.offline {
  background: #ef4444;
}

.readout-value {
  font-size: 34px;
  line-height: 1;
  font-weight: 700;
  color: #f8fafc;
  font-family: 'DIN', 'Monaco', monospace;
}

.readout-value small {
  margin-left: 6px;
  font-size: 13px;
  color: #92a5bf;
}

.readout-caption {
  font-size: 12px;
  color: #7d8fa8;
}

.event-card .card-body {
  padding-top: 12px;
}

.event-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.event-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border-radius: 12px;
  border: 1px solid #243244;
  background: #162130;
}

.event-item.critical {
  border-color: rgba(239, 68, 68, 0.28);
}

.event-item.warning {
  border-color: rgba(245, 158, 11, 0.28);
}

.event-item.notice {
  border-color: rgba(59, 130, 246, 0.28);
}

.event-item__head,
.event-item__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.event-item__name {
  font-size: 13px;
  font-weight: 600;
  color: #f8fafc;
}

.event-item__time {
  font-size: 11px;
  color: #91a4bf;
}

.event-item__message {
  margin: 0;
  color: #d8e2ef;
  line-height: 1.5;
  font-size: 13px;
}

.event-item__level {
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(255,255,255,0.08);
  color: #dce7f6;
  font-size: 11px;
}

.event-item__action {
  font-size: 12px;
  color: #8ea2bc;
  text-align: right;
}

.chart-container {
  width: 100%;
  min-height: 200px;
}

.chart-container--pie {
  height: clamp(240px, 28vh, 320px);
}

.chart-container--trend {
  height: clamp(400px, 48vh, 560px);
  min-height: 400px;
}

/* ========== 右侧面板 ========== */
.panel-right {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.distribution-empty {
  min-height: 240px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10px;
  padding: 20px;
  border: 1px dashed #314055;
  border-radius: 12px;
  background: #162130;
}

.distribution-empty strong {
  font-size: 15px;
  color: #e5edf7;
}

.distribution-empty p {
  margin: 0;
  font-size: 12px;
  line-height: 1.6;
  color: #8ea0bc;
}

/* 设备列表 */
.device-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.scada-device-list {
  gap: 10px;
  margin-top: 12px;
  max-height: 520px;
  overflow: auto;
  padding-right: 4px;
}

.device-board-header {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.device-board-header__item {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #162130;
  border: 1px solid #243244;
}

.device-board-header__item span {
  font-size: 11px;
  color: #90a4c0;
}

.device-board-header__item strong {
  color: #f8fafc;
  font-size: 18px;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.device-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #162130;
  border-radius: 12px;
  border: 1px solid #243244;
}

.device-item--button {
  width: 100%;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.device-item--button:hover {
  border-color: #35608d;
  background: #192638;
}

.device-item.active {
  border-color: rgba(56, 189, 248, 0.45);
  background: #19293d;
}

.device-status {
  width: 8px;
  height: 8px;
  background: #ef4444;
  border-radius: 50%;
}

.device-item.active .device-status {
  background: #22c55e;
  box-shadow: none;
}

.device-item.offline .device-status {
  background: #ef4444;
}

.device-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.device-name {
  font-size: 13px;
  color: #fff;
}

.device-location {
  font-size: 11px;
  color: #7f93ae;
}

.device-type {
  font-size: 11px;
  color: #8892b0;
  padding: 2px 8px;
  background: #1d2938;
  border-radius: 10px;
}

.device-empty {
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8396b1;
  border: 1px dashed #314055;
  border-radius: 12px;
  background: #162130;
  text-align: center;
  padding: 18px;
}

.alarm-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alarm-item {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding: 14px;
  border-radius: 12px;
  border: 1px solid #243244;
  background: #162130;
}

.alarm-item.critical {
  border-color: rgba(239, 68, 68, 0.28);
}

.alarm-item.warning {
  border-color: rgba(245, 158, 11, 0.28);
}

.alarm-item.notice {
  border-color: rgba(59, 130, 246, 0.28);
}

.alarm-main,
.alarm-side {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.alarm-main {
  min-width: 0;
  flex: 1;
}

.alarm-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.alarm-device {
  font-size: 13px;
  font-weight: 600;
  color: #f8fbff;
}

.alarm-level {
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 11px;
  color: #dbe6f5;
  background: rgba(255,255,255,0.08);
}

.alarm-item.critical .alarm-level {
  background: rgba(239, 68, 68, 0.12);
  color: #fca5a5;
}

.alarm-item.warning .alarm-level {
  background: rgba(245, 158, 11, 0.12);
  color: #fcd34d;
}

.alarm-item.notice .alarm-level {
  background: rgba(59, 130, 246, 0.12);
  color: #93c5fd;
}

.alarm-message {
  margin: 0;
  color: #cdd9ec;
  font-size: 13px;
  line-height: 1.5;
}

.alarm-side {
  min-width: 132px;
  align-items: flex-end;
  text-align: right;
}

.alarm-time {
  font-size: 11px;
  color: #95a7c3;
}

.alarm-action {
  font-size: 12px;
  color: #dbe6f5;
  line-height: 1.4;
}

/* ========== 响应式 ========== */
@media (max-width: 1400px) {
  .main {
    grid-template-columns: 260px 1fr 280px;
  }

  .ops-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .device-section {
    grid-template-columns: 1fr;
  }

  .focus-dual-panel {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1320px) {
  .focus-strip {
    flex-direction: column;
  }

  .focus-numbers {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .focus-dual-panel {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1200px) {
  .main {
    grid-template-columns: 1fr 1fr;
  }
  
  .panel-left { order: 1; }
  .panel-center { order: 2; }
  .panel-right { 
    order: 3; 
    grid-column: span 2;
    flex-direction: row;
    flex-wrap: wrap;
  }

  .gauge-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .gauge-console {
    grid-template-columns: 1fr;
  }

  .ops-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .trend-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  
  .panel-right .card {
    flex: 2;
    min-width: 300px;
  }
}

@media (max-width: 900px) {
  .main {
    grid-template-columns: 1fr;
  }
  
  .panel-right {
    grid-column: span 1;
  }
  
  .header {
    flex-wrap: wrap;
    height: auto;
    padding: 15px;
    gap: 15px;
  }
  
  .header-center {
    order: -1;
    width: 100%;
    text-align: center;
  }

  .focus-numbers {
    grid-template-columns: 1fr;
  }

  .ops-strip {
    grid-template-columns: 1fr;
  }

  .trend-summary {
    grid-template-columns: 1fr;
  }

  .gauge-stats {
    grid-template-columns: 1fr;
  }

  .alarm-item {
    flex-direction: column;
  }

  .alarm-side {
    min-width: 0;
    align-items: flex-start;
    text-align: left;
  }
}
</style>
