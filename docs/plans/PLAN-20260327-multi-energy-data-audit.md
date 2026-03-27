# Multi Energy Data Audit

## 背景

当前项目已经具备“多能源统一接入、统一存储、统一查询、统一展示”的基础能力，但随着系统定位逐步从单一遥测平台转向园区 EMS，`电 / 热 / 气 / 冷 / 碳排放` 这五类对象的数据业务逻辑是否足够支撑正式业务判断，已经成为新的关键问题。

本次审计不做大规模实现，也不推翻现有底座，只回答一个核心问题：

- 当前多能源数据逻辑，到底更偏“能接入、能展示”，还是已经足够支撑严肃的多能源业务判断与核算。

本轮重点阅读和核对了以下内容：

- 协作与计划规范：`docs/guides/*`、`docs/plans/current-status.md`、`docs/plans/handoff.md`
- 业务文档：`README.md`、`docs/02-功能使用/多能源管理指南.md`、`docs/05-架构与设计/*`、`docs/关键功能链路说明.md`
- 后端代码：`app/models/tables.py`、`app/domain/energy_rules.py`、`app/domain/device_payloads.py`、`app/core/device_registry.py`
- 服务与查询：`app/services/energy_service.py`、`app/services/analysis_service.py`、`app/services/report_service.py`、`app/repositories/energy_repository.py`
- use case 与接口：`app/application/energy_management.py`、`app/application/analysis.py`、`app/application/reporting.py`、`app/api/endpoints/energy/*`、`app/api/endpoints/analysis.py`、`app/api/endpoints/reports.py`

---

## 结论摘要

- 当前系统已经具备多能源统一接入和统一展示能力，但业务语义整体仍偏薄，更接近“多能源数据展示平台 / 基础 EMS 底座”，而不是业务语义很强的多能源业务系统。
- 多能源建模目前主要依赖 `energy_type`、`device_type`、`device_category` 区分，核心时序模型仍围绕 `consumption` 和 `flow_rate` 这两个通用字段运转，见 `app/models/tables.py`、`app/core/device_registry.py`。
- 电、热、气、冷虽然有少量专属字段，但大多数统计、分析、报表逻辑并没有真正利用这些差异，更多只是“能存下来”，而不是“能按能源业务特性判断”。
- `consumption` 被定义为累计量，`flow_rate` 被定义为瞬时量，这个概念在模型和注释里存在，但在统计与汇总代码里没有被严格保护，累计量和瞬时量混用风险很高。
- 当前统计逻辑大量直接对 `consumption` 求和、求平均，这对累计表计型数据并不严谨，尤其不适合作为正式能耗核算口径，见 `app/domain/energy_rules.py` 和 `app/services/energy_service.py`。
- 单位体系已经有静态映射，但仍停留在“枚举到显示单位”的层面，尚未形成“内部标准单位 + 入库归一化 + 展示转换”的完整体系，见 `app/domain/energy_rules.py`、`app/api/endpoints/energy/shared.py`、`app/core/device_registry.py`。
- 碳排逻辑目前本质上是“按能源类型查一个固定因子，再乘 consumption”，未区分来源边界、地区因子、购电 / 自发电 / 外购冷热 / 天然气燃烧等核算口径，见 `app/domain/energy_rules.py`、`app/services/energy_service.py`。
- analysis / reporting 对多能源的理解仍然很浅。`analysis` 目前几乎只服务电力场景，`reports` 主要是通用明细导出和按 `energy_type` 分类，并没有形成热 / 冷 / 气 / 电各自业务指标体系。
- 文档里对多能源能力的描述明显偏“统一管理”和“自动计算”，但代码实际更适合驾驶舱展示与基础统计，不适合直接宣称可用于正式核算或精细业务判断。
- 第一批最值得补的不是前端页面，也不是全模型重构，而是：数据口径层、单位与标准化层、碳排核算层、能源专属语义层。

---

## 当前实现的问题清单

### 1. 多能源建模问题

#### 涉及文件

- `app/models/tables.py`
- `app/core/device_registry.py`
- `app/domain/device_payloads.py`
- `app/api/endpoints/energy/shared.py`

#### 当前做法

- 设备侧主要用 `device_type`、`device_category`、`energy_type` 区分能源对象。
- 时序主表 `EnergyData` 使用统一字段：
  - `consumption`
  - `flow_rate`
  - 少量按能源补充的可选字段，如 `voltage/current`、`pressure/temperature`、`supply_temp/return_temp/heat_flow`
- 上报链路会把不同设备的数据规范化成统一 payload，再落到统一模型。

#### 问题

