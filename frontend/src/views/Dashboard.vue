<script setup lang="ts">
import { onMounted, watch, computed, nextTick } from 'vue'
import { useSocketStore } from '@/stores/useSocketStore'
import { useDashboardClock } from '@/features/dashboard/composables/useDashboardClock'
import { useDashboardDeviceSelection } from '@/features/dashboard/composables/useDashboardDeviceSelection'
import { useDashboardEnergyStats } from '@/features/dashboard/composables/useDashboardEnergyStats'
import { useDashboardRealtime } from '@/features/dashboard/composables/useDashboardRealtime'
import { useECharts } from '@/shared/composables/useECharts'
import MetricCard from '@/shared/ui/MetricCard.vue'
import StatTile from '@/shared/ui/StatTile.vue'

// --- 状态定义 ---
const socketStore = useSocketStore()
const { currentTime, currentDate } = useDashboardClock()
const { currentDevice, currentDeviceId, deviceList, totalDevices, onlineDevices, loadDeviceList } = useDashboardDeviceSelection()
const { energyStats, todayEnergy, loadEnergyStats } = useDashboardEnergyStats()
const {
  displayCurrent,
  displayEnergy,
  displayPower,
  energyTrendData,
  isStorageDevice,
  realTimeData,
  storageStatus,
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
  alarmCount: 20,
  todayEnergy: todayEnergy.value
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
    caption: '已接入矿区能源网络',
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
    caption: '待接入实时告警聚合',
    tone: 'red' as const
  },
  {
    label: '今日用电',
    value: overview.value.todayEnergy.toFixed(0),
    caption: '单位 kWh',
    tone: 'purple' as const
  }
])

const energyRows = computed(() => [
  { icon: '⚡', name: '电力', tone: 'cyan', value: `${(energyStats.electricity?.total_consumption || 0).toFixed(1)} kWh` },
  { icon: '💧', name: '用水', tone: 'blue', value: `${(energyStats.water?.total_consumption || 0).toFixed(1)} m³` },
  { icon: '🔥', name: '燃气', tone: 'pink', value: `${(energyStats.gas?.total_consumption || 0).toFixed(1)} m³` },
  { icon: '♨️', name: '热力', tone: 'red', value: `${(energyStats.heat?.total_consumption || 0).toFixed(1)} GJ` },
  { icon: '❄️', name: '冷气', tone: 'purple', value: `${(energyStats.cooling?.total_consumption || 0).toFixed(1)} kWh` }
])

const liveMetricCards = computed(() => [
  {
    accent: 'cyan' as const,
    icon: '⚡',
    label: '实时功率',
    value: displayPower.value.toFixed(1),
    unit: 'kW',
    badge: isStorageDevice.value ? storageStatus.value : undefined,
    progress: Math.min(displayPower.value, 100)
  },
  {
    accent: 'green' as const,
    icon: '📊',
    label: '今日用电',
    value: displayEnergy.value.toFixed(1),
    unit: 'kWh'
  },
  {
    accent: 'pink' as const,
    icon: '🔌',
    label: 'A相电流',
    value: displayCurrent.value.toFixed(1),
    unit: 'A'
  },
  {
    accent: 'purple' as const,
    icon: '🔋',
    label: '母线电压',
    value: realTimeData.voltage.toFixed(1),
    unit: 'V'
  }
])

