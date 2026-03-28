本模板用于输出“阶段验收 / 正式收口 / 归档判断”的统一结构，适合验收线程或总控线程复用。

# 当前验收结论

- 当前验收类型：{{acceptance_type}}
- 当前结论：{{acceptance_result}}
- 结论原因：{{acceptance_reason}}

# 当前主题状态

- 是否继续保留当前主题：{{keep_current_topic}}
- 当前是否仍作为执行依据：{{still_execution_basis}}
- 当前是否仍需正式 PLAN：{{keep_plan}}
- 当前是否仍需保留 analysis：{{keep_analysis}}

# 当前收口判断

- 是否达到阶段完成：{{stage_complete}}
- 是否达到正式收口条件：{{ready_for_closure}}

# 当前归档判断

- 是否迁 archive：{{move_to_archive}}
- 建议迁移文件：{{archive_targets}}

# 下一步

- 下一棒线程：{{next_thread}}
- 下一步建议：{{next_step}}

# 剩余风险

- 风险列表：{{risks}}
