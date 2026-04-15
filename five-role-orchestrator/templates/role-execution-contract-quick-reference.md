# 角色执行协议速查表

本文件用于给 `role-execution-contract-template.md` 提供常用填充值参考，帮助总控层快速生成五角色交棒协议。

注意：

- 这是速查表，不是角色正文替代品。
- 优先复用仓库现有 `AGENTS.md`、`docs/guides/*`、`docs/plans/*` 中已存在的规则来源。
- 若当前任务已有更明确的主题边界、PLAN 约束或主区结论，应以当前任务上下文为准。

## 预判

- 常见 `required_reads`
  - `AGENTS.md`
  - `docs/plans/current-status.md`
  - `docs/plans/handoff.md`
  - 当前主题 `PLAN-*.md`

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

- 常见 `writeback_owner`
  - 预判角色默认负责回写 `current-status.md`
  - 预判角色默认负责回写 `handoff.md`

- 常见 `stop_conditions`
  - 根因仍不清楚
  - 需要长期规则裁决
  - 已涉及 breaking change 或正式 PLAN 升级

- 常见 `schema_change_action`
  - 若已触及 schema 或接口契约调整，停止继续预判，升级到规则或后端边界判断

- 常见 `breaking_change_action`
  - 不自行批准，升级到规则并保留用户拍板点

- 常见 `topic_drift_action`
  - 若任务已不属于当前主主题，停止续跑并建议新开主题或升级正式 PLAN

- 常见 `retry_or_failure_threshold`
  - 连续两次最小验证仍不能收敛结论时，停止原路径并升级角色路径判断

- 常见 `default_next_role`
  - `前端`
  - `后端`
  - `规则`
  - `验收`

## 规则

- 常见 `required_reads`
  - `AGENTS.md`
  - `docs/plans/current-status.md`
  - `docs/plans/handoff.md`
  - 当前主题 `PLAN-*.md`
  - `docs/guides/five-thread-vibe-coding-framework.md`

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

- 常见 `writeback_owner`
  - 规则角色默认负责回写 `handoff.md`
  - 规则角色默认负责在边界变化时回写 `PLAN-*.md`
  - 若当前阶段、待办、风险变化明显，规则角色也应回写 `current-status.md`

- 常见 `acceptance_writeback_target`
  - 若本轮只锁边界，不写验收结论
  - 若本轮同时定义收口前提，可在 `PLAN-*.md` 与 `handoff.md` 中写明验收入口条件

- 常见 `stop_conditions`
  - 缺少事实依据，无法裁决
  - 发现仍需先回预判补证据
  - 命中高风险运行时契约变更

- 常见 `schema_change_action`
  - 判断是否允许当前主题继续承载；若会改变接口契约，必须更新 `PLAN-*.md`

- 常见 `breaking_change_action`
  - 默认不自动批准，要求用户拍板，并在主区/PLAN 中锁定兼容边界

- 常见 `topic_drift_action`
  - 若任务已漂移为新主题，应停止当前实现路径并要求新主题/新 PLAN 判断

- 常见 `retry_or_failure_threshold`
  - 连续两次规则裁决仍依赖缺失事实时，应交回预判，不继续空转

- 常见 `default_next_role`
  - `前端`
  - `后端`
  - `验收`

## 前端

- 常见 `required_reads`
  - `AGENTS.md`
  - `docs/plans/current-status.md`
  - `docs/plans/handoff.md`
  - 当前主题 `PLAN-*.md`
  - `docs/guides/frontend-guidelines.md`

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

- 常见 `writeback_owner`
  - 前端角色默认负责回写 `current-status.md`
  - 若仍需交接，前端角色默认负责回写 `handoff.md`

- 常见 `acceptance_writeback_target`
  - 前端不直接写最终验收结论
  - 只在 `handoff.md` 中写清“为什么可以交验收”

- 常见 `stop_conditions`
  - 发现接口契约不稳定
  - 发现任务已越出当前主题或非目标
  - 需要新增后端能力才能继续

- 常见 `schema_change_action`
  - 若前端实现要求新增/调整 schema，停止当前实现并交回后端/规则

- 常见 `breaking_change_action`
  - 不以 UI 兼容掩盖 breaking change，交回规则并等待拍板

- 常见 `topic_drift_action`
  - 若当前需求已变成新页面/新主题，不继续顺手扩写

- 常见 `retry_or_failure_threshold`
  - 连续两次最小验证仍失败，或失败原因已明显超出前端边界时，停止并交回预判/后端/规则

- 常见 `default_next_role`
  - `验收`
  - `后端`
  - `预判`
  - `规则`

## 后端

- 常见 `required_reads`
  - `AGENTS.md`
  - `docs/plans/current-status.md`
  - `docs/plans/handoff.md`
  - 当前主题 `PLAN-*.md`
  - `docs/guides/backend-guidelines.md`

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

- 常见 `writeback_owner`
  - 后端角色默认负责回写 `current-status.md`
  - 若仍需联调或验收，后端角色默认负责回写 `handoff.md`

- 常见 `acceptance_writeback_target`
  - 后端不直接写最终验收结论
  - 只在 `handoff.md` / `PLAN-*.md` 中写清接口边界与联调注意项

- 常见 `stop_conditions`
  - 发现需要重锁边界
  - 发现需要用户拍板的 breaking change
  - 发现问题本质并不属于后端

- 常见 `schema_change_action`
  - 若 schema 变化会影响接口契约、前端消费或长期复用，必须同步更新 `PLAN-*.md` 或交规则锁边界

- 常见 `breaking_change_action`
  - 默认停机并升级到规则；无明确拍板不继续推进

- 常见 `topic_drift_action`
  - 若问题已从局部接口修复漂移成新主题能力，不继续在当前轮顺手扩张

- 常见 `retry_or_failure_threshold`
  - 连续两次最小验证仍失败，且失败原因涉及边界或契约不稳时，停止并升级角色路径判断

- 常见 `default_next_role`
  - `验收`
  - `前端`
  - `预判`
  - `规则`

## 验收

- 常见 `required_reads`
  - `AGENTS.md`
  - `docs/plans/current-status.md`
  - `docs/plans/handoff.md`
  - 当前主题 `PLAN-*.md`
  - `docs/guides/ai-collaboration-sop.md`

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

- 常见 `writeback_owner`
  - 验收角色默认负责回写 `current-status.md`
  - 验收角色默认负责回写 `handoff.md`
  - 若阶段状态或收口判断变化，验收角色也应回写当前 `PLAN-*.md`

- 常见 `acceptance_writeback_target`
  - 阶段验收结论至少写入 `current-status.md`
  - 若影响正式主题状态或收口判断，也应写入 `PLAN-*.md`
  - 若仍需接棒，需在 `handoff.md` 写清下一角色与打回原因

- 常见 `stop_conditions`
  - 关键验证缺失
  - 当前证据不足以支撑通过或收口
  - 当前结论仍依赖规则裁决

- 常见 `schema_change_action`
  - 若验收发现 schema/契约已变且未被规则锁定，停止验收并打回规则或后端

- 常见 `breaking_change_action`
  - 若发现未拍板的 breaking change，默认不通过并打回规则/后端

- 常见 `topic_drift_action`
  - 若当前行动项已脱离本主题，停止正式收口判断并交回规则/预判

- 常见 `retry_or_failure_threshold`
  - 连续两次验收仍因同一类证据缺失失败时，应显式升级路径，不继续模糊打回

- 常见 `default_next_role`
  - `前端`
  - `后端`
  - `预判`
  - `规则`
  - `收口 / archive 判断`
