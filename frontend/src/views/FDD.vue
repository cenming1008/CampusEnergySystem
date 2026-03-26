<script setup lang="ts">
	    import { computed, ref, onMounted, onUnmounted } from 'vue'
	    import { echarts } from '@/shared/lib/echarts'
	    import { getFDDStats, diagnoseDevice, type FDDReport, type FDDDiagnosis } from '@/api/fdd'
	    import { Refresh, Loading } from '@element-plus/icons-vue'
	    import { ElMessage } from 'element-plus'
	    import { useAuthStore } from '@/stores/useAuthStore'
	    import { usePermissions } from '@/shared/composables/usePermissions'

    interface ChartTooltipItem {
      dataIndex: number
    }

    interface ChartBarColorParam {
      value: number
    }

    interface ChartClickParam {
      componentType?: string
      seriesName?: string
      dataIndex: number
    }

    const getErrorMessage = (error: unknown, fallback: string) => {
      if (
        typeof error === 'object' &&
        error !== null &&
        'response' in error &&
        typeof error.response === 'object' &&
        error.response !== null &&
        'data' in error.response &&
        typeof error.response.data === 'object' &&
        error.response.data !== null &&
        'detail' in error.response.data &&
        typeof error.response.data.detail === 'string'
      ) {
        return error.response.data.detail
      }

      if (error instanceof Error && error.message) return error.message
      return fallback
    }
    
    const chartRef = ref<HTMLElement>()
    let myChart: echarts.ECharts | null = null
    const loading = ref(false)
	    const diagnosisLoading = ref(false)
	    const authStore = useAuthStore()
	    const { hasScopedAccess } = usePermissions()
    
    // 设备详细诊断相关
    const showDiagnosisDialog = ref(false)
    const currentDiagnosis = ref<FDDDiagnosis | null>(null)
	    const deviceList = ref<FDDReport[]>([])
	    const visibleDeviceCount = computed(() => deviceList.value.length)
	    const fddHint = computed(() => {
	      if (!authStore.locationScope) {
	        return '当前诊断面板展示的是当前账号可访问的全部设备健康情况。'
	      }
	      return `当前诊断面板已按位置范围 ${authStore.locationScope} 过滤，仅显示允许访问的设备。`
	    })
    
    // --- 初始化图表 ---
    const initChart = async () => {
      if (!chartRef.value) return
      
      loading.value = true
      if (!myChart) {
        myChart = echarts.init(chartRef.value)
        // 添加点击事件监听
        myChart.on('click', handleChartClick)
      }
      myChart.showLoading({ textColor: '#fff', maskColor: 'rgba(255, 255, 255, 0.05)' })
    
      try {
        // 1. 获取数据
        const data = await getFDDStats()
        deviceList.value = data
        
        // 2. 转换数据格式
        const names = data.map(i => i.device_name)
        const scores = data.map(i => i.health_score)
        const alarms = data.map(i => i.alarm_count)
    
        // 3. 配置 ECharts
        const option = {
          backgroundColor: 'transparent',
          tooltip: { 
            trigger: 'axis', 
            axisPointer: { type: 'shadow' },
            formatter: (params: ChartTooltipItem[]) => {
              const dataIndex = params[0].dataIndex
              const device = data[dataIndex]
              return `${device.device_name}<br/>健康评分: ${device.health_score}分<br/>报警次数: ${device.alarm_count}次<br/>状态: ${getStatusText(device.status)}<br/><span style="color: #94a3b8; font-size: 12px;">点击查看详细诊断</span>`
            }
          },
          legend: { textStyle: { color: '#94a3b8' } },
          grid: { left: '3%', right: '5%', bottom: '3%', containLabel: true },
          xAxis: { 
            type: 'value', 
            splitLine: { show: false },
            axisLabel: { color: '#94a3b8' }
          },
          yAxis: { 
            type: 'category', 
            data: names, 
            axisLabel: { color: '#fff', fontSize: 13, fontWeight: 'bold' } 
          },
          series: [
            {
              name: '健康评分', 
              type: 'bar', 
              data: scores,
              barWidth: 15,
              label: { show: true, position: 'right', color: '#fff' },
              itemStyle: { 
                // 动态颜色：根据分数变色
                color: (params: ChartBarColorParam) => {
                  const val = params.value
                  if (val > 80) return '#10b981' // 绿
                  if (val > 60) return '#f59e0b' // 黄
                  return '#ef4444' // 红
                },
                borderRadius: [0, 4, 4, 0]
              }
            },
            {
              name: '报警次数', 
              type: 'bar', 
              data: alarms,
              barWidth: 15,
              itemStyle: { color: '#475569', borderRadius: [0, 4, 4, 0] }
            }
          ]
        }
        
        myChart.setOption(option)
      } catch(e) {
        console.error(e)
        ElMessage.error('获取诊断数据失败')
      } finally {
        myChart.hideLoading()
        loading.value = false
      }
    }
    
    // --- 图表点击事件 ---
    const handleChartClick = (params: ChartClickParam) => {
      if (params.componentType === 'series' && params.seriesName === '健康评分') {
        const device = deviceList.value[params.dataIndex]
        if (device) {
          void showDeviceDiagnosis(device.device_id)
        }
      }
    }
    
    // --- 显示设备详细诊断 ---
    const showDeviceDiagnosis = async (deviceId: number) => {
      diagnosisLoading.value = true
      try {
        const diagnosis = await diagnoseDevice(deviceId)
        currentDiagnosis.value = diagnosis
        showDiagnosisDialog.value = true
      } catch (error) {
        ElMessage.error(getErrorMessage(error, '获取设备诊断详情失败'))
      } finally {
        diagnosisLoading.value = false
      }
    }
    
    // --- 获取状态文本 ---
    const getStatusText = (status: string) => {
      const statusMap: Record<string, string> = {
        healthy: '健康',
        warning: '警告',
        critical: '严重'
      }
      return statusMap[status] || status
    }
    
    // --- 获取健康分数颜色 ---
    const getScoreColor = (score: number) => {
      if (score > 80) return '#10b981'
      if (score > 60) return '#f59e0b'
      return '#ef4444'
    }
    
    // --- 窗口自适应 ---
    const handleResize = () => myChart?.resize()
    
    onMounted(() => {
      initChart()
      window.addEventListener('resize', handleResize)
    })
    
    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
      myChart?.dispose()
    })
    </script>
    
