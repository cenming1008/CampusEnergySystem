# Handoff

## 规范 -> 后端
### 任务
- 按 [PLAN-20260327-multi-energy-data-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-multi-energy-data-optimization.md) 实施第一批多能源数据业务优化
- 本轮只允许优先处理电 / 热 / 气 / 冷 / 碳排放在口径、单位、碳排边界和 `analysis` / `reports` 第一批收敛上的问题

### 已知信息
- 允许修改目录：
  - `docs/plans/*`
  - `docs/05-架构与设计/*`
  - `app/models/*`
  - `app/services/energy_service.py`
  - `app/services/analysis_service.py`
  - `app/services/report_service.py`
  - `app/application/*`
  - `app/api/endpoints/energy*`
  - `app/api/endpoints/reports*`
  - `app/api/endpoints/analysis*`
  - 与上述内容直接相关的 schemas / DTO / tests
- 探索线程已确认的问题：
  - 当前多能源建模仍偏 `energy_type + consumption / flow_rate` 的通用模型，能源专属业务语义不足
  - `consumption` / `flow_rate` 的累计量与瞬时量口径存在混用风险
  - 单位体系尚未形成“内部标准单位 + 入库换算 + 展示单位”三层规则
  - 碳排逻辑当前更适合展示级，不适合作为正式核算结论
  - `analysis` / `reports` 仍偏通用分类和明细导出，尚未形成第一批多能源业务指标

### 建议处理方式
- 后端第一批优先顺序：
  - 先处理累计量 / 瞬时量 / 差值量 / 统计量口径
  - 再处理单位标准化与展示单位约束
  - 再明确碳排展示级与核算级边界
  - 最后处理 `analysis` / `reports` 的第一批多能源业务口径
- 兼容原则：
  - 不做接口路径大规模重命名
  - 不做数据库 schema 大爆炸式改造
  - 若现有模型不足以一次补齐，优先保留兼容层和边界说明
  - 若返回字段需要变化，必须先写回本文件并说明影响范围
- 验证要求：
  - 验证电 / 热 / 气 / 冷 / 碳排放第一批业务口径已明确
  - 验证累计量 / 瞬时量口径已在代码和文档中可对应
  - 验证单位与换算策略已形成统一约束
  - 验证碳排逻辑已明确当前适用边界
  - 验证 `analysis` / `reports` 第一批不再仅依赖粗粒度 `energy_type` 汇总
- 明确禁止：
  - 不做告警逻辑重构
  - 不做预测模型重构
  - 不做设备控制链路重构
  - 不做前端页面大改版
  - 不做全项目数据模型推翻式重写
  - 不一次性补齐所有能源机理模型
  - 不做全局报表系统重构
  - 不做数据库 schema 的大爆炸式改造
  - 不处理本轮主线之外的顺手优化

---

## 规范 -> 前端
### 任务
- 为第一批多能源数据业务优化做联调准备
- 本轮只围绕多能源口径和返回结构做最小适配，不做页面大重构

### 已知信息
- 本轮重点接口和输出层主要集中在：
  - `app/api/endpoints/energy*`
  - `app/api/endpoints/analysis*`
  - `app/api/endpoints/reports*`
- 字段原则：
  - 与累计量 / 瞬时量相关的字段语义原则上不要轻易改名
  - 单位字段、展示单位、碳排相关字段若变化，必须提前说明
  - `analysis` / `reports` 若增加分能源口径字段，应优先走兼容新增，而不是直接删改旧字段

### 建议处理方式
- 前端本轮重点关注：
  - 多能源口径是否更清晰
  - 返回字段是否仍可兼容现有展示
  - 单位展示是否需要做最小适配
  - 报表与分析页是否需要按新口径做文案或字段映射微调
- 前端本轮不要做：
  - 页面大改版
  - 状态管理重构
  - 因猜测字段变化而提前重写多能源页面
- 若联调发现以下情况，必须先回写 handoff 再动代码：
  - 返回字段删除或重命名
  - 累计量 / 瞬时量含义变化
  - 单位或量纲变化
  - 碳排字段边界变化
  - 异常语义变化
  - CSV 结构变化
  - 原有路径不兼容

---

