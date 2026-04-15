本模板用于为五角色中的任一角色生成统一执行协议。它不是角色正文替代品，而是总控层在交棒时附带的最小 harness contract，用于补齐权限边界、验证要求、回写要求、停机规则与升级规则。

# 角色执行协议

## 基本信息

- 当前主主题：{{current_topic}}
- 当前角色：{{current_role}}
- 上一棒角色：{{previous_role}}
- 本轮目标：{{goal}}

## 权限边界

- 本轮允许动作：{{allowed_actions}}
- 本轮禁止动作：{{forbidden_actions}}
- 本轮允许触达文件/目录：{{allowed_targets}}
- 本轮禁止扩张项：{{forbidden_expansion}}

## 输入与依赖

- 必读文档：{{required_reads}}
- 当前执行依据：{{execution_basis}}
- 需要承接的已知结论：{{known_findings}}
- 缺失证据：{{missing_evidence}}

## 验证协议

- 本轮最低验证：{{minimum_validation}}
- 验证责任归属：{{validation_owner}}
- 必须产出的验证材料：{{validation_artifacts}}
- 必须记录的验证结果：{{validation_evidence}}
- 验证失败时处理：{{validation_failure_action}}
- 验证不足时处理：{{insufficient_validation_action}}
- 连续验证失败阈值：{{retry_or_failure_threshold}}

## 回写协议

- 必须回写文档：{{required_writeback_docs}}
- 回写责任归属：{{writeback_owner}}
- `current-status.md` 最少回写项：{{current_status_writeback}}
- `handoff.md` 最少回写项：{{handoff_writeback}}
- `PLAN-*.md` 更新条件：{{plan_update_conditions}}
- 验收结论写入位置：{{acceptance_writeback_target}}
- 本轮可不回写的条件：{{writeback_skip_conditions}}

## 停机规则

- 必须停止并上交的条件：{{stop_conditions}}
- 不得继续硬做的场景：{{no_force_continue_cases}}
- 遇到 schema 变更时动作：{{schema_change_action}}
- 遇到 breaking change 时动作：{{breaking_change_action}}
- 任务漂移到新主题时动作：{{topic_drift_action}}
- 命中停机后交回角色：{{stop_return_role}}

## 升级规则

- 升级到预判的条件：{{escalate_to_prejudge}}
- 升级到规则的条件：{{escalate_to_rules}}
- 升级到验收的条件：{{escalate_to_acceptance}}
- 需要用户拍板的事项：{{user_decision_points}}

## 完成定义

- 本轮完成条件：{{done_definition}}
- 完成后默认下一棒：{{default_next_role}}
- 若未完成应如何交接：{{incomplete_handoff_rule}}
