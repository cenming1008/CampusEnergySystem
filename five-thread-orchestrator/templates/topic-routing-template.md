本模板用于输出“主题判断 + 线程路径判断”的统一结构，适合总控线程直接套用。

# 当前调度目标

- 调度目标：{{routing_goal}}

# 当前任务判断

- 当前主主题：{{current_topic}}
- 是否属于当前主主题：{{belongs_to_current_topic}}
- 是否建议新开主题：{{should_create_new_topic}}
- 是否建议升级为正式 PLAN：{{should_upgrade_plan}}
- 是否需要用户拍板：{{needs_user_decision}}

# 当前路径判断

- 建议线程路径：{{thread_path}}
- 判断原因：{{reason}}
- 当前不应走的路径：{{not_recommended_paths}}

# 下一棒线程

- 下一线程：{{next_thread}}
- 交给它的原因：{{next_thread_reason}}
- 本轮边界：{{scope}}
- 本轮非目标：{{non_goals}}

# 人类拍板点

- 是否需要拍板：{{needs_user_decision}}
- 拍板事项：{{decision_items}}

# 当前风险

- 风险列表：{{risks}}

# 调度结论

- 当前结论：{{routing_conclusion}}
- 如果继续推进，下一步是什么：{{next_step}}