## 前端 -> 后端
### 当前建议
- 前端本轮已完成多能源相关调用链审计，当前高优先级联调点如下：
  - `GET /energy/types`
    - 受影响模块：`frontend/src/api/energy.ts`、`frontend/src/views/EnergyManagement.vue`
    - 当前强依赖字段：`energy_types[*].value`、`label`、`unit`
    - 新增建议保持稳定字段：`flow_unit`、`consumption_semantics`、`flow_semantics`、`carbon_scope`
    - 联调提醒：这些新增语义字段当前主要用于前端兼容理解与后续展示约束，若改名或删除必须提前通知
  - `GET /energy/statistics`
    - 受影响模块：`frontend/src/api/energy.ts`、`frontend/src/features/dashboard/composables/useDashboardEnergyStats.ts`、`frontend/src/views/Dashboard.vue`
    - 当前强依赖字段：`total_consumption`、`avg_flow_rate`、`peak_flow_rate`、`data_count`
    - 新增建议保持稳定字段：`consumption_unit`、`flow_unit`、`consumption_semantics`、`consumption_stat_basis`、`flow_semantics`、`flow_stat_basis`、`meter_reset_suspected`
    - 隐式假设：`Dashboard.vue` 仍把多种能源的 `total_consumption` 聚合成单一“总能耗”值，若单位或口径再次变化会直接影响首页卡片含义
  - `GET /energy/overview`
    - 受影响模块：`frontend/src/api/energy.ts`、`frontend/src/views/EnergyManagement.vue`
    - 当前强依赖字段：`statistics`、`carbon_summary`
    - 新增建议保持稳定字段：`overview_boundary`、`unit_rule`、`cross_energy_mix_allowed`
    - 联调提醒：`EnergyManagement.vue` 当前仍直接用 `statistics[*].total_consumption` 做跨能源对比；若后端明确 `cross_energy_mix_allowed=false`，后续前端会据此限制混合展示
  - `GET /energy/carbon/summary`
    - 受影响模块：`frontend/src/api/energy.ts`、`frontend/src/views/EnergyManagement.vue`
    - 当前强依赖字段：`total_carbon`、`by_energy_type[*].carbon_emission`、`by_energy_type[*].energy_consumption`、`by_energy_type[*].unit`
    - 新增建议保持稳定字段：`boundary`、`calculation_method`、`is_accounting_grade`、`note`、`summary_basis`
    - 联调提醒：前端当前把这组数据用于驾驶舱/多能源展示，不应把它误导成正式核算；若边界文案或布尔语义变化必须提前通知
  - `GET /analysis/{device_id}`
    - 受影响模块：`frontend/src/api/telemetry.ts`、`frontend/src/features/dashboard/composables/useDashboardRealtime.ts`、`frontend/src/views/CampusScene.vue`
    - 当前兼容依赖字段：`device_id`、`is_active`、`current_power`、`voltage`、`current`、`today_energy`、`today_cost`
    - 当前新增依赖字段：`energy_type`、`energy_label`、`current_value`、`current_value_label`、`current_value_unit`、`today_consumption`、`today_consumption_unit`、`today_consumption_semantics`、`electrical_fields_applicable`
    - 联调提醒：旧兼容字段当前仍被页面直接消费；如果其空值语义、数值精度或适用范围变化，前端会直接受影响
  - `GET /reports/export_csv`
    - 受影响模块：`frontend/src/api/report.ts`、`frontend/src/views/Report.vue`
    - 当前已接入报表类型：`energy_detail`、`alarm_history`、`carbon_emission`、`multi_energy_summary`
    - 当前依赖行为：返回 200 + blob 下载流；路径与主要查询参数保持不变；默认文件名规则仍按 `{report_type}_{YYYYMMDD}.csv` 兜底
    - 联调提醒：`multi_energy_summary` 的列顺序、列头命名、单位列和碳排边界说明若变化，必须提前同步前端
- 前端已识别的高风险页面：
  - `frontend/src/views/Dashboard.vue`
    - 仍将多能源 `total_consumption` 混算成单一“今日总能耗 / 本月总能耗”
  - `frontend/src/views/EnergyManagement.vue`
    - 仍直接将分能源统计与碳排汇总拼成统一图表，尚未依据 `cross_energy_mix_allowed` / `is_accounting_grade` 做展示约束
  - `frontend/src/views/CampusScene.vue`
    - 仍主要依赖 `analysis` 的电力兼容字段推导状态