- 建模更偏“统一接入”，不是“能源业务语义建模”。
- 电、热、气、冷缺少真正的领域对象和领域约束，仍是一个通用时序模型上的不同标签。
- 例如：
  - 电没有区分有功 / 无功 / 需量 / 尖峰功率 / 功率因数治理结果。
  - 气没有区分工况 / 标况、热值、压缩因子、计费口径。
  - 热没有区分供热 / 回热、热量积分口径、焓差、热网侧指标。
  - 冷没有区分冷量、冷机出力、COP、冷冻水侧口径。

#### 风险

- 后续业务判断只能依赖非常粗的通用字段，无法支撑精细 EMS 逻辑。
- 一旦要做正式报表、对账、成本归因、能效诊断，就会发现模型先天不足。

#### 影响范围

- 设备接入
- 能源数据入库
- 多能源统计
- 报表导出
- 前端多能源总览与分析页

---

### 2. 累计量 / 瞬时量口径问题

#### 涉及文件

- `app/models/tables.py`
- `app/services/energy_service.py`
- `app/repositories/energy_repository.py`
- `app/domain/energy_rules.py`
- `app/services/analysis_service.py`

#### 当前做法

- `EnergyData.consumption` 被注释定义为累计消耗量 / 表计读数。
- `EnergyData.flow_rate` 被注释定义为瞬时流量 / 瞬时功率。
- 但统计层直接：
  - 对 `consumption` 求和
  - 对 `consumption` 求平均
  - 对 `flow_rate` 求平均 / 峰值
- 单设备分析里通过“最新值 - 当日首值”计算日电量。

#### 问题

- 模型层和统计层对累计量的使用口径不一致。
- 如果 `consumption` 是累计表计值，`sum(consumption)` 通常没有业务意义。
- 当前同时存在两种思路：
  - analysis 路径按“差值”理解累计量
  - statistics / overview / carbon summary 路径按“直接汇总”理解累计量
- 这会让同一设备、同一时间段在不同接口里出现不同口径。

#### 风险

- 汇总统计偏大或失真。
- 报表导出可能混合“原始累计读数”和“期间能耗”的概念。
- 碳排计算如果直接使用累计读数而非期间增量，会进一步放大误差。

#### 影响范围

- `GET /energy/statistics`
- `GET /energy/overview`
- `GET /energy/carbon/summary`
- `GET /analysis/{device_id}`
- `GET /reports/export_csv`

---

### 3. 单位与换算问题

#### 涉及文件

- `app/domain/energy_rules.py`
- `app/core/device_registry.py`
- `app/api/endpoints/energy/shared.py`
- `app/models/tables.py`
- `docs/02-功能使用/多能源管理指南.md`

#### 当前做法

- 系统维护了一组静态单位映射：
  - electricity -> `kWh`
  - gas -> `m³`
  - heat -> `GJ`
  - cooling -> `kWh`
  - steam -> `t`
- 设备注册表中还维护了设备侧单位，如：
  - `water_meter` -> `m³/h`
  - `gas_meter` -> `m³/h`
  - `heat_meter` -> `GJ/h`
  - `cooling_meter` -> `kW`
- API 文档把这些单位直接暴露给展示层。

#### 问题

- 当前没有明确区分：
  - 入库原始单位
  - 内部标准单位
  - 前端展示单位
- “冷”相关口径存在明显不一致：
  - `energy_rules.py` 把 cooling 的能耗单位定义为 `kWh`
  - `device_registry.py` 把 cooling_meter 单位定义为 `kW`
  - `energy/shared.py` 把 cooling 的类型单位展示为 `kWh`
- 压力、温度等专属字段也没有统一标准单位约束，例如压力注释同时写 `MPa/kPa`。

#### 风险

- 不同接入源如果上报单位不一致，系统会静默混存。
- 多能源概览可能把不同量纲的累计值并列展示，造成“可看但不可用”。
- 冷 / 热 / 气在成本与碳排计算时可能出现隐性错口径。

#### 影响范围

- 设备接入规范
- 数据入库
- 聚合统计
- 报表导出
- 碳排放展示与试算

---

### 4. 碳排逻辑问题

#### 涉及文件

- `app/domain/energy_rules.py`
- `app/services/energy_service.py`
- `app/models/tables.py`
- `app/api/endpoints/energy/carbon.py`
- `docs/02-功能使用/多能源管理指南.md`

#### 当前做法

- 碳排放因子是按 `energy_type` 固定配置的常量。
- `build_carbon_fields()` 直接执行：
  - `carbon_emission = consumption * carbon_factor`
