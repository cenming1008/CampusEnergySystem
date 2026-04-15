# 角色执行协议速查表

本文件用于给 `role-execution-contract-template.md` 提供常用填充值参考，帮助总控层快速生成五角色交棒协议。

注意：

- 这是速查表，不是角色正文替代品。
- 优先复用仓库现有 `AGENTS.md`、`docs/guides/*`、`docs/plans/*` 中已存在的规则来源。
- 若当前任务已有更明确的主题边界、PLAN 约束或主区结论，应以当前任务上下文为准。

## 预判

- 常见 `allowed_actions`
  - 阅读主区与必要代码
  - 判断归属、路径与最小修复方案
  - 做最小验证性检查
  - 回写 `current-status.md` 与 `handoff.md`

- 常见 `forbidden_actions`
  - 不直接展开大规模实现
  - 不扩写长期规则
  - 不把验证性修改扩成正式实现

- 常见 `minimum_validation`
  - 结论有文档或代码证据支撑
  - 已明确下一角色
  - 已说明是否需要升级到规则 / 验收 / 实现

- 常见 `required_writeback_docs`
  - `docs/plans/current-status.md`
  - `docs/plans/handoff.md`

- 常见 `stop_conditions`
  - 根因仍不清楚
  - 需要长期规则裁决
  - 已涉及 breaking change 或正式 PLAN 升级

- 常见 `default_next_role`
  - `前端`
  - `后端`
  - `规则`
  - `验收`

## 规则

- 常见 `allowed_actions`
  - 锁主题、范围、非目标、术语、对象边界
  - 判断是否升级为正式 `PLAN`
  - 更新 guide / PLAN / 主区中的必要规则性内容

- 常见 `forbidden_actions`
  - 不直接展开前后端实现
  - 不借机扩写重型治理文档
  - 不在证据不足时扩大主题

- 常见 `minimum_validation`
  - 当前主题与边界已稳定
  - 下一角色可直接接棒
  - 已明确是否需要用户拍板

- 常见 `required_writeback_docs`
  - `docs/plans/current-status.md`
  - `docs/plans/handoff.md`
  - 当前主题 `PLAN-*.md`
  - 必要时 `docs/guides/*`

- 常见 `stop_conditions`
  - 缺少事实依据，无法裁决
  - 发现仍需先回预判补证据
  - 命中高风险运行时契约变更

- 常见 `default_next_role`
  - `前端`
  - `后端`
  - `验收`

## 前端

- 常见 `allowed_actions`
  - 修改页面、组件、状态、路由、交互、接口消费
  - 做最小前端验证
  - 回写主区文档

- 常见 `forbidden_actions`
  - 不顺手改后端逻辑
  - 不擅自重定义接口语义
  - 不扩大成无依据的页面重构

- 常见 `minimum_validation`
  - 至少完成构建、类型检查或最小单测中的必要项
  - 已确认页面行为或文案收敛生效
  - 已明确是否仍需后端接棒

- 常见 `required_writeback_docs`
  - `docs/plans/current-status.md`
  - `docs/plans/handoff.md`
  - 必要时当前主题 `PLAN-*.md`

- 常见 `stop_conditions`
  - 发现接口契约不稳定
  - 发现任务已越出当前主题或非目标
  - 需要新增后端能力才能继续

- 常见 `default_next_role`
  - `验收`
  - `后端`
  - `预判`
  - `规则`

## 后端

- 常见 `allowed_actions`
  - 修改接口、schema、service、权限、返回结构、空值处理
  - 做最小后端验证
  - 回写主区文档

- 常见 `forbidden_actions`
  - 不顺手改前端页面逻辑
  - 不无依据扩大 schema 或 service 重构
  - 不默认引入 breaking change

- 常见 `minimum_validation`
  - 至少完成相关测试、最小接口验证或静态检查中的必要项
  - 已确认兼容边界
  - 已明确前端是否需要继续联调

- 常见 `required_writeback_docs`
  - `docs/plans/current-status.md`
  - `docs/plans/handoff.md`
  - 必要时当前主题 `PLAN-*.md`

- 常见 `stop_conditions`
  - 发现需要重锁边界
  - 发现需要用户拍板的 breaking change
  - 发现问题本质并不属于后端

- 常见 `default_next_role`
  - `验收`
  - `前端`
  - `预判`
  - `规则`

## 验收

- 常见 `allowed_actions`
  - 对照 PLAN、主区和验证证据做阶段判断
  - 判断是否打回、是否继续保留主题、是否正式收口
  - 回写验收结论

- 常见 `forbidden_actions`
  - 不顺手修代码
  - 不绕过正式 PLAN 重定义验收标准
  - 不借验收名义自动开新主题

- 常见 `minimum_validation`
  - 已核对目标、非目标、验证结果与剩余风险
  - 已明确“通过 / 打回 / 收口”结论
  - 已明确下一棒角色或收口动作

- 常见 `required_writeback_docs`
  - `docs/plans/current-status.md`
  - `docs/plans/handoff.md`
  - 当前主题 `PLAN-*.md`
  - 必要时 `docs/plans/daily/*`

- 常见 `stop_conditions`
  - 关键验证缺失
  - 当前证据不足以支撑通过或收口
  - 当前结论仍依赖规则裁决

- 常见 `default_next_role`
  - `前端`
  - `后端`
  - `预判`
  - `规则`
  - `收口 / archive 判断`
