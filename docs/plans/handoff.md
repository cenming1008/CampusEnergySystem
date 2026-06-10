# Handoff

## 当前主题

- `后端可靠性基线与渐进式解耦治理`
- 正式 PLAN：`docs/plans/PLAN-20260610-backend-reliability-progressive-decoupling.md`
- 设计：`docs/superpowers/specs/2026-06-10-backend-reliability-and-decoupling-design.md`
- 当前实施计划：`docs/superpowers/plans/2026-06-10-backend-reliability-phase1.md`

## 已知信息

- 用户已批准五阶段渐进治理路线。
- 阶段 1 只处理测试、CI、依赖和静态质量门禁，不处理迁移实现、MQTT 或事务重构。
- 当前 4 个 pytest 失败来自 `AnalysisService` 调用已删除的 `CampusService._find_ancestor_location`。
- 旧 coverage/CI 使用 `unittest discover`，漏掉 66 个 pytest 风格测试。
- 当前 Alembic offline upgrade 失败；阶段 1 只能保留显式非阻塞诊断，阶段 2 必须恢复为阻塞门禁。
- Ruff 历史债务不能在阶段 1 全量清零，应建立机器可比较的 baseline，只阻止新增问题。

## 下一棒

### 后端角色

- 严格按阶段 1 实施计划逐任务执行。
- 先使用现有失败测试修复 AnalysisService，再修改工程门禁。
- 不顺手处理 migration、readiness、MQTT、Unit of Work 或大型 service。
- 每个任务按计划独立提交。

### 验收角色

- 核对全量 pytest 零失败。
- 核对 coverage 与本地 pytest 使用相同测试人口。
- 核对 push / pull_request / workflow_dispatch 均可触发 CI。
- 核对 Ruff baseline 不允许新增或未同步移除的 finding。
- 核对 migration 仍明确标为 phase 2 debt，而不是被删除或声称通过。

### 规则 / 预判角色

- 阶段 1 通过后，再建立阶段 2 的 migration inventory、设计和实施计划。
- 阶段 2 必须覆盖 fresh database、representative existing database、offline SQL、deploy migration 和 readiness/rate-limit 状态码。

## 限制条件

- 保持 HTTP 路径、请求/响应 schema 和 MQTT topic 不变。
- readiness 503、rate limit 429 属于阶段 2 的运行正确性修复。
- 不使用双写维持新旧遥测路径。
- 不新增 application -> concrete MQTT processor 依赖。
- 不在没有独立计划的情况下调整 repository commit 默认值。

## 剩余风险

- CI 尚未实际在 GitHub 上运行，阶段 1 本地通过后仍需验收远端 workflow 证据。
- 当前 constraints 方案需在临时干净 venv 验证，避免只对现有开发环境有效。
- Ruff baseline 需要稳定归一化，避免单纯行号移动导致误报。
- 阶段 2 前 migration 仍不是可信门禁。
