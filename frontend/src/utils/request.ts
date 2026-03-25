import axios, { type InternalAxiosRequestConfig, type AxiosResponse } from 'axios'
import { useAuthStore } from '@/stores/useAuthStore' // 稍后会创建这个 Store
import { ElMessage } from 'element-plus'

interface SilentAxiosConfig extends InternalAxiosRequestConfig {
  silent?: boolean
}

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
    const msg =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      '网络请求失败'

    if (status === 401) {
      // 401 可能是：Token 过期、Token 无效、未携带 Token、用户不存在等，统一提示并清除本地登录态
      const hint = typeof msg === 'string' && msg.toLowerCase().includes('not authenticated')
        ? '请先登录'
        : '登录已过期或无效，请重新登录'
      ElMessage.error(hint)
      const authStore = useAuthStore()
      authStore.logout()
      // 清除token后，通过修改URL触发路由守卫重新检查
      // 避免使用reload，改用更优雅的路由跳转
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    } else {
      const requestConfig = error.config as SilentAxiosConfig | undefined
      if (!requestConfig?.silent) {
        ElMessage.error(msg)
      }
    }
    return Promise.reject(error)
  }
)

export default service
