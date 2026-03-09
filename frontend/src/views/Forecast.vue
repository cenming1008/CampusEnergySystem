<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import {
  forecastLoad,
  forecastRenewable,
  getLatestForecast,
  trainLSTMModel,
  evaluateLSTMModel,
  getModelVersions,
  activateModelVersion,
  getSchedulerJobs,
  type ForecastPoint,
  type ModelVersion,
  type PredictionType
} from '@/api/forecast'
import { getDevices, type Device } from '@/api/device'

// --- 状态 ---
const loading = ref(false)
const predictionType = ref<PredictionType>('load')
const selectedDeviceId = ref<number | undefined>(undefined)
const forecastHours = ref(24)
const algorithm = ref('')
const deviceList = ref<Device[]>([])
const predictions = ref<ForecastPoint[]>([])
const modelVersions = ref<ModelVersion[]>([])
const schedulerJobs = ref<any[]>([])

// 训练状态
const training = ref(false)
const trainDays = ref(60)
const useMultivariate = ref(false)

// 评估结果
const evaluation = ref<any>(null)

// 图表
let forecastChart: echarts.ECharts | null = null
const chartRef = ref<HTMLDivElement | null>(null)

// 预测类型选项
const predictionTypes = [
  { value: 'load', label: '负荷预测', icon: '⚡' },
  { value: 'solar', label: '光伏预测', icon: '☀️' },
  { value: 'wind', label: '风电预测', icon: '💨' }
]

// 算法选项
const algorithms = [
  { value: '', label: '自动选择' },
  { value: 'lstm', label: 'LSTM深度学习' },
  { value: 'moving_average', label: '移动平均' },
  { value: 'linear_regression', label: '线性回归' }
]

// --- 方法 ---
const loadDevices = async () => {
  try {
    deviceList.value = await getDevices()
  } catch (e) {
    console.error('加载设备失败:', e)
  }
}

const loadModelVersions = async () => {
  try {
    const res = await getModelVersions(predictionType.value, selectedDeviceId.value)
    modelVersions.value = res.versions || []
  } catch (e) {
    console.error('加载模型版本失败:', e)
  }
}

const loadSchedulerJobs = async () => {
  try {
    const res = await getSchedulerJobs()
    schedulerJobs.value = res.jobs || []
  } catch (e) {
    console.error('加载定时任务失败:', e)
  }
}

const handleForecast = async () => {
  loading.value = true
  try {
    let result
    if (predictionType.value === 'load') {
      result = await forecastLoad(selectedDeviceId.value, forecastHours.value, algorithm.value || undefined)
    } else {
      result = await forecastRenewable(
        predictionType.value as 'solar' | 'wind',
        selectedDeviceId.value,
        forecastHours.value,
        algorithm.value || undefined
      )
    }
    predictions.value = result.predictions || []
    renderChart()
    ElMessage.success(`预测完成，共 ${predictions.value.length} 个数据点`)
  } catch (e: any) {
    ElMessage.error(e.message || '预测失败')
  } finally {
    loading.value = false
  }
}

const handleTrain = async () => {
  training.value = true
  try {
    const result = await trainLSTMModel({
      prediction_type: predictionType.value,
      device_id: selectedDeviceId.value,
      days: trainDays.value,
      retrain: true,
      use_multivariate: useMultivariate.value
    })
    ElMessage.success('模型训练完成')
    loadModelVersions()
  } catch (e: any) {
    ElMessage.error(e.message || '训练失败')
  } finally {
    training.value = false
  }
}

const handleEvaluate = async () => {
  loading.value = true
  try {
    const result = await evaluateLSTMModel(predictionType.value, selectedDeviceId.value)
    evaluation.value = result
    ElMessage.success('评估完成')
  } catch (e: any) {
    ElMessage.error(e.message || '评估失败')
  } finally {
    loading.value = false
  }
}

const handleActivateVersion = async (version: ModelVersion) => {
  try {
    await activateModelVersion(predictionType.value, version.version, selectedDeviceId.value)
    ElMessage.success('已激活版本 ' + version.version)
    loadModelVersions()
  } catch (e) {
    ElMessage.error('激活失败')
  }
}

const initChart = () => {
  if (!chartRef.value) return
  forecastChart = echarts.init(chartRef.value)
  window.addEventListener('resize', () => forecastChart?.resize())
}

