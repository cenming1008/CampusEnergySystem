# Handoff

## 规范 -> 后端
### 任务
- 第一批设备分类与对象分层建模优化的后端范围已实施完成
- 除非前端真实联调暴露兼容问题，本轮不要继续扩张新主题或新 schema 设计

### 已知信息
- 允许修改目录：
  - `app/models/`
  - `app/domain/`
  - `app/core/device_registry.py`
  - `app/services/device_service.py`
  - `app/services/energy_service.py`
  - `app/repositories/device_repository.py`
  - `app/repositories/energy_repository.py`
  - `app/application/device_reporting.py`
  - `app/application/energy_management.py`
  - `app/api/endpoints/devices/`
  - `app/api/endpoints/energy/`
  - `docs/plans/`
  - `docs/05-架构与设计/`
- 探索线程已确认的问题：
  - 当前系统主要停留在 `device_type + device_category + energy_type` 的薄分类层，`Device` 仍混合承载业务设备、计量设备和能源类型标签语义
  - 当前没有独立计量对象层，表计主要仍通过 `water_meter / gas_meter / heat_meter / cooling_meter / steam_meter` 这类 `device_type` 表达
  - 当前没有独立点位对象层，采集值主要通过 `EnergyData` 宽表字段和 payload 承载
  - `EnergyData` 宽表中的专属字段语义不清，空字段与“本对象无此语义字段”混淆
  - `device_registry`、payload schema、落库模型之间存在能力不一致
  - 文档与代码存在不一致：设备类型数量文档写 11 种，代码实际 10 种；`DeviceManagement.vue` 实际文件为 `DeviceManager.vue`

### 建议处理方式
- 后端第一批优先顺序：
  - 先收敛 `Device`、`device_type`、`device_category`、`energy_type` 的对象边界与派生边界
  - 再收敛 `EnergyData` 宽表中公共层 / 专属层 / 兼容层字段语义
  - 再校正 `device_registry`、请求 schema、payload 规范化、落库模型之间的一致性
  - 最后补齐设备 API / 能源 API 的第一批对象语义说明和兼容字段策略
- 当前阶段要求：
  - 已完成的第一批后端收敛不再继续扩张
  - 若真实联调暴露问题，只做兼容修正和说明补齐
  - 不再主动进入完整 `meter / point / relation` schema 设计
- 兼容原则：
  - 不做接口路径大规模重命名
  - 不做全量数据库 schema 重构
  - 若现有模型不足以一次补齐，优先保留兼容层和边界说明
  - 若返回字段需要变化，必须先写回本文件并说明影响范围
- 验证要求：
  - 验证设备对象、计量对象、能源类别对象第一批边界已明确
  - 验证 `EnergyData` 宽表字段的公共层 / 专属层 / 兼容层语义已补齐
  - 验证 `device_registry`、schema、落库模型的不一致项已收敛或明确记录
  - 验证设备 API / 能源 API 的第一批对象语义说明已可核对
- 明确禁止：
  - 不做完整 `meter / offline meter / virtual meter / point / relation table` 全量数据库落地
  - 不做前端设备管理页、多能源页、驾驶舱页面的大改版
  - 不扩张到告警、预测、控制、调度优化、碳排核算细则、费用结算细则等设备分类建模之外的业务主题
  - 不处理本轮主线之外的顺手优化

---

## 规范 -> 前端
### 任务
- 为第一批设备分类与对象分层建模优化做联调准备
- 本轮只围绕设备语义、计量语义、字段兼容说明做最小适配，不做页面大重构

### 已知信息
- 本轮重点接口和输出层主要集中在：
  - `frontend/src/api/device.ts`
  - `frontend/src/api/energy.ts`
  - `frontend/src/views/DeviceManager.vue`
  - `frontend/src/views/EnergyManagement.vue`
- 字段原则：
  - 与设备对象、计量对象、能源类别对象边界相关的字段原则上不要轻易改名
  - `device_type`、`device_category`、`energy_type`、`unit`、`rated_capacity` 的兼容语义如需变化，必须提前说明
  - 若后端补充“计量语义 / 点位语义 / 兼容说明字段”，优先走兼容新增，不直接删改旧字段

