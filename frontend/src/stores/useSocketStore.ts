import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElNotification } from 'element-plus'
import { useAuthStore } from '@/stores/useAuthStore'

interface SocketTelemetryPayload {
  device_id?: number
  power?: number
  current?: number
  voltage?: number
  timestamp?: string
}

export interface SocketMessage {
  type?: string
  data?: SocketTelemetryPayload
}

const MAX_RETRIES = 5

function buildWsUrl(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws`
}

export const useSocketStore = defineStore('socket', () => {
  const isConnected = ref(false)
  const latestMessage = ref<SocketMessage | null>(null)
  let ws: WebSocket | null = null
  let retryCount = 0
  let retryTimer: ReturnType<typeof setTimeout> | null = null
  let isManualDisconnect = false

  function connect() {
    const authStore = useAuthStore()
    if (!authStore.token) return

    if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) return

    if (ws) {
      try { ws.close() } catch { /* ignore */ }
      ws = null
    }

    isManualDisconnect = false

    const wsUrl = buildWsUrl()
    const separator = wsUrl.includes('?') ? '&' : '?'
    const authenticatedWsUrl = `${wsUrl}${separator}access_token=${encodeURIComponent(authStore.token)}`

    try {
      ws = new WebSocket(authenticatedWsUrl)

      ws.onopen = () => {
        isConnected.value = true
        retryCount = 0
        isManualDisconnect = false

        if (retryTimer) {
          clearTimeout(retryTimer)
          retryTimer = null
        }

        ElNotification({
          title: 'WebSocket 连接成功',
          message: '实时数据推送已启用',
          type: 'success',
          duration: 2000
        })
      }

      ws.onerror = () => {
        if (retryCount === 0) {
          ElNotification({
            title: 'WebSocket 连接失败',
            message: '无法连接到后端服务，请检查服务是否正常运行',
            type: 'error',
            duration: 5000
          })
        }
      }

      ws.onmessage = (event) => {
        try {
          latestMessage.value = JSON.parse(event.data)
        } catch {
          // 消息解析失败，忽略非 JSON 帧
        }
      }

      ws.onclose = (event) => {
        isConnected.value = false
        ws = null

        if (isManualDisconnect) return

        if (retryCount < MAX_RETRIES) {
          retryCount++
          const delay = Math.min(3000 * retryCount, 10000)
          retryTimer = setTimeout(() => connect(), delay)
        } else {
          ElNotification({
            title: 'WebSocket 连接失败',
            message: `连接断开(code=${event.code})，重连次数已达上限，请检查后端服务`,
            type: 'error',
            duration: 0
          })
        }
      }
    } catch {
      ws = null
      isConnected.value = false

      if (retryCount < MAX_RETRIES) {
        retryCount++
        retryTimer = setTimeout(() => connect(), 3000)
      }
    }
  }

  function disconnect() {
    isManualDisconnect = true

    if (retryTimer) {
      clearTimeout(retryTimer)
      retryTimer = null
    }

    if (ws) {
      try { ws.close(1000, '手动断开') } catch { /* ignore */ }
      ws = null
    }

    isConnected.value = false
  }

  return { isConnected, latestMessage, connect, disconnect }
})
