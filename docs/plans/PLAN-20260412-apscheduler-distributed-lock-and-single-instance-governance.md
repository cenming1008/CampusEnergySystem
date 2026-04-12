# PLAN-20260412-APScheduler-分布式锁与单实例调度治理专题

> 状态：已阶段收口，暂不迁 archive，等待下一个主主题 | 负责人：规则 / 后端角色 / 验收角色 | 更新时间：2026-04-12

## 1. 背景

当前 APScheduler 跟随 API 进程启动，默认任务包括：

- `auto_train_lstm`
- `auto_update_forecasts`
- `auto_cleanup_data`

当前实现中不存在任何跨实例互斥。单实例默认部署下，这个风险偏潜伏；但在 `WORKERS > 1`、多实例部署或滚动重叠时，会显性化为同一批 job 被重复调度。

当前风险优先级排序为：

1. `auto_train_lstm`
2. `auto_update_forecasts`
3. `auto_cleanup_data`

当前最适合复用的协调基础设施是 Redis，因此第一轮不做复杂调度平台化，而是优先建立最小 owner 级互斥。

## 2. 目标

- 在多实例 / 多 worker / 滚动重叠场景下，保证只有一个实例实际启动 scheduler。
- 让非 owner 实例明确处于 `standby / skipped` 状态，而不是“看起来也启动成功”。
- 在生产环境中，Redis 不可用时默认采用 `fail-closed`，避免误启动多个 scheduler。
- 通过显式配置开关收敛 scheduler 启停与模式选择。

## 3. 第一轮最小可控范围

第一轮只允许处理：

- [lifecycle.py](/Users/todo/CampusEnergySystem/app/core/lifecycle.py)
- [scheduler_service.py](/Users/todo/CampusEnergySystem/app/services/scheduler_service.py)
- [scheduler_registry.py](/Users/todo/CampusEnergySystem/app/services/scheduler_registry.py)
- [settings.py](/Users/todo/CampusEnergySystem/app/core/settings.py)
- [redis.py](/Users/todo/CampusEnergySystem/app/core/redis.py)
- [runtime_state.py](/Users/todo/CampusEnergySystem/app/core/runtime_state.py)
- 必要时 [forecast/admin.py](/Users/todo/CampusEnergySystem/app/api/endpoints/forecast/admin.py) 中与状态暴露直接相关的最小联动
- [current-status.md](/Users/todo/CampusEnergySystem/docs/plans/current-status.md)
- [handoff.md](/Users/todo/CampusEnergySystem/docs/plans/handoff.md)

第一轮目标只限于：

- scheduler owner 级互斥
- Redis lease lock
- owner / standby / skipped / failed-closed 状态明确
- 显式配置开关

## 4. 第一轮职责边界

后端职责边界：

- 在应用启动阶段决定当前实例是否有资格启动 scheduler
- 使用 Redis lease lock 完成 owner 的 acquire / renew / release
- 让非 owner 实例跳过 scheduler 启动并写入运行状态
- 增加显式配置开关控制 scheduler 是否启用、采用何种模式
- 在关闭阶段释放 owner 租约

前端职责边界：

- 第一轮默认不启动

规则职责边界：

- 只锁主题、范围、配置口径、冻结边界、回滚点与验收口径

## 5. 配置口径

第一轮建议新增显式开关：

- `SCHEDULER_ENABLED`
- `SCHEDULER_MODE`

建议模式至少覆盖：

- `off`：完全关闭 scheduler
- `local`：本地单实例直启
- `redis_owner`：通过 Redis lease lock 竞争 owner

生产默认建议：

- 使用 `redis_owner`
- Redis 不可用时 `fail-closed`

## 6. 第一轮明确不应纳入的内容

- 不做 per-job distributed lock
- 不做 APScheduler jobstore 持久化
- 不做独立调度服务拆分
- 不做预测写入全量幂等体系改造
- 不做训练任务内部的更细粒度互斥改造
- 不把第一轮扩大为完整调度平台重构

## 7. 冻结边界

- 第一轮只解决 scheduler owner 级互斥，不处理每个 job 的细粒度分布式锁。
- 不引入 APScheduler jobstore 持久化或数据库持久化调度状态。
- 不将 scheduler 从 API 进程中拆为独立服务。
- 不顺手改造预测写入、清理任务、训练任务的幂等体系。
- 不把 Redis lease lock 延展成全局任务协调框架。

## 8. 回滚边界

- 若 owner 级互斥实现后导致 scheduler 无法稳定启动、无法稳定续租或关闭时无法明确释放租约，应整轮回退到当前单实例直启状态。
- 若实现中发现 Redis lease lock 方案无法在现有启动路径中稳定成立，应停止第一轮并回到规则角色重新锁方案。
- 若实现开始波及 per-job lock、jobstore 持久化或独立调度服务拆分，应立即回退到第一轮范围。

## 9. 验收口径

第一轮验收至少应核对：

- 多实例下是否只有一个实例实际启动 scheduler
- 非 owner 实例是否明确暴露 `standby / skipped` 状态
- Redis 不可用时生产默认是否为 `fail-closed`
- 显式配置开关是否已存在，且 `enabled / mode` 口径清晰
- 本轮是否仍严格停留在 owner 级互斥，没有越界到：
  - per-job distributed lock
  - APScheduler jobstore 持久化
  - 独立调度服务拆分
  - 预测写入幂等体系重构

## 10. 推荐角色路径

- `规则 -> 后端 -> 验收`

## 11. 进度记录

- 2026-04-12：已确认 APScheduler 当前跟随 API 进程启动，默认任务为 `auto_train_lstm`、`auto_update_forecasts`、`auto_cleanup_data`，且不存在跨实例互斥。
- 2026-04-12：已正式建立 `APScheduler 分布式锁与单实例调度治理专题`，并锁定第一轮只做 Redis lease lock + owner 级互斥。
- 2026-04-12：第一轮已验收通过，Redis lease lock 已成为 scheduler 启动前置条件，`owner / standby / skipped / failed-closed` 与健康状态已明确暴露。
- 2026-04-12：已完成阶段收口判断；当前没有足够明确、足够独立的后续最小可控范围，本主题退出主区、暂不迁 archive，保留在 `docs/plans/` 作为近期成果主题。

## 12. 阶段收口结论

- 已确认本主题达到阶段收口条件。
- 已确认不再默认启用后续轮次。
- 已确认本主题退出主区，但暂不迁 archive。
- 已确认当前主区应切换为“等待下一个主主题”。