const renderChart = () => {
  if (!forecastChart) return
  
  const times = predictions.value.map(p => {
    const d = new Date(p.forecast_time)
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  })
  const values = predictions.value.map(p => p.predicted_value)
  const confidences = predictions.value.map(p => p.confidence || 0.8)
  
  // 计算置信区间
  const upperBound = values.map((v, i) => v * (1 + (1 - confidences[i]) * 0.5))
  const lowerBound = values.map((v, i) => v * (1 - (1 - confidences[i]) * 0.5))
  
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0,0,0,0.8)',
      borderColor: '#00f2fe',
      textStyle: { color: '#fff' },
      formatter: (params: any) => {
        const p = params[0]
        const conf = confidences[p.dataIndex]
        return `
          <div style="padding:5px">
            <div style="color:#8892b0">${p.axisValue}</div>
            <div style="color:#00f2fe;font-size:16px;font-weight:bold">${p.value.toFixed(2)} kW</div>
            <div style="color:#67c23a;font-size:12px">置信度: ${(conf * 100).toFixed(0)}%</div>
          </div>
        `
      }
    },
    legend: {
      data: ['预测值', '置信区间'],
      textStyle: { color: '#8892b0' },
      top: 10
    },
    grid: { left: 60, right: 30, top: 50, bottom: 30 },
    xAxis: {
      type: 'category',
      data: times,
      axisLine: { lineStyle: { color: '#1e3a5f' } },
      axisLabel: { color: '#8892b0', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      name: '预测值 (kW)',
      nameTextStyle: { color: '#8892b0' },
      axisLine: { show: false },
      axisLabel: { color: '#8892b0' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
    },
    series: [
      {
        name: '置信区间',
        type: 'line',
        data: upperBound,
        lineStyle: { opacity: 0 },
        areaStyle: { opacity: 0 },
        stack: 'confidence',
        symbol: 'none'
      },
      {
        name: '置信区间',
        type: 'line',
        data: lowerBound.map((v, i) => upperBound[i] - v),
        lineStyle: { opacity: 0 },
        areaStyle: {
          color: 'rgba(0, 242, 254, 0.1)'
        },
        stack: 'confidence',
        symbol: 'none'
      },
      {
        name: '预测值',
        type: 'line',
        data: values,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 3, color: '#00f2fe' },
        itemStyle: { color: '#00f2fe' }
      }
    ]
  }
  forecastChart.setOption(option, true)
}

// --- 监听 ---
watch(predictionType, () => {
  loadModelVersions()
  predictions.value = []
  evaluation.value = null
})

// --- 生命周期 ---
onMounted(async () => {
  await loadDevices()
  await loadModelVersions()
  await loadSchedulerJobs()
  initChart()
})

onUnmounted(() => {
  forecastChart?.dispose()
})
</script>

