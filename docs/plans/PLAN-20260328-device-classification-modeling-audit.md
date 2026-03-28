# Device Classification Modeling Audit

## 1. 背景

本轮审计聚焦：

- 基于 EMS（MyEMS）项目设备分类建模思路，对 CampusEnergySystem 的设备分类、计量对象、点位对象、对象关系与多能源扩展建模进行审计。

当前系统中，这一主题主要落在以下位置：

- 后端模型与领域规则：
  - `app/models/tables.py`
  - `app/domain/device_payloads.py`
  - `app/domain/energy_rules.py`
  - `app/core/device_registry.py`
- 设备与能耗服务：
  - `app/services/device_service.py`
  - `app/services/energy_service.py`
  - `app/repositories/device_repository.py`
  - `app/repositories/energy_repository.py`
- use case 与接口：
  - `app/application/device_reporting.py`
  - `app/application/energy_management.py`
  - `app/api/endpoints/devices/*.py`
  - `app/api/endpoints/energy/*.py`
- 前端语义与展示落点：
  - `frontend/src/api/device.ts`
  - `frontend/src/api/energy.ts`
  - `frontend/src/views/DeviceManager.vue`
  - `frontend/src/views/EnergyManagement.vue`

本轮输入来源包括：

- 协作与计划文档：
  - `docs/plans/current-status.md`
  - `docs/plans/handoff.md`
  - `docs/plans/PLAN-20260327-multi-energy-data-audit.md`
- 业务与架构文档：
  - `README.md`
  - `docs/05-架构与设计/*`
  - `docs/02-功能使用/统一设备管理指南.md`
  - `docs/02-功能使用/多能源管理指南.md`
  - `docs/关键功能链路说明.md`

本轮参考的 EMS（MyEMS）式分层建模特征，不来自本仓库代码，而是来自你给出的目标建模特征：

- 能源类别表
- 仪表对象层
- 点位对象层
- 业务对象分表
- 关系表挂接

因此本轮审计的核心，不是判断“当前系统能不能跑”，而是判断：

- 它在“能源类别 / 仪表对象 / 点位对象 / 业务对象 / 关系表”这些层面，距离专业 EMS 分层建模还有多远。

---

## 2. 结论摘要

- 当前系统在本主题上**不是完全没有设备分类能力**，而是分类主要停留在 `device_type + device_category + energy_type` 这组薄标签层，尚未形成 EMS（MyEMS）式的分层对象建模。
- 当前主设备对象 `Device` 同时承担了“业务设备 / 计量设备 / 能源类型标签 / 部分计量配置”的多重角色，设备对象、计量对象、能源类别对象并未真正分层。
- 当前多能源时序对象 `EnergyData` 仍是典型统一宽表，依靠大量可空字段承载电、热、气、冷、水、蒸汽等异构对象，语义边界不够清晰。
- 当前系统**没有独立的计量对象层雏形**：未发现独立的 `meter` / `offline meter` / `virtual meter` 模型，也没有“业务对象挂接计量对象”的关系表。
- 当前系统**没有独立的点位对象层雏形**：与设备采集相关的数据仍通过 `EnergyData` 可空字段和 MQTT payload 字段承载，没有类似 MyEMS 的 point / telemetry point 对象。
- 当前实现与文档存在多处不一致：
  - `docs/02-功能使用/统一设备管理指南.md` 写“内置 11 种设备类型”，代码实际注册了 10 种。
  - 注册表给部分电力设备声明了 `irradiance`、`wind_speed`、`soc`、`charging_status` 等字段，但实际 schema / model / payload 规范化并未承接。
  - 用户指定的前端文件 `frontend/src/views/DeviceManagement.vue` 在仓库中不存在，实际文件为 `frontend/src/views/DeviceManager.vue`。
