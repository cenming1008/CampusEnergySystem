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
    - 当前已承接兼容新增字段：`supported_device_types`、`data_object_kind`、`point_kind`、`public_fields`、`specialized_fields`、`field_boundary_rule`、`null_field_rule`、`device_object_boundary`
    - 隐式假设：前端仍把 `energy_type` 视为设备和计量语义的主要来源之一
    - 联调提醒：即使字段名不变，`supported_device_types / public_fields / specialized_fields / field_boundary_rule / null_field_rule / device_object_boundary` 的语义变化也必须提前通知
  - `GET /energy/data/{device_id}` / `GET /analysis/{device_id}`
    - 受影响模块：`frontend/src/api/energy.ts`、`frontend/src/api/telemetry.ts`、`frontend/src/views/EnergyManagement.vue`、`frontend/src/features/dashboard/composables/useDashboardRealtime.ts`、`frontend/src/views/CampusScene.vue`
    - 当前直接依赖字段：`consumption`、`flow_rate`、`voltage`、`current`、`pressure`、`temperature`、`supply_temp`、`return_temp`、`heat_flow`、`quality_index`、`current_power`、`today_energy`
    - 当前已承接兼容新增字段：`device_type`、`device_category`、`device_object_role`、`metering_role`、`point_kind`、`measurement_subject`、`energy_data_public_fields`、`energy_data_specialized_fields`
    - 隐式假设：页面仍通过“字段是否有值”猜对象语义，尚无法区分“当前没采到”和“该对象本无此字段”
    - 联调提醒：`current_power / today_energy` 旧字段仍被页面直接消费；若其含义与新增对象语义字段出现偏移，必须提前通知前端
  - `GET /energy/statistics` / `GET /energy/overview`
    - 受影响模块：`frontend/src/api/energy.ts`、`frontend/src/views/EnergyManagement.vue`、`frontend/src/features/dashboard/composables/useDashboardEnergyStats.ts`、`frontend/src/views/Dashboard.vue`
    - 当前直接依赖字段：`total_consumption`、`avg_consumption`、`avg_flow_rate`、`peak_flow_rate`、`statistics`
    - 当前已承接兼容新增字段：`supported_device_types`、`data_object_kind`、`point_kind`、`public_fields`、`specialized_fields`、`field_boundary_rule`、`null_field_rule`、`energy_profiles`
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
  - `EnergyManagement.vue` 是否需要基于 `public_fields / specialized_fields / null_field_rule / field_boundary_rule / device_object_boundary` 调整展示解释
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

## 每日归档入口

- [2026-03-27 交接快照](./daily/2026-03/2026-03-27-handoff.md)
- [2026-03-28 交接快照](./daily/2026-03/2026-03-28-handoff.md)
