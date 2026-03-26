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

export const useSocketStore = defineStore('socket', () => {
  const isConnected = ref(false)
  const latestMessage = ref<SocketMessage | null>(null) // 存放最新收到的遥测数据
  let ws: WebSocket | null = null
  let retryCount = 0
  let retryTimer: ReturnType<typeof setTimeout> | null = null
  let isManualDisconnect = false // 标记是否为手动断开
  let useDirectConnection = false // 是否使用直接连接（绕过 Vite 代理）

  function connect() {
    const authStore = useAuthStore()
    if (!authStore.token) {
      console.warn('⚠️ [WebSocket] 当前无 access token，跳过连接')
      return
    }

    // 检查是否已有连接且处于连接中或已连接状态
    if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
      console.log('⚠️ [WebSocket] 连接已存在，跳过重复连接')
      return
    }

    // 清理之前的连接
    if (ws) {
      try {
        ws.close()
      } catch (e) {
        // 忽略关闭错误
      }
      ws = null
    }

    // 如果是手动断开，不自动重连
    if (isManualDisconnect) {
      console.log('ℹ️ [WebSocket] 手动断开，不自动重连')
      return
    }

    // WebSocket 连接地址
    // 开发环境：优先通过 Vite 代理连接，失败则直接连接后端
    // 生产环境：直接连接后端
    const isDev = import.meta.env.DEV
    let wsUrl: string
    
    if (isDev) {
      // 开发环境：根据 useDirectConnection 标志选择连接方式
      if (useDirectConnection) {
        // 直接连接后端（绕过 Vite 代理）
        wsUrl = 'ws://localhost:8088/ws'
        console.log(`🔌 [WebSocket] 开发环境 - 直接连接后端: ${wsUrl}`)
      } else {
        // 通过 Vite 代理连接
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const host = window.location.host
        wsUrl = `${protocol}//${host}/ws`
        console.log(`🔌 [WebSocket] 开发环境 - 通过 Vite 代理连接: ${wsUrl}`)
      }
    } else {
      // 生产环境：直接连接后端
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      wsUrl = `${protocol}//${window.location.host}/ws`
    }

    console.log(`🔌 [WebSocket] 尝试连接: ${wsUrl}`)
    console.log(`📋 [WebSocket] 环境信息:`, {
      isDev,
      host: window.location.host,
      protocol: window.location.protocol,
      href: window.location.href
    })
    
    const separator = wsUrl.includes('?') ? '&' : '?'
    const authenticatedWsUrl = `${wsUrl}${separator}access_token=${encodeURIComponent(authStore.token)}`

    try {
      ws = new WebSocket(authenticatedWsUrl)

      ws.onopen = () => {
        console.log('✅ [WebSocket] 连接成功')
        isConnected.value = true
        retryCount = 0
        isManualDisconnect = false
        
        // 清除重连定时器
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

      ws.onerror = (error) => {
        console.error('❌ [WebSocket] 连接错误:', error)
        console.error('连接地址:', authenticatedWsUrl)
        console.error('WebSocket 状态:', ws?.readyState)
        console.error('提示: 请确认后端服务运行在 http://localhost:8088')
        
        // 开发环境下，如果通过代理连接失败，尝试直接连接后端
        const isDev = import.meta.env.DEV
        if (isDev && retryCount === 0 && wsUrl.includes(window.location.host)) {
          console.warn('⚠️ [WebSocket] Vite 代理连接失败，将在重连时尝试直接连接后端')
        }
        
        console.error('💡 排查步骤:')
        console.error('   1. 检查后端服务是否运行: curl http://localhost:8088/docs')
        console.error('   2. 检查 Docker 容器状态: docker compose ps')
        console.error('   3. 查看后端日志: docker compose logs -f backend')
        console.error('   4. 检查 Vite 代理配置: frontend/vite.config.ts')
        
        // 只在首次连接失败时显示通知
        if (retryCount === 0) {
          ElNotification({
            title: 'WebSocket 连接失败',
            message: '无法连接到后端服务，请检查后端是否运行在 http://localhost:8088',
            type: 'error',
            duration: 5000
          })
        }
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          console.log('📨 [WebSocket] 收到消息:', msg)
          // 将收到的消息存入响应式变量，任何组件都可以监听这个变量的变化
          latestMessage.value = msg
        } catch (e) {
          console.error('❌ [WebSocket] 消息解析错误:', e, '原始数据:', event.data)
        }
      }

      ws.onclose = (event) => {
        const closeCode = event.code
        const closeReason = event.reason || '无'
        const wasClean = event.wasClean
        
        console.log(`❌ [WebSocket] 连接断开`)
        console.log(`   Code: ${closeCode}${closeCode === 1006 ? ' (异常关闭，通常表示连接失败)' : ''}`)
        console.log(`   Reason: ${closeReason}`)
        console.log(`   WasClean: ${wasClean}`)
        console.log(`   连接地址: ${authenticatedWsUrl}`)
        
        // 常见错误代码说明
        if (closeCode === 1006) {
          console.error('💡 错误代码 1006 通常表示:')
          console.error('   - 后端服务未运行')
          console.error('   - 网络连接问题')
          console.error('   - Vite 代理配置问题')
          console.error('   - 防火墙阻止连接')
        }
        
        isConnected.value = false
        
        // 清理 WebSocket 引用
        ws = null
        
        // 如果是手动断开，不自动重连
        if (isManualDisconnect) {
          console.log('ℹ️ [WebSocket] 手动断开，不自动重连')
          return
        }
        
        // 自动重连机制
        if (retryCount < 5) {
          retryCount++
          const delay = Math.min(3000 * retryCount, 10000) // 递增延迟，最多10秒
          
          // 开发环境下，如果代理连接失败，尝试直接连接后端
          const isDev = import.meta.env.DEV
          if (isDev && retryCount === 2 && !useDirectConnection) {
            console.warn('⚠️ [WebSocket] Vite 代理连接失败，切换到直接连接后端')
            useDirectConnection = true // 切换到直接连接
            console.log(`🔄 [WebSocket] ${delay / 1000}秒后尝试直接连接后端: ws://localhost:8088/ws`)
          } else {
            console.log(`🔄 [WebSocket] ${delay / 1000}秒后尝试重连 (${retryCount}/5)...`)
          }
          
          retryTimer = setTimeout(() => {
            connect()
          }, delay)
        } else {
          console.error('❌ [WebSocket] 重连次数已达上限，请检查后端服务')
          console.error('💡 请执行以下命令检查后端服务:')
          console.error('   docker compose ps')
          console.error('   docker compose logs backend')
          console.error('   curl http://localhost:8088/docs')
          
          ElNotification({
            title: 'WebSocket 连接失败',
            message: '重连次数已达上限，请检查后端服务是否正常运行',
            type: 'error',
            duration: 0 // 不自动关闭
          })
        }
      }
    } catch (error) {
      console.error('❌ [WebSocket] 创建连接失败:', error)
      ws = null
      isConnected.value = false
      
      // 尝试重连
      if (retryCount < 5) {
        retryCount++
        retryTimer = setTimeout(() => {
          connect()
        }, 3000)
      }
    }
  }

  function disconnect() {
    isManualDisconnect = true
    
    // 清除重连定时器
    if (retryTimer) {
      clearTimeout(retryTimer)
      retryTimer = null
    }
    
    if (ws) {
      try {
        ws.close(1000, '手动断开')
      } catch (e) {
        console.error('关闭 WebSocket 时出错:', e)
      }
      ws = null
    }
    
    isConnected.value = false
    useDirectConnection = false // 重置连接方式
    console.log('ℹ️ [WebSocket] 手动断开连接')
  }

  // 手动切换连接方式（用于调试）
  function toggleConnectionMode() {
    useDirectConnection = !useDirectConnection
    console.log(`🔄 [WebSocket] 切换连接方式: ${useDirectConnection ? '直接连接' : 'Vite 代理'}`)
    if (ws) {
      disconnect()
      setTimeout(() => connect(), 1000)
    }
  }

  return { isConnected, latestMessage, connect, disconnect, toggleConnectionMode }
})
