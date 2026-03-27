# Document Audit

## 审计范围与方法
- 范围：
  - 项目根目录 Markdown
  - `docs/` 下全部 Markdown
  - 与前端、后端、分层、接口、页面结构、计划、排障、重构、迁移、交接相关的历史说明
  - 补充参考了少量模块级 README：`app/README.md`、`app/api/README.md`、`frontend/README.md`、`frontend/DEVELOPMENT.md`、`frontend/FRONTEND_STRUCTURE.md`
- 本轮动作：
  - 只做盘点、分类、判断、建议
  - 不删除文件
  - 不改业务代码
- 判断标准：
  - 当前开发是否真的会看
  - 是否仍匹配当前代码结构
  - 是否被 `AGENTS.md`、`README.md`、`docs/README.md` 或流程文档引用
  - 是否与同主题文档重复
  - 是否只是一次性历史遗留

---

## 一、核心保留文档

以下文档应长期保留，并继续维护。

- [AGENTS.md](/Users/todo/MineEnergySystem/AGENTS.md)
  - 当前协作主规则，直接决定四线程工作顺序与交接格式。
  - 与当前协作流程完全一致。

- [README.md](/Users/todo/MineEnergySystem/README.md)
  - 项目总入口，仍是新成员和外部读者最先看到的文档。
  - 整体仍有价值，但内部已有少量旧链接和旧接口描述，属于“保留并修正”。

- [docs/README.md](/Users/todo/MineEnergySystem/docs/README.md)
  - 文档中心总入口。
  - 仍有导航价值，但当前混入了一些不该作为主入口的历史/一次性文档，需收敛索引。

- [docs/guides/README.md](/Users/todo/MineEnergySystem/docs/guides/README.md)
- [docs/guides/frontend-guidelines.md](/Users/todo/MineEnergySystem/docs/guides/frontend-guidelines.md)
- [docs/guides/backend-guidelines.md](/Users/todo/MineEnergySystem/docs/guides/backend-guidelines.md)
- [docs/guides/文档体系规范.md](/Users/todo/MineEnergySystem/docs/guides/%E6%96%87%E6%A1%A3%E4%BD%93%E7%B3%BB%E8%A7%84%E8%8C%83.md)
- [docs/guides/变更计划规范.md](/Users/todo/MineEnergySystem/docs/guides/%E5%8F%98%E6%9B%B4%E8%AE%A1%E5%88%92%E8%A7%84%E8%8C%83.md)
  - 这是当前真正的“长期规则层”。
  - 与 `AGENTS.md` 和当前文档治理方向一致，应持续维护。

- [docs/plans/current-status.md](/Users/todo/MineEnergySystem/docs/plans/current-status.md)
- [docs/plans/handoff.md](/Users/todo/MineEnergySystem/docs/plans/handoff.md)
- [docs/plans/README.md](/Users/todo/MineEnergySystem/docs/plans/README.md)
- [docs/plans/TEMPLATE.md](/Users/todo/MineEnergySystem/docs/plans/TEMPLATE.md)
  - 当前协作状态与交接核心。
  - `TEMPLATE.md` 虽是模板，但仍有明确用途，不是空壳噪音。

- [docs/01-新手入门/快速启动指南.md](/Users/todo/MineEnergySystem/docs/01-%E6%96%B0%E6%89%8B%E5%85%A5%E9%97%A8/%E5%BF%AB%E9%80%9F%E5%90%AF%E5%8A%A8%E6%8C%87%E5%8D%97.md)
- [docs/01-新手入门/安装配置完整指南.md](/Users/todo/MineEnergySystem/docs/01-%E6%96%B0%E6%89%8B%E5%85%A5%E9%97%A8/%E5%AE%89%E8%A3%85%E9%85%8D%E7%BD%AE%E5%AE%8C%E6%95%B4%E6%8C%87%E5%8D%97.md)
- [docs/01-新手入门/本地开发环境配置.md](/Users/todo/MineEnergySystem/docs/01-%E6%96%B0%E6%89%8B%E5%85%A5%E9%97%A8/%E6%9C%AC%E5%9C%B0%E5%BC%80%E5%8F%91%E7%8E%AF%E5%A2%83%E9%85%8D%E7%BD%AE.md)
  - 当前仍是有效的新手与开发入口。
  - 与实际 `8088` 后端、Vite 前端、Docker 中间件结构基本一致。

- [docs/03-开发与部署/README.md](/Users/todo/MineEnergySystem/docs/03-%E5%BC%80%E5%8F%91%E4%B8%8E%E9%83%A8%E7%BD%B2/README.md)
- [docs/03-开发与部署/企业部署完整指南.md](/Users/todo/MineEnergySystem/docs/03-%E5%BC%80%E5%8F%91%E4%B8%8E%E9%83%A8%E7%BD%B2/%E4%BC%81%E4%B8%9A%E9%83%A8%E7%BD%B2%E5%AE%8C%E6%95%B4%E6%8C%87%E5%8D%97.md)
- [docs/03-开发与部署/工业上线清单.md](/Users/todo/MineEnergySystem/docs/03-%E5%BC%80%E5%8F%91%E4%B8%8E%E9%83%A8%E7%BD%B2/%E5%B7%A5%E4%B8%9A%E4%B8%8A%E7%BA%BF%E6%B8%85%E5%8D%95.md)
- [docs/03-开发与部署/MQTT接入协议冻结版.md](/Users/todo/MineEnergySystem/docs/03-%E5%BC%80%E5%8F%91%E4%B8%8E%E9%83%A8%E7%BD%B2/MQTT%E6%8E%A5%E5%85%A5%E5%8D%8F%E8%AE%AE%E5%86%BB%E7%BB%93%E7%89%88.md)
- [docs/03-开发与部署/后端容量基线指南.md](/Users/todo/MineEnergySystem/docs/03-%E5%BC%80%E5%8F%91%E4%B8%8E%E9%83%A8%E7%BD%B2/%E5%90%8E%E7%AB%AF%E5%AE%B9%E9%87%8F%E5%9F%BA%E7%BA%BF%E6%8C%87%E5%8D%97.md)
- [docs/03-开发与部署/试点发布与现场演练手册.md](/Users/todo/MineEnergySystem/docs/03-%E5%BC%80%E5%8F%91%E4%B8%8E%E9%83%A8%E7%BD%B2/%E8%AF%95%E7%82%B9%E5%8F%91%E5%B8%83%E4%B8%8E%E7%8E%B0%E5%9C%BA%E6%BC%94%E7%BB%83%E6%89%8B%E5%86%8C.md)
- [docs/03-开发与部署/试点验收证据包模板.md](/Users/todo/MineEnergySystem/docs/03-%E5%BC%80%E5%8F%91%E4%B8%8E%E9%83%A8%E7%BD%B2/%E8%AF%95%E7%82%B9%E9%AA%8C%E6%94%B6%E8%AF%81%E6%8D%AE%E5%8C%85%E6%A8%A1%E6%9D%BF.md)
  - 这些文档仍服务当前部署、上线、试点、演练和交付流程。

