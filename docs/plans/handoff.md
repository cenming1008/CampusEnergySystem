# Handoff

## 探索 -> 前端
### 任务
- 已完成：优先做“产品外壳迁移”，未大改业务逻辑
- 已完成：前端主入口已从煤矿叙事切到园区 EMS 叙事

### 已知信息
- 可直接复用页面：
  - `DeviceManager.vue`
  - `DeviceMonitor.vue`
  - `LocationManager.vue`
  - `DeviceGroups.vue`
  - `AlarmCenter.vue`
  - `EnergyManagement.vue`
  - `Maintenance.vue`
  - `Inspection.vue`
  - `Report.vue`
  - `SystemSettings.vue`
  - `UserManagement.vue`
  - `AuditCenter.vue`
- 优先迁移区域：
  - `Layout.vue`
  - `router/index.ts`
  - `Dashboard.vue`
  - `Login.vue`
  - `CampusScene.vue`
- `CampusScene.vue` 和 `three/mine/` 的组合更像历史煤矿数字孪生底座之上的兼容改造，不适合继续用煤矿命名作为园区 EMS 主导航入口
- 本轮已完成的前端改动：
  - 菜单与路由标题已切换为园区 EMS 主线
  - 首页已改成“园区能源驾驶舱”表达
  - 登录页品牌已改成园区 EMS
  - `CampusScene.vue` 已改成“园区总览与实时态势”表达
  - 系统设置页“关于系统”已同步调整产品描述
  - 园区总览入口 URL 已从 `/mine-scene` 切到 `/campus-overview`
  - 浏览器标题与默认应用示例名已统一为“园区综合能源管理系统 / Campus EMS”

### 建议处理方式
- 前端第一批迁移已完成，后续可继续补：
  - 更精确的园区 / 区域 / 楼栋首页聚合数据
  - `CampusScene` 的真实园区空间建模
  - 文档层的产品表述统一

---

## 探索 -> 后端
### 任务
- 保留模型底座，优先补园区 EMS 主线聚合能力
- 不急于全量重命名旧接口路径

### 已知信息
- 可直接复用的主干对象：
  - `Location`
  - `Device`
  - `EnergyData`
  - `Alarm`
  - `CarbonEmission`
  - `EnergyStatistics`
  - `Prediction`
  - `DeviceMaintenance`
  - `Inspection*`
  - `DeviceGroup*`
  - `User`
  - `AuditEvent`
  - `DeviceControlLog`
  - `MqttIngestionRecord`
  - `DeviceIngestionHealth`
- 煤矿专属性主要在：
  - `app_name` 默认值
  - 默认 MQTT topic
  - README / 文档 / 样例文案
  - 历史项目命名

### 建议处理方式
- 第一批优先补：
  - 园区总览聚合
  - 区域排行
  - 楼栋排行
  - 分能源类型汇总
  - 分项负荷 / 分项能耗
  - 驾驶舱告警概览
- 暂时不要：
  - 推翻现有模型
  - 全量重命名旧 URL
  - 为了换定位去动权限、审计、监控、部署底座

---

## 前端 -> 后端
### 当前建议
- 首页驾驶舱下一阶段需要后端补齐真正的园区 EMS 聚合能力，优先建议：
  - 园区首页总览汇总接口
  - 区域排行 / 楼栋排行接口
  - 本月能耗与分能源介质汇总接口
  - 告警总数与按区域分布接口
- 当前前端已先用现有设备与能耗接口做最小迁移，但这些数据仍偏“前端拼装”，不适合作为长期正式驾驶舱口径

---

## 后端 -> 前端
### 当前建议
- 本轮后端已新增园区聚合接口，可优先联调：
  - `GET /campus/overview`
  - `GET /campus/energy-statistics?dimension=area|building`
  - `GET /campus/energy-categories`
  - `GET /campus/subitems`
  - `GET /campus/realtime-load-trend`
  - `GET /campus/alarms/summary`
- 旧接口继续保留兼容：
  - `GET /locations/*`
  - `GET /energy/overview`
  - `GET /energy/statistics`
  - `GET /analysis/{device_id}`
  - `GET /alarms`
- 本轮影响的后端主线对象与表达：
  - `LocationType` 新增 `park/campus/site`
  - 园区主线对象统一为 `campus_entities`、`hierarchy_summary`、`analysis_summary`
  - 分项统计当前以 `Device.device_category` 作为兼容型 `sub_item` 口径
- 前端联调建议：
  - 驾驶舱首页优先切到 `/campus/overview`
  - 区域/楼栋排行页可切到 `/campus/energy-statistics`
  - 能源占比、分项能耗、实时负荷趋势、告警汇总可分别切到新的 `/campus/*` 端点
  - 如果前端短期仍复用旧接口，不要继续扩散煤矿命名到新页面

---

## 后续维护建议

- 当前迁移策略应坚持“保留底座、迁移叙事”
- 优先级顺序：
  - 产品名称与主文案
  - 首页与导航
  - 园区 / 区域 / 楼栋聚合
  - 文档与样例
  - 历史命名清理
- 煤矿专属模块短期不必激进删除，但应退出主线入口
