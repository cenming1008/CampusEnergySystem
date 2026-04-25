/// <reference types="node" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'url'
import path from 'path'

const backendTarget = 'http://127.0.0.1:8088'

function spaAwareProxy(overlapWithSpa: boolean = false) {
  return {
    target: backendTarget,
    changeOrigin: true,
    secure: false,
    bypass(req: { method?: string; headers?: Record<string, string | string[] | undefined> }) {
      if (!overlapWithSpa || req.method !== 'GET') return
      const acceptHeader = req.headers?.accept
      const accept = Array.isArray(acceptHeader) ? acceptHeader.join(',') : (acceptHeader || '')
      if (accept.includes('text/html')) {
        return '/index.html'
      }
    },
  }
}

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
      '/auth': spaAwareProxy(false),
      '/devices': spaAwareProxy(true),
      '/alarms': spaAwareProxy(true),
      '/analysis': spaAwareProxy(false),
      '/fdd': spaAwareProxy(true),
      '/reports': spaAwareProxy(false),
      '/energy/': spaAwareProxy(false),
      '/maintenance': spaAwareProxy(true),
      '/inspection': spaAwareProxy(true),
      '/locations': spaAwareProxy(false),
      '/campus': spaAwareProxy(false),
      '/device-groups': spaAwareProxy(false),
      '/data-cleanup': spaAwareProxy(false),
      '/health': spaAwareProxy(false),
      '/metrics': spaAwareProxy(false),
      '/users': spaAwareProxy(true),
      '/audit': spaAwareProxy(true),
      '/frontend-errors': spaAwareProxy(false),
      // WebSocket 代理
      '/ws': {
        target: backendTarget,
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
  },

  build: {
    sourcemap: 'hidden',
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return

          if (id.includes('/three/')) {
            return 'three-vendor'
          }

          if (id.includes('/echarts/')) {
            return 'echarts-vendor'
          }

          if (id.includes('/element-plus/') || id.includes('/@element-plus/')) {
            return 'ui-vendor'
          }

          if (
            id.includes('/vue/') ||
            id.includes('/vue-router/') ||
            id.includes('/pinia/') ||
            id.includes('/axios/')
          ) {
            return 'core-vendor'
          }

          return 'vendor'
        }
      }
    }
  }
})
