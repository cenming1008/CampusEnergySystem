# PLAN-20260408-能耗分析页产品化重构专题

> 状态：已阶段收口，暂不迁 archive，等待下一个主主题 | 负责人：规范 / 前端 / 后端 / 验收线程 | 更新时间：2026-04-08

---

## 背景

当前路由中：

- `/forecast` 的导航标题是“能耗分析”
- 实际页面实现却是 [Forecast.vue](/Users/todo/CampusEnergySystem/frontend/src/views/Forecast.vue)

基于最新探索结论，当前页面真实角色更像：

- 预测结果查看页
- 模型训练 / 评估 / 版本管理工具页
- 预测能力调试与运营工具页

它并不是一个面向园区运营侧的“能耗分析主页面”。

与此同时：

- 当前后端对预测能力支撑较完整
- 当前后端对“园区 / 区域 / 楼栋 / 设备 / 能源介质 / 分项能耗”的产品化分析页支撑不足
- 如果目标是“真正的能耗分析页产品化”，默认需要后端线程介入，补齐园区运营分析主线所需的聚合接口

因此需要正式建立新主题：

- 保留 [Forecast.vue](/Users/todo/CampusEnergySystem/frontend/src/views/Forecast.vue) 作为独立“预测 / 模型工具页”
- 将“能耗分析”收敛为新的园区运营分析主页面方向

---

## 目标

- 明确页面角色拆分：
  - [Forecast.vue](/Users/todo/CampusEnergySystem/frontend/src/views/Forecast.vue) 保留为预测 / 模型工具页
  - “能耗分析”转向面向园区运营侧的新主页面
- 新主页面默认围绕以下对象建立产品化分析主线：
  - 园区
  - 区域
  - 楼栋
  - 设备
  - 能源介质
  - 分项能耗
- 页面能力优先收敛为：
  - 趋势
  - 对比
  - 排行
  - 异常
  - 洞察
- 通过前后端协同完成“页面产品化分析能力”闭环，而不是继续把训练、版本、超参工具堆在主视图里

## 页面角色拆分结论

### `Forecast.vue`

- 继续保留为独立“预测 / 模型工具页”
- 它可以继续承载：
  - 预测生成
  - 精度评估
  - 模型训练
  - 版本管理
  - 超参数搜索
  - 调度任务查看

### “能耗分析”

- 不应再直接等同于 `Forecast.vue`
- 应成为新的园区运营分析主页面
- 面向运营侧用户，而不是模型维护者

## 最小可控范围

涉及目录或模块：

- [router/index.ts](/Users/todo/CampusEnergySystem/frontend/src/router/index.ts)
- [Forecast.vue](/Users/todo/CampusEnergySystem/frontend/src/views/Forecast.vue)
- 新的能耗分析主页面文件（文件名由后续前端线程在实现时最小确定）
- [forecast.ts](/Users/todo/CampusEnergySystem/frontend/src/api/forecast.ts)
- [device.ts](/Users/todo/CampusEnergySystem/frontend/src/api/device.ts)
- [telemetry.ts](/Users/todo/CampusEnergySystem/frontend/src/api/telemetry.ts)
- [analysis.py](/Users/todo/CampusEnergySystem/app/api/endpoints/analysis.py)
- [basic.py](/Users/todo/CampusEnergySystem/app/api/endpoints/forecast/basic.py)
- [lstm.py](/Users/todo/CampusEnergySystem/app/api/endpoints/forecast/lstm.py)
- [forecasting.py](/Users/todo/CampusEnergySystem/app/application/forecasting.py)
- [analysis_service.py](/Users/todo/CampusEnergySystem/app/services/analysis_service.py)
- [adapter.py](/Users/todo/CampusEnergySystem/app/integrations/forecasting/adapter.py)
- [current-status.md](/Users/todo/CampusEnergySystem/docs/plans/current-status.md)
- [handoff.md](/Users/todo/CampusEnergySystem/docs/plans/handoff.md)