- 前端设备管理页和多能源页目前更多是消费“设备类型配置”和“统一能耗宽表字段”，并未建立明确的设备对象 / 计量对象 / 点位对象语义。
- 综合判断：当前系统在本主题上更接近**基础设备台账级 + 统一接入展示级之间的过渡状态**，明显低于“分层对象建模级”，更不是“专业 EMS 对象建模级”。

---

## 3. 当前实现的问题清单

### 问题 1：`Device` 同时承担设备对象、计量对象和能源类型对象语义

- 涉及文件：
  - `app/models/tables.py`
  - `app/domain/device_payloads.py`
  - `app/services/device_service.py`
  - `app/api/endpoints/devices/management.py`
  - `frontend/src/api/device.ts`
  - `frontend/src/views/DeviceManager.vue`
- 涉及函数 / 类 / endpoint：
  - `Device`
  - `build_device_create_fields`
  - `DeviceService.create_device_smart`
  - `GET /devices/`
  - `POST /devices/`
  - `GET /devices/types`
- 当前做法：
  - `Device` 直接持有 `device_type`、`device_category`、`energy_type`、`rated_capacity`、`unit`。
  - `build_device_create_fields()` 会根据 `device_type` 一次性回填 `device_category`、`energy_type`、`unit`、`rated_capacity`。
  - 前端新增设备时只选 `device_type`，其他语义都默认由后端派生。
- 问题：
  - 这说明当前只有“统一 Device + 标签派生”的轻量建模，没有把业务设备、计量设备、能源类别对象分层。
  - `Device` 既像台账对象，又像仪表对象，还带着能源类型标签与单位定义，职责混合。
- 风险：
  - 后续若需要引入“一个业务设备挂多个计量表”“一个计量表挂多个点位”“一个虚拟表聚合多个实体表”，现有 `Device` 结构会很吃力。
  - 业务设备与计量设备无法区分，会让统计、展示和接入语义继续纠缠。
- 影响范围：
  - 设备创建
  - 设备查询
  - 设备筛选
  - 能源统计
  - 前端设备页和多能源页

### 问题 2：设备类型注册表增强了“分类配置”，但没有形成对象分层

- 涉及文件：
  - `app/core/device_registry.py`
  - `app/services/device_service.py`
  - `app/api/endpoints/devices/management.py`
  - `docs/02-功能使用/统一设备管理指南.md`
- 涉及函数 / 类 / endpoint：
  - `DeviceTypeConfig`
  - `DeviceRegistry._init_registry`
  - `DeviceRegistry.to_dict`
  - `DeviceService.get_device_types`
  - `GET /devices/types`
- 当前做法：
  - 系统用注册表维护 `device_type -> category / energy_type / unit / required_fields / optional_fields`。
  - 前后端通过 `/devices/types` 消费这个配置。
- 问题：
  - 这是一种“设备类型元数据表征”，不是“对象分层”。
  - 注册表虽然提供分类增强，但并没有独立出：
    - 计量对象层
    - 点位对象层
    - 业务对象层
    - 关系挂接层
- 风险：
  - 容易让后续线程误以为“既然有注册表，就已经有了设备建模体系”，从而继续把复杂语义往 `Device` 和 `EnergyData` 上硬塞。
- 影响范围：
  - 设备类型扩展
  - 文档说明
  - 前端设备类型选择与展示

### 问题 3：注册表声明的字段与实际承载字段不一致

- 涉及文件：
  - `app/core/device_registry.py`
  - `app/domain/device_payloads.py`
  - `app/api/endpoints/devices/shared.py`
  - `app/models/tables.py`
  - `tests/test_device_domain.py`
- 涉及函数 / 类 / endpoint：
  - `DeviceRegistry._init_registry`
  - `OPTIONAL_REPORT_FIELDS`
  - `normalize_device_report_payload`
  - `DeviceDataReportRequest`
  - `EnergyData`
- 当前做法：
  - 注册表为不同设备声明 `optional_fields`。
  - 上报请求模型和 payload 规范化只支持固定字段集合。
  - `EnergyData` 也只落一组固定宽表字段。