const selectedDeviceSummary = computed(() => ({
  name: currentDevice.value?.name || '暂无设备',
  type: currentDevice.value?.device_type || '未选择',
  energyType: currentDevice.value?.energy_type || '未知',
  status: currentDevice.value?.is_active ? '在线运行' : '离线待机'
}))

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
        </div>`
      }
    },
    grid: { left: 60, right: 30, top: 30, bottom: 30 },
    xAxis: {
      type: 'category',
      data: times.length ? times : ['--'],
      axisLine: { lineStyle: { color: '#1e3a5f' } },
      axisLabel: { color: '#8892b0', fontSize: 11 },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'value',
      name: '负荷 (kW)',
      nameTextStyle: { color: '#8892b0', fontSize: 11 },
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
        showSymbol: false,
        lineStyle: { width: 3, color: '#00f2fe' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(0,242,254,0.4)' },
              { offset: 1, color: 'rgba(0,242,254,0)' }
            ]
          }
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
    data.push({ value: 1, name: '暂无数据', itemStyle: { color: '#1e3a5f' } })
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
      textStyle: { color: '#8892b0', fontSize: 11 },
      itemWidth: 10,
      itemHeight: 10
    },
    series: [{
      type: 'pie',
      radius: ['50%', '75%'],
      center: ['35%', '50%'],
      label: { show: false },
      itemStyle: { borderColor: '#0a1628', borderWidth: 2 },
      emphasis: {
        itemStyle: { shadowBlur: 20, shadowColor: 'rgba(0,242,254,0.5)' }
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
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="grid-lines"></div>
      <div class="glow glow-1"></div>
      <div class="glow glow-2"></div>
    </div>

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
        </div>
      </div>
      
      <div class="header-right">
        <div class="status-box" :class="{ online: socketStore.isConnected }">
          <span class="status-dot"></span>
          <span class="status-text">{{ socketStore.isConnected ? '系统运行中' : '连接断开' }}</span>
        </div>
      </div>
      
      <div class="header-line"></div>
    </header>

    <!-- 主内容 -->
    <main class="main">
      <!-- 左侧面板 -->
      <aside class="panel-left">
        <!-- 系统概览 -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">系统概览</span>
            <span class="card-subtitle">System Overview</span>
          </div>
          <div class="card-body">
            <div class="stat-grid">
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

        <!-- 能源占比 -->
        <div class="card flex-1">
          <div class="card-header">
            <span class="card-title">能源消耗占比</span>
            <span class="card-subtitle">Energy Distribution</span>
          </div>
          <div class="card-body">
            <div class="chart-container" :ref="pieChart.chartRef"></div>
          </div>
        </div>

        <!-- 能源列表 -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">今日能耗</span>
            <span class="card-subtitle">Today's Consumption</span>
          </div>
          <div class="card-body">
            <div class="energy-list">
              <div v-for="item in energyRows" :key="item.name" class="energy-row">
                <span class="energy-icon" :class="item.tone">{{ item.icon }}</span>
                <div class="energy-copy">
                  <span class="energy-name">{{ item.name }}</span>
                  <span class="energy-meta">今日累计能耗</span>
                </div>
                <span class="energy-value">{{ item.value }}</span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- 中间面板 -->
      <section class="panel-center">
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
            <div class="focus-number">
              <span class="focus-number__label">当前功率</span>
              <strong>{{ displayPower.toFixed(1) }}</strong>
              <small>kW</small>
            </div>
            <div class="focus-number">
              <span class="focus-number__label">母线电压</span>
              <strong>{{ realTimeData.voltage.toFixed(1) }}</strong>
              <small>V</small>
            </div>
          </div>
        </div>

        <!-- 实时负荷仪表 -->
        <div class="card gauge-card">
          <div class="card-header">
            <span class="card-title">实时负荷</span>
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
              <span class="label">电压</span>
              <span class="value">{{ realTimeData.voltage.toFixed(1) }}<small>V</small></span>
            </div>
            <div class="gauge-stat">
              <span class="label">电流</span>
              <span class="value">{{ displayCurrent.toFixed(1) }}<small>A</small></span>
            </div>
            <div class="gauge-stat">
              <span class="label">今日用电</span>
              <span class="value">{{ displayEnergy.toFixed(1) }}<small>kWh</small></span>
            </div>
          </div>
          </div>
        </div>

        <!-- 实时负荷曲线 -->
        <div class="card flex-1">
          <div class="card-header">
            <span class="card-title">实时负荷曲线</span>
            <span class="card-subtitle">Real-time Load Curve</span>
          </div>
          <div class="card-body">
            <div class="chart-container" :ref="mainChart.chartRef"></div>
          </div>
        </div>
      </section>

      <!-- 右侧面板 -->
      <aside class="panel-right">
        <div class="metric-grid">
          <MetricCard
            v-for="item in liveMetricCards"
            :key="item.label"
            :accent="item.accent"
            :icon="item.icon"
            :label="item.label"
            :value="item.value"
            :unit="item.unit"
            :badge="item.badge"
            :progress="item.progress"
          />
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
  background: #0a1628;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow-x: hidden;
  overflow-y: auto;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* ========== 背景装饰 ========== */
.bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.grid-lines {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(0,242,254,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,242,254,0.03) 1px, transparent 1px);
  background-size: 50px 50px;
}

.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.15;
}

.glow-1 {
  width: 600px;
  height: 600px;
  background: #00f2fe;
  top: -200px;
  left: -100px;
  animation: float 20s ease-in-out infinite;
}

.glow-2 {
  width: 500px;
  height: 500px;
  background: #f093fb;
  bottom: -150px;
  right: -100px;
  animation: float 25s ease-in-out infinite reverse;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(50px, 30px); }
}

/* ========== 顶部标题栏 ========== */
.header {
  height: 80px;
  padding: 0 30px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  z-index: 10;
  background: linear-gradient(180deg, rgba(10,22,40,0.95) 0%, rgba(10,22,40,0.8) 100%);
}

.header-line {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00f2fe, #4facfe, #00f2fe, transparent);
}

.title-box {
  display: flex;
  align-items: center;
  gap: 15px;
}

.title-icon {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 30px rgba(0,242,254,0.4);
}

.title-icon svg {
  width: 28px;
  height: 28px;
  color: white;
}

.title-text h1 {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(90deg, #fff 0%, #00f2fe 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: 3px;
}

.title-text span {
  font-size: 11px;
  color: #4a5568;
  letter-spacing: 1px;
}

.time-box {
  text-align: center;
}

.time-box .time {
  font-size: 32px;
  font-weight: 700;
  font-family: 'DIN', 'Monaco', monospace;
  color: #00f2fe;
  text-shadow: 0 0 20px rgba(0,242,254,0.5);
  letter-spacing: 4px;
}

.time-box .date {
  font-size: 13px;
  color: #8892b0;
  margin-top: 2px;
}

.status-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  background: rgba(239,68,68,0.15);
  border: 1px solid rgba(239,68,68,0.3);
  border-radius: 25px;
  transition: all 0.3s;
}

.status-box.online {
  background: rgba(0,242,254,0.15);
  border-color: rgba(0,242,254,0.3);
}

.status-dot {
  width: 10px;
  height: 10px;
  background: #ef4444;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.status-box.online .status-dot {
  background: #00f2fe;
  box-shadow: 0 0 10px #00f2fe;
}

.status-text {
  font-size: 13px;
  color: #ef4444;
}

.status-box.online .status-text {
  color: #00f2fe;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ========== 主内容区 ========== */
.main {
  flex: 1;
  display: grid;
  grid-template-columns: 300px 1fr 320px;
  gap: 20px;
  padding: 20px;
  position: relative;
  z-index: 10;
  min-height: 600px;
}

/* ========== 通用卡片样式 ========== */
.card {
  position: relative;
  background: rgba(10,22,40,0.8);
  border: 1px solid rgba(0,242,254,0.2);
  border-radius: 18px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(18px);
  box-shadow: 0 18px 50px rgba(1, 9, 24, 0.22);
}

.card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00f2fe, transparent);
}

.card-header {
  padding: 15px 20px;
  border-bottom: 1px solid rgba(0,242,254,0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
}

.card-subtitle {
  font-size: 11px;
  color: #4a5568;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.card-body {
  flex: 1;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
}

.flex-1 { flex: 1; }

/* ========== 左侧面板 ========== */
.panel-left {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.stat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
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
  padding: 12px 14px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
}

.energy-icon {
  font-size: 18px;
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.06);
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

.energy-icon.cyan { color: #00f2fe; }
.energy-icon.blue { color: #4facfe; }
.energy-icon.pink { color: #f093fb; }
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
  gap: 15px;
}

.focus-strip {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: stretch;
  padding: 20px 24px;
  border-radius: 22px;
  background:
    radial-gradient(circle at top left, rgba(0,242,254,0.12), transparent 38%),
    radial-gradient(circle at bottom right, rgba(167,139,250,0.14), transparent 30%),
    rgba(8, 17, 34, 0.84);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 20px 55px rgba(1, 9, 24, 0.22);
}

.focus-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.focus-eyebrow {
  font-size: 11px;
  color: #7b8da9;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.focus-copy h2 {
  margin: 10px 0 8px;
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
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.06);
  color: #93a6c3;
  font-size: 12px;
}

.focus-meta .online {
  color: #00f2fe;
  background: rgba(0,242,254,0.09);
}

.focus-numbers {
  display: grid;
  grid-template-columns: repeat(2, minmax(120px, 1fr));
  gap: 12px;
  min-width: 280px;
}

.focus-number {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.05);
}

.focus-number__label {
  font-size: 12px;
  color: #8396b2;
}

.focus-number strong {
  margin-top: 8px;
  font-size: 30px;
  line-height: 1;
  color: #fff;
  font-family: 'DIN', 'Monaco', monospace;
}

.focus-number small {
  margin-top: 6px;
  font-size: 12px;
  color: #7d90ab;
}

.gauge-card .card-body {
  flex-direction: row;
  align-items: center;
  gap: 30px;
}

.gauge-wrapper {
  position: relative;
  width: 200px;
  height: 180px;
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
  font-size: 16px;
  color: #8892b0;
}

.gauge-stats {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.gauge-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: rgba(0,242,254,0.05);
  border-radius: 8px;
  border-left: 3px solid #00f2fe;
}

.gauge-stat .label {
  font-size: 13px;
  color: #8892b0;
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
  flex: 1;
  width: 100%;
  min-height: 200px;
}

/* ========== 右侧面板 ========== */
.panel-right {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.metric-grid {
  display: grid;
  gap: 14px;
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
  background: rgba(255,255,255,0.03);
  border-radius: 12px;
  border-left: 3px solid #ef4444;
}

.device-item.active {
  border-left-color: #00f2fe;
}

.device-status {
  width: 8px;
  height: 8px;
  background: #ef4444;
  border-radius: 50%;
}

.device-item.active .device-status {
  background: #00f2fe;
  box-shadow: 0 0 8px #00f2fe;
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
  background: rgba(255,255,255,0.05);
  border-radius: 10px;
}

.device-empty {
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #7f8ea7;
  border: 1px dashed rgba(255,255,255,0.08);
  border-radius: 14px;
  background: rgba(255,255,255,0.02);
}

/* ========== 响应式 ========== */
@media (max-width: 1400px) {
  .main {
    grid-template-columns: 260px 1fr 280px;
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
  
  .metric-grid {
    flex: 1;
    min-width: 280px;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .panel-right .metric-grid {
    flex: 1;
  }

  .focus-strip {
    flex-direction: column;
  }

  .focus-numbers {
    min-width: 0;
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

  .metric-grid {
    grid-template-columns: 1fr;
    min-width: 0;
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
}
</style>
