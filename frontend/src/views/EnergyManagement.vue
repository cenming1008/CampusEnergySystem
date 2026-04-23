<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { echarts } from '@/shared/lib/echarts'
import { ElMessage } from 'element-plus'
import {
  getCarbonEmissions,
  getEnergyTypes,
  getEnergyData,
  getEnergyOverview,
  getCarbonSummary,
  getCarbonFactors,
  calculateCarbon,
  saveEnergyData,
  type CarbonEmission,
  type EnergyData,
  type EnergyTypeInfo,
  type EnergyStatistics,
  type CarbonSummary,
  type CarbonFactor,
  type EnergyOverview
} from '@/api/energy'
import { getDevices, type Device } from '@/api/device'
import { useAuthStore } from '@/stores/useAuthStore'
import { usePermissions } from '@/shared/composables/usePermissions'

// ==================== 状态定义 ====================

const energyTypes = ref<EnergyTypeInfo[]>([])
const selectedEnergyType = ref<string>('electricity')
const deviceList = ref<Device[]>([])
const dateRange = ref<[Date, Date]>([
  new Date(new Date().getTime() - 7 * 24 * 3600 * 1000),
  new Date()
])

const statistics = ref<{ [key: string]: EnergyStatistics }>({})
const overviewMeta = ref<EnergyOverview | null>(null)
const carbonSummary = ref<CarbonSummary | null>(null)
const carbonFactors = ref<Record<string, CarbonFactor>>({})
const loading = ref(false)
const detailLoading = ref(false)
const detailDeviceId = ref<number | undefined>(undefined)
const energyDetails = ref<EnergyData[]>([])
const carbonDetails = ref<CarbonEmission[]>([])
const entryDialogVisible = ref(false)
const authStore = useAuthStore()
const { hasScopedAccess } = usePermissions()

interface CarbonCalculationResult {
  energy_type: string
  consumption: number
  consumption_unit: string
  carbon_factor: number
  carbon_emission: number
  emission_unit: string
}

const comparisonChartRef = ref<HTMLElement | null>(null)
const carbonChartRef = ref<HTMLElement | null>(null)
let comparisonChart: echarts.ECharts | null = null
let carbonChart: echarts.ECharts | null = null
let refreshTimer: ReturnType<typeof setTimeout> | null = null
const secondaryPanelActive = ref<string[]>([])

const carbonCalculator = ref({
  energy_type: 'electricity',
  consumption: 0,
  result: null as CarbonCalculationResult | null
})

const entryForm = ref({
  device_id: undefined as number | undefined,
  energy_type: 'electricity',
  consumption: 0,
  flow_rate: 0,
  timestamp: '',
})

// ==================== 颜色映射 ====================

const typeColorMap: Record<string, string> = {
  electricity: '#5eead4',
  water: '#7ab8ff',
  gas: '#f7b267',
  heat: '#fb7185',
  cooling: '#b794f6',
  steam: '#a78bfa',
}
const typeColor = (key: string) => typeColorMap[key] || '#94a3b8'

// ==================== 计算属性 ====================