- 问题：
  - `solar` 注册了 `irradiance`
  - `wind` 注册了 `wind_speed`
  - `storage` 注册了 `soc`
  - `charger` 注册了 `charging_status`
  - 但这些字段：
    - 不在 `DeviceDataReportRequest`
    - 不在 `OPTIONAL_REPORT_FIELDS`
    - 不在 `EnergyData`
  - 说明“模型定义”和“代码实际承载能力”不一致。
- 风险：
  - 文档和注册表会给人一种“系统支持这些字段”的印象，但真实链路里这些字段既不入参稳定，也不入库。
  - 后续线程容易基于注册表误判当前能力。
- 影响范围：
  - 设备类型文档
  - 数据上报
  - 设备语义扩展
  - 前后端联调预期

### 问题 4：`EnergyData` 统一宽表承载异构设备字段，空字段与无意义字段混淆

- 涉及文件：
  - `app/models/tables.py`
  - `app/domain/device_payloads.py`
  - `app/services/energy_service.py`
  - `app/api/endpoints/energy/shared.py`
  - `frontend/src/api/energy.ts`
  - `frontend/src/views/EnergyManagement.vue`
- 涉及函数 / 类 / endpoint：
  - `EnergyData`
  - `EnergyDataCreate`
  - `save_energy_data`
  - `get_energy_data`
- 当前做法：
  - 一个统一 `EnergyData` 表承载：
    - 电压 / 电流 / 功率因数
    - 压力 / 温度
    - 供回水温度 / 热流量
    - 质量指标
  - 电、热、气、冷、水、蒸汽共用同一时序表。
- 问题：
  - 当前是标准的“统一表 + 大量 nullable 字段”模式。
  - 对某些对象来说，字段为空可能意味着：
    - 该字段暂时没采到
    - 该字段对该对象根本没有意义
  - 这两种情况在模型里无法区分。
- 风险：
  - 前端和后端都容易通过“字段有没有值”猜对象语义。
  - 后续如果继续往表里加更多设备专属字段，宽表会继续膨胀。
- 影响范围：
  - 入库逻辑
  - 统计逻辑
  - 前端明细展示
  - 报表导出

### 问题 5：当前没有独立计量对象层

- 涉及文件：
  - `app/models/tables.py`
  - `app/services/device_service.py`
  - `app/api/endpoints/devices/management.py`
  - `app/services/campus_service.py`
- 涉及函数 / 类 / endpoint：
  - `Device`
  - `DeviceService.create_device_smart`
  - `CampusService._is_meter`
- 当前做法：
  - 系统通过 `device_type` 或 `device_category` 间接表达“表计”。
  - `CampusService` 甚至通过 `device_category in METER_DEVICE_CATEGORIES` 或字符串包含 `meter` 来判断是否为表计。
- 问题：
  - 这说明“meter”不是正式对象层，而只是标签和命名约定。
  - 未发现独立 `Meter` / `VirtualMeter` / `OfflineMeter` 模型。
- 风险：
  - 业务设备与计量设备无法解耦。
  - 虚拟表、分摊表、总表、分表等专业 EMS 典型对象无法自然落位。
- 影响范围：
  - 多能源统计
  - 园区汇总
  - 后续报表和能效分析

### 问题 6：当前没有独立点位 / 测点对象层

- 涉及文件：
  - `app/models/tables.py`
  - `app/integrations/mqtt/processor.py`
  - `app/domain/device_payloads.py`
  - `app/api/endpoints/devices/shared.py`
  - `app/api/endpoints/energy/shared.py`
- 涉及函数 / 类 / endpoint：
  - `EnergyData`
  - `build_data_dict`
  - `normalize_device_report_payload`
  - `DeviceDataReportRequest`
  - `EnergyDataCreate`
