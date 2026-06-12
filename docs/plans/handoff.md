# Handoff

## 当前主题

- `后端可靠性基线与渐进式解耦治理`
- 正式 PLAN：`docs/plans/PLAN-20260610-backend-reliability-progressive-decoupling.md`
- 当前阶段：阶段 1 本地验收已通过，远端 GitHub CI 待推送后验证。
- Task 1-7 本地验收基线提交：`7355fb3c`。
- 最终审查修复与最新本地验证提交：`2ce60f08`。

## 已完成

- 修复 AnalysisService 祖先位置查询回归。
- 统一 pytest 为本地、coverage 和 CI 的测试入口。
- 拆分 runtime / development 依赖并建立精确 CI constraints。
- 建立 Ruff 历史基线与 no-new-debt gate。
- Ruff baseline writer 的有效变更只允许首次创建或收缩，含新增 finding 时拒绝写入。
- 根 README 的本地开发安装入口已使用 `constraints-ci.txt`，与 CI 解析同一组依赖版本。
- 完成自动 CI workflow、工具契约测试和本地独立验收。
- 本地证据：compile 通过，依赖无破损，护栏 40 passed，Ruff 168 findings unchanged，Mypy 2 files success，全量 pytest 574 passed、3 warnings，coverage 73% > 57% 且已生成 `coverage.xml`，`git diff --check` 通过。

## 下一棒

### 验收 / 集成角色

- 优先推送阶段 1 分支并核对远端 GitHub CI 实际运行证据。
- 核对 `push`、`pull_request`、`workflow_dispatch` 触发能力以及阻塞式 Trivy 扫描。
- 远端 CI 通过后，给出阶段 1 正式收口结论；若失败，只打回阶段 1 范围内的问题。

### 规则 / 预判角色

- 仅在阶段 1 远端 CI 证据通过后，建立阶段 2 migration inventory、技术设计与实施计划。
- 阶段 2 必须覆盖 fresh database、representative existing database、offline SQL、deploy migration、readiness 503 和 rate limit 429。

### 后端角色

- 阶段 2 正式设计和实施计划建立前，不修改 migration、部署、readiness 或 rate limit 生产逻辑。
- 不提前处理 MQTT 依赖反转、Unit of Work 或大型 service 拆分。

## 限制条件

- 保持 HTTP 路径、请求 / 响应 schema、MQTT topic 和主要业务行为兼容。
- Alembic migration 在阶段 1 CI 中仍是明确的 Phase 2 非阻塞诊断，不得写成已通过。
- Mypy 当前只覆盖配置中的 2 个文件，不得表述为全应用类型检查。
- 阶段 1 未修改 MQTT 或事务生产代码。

## 剩余风险

- 远端 GitHub CI 尚未运行，平台侧证据待补。
- Alembic migration 链仍不可信，必须在阶段 2 恢复为阻塞门禁。
- LibreSSL 与默认 `SECRET_KEY` 产生 3 条非阻塞测试警告。

## 交接结论

- 当前优先交接给验收 / 集成角色。
- 远端 CI 验收完成后，才交规则 / 预判角色准备阶段 2。
