<script setup lang="ts">
    import { ref, onMounted, onUnmounted } from 'vue'
    import { useRouter, useRoute } from 'vue-router'
    import { useAuthStore } from '@/stores/useAuthStore'
    import { getAlarms, resolveAllAlarms, type Alarm } from '@/api/alarm'
    import { ElMessage } from 'element-plus'
    
    const router = useRouter()
    const route = useRoute()
    const authStore = useAuthStore()
    
    // --- 状态数据 ---
    const alarmCount = ref(0)
    const alarmList = ref<Alarm[]>([])
    const pollTimer = ref<any>(null)
    
    // --- 动作：退出登录 ---
    const handleLogout = () => {
      authStore.logout()
      router.push('/login')
      ElMessage.success('已退出系统')
    }
    
    // --- 动作：获取报警 (轮询) ---
    const fetchAlarms = async () => {
      try {
        // 获取未处理报警
        const res = await getAlarms()
        alarmList.value = res
        alarmCount.value = res.length
      } catch (e) {
        console.error('报警获取失败', e)
      }
    }
    
    // --- 动作：一键清除报警 ---
    const handleClearAlarms = async () => {
      try {
        const res = await resolveAllAlarms()
        // 使用后端返回的消息，或显示默认消息
        const message = res?.message || `已解决 ${res?.data?.count || 0} 条报警`
        ElMessage.success(message)
        fetchAlarms() // 刷新状态
      } catch (e) {
        ElMessage.error('操作失败')
      }
    }
    
    // --- 工具函数：格式化时间戳 ---
    const formatTime = (timestamp: string) => {
      if (!timestamp) return ''
      try {
        const date = new Date(timestamp)
        const now = new Date()
        const diff = now.getTime() - date.getTime()
        const minutes = Math.floor(diff / 60000)
        const hours = Math.floor(diff / 3600000)
        const days = Math.floor(diff / 86400000)
        
        // 如果是今天，显示时:分
        if (date.toDateString() === now.toDateString()) {
          return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
        }
        // 如果是昨天
        if (days === 1) {
          return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
        }
        // 如果是一周内
        if (days < 7) {
          return `${days}天前`
        }
        // 更早的显示完整日期
        return date.toLocaleString('zh-CN', { 
          month: '2-digit', 
          day: '2-digit', 
          hour: '2-digit', 
          minute: '2-digit' 
        })
      } catch (e) {
        return timestamp
      }
    }
    
    // --- 生命周期 ---
    onMounted(() => {
      fetchAlarms()
      // 每 5 秒轮询一次报警状态
      pollTimer.value = setInterval(fetchAlarms, 5000)
    })
    
    onUnmounted(() => {
      if (pollTimer.value) clearInterval(pollTimer.value)
    })
    </script>
    
    <template>
      <el-container class="layout-container">
        
        <el-aside width="240px" class="sidebar">
          <div class="logo-area">
            <el-icon class="logo-icon" size="24" color="#3b82f6"><Odometer /></el-icon>
            <span class="logo-text">MINE EMS</span>
          </div>
    
          <el-menu
            :default-active="route.path"
            class="el-menu-vertical"
            background-color="transparent"
            text-color="#94a3b8"
            active-text-color="#fff"
            router
          >
            <div class="menu-header">概览</div>
            <el-menu-item index="/dashboard">
              <el-icon><DataLine /></el-icon>
              <span>驾驶舱首页</span>
            </el-menu-item>
            
            <div class="menu-header">设备管理</div>
            <el-menu-item index="/devices">
              <el-icon><Cpu /></el-icon>
              <span>设备台账</span>
            </el-menu-item>
    
            <div class="menu-header">运维中心</div>
            <el-menu-item index="/fdd">
              <el-icon><FirstAidKit /></el-icon>
              <span>故障诊断 (FDD)</span>
            </el-menu-item>
            <el-menu-item index="/report">
              <el-icon><Files /></el-icon>
              <span>报表导出</span>
            </el-menu-item>
          </el-menu>
    
          <div class="user-profile">
            <div class="avatar"><el-icon><UserFilled /></el-icon></div>
            <div class="user-info">
              <div class="name">{{ authStore.username || 'Admin' }}</div>
              <div class="role">在线操作员</div>
            </div>
            <el-button link class="logout-btn" @click="handleLogout">
              <el-icon size="18"><SwitchButton /></el-icon>
            </el-button>
          </div>
        </el-aside>
    
        <el-container>
          <el-header class="top-header">
            <div class="breadcrumb">
              <span>当前位置 / {{ route.meta.title || '系统' }}</span>
            </div>
    
            <div class="header-tools">
              <el-popover
                placement="bottom"
                title="未处理报警"
                :width="300"
                trigger="click"
                popper-class="alarm-popper"
              >
                <template #reference>
                  <div class="tool-item alarm-wrapper">
                    <el-badge :value="alarmCount" :hidden="alarmCount === 0" class="item">
                      <el-button circle :class="{ 'has-alarm': alarmCount > 0 }">
                        <el-icon><Bell /></el-icon>
                      </el-button>
                    </el-badge>
                  </div>
                </template>
                
                <div class="alarm-list">
                  <div v-if="alarmList.length === 0" class="empty-alarm">
                    🎉 系统运行正常
                  </div>
                  <div v-else v-for="alarm in alarmList" :key="alarm.id" class="alarm-item">
                    <el-icon color="#ef4444"><Warning /></el-icon>
                    <div class="alarm-content">
                      <div class="msg">{{ alarm.message }}</div>
                      <div class="time">{{ formatTime(alarm.timestamp) }}</div>
                    </div>
                  </div>
                  <div v-if="alarmList.length > 0" class="alarm-footer">
                    <el-button type="primary" link size="small" @click="handleClearAlarms">全部清除</el-button>
                  </div>
                </div>
              </el-popover>
    
              <el-button circle class="tool-item">
                <el-icon><Setting /></el-icon>
              </el-button>
            </div>
          </el-header>
    
          <el-main class="main-content">
            <div class="content-wrapper">
              <router-view v-slot="{ Component }">
                <transition name="fade" mode="out-in">
                  <component :is="Component" />
                </transition>
              </router-view>
            </div>
          </el-main>
        </el-container>
      </el-container>
    </template>
    
    <style scoped>
    /* --- 布局容器 --- */
    .layout-container {
      height: 100vh;
      width: 100%;
      display: flex;
    }
    
    :deep(.el-container) {
      width: 100%;
      height: 100%;
    }
    
    /* --- 侧边栏样式 --- */
    .sidebar {
      background-color: var(--bg-sidebar);
      border-right: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
    }
    
    .logo-area {
      height: 60px;
      display: flex;
      align-items: center;
      padding: 0 20px;
      border-bottom: 1px solid var(--border-color);
      gap: 10px;
    }
    .logo-text {
      font-weight: 800;
      font-size: 18px;
      color: #fff;
      letter-spacing: 1px;
    }
    
    .menu-header {
      font-size: 12px;
      color: var(--text-secondary);
      padding: 15px 20px 5px;
      font-weight: 600;
    }
    
    /* 覆盖 Element Menu 默认样式以适配暗黑主题 */
    :deep(.el-menu) {
      border-right: none;
    }
    :deep(.el-menu-item:hover) {
      background-color: rgba(255, 255, 255, 0.05) !important;
    }
    :deep(.el-menu-item.is-active) {
      background-color: var(--brand-color) !important;
      color: #fff !important;
    }
    
    .user-profile {
      margin-top: auto; /* 推到底部 */
      padding: 20px;
      border-top: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .avatar {
      width: 36px; height: 36px;
      background: #334155;
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      color: #fff;
    }
    .user-info { flex: 1; }
    .user-info .name { font-size: 14px; font-weight: 600; color: #fff; }
    .user-info .role { font-size: 12px; color: var(--success-color); }
    .logout-btn { color: var(--text-secondary); }
    .logout-btn:hover { color: var(--danger-color); }
    
    /* --- 顶部 Header --- */
    .top-header {
      background-color: var(--bg-sidebar);
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 60px;
    }
    .breadcrumb { color: var(--text-secondary); font-size: 14px; }
    
    .header-tools { display: flex; gap: 15px; align-items: center; }
    .tool-item { background: transparent; border: none; color: var(--text-secondary); }
    .has-alarm { 
      color: var(--danger-color) !important; 
      animation: pulse 2s infinite; 
    }
    
    /* --- 报警弹窗样式 --- */
    .alarm-list { max-height: 300px; overflow-y: auto; }
    .alarm-item {
      display: flex; gap: 10px; padding: 10px 0;
      border-bottom: 1px solid #eee;
    }
    .alarm-content .msg { font-size: 13px; color: #333; }
    .alarm-content .time { font-size: 12px; color: #999; margin-top: 2px; }
    .alarm-footer { text-align: center; margin-top: 10px; }
    .empty-alarm { text-align: center; color: #999; padding: 20px; }
    
    /* --- 主内容区 --- */
    .main-content {
      padding: 20px !important;
      background-color: var(--bg-body);
      overflow-y: auto;
      width: 100%;
      box-sizing: border-box;
    }
    
    .content-wrapper {
      width: 100%;
      max-width: 100%;
      height: 100%;
      box-sizing: border-box;
    }
    
    /* --- 动画 --- */
    .fade-enter-active, .fade-leave-active {
      transition: opacity 0.2s ease;
    }
    .fade-enter-from, .fade-leave-to {
      opacity: 0;
    }
    
    @keyframes pulse {
      0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
      70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
      100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    </style>