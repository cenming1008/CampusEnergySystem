# Handoff

## 当前主题

- `后端可靠性基线与渐进式解耦治理`
- 正式 PLAN：`docs/plans/PLAN-20260610-backend-reliability-progressive-decoupling.md`
- 阶段 1 已通过远端 CI 并正式收口。
- 当前切换至阶段 2 规则 / 预判工作。

## 阶段 1 最终证据

- 最终提交：`1dfd2314`。
- GitHub Actions：`backend-ci` run `27456526020` success。
- 580 tests passed，coverage 73%。
- Ruff baseline 168 unchanged，Mypy 配置范围 2 files success。
- Docker build、production Compose、阻塞式 Trivy 扫描通过。
- Trivy 报告中 Debian 与 Python packages 均为 0 findings。
- coverage artifact：`backend-coverage-xml`。

## 阶段 2 预判结论

- 事实清单：`docs/plans/backend-reliability-phase2-inventory.md`。
- 推荐拆分：
  - 阶段 2A：Alembic 链可信化。
  - 阶段 2B：部署顺序与 HTTP 运行语义。
- 不建议在一个实现轮次同时修改 migration、deploy、readiness 和 rate limit。

## 下一棒

### 规则角色

- 确认阶段 2A / 2B 拆分。
- 锁定阶段 2A 契约：
  - revision ID 和顺序保持不变；
  - fresh / offline / 两类 existing database 都必须验证；
  - schema 完整性不能只看 Alembic head；
  - CI migration 门禁恢复为 blocking。

### 后端角色

- 仅在阶段 2A 设计和实施计划获批后开始实现。
- 第一轮不修改 readiness、rate limit 或生产部署脚本。
- 按 TDD 建立 PostgreSQL fixtures、migration checker 和 reconciliation revision。

### 验收角色

- 核对 offline SQL 可生成并可执行。
- 核对 fresh、纯 migration existing、runtime-sync existing 三条升级路径。
- 核对数据保留、schema 对齐和 CI 阻塞门禁。

## 限制条件

- 保持 HTTP 路径、请求 / 响应 schema、MQTT topic 和主要业务行为兼容。
- 保留全部 Alembic revision ID 和历史顺序。
- 不通过直接 stamp 掩盖 schema 漂移。
- 不提前扩张到 MQTT 依赖反转、Unit of Work 或大型 service 拆分。
- 阶段 2B 前不修改部署和运行状态码生产逻辑。

## 剩余风险

- 动态 baseline 和 runtime schema sync 造成同 revision 不可复现。
- 多个模型结构没有正式 migration 承载。
- 部署未运行 migration，worker 可能继续运行旧代码。
- readiness 200 和 rate-limit 500 的错误语义尚未修复。
- GitHub Actions Node.js 20 runtime 弃用提示待后续维护。

## 交接结论

- 当前交接给规则角色确认阶段 2A 设计边界。
- 用户批准详细设计后，再交后端角色执行。