- [docs/04-故障排查/README.md](/Users/todo/MineEnergySystem/docs/04-%E6%95%85%E9%9A%9C%E6%8E%92%E6%9F%A5/README.md)
- [docs/04-故障排查/fix_venv_issue.md](/Users/todo/MineEnergySystem/docs/04-%E6%95%85%E9%9A%9C%E6%8E%92%E6%9F%A5/fix_venv_issue.md)
  - 排障目录入口应保留，但目录内部要显著收敛。
  - `fix_venv_issue.md` 仍是复用型专项排障，不是一次性聊天记录。

- [docs/05-架构与设计/README.md](/Users/todo/MineEnergySystem/docs/05-%E6%9E%B6%E6%9E%84%E4%B8%8E%E8%AE%BE%E8%AE%A1/README.md)
- [docs/05-架构与设计/系统总体架构说明.md](/Users/todo/MineEnergySystem/docs/05-%E6%9E%B6%E6%9E%84%E4%B8%8E%E8%AE%BE%E8%AE%A1/%E7%B3%BB%E7%BB%9F%E6%80%BB%E4%BD%93%E6%9E%B6%E6%9E%84%E8%AF%B4%E6%98%8E.md)
- [docs/05-架构与设计/角色权限矩阵.md](/Users/todo/MineEnergySystem/docs/05-%E6%9E%B6%E6%9E%84%E4%B8%8E%E8%AE%BE%E8%AE%A1/%E8%A7%92%E8%89%B2%E6%9D%83%E9%99%90%E7%9F%A9%E9%98%B5.md)
- [docs/05-架构与设计/后端代码分析报告.md](/Users/todo/MineEnergySystem/docs/05-%E6%9E%B6%E6%9E%84%E4%B8%8E%E8%AE%BE%E8%AE%A1/%E5%90%8E%E7%AB%AF%E4%BB%A3%E7%A0%81%E5%88%86%E6%9E%90%E6%8A%A5%E5%91%8A.md)
  - 这几份最接近当前真实结构。
  - 尤其 `后端代码分析报告.md` 明确写了按 2026-03-26 仓库状态更新，参考价值高。

- [docs/关键功能链路说明.md](/Users/todo/MineEnergySystem/docs/%E5%85%B3%E9%94%AE%E5%8A%9F%E8%83%BD%E9%93%BE%E8%B7%AF%E8%AF%B4%E6%98%8E.md)
  - 适合作为当前项目的高层“讲清楚这套系统怎么跑”的入口文档。

- [app/README.md](/Users/todo/MineEnergySystem/app/README.md)
- [app/api/README.md](/Users/todo/MineEnergySystem/app/api/README.md)
- [frontend/README.md](/Users/todo/MineEnergySystem/frontend/README.md)
- [scripts/README.md](/Users/todo/MineEnergySystem/scripts/README.md)
- [config/README.md](/Users/todo/MineEnergySystem/config/README.md)
- [config/README_gateway_devices.md](/Users/todo/MineEnergySystem/config/README_gateway_devices.md)
- [migrations/README.md](/Users/todo/MineEnergySystem/migrations/README.md)
- [artifacts/README.md](/Users/todo/MineEnergySystem/artifacts/README.md)
- [bin/README.md](/Users/todo/MineEnergySystem/bin/README.md)
  - 这些是当前真实目录的模块入口说明。
  - 整体价值高于大部分历史总结型文档。

---

## 二、建议合并的文档

以下文档内容仍有价值，但不值得继续独立维护。

- [docs/01-新手入门/全新系统初始化指南.md](/Users/todo/MineEnergySystem/docs/01-%E6%96%B0%E6%89%8B%E5%85%A5%E9%97%A8/%E5%85%A8%E6%96%B0%E7%B3%BB%E7%BB%9F%E5%88%9D%E5%A7%8B%E5%8C%96%E6%8C%87%E5%8D%97.md)
  - 建议并入：
    - [docs/01-新手入门/安装配置完整指南.md](/Users/todo/MineEnergySystem/docs/01-%E6%96%B0%E6%89%8B%E5%85%A5%E9%97%A8/%E5%AE%89%E8%A3%85%E9%85%8D%E7%BD%AE%E5%AE%8C%E6%95%B4%E6%8C%87%E5%8D%97.md)
  - 理由：
    - 与快速启动/安装配置高度重叠
    - 不是独立产品线，而是初始化场景分支
    - 保留三套新手路径会增加维护成本