- 前端建议的最小兼容方式：
  - 多能源第一批新增字段优先通过“兼容新增”提供，不直接删改旧字段
  - `analysis` 继续保留旧兼容字段，同时稳定提供新增语义字段，便于前端分阶段切换
  - `reports/export_csv` 继续保持 blob 下载模式；`multi_energy_summary` 如需扩列，请追加列而不是重排已有核心列
  - 若后端后续要彻底禁止跨能源混算，优先通过 `cross_energy_mix_allowed`、`unit_rule` 等边界字段表达，不要让前端靠猜测判断

## 前端 -> 规范
### 当前建议
- 本轮前端审计已确认，当前最大的联调风险不是“拿不到字段”，而是“旧页面可能继续按旧业务口径解释新字段”。
- 若规范线程后续继续补文档，建议优先补两类展示级约束说明：
  - “跨能源混合展示”在什么条件下允许，哪些页面必须按分能源拆开显示
  - “展示级碳排”与“核算级碳排”在前端文案上的最小区分要求
- 这部分目前还不需要扩成新的大规范，只要能让前后端在 `cross_energy_mix_allowed`、`is_accounting_grade`、`boundary` 的解释上保持一致即可

---

## 后端 -> 前端
### 当前建议
- 本轮已完成第一批多能源后端收敛的接口：
  - `GET /energy/statistics`
  - `GET /energy/overview`
  - `GET /energy/types`
  - `GET /energy/carbon/summary`
  - `GET /energy/carbon/factors`
  - `GET /analysis/{device_id}`
  - `GET /reports/export_csv`
- 已收敛的多能源口径：
  - `consumption` 继续表示累计量 / 累计表计读数，不再在统计汇总里直接求和
  - `flow_rate` 继续表示瞬时量，统计口径固定为均值 / 峰值，不与累计量混算
  - `/energy/statistics`、`/energy/overview` 的 `total_consumption` 现在表示“时段首末差值”
  - `/energy/carbon/summary` 现在表示“基于时段消耗差值 * 固定因子”的展示级估算，不是正式碳核算
- 对前端保持兼容的内容：
  - 请求参数未改
  - `GET /analysis/{device_id}` 仍保留 `device_id`、`is_active`、`current_power`、`voltage`、`current`、`today_energy`、`today_cost`
  - `GET /reports/export_csv` 仍返回 200 + CSV 流，原有 `energy_detail` / `alarm_history` / `carbon_emission` 仍可用
  - 原有接口路径没有重命名
- 本轮兼容新增字段：
  - `/analysis/{device_id}` 新增 `energy_type`、`energy_label`、`current_value`、`current_value_label`、`current_value_unit`、`today_consumption`、`today_consumption_unit`、`today_consumption_semantics`、`electrical_fields_applicable`
  - `/energy/statistics` 新增 `consumption_unit`、`flow_unit`、`consumption_semantics`、`consumption_stat_basis`、`flow_semantics`、`flow_stat_basis`、`meter_reset_suspected`
  - `/energy/overview` 新增 `overview_boundary`、`unit_rule`、`cross_energy_mix_allowed`
  - `/energy/carbon/summary` 新增 `boundary`、`calculation_method`、`is_accounting_grade`、`note`、`summary_basis`
  - `/energy/types` 新增每类能源的 `flow_unit`、`consumption_semantics`、`flow_semantics`、`carbon_scope` 等语义字段
- 新增报表类型：
  - `GET /reports/export_csv?report_type=multi_energy_summary&start_time=...&end_time=...`
  - 返回按能源类型汇总的周期消耗、瞬时统计和展示级碳排估算
  - 前端当前若没有入口，可先不接；如要接，只需按现有 blob 下载逻辑接入
