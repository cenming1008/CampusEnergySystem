# Backend Reliability Phase 2 Inventory

> 状态：预判完成，待规则角色确认阶段 2A 设计 | 日期：2026-06-13

## 目标

为 `后端可靠性基线与渐进式解耦治理` 阶段 2 建立可执行事实清单，覆盖迁移链、部署顺序、readiness 与 rate-limit 运行语义。

## 总体判断

阶段 2 不应一次同时修改迁移、部署和 HTTP 语义。建议拆为：

1. **阶段 2A：Alembic 链可信化**
2. **阶段 2B：部署顺序与运行状态码**

阶段 2A 先恢复数据库状态演进的可信验证；阶段 2B 再依赖该门禁接入生产部署和运行探针。

## Alembic Revision 清单

当前 revision 为单头线性链，head 为 `20260515_0011`：

| Revision | 职责 |
| --- | --- |
| `20260325_0001` | 动态加载当前 `SQLModel.metadata` 创建全部表，再补告警、MQTT、用户列和索引。 |
| `20260325_0002` | 增加 MQTT 重试字段和索引。 |
| `20260412_0003` | 增加 `energydata.reactive_power`。 |
| `20260412_0004` | 创建 SVG 配置、遥测和资产档案表。 |
| `20260412_0005` | 合并 SVG 参数字段并迁移配置数据。 |
| `20260414_0006` | 无操作占位 revision。 |
| `20260414_0007` | 增加并回填 `device_subtype`。 |
| `20260423_0008` | 删除历史 `prediction` 表。 |
| `20260424_0009` | 条件性补充电容器组监控和控制字段。 |
| `20260424_0010` | 增加 `device.archive_status` 和索引。 |
| `20260515_0011` | 条件性增加电容器组谐波 JSON 字段。 |

## 已确认的迁移风险

### Fresh Database

- `20260325_0001` 调用当前 `SQLModel.metadata.create_all`，同一 revision 会随模型变化。
- 当前模型已包含后续 revision 字段，fresh 升级会提前创建字段。
- `20260424_0010` 无条件增加 `archive_status`，在 fresh 链中可能触发 duplicate-column。

### Offline SQL

- `0001` 和 `0002` 在 offline 模式会输出重复 DDL。
- `0003` 在 `result.fetchone()` 处稳定失败。
- `0004/0005/0007/0008/0009/0011` 仍依赖实时连接或 inspector。
- 当前 CI 的 migration 步骤仍为 `continue-on-error`，不能作为合并门禁。

### Representative Existing Database

必须覆盖两种已有库：

1. 仅通过 migration 管理的历史库。
2. 曾启用 `create_all` 或 runtime schema sync 的漂移库。

已发现没有正式 migration 承载的结构：

- 电容补偿基础表。
- `storage_telemetry`。
- `alarm.instance_key`、`alarm.last_seen_at` 及相关索引。

仅检查 Alembic head 不足以证明 schema 完整。

## 当前部署与运行语义

现有生产部署顺序：

```text
发布前检查与备份
-> 本机构建镜像
-> 启动 backend
-> 启动 nginx
-> 固定等待
-> 请求 /health/live
```

缺口：

- 未执行 `alembic upgrade head`。
- `mqtt_ingest_worker` 未纳入同一次发布重建和重启。
- 成功探针使用 liveness，不验证数据库、Redis、MQTT 等依赖。
- HTTP 301 可能被误判为部署成功。

运行语义：

- `/health/ready` 在依赖失败时返回 `not_ready` payload，但 HTTP 仍为 200。
- 限流器抛出 429，但全局 middleware 边界会将其转换为通用 500。
- 现有测试主要直接调用函数，没有覆盖真实 ASGI 状态码。

## 推荐阶段边界

### 阶段 2A：Alembic 链可信化

- 将 `0001` 固化为确定性 PostgreSQL schema snapshot。
- 消除历史 revision 的 offline 实时查询。
- 兼容 runtime-sync 已提前创建字段的数据库。
- 新增 reconciliation revision，补齐没有 migration 承载的结构。
- 建立 fresh、纯 migration existing、runtime-sync existing 三类 PostgreSQL fixture。
- 比较规范化 schema，不只检查 revision number。
- 将 CI migration 验证恢复为阻塞门禁。

### 阶段 2B：部署与运行语义

- migration 在 backend 和 worker 启动前执行，失败则停止部署。
- 部署成功探针改为 `/health/ready` 且要求精确 HTTP 200。
- 保持 `/health/live` 只表达进程存活。
- `/health/ready` 在未就绪时返回 503，payload shape 不变。
- 全局 rate limit 返回 429，沿用现有 detail 契约。
- 将运行时 hypertable/schema DDL 移至 migration 或显式管理命令。

## 验收矩阵

- `alembic upgrade head --sql` 完整生成并可在临时 PostgreSQL 执行。
- fresh database 从 base 升级到 head。
- 两类 representative existing database 升级到 head，数据保留且 schema 对齐。
- 生产配置下 `init_db()` 不做通用建表或 schema 修补。
- migration 失败时 backend/worker 不启动。
- live 200；ready 成功 200；任一关键依赖失败时 ready 503。
- 全局限流通过真实 HTTP 请求返回 429。
- 部署探针拒绝 3xx 和固定 sleep 假成功。

## 关键文件

- `migrations/env.py`
- `migrations/versions/20260325_0001_industrial_baseline.py`
- `migrations/versions/20260412_0003_add_reactive_power.py`
- `migrations/versions/20260424_0010_add_device_archive_status.py`
- `app/core/database.py`
- `app/core/lifecycle.py`
- `app/api/endpoints/health.py`
- `app/core/rate_limit.py`
- `app/main.py`
- `scripts/shell/deploy_prod.sh`
- `.github/workflows/backend-ci.yml`

## 交接

- 下一角色：规则。
- 下一动作：确认先执行阶段 2A，再编写阶段 2A 详细设计与实施计划。
- 后端角色在详细设计和实施计划获批前不修改 migration、部署或运行语义生产代码。
