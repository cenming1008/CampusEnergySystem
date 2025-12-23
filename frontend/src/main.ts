import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css' // 引入 ElementPlus 样式
import * as ElementPlusIconsVue from '@element-plus/icons-vue' // 引入图标

import App from './App.vue'
import router from './router'

// 引入全局样式 (稍后创建)
import './assets/main.css'

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus) // 使用 Element UI

app.mount('#app')