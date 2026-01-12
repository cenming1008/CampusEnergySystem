/// <reference types="node" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'url'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  
  resolve: {
    alias: {
      // 设置 @ 指向 src 目录，方便引入组件 (例如: import X from '@/components/X')
      '@': path.resolve(fileURLToPath(new URL('.', import.meta.url)), 'src')
    }
  },

  server: {
    host: '0.0.0.0', // 允许外部访问（包括 localhost 和 127.0.0.1）
    port: 3000, // 前端开发端口
    open: true, // 启动时自动打开浏览器
    strictPort: false, // 如果端口被占用，自动选择其他端口

    // ⚡️ 关键配置：反向代理
    // 让前端请求 /auth, /devices 等接口时，自动转发给后端 FastAPI (8088)
    // 解决跨域问题 (CORS)
    proxy: {
      '/auth': {
        target: 'http://localhost:8088',  // 使用 localhost 代替 127.0.0.1，避免 VPN 干扰
        changeOrigin: true,
        secure: false
      },
      '/devices': {
        target: 'http://localhost:8088',
        changeOrigin: true,
        secure: false
      },
      '/telemetry': {
        target: 'http://localhost:8088',
        changeOrigin: true,
        secure: false
      },
      '/alarms': {
        target: 'http://localhost:8088',
        changeOrigin: true,
        secure: false
      },
      '/analysis': {
        target: 'http://localhost:8088',
        changeOrigin: true,
        secure: false
      },
      '/fdd': {
        target: 'http://localhost:8088',
        changeOrigin: true,
        secure: false
      },
      '/reports': {
        target: 'http://localhost:8088',
        changeOrigin: true,
        secure: false
      },
      // WebSocket 代理
      '/ws': {
        target: 'http://localhost:8088',  // Vite 会自动处理 WebSocket 升级，使用 http:// 即可
        ws: true,
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path,  // 保持路径不变
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('WebSocket 代理错误:', err);
          });
          proxy.on('proxyReqWs', (proxyReq, _req, _socket) => {
            console.log('WebSocket 代理请求:', proxyReq.path);
          });
        }
      }
    }
  }
})