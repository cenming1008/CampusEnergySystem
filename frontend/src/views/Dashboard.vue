<script setup lang="ts">
    import { ref, onMounted, onUnmounted, watch, reactive } from 'vue'
    import * as echarts from 'echarts'
    import { getDevices, type Device } from '@/api/device'
    import { getHistory, getAnalysis } from '@/api/telemetry'
    import { useSocketStore } from '@/stores/useSocketStore'
    import { Lightning, Timer, Odometer, VideoPlay } from '@element-plus/icons-vue'
    
    // --- 状态定义 ---
    const socketStore = useSocketStore()
    const currentDeviceId = ref<number | undefined>(undefined)
    const deviceList = ref<Device[]>([])
    const chartRef = ref<HTMLElement | null>(null)
    let myChart: echarts.ECharts | null = null
    
    // 卡片数据 (响应式对象)
    const dashboardData = reactive({
      power: 0,
      energy: 0,
      current: 0,
      voltage: 0,
      isActive: false
    })
    
    // --- 1. 初始化逻辑 ---
    onMounted(async () => {
      // 1.1 建立 WebSocket 连接 (如果还没连)
      socketStore.connect()
    
      // 1.2 初始化图表实例
      if (chartRef.value) {
        myChart = echarts.init(chartRef.value)
        window.addEventListener('resize', handleResize)
      }
    
      // 1.3 获取设备列表并默认选中第一个
      await loadDeviceList()
    })
    
    onUnmounted(() => {
      // 页面销毁时，清理资源
      window.removeEventListener('resize', handleResize)
      myChart?.dispose()
      // 注意：我们不在这里断开 Socket，因为用户可能只是切到"设备管理"页，Socket 可以保持连接
    })
    
    const handleResize = () => myChart?.resize()
    
    // --- 2. 核心业务逻辑 ---
    
    // 加载设备列表
    const loadDeviceList = async () => {
      try {
        const res = await getDevices()
        deviceList.value = res
        if (res.length > 0) {
          currentDeviceId.value = res[0].id
          handleDeviceChange() // 手动触发一次数据加载
        }
      } catch (e) {
        console.error(e)
      }
    }
    
    // 切换设备时触发
    const handleDeviceChange = async () => {
      if (!currentDeviceId.value) return
    
      // 2.1 加载卡片初始数据 (Analysis 接口)
      const analysis = await getAnalysis(currentDeviceId.value)
      dashboardData.power = analysis.current_power
      dashboardData.energy = analysis.today_energy
      dashboardData.current = analysis.current
      dashboardData.voltage = analysis.voltage
      dashboardData.isActive = analysis.is_active
    
      // 2.2 加载历史曲线 (Telemetry 接口)
      const history = await getHistory(currentDeviceId.value)
      renderChart(history)
    }
    
    // --- 3. 图表渲染逻辑 ---
    const renderChart = (data: any[]) => {
      if (!myChart) return
    
      const times = data.map(item => item.timestamp.substring(11, 19)) // 只取时分秒
      const powers = data.map(item => item.power)
      const currents = data.map(item => item.current)
    
      const option = {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
        legend: { textStyle: { color: '#94a3b8' }, top: 0 },
        grid: { left: '3%', right: '3%', bottom: '0%', top: '15%', containLabel: true },
        xAxis: {
          type: 'category',
          data: times,
          axisLine: { lineStyle: { color: '#475569' } },
          axisLabel: { color: '#94a3b8' }
        },
        yAxis: [
          {
            type: 'value', name: '功率 (kW)', position: 'left',
            splitLine: { lineStyle: { color: '#334155', type: 'dashed', opacity: 0.3 } },
            axisLabel: { color: '#94a3b8' }
          },
          {
            type: 'value', name: '电流 (A)', position: 'right',
            splitLine: { show: false },
            axisLabel: { color: '#94a3b8' }
          }
        ],
        series: [
          {
            name: '功率', type: 'line', data: powers, yAxisIndex: 0,
            color: '#3b82f6', smooth: true, showSymbol: false,
            areaStyle: { opacity: 0.2, color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(59,130,246,0.5)' }, { offset: 1, color: 'rgba(59,130,246,0.01)' }]) }
          },
          {
            name: '电流', type: 'line', data: currents, yAxisIndex: 1,
            color: '#ef4444', smooth: true, showSymbol: false
          }
        ]
      }
      myChart.setOption(option)
    }
    
    // --- 4. WebSocket 实时更新 ---
    // 监听 Store 中的最新消息
    watch(() => socketStore.latestMessage, (newMsg) => {
      // 过滤：只处理当前选中设备的数据
      if (newMsg && newMsg.type === 'telemetry_update' && newMsg.data.device_id === currentDeviceId.value) {
        const realTimeData = newMsg.data
    
        // 4.1 更新卡片数值
        dashboardData.power = realTimeData.power
        dashboardData.current = realTimeData.current
        dashboardData.voltage = realTimeData.voltage
        // 注意：websocket 推送通常不带 today_energy，如果后端没改，这里先不动 energy
    
        // 4.2 动态更新图表 (追加数据)
        if (myChart) {
          const option = myChart.getOption() as any
          // 获取当前数据队列
          const times = option.xAxis[0].data
          const powers = option.series[0].data
          const currents = option.series[1].data
    
          // 追加新点
          times.push(realTimeData.timestamp.substring(11, 19))
          powers.push(realTimeData.power)
          currents.push(realTimeData.current)
    
          // 保持队列长度 (例如只保留最近50个点)
          if (times.length > 50) {
            times.shift()
            powers.shift()
            currents.shift()
          }
    
          // 增量设置 (ECharts 会自动做平滑动画)
          myChart.setOption({
            xAxis: { data: times },
            series: [
              { data: powers },
              { data: currents }
            ]
          })
        }
      }
    })
    </script>
    
    <template>
      <div class="dashboard-container">
        
        <div class="dashboard-header">
          <div class="title">
            实时监控中心
            <el-tag v-if="socketStore.isConnected" type="success" size="small" effect="dark" class="status-tag">
              ● 实时数据接收中
            </el-tag>
            <el-tag v-else type="danger" size="small" effect="dark" class="status-tag">
              ● 连接断开
            </el-tag>
          </div>
          
          <div class="selector">
            <span>当前监控设备：</span>
            <el-select 
              v-model="currentDeviceId" 
              placeholder="请选择设备" 
              style="width: 240px"
              @change="handleDeviceChange"
            >
              <el-option
                v-for="item in deviceList"
                :key="item.id"
                :label="`${item.id}. ${item.name}`"
                :value="item.id"
              />
            </el-select>
          </div>
        </div>
    
        <div class="data-grid">
          <div class="data-card">
            <div class="card-icon blue"><el-icon><Lightning /></el-icon></div>
            <div class="card-info">
              <div class="label">实时负荷 (Power)</div>
              <div class="value">{{ dashboardData.power }} <span class="unit">kW</span></div>
            </div>
            <div class="mini-chart">
              <div class="bar" :style="{ width: Math.min(dashboardData.power, 100) + '%' }"></div>
            </div>
          </div>
    
          <div class="data-card">
            <div class="card-icon green"><el-icon><Odometer /></el-icon></div>
            <div class="card-info">
              <div class="label">今日用电 (Energy)</div>
              <div class="value">{{ dashboardData.energy }} <span class="unit">kWh</span></div>
            </div>
          </div>
    
          <div class="data-card">
            <div class="card-icon red"><el-icon><VideoPlay /></el-icon></div>
            <div class="card-info">
              <div class="label">A相电流 (Current)</div>
              <div class="value">{{ dashboardData.current }} <span class="unit">A</span></div>
            </div>
          </div>
    
          <div class="data-card">
            <div class="card-icon purple"><el-icon><Timer /></el-icon></div>
            <div class="card-info">
              <div class="label">母线电压 (Voltage)</div>
              <div class="value">{{ dashboardData.voltage }} <span class="unit">V</span></div>
            </div>
          </div>
        </div>
    
        <div class="chart-panel">
          <div class="panel-header">
            <h3>负荷趋势分析</h3>
          </div>
          <div class="chart-box" ref="chartRef"></div>
        </div>
    
      </div>
    </template>
    
    <style scoped>
    .dashboard-container {
      padding: 0;
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      gap: 20px;
      box-sizing: border-box;
    }
    
    /* --- 顶部栏 --- */
    .dashboard-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--bg-sidebar);
      padding: 15px 20px;
      border-radius: 8px;
      border: 1px solid var(--border-color);
      width: 100%;
      box-sizing: border-box;
    }
    
    @media (max-width: 768px) {
      .dashboard-header {
        flex-direction: column;
        gap: 15px;
        align-items: flex-start;
      }
    }
    .title { font-size: 16px; font-weight: bold; display: flex; align-items: center; gap: 10px; }
    .selector { display: flex; align-items: center; gap: 10px; font-size: 14px; color: var(--text-secondary); }
    
    /* --- 卡片网格 --- */
    .data-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      width: 100%;
    }
    
    @media (max-width: 1400px) {
      .data-grid {
        grid-template-columns: repeat(2, 1fr);
      }
    }
    
    @media (max-width: 768px) {
      .data-grid {
        grid-template-columns: 1fr;
      }
    }
    .data-card {
      background: var(--bg-sidebar);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px;
      display: flex;
      align-items: center;
      position: relative;
      overflow: hidden;
      transition: transform 0.2s;
    }
    .data-card:hover { transform: translateY(-3px); border-color: var(--brand-color); }
    
    .card-icon {
      width: 48px; height: 48px;
      border-radius: 12px;
      display: flex; align-items: center; justify-content: center;
      font-size: 24px;
      margin-right: 15px;
    }
    /* 图标颜色背景 */
    .card-icon.blue { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
    .card-icon.green { background: rgba(16, 185, 129, 0.1); color: #10b981; }
    .card-icon.red { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
    .card-icon.purple { background: rgba(168, 85, 247, 0.1); color: #a855f7; }
    
    .card-info .label { font-size: 13px; color: var(--text-secondary); margin-bottom: 4px; }
    .card-info .value { font-size: 24px; font-weight: bold; color: #fff; }
    .card-info .unit { font-size: 12px; color: var(--text-muted); font-weight: normal; }
    
    .mini-chart {
      position: absolute; bottom: 0; left: 0; width: 100%; height: 3px; background: #334155;
    }
    .mini-chart .bar { height: 100%; background: var(--brand-color); transition: width 0.3s; }
    
    /* --- 图表区域 --- */
    .chart-panel {
      flex: 1; /* 占满剩余高度 */
      background: var(--bg-sidebar);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      min-height: 300px;
      width: 100%;
      box-sizing: border-box;
    }
    .panel-header h3 { margin: 0 0 15px 0; font-size: 16px; border-left: 4px solid var(--brand-color); padding-left: 10px; }
    .chart-box { flex: 1; width: 100%; }
    </style>