# PLAN-20260610 后端可靠性基线与渐进式解耦治理

> 状态：阶段 1 本地验收完成，远端 CI 待推送后验证；阶段 2 待立项 | 负责人：规则 -> 后端 -> 验收 | 更新时间：2026-06-12

---

## 背景

`后端架构分层审计与规范整理` 已完成审计库存、基础 import 护栏、能源 endpoint 拆分、审计查询下沉和多轮纯规则收口。最新全量审查表明，项目当前风险已从单文件职责泄漏升级为跨测试、CI、迁移、部署、MQTT 和事务边界的系统性问题：

- 全量 pytest 存在 4 个确定性失败，来源是 `AnalysisService` 调用已删除的 `CampusService._find_ancestor_location`。
- 后端 CI 仅手动触发，coverage 入口使用 `unittest discover`，漏掉 pytest 风格测试和部分架构护栏。
- Alembic 基线依赖当前模型动态建表，离线迁移链不能执行到 head。
- 生产部署脚本未显式执行 migration。
- MQTT processor 与 application 形成双向依赖和延迟导入循环。
- repository、service、application 和 integration 都存在事务提交点。
- application 直接 ORM、domain 依赖 ORM/settings/registry 等边界债务仍存在。

这些问题涉及部署、数据库状态、遥测接入、告警和数据一致性，必须按重量轮独立治理。

## 目标

- 恢复可信、自动、完整的后端测试与 CI 基线。
- 建立可验证的 Alembic 和部署迁移链。
- 消除 application 与 MQTT integration 的循环依赖。
- 建立“一次业务动作、一个事务所有者”的 Unit of Work 边界。
- 继续按单一职责泄漏点收敛 application、service、repository、domain 和 endpoint。
- 保持园区 EMS 产品方向及现有公开 API、MQTT topic 和主要数据契约兼容。

## 非目标

- 不一次性重写全部 service 或 repository。
- 不引入微服务、CQRS、通用事件总线或新的依赖注入框架。
- 不修改前端页面或前端状态逻辑。
- 不批量 rename 历史运行时标识。
- 不通过双写维持新旧遥测或告警路径。
- 不在一个实施轮次同时处理迁移、MQTT、事务和大型 service 拆分。

## 范围

重点涉及：

- `.github/workflows/backend-ci.yml`
- `requirements.txt`、开发依赖和 CI constraints
- `scripts/shell/run_backend_coverage.sh`
- `scripts/shell/deploy_prod.sh`
- `app/services/analysis_service.py`
- `app/application/telemetry_ingestion.py`
- `app/integrations/mqtt/`
- `app/repositories/`
- `app/services/device_group_service.py`
- `app/api/endpoints/device_groups.py`
- `migrations/`
- 后端架构、事务、迁移和运行语义测试

明确不改动：

- `frontend/`
- 现有 HTTP 路径和请求/响应 schema，除非 PLAN 明确记录运行正确性修复
- MQTT topic 和现有设备 payload alias
- 数据库名、容器名、环境变量键名和历史兼容标识

## 契约

- HTTP 路径与方法：保持不变。
- 请求与响应 schema：默认保持不变。
- MQTT topic：保持不变。
- MQTT payload alias：通过适配器和契约测试保留。
- readiness：依赖未就绪时由错误的 HTTP 200 修正为 HTTP 503。
- rate limit：由错误的 HTTP 500 修正为 HTTP 429。
- 设备分组批处理：保持 API shape，但写入语义修正为原子执行。
- 数据库迁移：保留 revision 历史；新库必须可从 base 升级到 head。

## 目标依赖方向

```text
HTTP / MQTT Consumer / Scheduler
                ↓
        Application Use Case
                ↓
      Service / Domain / Ports
                ↓
       Repository / Infrastructure
```

硬边界：

- application 不导入具体 endpoint 或 MQTT processor。
- integration 不决定告警生命周期或提交数据库事务。
- repository 新接口默认不 commit。
- domain 新代码不依赖 Session、ORM、settings、MQTT、Redis 或 HTTP。
- endpoint 不捕获所有异常并覆盖已有类型化错误语义。

## 实施阶段

### 阶段 1：可信测试与 CI 基线

状态：本地实现与独立验收已完成；远端 GitHub CI 运行证据待分支推送后补齐。

- 修复当前 4 个 pytest 回归。
- 统一 pytest 为本地、coverage 和 CI 的测试入口。
- CI 增加 push、pull_request 自动触发。
- 将 pytest、coverage、Ruff、Mypy 移入明确的开发依赖。
- 建立精确 CI constraints。
- 建立 Ruff 历史基线，只阻止新增问题。
- Ruff baseline writer 的有效变更只允许首次创建或收缩；检测到新增 finding 时拒绝写入。
- 根 README 的本地开发安装入口使用 `constraints-ci.txt`，与 CI 解析同一组依赖版本。
- 当前已知迁移失败在本阶段以显式非阻塞诊断保留，阶段 2 恢复为阻塞门禁。