- 当前做法：
  - MQTT 和 API 上报都直接把测点值塞入统一 payload。
  - 后端没有独立的 point / telemetry_point / measurement_point 模型。
  - `point` 这个词只在巡检模块里出现，与能源采集无关。
- 问题：
  - 采集点位语义没有被建模成稳定对象，只剩“设备上的一组可空字段”。
  - 当前更像“设备快照宽表”而不是“设备 + 点位 + 采样值”。
- 风险：
  - 难以表达一个设备挂多个测点、测点有编码、有单位、有含义、有来源的专业场景。
  - 也难以做点位级映射、点位模板、点位复用和点位权限。
- 影响范围：
  - MQTT 接入
  - API 手工补录
  - 设备监控
  - 多能源明细和报表

### 问题 7：前后端对设备对象的理解并不完全一致

- 涉及文件：
  - `app/models/tables.py`
  - `frontend/src/api/device.ts`
  - `frontend/src/views/DeviceManager.vue`
- 涉及函数 / 类 / endpoint：
  - 后端 `Device`
  - 前端 `Device` interface
  - `getDevices`
  - `createDevice`
- 当前做法：
  - 后端 `Device` 有 `location_id` 和 `location` 双字段。
  - 前端 `Device` interface 只声明了 `location`，未声明 `location_id`。
  - 设备页也只围绕 `location` 字符串编辑和展示。
- 问题：
  - 这使设备对象在前端被理解成“带位置文本的台账项”，而不是“挂接到位置体系的对象”。
  - 设备与业务空间对象的关系，前端没有稳定显式建模。
- 风险：
  - 后续若要推进真正的对象关系建模，前端会先卡在接口语义层。
- 影响范围：
  - 设备页
  - 位置权限理解
  - 设备与位置联动展示

### 问题 8：文档与代码存在可验证的不一致

- 涉及文件：
  - `docs/02-功能使用/统一设备管理指南.md`
  - `app/core/device_registry.py`
  - `frontend/src/views/DeviceManager.vue`
- 涉及函数 / 类 / endpoint：
  - `DeviceRegistry._init_registry`
  - `/devices/types`
- 当前做法：
  - 文档写“内置 11 种设备类型”。
  - 实际注册表中可数出 10 种：
    - load
    - solar
    - wind
    - storage
    - charger
    - water_meter
    - gas_meter
    - heat_meter
    - cooling_meter
    - steam_meter
  - 用户指定的 `frontend/src/views/DeviceManagement.vue` 在仓库中不存在，实际文件是 `frontend/src/views/DeviceManager.vue`。
- 问题：
  - 文档与代码、输入与代码均存在不一致点。
- 风险：
  - 后续线程会基于错误文件名或错误设备类型数量理解系统边界。
- 影响范围：
  - 文档导航
  - 设备类型扩展认知
  - 线程间交接准确性

---

## 4. 分模块 / 分对象逐项分析

### 4.1 设备主对象（Device）

#### 代码落点

- `app/models/tables.py` 的 `Device`
- `app/domain/device_payloads.py` 的 `build_device_create_fields`
- `app/services/device_service.py` 的 `create_device_smart` / `get_device_data` / `get_device_statistics`
- `app/api/endpoints/devices/management.py`

#### 当前实现

- `Device` 是唯一主设备对象。
- 新建设备时，只要给 `device_type`，后端就自动推出：
  - `device_category`
  - `energy_type`
  - `unit`
  - `rated_capacity`
- 后续统计、明细、监控都仍然围绕这个 `Device` 展开。

#### 审计判断

- 当前 `Device` 更像“统一设备台账 + 轻量计量标签”。
- 它没有分离出：
  - 业务设备对象
  - 计量设备对象
  - 能源类别对象
  - 关系对象

#### 结论

- 当前系统不是没有分类，而是分类主要停留在“设备类型映射 + 标签派生”，没有进入分层对象建模。

---

### 4.2 多能源时序对象（EnergyData）

#### 代码落点