- [docs/02-功能使用/数据清理功能说明.md](/Users/todo/MineEnergySystem/docs/02-%E5%8A%9F%E8%83%BD%E4%BD%BF%E7%94%A8/%E6%95%B0%E6%8D%AE%E6%B8%85%E7%90%86%E5%8A%9F%E8%83%BD%E8%AF%B4%E6%98%8E.md)
- [docs/02-功能使用/数据自动清理功能说明.md](/Users/todo/MineEnergySystem/docs/02-%E5%8A%9F%E8%83%BD%E4%BD%BF%E7%94%A8/%E6%95%B0%E6%8D%AE%E8%87%AA%E5%8A%A8%E6%B8%85%E7%90%86%E5%8A%9F%E8%83%BD%E8%AF%B4%E6%98%8E.md)
- [docs/07-快速参考/清除多能源管理页面数据指南.md](/Users/todo/MineEnergySystem/docs/07-%E5%BF%AB%E9%80%9F%E5%8F%82%E8%80%83/%E6%B8%85%E9%99%A4%E5%A4%9A%E8%83%BD%E6%BA%90%E7%AE%A1%E7%90%86%E9%A1%B5%E9%9D%A2%E6%95%B0%E6%8D%AE%E6%8C%87%E5%8D%97.md)
  - 建议并入：
    - 一个新的统一文档，例如 `docs/02-功能使用/数据清理与保留策略.md`
  - 理由：
    - 三份文档同主题重复明显
    - 当前相互引用已有失效链接
    - 手动清理、自动清理、页面操作应放在同一个概念入口

- [docs/02-功能使用/统一设备管理指南.md](/Users/todo/MineEnergySystem/docs/02-%E5%8A%9F%E8%83%BD%E4%BD%BF%E7%94%A8/%E7%BB%9F%E4%B8%80%E8%AE%BE%E5%A4%87%E7%AE%A1%E7%90%86%E6%8C%87%E5%8D%97.md)
- [docs/07-快速参考/快速参考-统一设备管理.md](/Users/todo/MineEnergySystem/docs/07-%E5%BF%AB%E9%80%9F%E5%8F%82%E8%80%83/%E5%BF%AB%E9%80%9F%E5%8F%82%E8%80%83-%E7%BB%9F%E4%B8%80%E8%AE%BE%E5%A4%87%E7%AE%A1%E7%90%86.md)
  - 建议并入：
    - 以 `统一设备管理指南.md` 为主
  - 理由：
    - 速查卡中大量旧接口与旧路径已失效
    - 主指南价值更高，速查卡应成为主指南中的“快速开始”章节，而不是独立文档

- [docs/07-快速参考/本地开发快速参考.md](/Users/todo/MineEnergySystem/docs/07-%E5%BF%AB%E9%80%9F%E5%8F%82%E8%80%83/%E6%9C%AC%E5%9C%B0%E5%BC%80%E5%8F%91%E5%BF%AB%E9%80%9F%E5%8F%82%E8%80%83.md)
  - 建议并入：
    - [docs/01-新手入门/本地开发环境配置.md](/Users/todo/MineEnergySystem/docs/01-%E6%96%B0%E6%89%8B%E5%85%A5%E9%97%A8/%E6%9C%AC%E5%9C%B0%E5%BC%80%E5%8F%91%E7%8E%AF%E5%A2%83%E9%85%8D%E7%BD%AE.md)
  - 理由：
    - 同一主题两份入口
    - 速查文档里已有失效相对路径

- [docs/02-功能使用/串口通信入门.md](/Users/todo/MineEnergySystem/docs/02-%E5%8A%9F%E8%83%BD%E4%BD%BF%E7%94%A8/%E4%B8%B2%E5%8F%A3%E9%80%9A%E4%BF%A1%E5%85%A5%E9%97%A8.md)
- [docs/02-功能使用/串口通信精通版.md](/Users/todo/MineEnergySystem/docs/02-%E5%8A%9F%E8%83%BD%E4%BD%BF%E7%94%A8/%E4%B8%B2%E5%8F%A3%E9%80%9A%E4%BF%A1%E7%B2%BE%E9%80%9A%E7%89%88.md)
- [docs/02-功能使用/工控设备常用通讯方式.md](/Users/todo/MineEnergySystem/docs/02-%E5%8A%9F%E8%83%BD%E4%BD%BF%E7%94%A8/%E5%B7%A5%E6%8E%A7%E8%AE%BE%E5%A4%87%E5%B8%B8%E7%94%A8%E9%80%9A%E8%AE%AF%E6%96%B9%E5%BC%8F.md)
- [docs/02-功能使用/通讯协议第一阶段学习指南.md](/Users/todo/MineEnergySystem/docs/02-%E5%8A%9F%E8%83%BD%E4%BD%BF%E7%94%A8/%E9%80%9A%E8%AE%AF%E5%8D%8F%E8%AE%AE%E7%AC%AC%E4%B8%80%E9%98%B6%E6%AE%B5%E5%AD%A6%E4%B9%A0%E6%8C%87%E5%8D%97.md)
  - 建议并入：
    - 一个统一的“设备接入与通信学习专题”
  - 理由：
    - 它们更像培训材料，不是主功能入口
    - 长期散落会冲淡真正用于开发的文档入口

- [docs/03-开发与部署/Docker清理与本地运行指南.md](/Users/todo/MineEnergySystem/docs/03-%E5%BC%80%E5%8F%91%E4%B8%8E%E9%83%A8%E7%BD%B2/Docker%E6%B8%85%E7%90%86%E4%B8%8E%E6%9C%AC%E5%9C%B0%E8%BF%90%E8%A1%8C%E6%8C%87%E5%8D%97.md)
  - 建议并入：
    - `本地开发环境配置.md`
    - `DOCKER_SCRIPTS.md`
  - 理由：
    - 生成于固定日期
    - 主体是操作整理，不该独立长期维护

