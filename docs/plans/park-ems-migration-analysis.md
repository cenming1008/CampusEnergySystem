# Park EMS Migration Analysis

## 一、总体判断

当前项目迁移到园区 EMS 的可行性高。

从现有代码看，这个项目的真正底座并不是“煤矿生产流程系统”，而是一个已经具备通用 EMS 主干能力的综合能源管理平台。它的核心能力集中在：
- 多能源接入
- 设备与表计管理
- 位置层级管理
- 实时监控
- 告警
- 能耗统计与碳排放
- 维护与巡检
- 报表
- 权限、审计、监控与部署

这些能力天然适合迁移到园区综合能源管理系统、工厂园区、校园、医院园区、商业综合体等场景。

整体迁移成本偏中低，更准确地说属于“保留底座、迁移叙事”的类型，而不是推倒重写。真正带有煤矿专属表达的部分，主要集中在：
- 前端菜单、首页、登录页、3D 总览页
- 项目名称、默认应用名和部分默认输出文案
- README 与部分功能 / 部署文档
- 历史项目命名，例如 `mine/telemetry`、`mine_energy`

因此当前最优策略不是全面改造底层，而是先把产品主线、入口叙事、聚合对象和页面表达迁到园区 EMS。

## 二、可直接复用部分

### 前端

以下页面可以直接复用为园区 EMS 页面底座：
- [DeviceManager.vue](/Users/todo/MineEnergySystem/frontend/src/views/DeviceManager.vue)
- [DeviceMonitor.vue](/Users/todo/MineEnergySystem/frontend/src/views/DeviceMonitor.vue)
- [LocationManager.vue](/Users/todo/MineEnergySystem/frontend/src/views/LocationManager.vue)
- [DeviceGroups.vue](/Users/todo/MineEnergySystem/frontend/src/views/DeviceGroups.vue)
- [AlarmCenter.vue](/Users/todo/MineEnergySystem/frontend/src/views/AlarmCenter.vue)
- [EnergyManagement.vue](/Users/todo/MineEnergySystem/frontend/src/views/EnergyManagement.vue)
- [Maintenance.vue](/Users/todo/MineEnergySystem/frontend/src/views/Maintenance.vue)
- [Inspection.vue](/Users/todo/MineEnergySystem/frontend/src/views/Inspection.vue)
- [Report.vue](/Users/todo/MineEnergySystem/frontend/src/views/Report.vue)
- [SystemSettings.vue](/Users/todo/MineEnergySystem/frontend/src/views/SystemSettings.vue)
- [UserManagement.vue](/Users/todo/MineEnergySystem/frontend/src/views/UserManagement.vue)
- [AuditCenter.vue](/Users/todo/MineEnergySystem/frontend/src/views/AuditCenter.vue)

可直接复用的前端底座：
- `frontend/src/api/*`
- `frontend/src/shared/ui/*`
- `frontend/src/shared/composables/*`
- `stores/useAuthStore.ts`
- `stores/useSocketStore.ts`
- 权限与位置范围控制逻辑

### 后端

以下对象基本都可以直接作为园区 EMS 主干模型继续保留：
- `Location`
- `Device`
- `EnergyData`
- `Alarm`
- `CarbonEmission`
- `EnergyStatistics`
- `Prediction`
- `DeviceMaintenance`
- `InspectionRoute / Point / Plan / Task / Record`
- `DeviceGroup / DeviceGroupMembership`
- `User`
- `AuditEvent`
- `DeviceControlLog`
- `MqttIngestionRecord`
- `DeviceIngestionHealth`

以下接口主线可直接复用：
- 认证与用户
- 设备管理
- 设备监控
- 位置管理
- 能源统计
- 告警中心
- 报表导出
- 巡检与维护
- 审计日志
- 健康检查
- MQTT 接入健康与重放

### 脚本

绝大多数脚本不需要因为“从煤矿迁移到园区”而立刻改动逻辑，尤其是：
- 启动、停止、状态检查
- 健康检查
- 备份恢复
- 发布与 readiness
- 监控与告警测试
- 权限、账号、配置检查类脚本

### 部署

部署底座可直接复用：
- Docker Compose
- Nginx
- Prometheus / Grafana / Alertmanager / Loki / Promtail
- GitHub Actions 基线
- 备份恢复和发布前检查链路