- `app/models/tables.py` 的 `EnergyData`
- `app/services/energy_service.py`
- `app/api/endpoints/energy/shared.py`
- `frontend/src/api/energy.ts`

#### 当前实现

- `EnergyData` 是统一时序对象。
- 同时承载：
  - 通用字段：`consumption`、`flow_rate`
  - 电字段：`voltage`、`current`、`power_factor`
  - 水气字段：`pressure`、`temperature`
  - 热字段：`supply_temp`、`return_temp`、`heat_flow`
  - 质量字段：`quality_index`

#### 审计判断

- 这是典型的统一宽表。
- 它适合统一接入、统一查询，但不适合持续承接越来越多的异构设备语义。

#### 结论

- 当前 `EnergyData` 还不具备 MyEMS 式“仪表对象 + 点位对象 + 采样值”的分层表达能力。

---

### 4.3 计量对象缺失问题

#### 代码落点

- `app/models/tables.py`
- `app/services/device_service.py`
- `app/services/campus_service.py`
- `docs/02-功能使用/统一设备管理指南.md`

#### 当前实现

- 表计只是 `device_type=water_meter/gas_meter/...` 这种设备类型。
- 计量属性靠 `energy_type`、`unit`、`rated_capacity` 和时序字段表达。

#### 审计判断

- 还没有“计量对象独立建模”的雏形。
- `meter` 只是设备分类词，不是正式对象层。

#### 结论

- 当前系统若继续叠加“总表 / 分表 / 虚拟表 / 分摊表 / 成本科目表”等能力，会很容易失去边界。

---

### 4.4 点位对象缺失问题

#### 代码落点

- `app/integrations/mqtt/processor.py`
- `app/domain/device_payloads.py`
- `app/api/endpoints/devices/shared.py`
- `app/api/endpoints/energy/shared.py`

#### 当前实现

- 测点在 MQTT payload 和 API 请求里直接以字段形式出现。
- 点位没有独立编码、独立定义、独立单位、独立关系。
- 巡检模块存在 `InspectionPoint`，但这是巡检业务点，不是能源采集点。

#### 审计判断

- 当前还没有点位对象层雏形。
- `field -> value` 仍是“扁平属性”，不是“点位对象”。

#### 结论

- 与 MyEMS 的“点位对象单独建模、对象表通过 point_id 或关系表挂接点位”相比，当前差距明显。

---

### 4.5 前端设备语义与展示层

#### 代码落点

- `frontend/src/api/device.ts`
- `frontend/src/views/DeviceManager.vue`
- `frontend/src/api/energy.ts`
- `frontend/src/views/EnergyManagement.vue`

#### 当前实现

- 设备页：
  - 主要展示 `name / sn / device_type / location / is_active`
  - 创建设备时只选 `device_type`
- 多能源页：
  - 主要消费统一 `EnergyData`、`EnergyStatistics`、`CarbonSummary`
  - 页面直接用 `energyTypes[*].unit` 和 `statistics[*].total_consumption` 做展示

#### 审计判断

- 前端没有设备对象 / 计量对象 / 点位对象的独立视角。
- 页面主要依赖：
  - 后端给的设备类型元数据
  - 宽表统计结果
- 不是通过对象关系，而是通过“字段组合 + 类型标签”理解设备语义。

#### 结论

- 当前前端语义与展示层仍然跟随后端的轻量建模，而不是在消费专业对象模型。

---

### 4.6 与 EMS（MyEMS）分层建模的对照分析

#### MyEMS 目标特征

- 能源类别表
- 仪表对象层
- 点位对象层
- 业务对象分表
- 关系表挂接

#### 当前系统实际情况

- 能源类别表：
  - 没有独立表。
  - 目前只有 `EnergyType` 枚举和若干静态 options。
- 仪表对象层：
  - 没有独立模型。
  - 目前通过 `device_type` 中带 `meter` 的设备类型表达。