- [docs/05-架构与设计/统一架构重构说明.md](/Users/todo/MineEnergySystem/docs/05-%E6%9E%B6%E6%9E%84%E4%B8%8E%E8%AE%BE%E8%AE%A1/%E7%BB%9F%E4%B8%80%E6%9E%B6%E6%9E%84%E9%87%8D%E6%9E%84%E8%AF%B4%E6%98%8E.md)
- [docs/05-架构与设计/后端调用流程图.md](/Users/todo/MineEnergySystem/docs/05-%E6%9E%B6%E6%9E%84%E4%B8%8E%E8%AE%BE%E8%AE%A1/%E5%90%8E%E7%AB%AF%E8%B0%83%E7%94%A8%E6%B5%81%E7%A8%8B%E5%9B%BE.md)
- [docs/05-架构与设计/DeviceService与EnergyService对比说明.md](/Users/todo/MineEnergySystem/docs/05-%E6%9E%B6%E6%9E%84%E4%B8%8E%E8%AE%BE%E8%AE%A1/DeviceService%E4%B8%8EEnergyService%E5%AF%B9%E6%AF%94%E8%AF%B4%E6%98%8E.md)
- [docs/05-架构与设计/枚举设计说明.md](/Users/todo/MineEnergySystem/docs/05-%E6%9E%B6%E6%9E%84%E4%B8%8E%E8%AE%BE%E8%AE%A1/%E6%9E%9A%E4%B8%BE%E8%AE%BE%E8%AE%A1%E8%AF%B4%E6%98%8E.md)
  - 建议并入：
    - [docs/05-架构与设计/系统总体架构说明.md](/Users/todo/MineEnergySystem/docs/05-%E6%9E%B6%E6%9E%84%E4%B8%8E%E8%AE%BE%E8%AE%A1/%E7%B3%BB%E7%BB%9F%E6%80%BB%E4%BD%93%E6%9E%B6%E6%9E%84%E8%AF%B4%E6%98%8E.md)
    - [docs/05-架构与设计/后端代码分析报告.md](/Users/todo/MineEnergySystem/docs/05-%E6%9E%B6%E6%9E%84%E4%B8%8E%E8%AE%BE%E8%AE%A1/%E5%90%8E%E7%AB%AF%E4%BB%A3%E7%A0%81%E5%88%86%E6%9E%90%E6%8A%A5%E5%91%8A.md)
  - 理由：
    - 这些文档里有价值的内容不少，但过于碎片化
    - 主架构入口应尽量收敛到 1-2 个核心文档

- [frontend/DEVELOPMENT.md](/Users/todo/MineEnergySystem/frontend/DEVELOPMENT.md)
  - 建议并入：
    - [frontend/README.md](/Users/todo/MineEnergySystem/frontend/README.md)
  - 理由：
    - 仍有价值，但端口与代理描述停留在旧状态
    - 独立维护成本高于收益

- [lstm_forecast/README.md](/Users/todo/MineEnergySystem/lstm_forecast/README.md)
  - 建议并入：
    - `docs/02-功能使用/LSTM预测完整指南.md`
  - 理由：
    - 仍有价值，但内容引用了不存在的 `app/services/lstm_adapter.py`
    - 目录 README 更适合缩成“目录职责说明”

---

## 三、建议归档的文档

以下文档有历史价值，但不应继续作为当前开发入口。

- [CHANGELOG_v2.2.0.md](/Users/todo/MineEnergySystem/CHANGELOG_v2.2.0.md)
  - 版本历史记录，应保留但不该作为主入口。

- [docs/plans/PLAN-20260327-文档体系建设.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-%E6%96%87%E6%A1%A3%E4%BD%93%E7%B3%BB%E5%BB%BA%E8%AE%BE.md)
  - 已完成计划。
  - 不再是当前进行中的执行入口。

- [docs/plans/device-manager-analysis.md](/Users/todo/MineEnergySystem/docs/plans/device-manager-analysis.md)
  - 当前仍有参考价值，但一旦对应问题完成，应该转历史分析，不应长期留在活跃入口。

- [docs/02-功能使用/多能源管理功能实现说明.md](/Users/todo/MineEnergySystem/docs/02-%E5%8A%9F%E8%83%BD%E4%BD%BF%E7%94%A8/%E5%A4%9A%E8%83%BD%E6%BA%90%E7%AE%A1%E7%90%86%E5%8A%9F%E8%83%BD%E5%AE%9E%E7%8E%B0%E8%AF%B4%E6%98%8E.md)
  - 已完成实现总结，偏历史复盘。

- [docs/03-开发与部署/OPTIMIZATION_RECOMMENDATIONS.md](/Users/todo/MineEnergySystem/docs/03-%E5%BC%80%E5%8F%91%E4%B8%8E%E9%83%A8%E7%BD%B2/OPTIMIZATION_RECOMMENDATIONS.md)
- [docs/03-开发与部署/试点验收结论_20260326.md](/Users/todo/MineEnergySystem/docs/03-%E5%BC%80%E5%8F%91%E4%B8%8E%E9%83%A8%E7%BD%B2/%E8%AF%95%E7%82%B9%E9%AA%8C%E6%94%B6%E7%BB%93%E8%AE%BA_20260326.md)
- [docs/03-开发与部署/试点验收简版汇报_20260326.md](/Users/todo/MineEnergySystem/docs/03-%E5%BC%80%E5%8F%91%E4%B8%8E%E9%83%A8%E7%BD%B2/%E8%AF%95%E7%82%B9%E9%AA%8C%E6%94%B6%E7%AE%80%E7%89%88%E6%B1%87%E6%8A%A5_20260326.md)
- [docs/03-开发与部署/正式投产前差距清单_20260326.md](/Users/todo/MineEnergySystem/docs/03-%E5%BC%80%E5%8F%91%E4%B8%8E%E9%83%A8%E7%BD%B2/%E6%AD%A3%E5%BC%8F%E6%8A%95%E4%BA%A7%E5%89%8D%E5%B7%AE%E8%B7%9D%E6%B8%85%E5%8D%95_20260326.md)
- [docs/03-开发与部署/恢复演练记录.md](/Users/todo/MineEnergySystem/docs/03-%E5%BC%80%E5%8F%91%E4%B8%8E%E9%83%A8%E7%BD%B2/%E6%81%A2%E5%A4%8D%E6%BC%94%E7%BB%83%E8%AE%B0%E5%BD%95.md)
  - 都属于带日期的阶段性交付、验收、评估和演练记录。
  - 有保留价值，但不应继续被当成当前操作入口。

