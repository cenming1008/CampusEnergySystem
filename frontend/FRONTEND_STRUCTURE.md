# 前端目录与文件说明（按实际文件整理）

> 基于当前仓库 `frontend/` 实际文件整理，无重复、无虚构。  
> 根目录配置与文档见 [README.md](./README.md)、[DEVELOPMENT.md](./DEVELOPMENT.md)。

---

## 一、目录树（仅源码与静态资源，不含 node_modules）

```
frontend/
├── public/                      # 静态资源（不经过 Vite 处理，原样输出）
│   ├── draco/                   # Draco 压缩库（glTF 模型解压用）
│   │   ├── gltf/*.js
│   │   └── *.js
│   ├── model/                   # 3D 模型（见 public/model/README.md）
│   └── textures/                # HDR 等贴图（如 023.hdr）
│
├── src/
│   ├── api/                     # 后端 API 封装（按业务模块）
│   ├── assets/                  # 需构建的静态资源
│   ├── layout/                  # 布局组件
│   ├── router/                  # 路由
│   ├── shaders/                 # WebGL 着色器（Three.js 用）
│   ├── stores/                  # Pinia 状态
│   ├── three/                   # Three.js 场景与特效
│   ├── utils/                   # 工具函数
│   ├── views/                   # 页面级组件（与路由一一对应）
│   ├── App.vue
│   └── main.ts
│
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── README.md
├── DEVELOPMENT.md
├── CHANGELOG.md
└── FRONTEND_STRUCTURE.md        # 本文件
```

---

## 二、src 下各目录与文件作用

### 1. `src/api/` — 接口层（14 个文件）

| 文件 | 作用 |
|------|------|
| **alarm.ts** | 告警：获取告警列表、确认/解决告警等 |
| **auth.ts** | 认证：登录、登出（Token） |
| **dataCleanup.ts** | 数据清理：清理策略、执行清理、清理统计（在系统设置页使用） |
| **device.ts** | 设备：设备 CRUD、列表、状态、控制等 |
| **deviceGroup.ts** | 设备分组：分组 CRUD、分组下设备 |
| **energy.ts** | 多能源：能耗统计、趋势、碳排放等 |
| **fdd.ts** | 故障诊断（FDD）：故障记录、统计 |
| **forecast.ts** | 负荷/能源预测：预测任务、结果查询 |
| **inspection.ts** | 巡检运维：巡检任务、记录、统计 |
| **location.ts** | 位置管理：位置树、CRUD、设备关联 |
| **maintenance.ts** | 设备维护：维护计划、任务、记录 |
| **report.ts** | 报表：报表生成、导出 |
| **telemetry.ts** | 遥测数据：实时/历史遥测查询 |
| **request.ts** | 不在 api/，在 utils/request.ts：Axios 实例、拦截器、Token 注入 |

### 2. `src/assets/`

| 文件 | 作用 |
|------|------|
| **main.css** | 全局样式、CSS 变量（主题色、背景等） |

### 3. `src/layout/`

| 文件 | 作用 |
|------|------|
| **Layout.vue** | 主布局：侧栏菜单、顶栏（面包屑、告警铃铛、用户）、主内容区 `<router-view>`；内含告警轮询与退出登录 |

### 4. `src/router/`

| 文件 | 作用 |
|------|------|
| **index.ts** | 路由定义：登录页、Layout 及所有子路由、404 重定向；全局前置守卫做登录校验（无 Token 跳登录） |

### 5. `src/shaders/` — 自定义着色器（Three.js 用）

| 目录/文件 | 作用 |
|-----------|------|
| **lightRadar/vertex.glsl** | 光雷达顶点着色器 |
| **lightRadar/fragment.glsl** | 光雷达片元着色器 |
| **lightWall/vertex.glsl** | 光墙顶点着色器 |
| **lightWall/fragment.glsl** | 光墙片元着色器 |

### 6. `src/stores/` — Pinia（仅 2 个 Store）

| 文件 | 作用 |
|------|------|
| **useAuthStore.ts** | 认证状态：token、username、login/logout、持久化（如 localStorage） |
| **useSocketStore.ts** | WebSocket 状态：连接、重连、订阅/推送消息（实时数据） |

