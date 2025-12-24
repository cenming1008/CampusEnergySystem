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
    host: '0.0.0.0', // 允许外部访问（WSL2 需要）
    port: 5173, // 前端开发端口
    open: true, // 启动时自动打开浏览器
    
    // ⚡️ 关键配置：反向代理
    // 让前端请求 /auth, /devices 等接口时，自动转发给后端 FastAPI (8088)
    // 解决跨域问题 (CORS)
    proxy: {
      '/auth': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true,
        secure: false
      },
      '/devices': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true,
        secure: false
      },
      '/telemetry': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true,
        secure: false
      },
      '/alarms': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true,
        secure: false
      },
      '/analysis': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true,
        secure: false
      },
      '/fdd': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true,
        secure: false
      },
      '/reports': {
        target: 'http://127.0.0.1:8088',
        changeOrigin: true,
        secure: false
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