<template>
  <div class="fdd-container">
    <div class="header">
      <div class="title-area">
        <h2 class="title">
          设备健康度诊断 (FDD)
        </h2>
        <p class="subtitle">
          基于报警频率的健康评分模型 - 点击图表查看设备详细诊断
        </p>
        <div class="meta-row">
          <el-tag
            size="small"
            effect="dark"
            type="info"
          >
            当前设备 {{ visibleDeviceCount }} 台
          </el-tag>
          <el-tag
            v-if="hasScopedAccess"
            size="small"
            effect="dark"
            type="warning"
          >
            诊断范围受限
          </el-tag>
        </div>
      </div>
      <el-button
        :icon="Refresh"
        circle
        :loading="loading"
        @click="initChart"
      />
    </div>

    <el-alert
      :title="fddHint"
      :type="hasScopedAccess ? 'warning' : 'info'"
      :closable="false"
      show-icon
      style="margin-bottom: 16px;"
    />
	    
    <div class="chart-wrapper">
      <div
        ref="chartRef"
        class="chart-box"
      />
    </div>
        
    <!-- 设备详细诊断对话框 -->
    <el-dialog
      v-model="showDiagnosisDialog"
      title="设备详细诊断"
      width="600px"
      :close-on-click-modal="false"
    >
      <div
        v-if="diagnosisLoading"
        class="loading-container"
      >
        <el-icon class="is-loading">
          <Loading />
        </el-icon>
        <span>正在分析设备数据...</span>
      </div>
      <div
        v-else-if="currentDiagnosis"
        class="diagnosis-content"
      >
        <div class="device-info">
          <h3>{{ currentDiagnosis.device_name }}</h3>
          <div class="score-display">
            <span class="score-label">健康分数：</span>
            <span
              class="score-value"
              :style="{ color: getScoreColor(currentDiagnosis.health_score) }"
            >
              {{ currentDiagnosis.health_score }} 分
            </span>
          </div>
        </div>
            
        <div class="suggestions-section">
          <h4>诊断建议：</h4>
          <ul class="suggestions-list">
            <li
              v-for="(suggestion, index) in currentDiagnosis.suggestions"
              :key="index"
            >
              {{ suggestion }}
            </li>
          </ul>
        </div>
      </div>
    </el-dialog>
  </div>
</template>
    
    <style scoped>
    .fdd-container {
      background: var(--bg-sidebar);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 24px;
      height: 85vh;
      display: flex;
      flex-direction: column;
      width: 100%;
      box-sizing: border-box;
    }
    
    .header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 20px;
    }
    
    .title { margin: 0; color: #fff; font-size: 18px; border-left: 4px solid var(--brand-color); padding-left: 10px; }
	    .subtitle { margin: 5px 0 0 14px; color: var(--text-secondary); font-size: 13px; }
	    .meta-row { margin: 10px 0 0 14px; display: flex; gap: 8px; flex-wrap: wrap; }
    
    .chart-wrapper {
      flex: 1;
      width: 100%;
      min-height: 0;
    }
    
    .chart-box {
      width: 100%;
      height: 100%;
      cursor: pointer;
    }
    
    .loading-container {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      padding: 40px;
      color: var(--text-secondary);
    }
    
    .diagnosis-content {
      padding: 10px 0;
    }
    
    .device-info {
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--border-color);
    }
    
    .device-info h3 {
      margin: 0 0 12px 0;
      color: #fff;
      font-size: 18px;
    }
    
    .score-display {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .score-label {
      color: var(--text-secondary);
      font-size: 14px;
    }
    
    .score-value {
      font-size: 24px;
      font-weight: bold;
    }
    
    .suggestions-section h4 {
      margin: 0 0 12px 0;
      color: #fff;
      font-size: 16px;
    }
    
    .suggestions-list {
      margin: 0;
      padding-left: 20px;
      color: var(--text-primary);
      line-height: 1.8;
    }
    
    .suggestions-list li {
      margin-bottom: 8px;
    }
    </style>