const formatDateRange = computed(() => {
  if (!dateRange.value) return ['', '']

  const formatLocalDateTime = (date: Date) => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')
    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`
  }

  const startDate = new Date(dateRange.value[0])
  startDate.setHours(0, 0, 0, 0)

  const endDate = new Date(dateRange.value[1])
  endDate.setHours(23, 59, 59, 999)

  return [formatLocalDateTime(startDate), formatLocalDateTime(endDate)]
})

const currentStats = computed(() => {
  return statistics.value[selectedEnergyType.value] || {
    total_consumption: 0,
    avg_consumption: 0,
    avg_flow_rate: 0,
    peak_flow_rate: 0,
    data_count: 0
  }
})

const currentEnergyInfo = computed(() => {
  return energyTypes.value.find(t => t.value === selectedEnergyType.value) || {
    value: '',
    label: '',
    unit: ''
  }
})

const currentEnergyProfile = computed(() => {
  return overviewMeta.value?.energy_profiles?.[selectedEnergyType.value] || currentEnergyInfo.value
})

const hasSteamRuntimePresence = computed(() => {
  const steamStats = statistics.value.steam
  const hasSteamDevice = deviceList.value.some((device) => device.energy_type === 'steam')
  const hasSteamStats = Boolean(
    steamStats && (
      steamStats.data_count > 0 ||
      steamStats.total_consumption > 0 ||
      steamStats.avg_flow_rate > 0 ||
      steamStats.peak_flow_rate > 0
    )
  )
  const steamCarbon = carbonSummary.value?.by_energy_type?.steam
  const hasSteamCarbon = Boolean(
    steamCarbon && (steamCarbon.energy_consumption > 0 || steamCarbon.carbon_emission > 0)
  )
  return hasSteamDevice || hasSteamStats || hasSteamCarbon
})

const visibleEnergyTypes = computed(() => {
  return energyTypes.value.filter((type) => type.value !== 'steam' || hasSteamRuntimePresence.value)
})

const scopeDescription = computed(() => {
  if (!authStore.locationScope) {
    return '当前统计默认展示当前账号可见的全部设备数据。'
  }
  return `当前账号的位置范围为 ${authStore.locationScope}，页面中的能耗与碳排放数据已由后端按该范围过滤。`
})

const visibleDeviceCount = computed(() => deviceList.value.length)
const detailDeviceName = computed(() => {
  if (!detailDeviceId.value) return '全部设备'
  return deviceList.value.find((item) => item.id === detailDeviceId.value)?.name || `设备 ${detailDeviceId.value}`
})

const selectedDevice = computed(() => {
  if (!detailDeviceId.value) return null
  return deviceList.value.find((item) => item.id === detailDeviceId.value) || null
})

const activeEnergyCount = computed(() => {
  return visibleEnergyTypes.value.filter((type) => {
    const stats = statistics.value[type.value]
    const carbon = carbonSummary.value?.by_energy_type?.[type.value]
    return Boolean(
      stats && (
        stats.data_count > 0 ||
        stats.total_consumption > 0 ||
        stats.avg_flow_rate > 0 ||
        stats.peak_flow_rate > 0
      )
    ) || Boolean(carbon && (carbon.energy_consumption > 0 || carbon.carbon_emission > 0))
  }).length
})

const deviceEntryDescription = computed(() => {
  if (!detailDeviceId.value) {
    return '先选择设备，再查看该设备在当前时间范围内的能耗与碳排明细。'
  }
  if (selectedDevice.value) {
    return `当前明细设备：${selectedDevice.value.name}，能源类型：${selectedDevice.value.energy_type || '未标注'}。`
  }
  return '当前明细已切换到指定设备。'
})

const formatBooleanRule = (value?: boolean) => {
  if (value == null) return '未声明'
  return value ? '允许' : '不允许'
}

const formatListText = (items?: string[]) => {
  if (!items?.length) return '暂无'
  return items.join(' / ')
}

const formatMetricValue = (value?: number, digits = 1) => {
  return Number.isFinite(value) ? Number(value).toFixed(digits) : '0.0'
}

const currentRangeLabel = computed(() => {
  if (!dateRange.value?.length) return '最近 7 天'
  const [start, end] = dateRange.value
  const format = (date: Date) => `${date.getMonth() + 1}/${date.getDate()}`
  return `${format(start)} – ${format(end)}`
})

const totalEnergyConsumption = computed(() => {
  return visibleEnergyTypes.value.reduce((sum, type) => {
    return sum + (statistics.value[type.value]?.total_consumption || 0)
  }, 0)
})

const energyMixItems = computed(() => {
  const items = visibleEnergyTypes.value
    .map((type) => {
      const stats = statistics.value[type.value]
      const value = stats?.total_consumption || 0
      return {
        key: type.value,
        label: type.label,
        unit: type.unit,
        value,
        color: typeColorMap[type.value] || '#94a3b8',
      }
    })
    .filter((item) => item.value > 0)

  const total = items.reduce((sum, item) => sum + item.value, 0)

  return items.map((item) => ({
    ...item,
    percent: total > 0 ? (item.value / total) * 100 : 0,
  }))
})

const selectedEnergyShare = computed(() => {
  if (totalEnergyConsumption.value <= 0) return 0
  return (currentStats.value.total_consumption / totalEnergyConsumption.value) * 100
})

const overviewMetrics = computed(() => [
  {
    label: '活跃能源',
    value: String(activeEnergyCount.value),
    unit: '类',
    caption: '当前运行态已产生统计或碳排数据',
    accent: 'kpi-tile--energy',
  },
  {
    label: '总能耗汇总',
    value: formatMetricValue(totalEnergyConsumption.value, 2),
    unit: currentEnergyInfo.value.unit || 'kWh',
    caption: '按各能源自身口径分别统计后聚合',
    accent: 'kpi-tile--load',
  },
  {
    label: '总碳排',
    value: formatMetricValue(carbonSummary.value?.total_carbon || 0, 2),
    unit: 'kg CO₂',
    caption: '当前范围内多能源阶段汇总',
    accent: 'kpi-tile--carbon',
  },
  {
    label: '设备入口',
    value: String(visibleDeviceCount.value),
    unit: '台',
    caption: detailDeviceId.value ? `已选 ${detailDeviceName.value}` : '支持按设备下钻查看明细',
    accent: 'kpi-tile--device',
  },
])

const focusHighlights = computed(() => [
  {
    label: '焦点占比',
    value: `${selectedEnergyShare.value.toFixed(1)}%`,
    hint: '占当前多能源总量',
  },
  {
    label: '峰值流量',
    value: `${formatMetricValue(currentStats.value.peak_flow_rate, 2)} ${currentEnergyInfo.value.flow_unit || currentEnergyInfo.value.unit || ''}`.trim(),
    hint: '当前时间范围内最高瞬时值',
  },
  {
    label: '采样条数',
    value: `${currentStats.value.data_count} 条`,
    hint: '用于当前焦点统计的记录数',
  },
])

const carbonMetaItems = computed(() => {
  if (!carbonSummary.value) return []
  return [
    { label: '碳汇总边界', value: carbonSummary.value.boundary || '未声明' },
    { label: '计算方法', value: carbonSummary.value.calculation_method || '未声明' },
    { label: '汇总依据', value: carbonSummary.value.summary_basis || '未声明' },
    { label: '核算等级', value: carbonSummary.value.is_accounting_grade ? '正式核算' : '展示估算' },
    { label: '说明', value: carbonSummary.value.note || '未声明' },
  ]
})

const secondaryOverviewItems = computed(() => {
  const meta = overviewMeta.value
  if (!meta) return []
  return [
    { label: '总览边界', value: meta.overview_boundary || '未声明' },
    { label: '统计口径', value: meta.unit_rule || '未声明' },
    { label: '跨能源混算', value: formatBooleanRule(meta.cross_energy_mix_allowed) },
    { label: '字段边界', value: meta.field_boundary_rule || '未声明' },
    { label: '累计量语义', value: currentStats.value.consumption_semantics || currentEnergyInfo.value.consumption_semantics || '未声明' },
    { label: '瞬时量语义', value: currentStats.value.flow_semantics || currentEnergyInfo.value.flow_semantics || '未声明' },
  ]
})

// ==================== 数据加载 ====================

const loadEnergyTypes = async () => {
  try {
    const res = await getEnergyTypes()
    energyTypes.value = res.energy_types
    if (energyTypes.value.length > 0 && !selectedEnergyType.value) {
      selectedEnergyType.value = energyTypes.value[0].value
    }
  } catch (e) {
    ElMessage.error('加载能源类型失败')
    throw e
  }
}

const loadDevices = async () => {
  try {
    deviceList.value = await getDevices()
  } catch {
    // 由 axios 拦截器统一提示
  }
}

const loadCarbonFactors = async () => {
  try {
    const res = await getCarbonFactors()
    carbonFactors.value = res.carbon_factors
  } catch {
    // 碳排放因子加载失败
  }
}

const loadOverview = async () => {
  loading.value = true
  try {
    const [startTime, endTime] = formatDateRange.value
    if (!startTime || !endTime) {
      ElMessage.error('时间参数无效')
      return
    }
    const overview = await getEnergyOverview({
      start_time: startTime,
      end_time: endTime,
      device_id: detailDeviceId.value,
    })
    overviewMeta.value = overview
    statistics.value = overview.statistics
    carbonSummary.value = overview.carbon_summary
    renderComparisonChart()
    renderCarbonChart()
  } catch (e) {
    ElMessage.error('加载数据失败: ' + (e as Error).message)
  } finally {
    loading.value = false
  }
}

const refreshData = async () => {
  try {
    await Promise.all([loadOverview(), loadDetailData()])
  } catch {
    // 刷新时部分失败由各子函数处理
  }
}

const loadDetailData = async () => {
  const [startTime, endTime] = formatDateRange.value
  if (!startTime || !endTime) return

  if (!detailDeviceId.value) {
    energyDetails.value = []
    carbonDetails.value = []
    return
  }

  detailLoading.value = true
  try {
    energyDetails.value = await getEnergyData({
      device_id: detailDeviceId.value,
      energy_type: selectedEnergyType.value,
      start_time: startTime,
      end_time: endTime,
      limit: 50
    })
    carbonDetails.value = await getCarbonEmissions({
      device_id: detailDeviceId.value,
      energy_type: selectedEnergyType.value,
      start_time: startTime,
      end_time: endTime,
      limit: 100
    })
  } catch {
    ElMessage.error('加载能源明细失败')
  } finally {
    detailLoading.value = false
  }
}

// ==================== 图表渲染 ====================

const renderComparisonChart = () => {
  if (!comparisonChart || !comparisonChartRef.value) return

  const data = visibleEnergyTypes.value.map(type => ({
    name: type.label,
    value: statistics.value[type.value]?.total_consumption || 0,
    unit: type.unit
  })).filter(item => item.value > 0)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: 'rgba(0,0,0,0.8)',
      borderColor: '#5eead4',
      textStyle: { color: '#f0f6ff' }
    },
    legend: {
      show: false
    },
    series: [{
      name: '能源消耗',
      type: 'pie',
      radius: ['42%', '72%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 6,
        borderColor: 'rgba(9,14,23,0.8)',
        borderWidth: 2
      },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#f0f6ff' },
        itemStyle: { shadowBlur: 14, shadowColor: 'rgba(94,234,212,0.22)' }
      },
      labelLine: { show: false },
      data,
      color: Object.values(typeColorMap)
    }]
  }

  comparisonChart.setOption(option)
}

const renderCarbonChart = () => {
  if (!carbonChart || !carbonChartRef.value || !carbonSummary.value) return

  const data = Object.entries(carbonSummary.value.by_energy_type).map(([type, info]) => {
    if (type === 'steam' && !hasSteamRuntimePresence.value) return null
    const typeInfo = energyTypes.value.find(t => t.value === type)
    return {
      name: typeInfo?.label || type,
      value: info.carbon_emission
    }
  }).filter((item): item is { name: string; value: number } => Boolean(item && item.value > 0))

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(0,0,0,0.8)',
      borderColor: '#fb7185',
      textStyle: { color: '#f0f6ff' }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map(d => d.name),
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisLabel: { color: 'rgba(255,255,255,0.45)', fontSize: 11 },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      name: 'kg CO₂',
      nameTextStyle: { color: 'rgba(255,255,255,0.35)', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'dashed' } },
      axisLabel: { color: 'rgba(255,255,255,0.4)', fontSize: 10 }
    },
    series: [{
      name: '碳排放',
      type: 'bar',
      data: data.map(d => d.value),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#fb7185' },
          { offset: 1, color: 'rgba(251,113,133,0.3)' }
        ]),
        borderRadius: [6, 6, 0, 0]
      },
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#fda4af' },
            { offset: 1, color: 'rgba(251,113,133,0.5)' }
          ])
        }
      }
    }]
  }

  carbonChart.setOption(option)
}

const initCharts = () => {
  if (comparisonChartRef.value) {
    comparisonChart = echarts.init(comparisonChartRef.value)
    window.addEventListener('resize', () => comparisonChart?.resize())
  }
  if (carbonChartRef.value) {
    carbonChart = echarts.init(carbonChartRef.value)
    window.addEventListener('resize', () => carbonChart?.resize())
  }
}

// ==================== 碳排放计算器 ====================

const handleCalculateCarbon = async () => {
  try {
    const res = await calculateCarbon({
      energy_type: carbonCalculator.value.energy_type,
      consumption: carbonCalculator.value.consumption
    })
    carbonCalculator.value.result = res
    ElMessage.success('计算完成')
  } catch {
    ElMessage.error('计算失败')
  }
}

const openEntryDialog = () => {
  entryForm.value = {
    device_id: detailDeviceId.value,
    energy_type: selectedEnergyType.value,
    consumption: 0,
    flow_rate: 0,
    timestamp: new Date().toISOString().slice(0, 19),
  }
  entryDialogVisible.value = true
}

const handleSaveEntry = async () => {
  if (entryForm.value.device_id == null) {
    ElMessage.warning('请选择要补录的设备')
    return
  }
  try {
    await saveEnergyData({
      device_id: entryForm.value.device_id,
      energy_type: entryForm.value.energy_type,
      consumption: entryForm.value.consumption,
      flow_rate: entryForm.value.flow_rate,
      timestamp: entryForm.value.timestamp
    })
    ElMessage.success('补录成功')
    entryDialogVisible.value = false
    await refreshData()
  } catch {
    ElMessage.error('补录失败')
  }
}

// ==================== 生命周期 ====================

onMounted(async () => {
  try {
    await loadEnergyTypes()
    await loadDevices()
    await loadCarbonFactors()
    initCharts()
    await new Promise(resolve => setTimeout(resolve, 100))
    await refreshData()
  } catch {
    ElMessage.error('页面初始化失败，请刷新重试')
  }
})

watch(selectedEnergyType, () => { loadDetailData() })

watch(visibleEnergyTypes, (types) => {
  if (!types.length) return
  if (!types.some((item) => item.value === selectedEnergyType.value)) {
    selectedEnergyType.value = types[0].value
  }
  if (!types.some((item) => item.value === carbonCalculator.value.energy_type)) {
    carbonCalculator.value.energy_type = types[0].value
  }
  if (!types.some((item) => item.value === entryForm.value.energy_type)) {
    entryForm.value.energy_type = types[0].value
  }
}, { immediate: true })

watch(dateRange, () => {
  if (refreshTimer) clearTimeout(refreshTimer)
  refreshTimer = setTimeout(() => { refreshData() }, 250)
})

watch(detailDeviceId, () => { loadDetailData() })
</script>

<template>
  <div class="em-page">
    <!-- 背景光晕 -->
    <div class="em-glow em-glow--tl" />
    <div class="em-glow em-glow--br" />

    <!-- 紧凑头部 -->
    <header class="em-header glass-card">
      <div class="em-header__brand">
        <p class="eyebrow">区域 · 楼宇能耗</p>
        <h2>多能源管理中心</h2>
        <div class="em-header__tags">
          <span class="hdr-tag">{{ currentRangeLabel }}</span>
          <span class="hdr-tag hdr-tag--cyan">{{ activeEnergyCount }} 类活跃</span>
          <span v-if="hasScopedAccess" class="hdr-tag hdr-tag--amber">范围受限</span>
        </div>
      </div>
      <div class="em-header__controls">
        <el-select
          v-model="detailDeviceId"
          clearable
          filterable
          placeholder="选择设备查看明细"
          teleported
          popper-class="app-select-popper"
          style="width: 200px"
        >
          <el-option
            v-for="d in deviceList"
            :key="d.id"
            :label="d.name"
            :value="d.id"
          />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="–"
          start-placeholder="开始"
          end-placeholder="结束"
          style="width: 240px"
        />
        <el-button type="primary" :loading="loading" @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="openEntryDialog">补录</el-button>
      </div>
    </header>

    <!-- KPI Strip -->
    <div class="kpi-strip">
      <div
        v-for="m in overviewMetrics"
        :key="m.label"
        class="kpi-tile"
        :class="m.accent"
      >
        <p class="kpi-eyebrow">{{ m.label }}</p>
        <div class="kpi-val">
          <strong>{{ m.value }}</strong>
          <span class="kpi-unit">{{ m.unit }}</span>
        </div>
      </div>
    </div>

    <!-- 能源类型选择条 -->
    <div class="energy-rail">
      <button
        v-for="type in visibleEnergyTypes"
        :key="type.value"
        class="energy-chip"
        :class="{ active: selectedEnergyType === type.value }"
        :style="{
          '--chip-color': typeColor(type.value),
          ...(selectedEnergyType === type.value ? {
            borderColor: typeColor(type.value) + '55',
            background: typeColor(type.value) + '18',
            color: typeColor(type.value)
          } : {})
        }"
        @click="selectedEnergyType = type.value"
      >
        <span
          class="chip-dot"
          :style="{
            background: typeColor(type.value),
            boxShadow: selectedEnergyType === type.value ? `0 0 8px ${typeColor(type.value)}88` : 'none'
          }"
        />
        <span class="chip-label">{{ type.label }}</span>
        <span class="chip-val">
          {{ (statistics[type.value]?.total_consumption || 0).toFixed(1) }}<em> {{ type.unit }}</em>
        </span>
      </button>
    </div>

    <!-- 主内容区 -->
    <div class="em-stage">
      <section class="em-main">
        <!-- 能源结构 -->
        <div class="glass-card em-card">
          <div class="card-head">
            <p class="eyebrow">Energy Structure</p>
            <div class="card-title-row">
              <h3 class="card-title">多能源结构</h3>
              <span class="card-badge">总 {{ formatMetricValue(totalEnergyConsumption, 2) }}</span>
            </div>
          </div>
          <div class="structure-body">
            <div
              ref="comparisonChartRef"
              class="chart-box"
            />
            <div class="legend-list">
              <div
                v-for="item in energyMixItems"
                :key="item.key"
                class="legend-row"
              >
                <span
                  class="legend-swatch"
                  :style="{ background: item.color, boxShadow: `0 0 6px ${item.color}66` }"
                />
                <span class="legend-name">{{ item.label }}</span>
                <span class="legend-pct">{{ item.percent.toFixed(1) }}%</span>
                <span class="legend-val">{{ formatMetricValue(item.value, 1) }} {{ item.unit }}</span>
              </div>
              <div
                v-if="!energyMixItems.length"
                class="card-empty"
              >
                暂无多能源结构数据
              </div>
            </div>
          </div>
        </div>

        <!-- 碳排放图 -->
        <div class="glass-card em-card">
          <div class="card-head">
            <p class="eyebrow">Carbon Snapshot</p>
            <div class="card-title-row">
              <h3 class="card-title">碳排运行态</h3>
              <span class="card-badge card-badge--rose">
                {{ formatMetricValue(carbonSummary?.total_carbon || 0, 2) }} kg CO₂
              </span>
            </div>
          </div>
          <div
            ref="carbonChartRef"
            class="chart-box"
          />
        </div>
      </section>

      <aside class="em-side">
        <!-- 焦点能源 -->
        <div class="glass-card em-card focus-card">
          <div class="card-head">
            <p class="eyebrow">Current Focus</p>
            <h3 class="card-title">{{ currentEnergyInfo.label || '能源焦点' }}</h3>
          </div>
          <div class="focus-hero">
            <strong class="focus-value">{{ formatMetricValue(currentStats.total_consumption, 2) }}</strong>
            <span class="focus-unit">{{ currentEnergyInfo.unit }}</span>
          </div>
          <div class="focus-metrics">
            <div
              v-for="item in focusHighlights"
              :key="item.label"
              class="focus-metric"
            >
              <span class="focus-metric__label">{{ item.label }}</span>
              <strong class="focus-metric__val">{{ item.value }}</strong>
            </div>
          </div>
        </div>

        <!-- 设备入口 -->
        <div class="glass-card em-card">
          <div class="card-head">
            <p class="eyebrow">Device Entry</p>
            <h3 class="card-title">设备维度</h3>
          </div>
          <div class="device-state">
            <span>当前焦点设备</span>
            <strong>{{ detailDeviceName }}</strong>
          </div>
          <div class="device-actions">
            <el-button
              size="small"
              type="primary"
              :disabled="!detailDeviceId"
              @click="loadDetailData"
            >
              刷新明细
            </el-button>
            <el-button
              size="small"
              @click="detailDeviceId = undefined"
            >
              系统总览
            </el-button>
          </div>
        </div>

      </aside>
    </div>

    <!-- 折叠面板 -->
    <el-collapse
      v-model="secondaryPanelActive"
      class="em-collapse"
    >
      <el-collapse-item
        name="summary-rules"
        title="统计口径与边界"
      >
        <div class="glass-card collapse-panel">
          <div class="info-list">
            <div
              v-for="item in secondaryOverviewItems"
              :key="item.label"
              class="info-item"
            >
              <span class="info-label">{{ item.label }}</span>
              <span class="info-value">{{ item.value }}</span>
            </div>
          </div>
        </div>
      </el-collapse-item>

      <el-collapse-item
        name="carbon-rules"
        title="碳排放说明 / 试算"
      >
        <div class="glass-card collapse-panel">
          <div class="info-list">
            <div
              v-for="item in carbonMetaItems"
              :key="item.label"
              class="info-item"
            >
              <span class="info-label">{{ item.label }}</span>
              <span class="info-value">{{ item.value }}</span>
            </div>
          </div>
          <div class="collapse-divider">碳排放试算</div>
          <div class="trial-form">
            <el-form label-width="90px">
              <el-form-item label="能源类型">
                <el-select
                  v-model="carbonCalculator.energy_type"
                  style="width: 100%"
                  teleported
                  popper-class="app-select-popper"
                >
                  <el-option
                    v-for="type in visibleEnergyTypes"
                    :key="type.value"
                    :label="type.label"
                    :value="type.value"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="消耗量">
                <el-input-number
                  v-model="carbonCalculator.consumption"
                  :min="0"
                  style="width: 100%"
                />
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  @click="handleCalculateCarbon"
                >
                  计算碳排放
                </el-button>
              </el-form-item>
            </el-form>
            <div
              v-if="carbonCalculator.result"
              class="result-box"
            >
              <h4>计算结果</h4>
              <div class="result-item">
                <span>能源类型</span>
                <strong>{{ carbonCalculator.result.energy_type }}</strong>
              </div>
              <div class="result-item">
                <span>消耗量</span>
                <strong>{{ carbonCalculator.result.consumption }} {{ carbonCalculator.result.consumption_unit }}</strong>
              </div>
              <div class="result-item">
                <span>碳排放因子</span>
                <strong>{{ carbonCalculator.result.carbon_factor }} {{ carbonCalculator.result.emission_unit }}/{{ carbonCalculator.result.consumption_unit }}</strong>
              </div>
              <div class="result-item result-item--highlight">
                <span>碳排放量</span>
                <strong>{{ carbonCalculator.result.carbon_emission }} {{ carbonCalculator.result.emission_unit }}</strong>
              </div>
            </div>
          </div>
        </div>
      </el-collapse-item>

      <el-collapse-item
        name="detail-data"
        title="设备原始明细"
      >
        <div class="detail-layout">
          <div class="glass-card detail-panel">
            <div class="detail-panel__head">
              <h3>能源明细</h3>
              <el-tag
                size="small"
                effect="dark"
                type="info"
              >
                {{ detailDeviceName }}
              </el-tag>
            </div>
            <el-alert
              v-if="!detailDeviceId"
              title="未选择设备时仅展示系统级统计，能源原始明细需选择具体设备。"
              type="warning"
              :closable="false"
              show-icon
            />
            <el-table
              v-else
              v-loading="detailLoading"
              :data="energyDetails"
              max-height="320"
              size="small"
            >
              <el-table-column
                prop="timestamp"
                label="时间"
                min-width="180"
              />
              <el-table-column
                prop="consumption"
                label="累计消耗"
                width="120"
              />
              <el-table-column
                prop="flow_rate"
                label="瞬时流量/功率"
                width="140"
              />
              <el-table-column
                prop="voltage"
                label="电压"
                width="100"
              />
              <el-table-column
                prop="current"
                label="电流"
                width="100"
              />
            </el-table>
          </div>

          <div class="glass-card detail-panel">
            <div class="detail-panel__head">
              <h3>碳排放明细</h3>
              <el-tag
                size="small"
                type="danger"
                effect="dark"
              >
                {{ carbonDetails.length }} 条
              </el-tag>
            </div>
            <el-table
              v-loading="detailLoading"
              :data="carbonDetails"
              max-height="320"
              size="small"
            >
              <el-table-column
                prop="timestamp"
                label="时间"
                min-width="180"
              />
              <el-table-column
                prop="energy_consumption"
                label="能耗"
                width="120"
              />
              <el-table-column
                prop="carbon_factor"
                label="因子"
                width="100"
              />
              <el-table-column
                prop="carbon_emission"
                label="碳排放"
                width="120"
              />
            </el-table>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>

    <!-- 手工补录 Dialog -->
    <el-dialog
      v-model="entryDialogVisible"
      title="手工补录能源数据"
      width="520px"
    >
      <el-form label-position="top">
        <el-form-item label="设备">
          <el-select
            v-model="entryForm.device_id"
            filterable
            placeholder="选择设备"
            style="width: 100%"
            teleported
            popper-class="app-select-popper"
          >
            <el-option
              v-for="d in deviceList"
              :key="d.id"
              :label="d.name"
              :value="d.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="能源类型">
          <el-select
            v-model="entryForm.energy_type"
            style="width: 100%"
            teleported
            popper-class="app-select-popper"
          >
            <el-option
              v-for="type in visibleEnergyTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="累计消耗">
          <el-input-number
            v-model="entryForm.consumption"
            :min="0"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="瞬时流量/功率">
          <el-input-number
            v-model="entryForm.flow_rate"
            :min="0"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="时间戳">
          <el-date-picker
            v-model="entryForm.timestamp"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="选择时间"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="entryDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleSaveEntry"
        >
          提交补录
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
/* ── 页面底色 ── */
.em-page {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px;
  min-height: 100%;
  background:
    radial-gradient(circle at 12% 8%, rgba(107, 184, 255, 0.07), transparent 32%),
    radial-gradient(circle at 90% 90%, rgba(56, 189, 248, 0.05), transparent 30%),
    #090e17;
}

/* 背景光晕装饰 */
.em-glow {
  position: fixed;
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
}
.em-glow--tl {
  top: -100px;
  left: 160px;
  width: 480px;
  height: 480px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.06), transparent 65%);
}
.em-glow--br {
  bottom: -60px;
  right: 0;
  width: 360px;
  height: 360px;
  background: radial-gradient(circle, rgba(94, 234, 212, 0.04), transparent 65%);
}

/* ── 玻璃卡片基类 ── */
.glass-card {
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(18px) saturate(145%);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.06),
    0 10px 28px rgba(0, 0, 0, 0.2);
}

/* Eyebrow 标签 */
.eyebrow {
  margin: 0;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.35);
}

/* ── 头部 ── */
.em-header {
  position: relative;
  z-index: 1;
  padding: 18px 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.em-header__brand h2 {
  margin: 6px 0 10px;
  font-size: clamp(18px, 1.8vw, 24px);
  font-weight: 700;
  letter-spacing: -0.03em;
  color: #f0f6ff;
}

.em-header__tags {
  display: flex;
  gap: 7px;
  flex-wrap: wrap;
}

.hdr-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 11px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.5);
}
.hdr-tag--cyan  { color: #5eead4; border-color: rgba(94,234,212,0.24); background: rgba(94,234,212,0.08); }
.hdr-tag--amber { color: #fbbf24; border-color: rgba(251,191,36,0.24); background: rgba(251,191,36,0.08); }

.em-header__controls {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

/* ── KPI Strip ── */
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  position: relative;
  z-index: 1;
}

.kpi-tile {
  padding: 13px 16px 11px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-bottom: 2px solid var(--kpi-accent, rgba(255,255,255,0.1));
  transition: background 0.18s;
}
.kpi-tile:hover { background: rgba(255, 255, 255, 0.06); }

.kpi-tile--energy { --kpi-accent: #a78bfa; }
.kpi-tile--load   { --kpi-accent: #38bdf8; }
.kpi-tile--carbon { --kpi-accent: #34d399; }
.kpi-tile--device { --kpi-accent: #fb923c; }

.kpi-eyebrow {
  margin: 0;
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.38);
}

.kpi-val {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  margin: 10px 0 6px;
}
.kpi-val strong {
  font-size: 26px;
  font-weight: 700;
  line-height: 1;
  color: #f0f6ff;
  font-variant-numeric: tabular-nums;
}
.kpi-unit {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 2px;
}
.kpi-caption {
  margin: 0;
  font-size: 11px;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.32);
}

/* ── 能源类型选择条 ── */
.energy-rail {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  position: relative;
  z-index: 1;
}

.energy-chip {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 7px 14px 7px 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
  cursor: pointer;
  transition: all 0.18s;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}
.energy-chip:hover {
  background: rgba(255, 255, 255, 0.07);
}

.chip-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  transition: box-shadow 0.18s;
}
.chip-label { font-weight: 500; }
.chip-val {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.38);
  margin-left: 2px;
}
.energy-chip.active .chip-val { opacity: 0.7; }
.chip-val em { font-style: normal; margin-left: 1px; }

/* ── Main Stage ── */
.em-stage {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(260px, 0.75fr);
  gap: 14px;
  position: relative;
  z-index: 1;
}

.em-main,
.em-side {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.em-card {
  padding: 18px;
}

/* 卡片头部 */
.card-head {
  margin-bottom: 14px;
}
.card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 5px;
}
.card-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: #f0f6ff;
}
.card-badge {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(56, 189, 248, 0.1);
  border: 1px solid rgba(56, 189, 248, 0.2);
  color: #7dd3fc;
  white-space: nowrap;
}
.card-badge--rose {
  background: rgba(251, 113, 133, 0.1);
  border-color: rgba(251, 113, 133, 0.2);
  color: #fda4af;
}

/* ── 能源结构图 ── */
.structure-body {
  display: grid;
  grid-template-columns: 1fr minmax(180px, 0.65fr);
  gap: 14px;
  align-items: center;
}

.chart-box {
  width: 100%;
  min-height: 240px;
}

.legend-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.legend-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.03);
  font-size: 12px;
  transition: background 0.15s;
}
.legend-row:hover { background: rgba(255, 255, 255, 0.055); }
.legend-swatch {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.legend-name {
  flex: 1;
  color: rgba(255, 255, 255, 0.72);
}
.legend-pct {
  font-weight: 600;
  color: #f0f6ff;
  width: 40px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.legend-val {
  width: 76px;
  text-align: right;
  color: rgba(255, 255, 255, 0.35);
  font-size: 11px;
}

.card-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80px;
  border-radius: 12px;
  border: 1px dashed rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.3);
  font-size: 13px;
}

/* ── 焦点能源卡 ── */
.focus-card {}
.focus-hero {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 16px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.1), rgba(94, 234, 212, 0.06));
  border: 1px solid rgba(56, 189, 248, 0.14);
  margin-bottom: 12px;
}
.focus-value {
  font-size: 38px;
  font-weight: 700;
  line-height: 1;
  color: #38bdf8;
  font-variant-numeric: tabular-nums;
}
.focus-unit {
  font-size: 14px;
  color: rgba(125, 211, 252, 0.65);
  margin-bottom: 4px;
}
.focus-metrics {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.focus-metric {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 12px;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
}
.focus-metric__label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.42);
}
.focus-metric__val {
  font-size: 15px;
  font-weight: 600;
  color: #f0f6ff;
  font-variant-numeric: tabular-nums;
}

/* ── 设备入口卡 ── */
.dim-text {
  margin: 0 0 12px;
  font-size: 12px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.4);
}
.device-state {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  margin-bottom: 12px;
}
.device-state span {
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.35);
}
.device-state strong {
  font-size: 14px;
  color: #f0f6ff;
}
.device-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* ── 范围卡 ── */
.scope-card {}
.scope-name {
  font-size: 16px;
  color: #f0f6ff;
}

/* ── 折叠面板 ── */
.em-collapse {
  position: relative;
  z-index: 1;
  background: transparent;
  border: none;
}
.em-collapse :deep(.el-collapse-item__header) {
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.7);
  border: none;
  border-radius: 12px;
  padding: 0 18px;
  margin-bottom: 8px;
  height: 44px;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.06);
  font-size: 13px;
  letter-spacing: 0.02em;
  transition: background 0.15s;
}
.em-collapse :deep(.el-collapse-item__header:hover) {
  background: rgba(255, 255, 255, 0.06);
}
.em-collapse :deep(.el-collapse-item__wrap) {
  background: transparent;
  border: none;
}
.em-collapse :deep(.el-collapse-item__content) {
  padding-bottom: 10px;
}

.collapse-panel { padding: 16px 18px; }

.collapse-divider {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 11px;
  letter-spacing: 0.1em;
  color: rgba(255, 255, 255, 0.35);
  margin: 18px 0 12px;
}
.collapse-divider::before,
.collapse-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(255, 255, 255, 0.07);
}

/* Info 列表 */
.info-list { display: flex; flex-direction: column; }
.info-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 13px;
}
.info-item:last-child { border-bottom: none; }
.info-label { color: rgba(255, 255, 255, 0.38); flex: 0 0 108px; }
.info-value { color: rgba(255, 255, 255, 0.82); text-align: right; word-break: break-word; }

.summary-inline {
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

/* 试算 */
.trial-form { margin-top: 12px; }
.result-box {
  margin-top: 12px;
  padding: 14px;
  border-radius: 12px;
  background: rgba(56, 189, 248, 0.07);
  border: 1px solid rgba(56, 189, 248, 0.16);
}
.result-box h4 {
  margin: 0 0 10px;
  font-size: 12px;
  color: #7dd3fc;
  letter-spacing: 0.06em;
}
.result-item {
  display: flex;
  justify-content: space-between;
  padding: 7px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 13px;
}
.result-item:last-child { border-bottom: none; }
.result-item span { color: rgba(255, 255, 255, 0.42); }
.result-item strong { color: #f0f6ff; }
.result-item--highlight {
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid rgba(56, 189, 248, 0.28);
  font-size: 15px;
  font-weight: 600;
}
.result-item--highlight strong { color: #38bdf8; }

/* 明细表格 */
.detail-layout {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}
.detail-panel { padding: 16px; }
.detail-panel__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.detail-panel__head h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #f0f6ff;
}

/* 表格暗色覆盖 */
:deep(.el-table) {
  background: transparent;
  color: rgba(255, 255, 255, 0.75);
  font-size: 12px;
}
:deep(.el-table th.el-table__cell),
:deep(.el-table tr),
:deep(.el-table td.el-table__cell) {
  background: transparent;
  border-bottom-color: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.72);
}
:deep(.el-table__header-wrapper th) {
  color: rgba(255, 255, 255, 0.38);
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
:deep(.el-table__empty-block) { background: transparent; }

/* ── 响应式 ── */
@media (max-width: 1200px) {
  .em-stage,
  .structure-body,
  .detail-layout {
    grid-template-columns: 1fr;
  }
  .kpi-strip { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .em-page { padding: 12px; gap: 10px; }
  .em-header { padding: 14px 16px; }
  .kpi-strip { grid-template-columns: repeat(2, 1fr); }
  .focus-value { font-size: 30px; }
}
</style>
