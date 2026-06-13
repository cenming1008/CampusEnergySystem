# Current Status

## 当前总目标

- 当前主主题：`后端可靠性基线与渐进式解耦治理`
- 当前总目标：阶段 1 已正式收口；当前由规则 / 预判角色准备阶段 2A Alembic 链可信化设计与实施计划。
- 当前执行依据：
  - `docs/plans/PLAN-20260610-backend-reliability-progressive-decoupling.md`
  - `docs/superpowers/specs/2026-06-10-backend-reliability-and-decoupling-design.md`
  - `docs/superpowers/plans/2026-06-10-backend-reliability-phase1.md`
  - `docs/plans/backend-reliability-phase2-inventory.md`

## 当前阶段

- [x] 完成后端框架规范性、整齐度、可修改性和低耦合审查。
- [x] 完成阶段 1 可信测试、依赖、CI 与静态质量门禁实现。
- [x] 完成阶段 1 本地独立验收。
- [x] 完成远端 GitHub CI、Docker、Compose、Trivy 和 coverage artifact 验收。
- [x] 建立阶段 2 migration、部署和运行语义事实清单。
- [ ] 由规则角色确认阶段 2 拆分为 2A Alembic 链可信化、2B 部署与运行语义。
- [ ] 编写并批准阶段 2A 详细设计与实施计划。

## 当前阻塞

- 无阶段 1 阻塞。
- 阶段 2A 生产代码受设计门禁约束，尚未开始修改。
- 当前 migration 链的 fresh、offline 和 representative existing database 路径均不可信。

## 当前验证结论

- 阶段 1 最终提交：`1dfd2314`。
- 远端 `backend-ci` run：`27456526020`，结论 success。
- 远端全量 pytest：580 passed、1 warning。
- coverage：73%，已上传 `backend-coverage-xml` artifact。
- Ruff baseline：168 findings unchanged。
- Mypy 配置范围：2 files success。
- Docker image build 与 production Compose validation 通过。
- Trivy 阻塞式 HIGH / CRITICAL 扫描通过，Debian 与 Python packages 均 0 findings。
- 后端最低版本已统一为 Python 3.10+。

## 当前待办

1. 规则角色确认阶段 2A / 2B 拆分和契约边界。
2. 先为阶段 2A 编写正式设计，覆盖确定性基线、offline SQL、三类数据库 fixture、schema reconciliation 和 CI 阻塞门禁。
3. 设计获批后编写阶段 2A TDD 实施计划，并继续采用 Subagent-Driven 逐任务分派和逐项复核。
4. 阶段 2A 验收通过后，再建立阶段 2B 的部署与 HTTP 运行语义实施计划。

## 当前剩余风险

- `20260325_0001` 仍依赖当前 ORM metadata 动态建表。
- offline SQL 在 `20260412_0003` 稳定失败，后续多个 revision 仍有在线查询。
- Alembic head 不能证明现有库 schema 完整。
- 部署脚本未显式执行 migration，且使用 liveness 代替 readiness。
- readiness 失败仍返回 HTTP 200；全局 rate limit 仍可能返回 HTTP 500。
- GitHub Actions 提示 Node.js 20 action runtime 将被弃用，属于后续 CI 维护项，不阻塞阶段 1。

## 当前验收判断

- 阶段 1：通过并正式收口。
- 阶段 2 预判：完成。
- 下一接手角色：规则；设计批准后交后端。
