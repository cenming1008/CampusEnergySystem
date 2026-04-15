本模板用于输出“下一棒 prompt”的统一骨架，适合总控角色在确定接棒对象后直接复制使用。

# 当前主题

- 当前主主题：{{current_topic}}

# 当前路径判断

- 当前角色路径：{{role_path}}
- 当前任务归属：{{task_judgement}}

# 下一棒角色

- 下一角色：{{next_role}}
- 交接原因：{{handoff_reason}}

# 当前允许范围

- 本轮允许动作：{{scope}}
- 本轮允许触达：{{allowed_targets}}

# 当前非目标

- 本轮不做：{{non_goals}}

# 当前风险

- 风险列表：{{risks}}

# 权限边界

- 本轮禁止动作：{{forbidden_actions}}
- 本轮禁止扩张：{{forbidden_expansion}}

# 验证协议

- 本轮最低验证：{{minimum_validation}}
- 必须记录的验证结果：{{validation_evidence}}
- 验证失败时处理：{{validation_failure_action}}

# 回写协议

- 必须回写文档：{{required_writeback_docs}}
- `current-status.md` 最少回写项：{{current_status_writeback}}
- `handoff.md` 最少回写项：{{handoff_writeback}}
- `PLAN-*.md` 更新条件：{{plan_update_conditions}}

# 停机 / 升级规则

- 必须停止并上交的条件：{{stop_conditions}}
- 升级到预判的条件：{{escalate_to_prejudge}}
- 升级到规则的条件：{{escalate_to_rules}}
- 升级到验收的条件：{{escalate_to_acceptance}}
- 需要用户拍板的事项：{{user_decision_points}}

# 本轮完成定义

- 本轮完成条件：{{done_definition}}
- 若未完成应如何交接：{{incomplete_handoff_rule}}

# 下一棒 prompt

{{next_role_prompt}}
