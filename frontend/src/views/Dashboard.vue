<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, reactive, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getDevices, type Device } from '@/api/device'
import { getHistory, getAnalysis } from '@/api/telemetry'
import { getEnergyStatistics, type EnergyStatistics } from '@/api/energy'
import { useSocketStore } from '@/stores/useSocketStore'

// --- 状态定义 ---
const socketStore = useSocketStore()
const currentDeviceId = ref<number | undefined>(undefined)
const deviceList = ref<Device[]>([])

// 图表引用
const mainChartRef = ref<HTMLElement | null>(null)
const gaugeChartRef = ref<HTMLElement | null>(null)
const pieChartRef = ref<HTMLElement | null>(null)
let mainChart: echarts.ECharts | null = null
let gaugeChart: echarts.ECharts | null = null
let pieChart: echarts.ECharts | null = null

// 当前时间
const currentTime = ref('')
const currentDate = ref('')
let timeTimer: ReturnType<typeof setInterval> | null = null

// 能源统计
const energyStats = reactive<Record<string, EnergyStatistics>>({})

// 实时数据
const realTimeData = reactive({
  power: 0,
  energy: 0,
  current: 0,
  voltage: 0
})

// 当前设备是否是储能设备
const isStorageDevice = computed(() => {
  const device = deviceList.value.find(d => d.id === currentDeviceId.value)
  return device?.device_type === 'storage'
})

// 储能设备状态（充电/放电）
const storageStatus = computed(() => {
  if (!isStorageDevice.value) return ''
  return realTimeData.power < 0 ? '充电中' : '放电中'
})

// 显示用的功率值（绝对值）
const displayPower = computed(() => Math.abs(realTimeData.power))
const displayCurrent = computed(() => Math.abs(realTimeData.current))
const displayEnergy = computed(() => Math.abs(realTimeData.energy))

// 系统概览
const overview = reactive({
  totalDevices: 0,
  onlineDevices: 0,
  alarmCount: 20,
  todayEnergy: 0
})

// 计算属性
const onlineRate = computed(() => {
  if (overview.totalDevices === 0) return 0
  return Math.round((overview.onlineDevices / overview.totalDevices) * 100)
})

// 更新时间
const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', { hour12: false })
  currentDate.value = now.toLocaleDateString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    weekday: 'long'
  })
}

// 用电趋势数据（今日用电量累计曲线）
const energyTrendData = reactive<{ times: string[], values: number[] }>({
  times: [],
  values: []
})

// --- 初始化 ---
onMounted(async () => {
  socketStore.connect()
  updateTime()
  timeTimer = setInterval(updateTime, 1000)
  
  // 等待 DOM 渲染完成
  await nextTick()
  
  // 初始化图表
  initCharts()
  
  // 加载数据
  await loadDeviceList()  // 这里面会调用 loadDeviceData，加载用电曲线
  await loadEnergyStats()
})

onUnmounted(() => {
  if (timeTimer) clearInterval(timeTimer)
  window.removeEventListener('resize', handleResize)
  mainChart?.dispose()
  gaugeChart?.dispose()
  pieChart?.dispose()
})

const initCharts = () => {
  if (mainChartRef.value) mainChart = echarts.init(mainChartRef.value)
  if (gaugeChartRef.value) gaugeChart = echarts.init(gaugeChartRef.value)
  if (pieChartRef.value) pieChart = echarts.init(pieChartRef.value)
  window.addEventListener('resize', handleResize)
  
  renderGauge(0)
  renderPieChart()
  // 主图表会在 loadPowerTrend 后渲染
}

const handleResize = () => {
  setTimeout(() => {
    mainChart?.resize()
    gaugeChart?.resize()
    pieChart?.resize()
  }, 100)
}