执行依据：

- `docs/superpowers/plans/2026-06-10-backend-reliability-phase1.md`

### 阶段 2：迁移、部署与运行可靠性

- 将动态 Alembic 基线固化为确定性 schema snapshot。
- 修复离线迁移链。
- 使用临时 PostgreSQL 验证新库和代表性已有库升级。
- 部署启动前显式执行 `alembic upgrade head`。
- readiness 返回 503，rate limit 返回 429。
- 迁移验证恢复为 CI 阻塞门禁。

### 阶段 3：MQTT 依赖反转

- 引入协议无关 `TelemetryCommand`。
- decoder 仅负责 topic/payload 解析和字段映射。
- application use case 负责接入、幂等、告警和控制回执编排。
- replay 与 realtime 使用同一 application 工作流。
- 消除 application 与 MQTT integration 的循环依赖。

### 阶段 4：事务所有权与 Unit of Work

- application use case 持有事务。
- repository 使用同一 Session，只做持久化和 flush。
- 设备分组批处理改为单事务。
- 遥测接入形成单一 commit 点。
- 建立剩余内部 commit allowlist，并在后续切片中只减不增。

### 阶段 5：持续职责收敛

按顺序独立立项：

1. DeviceGroup 权限、workflow、repository 和统计边界。
2. application 直接 ORM 查询。
3. inspection / maintenance 大型 service。
4. domain 对 ORM、settings 和 registry 的依赖。
5. endpoint 宽泛异常捕获。

## 风险与回滚

- 风险：阶段 1 自动 CI 暴露既有迁移失败。
  - 应对：迁移步骤暂时改为明确的非阻塞诊断，阶段 2 必须恢复阻塞。
- 风险：固化基线后新库 schema 与已有库漂移。
  - 应对：阶段 2 比较 fresh-to-head 与 representative-existing-to-head schema。
- 风险：MQTT 解耦改变幂等、告警顺序或 replay 行为。
  - 应对：移动前建立实时、重复消息、失败消息、重放和控制回执契约测试。
- 风险：事务范围扩大造成锁时间增加。
  - 应对：解析和纯校验放在事务外，外部 I/O 放在 commit 后。
- 风险：兼容 wrapper 长期残留。
  - 应对：每个 wrapper 必须记录调用方、移除条件和对应 allowlist。

## 阶段门禁

| 进入条件 | 必须证据 |
| --- | --- |
| 进入阶段 2 | 全量 pytest 绿色；CI 与本地测试人口一致；Ruff 新增债务门禁生效 |
| 进入阶段 3 | 新库/已有库迁移验证通过；部署和运行状态码验收通过 |
| 进入阶段 4 | MQTT 循环消除；实时与 replay 契约测试通过 |
| 进入阶段 5 | UoW 试点通过；事务所有者和剩余 commit allowlist 已记录 |
| 主题收口 | 五阶段证据完成；剩余债务回到有边界的审计库存 |

## 验收标准

- [ ] 全量后端测试和架构护栏在 push / pull_request 自动执行并通过。
- [ ] 新 Ruff 违规会阻止合并，历史基线不会静默增长。
- [ ] 新库和代表性已有 PostgreSQL 数据库可迁移至 head。
- [ ] 部署在应用 ready 前完成 migration。
- [ ] application 与 MQTT integration 不存在循环依赖。
- [ ] 已治理 workflow 只有一个事务所有者。
- [ ] 设备分组批量写入具备原子性。
- [ ] 新代码不新增 application 直接 ORM、domain 基础设施依赖或 integration commit。
- [ ] API、MQTT topic 和主要业务行为保持兼容。

## 进度记录

- 2026-06-10：完成后端全量架构复核，综合判断为方向正确但可靠性与低耦合不足。
- 2026-06-10：用户批准“最终目标彻底治理、执行采用渐进路径”。
- 2026-06-10：设计文档通过审核，正式建立五阶段重量级治理主题。
- 2026-06-12：阶段 1 Task 1-7 初始本地验收基线提交为 `7355fb3c`；最终审查修复与最新本地验证提交为 `2ce60f08`。
- 2026-06-12：最终本地验证完成；compile 通过，依赖无破损，护栏 40 passed，Ruff 基线保持 168 findings，Mypy 配置范围 2 files 通过，全量 pytest 574 passed、3 warnings，coverage 73%（门槛 57%），`coverage.xml` 已生成，`git diff --check` 通过。
- 2026-06-12：远端 GitHub CI 尚未运行，保留为推送后的验收动作；Alembic migration 继续作为阶段 2 非阻塞债务，未提前修改 MQTT 或事务生产代码。

## 相关文档

- `docs/superpowers/specs/2026-06-10-backend-reliability-and-decoupling-design.md`
- `docs/superpowers/plans/2026-06-10-backend-reliability-phase1.md`
- `docs/plans/backend-architecture-audit-inventory.md`
- `docs/guides/backend-guidelines.md`
- `docs/guides/five-role-vibe-coding-framework.md`
