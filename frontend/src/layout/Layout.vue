<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/useAuthStore'
import { useSocketStore } from '@/stores/useSocketStore'
import { ElMessage } from 'element-plus'
import { getCurrentUserApi, logoutApi } from '@/api/auth'

const AlarmPopover = defineAsyncComponent(() => import('@/features/alarm/components/AlarmPopover.vue'))

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const socketStore = useSocketStore()

const roleLabelMap: Record<string, string> = {
  admin: '系统管理员',
  operator: '能源运营人员',
  maintainer: '设备运维人员',
  viewer: '园区观察员',
}

const visibleSystemMenu = computed(() => authStore.role === 'admin')
const roleLabel = computed(() => roleLabelMap[authStore.role || 'viewer'] || authStore.role || '未识别角色')
const scopeLabel = computed(() => authStore.locationScope ? `可见范围: ${authStore.locationScope}` : '园区全域可见')

onMounted(async () => {
  if (!authStore.token) return
  try {
    const profile = await getCurrentUserApi()
    authStore.applyProfile(profile)
  } catch (_error) {
    // Ignore here; global interceptor will handle auth failures.
  }
})

// --- 动作：退出登录 ---
const handleLogout = async () => {
  try {
    await logoutApi()
  } catch (_error) {
    // Best-effort logout.
  }
  socketStore.disconnect()
  authStore.logout()
  await router.push('/login')
  ElMessage.success('已退出系统')
}

const handleSettingsClick = async () => {
  const targetRoute = visibleSystemMenu.value ? { name: 'Settings' } : { name: 'AccountSecurity' }
  if (route.name === targetRoute.name) return
  await router.push(targetRoute)
}
</script>

<template>
  <el-container class="layout-container">
    <el-aside
      width="240px"
      class="sidebar"
    >
      <div class="logo-area">
        <el-icon
          class="logo-icon"
          size="24"
          color="#3b82f6"
        >
          <Odometer />
        </el-icon>
        <span class="logo-text">PARK EMS</span>
      </div>
    
      <el-menu
        :default-active="route.path"
        class="el-menu-vertical"
        background-color="transparent"
        text-color="#94a3b8"
        active-text-color="#fff"
        router
      >
        <div class="menu-header">园区主线</div>
        <el-menu-item index="/dashboard">
          <el-icon><DataLine /></el-icon>
          <span>首页驾驶舱</span>
        </el-menu-item>
        <el-menu-item index="/campus-overview">
          <el-icon><OfficeBuilding /></el-icon>
          <span>园区总览</span>
        </el-menu-item>
        <el-menu-item index="/energy">
          <el-icon><Lightning /></el-icon>
          <span>区域/楼栋能耗</span>
        </el-menu-item>
        <el-menu-item index="/devices">
          <el-icon><Cpu /></el-icon>
          <span>设备与表计</span>
        </el-menu-item>
        <el-menu-item index="/alarms">
          <el-icon><Bell /></el-icon>
          <span>告警中心</span>
        </el-menu-item>
        <el-menu-item index="/forecast">
          <el-icon><TrendCharts /></el-icon>
          <span>能耗分析</span>
        </el-menu-item>

        <div class="menu-header">运行与运维</div>
        <el-menu-item index="/spaces">
          <el-icon><Location /></el-icon>
          <span>园区空间</span>
        </el-menu-item>
        <el-menu-item index="/groups">
          <el-icon><Folder /></el-icon>
          <span>子系统分组</span>
        </el-menu-item>
        <el-menu-item index="/fdd">
          <el-icon><FirstAidKit /></el-icon>
          <span>实时监测</span>
        </el-menu-item>
        <el-menu-item index="/maintenance">
          <el-icon><Tools /></el-icon>
          <span>设备维护</span>
        </el-menu-item>
        <el-menu-item index="/inspection">
          <el-icon><Compass /></el-icon>
          <span>巡检计划</span>
        </el-menu-item>
        <el-menu-item index="/report">
          <el-icon><Files /></el-icon>
          <span>数据报表</span>
        </el-menu-item>
            
        <div class="menu-header">
          账户
        </div>
        <el-menu-item index="/account/security">
          <el-icon><Lock /></el-icon>
          <span>账户安全</span>
        </el-menu-item>

        <template v-if="visibleSystemMenu">
          <div class="menu-header">系统设置</div>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
          <el-menu-item index="/users">
            <el-icon><UserFilled /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="/audit">
            <el-icon><Document /></el-icon>
            <span>审计日志</span>
          </el-menu-item>
        </template>
      </el-menu>
    
      <div class="user-profile">
        <div class="avatar">
          <el-icon><UserFilled /></el-icon>
        </div>
        <div class="user-info">
          <div class="name">
            {{ authStore.username || 'Admin' }}
          </div>
          <div class="role">
            {{ roleLabel }}
          </div>
          <div class="scope">
            {{ scopeLabel }}
          </div>
        </div>
        <el-button
          link
          class="logout-btn"
          @click="handleLogout"
        >
          <el-icon size="18">
            <SwitchButton />
          </el-icon>
        </el-button>
      </div>
    </el-aside>
    
    <el-container>
      <el-header class="top-header">
        <div class="breadcrumb">
          <span>当前页面 / {{ route.meta.title || '系统设置' }}</span>
        </div>
    
        <div class="header-tools">
          <AlarmPopover />
    
          <el-button
            circle
            class="tool-item"
            @click="handleSettingsClick"
          >
            <el-icon><Setting /></el-icon>
          </el-button>
        </div>
      </el-header>
    
      <el-main class="main-content">
        <div class="content-wrapper">
          <router-view v-slot="{ Component }">
            <transition
              name="fade"
              mode="out-in"
            >
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
  font-weight: 700;
  font-size: 17px;
  color: #fff;
  letter-spacing: 0.04em;
}

.menu-header {
  font-size: 11px;
  color: var(--text-muted);
  padding: 18px 20px 8px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* 覆盖 Element Menu 默认样式以适配暗黑主题 */
:deep(.el-menu) {
  border-right: none;
  padding: 8px 12px 16px;
}

:deep(.el-menu-item) {
  height: 42px;
  margin-bottom: 6px;
  border-radius: 10px;
  color: var(--text-secondary) !important;
}

:deep(.el-menu-item .el-icon) {
  font-size: 16px;
}

:deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.04) !important;
  color: #fff !important;
}

:deep(.el-menu-item.is-active) {
  background-color: rgba(59, 130, 246, 0.12) !important;
  box-shadow: inset 3px 0 0 0 var(--brand-color);
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
  width: 36px;
  height: 36px;
  background: #334155;
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      color: #fff;
    }
    .user-info { flex: 1; }
    .user-info .name { font-size: 14px; font-weight: 600; color: #fff; }
	    .user-info .role { font-size: 12px; color: var(--success-color); }
	    .user-info .scope { font-size: 11px; color: var(--text-muted); }
    .logout-btn { color: var(--text-secondary); }
    .logout-btn:hover { color: var(--danger-color); }
    
    /* --- 顶部 Header --- */
    .top-header {
      background-color: #111a28;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 60px;
      padding: 0 20px;
    }
    .breadcrumb { color: var(--text-secondary); font-size: 13px; }
    
    .header-tools { display: flex; gap: 15px; align-items: center; }
    .tool-item {
      background: #162130;
      border: 1px solid var(--border-color);
      color: var(--text-secondary);
    }
    .has-alarm { 
      color: var(--danger-color) !important; 
      animation: pulse 2s infinite; 
    }
    
    /* --- 主内容区 --- */
    .main-content {
      padding: 16px !important;
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