- [docs/05-架构与设计/前后端功能对比分析.md](/Users/todo/MineEnergySystem/docs/05-%E6%9E%B6%E6%9E%84%E4%B8%8E%E8%AE%BE%E8%AE%A1/%E5%89%8D%E5%90%8E%E7%AB%AF%E5%8A%9F%E8%83%BD%E5%AF%B9%E6%AF%94%E5%88%86%E6%9E%90.md)
- [docs/05-架构与设计/设备层级管理需求分析.md](/Users/todo/MineEnergySystem/docs/05-%E6%9E%B6%E6%9E%84%E4%B8%8E%E8%AE%BE%E8%AE%A1/%E8%AE%BE%E5%A4%87%E5%B1%82%E7%BA%A7%E7%AE%A1%E7%90%86%E9%9C%80%E6%B1%82%E5%88%86%E6%9E%90.md)
- [docs/05-架构与设计/配置阈值优化报告.md](/Users/todo/MineEnergySystem/docs/05-%E6%9E%B6%E6%9E%84%E4%B8%8E%E8%AE%BE%E8%AE%A1/%E9%85%8D%E7%BD%AE%E9%98%88%E5%80%BC%E4%BC%98%E5%8C%96%E6%8A%A5%E5%91%8A.md)
  - 偏历史快照和已完成分析，不适合作为当前结构说明入口。

- [docs/06-历史记录/README.md](/Users/todo/MineEnergySystem/docs/06-%E5%8E%86%E5%8F%B2%E8%AE%B0%E5%BD%95/README.md) 及该目录全部内容
  - 这些本来就属于历史归档区，应继续保留在历史区。
  - 其中包括：
    - `README_全新系统.md`
    - `全新系统部署总结.md`
    - `根目录整理总结.md`
    - `项目文件整理总结.md`
    - `3D矿区场景升级说明.md`
    - `矿区场景仿真升级说明.md`
    - `CHANGELOG_维护功能.md`
    - `CHANGELOG_设备分组功能.md`
    - `MyEMS资源调研与3D模型建议.md`

---

## 四、删除候选文档

以下文档最像噪音，删除前只需要再做一次引用复核即可。

- [docs/04-故障排查/前端BUG修复报告.md](/Users/todo/MineEnergySystem/docs/04-%E6%95%85%E9%9A%9C%E6%8E%92%E6%9F%A5/%E5%89%8D%E7%AB%AFBUG%E4%BF%AE%E5%A4%8D%E6%8A%A5%E5%91%8A.md)
- [docs/04-故障排查/前端登录问题说明.md](/Users/todo/MineEnergySystem/docs/04-%E6%95%85%E9%9A%9C%E6%8E%92%E6%9F%A5/%E5%89%8D%E7%AB%AF%E7%99%BB%E5%BD%95%E9%97%AE%E9%A2%98%E8%AF%B4%E6%98%8E.md)
- [docs/04-故障排查/多能源管理问题修复说明.md](/Users/todo/MineEnergySystem/docs/04-%E6%95%85%E9%9A%9C%E6%8E%92%E6%9F%A5/%E5%A4%9A%E8%83%BD%E6%BA%90%E7%AE%A1%E7%90%86%E9%97%AE%E9%A2%98%E4%BF%AE%E5%A4%8D%E8%AF%B4%E6%98%8E.md)
- [docs/04-故障排查/控制台警告问题排查.md](/Users/todo/MineEnergySystem/docs/04-%E6%95%85%E9%9A%9C%E6%8E%92%E6%9F%A5/%E6%8E%A7%E5%88%B6%E5%8F%B0%E8%AD%A6%E5%91%8A%E9%97%AE%E9%A2%98%E6%8E%92%E6%9F%A5.md)
- [docs/04-故障排查/数据清理功能故障排查.md](/Users/todo/MineEnergySystem/docs/04-%E6%95%85%E9%9A%9C%E6%8E%92%E6%9F%A5/%E6%95%B0%E6%8D%AE%E6%B8%85%E7%90%86%E5%8A%9F%E8%83%BD%E6%95%85%E9%9A%9C%E6%8E%92%E6%9F%A5.md)
- [docs/04-故障排查/立即修复-操作步骤.md](/Users/todo/MineEnergySystem/docs/04-%E6%95%85%E9%9A%9C%E6%8E%92%E6%9F%A5/%E7%AB%8B%E5%8D%B3%E4%BF%AE%E5%A4%8D-%E6%93%8D%E4%BD%9C%E6%AD%A5%E9%AA%A4.md)
- [docs/04-故障排查/紧急修复-重启服务.md](/Users/todo/MineEnergySystem/docs/04-%E6%95%85%E9%9A%9C%E6%8E%92%E6%9F%A5/%E7%B4%A7%E6%80%A5%E4%BF%AE%E5%A4%8D-%E9%87%8D%E5%90%AF%E6%9C%8D%E5%8A%A1.md)
- [docs/04-故障排查/网络连接问题排查报告.md](/Users/todo/MineEnergySystem/docs/04-%E6%95%85%E9%9A%9C%E6%8E%92%E6%9F%A5/%E7%BD%91%E7%BB%9C%E8%BF%9E%E6%8E%A5%E9%97%AE%E9%A2%98%E6%8E%92%E6%9F%A5%E6%8A%A5%E5%91%8A.md)
- [docs/04-故障排查/项目问题分析报告.md](/Users/todo/MineEnergySystem/docs/04-%E6%95%85%E9%9A%9C%E6%8E%92%E6%9F%A5/%E9%A1%B9%E7%9B%AE%E9%97%AE%E9%A2%98%E5%88%86%E6%9E%90%E6%8A%A5%E5%91%8A.md)
  - 删除候选理由：
    - 大多是一次性修复记录
    - 多数标题已经明确“已修复”“立即执行”“修复报告”
    - 与当前主排障入口重复
    - 有些仍保留旧接口、旧端口、旧模块说明
  - 风险：
    - 若团队仍偶尔用它们回忆某次老问题，需要先做一次引用和口头确认