- `scope` 只按能源类型粗略分为 1 或 2。
- `EnergyService.save_energy_data()` 每次保存能耗时会自动同步写一条 `CarbonEmission`。
- 手工试算接口也直接复用相同逻辑。

#### 问题

- 这是典型的展示级碳排规则，不是正式核算规则。
- 未区分：
  - 购电 / 自发电 / 绿电
  - 天然气燃烧 / 蒸汽采购 / 外购热 / 外购冷
  - 区域排放因子 / 年度因子版本
  - 组织边界 / 核算边界 / 数据质量等级
- `scope` 逻辑过粗，甚至把 `heat` 直接归到 1 类排放，这对很多园区外购热场景并不可靠。
- 当前文档中对碳排功能的表述偏乐观，但代码实现仍然是固定因子乘法。

#### 风险

- 可以做驾驶舱趋势展示，但不应直接用于正式碳核算、审计或对外报送。
- 一旦业务方把当前接口当正式碳台账使用，后续会出现口径争议。

#### 影响范围

- `POST /energy/data`
- `GET /energy/carbon/emissions`
- `GET /energy/carbon/summary`
- `POST /energy/carbon/calculate`
- 报表导出中的碳排报表

---

### 5. analysis / reports 业务语义不足问题

#### 涉及文件

- `app/services/analysis_service.py`
- `app/application/analysis.py`
- `app/application/reporting.py`
- `app/services/report_service.py`
- `app/repositories/energy_repository.py`
- `app/api/endpoints/reports.py`

#### 当前做法

- analysis 目前主要围绕单设备：
  - 最新值
  - 今日能耗
  - 今日费用
- 报表主要提供：
  - energy detail 明细
  - alarm history
  - carbon emission
- 多能源 overview 主要提供：
  - 按 `energy_type` 的通用统计
  - 碳排汇总

#### 问题

- analysis 仍然是电力导向：
  - 返回字段直接是 `current_power`、`voltage`、`current`、`today_energy`、`today_cost`
  - 对热 / 气 / 冷没有各自的分析指标
- reporting 仍然是导出层，不是多能源业务报表层：
  - 没有热 / 冷 / 气 / 电各自的业务指标报表
  - 没有表计增量报表、成本归因报表、折标报表、等价碳报表
- `overview` 的统计指标全部是通用模板，没有体现能源特性。

#### 风险

- 系统容易被误认为“支持多能源业务分析”，但实际上主要是“支持多能源明细展示和粗统计”。
- 前端如果继续叠加可视化，会掩盖业务口径不足的问题。

#### 影响范围

- 单设备分析页
- 多能源管理页
- 报表页
- 园区驾驶舱的能源总览与碳排视图

---

## 分能源类型逐项分析

### 电

#### 当前系统如何存、算、展示

- 存储：
  - 设备类型主要包括 `load`、`solar`、`wind`、`storage`、`charger`
  - 主字段包括 `consumption`、`flow_rate`，以及 `voltage`、`current`、`power_factor`
- 计算：
  - analysis 支持日电量与日电费估算
  - 电价支持峰平谷时段
  - 碳排按固定电力因子乘以 consumption
- 展示：
  - analysis 返回 `current_power`、`voltage`、`current`、`today_energy`、`today_cost`
  - overview / reports 主要做明细和通用汇总

#### 缺少哪些关键业务语义

- 有功 / 无功 / 视在功率
- 需量、最大需量、尖峰负荷
- 电能质量指标
- 分时电量分摊
- 发电 / 用电 / 储能充放电方向性

#### 哪些判断逻辑过于简单

- 今日费用按“今日累计量差值 * 当前时段电价”估算，而不是按各时段分摊。
- 光伏 / 风电 / 储能仍沿用统一电量模型，没有形成单独业务语义。

#### 判断

- 电力是当前五类中最接近可用业务对象的一类，但仍属于“基础电能展示与估算”，还不是强语义电力 EMS。

---

### 热

#### 当前系统如何存、算、展示

- 存储：
  - `energy_type=heat`
  - `device_type=heat_meter`
  - 可选字段包括 `supply_temp`、`return_temp`、`heat_flow`
- 计算：
  - 统计仍走通用 `consumption / flow_rate`
  - 碳排按固定 heat 因子乘 consumption
- 展示：
  - overview 中仅按热力类型汇总
  - reports 仅按通用明细导出

#### 缺少哪些关键业务语义

- 供回水温差的业务意义
- 热量积分口径
- 热源类型区分（锅炉、外购热、热泵、余热）
- 热网运行效率指标

#### 哪些判断逻辑过于简单

- 虽然存了 `supply_temp` / `return_temp` / `heat_flow`，但分析和报表并未真正使用。
- `heat` 的成本与碳排仍然按固定单价和固定因子计算，没有区分来源。

