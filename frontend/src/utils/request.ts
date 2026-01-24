import axios, { type InternalAxiosRequestConfig, type AxiosResponse } from 'axios'
import { useAuthStore } from '@/stores/useAuthStore' // 稍后会创建这个 Store
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const service = axios.create({
  baseURL: '', // 配合 vite.config.ts 的 proxy
  timeout: 5000,
  headers: { 'Content-Type': 'application/json' }
})

// 🟢 请求拦截器
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 每次发送请求前，检查 pinia 里有没有 token
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error: any) => {
    return Promise.reject(error)
  }
)

// 🔵 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    // 只要 HTTP 状态码是 2xx，就认为成功，直接返回数据部分
    return response.data
  },
  (error: any) => {
    // 处理 HTTP 错误状态码
    const status = error.response?.status
    const msg = error.response?.data?.detail || '网络请求失败'

    if (status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      const authStore = useAuthStore()
      authStore.logout()
      // 清除token后，通过修改URL触发路由守卫重新检查
      // 避免使用reload，改用更优雅的路由跳转
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    } else {
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

export default service