说明：README 中曾提到的 `useDeviceStore` 当前**不存在**，设备相关状态由各页面自行请求或通过 Socket 更新。

### 7. `src/three/` — Three.js 相关

| 路径 | 作用 |
|------|------|
| **mine/index.ts** | 导出 MineSceneGenerator |
| **mine/MineSceneGenerator.ts** | 矿区 3D 场景生成：加载模型、布置设备、光照等 |
| **effects/index.ts** | 导出 LightWall、LightRadar、FlyLine、AlarmSprite |
| **effects/LightWall.ts** | 光墙特效 |
| **effects/LightRadar.ts** | 光雷达扫描特效 |
| **effects/FlyLine.ts** | 飞线动画 |
| **effects/AlarmSprite.ts** | 告警精灵（3D 场景内告警提示） |

### 8. `src/utils/`

| 文件 | 作用 |
|------|------|
| **request.ts** | Axios 实例、baseURL、请求/响应拦截器、携带 Token、统一错误与 401 处理 |

### 9. `src/views/` — 页面（与路由一一对应）

| 文件 | 路由 path | 作用 |
|------|-----------|------|
| **Login.vue** | /login | 登录页 |
| **Dashboard.vue** | /dashboard | 驾驶舱首页 |
| **CampusScene.vue** | /campus-overview | 园区总览（3D 场景） |
| **DeviceManager.vue** | /devices | 设备台账 |
| **LocationManager.vue** | /locations | 位置管理 |
| **DeviceGroups.vue** | /groups | 设备分组 |
| **EnergyManagement.vue** | /energy | 多能源管理 |
| **Forecast.vue** | /forecast | 负荷预测 |
| **FDD.vue** | /fdd | 故障诊断 |
| **Maintenance.vue** | /maintenance | 设备维护 |
| **Inspection.vue** | /inspection | 巡检运维 |
| **Report.vue** | /report | 报表导出 |
| **SystemSettings.vue** | /settings | 系统设置（含数据生成、数据清理、系统状态等） |

### 10. 入口与根组件

| 文件 | 作用 |
|------|------|
| **main.ts** | 创建 Vue 应用、挂载 Pinia、Router、全局样式、挂载 #app |
| **App.vue** | 根组件：仅包含 `<router-view />` |

---

## 三、路由与页面、API 对应关系（速查）

| 菜单/路由 | 页面组件 | 主要 API 模块 |
|-----------|----------|----------------|
| 驾驶舱首页 | Dashboard.vue | alarm、telemetry、device 等 |
| 园区总览 | CampusScene.vue | device、alarm、three 特效 |
| 设备台账 | DeviceManager.vue | device |
| 位置管理 | LocationManager.vue | location |
| 设备分组 | DeviceGroups.vue | deviceGroup、device |
| 多能源管理 | EnergyManagement.vue | energy |
| 负荷预测 | Forecast.vue | forecast、device |
| 故障诊断 | FDD.vue | fdd |
| 设备维护 | Maintenance.vue | maintenance |
| 巡检运维 | Inspection.vue | inspection |
| 报表导出 | Report.vue | report |
| 系统设置 | SystemSettings.vue | device、dataCleanup、request（数据生成/清理等） |

---

## 四、public 静态资源

| 路径 | 说明 |
|------|------|
| **public/draco/** | Draco 编解码脚本，用于 glTF 压缩模型加载 |
| **public/model/** | 3D 模型文件（.glb 等），见 public/model/README.md |
| **public/textures/** | HDR 等贴图，见 public/textures/README.md |

---

## 五、统计

| 类型 | 数量 |
|------|------|
| API 模块 | 14 |
| 页面视图 (views) | 13 |
| Store | 2 |
| 布局组件 | 1 |
| Three 特效/场景 | 4 个特效 + 1 个场景生成器 |
| 着色器目录 | 2（lightRadar、lightWall） |

---

**最后更新**：按当前仓库实际文件整理，与 README 中“项目结构”以本文件为准；若增删文件请同步更新本文档与 README。
