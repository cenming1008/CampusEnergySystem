# 矿区能源管理系统 - 前端

基于 Vue 3 + TypeScript + Vite + Three.js 构建的矿区能源管理系统前端应用。

## 📁 项目结构

```
frontend/
├── public/                  # 静态资源
│   ├── draco/              # Draco 3D 压缩库（用于 glTF 模型压缩）
│   ├── model/              # 3D 模型文件
│   │   ├── mine_env.glb   # 矿区环境模型
│   │   ├── Fighter*.glb   # 设备模型
│   │   ├── floor*.glb     # 地面模型
│   │   └── wall.glb       # 墙体模型
│   └── textures/           # HDR 环境贴图
│
├── src/
│   ├── api/                # API 接口层
│   │   ├── alarm.ts       # 告警接口
│   │   ├── auth.ts        # 认证接口
│   │   ├── dataCleanup.ts # 数据清理接口
│   │   ├── device.ts      # 设备接口
│   │   ├── deviceGroup.ts # 设备分组接口
│   │   ├── energy.ts      # 能源管理接口
│   │   ├── fdd.ts         # 故障诊断接口
│   │   ├── forecast.ts    # 预测接口
│   │   ├── location.ts    # 位置管理接口
│   │   ├── maintenance.ts # 维护管理接口
│   │   ├── report.ts      # 报表接口
│   │   └── telemetry.ts   # 遥测数据接口
│   │
│   ├── assets/             # 样式资源
│   │   └── main.css       # 全局样式
│   │
│   ├── layout/             # 布局组件
│   │   └── Layout.vue     # 主布局
│   │
│   ├── router/             # 路由配置
│   │   └── index.ts       # 路由定义
│   │
│   ├── shaders/            # WebGL 着色器
│   │   ├── lightRadar/    # 光雷达特效着色器
│   │   └── lightWall/     # 光墙特效着色器
│   │
│   ├── stores/             # Pinia 状态管理
│   │   ├── useAuthStore.ts   # 认证状态
│   │   ├── useDeviceStore.ts # 设备状态
│   │   └── useSocketStore.ts # WebSocket 状态
│   │
│   ├── three/              # Three.js 相关
│   │   ├── effects/       # 3D 特效
│   │   │   ├── AlarmSprite.ts  # 告警精灵
│   │   │   ├── FlyLine.ts      # 飞线特效
│   │   │   ├── LightRadar.ts   # 光雷达
│   │   │   └── LightWall.ts    # 光墙
│   │   └── mine/          # 矿区场景
│   │       └── MineSceneGenerator.ts # 场景生成器
│   │
│   ├── utils/              # 工具函数
│   │   └── request.ts     # HTTP 请求封装
│   │
│   ├── views/              # 页面组件
│   │   ├── Dashboard.vue        # 仪表盘
│   │   ├── DeviceGroups.vue     # 设备分组管理
│   │   ├── DeviceManager.vue    # 设备管理
│   │   ├── EnergyManagement.vue # 能源管理
│   │   ├── FDD.vue              # 故障检测诊断
│   │   ├── Forecast.vue         # 能源预测
│   │   ├── LocationManager.vue  # 位置管理
│   │   ├── Login.vue            # 登录页
│   │   ├── Maintenance.vue      # 维护管理
│   │   ├── MineScene.vue        # 3D 矿区场景
│   │   ├── Report.vue           # 报表分析
│   │   └── SystemSettings.vue   # 系统设置
│   │
│   ├── App.vue             # 根组件
│   └── main.ts             # 应用入口
│
├── index.html              # HTML 入口
├── package.json            # 项目依赖
├── tsconfig.json           # TypeScript 配置
├── vite.config.ts          # Vite 配置
└── README.md               # 项目说明（本文件）
```

## 🚀 快速开始

### 环境要求

- Node.js >= 16
- npm >= 8 或 pnpm

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 生产构建

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

### 预览生产构建

```bash
npm run preview
```

## 🔧 技术栈

- **框架**: Vue 3 (Composition API)
- **语言**: TypeScript
- **构建工具**: Vite
- **状态管理**: Pinia
- **路由**: Vue Router
- **3D 渲染**: Three.js
- **HTTP 客户端**: Axios
- **实时通信**: WebSocket

## 📦 主要功能模块

### 1. 设备管理
- 设备列表与详情查看
- 设备分组管理
- 设备实时状态监控
- 设备控制操作

### 2. 能源管理
- 多能源类型监控（电力、水、气等）
- 能源消耗统计
- 能源效率分析

### 3. 3D 可视化
- 矿区 3D 场景展示
- 设备位置可视化
- 告警状态可视化
- 光效特效（光墙、光雷达、飞线等）

### 4. 预测分析
- 能源消耗预测（LSTM）
- 趋势分析图表
- 历史数据对比

### 5. 故障诊断
- 实时故障检测
- 故障记录查看
- 故障统计分析

### 6. 维护管理
- 维护任务管理
- 维护记录查询
- 维护计划安排

### 7. 报表分析
- 能源消耗报表
- 设备运行报表
- 自定义报表导出

### 8. 数据清理
- 历史数据清理
- 清理策略配置
- 清理记录查询

## 🎨 3D 场景说明

项目使用 Three.js 实现了丰富的 3D 可视化效果：

- **模型加载**: 支持 glTF/GLB 格式，使用 Draco 压缩优化加载速度
- **环境光照**: HDR 环境贴图实现真实光照效果
- **特效系统**: 
  - 光墙特效（区域边界显示）
  - 光雷达特效（扫描效果）
  - 飞线特效（数据流动画）
  - 告警精灵（设备状态提示）

## 🔌 API 接口

所有 API 接口都封装在 `src/api/` 目录下，使用统一的请求拦截器处理：

- 自动添加认证 Token
- 统一错误处理
- 请求/响应拦截
- WebSocket 自动重连

## 📝 开发规范

### 代码风格

- 使用 TypeScript 严格模式
- 组件使用 Composition API
- 遵循 Vue 3 最佳实践

### 组件命名

- 页面组件：PascalCase (如 `DeviceManager.vue`)
- 通用组件：PascalCase (如 `DataTable.vue`)
- 布局组件：Layout 前缀 (如 `Layout.vue`)

### API 接口

- 接口文件按模块划分
- 使用 TypeScript 类型定义
- 统一使用 async/await

## 🐛 常见问题

### WebSocket 连接失败

检查后端服务是否启动，以及 `vite.config.ts` 中的代理配置是否正确。

### 3D 模型加载缓慢

- 确保使用了 Draco 压缩
- 检查网络连接
- 考虑使用模型懒加载

### 开发环境热更新不生效

- 清除 `node_modules/.vite` 缓存
- 重启开发服务器

## 📄 许可证

本项目采用 MIT 许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系方式

如有问题，请联系项目维护者。
