<script setup lang="ts">
import { onMounted, watch, computed, nextTick } from 'vue'
import { useSocketStore } from '@/stores/useSocketStore'
import { useAlarmPolling } from '@/features/alarm/composables/useAlarmPolling'
import { useDashboardClock } from '@/features/dashboard/composables/useDashboardClock'
import { useDashboardDeviceSelection } from '@/features/dashboard/composables/useDashboardDeviceSelection'
import { useDashboardEnergyStats } from '@/features/dashboard/composables/useDashboardEnergyStats'
import { useDashboardRealtime } from '@/features/dashboard/composables/useDashboardRealtime'
import { useECharts } from '@/shared/composables/useECharts'
import StatTile from '@/shared/ui/StatTile.vue'

// --- 状态定义 ---
const socketStore = useSocketStore()
const { alarmCount, alarmList } = useAlarmPolling({ interval: 10000 })
const { currentTime, currentDate } = useDashboardClock()
const { currentDevice, currentDeviceId, deviceList, totalDevices, onlineDevices, loadDeviceList } = useDashboardDeviceSelection()
const { energyStats, todayEnergy, loadEnergyStats } = useDashboardEnergyStats()
const {
  displayCurrent,
  displayEnergy,
  displayPower,
  energyTrendData,
  realTimeData,
  loadDeviceData
} = useDashboardRealtime({
  currentDeviceId,
  deviceList,
  latestMessage: socketStore.latestMessage
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
    label: '设备总数',
    value: overview.value.totalDevices,
    caption: '接入矿区能源网络',
    tone: 'cyan' as const
  },
  {
    label: '在线率',
    value: `${onlineRate.value}%`,
    caption: `${overview.value.onlineDevices} 台在线`,
    tone: 'green' as const
  },
  {
    label: '告警数',
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
  if (hour >= 8 && hour < 16) return '白班'
  if (hour >= 16 && hour < 24) return '中班'
  return '夜班'
})

const runtimeStatus = computed(() => socketStore.isConnected ? '正常运行' : '通讯中断')
const runtimeTone = computed(() => socketStore.isConnected ? 'green' as const : 'red' as const)

const topSummaryCards = computed(() => [
  {
    tone: 'cyan' as const,
    label: '当前总负荷',
    value: displayPower.value.toFixed(1),
    caption: `峰值 ${peakLoad.value.toFixed(1)} kW`
  },
  {
    tone: 'purple' as const,
    label: '今日总能耗',
    value: todayEnergy.value.toFixed(1),
    caption: '全系统累计 kWh'
  },
  {
    tone: 'green' as const,
    label: '在线设备',
    value: `${onlineDevices.value}/${totalDevices.value || 0}`,
    caption: `在线率 ${onlineRate.value}%`
  },
  {
    tone: overview.value.alarmCount ? 'red' as const : 'blue' as const,
    label: '未处理告警',
    value: overview.value.alarmCount,
    caption: overview.value.alarmCount ? '请优先处理严重异常' : '当前告警队列为空'
  },
  {
    tone: runtimeTone.value,
    label: '系统评分',
    value: socketStore.isConnected && overview.value.alarmCount === 0 ? 96 : socketStore.isConnected ? 82 : 61,
    caption: `${runtimeStatus.value} · ${shiftLabel.value}`
  }
])

const selectedDeviceSummary = computed(() => ({
  name: currentDevice.value?.name || '暂无设备',
  type: currentDevice.value?.device_type || '未选择',
  energyType: currentDevice.value?.energy_type || '未知',
  status: currentDevice.value?.is_active ? '在线运行' : '离线待机'
}))