- 点位对象层：
  - 没有独立模型。
  - 目前通过 `EnergyData` 可空字段和 MQTT payload 字段表达。
- 业务对象分表：
  - 没有。
  - 当前只有一个统一 `Device`。
- 关系表挂接：
  - 在本主题内没有发现。
  - 当前主要靠 `Device -> EnergyData` 直接关联。

#### 结论

- 相比 MyEMS，CampusEnergySystem 在本主题上仍处于“统一接入 + 统一设备台账 + 宽表时序”的阶段。
- 主要差距不是“缺一个枚举”，而是**对象层级本身没有分出来**。

---

## 5. 当前系统定位判断

### 判断结论

**当前系统在本主题上更接近：基础设备台账级。**

如果细分层级，可以说是：

- 以“统一接入展示级”为底
- 向“基础设备台账级”延伸
- 但尚未进入“分层对象建模级”

### 判断依据

#### 为什么高于“统一接入展示级”

- 已经有稳定 `Device` 台账对象。
- 已经有设备类型注册表。
- 已经有能源类型、设备类别、单位、默认容量等派生能力。
- 已经有设备管理、设备查询、设备类型查询、统一上报接口。

#### 为什么低于“分层对象建模级”

- 没有独立 meter 对象。
- 没有独立 point 对象。
- 没有业务对象与计量对象分离。
- 没有对象关系挂接层。
- 宽表仍承担大量异构字段。

#### 为什么不是“专业 EMS 对象建模级”

- MyEMS 式“能源类别 + 仪表对象 + 点位对象 + 业务对象 + 关系表”结构在当前仓库里没有雏形级落点。

---

## 6. 第一批最值得优化的方向

### 优先级 1：设备对象 / 计量对象 / 能源类型对象边界治理

- 为什么最高：
  - 这是所有后续问题的源头。
  - 如果不先把 `Device` 的角色边界说清，后面无论补点位、补报表还是补分析，都还会继续混层。
- 涉及模块：
  - `app/models/tables.py`
  - `app/domain/device_payloads.py`
  - `app/services/device_service.py`
  - `app/api/endpoints/devices/*`
- 本轮建议做到什么程度：
  - 先由规范线程明确对象边界与术语，不直接做数据库大改。

### 优先级 2：宽表可空字段与专属字段语义治理

- 为什么排第二：
  - 当前最直接的实现风险就在 `EnergyData` 宽表和注册表 / schema 不一致。
  - 这是“对象没分层”在代码层最容易继续恶化的地方。
- 涉及模块：
  - `app/models/tables.py`
  - `app/domain/device_payloads.py`
  - `app/api/endpoints/devices/shared.py`
  - `app/api/endpoints/energy/shared.py`
- 本轮建议做到什么程度：
  - 先梳理“哪些字段是稳定字段、哪些字段其实只是类型声明但未被实现”。

### 优先级 3：点位 / 测点建模与扩展字段治理

- 为什么高于 analysis / reporting 再建设：
  - 因为没有点位层，analysis / reporting 只能继续围绕宽表猜语义。
  - 先补点位视角，后续指标扩展才有对象落点。
- 涉及模块：
  - `app/domain/device_payloads.py`
  - `app/integrations/mqtt/processor.py`
  - `app/api/endpoints/devices/shared.py`
  - `app/models/tables.py`
- 本轮建议做到什么程度：
  - 先由规范线程定义“点位对象是否作为新层引入”的最小方案，而不是直接开工重写接入链路。

### 优先级 4：多能源对象分层与对象关系治理

- 为什么第四：
  - 这是中期结构性问题，价值高，但改动会明显大于前三项。
  - 需要在对象边界和点位边界明确后再推进。
- 涉及模块：
  - `app/models/`
  - `app/services/`
  - `app/repositories/`
  - `app/application/`
- 本轮建议做到什么程度：
  - 先规划，不直接重构。

### 优先级 5：analysis / reporting / overview 层再建设