<template>
  <div class="forecast-page">
    <div class="page-header">
      <h2>负荷预测</h2>
      <div class="type-selector">
        <el-radio-group v-model="predictionType" size="large">
          <el-radio-button v-for="t in predictionTypes" :key="t.value" :value="t.value">
            {{ t.icon }} {{ t.label }}
          </el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div class="main-content">
      <!-- 左侧控制面板 -->
      <div class="control-panel">
        <!-- 预测参数 -->
        <div class="panel-section">
          <div class="section-title">预测参数</div>
          <el-form label-position="top">
            <el-form-item label="设备">
              <el-select v-model="selectedDeviceId" placeholder="全部设备" clearable style="width: 100%">
                <el-option v-for="d in deviceList" :key="d.id" :label="d.name" :value="d.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="预测时长">
              <el-select v-model="forecastHours" style="width: 100%">
                <el-option :value="12" label="12小时" />
                <el-option :value="24" label="24小时" />
                <el-option :value="48" label="48小时" />
                <el-option :value="72" label="72小时" />
                <el-option :value="168" label="7天" />
              </el-select>
            </el-form-item>
            <el-form-item label="算法">
              <el-select v-model="algorithm" style="width: 100%">
                <el-option v-for="a in algorithms" :key="a.value" :label="a.label" :value="a.value" />
              </el-select>
            </el-form-item>
            <el-button type="primary" @click="handleForecast" :loading="loading" style="width: 100%">
              开始预测
            </el-button>
          </el-form>
        </div>

        <!-- 模型训练 -->
        <div class="panel-section">
          <div class="section-title">LSTM模型训练</div>
          <el-form label-position="top">
            <el-form-item label="训练天数">
              <el-input-number v-model="trainDays" :min="30" :max="365" style="width: 100%" />
            </el-form-item>
            <el-form-item>
              <el-checkbox v-model="useMultivariate">多变量预测</el-checkbox>
            </el-form-item>
            <el-button type="warning" @click="handleTrain" :loading="training" style="width: 100%">
              训练模型
            </el-button>
            <el-button @click="handleEvaluate" :loading="loading" style="width: 100%; margin-top: 10px">
              评估模型
            </el-button>
          </el-form>
        </div>

        <!-- 评估结果 -->
        <div class="panel-section" v-if="evaluation">
          <div class="section-title">模型评估</div>
          <div class="eval-grid">
            <div class="eval-item">
              <label>MAE</label>
              <span>{{ evaluation.mae?.toFixed(4) }}</span>
            </div>
            <div class="eval-item">
              <label>MAPE</label>
              <span>{{ (evaluation.mape * 100)?.toFixed(2) }}%</span>
            </div>
            <div class="eval-item">
              <label>RMSE</label>
              <span>{{ evaluation.rmse?.toFixed(4) }}</span>
            </div>
            <div class="eval-item">
              <label>测试样本</label>
              <span>{{ evaluation.test_samples }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间图表区域 -->
      <div class="chart-panel">
        <div class="chart-card">
          <div class="chart-header">
            <span class="chart-title">预测曲线</span>
            <span class="chart-info" v-if="predictions.length">
              共 {{ predictions.length }} 个预测点
            </span>
          </div>
          <div class="chart-container" ref="chartRef"></div>
          <el-empty v-if="predictions.length === 0" description="点击【开始预测】生成预测数据" :image-size="100" />
        </div>

        <!-- 预测数据表格 -->
        <div class="data-card" v-if="predictions.length > 0">
          <div class="card-header">预测数据</div>
          <el-table :data="predictions.slice(0, 24)" stripe max-height="200" size="small">
            <el-table-column label="时间" width="160">
              <template #default="{ row }">
                {{ new Date(row.forecast_time).toLocaleString('zh-CN') }}
              </template>
            </el-table-column>
            <el-table-column label="预测值 (kW)" width="120">
              <template #default="{ row }">
                {{ row.predicted_value.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column label="置信度" width="100">
              <template #default="{ row }">
                <el-progress
                  :percentage="(row.confidence || 0.8) * 100"
                  :stroke-width="8"
                  :show-text="false"
                  :color="row.confidence > 0.8 ? '#67c23a' : '#e6a23c'"
                />
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- 右侧模型管理 -->
      <div class="model-panel">
        <div class="panel-section">
          <div class="section-title">模型版本</div>
          <div class="version-list">
            <div
              v-for="v in modelVersions"
              :key="v.version"
              class="version-item"
              :class="{ active: v.is_active }"
            >
              <div class="version-info">
                <div class="version-name">
                  {{ v.version }}
                  <el-tag v-if="v.is_active" type="success" size="small">当前</el-tag>
                </div>
                <div class="version-meta">
                  创建于 {{ new Date(v.created_at).toLocaleDateString() }}
                </div>
                <div class="version-metrics" v-if="v.metrics">
                  <span v-if="v.metrics.mae">MAE: {{ v.metrics.mae.toFixed(4) }}</span>
                  <span v-if="v.metrics.val_loss">Loss: {{ v.metrics.val_loss.toFixed(4) }}</span>
                </div>
              </div>
              <el-button
                v-if="!v.is_active"
                text size="small"
                @click="handleActivateVersion(v)"
              >激活</el-button>
            </div>
            <el-empty v-if="modelVersions.length === 0" description="暂无模型" :image-size="60" />
          </div>
        </div>

        <div class="panel-section">
          <div class="section-title">定时任务</div>
          <div class="job-list">
            <div v-for="job in schedulerJobs" :key="job.id" class="job-item">
              <div class="job-name">{{ job.name }}</div>
              <div class="job-next" v-if="job.next_run_time">
                下次执行: {{ new Date(job.next_run_time).toLocaleString('zh-CN') }}
              </div>
            </div>
            <el-empty v-if="schedulerJobs.length === 0" description="暂无任务" :image-size="40" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.forecast-page {
  padding: 10px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: var(--text-primary);
}

.main-content {
  flex: 1;
  display: flex;
  gap: 20px;
  min-height: 0;
}

.control-panel, .model-panel {
  width: 280px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.chart-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.panel-section {
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 15px;
}

.section-title {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-color);
}

.chart-card, .data-card {
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 20px;
}

.chart-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.chart-title {
  font-weight: 600;
  color: var(--text-primary);
}

.chart-info {
  font-size: 12px;
  color: var(--text-secondary);
}

.chart-container {
  flex: 1;
  min-height: 300px;
}

.card-header {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 15px;
}

.eval-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.eval-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
}

.eval-item label {
  font-size: 12px;
  color: var(--text-secondary);
}

.eval-item span {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.version-list {
  max-height: 300px;
  overflow-y: auto;
}

.version-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-radius: 8px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.02);
  transition: all 0.2s;
}

.version-item.active {
  background: rgba(103, 194, 58, 0.1);
  border: 1px solid rgba(103, 194, 58, 0.3);
}

.version-name {
  font-weight: 500;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.version-meta {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.version-metrics {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 4px;
  display: flex;
  gap: 10px;
}

.job-list {
  max-height: 200px;
  overflow-y: auto;
}

.job-item {
  padding: 10px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  margin-bottom: 8px;
}

.job-name {
  font-weight: 500;
  color: var(--text-primary);
}

.job-next {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

:deep(.el-form-item) {
  margin-bottom: 15px;
}
</style>
