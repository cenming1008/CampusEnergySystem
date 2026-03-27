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
  type CarbonFactor
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
const consumptionChartRef = ref<HTMLElement | null>(null)
const comparisonChartRef = ref<HTMLElement | null>(null)
const carbonChartRef = ref<HTMLElement | null>(null)
let consumptionChart: echarts.ECharts | null = null
let comparisonChart: echarts.ECharts | null = null
let carbonChart: echarts.ECharts | null = null
let refreshTimer: ReturnType<typeof setTimeout> | null = null

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

// 渲染消耗趋势图（当前能源类型）
const renderConsumptionChart = () => {
  if (!consumptionChart || !consumptionChartRef.value) return
  
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      textStyle: { color: '#94a3b8' },
      top: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#94a3b8' }
    },
    yAxis: {
      type: 'value',
      name: `消耗量 (${currentEnergyInfo.value.unit})`,
      splitLine: {
        lineStyle: { color: '#334155', type: 'dashed', opacity: 0.3 }
      },
      axisLabel: { color: '#94a3b8' }
    },
    series: [
      {
        name: currentEnergyInfo.value.label,
        type: 'line',
        data: [120, 132, 101, 134, 90, 230, 210],
        smooth: true,
        color: '#3b82f6',
        areaStyle: {
          opacity: 0.2,
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59,130,246,0.5)' },
            { offset: 1, color: 'rgba(59,130,246,0.01)' }
          ])
        }
      }
    ]
  }
  
  consumptionChart.setOption(option)
}

// 渲染多能源对比图
const renderComparisonChart = () => {
  if (!comparisonChart || !comparisonChartRef.value) return
  
  const data = energyTypes.value.map(type => ({
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
    const typeInfo = energyTypes.value.find(t => t.value === type)
    return {
      name: typeInfo?.label || type,
      value: info.carbon_emission  // 修正：使用正确的字段名
    }
  }).filter(item => item.value > 0)
  
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
  if (consumptionChartRef.value) {
    consumptionChart = echarts.init(consumptionChartRef.value)
    window.addEventListener('resize', () => consumptionChart?.resize())
  }
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
    
    // 渲染消耗趋势图
    renderConsumptionChart()
  } catch {
    ElMessage.error('页面初始化失败，请刷新重试')
  }
})

// 监听能源类型变化
watch(selectedEnergyType, () => {
  renderConsumptionChart()
  loadDetailData()
})

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
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="title-section">
        <h2>多能源管理中心</h2>
        <p>全面监控和分析电、水、气、热、冷等多种能源消耗</p>
        <div class="meta-row">
          <el-tag
            size="small"
            effect="dark"
            type="info"
          >
            当前可见设备 {{ visibleDeviceCount }} 台
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
      
      <div class="controls">
        <el-select
          v-model="detailDeviceId"
          clearable
          filterable
          placeholder="选择设备查看明细"
          style="width: 220px"
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
          style="width: 300px"
        />
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

    <el-alert
      :title="scopeDescription"
      type="info"
      :closable="false"
      show-icon
    />

    <!-- 能源类型选择卡片 -->
    <div class="energy-types-grid">
      <div 
        v-for="type in energyTypes" 
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

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">
          总消耗
        </div>
        <div class="stat-value">
          {{ currentStats.total_consumption.toFixed(2) }}
          <span class="stat-unit">{{ currentEnergyInfo.unit }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">
          平均消耗
        </div>
        <div class="stat-value">
          {{ currentStats.avg_consumption.toFixed(2) }}
          <span class="stat-unit">{{ currentEnergyInfo.unit }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">
          峰值流量
        </div>
        <div class="stat-value">
          {{ currentStats.peak_flow_rate.toFixed(2) }}
          <span class="stat-unit">{{ currentEnergyInfo.unit }}/h</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">
          数据条数
        </div>
        <div class="stat-value">
          {{ currentStats.data_count }}
          <span class="stat-unit">条</span>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-layout">
      <!-- 消耗趋势图 -->
      <div class="chart-panel large">
        <div class="panel-header">
          <h3>{{ currentEnergyInfo.label }}消耗趋势</h3>
        </div>
        <div
          ref="consumptionChartRef"
          class="chart-box"
        />
      </div>

      <!-- 多能源对比图 -->
      <div class="chart-panel">
        <div class="panel-header">
          <h3>多能源消耗占比</h3>
        </div>
        <div
          ref="comparisonChartRef"
          class="chart-box"
        />
      </div>
    </div>

    <!-- 碳排放区域 -->
    <div class="carbon-section">
      <div class="chart-panel large">
        <div class="panel-header">
          <h3>碳排放统计</h3>
          <el-tag
            v-if="carbonSummary"
            type="danger"
            size="small"
          >
            总排放: {{ carbonSummary.total_carbon.toFixed(2) }} kg CO2
          </el-tag>
        </div>
        <div
          ref="carbonChartRef"
          class="chart-box"
        />
      </div>

      <!-- 碳排放计算器 -->
      <div class="calculator-panel">
        <div class="panel-header">
          <h3>碳排放计算器</h3>
          <el-tag
            size="small"
            type="success"
            effect="dark"
          >
            只读分析工具
          </el-tag>
        </div>
        <div class="calculator-content">
          <el-form label-width="100px">
            <el-form-item label="能源类型">
              <el-select
                v-model="carbonCalculator.energy_type"
                style="width: 100%"
                teleported
                popper-class="app-select-popper"
              >
                <el-option
                  v-for="type in energyTypes"
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
    </div>

    <div class="detail-layout">
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
              v-for="type in energyTypes"
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
  padding: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-sidebar);
  padding: 20px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.title-section h2 {
  margin: 0 0 5px 0;
  font-size: 20px;
}

.title-section p {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.meta-row {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

/* 能源类型卡片 */
.energy-types-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
}

.energy-card {
  background: var(--bg-sidebar);
  border: 2px solid var(--border-color);
  border-radius: 12px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.energy-card:hover {
  transform: translateY(-3px);
  border-color: var(--brand-color);
}

.energy-card.active {
  border-color: var(--brand-color);
  background: rgba(59, 130, 246, 0.1);
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
}

.energy-card .consumption {
  font-size: 24px;
  font-weight: bold;
  color: var(--brand-color);
}

.energy-card .unit {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: normal;
  margin-left: 4px;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.stat-card {
  background: var(--bg-sidebar);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #fff;
}

.stat-unit {
  font-size: 14px;
  color: var(--text-muted);
  font-weight: normal;
  margin-left: 4px;
}

/* 图表布局 */
.charts-layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

@media (max-width: 1200px) {
  .charts-layout {
    grid-template-columns: 1fr;
  }
}

.carbon-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

@media (max-width: 1200px) {
  .carbon-section {
    grid-template-columns: 1fr;
  }
}

.chart-panel {
  background: var(--bg-sidebar);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  min-height: 400px;
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
  border-left: 4px solid var(--brand-color);
  padding-left: 10px;
}

.chart-box {
  flex: 1;
  width: 100%;
  min-height: 300px;
}

/* 计算器面板 */
.calculator-panel {
  background: var(--bg-sidebar);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
}

.detail-layout {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.detail-panel {
  background: var(--bg-sidebar);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
}

.calculator-content {
  margin-top: 15px;
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

@media (max-width: 1200px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }
}
</style>
