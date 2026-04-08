# PLAN-20260408-多能源管理页面数据收敛专题

> 状态：已阶段收口，暂不迁 archive，等待下一个主主题 | 负责人：规范 / 前端 / 验收线程 | 更新时间：2026-04-08

---

## 背景

当前 [EnergyManagement.vue](/Users/todo/CampusEnergySystem/frontend/src/views/EnergyManagement.vue) 已接入多能源总览接口，但页面展示方向已出现偏差：

- 页面主视图开始趋近“接口说明页”
- 语义说明、字段边界、对象边界和碳汇总元信息占据了主展示位
- “消耗趋势图”仍使用静态样例数据，却继续占据核心展示位
- 当前代码层虽然支持 `steam`，但当前运行态并不存在真实 `steam` 设备、能耗记录或碳排记录

同时，当前主区仍停留在 `前后端联调断链排查专题`，与“多能源管理页数据补全”不是同一主题，必须独立立项。

---

## 目标

- 将多能源管理页主视图收回到“园区多能源核心运行态展示”
- 优先展示多能源总览、占比、碳排和设备维度入口
- 将字段口径、语义说明和元信息从主展示位降级
- 将 `steam` 的默认展示规则收回到“运行态存在时才显示”

## 非目标

- 不重做多能源页面整体视觉布局
- 不扩张为驾驶舱、园区总览、设备页的并行改造
- 不顺手重构能源接口体系
- 不修改数据库、MQTT、监控或运行时契约
- 不把页面继续做成“接口说明页”
- 不因为代码层支持就默认展示当前运行态不存在的能源类型

## 范围

涉及目录或模块：

- `frontend/src/views/EnergyManagement.vue`
- `frontend/src/api/energy.ts`
- `frontend/src/api/device.ts`
- `app/api/endpoints/energy/data.py`
- `app/api/endpoints/energy/shared.py`
- `app/services/energy_service.py`
- `docs/plans/current-status.md`
- `docs/plans/handoff.md`

明确不改动：

- `frontend/src/views/Dashboard.vue`
- `frontend/src/views/CampusScene.vue`
- `frontend/src/views/DeviceManager.vue`
- 运行时编排与 Docker 入口
- 数据库 / MQTT / 监控相关契约

## 当前边界判断

已确认当前主视图应优先服务“园区多能源核心运行态”，而不是“尽量展示后端所有已返回字段”。

主展示应优先保留：

1. 多能源总览卡片
- 各能源类型的核心统计值
- 当前可见范围下的运行态聚合信息

2. 多能源占比
- 能源类型占比
- 与当前总览直接相关的聚合结果

3. 碳排统计
- `carbon_summary.total_carbon`
- `carbon_summary.by_energy_type`

4. 设备维度明细入口
- 继续保留设备维度 drill-down / 明细入口

应降级到次级层或移除主展示位：

- `overview_boundary`
- `unit_rule`
- `cross_energy_mix_allowed`
- `field_boundary_rule`
- `device_object_boundary`
- `consumption_semantics / flow_semantics`
- `supported_device_types`
- `public_fields / specialized_fields`
- `carbon_summary.boundary / calculation_method / summary_basis`
- 对象类型 / 点位类型 / 公共字段 / 专属字段等接口说明式内容

关于趋势图：

- 当前“消耗趋势图”仍使用静态样例数据
- 若没有真实时序数据支撑，不应继续占据核心展示位
- 默认方向应为：降级隐藏或移出主展示区，而不是继续保留占位样例图

关于 `steam`：

- 当前代码层支持 `steam`
- 但当前开发运行环境中：
  - `steam` 设备实例数为 0
  - `energydata` 中 `steam` 记录数为 0
  - `carbon_emission` 中 `steam` 记录数为 0
- 结论：`steam` 当前不应继续作为默认展示能源之一
- 默认规则应改为：只有存在真实设备或真实统计数据时才展示

## 实施步骤

1. 规范线程先重锁页面展示边界，禁止继续按“接口说明页”扩张。
2. 前端线程执行收回式改造：
  - 保留核心运行态展示
  - 降级或移除过重的口径说明区块
  - 处理静态样例趋势图
  - 将 `steam` 改为“运行态存在时显示”
3. 若前端证明现有接口无法支持“运行态存在时显示”的判断，再最小引入后端线程。
4. 验收线程判断本专题是否达到阶段完成。

## 风险与回滚

- 风险：前端顺手把本轮扩成页面重构
  - 应对：只做收回式改造，不重写整体布局
- 风险：把多能源页问题扩到 Dashboard / CampusScene / DeviceManager
  - 应对：本轮只允许锁定 `EnergyManagement.vue` 单页
- 风险：后端被顺手拉入接口重构
  - 应对：默认先走前端；只有当前端证明确有缺字段时才引入后端
- 风险：`steam` 因代码层支持而被继续默认展示
  - 应对：明确改为“运行态存在时显示”

## 验收标准

- [ ] 多能源页主视图已回到“园区多能源核心运行态展示”
- [ ] 多能源总览卡片、多能源占比、碳排统计、设备维度明细入口仍保留
- [ ] 语义说明、字段边界、对象边界、碳汇总元信息已降级到次级层或移出主展示位
- [ ] 静态样例趋势图不再继续占据核心展示位
- [ ] `steam` 已改为“仅在存在真实设备或真实统计数据时显示”
- [ ] 本轮未扩张为页面重构、跨页联动改造或接口重构
- [ ] 若引入后端改动，已明确说明最小新增字段与前端依赖关系

## 进度记录

- 2026-04-08：探索完成，已确认当前问题不是“前后端断链”，而是 `EnergyManagement.vue` 仅消费了后端聚合返回的一小部分字段；正式立项为“多能源管理页面数据收敛专题”。
- 2026-04-08：基于最新探索结论，已将页面目标从“尽量展示后端所有已返回字段”收回到“优先展示园区多能源核心运行态”，并明确 `steam` 仅在运行态存在时显示。
- 2026-04-08：前端收回式改造已验收通过；已确认主视图回到园区多能源核心运行态展示，静态趋势图退出主展示位，`steam` 改为仅运行态存在时显示，本轮未越界到多页改造、后端接口或运行时契约修改。
- 2026-04-08：规范线程已确认当前主题达到阶段收口条件；当前不再继续默认启用后续轮次，退出主区，暂不迁 archive，继续保留在 `docs/plans/` 作为近期成果主题。

## 阶段收口结论

- 当前主题已达到阶段收口条件。
- 当前不建议继续默认启用后续轮次。
- 当前主题应退出主区。
- 当前主题暂不迁 archive。
- 当前主题继续保留在 `docs/plans/` 作为近期成果主题。
- 主区下一步应改为：`等待下一个主主题`。

## 相关文档

- [AGENTS.md](/Users/todo/CampusEnergySystem/AGENTS.md)
- [Current Status](/Users/todo/CampusEnergySystem/docs/plans/current-status.md)
- [Handoff](/Users/todo/CampusEnergySystem/docs/plans/handoff.md)
- [Frontend Guidelines](/Users/todo/CampusEnergySystem/docs/guides/frontend-guidelines.md)
- [Backend Guidelines](/Users/todo/CampusEnergySystem/docs/guides/backend-guidelines.md)