// --- 数据加载 ---
const loadDeviceList = async () => {
  try {
    const res = await getDevices()
    deviceList.value = res
    overview.totalDevices = res.length
    overview.onlineDevices = res.filter(d => d.is_active).length
    
    if (res.length > 0) {
      // 优先选择普通用电设备（load类型），避免储能设备显示负值
      const loadDevice = res.find(d => d.device_type === 'load')
      currentDeviceId.value = loadDevice?.id || res[0].id
      await loadDeviceData()
    }
  } catch (e) {
    console.error('加载设备失败:', e)
  }
}

const loadDeviceData = async () => {
  if (!currentDeviceId.value) return
  
  try {
    // 加载设备分析数据
    const analysis = await getAnalysis(currentDeviceId.value)
    realTimeData.power = analysis.current_power || 0
    realTimeData.energy = analysis.today_energy || 0
    realTimeData.current = analysis.current || 0
    realTimeData.voltage = analysis.voltage || 0
    
    // 仪表盘使用绝对值
    renderGauge(Math.abs(realTimeData.power))
    
    // 加载该设备的今日用电曲线
    await loadEnergyTrend()
  } catch (e) {
    console.error('加载设备数据失败:', e)
  }
}

// 加载实时负荷曲线（当前选中设备）
const loadEnergyTrend = async () => {
  if (!currentDeviceId.value) return
  
  try {
    console.log('📈 加载设备负荷曲线, ID:', currentDeviceId.value)
    const history = await getHistory(currentDeviceId.value, 100)
    
    if (history && history.length > 0) {
      console.log('✅ 获取到', history.length, '条历史数据')
      
      // 按时间正序处理（API返回的是倒序）
      const sortedHistory = [...history].reverse()
      
      // 使用 flow_rate（实时功率 kW）
      energyTrendData.times = sortedHistory.map((d: any) => d.timestamp?.substring(11, 19) || '')
      energyTrendData.values = sortedHistory.map((d: any) => Math.abs(d.flow_rate || 0))
      
      console.log('📊 负荷数据:', energyTrendData.values.slice(-5))
      renderMainChart()
    } else {
      console.log('⚠️ 无历史数据')
      energyTrendData.times = []
      energyTrendData.values = []
      renderMainChart()
    }
  } catch (e) {
    console.error('❌ 加载负荷曲线失败:', e)
  }
}

const loadEnergyStats = async () => {
  try {
    const today = new Date()
    const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
    
    const types = ['electricity', 'water', 'gas', 'heat', 'cooling']
    const results = await Promise.all(
      types.map(async (type) => {
        try {
          const stats = await getEnergyStatistics({
            energy_type: type,
            start_time: `${dateStr}T00:00:00`,
            end_time: `${dateStr}T23:59:59`
          })
          return { type, stats }
        } catch {
          return { type, stats: { total_consumption: 0, data_count: 0 } as EnergyStatistics }
        }
      })
    )
    
    results.forEach(({ type, stats }) => {
      energyStats[type] = stats
    })
    
    overview.todayEnergy = energyStats.electricity?.total_consumption || 0
    
    await nextTick()
    renderPieChart()
  } catch (e) {
    console.error('加载能源统计失败:', e)
  }
}


// --- 图表渲染 ---
const renderGauge = (value: number) => {
  if (!gaugeChart) return
  
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
  gaugeChart.setOption(option)
}

const renderMainChart = () => {
  if (!mainChart) {
    console.warn('⚠️ mainChart 未初始化')
    return
  }
  
  const { times, values } = energyTrendData
  console.log('📊 渲染负荷曲线:', times.length, '个数据点')
  
  // 获取当前设备名称
  const device = deviceList.value.find(d => d.id === currentDeviceId.value)
  const deviceName = device?.name || '设备'
  
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
  mainChart.setOption(option, true)
}

const renderPieChart = () => {
  if (!pieChart) return
  
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
  pieChart.setOption(option)
}