- 为什么最后：
  - 这些层现在的问题很多是“上游对象语义不足”的结果。
  - 现在就重做 analysis / reporting，容易把错误对象模型固化下来。
- 涉及模块：
  - `app/services/analysis_service.py`
  - `app/application/reporting.py`
  - `app/api/endpoints/energy/*`
  - `frontend/src/views/EnergyManagement.vue`
- 本轮建议做到什么程度：
  - 暂不作为第一批主线。

---

## 7. 本轮非目标

- 不展开告警模块。
- 不展开预测模块。
- 不展开设备控制模块。
- 不展开巡检模块。
- 不展开权限模块与认证模块。
- 不做前端通用 UI 重构。
- 不做数据库全量重构。
- 不做 LSTM 预测模块分析。
- 不做 MQTT 接入可靠性分析。
- 不展开碳排核算细则。
- 不展开费用结算细则。
- 不展开调度优化模块。
- 不在本轮直接设计或实现完整 meter / point 新模型。

---

## 8. 给规范线程的输入

### 建议计划标题

- `PLAN-20260328-device-object-layering-and-meter-point-governance.md`

### 建议范围

- 只聚焦：
  - 设备对象、计量对象、能源类型对象边界
  - 宽表专属字段语义清理
  - 点位对象是否引入以及如何最小落位
  - 前后端对象语义对齐
- 不扩展到：
  - 告警
  - 预测
  - 控制
  - 权限
  - 前端 UI 重构
  - 数据库全量重构

### 建议分阶段实施顺序

1. 先做术语和对象边界治理
- 明确什么叫设备对象、计量对象、能源类别对象、点位对象。

2. 再做现有模型与接口对齐
- 明确 `Device` / `EnergyData` 还能承载什么，哪些语义不应再继续往里塞。

3. 再做宽表和专属字段治理
- 梳理“已实现字段”“声明未实现字段”“仅展示字段”。

4. 再决定是否引入计量对象层和点位对象层
- 只做最小方案，不直接推翻现有表结构。

5. 最后才讨论 analysis / reporting / overview 如何迁移

### 建议验收标准

- 已形成明确的对象边界定义：
  - 设备对象
  - 计量对象
  - 能源类别对象
  - 点位对象
- 已列出现有 `Device` / `EnergyData` 中哪些字段继续保留，哪些属于未来不应继续膨胀的区域。
- 已列出注册表、schema、model、前端接口之间的已知不一致点。
- 已明确第一批实施边界，不把本轮扩成数据库全量重构。

### 建议控制的非目标

- 不直接引入完整 MyEMS 模型复刻。
- 不直接改全量历史数据结构。
- 不直接推动前端页面全面重做。
- 不把“对象分层治理”扩成“全项目重构”。

---

## 不一致点与不确定项

### 明确不一致点

- `docs/02-功能使用/统一设备管理指南.md` 声称“系统内置 11 种设备类型”，实际注册表只有 10 种。
- 用户指定的前端文件 `frontend/src/views/DeviceManagement.vue` 实际不存在，仓库中是 `frontend/src/views/DeviceManager.vue`。
- `device_registry` 中声明的部分可选字段，实际未被 `DeviceDataReportRequest`、`device_payloads` 和 `EnergyData` 承接。

### 不确定项

- 当前仓库中没有发现 MyEMS 项目本体或其实际表结构，因此本轮对 MyEMS 的对照仅基于你明确给出的分层特征，不对 MyEMS 的具体字段实现做额外脑补。
- `app/api/endpoints/campus.py` 中出现了 `energy_category` 表达，但它属于本轮范围外模块，本轮仅将其视为“范围外观察”，不把它当成当前系统已经具备独立能源类别对象层的证据。

### 范围外观察

- 巡检模块存在 `InspectionPoint`，说明仓库并非完全没有“点位”一词，但这套点位属于巡检业务，不是能源采集点位，不能混为本主题中的 point 对象层。

