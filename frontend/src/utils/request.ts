import axios, { AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/useAuthStore'
import { useSocketStore } from '@/stores/useSocketStore'
import { ElMessage } from 'element-plus'
import router from '@/router'
import type { AuthSession } from '@/api/auth'
import { reportFrontendError } from '@/observability/errorReporting'

interface SilentAxiosConfig extends InternalAxiosRequestConfig {
  silent?: boolean
  skipAuthRefresh?: boolean
  skipAuthHeader?: boolean
  _retry?: boolean
  timeout?: number
}

const TIMEOUT_DEFAULT = 15_000
const TIMEOUT_LONG = 60_000   // reports export, batch operations

const service = axios.create({
  baseURL: '',
  timeout: TIMEOUT_DEFAULT,
  headers: { 'Content-Type': 'application/json' }
})

export { TIMEOUT_LONG }

let refreshPromise: Promise<string | null> | null = null
let authFailureHandled = false

function resolveAuthErrorHint(message: string) {
  const normalized = message.toLowerCase()
  if (normalized.includes('not authenticated')) {
    return '请先登录'
  }
  if (message.includes('账户已锁定') || message.includes('账户已被锁定')) {
    return message
  }
  return '登录已过期或无效，请重新登录'
}

async function refreshAccessToken() {
  const authStore = useAuthStore()
  if (!authStore.refreshToken) {
    return null
  }

  if (!refreshPromise) {
    refreshPromise = service
      .post<{ refresh_token: string }, AuthSession>('/auth/refresh', { refresh_token: authStore.refreshToken }, {
        silent: true,
        skipAuthRefresh: true
      })
      .then((session) => {
        authStore.updateTokens(session)
        return session.access_token
      })
      .catch(() => {
        useSocketStore().disconnect()
        authStore.logout()
        return null
      })
      .finally(() => {
        refreshPromise = null
      })
  }

  return refreshPromise
}

// 🟢 请求拦截器
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 每次发送请求前，检查 pinia 里有没有 token
    const authStore = useAuthStore()
    const requestConfig = config as SilentAxiosConfig
    if (!requestConfig.skipAuthHeader && authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// 🔵 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    // 只要 HTTP 状态码是 2xx，就认为成功，直接返回数据部分
    authFailureHandled = false
    return response.data
  },
  async (error: AxiosError<{ detail?: string; message?: string }>) => {
    // 处理 HTTP 错误状态码
    const status = error.response?.status
    const msg =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      '网络请求失败'

    if (status === 401) {
      const authStore = useAuthStore()
      const requestConfig = error.config as SilentAxiosConfig | undefined
      const isLoginRequest = requestConfig?.url === '/auth/login'

      if (authStore.refreshToken && requestConfig && !requestConfig.skipAuthRefresh && !requestConfig._retry) {
        requestConfig._retry = true
        const refreshedToken = await refreshAccessToken()
        if (refreshedToken && requestConfig.headers) {
          requestConfig.headers.Authorization = `Bearer ${refreshedToken}`
          return service(requestConfig)
        }
      }

      const hint = resolveAuthErrorHint(String(msg))
      const shouldAlwaysShow = isLoginRequest || hint === msg
      if (shouldAlwaysShow || !authFailureHandled) {
        authFailureHandled = true
        ElMessage.error(hint)
      }
      useSocketStore().disconnect()
      authStore.logout()
      if (router.currentRoute.value.name !== 'Login') {
        router.push({ name: 'Login' })
      }
    } else if (status === 403 && typeof msg === 'string' && msg.includes('首次登录后必须先修改密码')) {
      const authStore = useAuthStore()
      authStore.mustChangePassword = true
      ElMessage.warning('请先完成密码修改后再继续使用系统')
      if (router.currentRoute.value.name !== 'AccountSecurity') {
        router.push({ name: 'AccountSecurity' })
      }
    } else {
      const requestConfig = error.config as SilentAxiosConfig | undefined
      if (!requestConfig?.silent) {
        ElMessage.error(msg)
      }
    }

    reportFrontendError({
      category: 'http',
      message: `${error.config?.method?.toUpperCase() ?? 'UNKNOWN'} ${error.config?.url ?? ''} → ${status ?? 'network_error'}: ${msg}`,
      url: window.location.href,
      route: window.location.pathname,
      metadata: { status, method: error.config?.method, endpoint: error.config?.url },
    })

    return Promise.reject(error)
  }
)

export default service