### 建议处理方式
- 前端本轮重点关注：
  - 设备列表和类型选择是否还能按现有接口正常工作
  - `device.ts`、`energy.ts` 是否已承接后端新增的最小对象语义字段
  - `DeviceManager.vue`、`EnergyManagement.vue` 是否需要按兼容新增字段做最小展示适配
- 前端本轮不要做：
  - 设备管理页大改版
  - 多能源页大改版
  - 驾驶舱全面改版
  - 因猜测 meter / point 语义而提前重写页面对象模型
- 当前阶段要求：
  - 先完成对后端新增对象语义兼容字段的真实联调确认
  - 收口前不新增页面级改造任务
- 若联调发现以下情况，必须先回写 handoff 再动代码：
  - 返回字段删除或重命名
  - `device_type / device_category / energy_type` 语义变化
  - `unit / rated_capacity / location` 的兼容语义变化
  - 设备对象和能耗对象的关联方式变化
  - 异常语义变化
  - 原有路径不兼容

---

## 前端 -> 后端
### 当前建议
- 前端本轮围绕“设备分类、计量对象、点位对象与多能源分层建模第一批收敛”已完成依赖审计，当前高优先级联调点如下：
  - `GET /devices/` / `POST /devices/` / `PUT /devices/{id}`
    - 受影响模块：`frontend/src/api/device.ts`、`frontend/src/views/DeviceManager.vue`、`frontend/src/views/Dashboard.vue`、`frontend/src/views/CampusScene.vue`
    - 当前直接依赖字段：`id`、`name`、`sn`、`device_type`、`device_category`、`energy_type`、`unit`、`rated_capacity`、`location`、`is_active`
    - 当前已补齐字段：`location_id`、`updated_at`
    - 隐式假设：前端仍把 `device_type` 当成设备对象、计量对象和能源类别对象的主入口字段；`rated_capacity` 仍被直接拿来做区域打分和运行规模推断
    - 联调提醒：`device_type / device_category / energy_type / unit / rated_capacity / location` 的兼容语义若变化，必须提前同步
  - `GET /devices/types`
    - 受影响模块：`frontend/src/api/device.ts`、`frontend/src/views/DeviceManager.vue`
    - 当前直接依赖字段：`device_type`、`category`、`energy_type`、`unit`、`default_capacity`、`required_fields`、`optional_fields`、`icon`、`name_zh`
    - 当前已承接兼容新增字段：`object_role`、`metering_role`、`point_kind`、`measurement_subject`、`public_data_fields`、`specialized_fields`、`compatible_aliases`
    - 隐式假设：页面仍以“注册表配置 = 对象语义”来渲染设备类型选择，没有独立 meter / point 对象层
    - 联调提醒：上述兼容新增字段原则上不要轻易改名；若继续追加 `rated_capacity_unit / consumption_unit / flow_unit` 这类说明字段，也请保持兼容新增
  - `GET /energy/types`
    - 受影响模块：`frontend/src/api/energy.ts`、`frontend/src/views/EnergyManagement.vue`
    - 当前直接依赖字段：`energy_types[*].value`、`label`、`unit`、`flow_unit`
    - 当前已承接兼容新增字段：`supported_device_types`、`data_object_kind`、`point_kind`、`public_fields`、`specialized_fields`、`field_boundary_rule`
    - 隐式假设：前端仍把 `energy_type` 视为设备和计量语义的主要来源之一
    - 联调提醒：即使字段名不变，`supported_device_types / public_fields / specialized_fields / field_boundary_rule` 的语义变化也必须提前通知
  - `GET /energy/data/{device_id}` / `GET /analysis/{device_id}`
    - 受影响模块：`frontend/src/api/energy.ts`、`frontend/src/api/telemetry.ts`、`frontend/src/views/EnergyManagement.vue`、`frontend/src/features/dashboard/composables/useDashboardRealtime.ts`、`frontend/src/views/CampusScene.vue`
    - 当前直接依赖字段：`consumption`、`flow_rate`、`voltage`、`current`、`pressure`、`temperature`、`supply_temp`、`return_temp`、`heat_flow`、`quality_index`、`current_power`、`today_energy`
    - 当前已承接兼容新增字段：`device_type`、`device_category`、`device_object_role`、`metering_role`、`point_kind`、`measurement_subject`、`energy_data_public_fields`、`energy_data_specialized_fields`
    - 隐式假设：页面仍通过“字段是否有值”猜对象语义，尚无法区分“当前没采到”和“该对象本无此字段”
    - 联调提醒：`current_power / today_energy` 旧字段仍被页面直接消费；若其含义与新增对象语义字段出现偏移，必须提前通知前端
  - `GET /energy/statistics` / `GET /energy/overview`
    - 受影响模块：`frontend/src/api/energy.ts`、`frontend/src/views/EnergyManagement.vue`、`frontend/src/features/dashboard/composables/useDashboardEnergyStats.ts`、`frontend/src/views/Dashboard.vue`
    - 当前直接依赖字段：`total_consumption`、`avg_consumption`、`avg_flow_rate`、`peak_flow_rate`、`statistics`
    - 当前已承接兼容新增字段：`supported_device_types`、`data_object_kind`、`point_kind`、`public_fields`、`specialized_fields`、`field_boundary_rule`
    - 隐式假设：`Dashboard.vue` 和 `EnergyManagement.vue` 仍自己拼业务口径
    - 联调提醒：字段名即使不变，只要对象语义或统计口径变化，也必须提前同步
  - `GET /reports/export_csv`
    - 受影响模块：`frontend/src/api/report.ts`、`frontend/src/views/Report.vue`
    - 当前依赖行为：仍假设 blob 下载稳定、设备和能源筛选参数保持兼容
    - 联调提醒：`energy_detail`、`carbon_emission` 既然已追加对象语义相关列，后续若继续调整列顺序或列名必须提前通知
