<script setup lang="ts">
    import { ref, onMounted, onUnmounted } from 'vue'
    import * as echarts from 'echarts'
    import { getFDDStats } from '@/api/fdd'
    import { Refresh } from '@element-plus/icons-vue'
    
    const chartRef = ref<HTMLElement>()
    let myChart: echarts.ECharts | null = null
    const loading = ref(false)
    
    // --- 初始化图表 ---
    const initChart = async () => {
      if (!chartRef.value) return
      
      loading.value = true
      if (!myChart) myChart = echarts.init(chartRef.value)
      myChart.showLoading({ textColor: '#fff', maskColor: 'rgba(255, 255, 255, 0.05)' })
    
      try {
        // 1. 获取数据
        const data = await getFDDStats()
        
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
            formatter: '{b}<br/>{a0}: {c0}分<br/>{a1}: {c1}次'
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
                color: (params: any) => {
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
      } finally {
        myChart.hideLoading()
        loading.value = false
      }
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
            <h2 class="title">设备健康度诊断 (FDD)</h2>
            <p class="subtitle">基于报警频率的健康评分模型</p>
          </div>
          <el-button :icon="Refresh" circle @click="initChart" :loading="loading" />
        </div>
    
        <div class="chart-wrapper">
          <div ref="chartRef" class="chart-box"></div>
        </div>
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
    
    .chart-wrapper {
      flex: 1;
      width: 100%;
      min-height: 0;
    }
    
    .chart-box {
      width: 100%;
      height: 100%;
    }
    </style>