const focusMetrics = computed(() => [
  { label: '实时功率', value: `${displayPower.value.toFixed(1)} kW` },
  { label: '母线电压', value: `${realTimeData.voltage.toFixed(1)} V` },
  { label: 'A相电流', value: `${displayCurrent.value.toFixed(1)} A` },
  { label: '今日用电', value: `${displayEnergy.value.toFixed(1)} kWh` }
])

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
  console.log('📊 渲染负荷曲线:', times.length, '个数据点')
  
  // 获取当前设备名称
  const deviceName = currentDevice.value?.name || '设备'
  
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0,0,0,0.8)',
      borderColor: '#00f2fe',
      textStyle: { color: '#fff' },
      formatter: (params: any) => {
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
        symbolSize: (value: number, params: any) => params.dataIndex === (values.length - 1) ? 8 : 0,
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
</script>

<template>
  <div class="big-screen">
    <!-- 顶部标题栏 -->
    <header class="header">
      <div class="header-left">
        <div class="title-box">
          <div class="title-icon">
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M13 3L4 14h7v7l9-11h-7V3z"/>
            </svg>
          </div>
          <div class="title-text">
            <h1>煤矿综合能源管理系统</h1>
            <span>Mine Integrated Energy Management System</span>
          </div>
        </div>
      </div>
      
      <div class="header-center">
        <div class="time-box">
          <div class="time">{{ currentTime }}</div>
          <div class="date">{{ currentDate }}</div>
          <div class="time-meta">当前班次：{{ shiftLabel }} · 数据轮询 10s</div>
        </div>
      </div>
      
      <div class="header-right">
        <div class="status-box" :class="{ online: socketStore.isConnected }">
          <span class="status-dot"></span>
          <span class="status-text">{{ socketStore.isConnected ? '系统运行中' : '连接断开' }}</span>
        </div>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="main">
      <!-- 左侧面板 -->
      <aside class="panel-left">
        <div class="card">
          <div class="card-header">
            <span class="card-title">迷你总览</span>
            <span class="card-subtitle">Overview</span>
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
            <span class="card-title">能源消耗占比</span>
            <span class="card-subtitle">Distribution</span>
          </div>
          <div class="card-body">
            <div v-if="hasEnergyDistributionData" class="chart-container chart-container--pie" :ref="pieChart.chartRef"></div>
            <div v-else class="distribution-empty">
              <strong>当前暂无有效占比数据</strong>
              <p>请检查采集链路、时间范围或等待更多能耗数据入库后再查看。</p>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <span class="card-title">区域能耗排行</span>
            <span class="card-subtitle">Estimated</span>
          </div>
          <div class="card-body">
            <div v-if="regionRankings.length" class="energy-list">
              <div v-for="item in regionRankings" :key="item.name" class="energy-row ranking-row">
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
            <div v-else class="device-empty">暂无区域设备数据可用于排行</div>
          </div>
        </div>
      </aside>

      <!-- 中间面板 -->
      <section class="panel-center">
        <div class="summary-grid">
          <StatTile
            v-for="item in topSummaryCards"
            :key="item.label"
            :tone="item.tone"
            :label="item.label"
            :value="item.value"
            :caption="item.caption"
          />
        </div>

        <div class="card chart-card chart-card--primary">
          <div class="card-header">
            <span class="card-title">24h 负荷趋势</span>
            <span class="card-subtitle">Trend Analysis</span>
          </div>
          <div class="card-body chart-card__body">
            <div class="trend-summary">
              <div v-for="item in trendHighlights" :key="item.label" class="trend-summary__item">
                <span class="trend-summary__label">{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
            <div class="chart-container chart-container--trend" :ref="mainChart.chartRef"></div>
          </div>
        </div>

        <div class="device-section">
          <div class="focus-strip">
            <div class="focus-copy">
              <span class="focus-eyebrow">当前监测设备</span>
              <h2>{{ selectedDeviceSummary.name }}</h2>
              <div class="focus-meta">
                <span>{{ selectedDeviceSummary.type }}</span>
                <span>{{ selectedDeviceSummary.energyType }}</span>
                <span :class="{ online: currentDevice?.is_active }">{{ selectedDeviceSummary.status }}</span>
              </div>
            </div>
            <div class="focus-numbers">
              <div v-for="item in focusMetrics" :key="item.label" class="focus-number">
                <span class="focus-number__label">{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
          </div>

          <div class="card gauge-card gauge-card--compact">
            <div class="card-header">
              <span class="card-title">设备负荷</span>
              <el-select 
                v-model="currentDeviceId" 
                size="small"
                style="width: 160px"
                @change="loadDeviceData"
              >
                <el-option v-for="d in deviceList" :key="d.id" :label="d.name" :value="d.id" />
              </el-select>
            </div>
            <div class="card-body gauge-body">
              <div class="gauge-wrapper">
                <div class="gauge-chart" :ref="gaugeChart.chartRef"></div>
                <div class="gauge-label">kW</div>
              </div>
              <div class="gauge-stats">
                <div class="gauge-stat">
                  <span class="label">当前功率</span>
                  <span class="value">{{ displayPower.toFixed(1) }}<small>kW</small></span>
                </div>
                <div class="gauge-stat">
                  <span class="label">预警阈值</span>
                  <span class="value">{{ warningThreshold.toFixed(1) }}<small>kW</small></span>
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
            <span class="card-title">最新告警</span>
            <span class="card-subtitle">Action Required</span>
          </div>
          <div class="card-body">
            <div v-if="latestAlarmItems.length" class="alarm-list">
              <div v-for="alarm in latestAlarmItems" :key="alarm.id" class="alarm-item" :class="alarm.tone">
                <div class="alarm-main">
                  <div class="alarm-title-row">
                    <span class="alarm-device">{{ alarm.deviceName }}</span>
                    <span class="alarm-level">{{ alarm.label }}</span>
                  </div>
                  <p class="alarm-message">{{ alarm.message }}</p>
                </div>
                <div class="alarm-side">
                  <span class="alarm-time">{{ alarm.time }}</span>
                  <span class="alarm-action">{{ alarm.action }}</span>
                </div>
              </div>
            </div>
            <div v-else class="device-empty">
              当前没有未处理告警，系统运行稳定。
            </div>
          </div>
        </div>

        <!-- 设备状态 -->
        <div class="card flex-1">
          <div class="card-header">
            <span class="card-title">设备状态</span>
            <span class="card-subtitle">Device Status</span>
          </div>
          <div class="card-body">
            <div v-if="deviceList.length" class="device-list">
              <div 
                v-for="device in deviceList.slice(0, 6)" 
                :key="device.id" 
                class="device-item"
                :class="{ active: device.is_active }"
              >
                <span class="device-status"></span>
                <span class="device-name">{{ device.name }}</span>
                <span class="device-type">{{ device.energy_type }}</span>
              </div>
            </div>
            <div v-else class="device-empty">
              暂无设备数据接入
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

.summary-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

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
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) 320px;
  gap: 16px;
  align-items: stretch;
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
  min-width: 360px;
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
  flex-direction: row;
  align-items: center;
  gap: 18px;
}

.gauge-card--compact .card-body {
  justify-content: space-between;
}

.gauge-wrapper {
  position: relative;
  width: 160px;
  height: 150px;
  flex: 0 0 auto;
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
  flex: 1;
  display: flex;
  flex-direction: column;
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

.device-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #162130;
  border-radius: 12px;
  border: 1px solid #243244;
}

.device-item.active {
  border-color: rgba(34,197,94,0.28);
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

.device-name {
  flex: 1;
  font-size: 13px;
  color: #fff;
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

  .summary-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .device-section {
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

  .focus-strip {
    flex-direction: column;
  }

  .focus-numbers {
    min-width: 0;
  }

  .summary-grid {
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

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .trend-summary {
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