- 前端已识别的高风险页面：
  - `frontend/src/views/DeviceManager.vue`
    - 仍以 `device_type` 驱动创建流程，页面本身没有设备对象 / 计量对象 / 点位对象分层消费
  - `frontend/src/views/EnergyManagement.vue`
    - 仍以 `energy_type + unit + total_consumption + 宽表字段` 组合消费对象语义
  - `frontend/src/views/Dashboard.vue`
    - 仍以 `device_type / energy_type / rated_capacity / total_consumption` 自行拼区域和总览口径
  - `frontend/src/views/CampusScene.vue`
    - 仍以 `device_type / current_power` 推断对象状态，偏旧电力设备理解
- 前端建议的最小兼容方式：
  - 旧字段继续保留，新增对象语义字段优先走兼容新增
  - 本轮前端已先补 `device.ts`、`energy.ts`、`telemetry.ts` 的类型层承接，不要求后端为此改路径或删旧字段
  - 若后端继续新增“公共层 / 专属层 / 兼容层”说明字段，前端优先先补 `api` 类型，再决定是否改页面消费点
  - `reports/export_csv` 继续保持现有 blob 下载模式，不要在本轮顺带改下载协议
- 当前真实联调仍需重点确认：
  - `DeviceManager.vue` 是否需要后续消费 `object_role / metering_role`
  - `EnergyManagement.vue` 是否需要基于 `public_fields / specialized_fields / field_boundary_rule` 调整展示解释
  - `Dashboard.vue` / `CampusScene.vue` 是否会继续误把 `current_power / rated_capacity` 当所有设备都适用的语义字段

## 前端 -> 规范
### 当前建议
- 当前最大的联调风险不是“字段不存在”，而是页面仍把 `device_type / device_category / energy_type / unit` 当作足够完整的对象语义。
- 若规范线程继续补文档，建议优先补三类说明：
  - `Device`、计量对象、点位对象在本轮第一批收敛中的边界说明
  - `EnergyData` 宽表字段里哪些属于公共层、哪些属于专属层、哪些只是兼容层
  - 当前不一致点的正式说明：输入中的 `DeviceManagement.vue` 实际文件为 `DeviceManager.vue`
- 当前不建议扩成新的大规范；只要让 PLAN、`current-status.md`、`handoff.md` 对本主题使用同一套对象语义表述即可
- 本轮前端已经补齐类型层承接，规范线程后续不需要再要求前端“先补 API 类型”；下一步更适合要求真实联调时核对页面消费语义

---

## 后端 -> 前端
### 当前建议
- 本轮已按 [PLAN-20260328-device-classification-modeling-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-optimization.md) 完成第一批后端收敛，重点接口如下：
  - `GET /devices/types`
  - `GET /devices/types/{device_type}`
  - `GET /devices/{device_id}/semantic-profile`
  - `GET /devices/{device_id}/statistics`
  - `GET /energy/types`
  - `GET /energy/overview`
  - `GET /energy/statistics`
  - `GET /analysis/{device_id}`
  - `GET /reports/export_csv`
