import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/useAuthStore'

// 路由表
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      // 路由懒加载：访问时才加载文件
      component: () => import('@/views/Login.vue')
    },
    {
      path: '/',
      name: 'Layout',
      component: () => import('@/layout/Layout.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: 'account/security',
          name: 'AccountSecurity',
          component: () => import('@/views/AccountSecurity.vue'),
          meta: { title: '账户安全' }
        },
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
          meta: { title: '首页总览' }
        },
        {
          path: 'campus-overview',
          name: 'CampusOverview',
          component: () => import('@/views/CampusScene.vue'),
          meta: { title: '园区总览' }
        },
        {
          path: 'devices',
          name: 'Devices',
          component: () => import('@/views/DeviceManager.vue'),
          meta: { title: '设备与表计' }
        },
        {
          path: 'devices/:id/monitor',
          name: 'DeviceMonitor',
          component: () => import('@/views/DeviceMonitor.vue'),
          meta: { title: '实时监控' }
        },
        {
          path: 'devices/:id/console',
          name: 'DeviceControlConsole',
          component: () => import('@/views/DeviceControlConsole.vue'),
          meta: { title: '设备控制台' }
        },
        {
          path: 'spaces',
          name: 'Locations',
          component: () => import('@/views/LocationManager.vue'),
          meta: { title: '园区空间' }
        },
        {
          path: 'groups',
          name: 'Groups',
          component: () => import('@/views/DeviceGroups.vue'),
          meta: { title: '子系统分组' }
        },
        {
          path: 'alarms',
          name: 'Alarms',
          component: () => import('@/views/AlarmCenter.vue'),
          meta: { title: '告警中心' }
        },
        {
          path: 'energy',
          name: 'Energy',
          component: () => import('@/views/EnergyManagement.vue'),
          meta: { title: '区域/楼栋能耗' }
        },
        {
          path: 'forecast',
          name: 'EnergyAnalysis',
          component: () => import('@/views/EnergyAnalysis.vue'),
          meta: { title: '能耗分析' }
        },
        {
          path: 'forecast-tools',
          name: 'Forecast',
          component: () => import('@/views/Forecast.vue'),
          meta: { title: '预测 / 模型工具' }
        },
        {
          path: 'fdd',
          name: 'FDD',
          component: () => import('@/views/FDD.vue'),
          meta: { title: '运行诊断' }
        },
        {
          path: 'maintenance',
          name: 'Maintenance',
          component: () => import('@/views/Maintenance.vue'),
          meta: { title: '设备维护' }
        },
        {
          path: 'inspection',
          name: 'Inspection',
          component: () => import('@/views/Inspection.vue'),
          meta: { title: '巡检运维' }
        },
        {
          path: 'report',
          name: 'Report',
          component: () => import('@/views/Report.vue'),
          meta: { title: '数据报表' }
        },
        {
          path: 'settings',
          name: 'Settings',
          component: () => import('@/views/SystemSettings.vue'),
          meta: { title: '系统设置', roles: ['admin'] }
        },
        {
          path: 'users',
          name: 'Users',
          component: () => import('@/views/UserManagement.vue'),
          meta: { title: '用户管理', roles: ['admin'] }
        },
        {
          path: 'audit',
          name: 'Audit',
          component: () => import('@/views/AuditCenter.vue'),
          meta: { title: '审计日志', roles: ['admin'] }
        }
      ]
    },
    {
      path: '/403',
      name: 'Forbidden',
      component: () => import('@/views/Forbidden.vue')
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/NotFound.vue')
    }
  ]
})

// 🛡️ 全局路由守卫
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  
  if (to.name === 'Login') {
    if (authStore.token) {
      next({ name: 'Dashboard' })
    } else {
      next()
    }
    return
  }

  if (!authStore.token) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else {
    const routeRoles = to.meta.roles as string[] | undefined
    const currentRole = authStore.role?.toLowerCase()
    if (authStore.mustChangePassword && to.name !== 'AccountSecurity') {
      next({ name: 'AccountSecurity' })
      return
    }
    if (routeRoles?.length && (!currentRole || !routeRoles.includes(currentRole))) {
      next({ name: 'Forbidden' })
      return
    }
    next()
  }
})

export default router
