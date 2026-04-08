# PLAN-20260407 Application Use Case 分层收口专题

> 状态：第三轮验收通过，进入阶段收口判断 | 负责人：规范线程 | 更新时间：2026-04-07

## 背景

当前仓库已经在 `app/application/` 下形成了一批 use case 入口，覆盖：

- `device_reporting`
- `analysis`
- `reporting`
- `energy_management`
- `telemetry_ingestion`
- `forecasting`

其中 [app/application/README.md](/Users/todo/CampusEnergySystem/app/application/README.md) 已明确：

- `endpoint` 负责协议适配
- `application` 负责 use case 编排
- `service` 提供稳定业务能力

但在本专题启动时，`inspection`、`maintenance`、`devices management`、`users` 仍大量保留 `endpoint -> service` 直连，访问前置、默认值兜底、审计触发点和主流程编排散落在端点层。

当前主题不属于此前主区主题“文档与代码入口口径收敛专题”，应独立按后端分层治理立项推进。

## 目标

- 将需要主流程编排价值的后端主路径继续收口到 `application/use case` 层。
- 让 endpoint 尽量只保留协议转换职责。
- 保持 service 继续承担稳定业务能力，不吸入 HTTP 细节。
- 在不改对外 API 契约的前提下，分轮推进最小闭环。

## 职责边界

### endpoint

- HTTP 参数解析
- Depends 注入
- Query/Path/Body 到 use case 入参映射
- 状态码 / 响应模型 / 文件响应
- 极薄的异常翻译

endpoint 不应继续承担：

- 访问前置主流程编排
- 多 service 协作
- 默认值兜底
- 审计触发点分散落点
- 控制命令触发编排

### application / use case

- 以“用户意图 / 主流程”命名和收口
- 负责访问前置
- 负责主流程编排
- 负责多 service 协作
- 负责默认值兜底
- 负责审计触发点统一
- 负责稳定结果对象或稳定返回口径

application / use case 不允许：

- 长成新的大 service 层
- 承担 HTTP 细节
- 变成纯透传壳函数

### service

- 提供稳定业务能力
- 保留资源读写、状态变化、规则校验、统计计算
- 不承担 HTTP 细节
- 不承担完整 endpoint 工作流编排

## 样板保留策略

- `reports` 继续作为当前 application/use case 分层样板保留。
- 本专题不重做 `reports`。
- 后续模块收口应优先向 `reporting` 的调用链对齐，而不是反向改写样板。

## 第一轮范围与结论

第一轮固定范围：

- `inspection`
- `maintenance`

第一轮已完成并通过验收：

- 已新增 `app/application/inspection.py`
- 已新增 `app/application/maintenance.py`
- 已将 `inspection` / `maintenance` 中具有主流程价值的访问前置、默认值、审计和编排从 endpoint 收回 use case
- 已保持对外 API 契约兼容
- 已确认 service 未吸入 HTTP 细节

第一轮不再继续扩张，也不回头重做，作为当前主题的已通过阶段保留。

## 第二轮范围

第二轮固定范围仅限：

- [app/api/endpoints/devices/management.py](/Users/todo/CampusEnergySystem/app/api/endpoints/devices/management.py)
- 对应新增或扩展的 `app/application/` 下 devices management use case

第二轮允许后端线程收口的动作仅聚焦：

- 列表 / 详情访问收口（仅在确有主流程价值时）
- `smart create`
- `update`
- `delete`
- `toggle_device_status`
- 与审计、默认值、控制命令触发相关的主流程编排

第二轮必须保持：

- 对外 API 路径不变
- 请求参数不变
- 响应模型与返回契约不变

## 第二轮非目标

- 不处理 `users`
- 不重做 `reports`
- 不回头重构第一轮 `inspection + maintenance`
- 不做 repository 重构
- 不做 domain 重构
- 不做 auth / token / session 重构
- 不做 frontend 联动改造
- 不修改外部 API 路径、请求参数、响应模型契约

## 禁止扩张项

- 不把第二轮扩大到 `users` 或其他 endpoint 模块
- 不为“分层更漂亮”而顺手做全仓 service 清洗
- 不新增纯透传 use case 壳函数
- 不把 application 层扩成新的“大 service 层”
- 不把控制命令发布、审计或访问控制重新做成新的基础设施改造专题
- 不借第二轮顺手做 MQTT、auth、repository、domain 或前端联动重构

## 第二轮打回条件

- `devices management` endpoint 仍保留明显主流程编排，未真正变薄
- 新增 use case 只是 endpoint 到 service 的空壳透传
- MQTT 控制命令触发、审计、访问前置、默认值等关键主流程仍散落在 endpoint
- service 吸入了 HTTP 细节、响应对象或状态码语义
- 改动越界到 `users`、`reports`、第一轮模块或其他非目标模块
- 需要改外部 API 契约才能完成收口，但未先回主区补充拍板

## 第二轮验收口径

- `devices management` endpoint 是否明显变薄
- application/use case 是否真正承担主流程编排，而非空壳透传
- MQTT 控制命令触发、审计、访问前置、默认值等是否从 endpoint 收回 use case
- service 是否未吸入 HTTP 细节
- 本轮是否未越界到 `users` 或其他模块
- `reports` 样板是否继续保持不动
- 对外 API 契约是否保持兼容