### 监控

监控、日志、告警、接入健康、指标导出链路都属于通用 EMS 基础能力，可继续保留。

### 权限

当前 RBAC、位置范围过滤、审计日志、密码与登录安全策略都可直接复用到园区 EMS。

### 告警

告警体系可以直接保留。阈值告警、未处理告警列表、确认处理、通知发送都不依赖煤矿专属对象。

### 历史分析

历史能耗、碳排放、趋势分析、预测、报表导出都可以继续作为园区 EMS 通用能力。

## 三、需要改名或重构的部分

### 明显煤矿专属命名

- [README.md](/Users/todo/MineEnergySystem/README.md)
  - 标题仍是“煤矿综合能源管理系统”
- [app/core/settings.py](/Users/todo/MineEnergySystem/app/core/settings.py)
  - `app_name` 默认值仍是“煤矿综合能源管理系统”
- [frontend/src/layout/Layout.vue](/Users/todo/MineEnergySystem/frontend/src/layout/Layout.vue)
  - Logo 文案仍是 `MINE EMS`
  - 菜单项仍有“矿区总览”
- [frontend/src/router/index.ts](/Users/todo/MineEnergySystem/frontend/src/router/index.ts)
  - 路由路径仍是 `mine-scene`
  - 路由标题仍是“矿区总览”
- [frontend/src/views/Dashboard.vue](/Users/todo/MineEnergySystem/frontend/src/views/Dashboard.vue)
  - 页面标题“煤矿综合能源管理系统”
  - 文案“接入矿区能源网络”
  - 提示“全矿全量数据”
- [frontend/src/views/Login.vue](/Users/todo/MineEnergySystem/frontend/src/views/Login.vue)
  - “矿山运营 卓越中心”
  - 挖掘机、传送带、车队负载等矿山场景表达
- [frontend/src/views/SystemSettings.vue](/Users/todo/MineEnergySystem/frontend/src/views/SystemSettings.vue)
  - “关于 MINE EMS”

### 不适合园区 EMS 主线的页面或模块

- [frontend/src/views/MineScene.vue](/Users/todo/MineEnergySystem/frontend/src/views/MineScene.vue)
- [frontend/src/three/mine/MineSceneGenerator.ts](/Users/todo/MineEnergySystem/frontend/src/three/mine/MineSceneGenerator.ts)
- [docs/02-功能使用/矿区总览3D资源说明.md](/Users/todo/MineEnergySystem/docs/02-功能使用/矿区总览3D资源说明.md)

这整块不是不能复用，但不适合作为园区 EMS 主线入口。它更像历史煤矿数字孪生展示底座，短期应弱化、降级或替换为“园区总览 / 园区驾驶舱”。

### 需要弱化但不必立刻删除的内容

- MQTT 默认 topic 仍是 `mine/telemetry`
- 数据库名、容器名仍沿用 `mine_energy`
- 文档中仍大量出现“煤矿”“矿区”“矿山”
- 若干接入文档和防火墙文档仍写“矿区网关”

这些内容短期不需要为了迁移而立刻全部改动，因为它们更多是历史项目命名，不影响底层逻辑复用。但它们不应继续作为新定位的主线表达。

## 四、建议归档或降级的部分

短期与园区主线无关、应降级处理的内容：
- `MineScene` 作为“矿区总览”主导航入口
- `frontend/src/three/mine/` 这一套矿区 3D 场景生成器
- `docs/02-功能使用/矿区总览3D资源说明.md`
- 文档中围绕矿区数字孪生、矿坑、矿卡、选矿车间的叙事
- 若后续发现与瓦斯、通风、排水、矿井流程深绑定的扩展内容，也应统一降级为历史背景能力

可保留但不再作为主线入口的模块：
- 3D 总览能力本身
- 工业接入与协议调试文档
- 预测和模拟能力

处理原则：
- 不急于删除
- 先从主导航、主文档、主首页中移开
- 作为历史兼容或可选展示能力保留

## 五、交给前端线程的任务

### 页面

- 将 `MineScene` 从“矿区总览”重定义为：
  - 园区总览占位页
  - 或历史 3D 展示页
  - 或暂时从主导航降级
