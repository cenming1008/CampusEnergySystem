# PLAN-20260413-设备监控页实时数据语义收敛专题

> 状态：第一轮已验收通过，主题进入阶段收口判断（暂不迁 archive） | 负责人：规则角色 / 后端角色 / 前端角色 / 验收角色 | 更新时间：2026-04-13

## 1. 背景

设备监控页目前大多数设备仍使用同一套通用监控模板，仅 SVG 设备有专属视图。补偿器设备（`reactive_power_compensator`）在接入链路和数据库中已经存在实时数据字段能力，但监控页没有形成专属语义展示，导致实时监控语义失真。

本专题目标是让设备监控页按设备类型收敛实时语义，第一轮仅聚焦补偿器，先补齐后端聚合语义，再由前端专属视图消费。

## 2. 目标

- 建立补偿器设备的第一类专属监控语义视图。
- 让设备监控页不再对所有设备使用同一套通用展示。
- 第一轮不新增后端接口，不扩展到其他设备类型。

## 3. 第一轮最小可控范围

允许范围（后端 + 前端串行）：

- /Users/todo/CampusEnergySystem/app/services/device_monitor_service.py
- /Users/todo/CampusEnergySystem/app/api/endpoints/devices/monitoring.py
- /Users/todo/CampusEnergySystem/frontend/src/api/deviceMonitor.ts
- /Users/todo/CampusEnergySystem/frontend/src/views/DeviceMonitor.vue
- 主区文档：
  - /Users/todo/CampusEnergySystem/docs/plans/current-status.md
  - /Users/todo/CampusEnergySystem/docs/plans/handoff.md

第一轮仅覆盖 `reactive_power_compensator`。

## 4. 实时语义口径（补偿器）

补偿器实时监控的最小语义集（只使用实时数据，不引入人工维护字段）：

- 有功功率 / 负荷（`flow_rate` 或等价字段）
- 无功功率（`reactive_power`）
- 功率因数（`power_factor`）
- 电压（`voltage`）
- 电流（`current`）
- 时间戳（`timestamp`）

如现有数据中存在温度或其他辅助字段，可作为次级信息展示，但不作为第一轮硬依赖。

## 5. 第一轮明确不应纳入的内容

- 不扩到 SVG 设备的专属监控改造
- 不扩到其他设备类型
- 不新增后端接口
- 不调整 MQTT 接入协议或字段标准化规则
- 不做监控页整体重构或跨页联动改造
- 不引入运维档案、资产信息等人工维护字段

## 6. 冻结边界

- 仅收敛补偿器实时语义展示，不改其他设备类型。
- 不改变既有接口路径与返回结构。
- 不改监控数据落库与接入链路。

## 7. 回滚边界

- 若补偿器专属视图导致监控页核心指标缺失或误导，整轮回退至通用模板。
- 若实现开始影响 SVG 或其他设备类型，应立即回退至第一轮范围。
- 若需要新增接口或改变返回结构，需回规则角色重锁边界。

## 8. 验收口径

第一轮验收至少核对：

- `reactive_power_compensator` 不再使用通用模板，而是专属监控视图。
- 后端监控聚合能稳定提供补偿器实时字段（含 `reactive_power`、`power_factor`、`voltage`、`current`、`flow_rate`）。
- 前端只消费实时数据，不混入人工维护字段。
- 未越界到 SVG 或其他设备类型。
- 未新增接口、未改变返回结构。

## 9. 推荐路径

- `规则角色 -> 后端角色 -> 前端角色 -> 验收角色`

## 10. 进度记录

- 2026-04-13：已建立 `设备监控页实时数据语义收敛专题`，第一轮锁定为补偿器实时语义收敛。
- 2026-04-13：第一轮已验收通过，未锁定第二轮最小范围，进入阶段收口判断。