- [docs/07-快速参考/开始使用-执行清单.md](/Users/todo/MineEnergySystem/docs/07-%E5%BF%AB%E9%80%9F%E5%8F%82%E8%80%83/%E5%BC%80%E5%A7%8B%E4%BD%BF%E7%94%A8-%E6%89%A7%E8%A1%8C%E6%B8%85%E5%8D%95.md)
  - 删除候选理由：
    - 引用了不存在文件
    - 仍使用旧路径
    - 与当前新手入口重复度高
  - 风险：
    - 若有人习惯它的 checklist 风格，可以先把其中仍有效的内容吸收到 `快速启动指南.md`

- [docs/07-快速参考/项目水平与求职定位.md](/Users/todo/MineEnergySystem/docs/07-%E5%BF%AB%E9%80%9F%E5%8F%82%E8%80%83/%E9%A1%B9%E7%9B%AE%E6%B0%B4%E5%B9%B3%E4%B8%8E%E6%B1%82%E8%81%8C%E5%AE%9A%E4%BD%8D.md)
  - 删除候选理由：
    - 不服务当前开发、部署、协作、排障
    - 无流程引用
    - 属于外部求职语境，不属于项目主文档资产
  - 风险：
    - 若作者把它当个人作品说明，应该迁出项目主文档体系，而不是继续放在 `docs/07`

- [/.pytest_cache/README.md](/Users/todo/MineEnergySystem/.pytest_cache/README.md)
  - 删除候选理由：
    - 工具生成，不属于项目文档
  - 风险：
    - 几乎没有

---

## 五、建议收敛后的文档结构

建议把“当前开发真正依赖的文档入口”尽量收敛到以下层级：

- [README.md](/Users/todo/MineEnergySystem/README.md)
- [AGENTS.md](/Users/todo/MineEnergySystem/AGENTS.md)
- [docs/README.md](/Users/todo/MineEnergySystem/docs/README.md)
- [docs/guides/frontend-guidelines.md](/Users/todo/MineEnergySystem/docs/guides/frontend-guidelines.md)
- [docs/guides/backend-guidelines.md](/Users/todo/MineEnergySystem/docs/guides/backend-guidelines.md)
- [docs/guides/文档体系规范.md](/Users/todo/MineEnergySystem/docs/guides/%E6%96%87%E6%A1%A3%E4%BD%93%E7%B3%BB%E8%A7%84%E8%8C%83.md)
- [docs/guides/变更计划规范.md](/Users/todo/MineEnergySystem/docs/guides/%E5%8F%98%E6%9B%B4%E8%AE%A1%E5%88%92%E8%A7%84%E8%8C%83.md)
- [docs/plans/current-status.md](/Users/todo/MineEnergySystem/docs/plans/current-status.md)
- [docs/plans/handoff.md](/Users/todo/MineEnergySystem/docs/plans/handoff.md)
- 必要的主文档：
  - `docs/01-新手入门/快速启动指南.md`
  - `docs/01-新手入门/安装配置完整指南.md`
  - `docs/01-新手入门/本地开发环境配置.md`
  - `docs/03-开发与部署/企业部署完整指南.md`
  - `docs/03-开发与部署/工业上线清单.md`
  - `docs/04-故障排查/README.md`
  - `docs/05-架构与设计/系统总体架构说明.md`
  - `docs/05-架构与设计/后端代码分析报告.md`
  - `docs/05-架构与设计/角色权限矩阵.md`
  - `docs/关键功能链路说明.md`
- 建议新增统一归档入口：
  - `docs/archive/`
  - 或沿用 `docs/06-历史记录/`，但需要在 `docs/README.md` 中降低其入口权重

目标不是让文档变少，而是让“当前入口少而清晰，历史材料进归档，重复主题收敛到主文档”。

---

## 六、执行建议

### 先做什么
1. 先修主入口：
   - `README.md`
   - `docs/README.md`
   - `docs/04-故障排查/README.md`
   - `docs/07-快速参考/README.md`
2. 清掉主入口里的失效链接、旧路径、旧接口表述。
3. 把明显历史性的修复报告和阶段结论从主索引中“下架”，但先不删文件。

### 哪些能安全归档
- 已完成计划
- 试点验收与简报
- 阶段性差距清单
- 功能实现总结
- 历史整理总结
- `docs/06-历史记录/*`

### 哪些需要人工确认
- `docs/04-故障排查/` 下的一次性修复文档
- `docs/07-快速参考/项目水平与求职定位.md`
- `frontend/DEVELOPMENT.md`
- `lstm_forecast/README.md`
  - 这些文件是否仍被团队某些成员私下使用，需要人工确认后再做合并或删除候选落地。

### 哪些不能贸然处理
- `AGENTS.md`
- `docs/plans/current-status.md`
- `docs/plans/handoff.md`
- `docs/guides/*`
- `README.md`
- `docs/README.md`
- 当前与真实代码结构一致的模块级 README
  - 这些文件是当前协作和导航的骨架，不能在未替代前贸然处理。

---

## 七、逐文档判断

以下矩阵覆盖本轮主审计范围中的根目录与 `docs/` 文档。字段含义：
- 用途：这份文档主要做什么
- 一致性：是否与当前代码/目录结构一致
- 维护：是否适合继续维护
- 重复：是否和其他文档明显重叠
- 历史：是否是一次性遗留
- 动作：保留 / 合并 / 归档 / 删除候选

### 根目录

| 文件 | 用途 | 一致性 | 维护 | 重复 | 历史 | 动作 |
|---|---|---|---|---|---|---|
| `AGENTS.md` | 协作规则 | 高 | 是 | 低 | 否 | 保留 |
| `README.md` | 项目总入口 | 中 | 是 | 中 | 否 | 保留 |
| `CHANGELOG_v2.2.0.md` | 版本变更记录 | 中 | 否 | 低 | 是 | 归档 |

### `docs/01-新手入门`

| 文件 | 用途 | 一致性 | 维护 | 重复 | 历史 | 动作 |
|---|---|---|---|---|---|---|
| `README.md` | 入门目录索引 | 高 | 是 | 低 | 否 | 保留 |
| `快速启动指南.md` | 快速启动 | 高 | 是 | 中 | 否 | 保留 |
| `安装配置完整指南.md` | 完整安装配置 | 高 | 是 | 中 | 否 | 保留 |
| `本地开发环境配置.md` | 本地开发模式 | 高 | 是 | 中 | 否 | 保留 |
| `全新系统初始化指南.md` | 初始化专项 | 中 | 否 | 高 | 中 | 合并 |

