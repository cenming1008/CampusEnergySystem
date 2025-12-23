import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElNotification } from 'element-plus'

export const useSocketStore = defineStore('socket', () => {
  const isConnected = ref(false)
  const latestMessage = ref<any>(null) // 存放最新收到的遥测数据
  let ws: WebSocket | null = null
  let retryCount = 0

  function connect() {
    if (ws) return // 避免重复连接

    // 自动判断协议 (ws:// 或 wss://)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // 开发环境连 8088，生产环境连当前 host
    // 注意：这里硬编码了 8088，如果 vite 代理配置好了，也可以用 ws://location.host/ws
    const wsUrl = import.meta.env.DEV 
      ? `ws://127.0.0.1:8088/ws` 
      : `${protocol}//${window.location.host}/ws`

    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('✅ [WebSocket] 连接成功')
      isConnected.value = true
      retryCount = 0
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        // 将收到的消息存入响应式变量，任何组件都可以监听这个变量的变化
        latestMessage.value = msg
      } catch (e) {
        console.error('WS 解析错误', e)
      }
    }

    ws.onclose = () => {
      console.log('❌ [WebSocket] 连接断开')
      isConnected.value = false
      ws = null
      
      // 简单的自动重连机制
      if (retryCount < 5) {
        setTimeout(() => {
          retryCount++
          console.log(`正在尝试重连 (${retryCount}/5)...`)
          connect()
        }, 3000)
      }
    }
  }

  function disconnect() {
    if (ws) {
      ws.close()
      ws = null
    }
  }

  return { isConnected, latestMessage, connect, disconnect }
})