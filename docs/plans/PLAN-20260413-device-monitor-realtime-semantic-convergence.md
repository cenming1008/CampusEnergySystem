# PLAN-20260413-设备监控页实时数据语义收敛专题

> 状态：补偿类设备监控语义与补偿扩展接口收敛已完成，进入规则/验收收口判断 | 负责人：规则角色 / 后端角色 / 前端角色 / 验收角色 | 更新时间：2026-04-14

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

## 10. 第二轮：补偿器专属详情页 UI 优化

### 目标

- 基于现有 EMS 深色工业风页面，为 `reactive_power_compensator` 建立专属详情页布局。
- 核心突出：
  - 当前无功功率
  - 功率因数
  - 补偿级数/补偿效果
  - 运行模式与告警状态
- 允许在真实接口未完全接入时使用演示占位，但必须与真实字段边界分明。

### 第二轮允许范围

- /Users/todo/CampusEnergySystem/frontend/src/views/DeviceMonitor.vue
- /Users/todo/CampusEnergySystem/frontend/src/api/deviceMonitor.ts
- /Users/todo/CampusEnergySystem/frontend/src/features/device-monitor/components/compensation/*
- /Users/todo/CampusEnergySystem/docs/plans/current-status.md
- /Users/todo/CampusEnergySystem/docs/plans/handoff.md

### 第二轮明确不应纳入

- 不扩到 SVG 或其他设备类型
- 不新增后端接口
- 不改 MQTT 协议
- 不做监控页整体重构
- 不引入资产/运维档案类人工维护字段作为主监控数据

### 第二轮验收口径

- 一眼能看出当前无功功率与功率因数
- 页面明显体现补偿器专属语义，而不是通用设备页换文案
- 当前投切级数或补偿组投入情况可感知
- 趋势区默认围绕补偿效果展开
- 右侧栏具备运行事件、运行状态、设备档案的运维价值
- 保持现有深色工业监控风格与桌面大屏可读性

### 第二轮验收结论

- 补偿器专属详情页 UI 优化已通过验收。
- 主视图已能一眼看出无功功率与功率因数，趋势围绕补偿效果，右侧栏具备运维价值。
- 演示占位已明确标注，未伪造真实数据。
- 未越界到 SVG、其他设备类型、新接口或监控页整体重构。
- 进入阶段收口判断，不默认继续后续轮次。

## 11. 进度记录

- 2026-04-13：已建立 `设备监控页实时数据语义收敛专题`，第一轮锁定为补偿器实时语义收敛。
- 2026-04-13：第一轮已验收通过，未锁定第二轮最小范围，进入阶段收口判断。
- 2026-04-13：主题重开，新增“补偿器专属详情页 UI 优化”轮次。
- 2026-04-13：补偿器专属详情页 UI 优化已完成并通过验收，进入阶段收口判断。
- 2026-04-14：已完成 `reactive_power_compensator -> svg` 代码口径统一，旧顶层 `/svg`、`/capacitor-bank` endpoint 与前端兼容 API 文件已删除，补偿类接口正式收敛为 `/devices/{id}/compensation/svg/*` 与 `/devices/{id}/compensation/capacitor-bank/*`，主题进入规则/验收收口判断。

## 12. 补偿类接口冻结口径

- 本专题后续默认只承认以下两组补偿类正式接口：
  - `/devices/{id}/compensation/svg/*`
  - `/devices/{id}/compensation/capacitor-bank/*`
- 该口径的含义是：
  - 补偿类扩展必须继续挂在设备主线 `/devices/{id}/compensation/*` 下
  - `svg` 与 `capacitor-bank` 作为补偿类子型分流，不再恢复旧顶层 `/svg`、`/capacitor-bank`
  - 不再新增与上述路径同义的并列入口，避免前后端、测试、联调脚本出现多套主口径
- 若未来确需新增新的补偿类子型，应沿用同一层级继续扩展，例如 `/devices/{id}/compensation/<subtype>/*`，而不是重新开一套顶层业务族路径。
- 若未来确需做 breaking change，必须先回规则角色重锁边界，再更新正式 PLAN、`current-status.md` 与 `handoff.md`，不得只在实现层偷偷漂移。

## 13. 正式完善门槛

当前 `MVP+` 阶段完成不等于“正式完善”。补偿器专题要进入“正式完善 / 可正式收口”至少还需同时满足：

- 真实设备/真实网关联调完成，并确认正式回执 topic、payload、命令关联键与当前 `command_id` 口径是否一致。
- 监控页关键指标已收敛为真实采集或真实参数回读，不再把“控制模式 / 补偿容量利用率 / 柜内温度健康度”等核心信息主要建立在估算或演示占位上。
- 控制状态语义在真实设备侧验证通过，`accepted / running / success / failed / timeout / rejected` 的边界已稳定，不再只是模拟器约定。
- 至少完成一轮真实设备侧受控参数写入与远程控制验证，并确认日志、回执、超时和失败路径都能落到最终可追踪状态。
- 高风险动作边界已明确：
  - 要么明确继续关闭并写入正式限制
  - 要么完成真实联调验证后正式开放
- 当前主区、正式 PLAN 与 Daily 快照已同步收口，不再存在“实现已完成但规则/验收结论仍悬空”的状态。