### `docs/02-功能使用`

| 文件 | 用途 | 一致性 | 维护 | 重复 | 历史 | 动作 |
|---|---|---|---|---|---|---|
| `README.md` | 功能目录索引 | 高 | 是 | 低 | 否 | 保留 |
| `统一设备管理指南.md` | 设备功能主指南 | 中 | 是 | 高 | 否 | 合并 |
| `多能源管理指南.md` | 多能源功能指南 | 中 | 是 | 中 | 否 | 保留 |
| `多能源管理功能实现说明.md` | 实现总结 | 中 | 否 | 中 | 是 | 归档 |
| `LSTM预测完整指南.md` | 预测功能说明 | 中 | 是 | 中 | 否 | 保留 |
| `设备分组快速开始.md` | 设备分组速查 | 中 | 否 | 高 | 中 | 合并 |
| `设备维护管理指南.md` | 维护模块说明 | 高 | 是 | 中 | 否 | 保留 |
| `数据清理功能说明.md` | 手动数据清理 | 中 | 否 | 高 | 否 | 合并 |
| `数据自动清理功能说明.md` | 自动清理策略 | 中 | 否 | 高 | 否 | 合并 |
| `真实设备接入指南.md` | 真实设备接入 | 高 | 是 | 中 | 否 | 保留 |
| `设备接入调试指南.md` | 接入调试 | 高 | 是 | 中 | 否 | 保留 |
| `外部设备接入后系统工作流程.md` | 链路流程说明 | 高 | 是 | 中 | 否 | 保留 |
| `矿区总览3D资源说明.md` | 3D资源接入说明 | 高 | 是 | 低 | 否 | 保留 |
| `串口通信入门.md` | 通信学习资料 | 中 | 否 | 高 | 否 | 合并 |
| `串口通信精通版.md` | 通信学习资料进阶 | 中 | 否 | 高 | 否 | 合并 |
| `工控设备常用通讯方式.md` | 通信学习资料 | 中 | 否 | 高 | 否 | 合并 |
| `通讯协议第一阶段学习指南.md` | 协议学习专题 | 中 | 否 | 高 | 否 | 合并 |

### `docs/03-开发与部署`

| 文件 | 用途 | 一致性 | 维护 | 重复 | 历史 | 动作 |
|---|---|---|---|---|---|---|
| `README.md` | 开发部署目录索引 | 高 | 是 | 低 | 否 | 保留 |
| `企业部署完整指南.md` | 生产部署主文档 | 高 | 是 | 中 | 否 | 保留 |
| `企业部署快速参考.md` | 部署速查 | 高 | 否 | 高 | 否 | 合并 |
| `工业上线清单.md` | 上线检查表 | 高 | 是 | 低 | 否 | 保留 |
| `MQTT接入协议冻结版.md` | MQTT接入规范 | 高 | 是 | 低 | 否 | 保留 |
| `MQTT端口防火墙策略.md` | 防火墙策略 | 高 | 是 | 低 | 否 | 保留 |
| `后端容量基线指南.md` | 容量基线 | 高 | 是 | 低 | 否 | 保留 |
| `试点发布与现场演练手册.md` | 试点发布/演练流程 | 高 | 是 | 低 | 否 | 保留 |
| `试点验收证据包模板.md` | 证据包模板 | 高 | 是 | 低 | 否 | 保留 |
| `GitHub_Actions_远程部署说明.md` | 部署流水线说明 | 高 | 是 | 低 | 否 | 保留 |
| `Git完整指南.md` | Git/SSH操作 | 高 | 是 | 中 | 否 | 保留 |
| `DATABASE_STORAGE.md` | 数据目录说明 | 中 | 是 | 中 | 否 | 保留 |
| `DOCKER_SCRIPTS.md` | Docker脚本说明 | 高 | 是 | 中 | 否 | 保留 |
| `日志管理指南.md` | 日志与清理说明 | 中 | 是 | 中 | 否 | 保留 |
| `Docker清理与本地运行指南.md` | 本地运行操作整理 | 中 | 否 | 高 | 中 | 合并 |
| `OPTIMIZATION_RECOMMENDATIONS.md` | 优化建议报告 | 中 | 否 | 中 | 是 | 归档 |
| `试点验收结论_20260326.md` | 验收结论 | 高 | 否 | 中 | 是 | 归档 |
| `试点验收简版汇报_20260326.md` | 对外简报 | 高 | 否 | 中 | 是 | 归档 |
| `正式投产前差距清单_20260326.md` | 阶段差距清单 | 高 | 否 | 中 | 是 | 归档 |
| `恢复演练记录.md` | 演练记录 | 高 | 否 | 低 | 是 | 归档 |

### `docs/04-故障排查`

| 文件 | 用途 | 一致性 | 维护 | 重复 | 历史 | 动作 |
|---|---|---|---|---|---|---|
| `README.md` | 排障入口 | 中 | 是 | 中 | 否 | 保留 |
| `fix_venv_issue.md` | 复用型专项排障 | 高 | 是 | 低 | 否 | 保留 |
| `CORS配置修复说明.md` | 一次性修复说明 | 中 | 否 | 中 | 是 | 归档 |
| `前端BUG修复报告.md` | 修复报告 | 低 | 否 | 高 | 是 | 删除候选 |
| `前端登录问题说明.md` | 单问题解释 | 中 | 否 | 高 | 是 | 删除候选 |
| `多能源管理问题修复说明.md` | 单问题修复说明 | 低 | 否 | 高 | 是 | 删除候选 |
| `控制台警告问题排查.md` | 泛化不足的排查记录 | 中 | 否 | 高 | 是 | 删除候选 |
| `数据清理功能故障排查.md` | 单问题修复说明 | 中 | 否 | 高 | 是 | 删除候选 |
| `立即修复-操作步骤.md` | 聊天式临时指令 | 低 | 否 | 高 | 是 | 删除候选 |
| `紧急修复-重启服务.md` | 临时操作指令 | 低 | 否 | 高 | 是 | 删除候选 |
| `网络连接问题排查报告.md` | 单次诊断报告 | 低 | 否 | 高 | 是 | 删除候选 |
| `项目问题分析报告.md` | 老问题快照 | 低 | 否 | 高 | 是 | 删除候选 |

