# PLAN-20260413-设备台账与首页SCADA导航联动收敛专题

> 状态：已重开，第一轮范围已锁定（分类契约收敛），待后端 + 前端角色执行 | 负责人：规则角色 / 后端角色 / 前端角色 | 更新时间：2026-04-13

## 1. 背景

当前设备台账页与首页 SCADA 导航都使用 `/devices/` 主数据，但前端消费口径不一致：

- 设备台账页使用动态 `getDeviceTypes()`。
- 首页 SCADA 类型展示仍依赖本地标签映射。
- SCADA 分组有前端本地组装逻辑，未与台账侧统一。
- 首页设备列表主要在挂载时加载一次，新建设备后的同会话联动缺少稳定机制。

同时，后端创建设备时会按设备类型自动补齐 `device_category` 与 `energy_type`，说明主数据契约已经具备统一来源条件。

当前新增问题表明“分类契约未收敛”仍存在：`reactive_power_compensator` 与 `svg` 在后端注册类别为 `load`，导致 SCADA 分组仍落在“用电设备”。

本专题第一轮仍不新增后端接口，但需要先收敛后端主数据分类契约，再由前端按新契约消费，不再用前端特判补洞。

## 2. 目标

- 统一设备台账与首页 SCADA 的主数据消费口径。
- 统一 SCADA 分组规则与类型标签展示规则。
- 给出“新增设备后首页可见”的最低保证规则。
- 第一轮不新增后端接口。

## 3. 第一轮最小可控范围（重开）

允许范围（后端 + 前端串行）：

- [DeviceManager.vue](/Users/todo/CampusEnergySystem/frontend/src/views/DeviceManager.vue)
- [Dashboard.vue](/Users/todo/CampusEnergySystem/frontend/src/views/Dashboard.vue)
- [ScadaBoard.vue](/Users/todo/CampusEnergySystem/frontend/src/features/dashboard/components/ScadaBoard.vue)
- [useDashboardDeviceSelection.ts](/Users/todo/CampusEnergySystem/frontend/src/features/dashboard/composables/useDashboardDeviceSelection.ts)
- [device.ts](/Users/todo/CampusEnergySystem/frontend/src/api/device.ts)
- [deviceTypeLabels.ts](/Users/todo/CampusEnergySystem/frontend/src/shared/deviceTypeLabels.ts)
- [device_registry.py](/Users/todo/CampusEnergySystem/app/core/device_registry.py)
- [device_payloads.py](/Users/todo/CampusEnergySystem/app/domain/device_payloads.py)
- [device_service.py](/Users/todo/CampusEnergySystem/app/services/device_service.py)
- [devices/management.py](/Users/todo/CampusEnergySystem/app/api/endpoints/devices/management.py)
- 主区文档：
  - [current-status.md](/Users/todo/CampusEnergySystem/docs/plans/current-status.md)
  - [handoff.md](/Users/todo/CampusEnergySystem/docs/plans/handoff.md)

第一轮默认需要先后端、再前端联动完成契约收敛。

## 4. 主数据单一来源口径

设备主数据契约单一来源：

- `/devices/` 为设备台账与首页 SCADA 的唯一数据来源。
- `/devices/types` 为设备类型、类别、能源介质、标签和单位的唯一权威配置来源。

前端不再本地硬编码主分类逻辑，除非作为兜底显示。

新增分类契约收敛口径：

- `reactive_power_compensator` 应从 `load` 独立出来，作为电能质量 / 无功补偿类设备类别。
- `svg` 应归入同一补偿类别（而不是继续落在 `load`）。

## 5. SCADA 分组规则

建议统一为：

1. 优先按 `device_category` 分组（由后端创建设备时补齐）。
2. 若缺失 `device_category`，按 `energy_type` 分组。
3. 若两者都缺失，落回 `device_type` 兜底分组。

分组 label 统一走 `deviceTypeLabels` 的动态配置映射，避免硬编码。

## 6. 设备类型展示口径

统一口径：

- 设备类型展示优先使用 `/devices/types` 返回的 `name_zh`。
- `deviceTypeLabels.ts` 仅作为兜底映射，不作为主来源。
- 首页与台账页必须使用同一套 label 生成逻辑。

## 7. 新增设备后首页可见的最低保证

最低保证规则：

- 设备创建成功后，必须触发一次设备列表刷新。
- 若首页处于同会话打开态，需提供显式刷新动作或事件触发 `loadDeviceList()`。
- 若首页未打开，至少保证下次进入首页时会重新拉取 `/devices/` 并可见新设备。

## 8. 第一轮明确不应纳入的内容

- 不新增后端接口
- 不改设备模型或主数据语义
- 不扩到 3D 场景、监控协议或拓扑重构
- 不扩到跨页面导航重构
- 不引入全局状态管理大改

## 9. 冻结边界

- 第一轮只做设备分类契约收敛与前端消费对齐。
- 不引入新的后端聚合接口。
- 不修改 `/devices/` 与 `/devices/types` 的返回结构。
- 不扩到设备主数据的其他字段语义重构。

## 10. 回滚边界

- 若分类契约调整导致设备分组与台账展示失真，整轮回退到本轮前状态。
- 若发现现有 `/devices/` 与 `/devices/types` 无法表达补偿器 / SVG 新类别，应停止本轮并回规则角色重锁边界。
- 若实现开始波及 3D 场景、监控协议或拓扑结构，应立即回退到第一轮范围。

## 11. 验收口径

第一轮验收至少应核对：

- `reactive_power_compensator` 与 `svg` 不再归入 `load`，而是归入同一补偿类设备类别。
- `/devices/` 返回的 `device_category` 已体现新类别，前端分组按新类别生效。
- 设备类型标签展示仍以 `/devices/types` 为主来源，`deviceTypeLabels` 仅兜底。
- SCADA 分组规则与台账口径一致，且有明确 fallback。
- 未越界到后端接口新增、3D 场景或拓扑重构。

## 12. 推荐路径

- `规则角色 -> 后端角色 -> 前端角色 -> 验收角色`

## 13. 进度记录

- 2026-04-13：已确认设备台账与首页 SCADA 同用 `/devices/` 但口径不一致，且新设备同会话联动缺失。
- 2026-04-13：已正式建立 `设备台账与首页 SCADA 导航联动收敛专题`，锁定第一轮为前端侧口径收敛。
- 2026-04-13：已确认 `reactive_power_compensator` 与 `svg` 仍归类为 `load`，导致 SCADA 导航分组失真，本专题重开并转为“分类契约收敛”。