#### 判断

- 热力数据目前更像“被纳入统一模型的扩展字段”，不是完整热力业务逻辑。

---

### 气

#### 当前系统如何存、算、展示

- 存储：
  - `energy_type=gas`
  - `device_type=gas_meter`
  - 可选字段主要是 `pressure`、`temperature`
- 计算：
  - 成本按固定单价
  - 碳排按固定因子
- 展示：
  - 作为 gas 类型参与 overview、report、carbon summary

#### 缺少哪些关键业务语义

- 标况 / 工况区分
- 热值折算
- 燃气来源区分
- 用气设备类型归因

#### 哪些判断逻辑过于简单

- 压力和温度只是存下来，没有参与折算与分析。
- m³ 直接参与成本与碳排计算，未考虑标准体积或热值换算。

#### 判断

- 燃气逻辑当前明显偏展示层，不适合直接作为正式用气核算与碳核算底座。

---

### 冷

#### 当前系统如何存、算、展示

- 存储：
  - `energy_type=cooling`
  - `device_type=cooling_meter`
  - 可选字段主要是 `supply_temp`、`return_temp`、`pressure`
- 计算：
  - 成本按固定单价
  - 碳排按固定 cooling 因子
- 展示：
  - 作为冷类型参与 overview、report、carbon summary

#### 缺少哪些关键业务语义

- 冷量与电耗的区别
- 冷站设备效率指标
- 外购冷 / 自产冷区分
- COP / EER / 冷冻水系统指标

#### 哪些判断逻辑过于简单

- cooling 的单位在不同层存在 `kW` / `kWh` 混用迹象。
- 系统未区分“冷量计量”和“制冷设备电耗”。

#### 判断

- 冷量逻辑是当前五类里语义最薄的几类之一，存在明显单位和业务含义混叠风险。

---

### 碳排放

#### 当前系统如何存、算、展示

- 存储：
  - 每条能耗记录同步写一条 `CarbonEmission`
  - 字段包括 `energy_type`、`energy_consumption`、`consumption_unit`、`carbon_factor`、`carbon_emission`、`scope`
- 计算：
  - 固定因子乘法
- 展示：
  - summary 汇总
  - emissions 列表
  - report 导出
  - 手动试算

#### 缺少哪些关键业务语义

- 因子版本管理
- 核算边界
- 数据质量标识
- 来源路径区分
- 折标煤 / 标准能耗 / 碳配额等扩展能力

#### 哪些判断逻辑过于简单

- 当前更接近“展示级碳指标”而不是“核算级碳台账”。
- 如果 `consumption` 本身口径不严，碳排结果会同步失真。

#### 判断

- 碳排放当前适合驾驶舱和趋势展示，不适合作为正式核算结论对外使用。

---

## 当前系统定位判断

### 判断结果

**B. 基础 EMS 平台底座**

### 原因

- 它已经明显强于单纯“多能源数据展示平台”，因为具备：
  - 统一多能源入库
  - 基础统计
  - 基础成本与碳排
  - 权限与报表接口
- 但它又还没到“具备较强业务语义的 EMS 系统”，因为：
  - 建模仍偏通用
  - 统计口径还不够严
  - 单位体系未彻底标准化
  - 碳排核算仍是展示级逻辑
  - 分能源业务分析尚未形成

更准确的说法是：

- 当前系统已经具备多能源 EMS 的底座能力；
- 但在 `电 / 热 / 气 / 冷 / 碳` 五类对象上，仍然偏“可采集、可展示、可粗统计”，还不够“可严肃判断、可正式核算”。

---

## 第一批最值得优化的方向

### 1. 优先级 P0：数据口径层

- 为什么先做：
  - 如果累计量和瞬时量口径不严，后面的成本、碳排、报表都会失真。
- 涉及模块：
  - `app/models/tables.py`
  - `app/services/energy_service.py`
  - `app/repositories/energy_repository.py`
  - `app/domain/energy_rules.py`
- 预期收益：
  - 明确哪些字段是累计量、哪些字段是瞬时量、哪些统计应做差值、哪些统计可直接汇总。
- 本轮建议做到什么程度：
  - 先由规范线程产出统一口径规范与实施计划，不立即全量改代码。

### 2. 优先级 P0：单位与标准化层

- 为什么先做：
  - 当前冷 / 热 / 气存在单位混用风险，不先统一标准单位，后续聚合都不稳。
- 涉及模块：
  - `app/domain/energy_rules.py`
  - `app/core/device_registry.py`
  - `app/api/endpoints/energy/shared.py`
  - 上报链路与文档
