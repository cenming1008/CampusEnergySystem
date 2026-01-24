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
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
          meta: { title: '驾驶舱首页' }
        },
        {
          path: 'mine-scene',
          name: 'MineScene',
          component: () => import('@/views/MineScene.vue'),
          meta: { title: '矿区总览' }
        },
        {
          path: 'devices',
          name: 'Devices',
          component: () => import('@/views/DeviceManager.vue'),
          meta: { title: '设备台账' }
        },
        {
          path: 'locations',
          name: 'Locations',
          component: () => import('@/views/LocationManager.vue'),
          meta: { title: '位置管理' }
        },
        {
          path: 'groups',
          name: 'Groups',
          component: () => import('@/views/DeviceGroups.vue'),
          meta: { title: '设备分组' }
        },
        {
          path: 'energy',
          name: 'Energy',
          component: () => import('@/views/EnergyManagement.vue'),
          meta: { title: '多能源管理' }
        },
        {
          path: 'forecast',
          name: 'Forecast',
          component: () => import('@/views/Forecast.vue'),
          meta: { title: '负荷预测' }
        },
        {
          path: 'fdd',
          name: 'FDD',
          component: () => import('@/views/FDD.vue'),
          meta: { title: '故障诊断' }
        },
        {
          path: 'maintenance',
          name: 'Maintenance',
          component: () => import('@/views/Maintenance.vue'),
          meta: { title: '设备维护' }
        },
        {
          path: 'report',
          name: 'Report',
          component: () => import('@/views/Report.vue'),
          meta: { title: '报表导出' }
        },
        {
          path: 'settings',
          name: 'Settings',
          component: () => import('@/views/SystemSettings.vue'),
          meta: { title: '系统设置' }
        }
      ]
    },
    // 404 页面 - 所有未匹配的路径都重定向到首页
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      redirect: (to) => {
        // 由路由守卫判断是否需要登录
        return { path: '/' }
      }
    }
  ]
})

// 🛡️ 全局路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // 1. 如果去的是登录页，直接放行
  if (to.name === 'Login') {
    next()
    return
  }

  // 2. 检查是否有 Token
  if (!authStore.token) {
    // 没登录，强制去登录页
    next({ name: 'Login' })
  } else {
    // 已登录，放行
    next()
  }
})

export default router