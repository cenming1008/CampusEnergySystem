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

// 能源类型列表
const energyTypes = ref<EnergyTypeInfo[]>([])
// 当前选中的能源类型
const selectedEnergyType = ref<string>('electricity')
// 设备列表
const deviceList = ref<Device[]>([])
// 时间范围
const dateRange = ref<[Date, Date]>([
  new Date(new Date().getTime() - 7 * 24 * 3600 * 1000), // 最近7天
  new Date()
])

// 统计数据
const statistics = ref<{ [key: string]: EnergyStatistics }>({})
// 总览元信息
const overviewMeta = ref<EnergyOverview | null>(null)
// 碳排放汇总
const carbonSummary = ref<CarbonSummary | null>(null)
// 碳排放因子
const carbonFactors = ref<Record<string, CarbonFactor>>({})
// 加载状态
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

// 图表引用
const comparisonChartRef = ref<HTMLElement | null>(null)
const carbonChartRef = ref<HTMLElement | null>(null)
let comparisonChart: echarts.ECharts | null = null
let carbonChart: echarts.ECharts | null = null
let refreshTimer: ReturnType<typeof setTimeout> | null = null
const secondaryPanelActive = ref<string[]>([])

// 碳排放计算器
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

// ==================== 计算属性 ====================

const formatDateRange = computed(() => {
  if (!dateRange.value) return ['', '']
  
  // 使用本地时间格式，避免时区问题
  const formatLocalDateTime = (date: Date) => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')
    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`
  }
  
  // 开始时间设为当天 00:00:00，结束时间设为当天 23:59:59
  const startDate = new Date(dateRange.value[0])
  startDate.setHours(0, 0, 0, 0)
  
  const endDate = new Date(dateRange.value[1])
  endDate.setHours(23, 59, 59, 999)
  
  return [
    formatLocalDateTime(startDate),
    formatLocalDateTime(endDate)
  ]
})

// 当前能源类型的统计数据
const currentStats = computed(() => {
  return statistics.value[selectedEnergyType.value] || {
    total_consumption: 0,
    avg_consumption: 0,
    avg_flow_rate: 0,
    peak_flow_rate: 0,
    data_count: 0
  }
})

// 当前能源类型信息
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
  return `${format(start)} - ${format(end)}`
})

const totalEnergyConsumption = computed(() => {
  return visibleEnergyTypes.value.reduce((sum, type) => {
    return sum + (statistics.value[type.value]?.total_consumption || 0)
  }, 0)
})

const energyMixItems = computed(() => {
  const palette: Record<string, string> = {
    electricity: '#3b82f6',
    water: '#10b981',
    gas: '#f59e0b',
    heat: '#ef4444',
    cooling: '#8b5cf6',
    steam: '#ec4899',
  }

  const items = visibleEnergyTypes.value
    .map((type) => {
      const stats = statistics.value[type.value]
      const value = stats?.total_consumption || 0
      return {
        key: type.value,
        label: type.label,
        unit: type.unit,
        value,
        color: palette[type.value] || '#94a3b8',
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
  },
  {
    label: '总能耗汇总',
    value: formatMetricValue(totalEnergyConsumption.value, 2),
    unit: currentEnergyInfo.value.unit || 'kWh',
    caption: '按各能源自身口径分别统计后聚合展示',
  },
  {
    label: '总碳排',
    value: formatMetricValue(carbonSummary.value?.total_carbon || 0, 2),
    unit: 'kg CO2',
    caption: '当前范围内多能源阶段汇总',
  },
  {
    label: '设备入口',
    value: String(visibleDeviceCount.value),
    unit: '台',
    caption: detailDeviceId.value ? `已选 ${detailDeviceName.value}` : '支持按设备下钻查看明细',
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
    { label: '当前能源累计量语义', value: currentStats.value.consumption_semantics || currentEnergyInfo.value.consumption_semantics || '未声明' },
    { label: '当前能源瞬时量语义', value: currentStats.value.flow_semantics || currentEnergyInfo.value.flow_semantics || '未声明' },
  ]
})

// ==================== 数据加载 ====================

// 加载能源类型
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

// 加载设备列表
const loadDevices = async () => {
  try {
    deviceList.value = await getDevices()
  } catch {
    // 设备列表加载失败，由 axios 拦截器统一提示
  }
}

// 加载碳排放因子
const loadCarbonFactors = async () => {
  try {
    const res = await getCarbonFactors()
    carbonFactors.value = res.carbon_factors
  } catch {
    // 碳排放因子加载失败
  }
}

// 加载聚合总览数据
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

// 刷新数据
const refreshData = async () => {
  try {
    await Promise.all([
      loadOverview(),
      loadDetailData()
    ])
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

// 渲染多能源对比图
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
      formatter: '{b}: {c} {d}%'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: '#94a3b8' }
    },
    series: [
      {
        name: '能源消耗',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#1e293b',
          borderWidth: 2
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold',
            color: '#fff'
          }
        },
        labelLine: {
          show: false
        },
        data: data,
        color: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
      }
    ]
  }
  
  comparisonChart.setOption(option)
}

// 渲染碳排放图表
const renderCarbonChart = () => {
  if (!carbonChart || !carbonChartRef.value || !carbonSummary.value) return
  
  const data = Object.entries(carbonSummary.value.by_energy_type).map(([type, info]) => {
    if (type === 'steam' && !hasSteamRuntimePresence.value) return null
    const typeInfo = energyTypes.value.find(t => t.value === type)
    return {
      name: typeInfo?.label || type,
      value: info.carbon_emission  // 修正：使用正确的字段名
    }
  }).filter((item): item is { name: string; value: number } => Boolean(item && item.value > 0))
  
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.name),
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#94a3b8' }
    },
    yAxis: {
      type: 'value',
      name: '碳排放 (kg CO2)',
      splitLine: {
        lineStyle: { color: '#334155', type: 'dashed', opacity: 0.3 }
      },
      axisLabel: { color: '#94a3b8' }
    },
    series: [
      {
        name: '碳排放',
        type: 'bar',
        data: data.map(d => d.value),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#ef4444' },
            { offset: 1, color: '#dc2626' }
          ]),
          borderRadius: [6, 6, 0, 0]
        }
      }
    ]
  }
  
  carbonChart.setOption(option)
}

// 初始化图表
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
  } catch (e) {
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
  } catch (error) {
    ElMessage.error('补录失败')
  }
}

// ==================== 生命周期 ====================

onMounted(async () => {
  try {
    await loadEnergyTypes()
    await loadDevices()
    await loadCarbonFactors()
    
    // 初始化图表
    initCharts()
    
    // 等待一小段时间确保图表初始化完成
    await new Promise(resolve => setTimeout(resolve, 100))
    
    // 加载数据
    await refreshData()
    
  } catch {
    ElMessage.error('页面初始化失败，请刷新重试')
  }
})

// 监听能源类型变化
watch(selectedEnergyType, () => {
  loadDetailData()
})

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

// 监听日期范围变化
watch(dateRange, () => {
  if (refreshTimer) {
    clearTimeout(refreshTimer)
  }
  refreshTimer = setTimeout(() => {
    refreshData()
  }, 250)
})

watch(detailDeviceId, () => {
  loadDetailData()
})
</script>

<template>
  <div class="energy-management">
    <header class="energy-hero">
      <div class="energy-hero__backdrop" />
      <div class="energy-hero__main">
        <div class="hero-brand">
          <p class="hero-kicker">Park Energy Hub</p>
          <h1>多能源管理中心</h1>
          <p class="hero-subtitle">
            围绕园区当前多能源运行态，集中查看总览指标、结构分布、焦点能源与设备下钻入口。
          </p>
          <div class="meta-row">
            <el-tag
              size="small"
              effect="dark"
              type="info"
            >
              时间范围 {{ currentRangeLabel }}
            </el-tag>
            <el-tag
              size="small"
              effect="dark"
              type="success"
            >
              当前可见设备 {{ visibleDeviceCount }} 台
            </el-tag>
            <el-tag
              size="small"
              effect="plain"
              type="success"
            >
              活跃能源 {{ activeEnergyCount }} 类
            </el-tag>
            <el-tag
              v-if="hasScopedAccess"
              size="small"
              effect="dark"
              type="warning"
            >
              数据范围已受限
            </el-tag>
          </div>
        </div>

        <div class="hero-side">
          <div class="hero-side__panel">
            <span class="hero-side__label">当前范围</span>
            <strong>{{ authStore.locationScope || '园区全域可见范围' }}</strong>
            <small>{{ scopeDescription }}</small>
          </div>
          <div class="hero-side__panel hero-side__panel--controls">
            <el-select
              v-model="detailDeviceId"
              clearable
              filterable
              placeholder="选择设备查看明细"
              style="width: 100%"
              teleported
              popper-class="app-select-popper"
            >
              <el-option
                v-for="device in deviceList"
                :key="device.id"
                :label="device.name"
                :value="device.id"
              />
            </el-select>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 100%"
            />
            <div class="hero-side__actions">
              <el-button
                type="primary"
                :loading="loading"
                @click="refreshData"
              >
                <el-icon><Refresh /></el-icon>
                刷新数据
              </el-button>
              <el-button
                type="warning"
                @click="openEntryDialog"
              >
                手工补录
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </header>

    <section class="metric-grid">
      <article
        v-for="metric in overviewMetrics"
        :key="metric.label"
        class="metric-card"
      >
        <span class="metric-card__label">{{ metric.label }}</span>
        <div class="metric-card__value">
          <strong>{{ metric.value }}</strong>
          <small>{{ metric.unit }}</small>
        </div>
        <span class="metric-card__caption">{{ metric.caption }}</span>
      </article>
    </section>

    <!-- 能源类型选择卡片 -->
    <div class="energy-types-grid">
      <div 
        v-for="type in visibleEnergyTypes" 
        :key="type.value"
        class="energy-card"
        :class="{ active: selectedEnergyType === type.value }"
        @click="selectedEnergyType = type.value"
      >
        <div class="card-header">
          <div
            class="icon"
            :class="`icon-${type.value}`"
          >
            <el-icon><Lightning /></el-icon>
          </div>
          <div class="label">
            {{ type.label }}
          </div>
        </div>
        <div class="consumption">
          {{ (statistics[type.value]?.total_consumption || 0).toFixed(2) }}
          <span class="unit">{{ type.unit }}</span>
        </div>
      </div>
    </div>

    <main class="energy-stage">
      <section class="stage-main">
        <article class="stage-card stage-card--hero">
          <div class="stage-card__head stage-card__head--split">
            <div>
              <span class="stage-card__eyebrow">Energy Structure</span>
              <h3>园区多能源结构</h3>
            </div>
            <div class="stage-card__tag">
              <span>总能耗</span>
              <strong>{{ formatMetricValue(totalEnergyConsumption, 2) }}</strong>
            </div>
          </div>
          <div class="structure-stage">
            <div class="structure-stage__chart">
              <div
                ref="comparisonChartRef"
                class="chart-box chart-box--hero"
              />
            </div>
            <div class="structure-stage__legend">
              <div
                v-for="item in energyMixItems"
                :key="item.key"
                class="energy-legend-card"
              >
                <div class="energy-legend-card__top">
                  <span class="energy-legend-card__swatch" :style="{ background: item.color }" />
                  <span>{{ item.label }}</span>
                </div>
                <div class="energy-legend-card__main">
                  <strong>{{ item.percent.toFixed(1) }}%</strong>
                  <small>{{ formatMetricValue(item.value, 2) }} {{ item.unit }}</small>
                </div>
              </div>
              <div
                v-if="!energyMixItems.length"
                class="card-empty"
              >
                当前暂无有效多能源结构数据
              </div>
            </div>
          </div>
        </article>

        <article class="stage-card stage-card--carbon">
          <div class="stage-card__head stage-card__head--split">
            <div>
              <span class="stage-card__eyebrow">Carbon Snapshot</span>
              <h3>碳排运行态</h3>
            </div>
            <div class="stage-card__tag stage-card__tag--danger">
              <span>总排放</span>
              <strong>{{ formatMetricValue(carbonSummary?.total_carbon || 0, 2) }}</strong>
            </div>
          </div>
          <div
            ref="carbonChartRef"
            class="chart-box chart-box--hero"
          />
        </article>
      </section>

      <aside class="stage-side">
        <article class="stage-card focus-card">
          <div class="stage-card__head">
            <span class="stage-card__eyebrow">Current Focus</span>
            <h3>{{ currentEnergyInfo.label || '当前能源焦点' }}</h3>
          </div>
          <div class="focus-card__hero">
            <div class="focus-card__value">
              <strong>{{ formatMetricValue(currentStats.total_consumption, 2) }}</strong>
              <small>{{ currentEnergyInfo.unit }}</small>
            </div>
            <p>{{ currentEnergyInfo.label }}是当前主视图焦点，可联动查看其统计表现与设备明细入口。</p>
          </div>
          <div class="focus-card__grid">
            <div
              v-for="item in focusHighlights"
              :key="item.label"
              class="focus-card__metric"
            >
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <small>{{ item.hint }}</small>
            </div>
          </div>
        </article>

        <article class="stage-card stage-card--entry">
          <div class="stage-card__head">
            <span class="stage-card__eyebrow">Device Entry</span>
            <h3>设备维度入口</h3>
          </div>
          <p class="entry-copy">
            {{ deviceEntryDescription }}
          </p>
          <div class="entry-actions">
            <el-button
              type="primary"
              :disabled="!detailDeviceId"
              @click="loadDetailData"
            >
              刷新当前设备明细
            </el-button>
            <el-button @click="detailDeviceId = undefined">
              返回系统级总览
            </el-button>
          </div>
          <div class="entry-state">
            <span>当前焦点设备</span>
            <strong>{{ detailDeviceName }}</strong>
          </div>
        </article>
      </aside>
    </main>

    <el-collapse
      v-model="secondaryPanelActive"
      class="secondary-collapse"
    >
      <el-collapse-item
        name="summary-rules"
        title="次级说明：统计口径与边界"
      >
        <div class="info-panel collapsed-panel">
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
        title="次级说明：碳排与字段说明 / 试算"
      >
        <div class="info-panel collapsed-panel">
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
          <div class="summary-inline">
            <span>支持设备类型：{{ formatListText(currentStats.supported_device_types || currentEnergyProfile.supported_device_types) }}</span>
            <span>公共字段：{{ formatListText(currentStats.public_fields || currentEnergyProfile.public_fields) }}</span>
            <span>专属字段：{{ formatListText(currentStats.specialized_fields || currentEnergyProfile.specialized_fields) }}</span>
          </div>
          <div class="secondary-divider">
            <span>碳排放试算</span>
          </div>
          <div class="trial-form">
            <el-form label-width="100px">
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
                <span>能源类型:</span>
                <strong>{{ carbonCalculator.result.energy_type }}</strong>
              </div>
              <div class="result-item">
                <span>消耗量:</span>
                <strong>{{ carbonCalculator.result.consumption }} {{ carbonCalculator.result.consumption_unit }}</strong>
              </div>
              <div class="result-item">
                <span>碳排放因子:</span>
                <strong>{{ carbonCalculator.result.carbon_factor }} {{ carbonCalculator.result.emission_unit }}/{{ carbonCalculator.result.consumption_unit }}</strong>
              </div>
              <div class="result-item highlight">
                <span>碳排放量:</span>
                <strong>{{ carbonCalculator.result.carbon_emission }} {{ carbonCalculator.result.emission_unit }}</strong>
              </div>
            </div>
          </div>
        </div>
      </el-collapse-item>
      <el-collapse-item
        name="detail-data"
        title="详情层：设备原始明细"
      >
        <div class="detail-layout detail-layout--collapsed">
          <div class="detail-panel">
            <div class="panel-header">
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
              title="未选择设备时，仅展示系统级统计；能源原始明细需要选择具体设备。"
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

          <div class="detail-panel">
            <div class="panel-header">
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
              v-for="device in deviceList"
              :key="device.id"
              :label="device.name"
              :value="device.id"
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
        <el-button @click="entryDialogVisible = false">
          取消
        </el-button>
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
.energy-management {
  position: relative;
  width: 100%;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding-bottom: 12px;
}

.energy-hero {
  position: relative;
  overflow: hidden;
  border-radius: 24px;
  padding: 28px;
  background:
    radial-gradient(circle at top left, rgba(59, 130, 246, 0.28), transparent 36%),
    radial-gradient(circle at bottom right, rgba(16, 185, 129, 0.18), transparent 30%),
    linear-gradient(145deg, rgba(15, 23, 42, 0.95), rgba(17, 24, 39, 0.92));
  border: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow: 0 24px 50px rgba(15, 23, 42, 0.28);
}

.energy-hero__backdrop {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px);
  background-size: 64px 64px;
  opacity: 0.12;
  pointer-events: none;
}

.energy-hero__main {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.9fr);
  gap: 24px;
}

.hero-brand h1 {
  margin: 0;
  font-size: 34px;
  line-height: 1.1;
  color: #f8fafc;
}

.hero-kicker {
  margin: 0 0 10px;
  font-size: 12px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.9);
}

.hero-subtitle {
  margin: 12px 0 0;
  max-width: 700px;
  font-size: 14px;
  line-height: 1.7;
  color: rgba(226, 232, 240, 0.82);
}

.meta-row {
  margin-top: 18px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.hero-side {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-side__panel {
  padding: 18px 18px 16px;
  border-radius: 18px;
  background: rgba(15, 23, 42, 0.44);
  border: 1px solid rgba(148, 163, 184, 0.14);
  backdrop-filter: blur(10px);
}

.hero-side__label {
  display: block;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: rgba(148, 163, 184, 0.78);
}

.hero-side__panel strong {
  display: block;
  margin-top: 8px;
  font-size: 18px;
  color: #f8fafc;
}

.hero-side__panel small {
  display: block;
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.6;
  color: rgba(203, 213, 225, 0.76);
}

.hero-side__panel--controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hero-side__actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.metric-card {
  padding: 20px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.84));
  border: 1px solid rgba(148, 163, 184, 0.12);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.metric-card__label {
  font-size: 12px;
  color: rgba(148, 163, 184, 0.84);
}

.metric-card__value {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  margin-top: 12px;
}

.metric-card__value strong {
  font-size: 32px;
  line-height: 1;
  color: #fff;
}

.metric-card__value small {
  font-size: 13px;
  color: rgba(191, 219, 254, 0.86);
  margin-bottom: 4px;
}

.metric-card__caption {
  display: block;
  margin-top: 12px;
  font-size: 12px;
  line-height: 1.5;
  color: rgba(203, 213, 225, 0.68);
}

.energy-types-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 14px;
}

.energy-card {
  background: linear-gradient(180deg, rgba(17, 24, 39, 0.92), rgba(15, 23, 42, 0.88));
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 18px;
  padding: 18px 16px;
  cursor: pointer;
  transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
}

.energy-card:hover {
  transform: translateY(-4px);
  border-color: rgba(59, 130, 246, 0.4);
  box-shadow: 0 16px 30px rgba(15, 23, 42, 0.18);
}

.energy-card.active {
  border-color: rgba(59, 130, 246, 0.56);
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.98), rgba(30, 64, 175, 0.22));
}

.energy-card .card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.energy-card .icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.icon-electricity { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
.icon-water { background: rgba(16, 185, 129, 0.2); color: #10b981; }
.icon-gas { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
.icon-heat { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
.icon-cooling { background: rgba(139, 92, 246, 0.2); color: #8b5cf6; }
.icon-steam { background: rgba(236, 72, 153, 0.2); color: #ec4899; }

.energy-card .label {
  font-weight: 600;
  font-size: 14px;
  color: #e2e8f0;
}

.energy-card .consumption {
  font-size: 26px;
  font-weight: 700;
  color: #f8fafc;
}

.energy-card .unit {
  font-size: 12px;
  color: rgba(148, 163, 184, 0.82);
  font-weight: normal;
  margin-left: 4px;
}

.energy-stage {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.85fr);
  gap: 20px;
}

.stage-main,
.stage-side {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stage-card {
  padding: 22px;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.94), rgba(17, 24, 39, 0.9));
  border: 1px solid rgba(148, 163, 184, 0.14);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.18);
}

.stage-card__head {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 18px;
}

.stage-card__head--split {
  flex-direction: row;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.stage-card__eyebrow {
  font-size: 11px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.8);
}

.stage-card__head h3 {
  margin: 0;
  font-size: 22px;
  color: #f8fafc;
}

.stage-card__tag {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  color: rgba(148, 163, 184, 0.84);
  font-size: 12px;
}

.stage-card__tag strong {
  font-size: 24px;
  color: #fff;
}

.stage-card__tag--danger strong {
  color: #fca5a5;
}

.structure-stage {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(260px, 0.8fr);
  gap: 18px;
  align-items: stretch;
}

.structure-stage__chart,
.structure-stage__legend {
  min-height: 100%;
}

.structure-stage__legend {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.energy-legend-card {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.52);
  border: 1px solid rgba(148, 163, 184, 0.1);
}

.energy-legend-card__top {
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(226, 232, 240, 0.88);
  font-size: 13px;
}

.energy-legend-card__swatch {
  width: 10px;
  height: 10px;
  border-radius: 999px;
}

.energy-legend-card__main {
  display: flex;
  margin-top: 16px;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.energy-legend-card__main strong {
  font-size: 24px;
  color: #fff;
}

.energy-legend-card__main small {
  font-size: 12px;
  color: rgba(191, 219, 254, 0.78);
}

.card-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
  border-radius: 16px;
  border: 1px dashed rgba(148, 163, 184, 0.18);
  color: rgba(148, 163, 184, 0.82);
  font-size: 13px;
  text-align: center;
}

.chart-box {
  width: 100%;
  min-height: 260px;
}

.chart-box--hero {
  min-height: 320px;
}

.focus-card__hero {
  padding: 18px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.18), rgba(15, 23, 42, 0.3));
  border: 1px solid rgba(96, 165, 250, 0.22);
}

.focus-card__value {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.focus-card__value strong {
  font-size: 38px;
  line-height: 1;
  color: #fff;
}

.focus-card__value small {
  font-size: 14px;
  color: rgba(191, 219, 254, 0.84);
  margin-bottom: 6px;
}

.focus-card__hero p,
.entry-copy {
  margin: 12px 0 0;
  font-size: 13px;
  line-height: 1.7;
  color: rgba(203, 213, 225, 0.78);
}

.focus-card__grid {
  display: grid;
  grid-template-columns: repeat(1, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.focus-card__metric {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.48);
  border: 1px solid rgba(148, 163, 184, 0.1);
}

.focus-card__metric span {
  display: block;
  font-size: 12px;
  color: rgba(148, 163, 184, 0.82);
}

.focus-card__metric strong {
  display: block;
  margin-top: 10px;
  font-size: 24px;
  color: #fff;
}

.focus-card__metric small {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: rgba(203, 213, 225, 0.68);
}

.entry-actions,
.device-entry-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 16px;
}

.entry-state {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid rgba(148, 163, 184, 0.12);
}

.entry-state span {
  font-size: 12px;
  color: rgba(148, 163, 184, 0.82);
}

.entry-state strong {
  font-size: 18px;
  color: #f8fafc;
}

.secondary-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 13px;
  margin: 20px 0 12px;
}

.secondary-divider::before,
.secondary-divider::after {
  content: '';
  height: 1px;
  background: rgba(255, 255, 255, 0.08);
  flex: 1;
}

.secondary-collapse {
  background: transparent;
}

.secondary-collapse :deep(.el-collapse-item__header) {
  background: rgba(15, 23, 42, 0.72);
  color: #e2e8f0;
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 14px;
  padding: 0 18px;
  margin-bottom: 10px;
}

.secondary-collapse :deep(.el-collapse-item__wrap) {
  background: transparent;
  border: none;
}

.secondary-collapse :deep(.el-collapse-item__content) {
  padding-bottom: 8px;
}

.collapsed-panel {
  padding: 0;
  border: none;
  background: transparent;
}

.info-panel {
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.88), rgba(17, 24, 39, 0.86));
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 18px;
  padding: 20px;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.info-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.info-label {
  color: rgba(148, 163, 184, 0.82);
  flex: 0 0 120px;
  font-size: 13px;
}

.info-value {
  color: #fff;
  text-align: right;
  word-break: break-word;
  font-size: 13px;
}

.summary-inline {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  color: #fff;
  margin-top: 16px;
}

.trial-form {
  margin-top: 18px;
}

.result-box {
  margin-top: 20px;
  padding: 15px;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.result-box h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: var(--brand-color);
}

.result-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 13px;
}

.result-item:last-child {
  border-bottom: none;
}

.result-item.highlight {
  font-size: 16px;
  color: var(--brand-color);
  font-weight: bold;
  margin-top: 10px;
  padding-top: 15px;
  border-top: 2px solid var(--brand-color);
}

.result-item span {
  color: var(--text-secondary);
}

.result-item strong {
  color: #fff;
}

.detail-layout {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.detail-layout--collapsed {
  margin-top: 6px;
}

.detail-panel {
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.88), rgba(17, 24, 39, 0.86));
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 18px;
  padding: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  color: #f8fafc;
}

@media (max-width: 1200px) {
  .energy-hero__main,
  .energy-stage,
  .structure-stage,
  .metric-grid,
  .detail-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .energy-hero {
    padding: 22px 18px;
    border-radius: 20px;
  }

  .hero-brand h1 {
    font-size: 28px;
  }

  .metric-card__value strong,
  .focus-card__value strong {
    font-size: 28px;
  }

  .stage-card {
    padding: 18px;
  }
}
</style>