// --- WebSocket 实时更新 ---
watch(() => socketStore.latestMessage, (msg) => {
  if (msg?.type === 'telemetry_update') {
    const data = msg.data
    
    // 只处理当前选中设备的数据
    if (data.device_id === currentDeviceId.value) {
      // 更新仪表盘数据
      realTimeData.power = data.power || 0
      realTimeData.current = data.current || 0
      realTimeData.voltage = data.voltage || 0
      renderGauge(Math.abs(realTimeData.power))
      
      // 更新实时负荷曲线（追加新的功率点）
      const time = data.timestamp?.substring(11, 19) || new Date().toTimeString().substring(0, 8)
      const power = Math.abs(data.power || 0)
      
      energyTrendData.times.push(time)
      energyTrendData.values.push(power)
      
      // 保持最近100个点
      if (energyTrendData.times.length > 100) {
        energyTrendData.times.shift()
        energyTrendData.values.shift()
      }
      
      renderMainChart()
    }
  }
})
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
              <div class="stat-item">
                <div class="stat-value cyan">{{ overview.totalDevices }}</div>
                <div class="stat-label">设备总数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value green">{{ onlineRate }}%</div>
                <div class="stat-label">在线率</div>
              </div>
              <div class="stat-item">
                <div class="stat-value red">{{ overview.alarmCount }}</div>
                <div class="stat-label">告警数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value purple">{{ overview.todayEnergy.toFixed(0) }}</div>
                <div class="stat-label">今日用电</div>
              </div>
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
            <div class="chart-container" ref="pieChartRef"></div>
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
              <div class="energy-row">
                <span class="energy-icon cyan">⚡</span>
                <span class="energy-name">电力</span>
                <span class="energy-value">{{ (energyStats.electricity?.total_consumption || 0).toFixed(1) }} kWh</span>
              </div>
              <div class="energy-row">
                <span class="energy-icon blue">💧</span>
                <span class="energy-name">用水</span>
                <span class="energy-value">{{ (energyStats.water?.total_consumption || 0).toFixed(1) }} m³</span>
              </div>
              <div class="energy-row">
                <span class="energy-icon pink">🔥</span>
                <span class="energy-name">燃气</span>
                <span class="energy-value">{{ (energyStats.gas?.total_consumption || 0).toFixed(1) }} m³</span>
              </div>
              <div class="energy-row">
                <span class="energy-icon red">♨️</span>
                <span class="energy-name">热力</span>
                <span class="energy-value">{{ (energyStats.heat?.total_consumption || 0).toFixed(1) }} GJ</span>
              </div>
              <div class="energy-row">
                <span class="energy-icon purple">❄️</span>
                <span class="energy-name">冷气</span>
                <span class="energy-value">{{ (energyStats.cooling?.total_consumption || 0).toFixed(1) }} kWh</span>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- 中间面板 -->
      <section class="panel-center">
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
              <div class="gauge-chart" ref="gaugeChartRef"></div>
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
            <div class="chart-container" ref="mainChartRef"></div>
          </div>
        </div>
      </section>

      <!-- 右侧面板 -->
      <aside class="panel-right">
        <!-- 实时数据卡片 -->
        <div class="data-card cyan">
          <div class="data-card-bg"></div>
          <div class="data-card-content">
            <div class="data-icon">⚡</div>
            <div class="data-info">
              <span class="data-label">实时功率 <span v-if="isStorageDevice" class="storage-tag">{{ storageStatus }}</span></span>
              <span class="data-value">{{ displayPower.toFixed(1) }}<small>kW</small></span>
            </div>
          </div>
          <div class="data-bar">
            <div class="data-bar-fill" :style="{ width: Math.min(displayPower, 100) + '%' }"></div>
          </div>
        </div>

        <div class="data-card green">
          <div class="data-card-bg"></div>
          <div class="data-card-content">
            <div class="data-icon">📊</div>
            <div class="data-info">
              <span class="data-label">今日用电</span>
              <span class="data-value">{{ displayEnergy.toFixed(1) }}<small>kWh</small></span>
            </div>
          </div>
        </div>

        <div class="data-card pink">
          <div class="data-card-bg"></div>
          <div class="data-card-content">
            <div class="data-icon">🔌</div>
            <div class="data-info">
              <span class="data-label">A相电流</span>
              <span class="data-value">{{ displayCurrent.toFixed(1) }}<small>A</small></span>
            </div>
          </div>
        </div>

        <div class="data-card purple">
          <div class="data-card-bg"></div>
          <div class="data-card-content">
            <div class="data-icon">🔋</div>
            <div class="data-info">
              <span class="data-label">母线电压</span>
              <span class="data-value">{{ realTimeData.voltage.toFixed(1) }}<small>V</small></span>
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
            <div class="device-list">
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
  background: rgba(10,22,40,0.8);
  border: 1px solid rgba(0,242,254,0.2);
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(10px);
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
  padding: 15px 20px;
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