- 本轮已收敛的对象语义：
  - `Device` 仍是统一对象，但现在明确通过 `device_type` registry 派生第一批 `object_role`、`metering_role`、`point_kind`、`measurement_subject`
  - `device_category` 继续表示兼容分组层，`energy_type` 继续表示能源介质层，前端不要再把任一单字段当成完整对象模型
  - `EnergyData` 仍是统一宽表，但现在明确区分：
    - 公共字段：`consumption`、`flow_rate`、`timestamp`
    - 专属字段：`voltage`、`current`、`power_factor`、`pressure`、`temperature`、`supply_temp`、`return_temp`、`heat_flow`、`quality_index`
    - 兼容层：如热量场景下 `heat_flow` 会映射到公共层 `flow_rate`
- 对前端保持兼容的内容：
  - 现有路径未重命名，请求参数未改
  - `GET /analysis/{device_id}` 仍保留 `device_id`、`is_active`、`current_power`、`voltage`、`current`、`today_energy`、`today_cost`
  - `GET /reports/export_csv` 仍返回 200 + CSV 流，原有 `energy_detail` / `alarm_history` / `carbon_emission` 仍可下载
  - 原有 `device_type`、`device_category`、`energy_type`、`unit`、`rated_capacity` 字段继续保留
- 本轮兼容新增字段：
  - `GET /devices/types` / `GET /devices/types/{device_type}`：
    - `object_role`
    - `metering_role`
    - `point_kind`
    - `measurement_subject`
    - `rated_capacity_unit`
    - `consumption_unit`
    - `flow_unit`
    - `public_data_fields`
    - `specialized_fields`
    - `compatible_aliases`
  - `GET /devices/{device_id}/semantic-profile`：
    - 设备对象、计量对象、点位对象的第一批兼容语义快照
  - `GET /devices/{device_id}/statistics`：
    - `device_semantics`
    - `statistics_boundary`
  - `GET /energy/types` / `GET /energy/overview` / `GET /energy/statistics`：
    - `supported_device_types`
    - `data_object_kind`
    - `point_kind`
    - `public_fields`
    - `specialized_fields`
    - `null_field_rule`
    - `field_boundary_rule`
    - `device_object_boundary`
  - `GET /analysis/{device_id}`：
    - `device_type`
    - `device_category`
    - `device_object_role`
    - `metering_role`
    - `point_kind`
    - `measurement_subject`
    - `energy_data_public_fields`
    - `energy_data_specialized_fields`
- 本轮细微变化但未改路径 / 主字段名的点：
  - 前端不能再把“宽表字段有值 / 无值”直接理解成对象语义；要优先结合 `public_fields`、`specialized_fields`、`null_field_rule`
  - 前端不能再把 `device_type` 单独理解成“设备对象 = 计量对象 = 点位对象 = 能源类别对象”的完整表达
  - `energy_detail`、`carbon_emission` 两类 CSV 在原列之后追加了：
    - `设备类型`
    - `设备类别`
    - `对象语义`
    - `点位语义`
    现有 blob 下载逻辑可继续用，但如果页面或脚本依赖固定列序，需要按新列头联调
- 前端联调注意：
  - 设备列表、设备类型选择器、驾驶舱实时卡片仍可继续用旧字段跑通，但若要正确消费对象语义，优先读取新增兼容字段
  - `EnergyManagement.vue` 这类页面如果还按 `energy_type + unit + 宽表字段有无` 猜对象语义，联调时要对照 `/energy/types`、`/energy/overview` 的新增边界字段确认
  - `Dashboard.vue` / `CampusScene.vue` 若继续拿 `current_power`、`rated_capacity` 直接推断全部设备语义，需结合 `metering_role`、`measurement_subject` 做最小消费调整
  - `GET /devices/{device_id}/semantic-profile` 是给联调和排障用的稳定入口，本轮推荐优先用它核对单设备语义
- 当前仍未解决的风险：
  - 还没有真正落地独立 meter / point / relation schema
  - `EnergyData` 宽表仍存在深层 nullable 扩展字段问题，本轮只补了第一批边界说明
  - `reports/export_csv` 的列追加是兼容新增，但外部脚本若硬编码列序仍需确认
  - 设备类型数量以后端注册表实际 10 种为准；若其他文档仍写 11 种，应以后端实际输出和本轮 PLAN 为准

