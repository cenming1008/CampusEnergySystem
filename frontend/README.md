# 园区综合能源管理系统 - 前端

基于 Vue 3 + TypeScript + Vite + Three.js 构建的园区综合能源管理系统前端应用。

## 📁 项目结构

以下为精简结构；**每个文件与目录的详细说明**见 **[FRONTEND_STRUCTURE.md](./FRONTEND_STRUCTURE.md)**（按实际文件整理，无重复）。

```
frontend/
├── public/                  # 静态资源（原样输出）
│   ├── draco/              # Draco 压缩库（glTF 解压）
│   ├── model/              # 3D 模型（.glb 等，见 model/README.md）
│   └── textures/           # HDR 等贴图
│
├── src/
│   ├── api/                # API 接口层（17 个模块）
│   │   ├── alarm.ts        # 告警
│   │   ├── analysis.ts     # 园区运营分析
│   │   ├── audit.ts        # 审计日志
│   │   ├── auth.ts         # 认证
│   │   ├── compensation.ts # 补偿类设备
│   │   ├── dataCleanup.ts  # 数据清理（系统设置页用）
│   │   ├── device.ts       # 设备
│   │   ├── deviceGroup.ts  # 设备分组
│   │   ├── deviceMonitor.ts # 设备监控
│   │   ├── energy.ts       # 能源管理
│   │   ├── fdd.ts          # 故障诊断
│   │   ├── inspection.ts   # 巡检运维
│   │   ├── location.ts     # 位置管理
│   │   ├── maintenance.ts  # 维护管理
│   │   ├── report.ts       # 报表
│   │   ├── telemetry.ts    # 遥测
│   │   └── users.ts        # 用户管理
│   │
│   ├── assets/main.css     # 全局样式
│   ├── layout/Layout.vue   # 主布局（侧栏、顶栏、告警、用户）
│   ├── router/index.ts    # 路由与登录守卫
│   ├── shaders/            # 光雷达、光墙着色器（GLSL）
│   ├── stores/             # Pinia（仅 2 个）
│   │   ├── useAuthStore.ts   # 认证状态
│   │   └── useSocketStore.ts # WebSocket 状态
│   │
│   ├── three/              # Three.js
│   │   ├── effects/        # 光墙、光雷达、飞线、告警精灵
│   │   └── mine/           # 历史 3D 场景生成器（兼容目录）
│   │
│   ├── utils/request.ts    # Axios 封装与 Token 注入
│   ├── views/              # 页面（20 个，含异常页与管理页）
│   │   ├── Login.vue, Dashboard.vue, AlarmCenter.vue
│   │   ├── DeviceManager.vue, DeviceMonitor.vue, DeviceControlConsole.vue
│   │   ├── LocationManager.vue, DeviceGroups.vue, EnergyManagement.vue
│   │   ├── EnergyAnalysis.vue, FDD.vue, Maintenance.vue
│   │   ├── Inspection.vue, Report.vue, SystemSettings.vue
│   │   └── AuditCenter.vue, UserManagement.vue, AccountSecurity.vue, Forbidden.vue, NotFound.vue
│   │
│   ├── App.vue
│   └── main.ts
│
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── README.md
├── FRONTEND_STRUCTURE.md   # 前端文件与作用详细说明
├── DEVELOPMENT.md
└── CHANGELOG.md
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
- 园区 3D 场景展示
- 设备位置可视化
- 告警状态可视化
- 光效特效（光墙、光雷达、飞线等）

### 4. 能耗分析
- 园区运营分析总览
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

### 7. 巡检运维
- 巡检任务管理
- 巡检记录与结果
- 巡检统计（对应页面：巡检运维；API：inspection.ts）

### 8. 报表分析
- 能源消耗报表
- 设备运行报表
- 自定义报表导出

### 9. 数据清理
- 历史数据清理
- 清理策略配置
- 清理记录查询

## 🎨 3D 场景说明

项目使用 Three.js 实现园区总览 3D 可视化：

- **当前场景**：由 `src/three/mine/MineSceneGenerator.ts` 用几何体程序化生成园区总览场景，**未使用外部 .glb 模型**；`public/model/` 下暂无模型文件。
- **模型加载**：支持 glTF/GLB，使用 Draco 压缩；若放入 `public/model/` 模型，需在场景中增加加载逻辑。
- **环境光照**：HDR 环境贴图（优先 2k.hdr，回退 023.hdr）；地面贴图缺失时使用纯色。
- **特效**：光墙、光雷达、飞线、告警精灵。

📌 **想补充更真实的园区 3D 模型？** 见 [园区总览 3D 资源说明（历史资源文档）](../docs/02-功能使用/矿区总览3D资源说明.md)：模型获取渠道、格式要求、接入方式。

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
