# PLAN-20260408-多能源管理中心展示重构专题

> 状态：已阶段收口，暂不迁 archive，等待下一个主主题 | 负责人：规范 / 前端 / 验收线程 | 更新时间：2026-04-08

---

## 背景

`多能源管理页面数据收敛专题` 已完成“字段展示页 -> 运行态主视图”的第一轮收回式改造，并已阶段收口。

基于最新探索结论，当前 `EnergyManagement.vue` 的主要问题已经不再是“前端漏展示字段”，而是：

- 页面整体仍然更像工具页或字段展示页
- 与 [Dashboard.vue](/Users/todo/CampusEnergySystem/frontend/src/views/Dashboard.vue) 相比，驾驶舱主视图感仍偏弱
- 强头部、强总览指标、强主图表、强运行态的故事线尚未真正建立
- 次级说明块、操作区和明细入口的主视觉权重仍偏重

因此需要正式新开主题，将多能源页目标切换为：

- 参考首页风格的园区多能源驾驶舱式主视图
- 但仍保持单页、局部、最小可控重构

---

## 目标

- 将 [EnergyManagement.vue](/Users/todo/CampusEnergySystem/frontend/src/views/EnergyManagement.vue) 收敛为“多能源管理中心”式主视图
- 参考首页驾驶舱的组织方式，强化：
  - 强头部
  - 强总览指标
  - 强主图表
  - 强运行态
  - 弱说明文
- 在不改后端接口的前提下，重组现有前端信息层级与视觉主次
- 继续保持 `steam` 为“仅运行态存在时显示”

## 非目标

- 不回到“补更多字段说明”的方向
- 不新增后端聚合能力
- 不修改 [Dashboard.vue](/Users/todo/CampusEnergySystem/frontend/src/views/Dashboard.vue)
- 不修改 [CampusScene.vue](/Users/todo/CampusEnergySystem/frontend/src/views/CampusScene.vue)
- 不修改 `DeviceManager.vue`
- 不做多页联动重构
- 不修改数据库、MQTT、监控或其他运行时契约

## 最小可控范围

涉及目录或模块：

- [EnergyManagement.vue](/Users/todo/CampusEnergySystem/frontend/src/views/EnergyManagement.vue)
- [energy.ts](/Users/todo/CampusEnergySystem/frontend/src/api/energy.ts)
- [device.ts](/Users/todo/CampusEnergySystem/frontend/src/api/device.ts)
- [current-status.md](/Users/todo/CampusEnergySystem/docs/plans/current-status.md)
- [handoff.md](/Users/todo/CampusEnergySystem/docs/plans/handoff.md)

默认不改动：

- [Dashboard.vue](/Users/todo/CampusEnergySystem/frontend/src/views/Dashboard.vue)
- [data.py](/Users/todo/CampusEnergySystem/app/api/endpoints/energy/data.py)
- [energy_service.py](/Users/todo/CampusEnergySystem/app/services/energy_service.py)
- 其他页面、后端接口与运行时契约

## 主视图区必须保留

主展示必须围绕以下内容重组：

1. 强头部
- 页面主标题
- 园区多能源当前态摘要
- 当前时间范围 / 位置范围等最少必要上下文

2. 强总览指标
- 多能源总览核心指标
- 多能源结构 / 占比
- 碳排核心统计

3. 强主图表
- 页面中央必须形成真正的主图中心
- 图表需要承接“园区多能源运行态”主故事线，而不是字段说明

4. 强运行态
- 当前能源焦点
- 活跃能源类型
- 当前设备 / 能源主焦点

5. 次级设备入口
- 设备维度 drill-down / 明细入口继续保留
- 但不占主视觉中心

## 必须降级到次级层或详情层

- 规则说明
- 字段说明
- 对象类型 / 点位类型 / 公共字段 / 专属字段说明
- 碳排试算
- 原始明细表的主视觉权重
- 其他接近接口说明页的元信息块
- 大段解释性文字

## `steam` 展示规则

- `steam` 继续固定为：仅运行态存在时显示
- 不因代码层支持而默认展示
- 若未来显示规则需要变化，应另行判断是否需要后端聚合能力，而不是在本主题内顺手扩张

## 冻结边界

- 不新增后端聚合能力
- 不修改后端接口结构
- 不修改 [Dashboard.vue](/Users/todo/CampusEnergySystem/frontend/src/views/Dashboard.vue) 以追求风格统一
- 不修改 [CampusScene.vue](/Users/todo/CampusEnergySystem/frontend/src/views/CampusScene.vue) 或 `DeviceManager.vue`
- 不扩张为多页视觉重构
- 不回到“补更多字段 / 元信息展示”的方向
- 不修改运行时命名、数据库、MQTT、监控或其他契约

## 回滚边界

- 若本轮重构导致页面主线更弱、信息层级更乱或可用性下降，应整轮回退到当前已验收通过的“收回式改造”稳定状态
- 若前端实现过程中发现必须新增后端聚合能力才能成立，应停止该项并从本轮剥离，不得顺手拉起后端改造
- 若实现尝试开始波及 `Dashboard.vue`、`CampusScene.vue` 或其他页面，应立即回退到单页范围

## 验收标准

- [ ] 页面主视图已从“字段展示页 / 工具页感”收敛为“多能源管理中心”式驾驶舱主视图
- [ ] 主展示已形成清晰的强头部、强总览指标、强主图表、强运行态故事线
- [ ] 总览指标、多能源结构、当前能源焦点、次级设备入口仍完整保留
- [ ] 规则说明、字段说明、碳排试算、原始明细表已降级到次级层或详情层
- [ ] 未新增后端聚合能力，默认未引入后端线程
- [ ] `steam` 继续保持“仅运行态存在时显示”
- [ ] 本轮未越界到跨页重构、接口改造或运行时契约修改

## 推荐路径

- `规范 -> 前端 -> 验收`

## 进度记录

- 2026-04-08：已确认这是新主题，不属于已阶段收口的 `多能源管理页面数据收敛专题` 后续轮次。
- 2026-04-08：已正式立项为 `多能源管理中心展示重构专题`，范围锁定为 `EnergyManagement.vue` 单页局部重构，默认不引入后端线程。
- 2026-04-08：前端单页局部重构已验收通过；已确认页面形成强头部、强总览指标、强主图中心、当前能源焦点、次级设备入口的驾驶舱层级，规则说明、字段说明、碳排试算和原始明细表已退到次级层，`steam` 继续保持仅运行态存在时显示。
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
- [Dashboard.vue](/Users/todo/CampusEnergySystem/frontend/src/views/Dashboard.vue)
- [EnergyManagement.vue](/Users/todo/CampusEnergySystem/frontend/src/views/EnergyManagement.vue)