## 前端职责边界

前端线程负责：

- 页面角色拆分
- 路由标题与导航语义收敛
- 新能耗分析主页面的信息架构
- 园区运营分析主页面的结构、交互路径与模块组织
- 将预测 / 模型相关内容从运营分析主视图中分离出去

前端线程不负责：

- 自行定义新的分析聚合口径
- 用临时拼装方式替代稳定后端聚合接口
- 顺手扩张到首页、园区总览、设备页等全站改造

## 后端职责边界

后端线程负责：

- 提供园区级 / 区域级 / 楼栋级 / 设备级分析聚合接口
- 提供能源介质 / 分项能耗的产品化分析读取能力
- 为趋势、对比、排行、异常、洞察提供稳定数据口径
- 保持预测能力接口与分析能力接口的职责分离

后端线程不负责：

- 扩张为算法平台改造
- 把训练、版本、超参与模型管理重新塞回运营分析主视图
- 无边界重做所有分析接口

## 明确非目标

- 不做算法平台扩张
- 不把训练 / 版本 / 超参继续放在运营分析主视图
- 不做无边界全站重构
- 不修改数据库、MQTT、监控或运行时契约
- 不把 `Forecast.vue` 删除或粗暴合并进新分析页
- 不在本轮顺手重构首页、园区总览、设备与表计页面

## 冻结边界

- 不把 “预测 / 模型工具页” 与 “能耗分析主页面” 混成一个页面
- 不顺手扩张为全站导航重构
- 不顺手扩张为算法训练平台专题
- 不修改运行时命名、数据库、MQTT、监控或其他契约
- 不在没有稳定后端分析聚合口径前，让前端长期依赖散装接口拼装

## 回滚边界

- 若前后端协同过程中发现“能耗分析主页面”与 `Forecast.vue` 的角色拆分反而更模糊，应回退到当前稳定状态：
  - `Forecast.vue` 继续保持预测 / 模型工具页
  - “能耗分析”先不切主页面实现
- 若后端聚合能力补齐范围明显超出园区运营分析主线，应整轮回退到“仅完成主题边界锁定”的状态
- 若前端实现开始波及首页、园区总览、设备页等其他主页面，应立即回退到本主题最小范围

## 验收标准

- [ ] `Forecast.vue` 的角色已明确收敛为独立“预测 / 模型工具页”
- [ ] “能耗分析”已明确转向新的园区运营分析主页面语义
- [ ] 新分析页面向园区 / 区域 / 楼栋 / 设备 / 能源介质 / 分项能耗主线组织
- [ ] 页面能力已围绕趋势、对比、排行、异常、洞察建立，而不是模型训练工具
- [ ] 前端与后端职责边界清晰，未互相越位
- [ ] 本轮未扩张为算法平台扩张、全站导航重构或无边界接口重写

## 推荐路径

- `规范 -> 前端 + 后端 -> 验收`

## 进度记录

- 2026-04-08：已确认当前路由标题“能耗分析”与 `Forecast.vue` 的真实页面角色不一致。
- 2026-04-08：已正式立项为 `能耗分析页产品化重构专题`，并锁定 `Forecast.vue` 保留为预测 / 模型工具页、“能耗分析”转向园区运营分析主页面的拆分方向。
- 2026-04-08：前后端联合作业验收已通过；已确认 `Forecast.vue` 保持独立预测 / 模型工具页，`EnergyAnalysis.vue` 已正式接入 `GET /analysis/overview`，并形成园区运营分析主页面与后端第一批最小运营分析聚合。
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
- [Forecast.vue](/Users/todo/CampusEnergySystem/frontend/src/views/Forecast.vue)
- [Dashboard.vue](/Users/todo/CampusEnergySystem/frontend/src/views/Dashboard.vue)
- [EnergyManagement.vue](/Users/todo/CampusEnergySystem/frontend/src/views/EnergyManagement.vue)
