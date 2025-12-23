import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  
  resolve: {
    alias: {
      // 设置 @ 指向 src 目录，方便引入组件 (例如: import X from '@/components/X')
      '@': path.resolve(__dirname, 'src')
    }
  },

  server: {
    port: 5173, // 前端开发端口
    open: true, // 启动时自动打开浏览器
    
    // ⚡️ 关键配置：反向代理
    // 让前端请求 /auth, /devices 等接口时，自动转发给后端 FastAPI (8088)
    // 解决跨域问题 (CORS)
    proxy: {
      '/auth': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true
      },
      '/devices': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true
      },
      '/telemetry': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true
      },
      '/alarms': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true
      },
      '/analysis': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true
      },
      '/fdd': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true
      },
      '/reports': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true
      },
      // WebSocket 代理
      '/ws': {
        target: 'ws://127.0.0.1:8088',
        ws: true,
        changeOrigin: true
      }
    }
  }
})