## 后端 -> 规范
### 当前建议
- 本轮已按 [PLAN-20260328-device-classification-modeling-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-optimization.md) 的既定边界实施，无需重新开新主题。
- 已落实的第一批规范口径：
  - `Device` 继续作为统一对象保留，不在本轮强拆数据库结构
  - `device_type` 作为对象语义派生入口，`device_category` 作为兼容分组层，`energy_type` 作为能源介质层
  - 计量对象 / 点位对象当前通过 registry 元信息和接口新增字段兼容表达，不等同于已落库成独立 schema
  - `EnergyData` 当前按“公共字段 / 专属字段 / 兼容层”解释，不代表宽表问题已经彻底解决
- 建议规范线程后续只补以下内容，不要扩成新一轮全系统重构：
  - 把“设备对象 / 计量对象 / 点位对象 / 能源类别对象”的第一批兼容表达写入后端规范或产品语义说明
  - 清理仍写成 11 种设备类型的历史文档，统一为注册表当前 10 种
  - 继续明确哪些场景必须进入真正的 meter / point / relation schema 设计，哪些场景继续沿用兼容层即可
- 当前代码与计划的最小兼容差异：
  - 本轮通过新增 `/devices/{device_id}/semantic-profile` 提供联调用语义快照，这属于计划允许的兼容新增，不是路径替换
  - `reports/export_csv` 没有新建独立报表协议，而是在现有 `energy_detail`、`carbon_emission` 导出里追加语义列，属于最小兼容实现

---

## 验收 -> 全局
### 验收结论
- 本轮“CampusEnergySystem 设备分类、计量对象、点位对象与多能源分层建模优化闭环验收”结论为：部分完成，需交回前端线程。
- 当前状态更准确地说是：
  - 探索线程达标
  - 规范线程达标
  - 后端线程达标
  - 前端线程仅在 API 类型层还剩一个未补齐的兼容字段缺口

### 暂不收口的原因
- 规范侧已不再是阻塞点：
  - [PLAN-20260328-device-classification-modeling-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-optimization.md) 已更新为“进行中”，并补齐了进度记录。
- 前端兼容字段承接仍有一个未闭环点：
  - [frontend/src/api/device.ts](/Users/todo/MineEnergySystem/frontend/src/api/device.ts) 已承接设备类型对象语义兼容新增字段。
  - [frontend/src/api/telemetry.ts](/Users/todo/MineEnergySystem/frontend/src/api/telemetry.ts) 已承接 `analysis` 对象语义兼容新增字段。
  - [frontend/src/api/energy.ts](/Users/todo/MineEnergySystem/frontend/src/api/energy.ts) 尚未承接后端 / handoff 已明确的 `null_field_rule`、`device_object_boundary`、`energy_profiles`，因此本轮“前端已完成对象语义兼容字段承接”还不能判定通过。

### 线程完成情况
- 探索线程：已完成。探索文档已落到 [PLAN-20260328-device-classification-modeling-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-audit.md)，且已明确 EMS 分层建模差距、本轮范围和非目标。
- 规范线程：已完成。正式 PLAN 已建立，且状态、进度记录已回写到当前实际状态。
- 后端线程：已完成。`Device`、`device_registry`、`EnergyData`、设备 / 能源接口、analysis / reports 兼容新增语义字段均已落地，且 38 个相关测试通过。
- 前端线程：部分完成。`device.ts`、`telemetry.ts` 已达标，但 `energy.ts` 仍未补齐全部对象语义边界字段。

### 下一步交接建议
- 交回前端线程：
  - 补齐 [energy.ts](/Users/todo/MineEnergySystem/frontend/src/api/energy.ts) 对 `null_field_rule`、`device_object_boundary`、`energy_profiles` 的类型承接。
  - 补完后重新执行前端构建，并由验收线程复核。
- 当前不建议交回规范线程或后端线程继续追加工作；这两侧已达到本次终验要求。

---

## 探索 -> 规范
### 摘要归档
- 当前问题不是“没有 application 目录”，而是“application use case 过薄、endpoint 过重、service 职责上浮”。
- 第一批只收敛三条主路径：
  - 设备数据上报 / 查询 / 统计
  - 设备分析
  - 报表导出
