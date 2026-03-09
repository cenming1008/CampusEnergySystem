# 前端开发快速参考

> 矿区能源管理系统前端开发指南

## 📋 目录

- [开发环境配置](#开发环境配置)
- [项目启动](#项目启动)
- [开发规范](#开发规范)
- [常用命令](#常用命令)
- [调试技巧](#调试技巧)
- [常见问题](#常见问题)

## 🔧 开发环境配置

### 必备工具

- **Node.js**: >= 16.x （推荐使用 18.x 或 20.x）
- **包管理器**: npm >= 8.x 或 pnpm
- **编辑器**: VS Code（推荐）

### VS Code 推荐插件

```json
{
  "recommendations": [
    "vue.volar",              // Vue 3 语言支持
    "dbaeumer.vscode-eslint", // ESLint
    "esbenp.prettier-vscode", // Prettier
    "bradlc.vscode-tailwindcss", // Tailwind CSS（如果使用）
    "antfu.iconify"           // 图标预览
  ]
}
```

### 安装依赖

```bash
cd frontend
npm install
```

或使用 pnpm（更快）：

```bash
pnpm install
```

## 🚀 项目启动

### 开发模式

```bash
npm run dev
```

默认运行在 http://localhost:3000

- 支持热更新（HMR）
- WebSocket 代理到后端 ws://localhost:8000/ws
- API 请求代理到 http://localhost:8000

### 生产构建

```bash
npm run build
```

构建产物输出到 `dist/` 目录。

### 预览生产构建

```bash
npm run preview
```

## 📝 开发规范

### 目录结构约定

```
src/
├── api/          # API 接口（按模块划分）
├── assets/       # 静态资源（图片、样式等）
├── components/   # 通用组件
├── layout/       # 布局组件
├── router/       # 路由配置
├── stores/       # Pinia 状态管理
├── utils/        # 工具函数
├── views/        # 页面组件
└── types/        # TypeScript 类型定义
```

### 命名规范

#### 文件命名

- **组件文件**: PascalCase
  ```
  DeviceManager.vue
  DataTable.vue
  ```

- **工具文件**: camelCase
  ```
  request.ts
  formatDate.ts
  ```

- **类型文件**: PascalCase
  ```
  Device.ts
  User.ts
  ```

#### 代码命名

```typescript
// 组件名称 - PascalCase
const DeviceCard = defineComponent({ ... })

// 变量和函数 - camelCase
const deviceList = ref([])
const fetchDeviceList = async () => { ... }

// 常量 - UPPER_SNAKE_CASE
const API_BASE_URL = 'http://localhost:8000'
const MAX_RETRY_COUNT = 3

// 类型和接口 - PascalCase
interface Device {
  id: string
  name: string
}

type DeviceStatus = 'online' | 'offline'
```

### 代码风格

#### Vue 组件结构（Composition API）

```vue
<template>
  <div class="device-manager">
    <!-- 模板内容 -->
  </div>
</template>

<script setup lang="ts">
// 1. 导入
import { ref, computed, onMounted } from 'vue'
import { useDeviceStore } from '@/stores/useDeviceStore'
import type { Device } from '@/types/device'

// 2. Props & Emits
interface Props {
  deviceId?: string
}
const props = defineProps<Props>()
const emit = defineEmits<{
  update: [device: Device]
}>()

// 3. Store（示例：当前项目无 useDeviceStore，可直接用 getDevices 等 API）
const deviceStore = useDeviceStore()

// 4. 响应式数据
const deviceList = ref<Device[]>([])
const loading = ref(false)

// 5. 计算属性
const onlineDevices = computed(() => {
  return deviceList.value.filter(d => d.status === 'online')
})

// 6. 方法
const fetchDevices = async () => {
  loading.value = true
  try {
    deviceList.value = await deviceStore.fetchDevices()
  } finally {
    loading.value = false
  }
}

// 7. 生命周期
onMounted(() => {
  fetchDevices()
})
</script>

<style scoped>
.device-manager {
  /* 样式 */
}
</style>
```

#### API 接口定义

```typescript
// src/api/device.ts
import request from '@/utils/request'

export interface Device {
  id: string
  name: string
  status: 'online' | 'offline'
  // ...
}

export interface DeviceListParams {
  page?: number
  pageSize?: number
  status?: string
}

// 获取设备列表
export const getDeviceList = (params?: DeviceListParams) => {
  return request.get<Device[]>('/api/devices', { params })
}

// 获取设备详情
export const getDeviceDetail = (id: string) => {
  return request.get<Device>(`/api/devices/${id}`)
}

// 更新设备
export const updateDevice = (id: string, data: Partial<Device>) => {
  return request.put<Device>(`/api/devices/${id}`, data)
}
```

#### Pinia Store（示例）

> 说明：以下 `useDeviceStore` 为**示例写法**，当前项目中并未实现该 Store，设备数据由各页面直接调用 `@/api/device` 获取。若需全局设备状态可参考此结构新增。

```typescript
// src/stores/useDeviceStore.ts（示例，项目中暂无此文件）
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getDeviceList } from '@/api/device'
import type { Device } from '@/api/device'

export const useDeviceStore = defineStore('device', () => {
  // State
  const devices = ref<Device[]>([])
  const loading = ref(false)

  // Getters
  const onlineDevices = computed(() => {
    return devices.value.filter(d => d.status === 'online')
  })

  // Actions
  const fetchDevices = async () => {
    loading.value = true
    try {
      const data = await getDeviceList()
      devices.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  return {
    devices,
    loading,
    onlineDevices,
    fetchDevices
  }
})
```

## 🛠️ 常用命令

### 开发命令

```bash
# 启动开发服务器
npm run dev

# 类型检查
vue-tsc --noEmit

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

### 依赖管理

```bash
# 安装依赖
npm install

# 添加新依赖
npm install package-name

# 添加开发依赖
npm install -D package-name

# 更新依赖
npm update

# 查看过时的依赖
npm outdated
```

### 清理命令

```bash
# 清除 node_modules
rm -rf node_modules

# 清除 Vite 缓存
rm -rf node_modules/.vite

# 重新安装依赖
npm install
```

## 🐛 调试技巧

### Vue DevTools

1. 安装 Vue DevTools 浏览器插件
2. 在开发模式下打开浏览器控制台
3. 切换到 Vue 标签页

### 网络请求调试

在 `src/utils/request.ts` 中添加日志：

```typescript
// 请求拦截器
request.interceptors.request.use(
  config => {
    console.log('🚀 Request:', config.method?.toUpperCase(), config.url)
    return config
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    console.log('✅ Response:', response.config.url, response.data)
    return response
  }
)
```

### WebSocket 调试

```typescript
// 在 stores/useSocketStore.ts 中添加日志
socket.onmessage = (event) => {
  const data = JSON.parse(event.data)
  console.log('📨 WebSocket Message:', data)
  // ...
}
```

### Three.js 调试

```typescript
// 添加性能监视器
import Stats from 'three/examples/jsm/libs/stats.module'

const stats = new Stats()
document.body.appendChild(stats.dom)

// 在动画循环中更新
function animate() {
  stats.update()
  renderer.render(scene, camera)
}
```

## ❓ 常见问题

### 1. 端口被占用

```bash
# 查找占用端口的进程
lsof -i :3000

# 杀死进程
kill -9 <PID>

# 或使用不同端口
vite --port 3001
```

### 2. 热更新不生效

```bash
# 清除 Vite 缓存
rm -rf node_modules/.vite

# 重启开发服务器
npm run dev
```

### 3. WebSocket 连接失败

检查 `vite.config.ts` 中的代理配置：

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
})
```

### 4. TypeScript 类型错误

```bash
# 运行类型检查
vue-tsc --noEmit

# 如果是第三方库类型问题，安装类型定义
npm install -D @types/package-name
```

### 5. Element Plus 样式不显示

确保在 `main.ts` 中导入了样式：

```typescript
import 'element-plus/dist/index.css'
```

### 6. 3D 模型加载失败

检查：
- 模型文件路径是否正确
- Draco 解码器路径配置
- 浏览器控制台错误信息

### 7. API 请求 CORS 错误

确保：
- 后端正确配置了 CORS
- Vite 代理配置正确
- 使用相对路径而不是完整 URL

## 📚 参考资源

### 官方文档

- [Vue 3 文档](https://cn.vuejs.org/)
- [Vite 文档](https://cn.vitejs.dev/)
- [Element Plus 文档](https://element-plus.org/zh-CN/)
- [Pinia 文档](https://pinia.vuejs.org/zh/)
- [Three.js 文档](https://threejs.org/docs/)

### 推荐阅读

- [Vue 3 组合式 API 常见问答](https://cn.vuejs.org/guide/extras/composition-api-faq.html)
- [TypeScript 与组合式 API](https://cn.vuejs.org/guide/typescript/composition-api.html)
- [Vite 特性](https://cn.vitejs.dev/guide/features.html)

## 🔗 相关文档

- [README.md](./README.md) - 项目概述
- [后端 API 文档](../docs/02-功能使用/) - 后端接口文档
- [部署指南](../docs/03-开发与部署/) - 部署相关文档

---

**最后更新**: 2026-01-24