- 预期收益：
  - 建立“内部标准单位 + 展示单位 + 接入换算”的基础规则。
- 本轮建议做到什么程度：
  - 先确定标准单位体系和不兼容项清单。

### 3. 优先级 P1：碳排核算层

- 为什么先做：
  - 当前碳排是最容易被误用为正式结果的模块，但实际最需要先补边界说明和核算层级。
- 涉及模块：
  - `app/domain/energy_rules.py`
  - `app/services/energy_service.py`
  - `app/models/tables.py`
  - `app/api/endpoints/energy/carbon.py`
- 预期收益：
  - 把“展示级碳排”与“核算级碳排”边界拉清。
  - 为后续购电 / 燃气 / 外购冷热来源区分打基础。
- 本轮建议做到什么程度：
  - 先出分层方案，不直接做复杂核算引擎。

### 4. 优先级 P1：多能源语义层

- 为什么先做：
  - 热 / 气 / 冷现在只是挂在统一模型上的类型值，缺少业务意义。
- 涉及模块：
  - `app/core/device_registry.py`
  - `app/domain/device_payloads.py`
  - `app/models/tables.py`
  - `analysis / reports / overview` 相关 use case
- 预期收益：
  - 让不同能源开始具备可扩展的专属指标，而不是始终只走通用字段。
- 本轮建议做到什么程度：
  - 先定义每类能源最小必备业务语义，不做全模型重构。

### 5. 优先级 P2：指标与分析层

- 为什么先做：
  - 当前 analysis / reports 还没有真正理解多能源业务，后补会很容易沦为只是更多图表。
- 涉及模块：
  - `app/services/analysis_service.py`
  - `app/application/analysis.py`
  - `app/application/reporting.py`
  - `app/services/report_service.py`
- 预期收益：
  - 形成分能源分析指标体系，为前端联调提供稳定业务口径。
- 本轮建议做到什么程度：
  - 等口径层和单位层明确后再推进。

---

## 本轮非目标

- 不展开告警逻辑审计。
- 不展开预测模型审计。
- 不展开设备控制逻辑。
- 不做前端页面改版。
- 不做全项目数据模型重构。
- 不在本轮直接重写 `EnergyData` / `CarbonEmission` 表结构。
- 不在本轮直接设计完整碳核算标准体系。
- 不顺手把多能源问题扩张成全仓库分层重构。

---

## 给规范线程的输入

### 建议计划标题

- `docs/plans/PLAN-20260327-multi-energy-semantics-and-metering-governance.md`

### 建议范围

- 第一阶段只聚焦：
  - 多能源计量口径
  - 单位标准化
  - 碳排逻辑分层
  - 分能源最小业务语义
- 不扩展到：
  - 告警
  - 预测
  - 设备控制
  - 前端大改版
  - 数据库大重构

### 建议分阶段实施顺序

1. 先定计量口径
- 明确累计量、瞬时量、差值量、统计量的定义和禁止混用场景。

2. 再定单位体系
- 明确每类能源的内部标准单位、前端展示单位、接入换算规则。

3. 再拆碳排逻辑层级
- 先把“展示级碳排”和“核算级碳排”边界明确。

4. 再补多能源语义层
- 明确电 / 热 / 气 / 冷各自最小必备业务字段与分析指标。

5. 最后再推进 analysis / reports
- 在口径明确后补专属指标与报表，而不是先堆图表。

### 建议验收标准

- 已形成明确的累计量 / 瞬时量口径规范，并映射到现有接口与字段。
- 已形成电 / 热 / 气 / 冷的标准单位表和展示单位规则。
- 已明确当前碳排逻辑的适用范围，并区分展示级与核算级实现边界。
- 已给出每类能源最小必备业务语义清单。
- 已锁定第一批实施范围，不扩散到前端改版、预测、告警和全模型重构。

### 建议控制的非目标

- 不把这轮工作做成“全面重写 EnergyData”。
- 不在第一阶段直接引入复杂行业核算标准。
- 不在单位和口径未统一前就推进前端大面积改造。

---

## 不确定项

- 当前仓库中没有看到独立的 `carbon_service.py`。碳排逻辑主要落在 `app/domain/energy_rules.py` 和 `app/services/energy_service.py`，这意味着碳排现在仍是能源服务附属逻辑，而不是独立核算域。
- 文档中部分历史描述仍提到旧表或旧链路，例如 `docs/05-架构与设计/DeviceData与EnergyData表说明.md` 和 `docs/关键功能链路说明.md`，本轮仅将其作为辅助参考，不把其中的旧实现表述当作当前事实依据。