- 前端联调注意：
  - 若页面以前把 `total_consumption` 理解成“累计值求和”，现在需要改成“周期消耗”
  - `today_energy` 在非电力设备上仍保留兼容，但语义应按新增字段 `today_consumption_unit` / `energy_type` 理解
  - 非电力设备的 `voltage` / `current` 继续保留兼容字段，是否适用请以 `electrical_fields_applicable` 为准
  - 若页面要展示碳排，请优先使用 `/energy/carbon/summary` 的新增边界字段，不要把结果当正式核算值
- 当前仍未解决的风险：
  - 接入侧异构单位自动换算还没做
  - 历史 `carbon_emission` 明细没有做回填重算
  - 更细粒度的热 / 冷 / 气专属业务指标还未补齐

## 后端 -> 规范
### 当前建议
- 本轮已按 [PLAN-20260327-multi-energy-data-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-multi-energy-data-optimization.md) 的既定边界实施，无需新增一套规范。
- 已落实的规范口径：
  - 累计量统计口径：首末差值
  - 瞬时量统计口径：均值 / 峰值
  - 单位策略：先锁定内部标准单位与展示单位说明，不做本轮接入换算重构
  - 碳排策略：展示级估算，非正式核算
- 建议规范线程后续只补“接入换算规则”和“展示级碳排 / 核算级碳排分层说明”，不要把本轮结果误解成需要立即推进数据库或接口大重构。

---

## 验收 -> 全局
### 验收结论
- 本轮“电 / 热 / 气 / 冷 / 碳排放数据业务优化”在实现层面已基本完成第一批目标：
  - 探索线程已形成审计文档并沉淀到 [PLAN-20260327-multi-energy-data-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-multi-energy-data-audit.md)
  - 规范线程已形成正式实施计划并把后端 / 前端边界写入交接文档
  - 后端线程已完成第一批口径、单位、碳排边界、`analysis` / `reports` 收敛，并提供测试验证
  - 前端线程已完成依赖审计、API 层最小适配和 `multi_energy_summary` 导出入口接入
- 但本轮暂不建议标记为“正式收口”。

### 暂不收口的原因
- 当前最大的缺口是文档闭环而不是主功能实现：
  - [PLAN-20260327-multi-energy-data-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-multi-energy-data-optimization.md) 仍显示“未开始”，进度记录未同步后端实施、前端最小适配和验收执行结果。
  - 这使得正式 PLAN、`current-status.md`、`handoff.md`、实际代码状态之间仍存在一处关键不一致。
- 前端页面层仍保留已知风险：
  - [frontend/src/views/Dashboard.vue](/Users/todo/MineEnergySystem/frontend/src/views/Dashboard.vue) 与 [frontend/src/features/dashboard/composables/useDashboardEnergyStats.ts](/Users/todo/MineEnergySystem/frontend/src/features/dashboard/composables/useDashboardEnergyStats.ts) 仍有跨能源 `total_consumption` 混算。
  - [frontend/src/views/EnergyManagement.vue](/Users/todo/MineEnergySystem/frontend/src/views/EnergyManagement.vue) 尚未基于 `cross_energy_mix_allowed`、`is_accounting_grade` 做展示级边界约束。
  - 上述页面风险已被识别并记录，当前属于“待真实联调后再决定是否最小微调”的剩余风险，不要求本轮继续扩大实现。

### 线程完成情况
- 探索线程：已完成。本轮多能源建模、累计量 / 瞬时量、单位与换算、碳排边界、`analysis` / `reports` 语义问题均已文档化。
- 规范线程：部分完成。正式 PLAN 已建立并约束了范围，但尚未把 PLAN 状态与进度记录更新到实际完成状态。
- 后端线程：已完成。第一批实现已落地，验证结果存在，范围未扩张到告警 / 预测 / 控制 / 数据库重构。
- 前端线程：已完成本轮范围内任务。已完成联调准备与最小适配，但未承诺完成页面级全面口径调整。

### 下一步交接建议
- 第一优先级交回规范线程：
  - 补齐 [PLAN-20260327-multi-energy-data-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-multi-energy-data-optimization.md) 的状态、进度记录和验收结果，使计划文档与现状一致。
- 第二优先级视真实联调结果决定是否交回前端线程：
  - 若真实联调确认首页和多能源页需要显式消费边界字段，再按最小修改原则处理展示层。
- 当前不建议交回后端线程继续追加主功能；后端第一批范围已经达到计划要求。

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