- 评估 [Dashboard.vue](/Users/todo/MineEnergySystem/frontend/src/views/Dashboard.vue) 直接演进为“园区能源驾驶舱”

### 菜单

- 调整 [Layout.vue](/Users/todo/MineEnergySystem/frontend/src/layout/Layout.vue)：
  - `MINE EMS` 改为园区 EMS 品牌
  - “矿区总览”改为“园区总览”或降级
- 按产品定位收敛主导航：
  - 驾驶舱首页
  - 园区总览
  - 区域 / 楼栋能耗
  - 设备与表计
  - 实时监控
  - 告警中心
  - 能耗分析
  - 系统设置

### 首页

- 将 [Dashboard.vue](/Users/todo/MineEnergySystem/frontend/src/views/Dashboard.vue) 改造成园区驾驶舱：
  - 园区总能耗
  - 区域 / 楼栋排行
  - 实时负荷
  - 告警概览
  - 多能源占比
  - 位置范围提示改成“园区 / 区域 / 楼栋可见范围”

### 文案

- 重写 [Login.vue](/Users/todo/MineEnergySystem/frontend/src/views/Login.vue) 的品牌文案
- 去掉挖掘机、矿坑、传送带、车队负载等矿山专属展示词
- 将“全矿”“矿区”“矿山运营”统一替换为：
  - 园区
  - 区域
  - 楼栋
  - 设备 / 表计
  - 综合能源

### 图表表达

- 首页与总览页图表统一改成：
  - 园区 / 区域 / 楼栋
  - 电 / 水 / 气 / 冷 / 热
  - 分项负荷
  - 告警分布
- 不要继续用矿区网络、矿坑视角等表达作为核心视图

## 六、交给后端线程的任务

### 数据模型

- 保留现有主干模型，不做推倒重建
- 复核并逐步弱化历史命名：
  - `Device.location` 的字符串兼容字段
  - `DeviceGroup.group_type` 中的历史业务语义
  - 默认示例文案和枚举说明
- 围绕“园区 / 区域 / 楼栋 / 设备 / 表计 / 能源介质 / 分项”重写描述和示例，而不是大改表结构

### 接口命名

- 保留现有接口主干
- 新增或补充时优先围绕：
  - 园区总览
  - 区域 / 楼栋统计
  - 多能源介质
  - 分项能耗
  - 实时负荷
  - 告警概览
- 不急于全量重命名旧 URL，但新的聚合接口不要继续扩张矿区语义

### 聚合统计

- 优先补园区 EMS 主线聚合接口：
  - 园区总览汇总
  - 区域排行
  - 楼栋排行
  - 分能源类型汇总
  - 分项负荷 / 分项能耗
  - 驾驶舱告警汇总

### 主线对象结构

- 将位置层级从“兼容位置树”提升为“园区空间主线对象”
- 重点围绕：
  - 园区
  - 区域
  - 楼栋
  - 设备 / 表计
  - 能源类型
  - 告警
  - 实时与历史统计
- 暂时不要动：
  - 认证
  - 审计
  - 运维脚本
  - 接入健康
  - 备份恢复

## 七、最小迁移路径

### 先做什么

1. 先改产品外壳：
   - README 标题与项目名称
   - 前端 Logo、菜单、首页标题、登录页文案
2. 再改主导航和首页：
   - 把“矿区总览”降级或替换为“园区总览”
   - 把首页改成园区驾驶舱
3. 再补驾驶舱聚合接口：
   - 园区 / 区域 / 楼栋聚合
   - 多能源统计
   - 告警概览

### 后做什么

4. 再逐步调整文档：
   - 功能说明
   - 部署说明
   - 接入说明
   - 3D 资源说明
5. 最后再考虑是否统一替换：
   - MQTT topic 默认值
   - 数据库名
   - 容器名
   - 历史脚本输出文案

### 什么暂时不要碰

- 不要全面重命名全部接口路径
- 不要推倒重做后端模型
- 不要一次性清空所有煤矿历史文档
- 不要优先处理深层技术命名
- 不要先动部署、监控、权限、审计底座

最小迁移策略应当是：
- 先换定位
- 再换主入口
- 再补园区主线聚合
- 最后处理历史命名清理