## 第二轮验收结论

第二轮已完成并通过验收：

- 已新增 [app/application/device_management.py](/Users/todo/CampusEnergySystem/app/application/device_management.py)
- [app/api/endpoints/devices/management.py](/Users/todo/CampusEnergySystem/app/api/endpoints/devices/management.py) 中具有主流程价值的写操作已委托 use case
- `toggle_device_status` 的访问前置、默认原因、MQTT 控制命令触发与审计已统一收口
- 读接口仍保留在 endpoint 轻量层，未为了分层一致性硬拆空壳 use case
- 已通过第二轮 use case 与 endpoint 收口测试
- 已确认本轮未越界到 `users`、`reports`、第一轮模块或其他非目标模块

第二轮作为已通过阶段保留，不再继续扩张，也不回头重做。

## 第三轮范围

第三轮建议范围仅限：

- [app/api/endpoints/users.py](/Users/todo/CampusEnergySystem/app/api/endpoints/users.py)
- 对应新增或扩展的 `app/application/` 下 users use case

第三轮建议继续保持“一轮只收一个模块”的节奏，本轮只优先处理 `users`，不与其他模块并行打包。

第三轮允许后端线程收口的动作仅聚焦：

- `list_users`
- `create_user`
- `update_user_role`
- `update_user_status`
- `update_user_location_scope`
- `change_user_password`
- `revoke_user_sessions`
- `set_force_password_reset`
- `unlock_user`
- `change_my_password`
- `get_me` 仅在确有稳定主流程价值时再判断是否收口，不为分层一致性硬拆空壳 use case

第三轮必须保持：

- 对外 API 路径不变
- 请求参数不变
- 响应模型与返回契约不变

## 第三轮非目标

- 不处理 `inspection`
- 不处理 `maintenance`
- 不回头重做第二轮 `devices management`
- 不重做 `reports`
- 不做 auth / token / session 重构
- 不做 legacy 兼容治理
- 不做 repository 重构
- 不做 domain 重构
- 不做 frontend 联动改造
- 不修改外部 API 路径、请求参数、响应模型契约

## 第三轮冻结边界与打回条件

第三轮冻结边界：

- `auth / token / session` 明确冻结，不因 `users` 收口而顺带扩张
- legacy 兼容治理明确冻结，不把历史兼容路径清理纳入本轮
- 前两轮样板明确冻结，不回头重做

第三轮打回条件：

- `users` endpoint 仍明显保留主流程编排，未真正变薄
- 新增 users use case 只是 endpoint 到 service 的空壳透传
- 审计、访问前置、默认值、会话吊销等关键主流程仍散落在 endpoint
- service 吸入 HTTP 细节、响应对象或状态码语义
- 改动越界到 auth / token / session、legacy 兼容治理或其他非目标模块
- 需要改外部 API 契约才能完成收口，但未先回主区补充拍板

## 第三轮验收口径

- `users` endpoint 是否明显变薄
- application/use case 是否真正承担主流程编排，而非空壳透传
- 审计、访问前置、默认值、会话吊销等是否从 endpoint 收回 use case
- service 是否未吸入 HTTP 细节
- 本轮是否未越界到 auth / token / session、legacy 兼容治理或其他模块
- 对外 API 契约是否保持兼容

## 第三轮验收结论

第三轮已完成并通过验收：

- 已新增 `app/application/users.py`
- `users` 中具有主流程价值的写操作、列表审计与会话吊销已委托 use case
- `get_me` 继续保留在 endpoint 轻量层，未为了分层一致性硬拆空壳 use case
- 已通过第三轮 use case 与 endpoint 收口测试
- 已确认本轮未越界到 auth / token / session、legacy 兼容治理或其他非目标模块

第三轮作为已通过阶段保留，不再继续扩张，也不回头重做。

## 阶段收口判断

当前主题已完成三轮已验证的、边界清晰的后台管理主流程收口：

- 第一轮：`inspection + maintenance`
- 第二轮：`devices management`
- 第三轮：`users`

当前三轮样板已经覆盖了本主题最核心的目标：

- 后台管理主流程向 `application/use case` 层收口
- endpoint 明显变薄
- service 保持稳定业务能力层
- 不通过“风格统一”强拆空壳 use case

当前剩余候选任务已不再具备足够明确、足够收敛的第四轮目标，主要原因是：

- 剩余任务边界开始明显靠近 `auth / token / session`
- 容易滑向 legacy 兼容治理
- 容易扩张到 repository / domain 层重构
- 缺乏像前三轮那样清晰、低争议、可独立验收的单模块目标

因此当前不建议默认惯性进入第四轮实现。

## 当前结论

- 建议执行一次“阶段收口”
- 当前主题暂不迁入 archive
- 当前 PLAN 继续保留在 `docs/plans/`，作为近期成果主题与后续重启时的执行依据
- 只有当后续出现新的、单模块、边界清晰、不会自然滑向 auth / token / session / legacy / repository / domain 的候选目标时，再考虑重启下一轮

## 推荐路径

- 当前主题在阶段收口判断后的推荐路径为：`规范 -> 验收`

## 默认接棒

- 当前不默认继续进入第四轮实现
- 下一棒建议交验收线程或主题治理收尾动作，确认阶段收口并决定后续是否切换下一个主主题