.stat-item {
  background: rgba(0,242,254,0.05);
  border: 1px solid rgba(0,242,254,0.1);
  border-radius: 8px;
  padding: 15px;
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  font-family: 'DIN', 'Monaco', monospace;
}

.stat-value.cyan { color: #00f2fe; }
.stat-value.green { color: #10b981; }
.stat-value.red { color: #ef4444; }
.stat-value.purple { color: #a78bfa; }

.stat-label {
  font-size: 12px;
  color: #8892b0;
  margin-top: 5px;
}

.energy-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.energy-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: rgba(255,255,255,0.02);
  border-radius: 6px;
}

.energy-icon {
  font-size: 18px;
}

.energy-name {
  flex: 1;
  font-size: 13px;
  color: #8892b0;
}

.energy-value {
  font-size: 14px;
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
  gap: 12px;
}

.data-card {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(10,22,40,0.8);
  border: 1px solid rgba(255,255,255,0.1);
}

.data-card-bg {
  position: absolute;
  inset: 0;
  opacity: 0.1;
  transition: opacity 0.3s;
}

.data-card:hover .data-card-bg {
  opacity: 0.2;
}

.data-card.cyan { border-color: rgba(0,242,254,0.3); }
.data-card.cyan .data-card-bg { background: linear-gradient(135deg, #00f2fe, transparent); }

.data-card.green { border-color: rgba(16,185,129,0.3); }
.data-card.green .data-card-bg { background: linear-gradient(135deg, #10b981, transparent); }

.data-card.pink { border-color: rgba(240,147,251,0.3); }
.data-card.pink .data-card-bg { background: linear-gradient(135deg, #f093fb, transparent); }

.data-card.purple { border-color: rgba(167,139,250,0.3); }
.data-card.purple .data-card-bg { background: linear-gradient(135deg, #a78bfa, transparent); }

.data-card-content {
  position: relative;
  padding: 15px;
  display: flex;
  align-items: center;
  gap: 15px;
}

.data-icon {
  font-size: 24px;
}

.data-info {
  flex: 1;
}

.data-label {
  display: block;
  font-size: 12px;
  color: #8892b0;
}

.data-value {
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  font-family: 'DIN', 'Monaco', monospace;
}

.data-value small {
  font-size: 12px;
  color: #8892b0;
  margin-left: 3px;
}

.storage-tag {
  font-size: 10px;
  padding: 2px 6px;
  background: rgba(240, 147, 251, 0.2);
  color: #f093fb;
  border-radius: 10px;
  margin-left: 5px;
}

.data-bar {
  height: 3px;
  background: rgba(255,255,255,0.1);
}

.data-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #00f2fe, #4facfe);
  transition: width 0.5s ease;
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
  background: rgba(255,255,255,0.02);
  border-radius: 6px;
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
  
  .panel-right .data-card {
    flex: 1;
    min-width: 200px;
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
}
</style>
