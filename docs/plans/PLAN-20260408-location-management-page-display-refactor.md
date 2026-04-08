# PLAN-20260408-位置管理页展示重构专题

> 状态：已阶段收口，暂不迁 archive，等待下一个主主题 | 负责人：探索 / 前端 / 验收线程 | 更新时间：2026-04-08

## 1. 背景

当前 [LocationManager.vue](/Users/todo/CampusEnergySystem/frontend/src/views/LocationManager.vue) 的真实角色仍然是“位置树 + CRUD 详情页”，不是面向园区运营侧的“园区空间主视图”。

当前已确认的核心问题：

- 页面整体仍偏工具页，不具备空间主视图的主线叙事。
- 右侧未选中默认态过空，是页面空感的最直接来源。
- 前端树与统计对后端响应存在字段错位：
  - tree 使用 `location_type`
  - 后端 tree 返回 `type`
  - stats 使用扁平字段
  - 后端实际返回嵌套结构
- 当前已有接口足以支撑第一轮重构，默认不需要新增后端接口。

因此，本专题第一轮不再以“补更多管理能力”或“继续强化 CRUD”为目标，而是把页面收敛为“园区空间主视图”。

## 2. 目标

- 将 [LocationManager.vue](/Users/todo/CampusEnergySystem/frontend/src/views/LocationManager.vue) 从“位置管理工具页”收敛为“园区空间主视图”。
- 让未选中态具备完整的“园区空间总览”主视图，而不是空白占位。
- 让选中态具备“空间焦点视图 + 次级管理入口”，而不是继续以 CRUD 详情为主。
- 在前端消费层解决 tree / stats 与后端响应的字段错位问题。

## 3. 第一轮最小可控范围

第一轮只允许处理：

- [LocationManager.vue](/Users/todo/CampusEnergySystem/frontend/src/views/LocationManager.vue)
- [location.ts](/Users/todo/CampusEnergySystem/frontend/src/api/location.ts)
- 必要时与该页直接相关的前端 API 消费适配层
- [current-status.md](/Users/todo/CampusEnergySystem/docs/plans/current-status.md)
- [handoff.md](/Users/todo/CampusEnergySystem/docs/plans/handoff.md)

第一轮默认路径：

- `规范 -> 前端 -> 验收`

第一轮默认不启动后端线程。

## 4. 未选中态必须展示的内容

未选中态必须改造成“园区空间总览”，至少包括：

- 园区空间层级的概览性主视图
- 位置类型 / 数量 / 分布的总览信息
- 当前空间体系的关键入口或聚焦提示
- 能让用户立即理解“园区空间结构”的主展示内容

未选中态不能继续是空白右侧加弱提示文案。

## 5. 选中态必须展示的内容

选中态必须改造成“空间焦点视图 + 次级管理入口”，至少包括：

- 当前空间名称与层级路径
- 当前空间的核心统计与状态摘要
- 子空间 / 关联设备 / 关键结构信息的主展示
- 次级管理入口，但不再让 CRUD 成为视觉主角

## 6. 必须降级到次级层的内容

以下能力必须退居次级层：

- 新建位置
- 编辑位置
- 删除位置
- 新建子位置
- 设备分配
- 纯 CRUD 详情展示

这些能力仍可保留，但不再构成页面主视图。

## 7. 第一轮明确不应纳入的内容

- 不做 3D 场景重构
- 不做位置模型大改
- 不默认新增后端接口
- 不改 [Dashboard.vue](/Users/todo/CampusEnergySystem/frontend/src/views/Dashboard.vue)
- 不改 [CampusScene.vue](/Users/todo/CampusEnergySystem/frontend/src/views/CampusScene.vue)
- 不做跨页面空间系统重构
- 不把本轮重新拉回“位置管理工具页增强”方向

## 8. 冻结边界

- 不新增后端接口，除非前端线程证明现有接口无法支撑第一轮目标，并先打回规范线程重锁边界。
- 不修改位置模型语义、层级定义或主数据结构。
- 不把本轮扩张为园区空间全站视觉重构。
- 不顺手修改 [Dashboard.vue](/Users/todo/CampusEnergySystem/frontend/src/views/Dashboard.vue)、[CampusScene.vue](/Users/todo/CampusEnergySystem/frontend/src/views/CampusScene.vue) 或其他页面。
- 不把 tree / stats 字段错位问题升级为后端模型重构。

## 9. 回滚边界

- 若本轮改造后，页面主线更弱、信息层级更乱、未选中 / 选中两态更难理解，则整轮回退到当前稳定状态。
- 若前端线程发现必须新增后端接口才能成立，应停止该项并回到规范线程重新锁边界，不得顺手启动后端扩张。
- 若实现开始波及 3D 场景、位置模型或其他页面，应立即回退到单页范围。

## 10. 验收口径

本轮验收至少应核对：

- 页面是否已从“位置树 + CRUD 详情页”收敛为“园区空间主视图”
- 未选中态是否已成为“园区空间总览”
- 选中态是否已成为“空间焦点视图 + 次级管理入口”
- CRUD / 设备分配 / 新建子位置是否已退居次级层
- tree / stats 与后端响应的字段错位是否已在前端消费层正确收敛
- 本轮是否未越界到 3D 场景重构、位置模型大改、后端接口新增或跨页重构

## 11. 进度记录

- 2026-04-08：已确认 [LocationManager.vue](/Users/todo/CampusEnergySystem/frontend/src/views/LocationManager.vue) 当前真实角色仍是“位置管理工具页”，需要独立立项重构。
- 2026-04-08：已正式建立 `位置管理页展示重构专题`，并锁定第一轮为前端单页局部重构。
- 2026-04-08：第一轮已验收通过，[LocationManager.vue](/Users/todo/CampusEnergySystem/frontend/src/views/LocationManager.vue) 已收敛为“园区空间主视图”，未选中态与选中态目标均已达成。
- 2026-04-08：已完成阶段收口判断；当前没有足够明确、足够独立的后续最小可控范围，本主题退出主区、暂不迁 archive，保留在 `docs/plans/` 作为近期成果主题。
- 2026-04-08：用户反馈“园区空间”页面运行态仍打不开；此前收口结论撤回，主题重开，当前优先级切换为锁定真实运行态根因并完成浏览器级可打开性修复。
- 2026-04-08：已锁定真实根因为前端页面路由命中后端代理前缀：原 `/locations` 与 `/locations` 接口冲突，尝试的 `/campus-space` 又命中 `/campus` 代理；当前优先执行彻底避让代理前缀的路由修复，并以浏览器级打开验证作为重新验收前置条件。
- 2026-04-08：已完成最小运行态修复：前端页面路由调整为 `/spaces`，并补齐 `/campus` 开发代理；`npx playwright test tests/e2e/location-manager-open.spec.ts` 已通过，当前进入重新验收。
- 2026-04-08：已完成重新验收；确认浏览器运行态下“园区空间”可稳定打开，本主题重新达到阶段完成与阶段收口条件，退出主区、暂不迁 archive。

## 12. 阶段收口结论

- 此前阶段收口结论已因用户运行态反馈撤回，并已在本轮完成重新修复与重新验收。
- 已确认新的收口判断以浏览器运行态可稳定打开为前置条件，本轮已满足该条件。
- 已确认本主题重新达到阶段收口条件。
- 已确认本主题退出主区，但暂不迁 archive。
- 已确认当前主区应切换为“等待下一个主主题”。