### `docs/05-架构与设计`

| 文件 | 用途 | 一致性 | 维护 | 重复 | 历史 | 动作 |
|---|---|---|---|---|---|---|
| `README.md` | 架构目录索引 | 高 | 是 | 低 | 否 | 保留 |
| `系统总体架构说明.md` | 主架构文档 | 高 | 是 | 中 | 否 | 保留 |
| `后端代码分析报告.md` | 当前后端结构说明 | 高 | 是 | 中 | 否 | 保留 |
| `角色权限矩阵.md` | 权限矩阵 | 高 | 是 | 低 | 否 | 保留 |
| `DeviceData与EnergyData表说明.md` | 数据模型演进说明 | 中 | 是 | 中 | 否 | 保留 |
| `多对多关系详解.md` | 关系设计背景 | 中 | 是 | 中 | 否 | 保留 |
| `统一架构重构说明.md` | 历史重构说明 | 中 | 否 | 高 | 中 | 合并 |
| `后端调用流程图.md` | 流程图专题 | 中 | 否 | 高 | 否 | 合并 |
| `后端功能实现详解.md` | 后端实现总讲解 | 中 | 否 | 高 | 否 | 合并 |
| `DeviceService与EnergyService对比说明.md` | 服务层对比 | 中 | 否 | 高 | 否 | 合并 |
| `枚举设计说明.md` | 枚举设计专题 | 中 | 否 | 中 | 否 | 合并 |
| `前后端功能对比分析.md` | 功能快照分析 | 中 | 否 | 中 | 是 | 归档 |
| `设备层级管理需求分析.md` | 历史需求分析 | 中 | 否 | 中 | 是 | 归档 |
| `配置阈值优化报告.md` | 已完成优化总结 | 中 | 否 | 中 | 是 | 归档 |

### `docs/06-历史记录`

| 文件 | 用途 | 一致性 | 维护 | 重复 | 历史 | 动作 |
|---|---|---|---|---|---|---|
| `README.md` | 历史目录索引 | 高 | 是 | 低 | 是 | 归档 |
| `README_全新系统.md` | 老启动说明 | 低 | 否 | 高 | 是 | 归档 |
| `全新系统部署总结.md` | 部署总结 | 中 | 否 | 中 | 是 | 归档 |
| `根目录整理总结.md` | 历史整理记录 | 中 | 否 | 中 | 是 | 归档 |
| `项目文件整理总结.md` | 历史整理记录 | 中 | 否 | 中 | 是 | 归档 |
| `3D矿区场景升级说明.md` | 历史升级说明 | 中 | 否 | 中 | 是 | 归档 |
| `矿区场景仿真升级说明.md` | 历史升级说明 | 低 | 否 | 高 | 是 | 归档 |
| `CHANGELOG_维护功能.md` | 功能总结 | 中 | 否 | 中 | 是 | 归档 |
| `CHANGELOG_设备分组功能.md` | 功能总结 | 中 | 否 | 中 | 是 | 归档 |
| `MyEMS资源调研与3D模型建议.md` | 参考调研 | 中 | 否 | 低 | 是 | 归档 |

### `docs/07-快速参考`

| 文件 | 用途 | 一致性 | 维护 | 重复 | 历史 | 动作 |
|---|---|---|---|---|---|---|
| `README.md` | 速查目录索引 | 中 | 是 | 中 | 否 | 保留 |
| `根目录结构说明.md` | 仓库结构速查 | 高 | 是 | 低 | 否 | 保留 |
| `快速参考-统一设备管理.md` | 设备管理速查 | 低 | 否 | 高 | 否 | 合并 |
| `本地开发快速参考.md` | 本地开发速查 | 中 | 否 | 高 | 否 | 合并 |
| `清除多能源管理页面数据指南.md` | 数据清理速查 | 中 | 否 | 高 | 否 | 合并 |
| `开始使用-执行清单.md` | 旧 checklist | 低 | 否 | 高 | 是 | 删除候选 |
| `项目水平与求职定位.md` | 求职语境说明 | 高 | 否 | 低 | 是 | 删除候选 |

### `docs/guides` 与 `docs/plans`

| 文件 | 用途 | 一致性 | 维护 | 重复 | 历史 | 动作 |
|---|---|---|---|---|---|---|
| `docs/guides/README.md` | 规范目录入口 | 高 | 是 | 低 | 否 | 保留 |
| `docs/guides/frontend-guidelines.md` | 前端协作规范 | 高 | 是 | 低 | 否 | 保留 |
| `docs/guides/backend-guidelines.md` | 后端协作规范 | 高 | 是 | 低 | 否 | 保留 |
| `docs/guides/文档体系规范.md` | 文档治理规范 | 高 | 是 | 低 | 否 | 保留 |
| `docs/guides/变更计划规范.md` | 计划治理规范 | 高 | 是 | 低 | 否 | 保留 |
| `docs/plans/README.md` | 计划目录入口 | 高 | 是 | 低 | 否 | 保留 |
| `docs/plans/TEMPLATE.md` | 计划模板 | 高 | 是 | 低 | 否 | 保留 |
| `docs/plans/current-status.md` | 当前状态 | 高 | 是 | 低 | 否 | 保留 |
| `docs/plans/handoff.md` | 当前交接 | 高 | 是 | 低 | 否 | 保留 |
| `docs/plans/PLAN-20260327-文档体系建设.md` | 已完成计划 | 高 | 否 | 低 | 是 | 归档 |
| `docs/plans/device-manager-analysis.md` | 专题分析 | 高 | 否 | 低 | 是 | 归档 |
| `docs/plans/document-audit.md` | 当前审计报告 | 高 | 是 | 低 | 否 | 保留 |

