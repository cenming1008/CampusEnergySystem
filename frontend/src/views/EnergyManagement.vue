<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { 
  getEnergyTypes, 
  getEnergyStatistics, 
  getCarbonSummary,
  getCarbonFactors,
  calculateCarbon,
  type EnergyTypeInfo,
  type EnergyStatistics,
  type CarbonSummary
} from '@/api/energy'
import { getDevices, type Device } from '@/api/device'

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
const carbonFactors = ref<any>({})
// 加载状态
const loading = ref(false)

// 图表引用
const consumptionChartRef = ref<HTMLElement | null>(null)
const comparisonChartRef = ref<HTMLElement | null>(null)
const carbonChartRef = ref<HTMLElement | null>(null)
let consumptionChart: echarts.ECharts | null = null
let comparisonChart: echarts.ECharts | null = null
let carbonChart: echarts.ECharts | null = null

// 碳排放计算器
const carbonCalculator = ref({
  energy_type: 'electricity',
  consumption: 0,
  result: null as any
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

// ==================== 数据加载 ====================

// 加载能源类型
const loadEnergyTypes = async () => {
  try {
    const res = await getEnergyTypes()
    energyTypes.value = res.energy_types
    if (energyTypes.value.length > 0 && !selectedEnergyType.value) {
      selectedEnergyType.value = energyTypes.value[0].value
    }
    console.log('✅ 加载能源类型成功:', energyTypes.value.length, '种')
  } catch (e) {
    console.error('❌ 加载能源类型失败:', e)
    ElMessage.error('加载能源类型失败')
    throw e
  }
}

// 加载设备列表
const loadDevices = async () => {
  try {
    deviceList.value = await getDevices()
  } catch (e) {
    console.error('加载设备列表失败', e)
  }
}

// 加载碳排放因子
const loadCarbonFactors = async () => {
  try {
    const res = await getCarbonFactors()
    carbonFactors.value = res.carbon_factors
  } catch (e) {
    console.error('加载碳排放因子失败', e)
  }
}

// 加载所有能源类型的统计数据
const loadAllStatistics = async () => {
  loading.value = true
  try {
    const [startTime, endTime] = formatDateRange.value
    
    console.log('🔄 开始加载统计数据:', { startTime, endTime, types: energyTypes.value.length })
    
    // 检查时间参数
    if (!startTime || !endTime) {
      console.error('❌ 时间参数无效')
      ElMessage.error('时间参数无效')
      return
    }
    
    // 为每个能源类型加载统计数据
    const promises = energyTypes.value.map(async (type) => {
      try {
        console.log(`📊 请求 ${type.label} 统计...`)
        const stats = await getEnergyStatistics({
          energy_type: type.value,
          start_time: startTime,
          end_time: endTime,
          period_type: 'day'
        })
        console.log(`✅ ${type.label} 统计成功:`, stats)
        return { type: type.value, stats }
      } catch (e) {
        console.error(`❌ 加载 ${type.label} 统计失败:`, e)
        // 即使失败也返回默认值，不阻断其他请求
        return { 
          type: type.value, 
          stats: {
            total_consumption: 0,
            avg_consumption: 0,
            avg_flow_rate: 0,
            peak_flow_rate: 0,
            data_count: 0
          } 
        }
      }
    })
    
    const results = await Promise.all(promises)
    const newStats: { [key: string]: EnergyStatistics } = {}
    results.forEach(({ type, stats }) => {
      newStats[type] = stats
    })
    statistics.value = newStats
    
    console.log('✅ 所有统计数据加载完成:', newStats)
    
    // 渲染对比图表
    renderComparisonChart()
    
  } catch (e) {
    console.error('❌ 加载统计数据失败:', e)
    ElMessage.error('加载数据失败: ' + (e as Error).message)
  } finally {
    loading.value = false
  }
}

// 加载碳排放汇总
const loadCarbonSummary = async () => {
  try {
    const [startTime, endTime] = formatDateRange.value
    
    if (!startTime || !endTime) {
      console.warn('⚠️ 碳排放查询缺少时间参数')
      return
    }
    
    console.log('🌱 加载碳排放数据...')
    carbonSummary.value = await getCarbonSummary({
      start_time: startTime,
      end_time: endTime
    })
    console.log('✅ 碳排放数据加载成功:', carbonSummary.value)
    
    // 渲染碳排放图表
    renderCarbonChart()
  } catch (e) {
    console.error('❌ 加载碳排放数据失败:', e)
  }
}

// 刷新数据
const refreshData = async () => {
  console.log('🔄 刷新数据...')
  try {
    await Promise.all([
      loadAllStatistics(),
      loadCarbonSummary()
    ])
    console.log('✅ 数据刷新完成')
  } catch (e) {
    console.error('❌ 数据刷新失败:', e)
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
    carbonCalculator.value.result = res.data
    ElMessage.success('计算完成')
  } catch (e) {
    ElMessage.error('计算失败')
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
  } catch (e) {
    console.error('初始化失败:', e)
    ElMessage.error('页面初始化失败，请刷新重试')
  }
})

// 监听能源类型变化
watch(selectedEnergyType, () => {
  renderConsumptionChart()
})

// 监听日期范围变化
watch(dateRange, () => {
  refreshData()
})
</script>

<template>
  <div class="energy-management">
    
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="title-section">
        <h2>多能源管理中心</h2>
        <p>全面监控和分析电、水、气、热、冷等多种能源消耗</p>
      </div>
      
      <div class="controls">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 300px"
        />
        <el-button type="primary" :loading="loading" @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
      </div>
    </div>

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
          <div class="icon" :class="`icon-${type.value}`">
            <el-icon><Lightning /></el-icon>
          </div>
          <div class="label">{{ type.label }}</div>
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
        <div class="stat-label">总消耗</div>
        <div class="stat-value">
          {{ currentStats.total_consumption.toFixed(2) }}
          <span class="stat-unit">{{ currentEnergyInfo.unit }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">平均消耗</div>
        <div class="stat-value">
          {{ currentStats.avg_consumption.toFixed(2) }}
          <span class="stat-unit">{{ currentEnergyInfo.unit }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">峰值流量</div>
        <div class="stat-value">
          {{ currentStats.peak_flow_rate.toFixed(2) }}
          <span class="stat-unit">{{ currentEnergyInfo.unit }}/h</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">数据条数</div>
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
        <div class="chart-box" ref="consumptionChartRef"></div>
      </div>

      <!-- 多能源对比图 -->
      <div class="chart-panel">
        <div class="panel-header">
          <h3>多能源消耗占比</h3>
        </div>
        <div class="chart-box" ref="comparisonChartRef"></div>
      </div>
    </div>

    <!-- 碳排放区域 -->
    <div class="carbon-section">
      <div class="chart-panel large">
        <div class="panel-header">
          <h3>碳排放统计</h3>
          <el-tag type="danger" size="small" v-if="carbonSummary">
            总排放: {{ carbonSummary.total_carbon.toFixed(2) }} kg CO2
          </el-tag>
        </div>
        <div class="chart-box" ref="carbonChartRef"></div>
      </div>

      <!-- 碳排放计算器 -->
      <div class="calculator-panel">
        <div class="panel-header">
          <h3>碳排放计算器</h3>
        </div>
        <div class="calculator-content">
          <el-form label-width="100px">
            <el-form-item label="能源类型">
              <el-select v-model="carbonCalculator.energy_type" style="width: 100%">
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
              <el-button type="primary" @click="handleCalculateCarbon">
                计算碳排放
              </el-button>
            </el-form-item>
          </el-form>

          <div v-if="carbonCalculator.result" class="result-box">
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
</style>
