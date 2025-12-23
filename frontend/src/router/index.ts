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
          path: 'devices',
          name: 'Devices',
          component: () => import('@/views/DeviceManager.vue'),
          meta: { title: '设备台账' }
        },
        {
          path: 'fdd',
          name: 'FDD',
          component: () => import('@/views/FDD.vue'),
          meta: { title: '故障诊断' }
        },
        {
            path: 'report',
            name: 'Report',
            component: () => import('@/views/Report.vue'),
            meta: { title: '报表导出' }
        }
      ]
    },
    // 404 页面
    {
      path: '/:pathMatch(.*)*',
      redirect: '/dashboard'
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