- 目标是形成清晰的 `endpoint -> application -> service/repository` 调用链，而不是做全项目分层重构。

---

## 规范 -> 全局
### 执行约束
- 本轮核心是“主路径统一”，不是“代码搬家”
- PLAN、`current-status.md`、`handoff.md` 必须一起维护，关键决策不能只留在聊天记录里
- 若 application 收敛未完成，优先保持兼容，不继续扩张范围

---

## 探索 -> 规范
### 交接主题
- 多能源数据业务逻辑审计：`电 / 热 / 气 / 冷 / 碳排放`

### 当前主要问题
- 当前多能源建模仍以 `energy_type` + 通用时序字段为主，核心模型主要依赖 `consumption` / `flow_rate`，能源专属业务语义不足。
- `EnergyData` 虽然把 `consumption` 注释为累计量、`flow_rate` 注释为瞬时量，但统计和汇总代码并未严格区分两类口径，存在累计量 / 瞬时量混用风险。
- 单位体系目前只有静态映射，尚未形成“内部标准单位、入库换算、展示单位”三层规则；冷 / 热 / 气的数据语义和量纲边界仍不够稳。
- 碳排逻辑当前主要是固定因子乘法，更适合驾驶舱展示，不适合作为正式核算口径。
- `analysis` / `reports` 对多能源的理解仍偏通用分类和明细导出，尚未形成电 / 热 / 气 / 冷各自的业务分析指标。

### 本轮建议优先优化的层
- P0：数据口径层
  - 先定义累计量、瞬时量、差值量、统计量的严格边界。
- P0：单位与标准化层
  - 先统一内部标准单位和接入换算规则。
- P1：碳排核算层
  - 先区分展示级碳排与核算级碳排。
- P1：多能源语义层
  - 明确每类能源最小必备业务语义。
- P2：指标与分析层
  - 在前面几层稳定后，再补多能源专属分析和报表。

### 为什么不要一开始就发散成全系统重构
- 当前问题的核心不在“没有多能源能力”，而在“现有多能源能力过于通用化”。
- 如果直接扩成全模型重构、全接口重命名或前端改版，范围会远大于真正的瓶颈。
- 更合理的路径是先把口径、单位、碳排边界和能源语义定清，再决定最小实施面。

### 规范线程下一步应该如何收敛成 PLAN
- 以 [PLAN-20260327-multi-energy-data-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-multi-energy-data-audit.md) 为输入，新建一个实施计划文档。
- 计划标题建议：
  - `docs/plans/PLAN-20260327-multi-energy-semantics-and-metering-governance.md`
- 计划范围建议优先锁定：
  - 累计量 / 瞬时量口径
  - 单位标准化
  - 碳排逻辑分层
  - 分能源最小业务语义
- 计划验收建议优先要求：
  - 已明确各字段口径和禁止混用场景
  - 已明确内部标准单位与展示单位规则
  - 已明确展示级 / 核算级碳排边界
  - 已明确各类能源的最小业务指标清单

### 本轮明确不做
- 不展开告警逻辑。
- 不展开预测逻辑。
- 不做前端页面改版。
- 不做设备控制逻辑改造。
- 不做全项目数据模型重构。
- 不在本轮直接重写 `EnergyData` / `CarbonEmission` 表结构。

### 可直接阅读的文档入口
- [PLAN-20260327-multi-energy-data-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-multi-energy-data-audit.md)
- [current-status.md](/Users/todo/MineEnergySystem/docs/plans/current-status.md)
- [handoff.md](/Users/todo/MineEnergySystem/docs/plans/handoff.md)

---

## 2026-03-28｜探索 -> 规范｜设备分类与对象分层建模

### 交接主题
- 基于 EMS（MyEMS）项目设备分类建模思路，对 CampusEnergySystem 的设备分类、计量对象、点位对象、对象关系与多能源扩展建模进行审计。

