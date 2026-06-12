# Current Status

## 当前总目标

- 当前主主题：`后端可靠性基线与渐进式解耦治理`
- 当前总目标：先完成阶段 1 的远端 CI 验收与集成收口，再按正式设计进入阶段 2 的迁移、部署与运行可靠性治理。
- 当前执行依据：
  - `docs/plans/PLAN-20260610-backend-reliability-progressive-decoupling.md`
  - `docs/superpowers/specs/2026-06-10-backend-reliability-and-decoupling-design.md`
  - `docs/superpowers/plans/2026-06-10-backend-reliability-phase1.md`

---

## 当前阶段

- [x] 完成后端框架规范性、整齐度、可修改性和低耦合审查。
- [x] 完成阶段 1 可信测试、依赖、CI 与静态质量门禁实现。
- [x] 完成阶段 1 本地独立验收。
- [ ] 推送分支后核对远端 GitHub CI 运行证据。
- [ ] 远端 CI 通过后，由规则 / 预判角色建立阶段 2 迁移清单、设计与实施计划。

## 当前阻塞

- 无本地实现阻塞。
- 远端 GitHub CI 尚未运行，阶段 1 还缺推送后的远端验收证据。
- Alembic migration 验证仍是阶段 2 非阻塞债务，不阻塞阶段 1 本地结论。

## 当前待办

1. 由验收 / 集成角色推送当前阶段 1 分支并核对 `push`、`pull_request` 或 `workflow_dispatch` 的实际运行结果。
2. 若远端 CI 失败，只在阶段 1 范围内修复测试、依赖、CI 或质量门禁问题，不扩到 migration、MQTT 或事务治理。
3. 远端 CI 通过后，由规则 / 预判角色先建立阶段 2 的 migration inventory、技术设计和实施计划，再交后端实现。

## 当前验证结论

- Task 1-7 本地验收基线提交：`7355fb3c`。
- compile 通过。
- `pip check` 返回 `No broken requirements found`。
- 架构与工具护栏：36 passed。
- Ruff no-new-debt gate 通过，历史基线保持 168 findings。
- Mypy 配置范围内 2 files 通过；尚非全应用类型检查。
- 全量 pytest：570 passed、3 warnings。
- coverage：73%，高于 57% 门槛，且使用与本地一致的 pytest 测试人口。
- `git diff --check` 通过。
- 阶段 1 未修改 MQTT 或事务生产代码。

## 当前剩余风险

- 远端 GitHub CI 尚未运行，自动触发、缓存和安全扫描的实际平台证据待补。
- Alembic offline / fresh database / representative existing database 迁移链仍未恢复可信，必须在阶段 2 独立治理。
- 3 条非阻塞警告来自 LibreSSL 和测试环境默认 `SECRET_KEY`。
- MQTT 循环、事务所有权和大型 service 分层债务均未进入本阶段。

## 当前验收判断

- 阶段 1 本地实现与验收：通过。
- 阶段 1 远端 CI 验收：待推送后验证。
- 下一接手角色：验收 / 集成；远端证据完成后再交规则 / 预判角色准备阶段 2。