### 当前主要简化点 / 风险点
- 当前系统不是没有设备分类能力，而是分类主要停留在 `device_type + device_category + energy_type` 的薄分类层，未形成“能源类别 / 仪表对象 / 点位对象 / 业务对象 / 关系表”分层。
- `Device` 同时承担业务设备、计量设备和能源类型标签语义；`build_device_create_fields()` 会从 `device_type` 派生 `device_category / energy_type / unit / rated_capacity`，说明对象边界仍混在一起。
- `EnergyData` 仍是统一宽表，`voltage / current / power_factor / pressure / temperature / supply_temp / return_temp / heat_flow / quality_index` 等异构字段共表存储，空字段与“本对象本来无此语义”无法区分。
- 当前没有独立计量对象层雏形：未发现 `meter / virtual meter / offline meter` 正式模型，表计主要通过 `water_meter / gas_meter / heat_meter / cooling_meter / steam_meter` 这类 `device_type` 表达。
- 当前没有独立点位对象层雏形：能源采集值主要通过 `EnergyData` 和 payload 字段承载，没有独立 `point / telemetry_point / measurement_point` 模型。
- `app/core/device_registry.py` 中声明的 `irradiance / wind_speed / soc / charging_status` 等字段，实际没有被 `app/api/endpoints/devices/shared.py`、`app/domain/device_payloads.py`、`app/models/tables.py` 承接，存在定义与实现不一致。
- 文档与代码也存在不一致：
  - `docs/02-功能使用/统一设备管理指南.md` 写内置 11 种设备类型，代码注册表实际为 10 种。
  - 任务输入给出的 `frontend/src/views/DeviceManagement.vue` 在仓库中不存在，实际文件为 `frontend/src/views/DeviceManager.vue`。

### 建议优先优化的层
- P0：设备对象 / 计量对象 / 能源类型对象边界治理
  - 先明确 `Device` 继续承载什么，不再往里继续塞 meter 语义和更多对象职责。
- P0：宽表可空字段与专属字段语义治理
  - 先把 `EnergyData` 中“可选采集字段”和“该对象无此字段语义”分清，避免继续无序膨胀。
- P1：点位 / 测点建模与扩展字段治理
  - 先明确是否需要独立 point 对象层，至少先建立扩展字段和采集语义边界。
- P1：多能源对象分层与对象关系治理
  - 在前两层稳定后，再决定是否补 meter / relation 这一层。
- P2：analysis / reporting / overview 层再建设
  - 在对象语义没站稳之前，不建议先堆新的统计与展示能力。

### 为什么不要一开始就发散成全系统重构
- 当前最核心的问题不是“系统完全没有设备建模”，而是“已有统一设备台账和统一接入底座，但分类过薄、对象未分层、宽表过载、定义与实现不一致”。
- 如果一开始就扩成数据库全量重构、全对象体系重建或前端全面改版，风险会超过当前真实瓶颈，也会让后续线程失去最小落地边界。
- 更合理的路径是先控制范围，先做对象边界和语义治理，再决定哪些层需要真正独立建模。

### 规范线程下一步应如何收敛成 PLAN
- 直接以 [PLAN-20260328-device-classification-modeling-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-audit.md) 为输入编写正式 PLAN。
- 建议计划标题：
  - `docs/plans/PLAN-20260328-device-object-layering-and-meter-point-governance.md`
- 建议第一批范围锁定：
  - `Device` 的对象边界和派生字段边界
  - `device_registry`、请求 schema、落库模型的一致性治理
  - `EnergyData` 宽表扩张边界和字段语义约束
  - 是否引入“计量对象层 / 点位对象层”的最小判定标准
- 建议验收优先要求：
  - 已明确当前系统在本主题上的定位不是“专业 EMS 分层对象建模级”
  - 已明确哪些语义不得继续塞进 `Device` 和 `EnergyData`
  - 已明确注册表、schema、model 的一致性规则
  - 已明确第一批不碰哪些范围外模块

### 本轮明确不做
- 不展开告警模块、预测模块、设备控制模块、巡检模块、权限模块、认证模块。
- 不展开前端通用 UI 重构。
- 不展开数据库全量重构。
- 不展开 LSTM 预测模块、MQTT 接入可靠性、碳排核算细则、费用结算细则、调度优化模块。
- 不在本轮直接设计或实现完整的 meter / point 新模型。

### 文档入口
- [PLAN-20260328-device-classification-modeling-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-audit.md)
- [current-status.md](/Users/todo/MineEnergySystem/docs/plans/current-status.md)
- [handoff.md](/Users/todo/MineEnergySystem/docs/plans/handoff.md)
