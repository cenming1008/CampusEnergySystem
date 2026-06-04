# Audit Endpoint Service Extraction Design

## Goal

把 `app/api/endpoints/audit.py` 中的审计事件 SQL 查询、分页计数和 summary 聚合下沉到 service 层，让 endpoint 只保留 HTTP 参数、依赖注入、响应模型与轻量序列化。

## Context

当前后端规范护栏已覆盖：

- domain 层不反向依赖外层。
- service 层不反向依赖 api/application。
- `DeviceMonitorService.get_monitor_overview()` 已回归 service 自有聚合能力。

继续扫描发现 `app/api/endpoints/audit.py` 仍直接：

- 构建 `select(AuditEvent)` 查询条件。
- 执行 `session.exec(...)`。
- 计算分页 total。
- 聚合近期 outcome/action summary。

这使 audit endpoint 比较厚，也不符合 endpoint “极薄 HTTP 适配”的方向。

## Scope

本轮修改范围：

- 新增 `app/services/audit_service.py`，承接审计事件查询、搜索分页和 summary 聚合。
- 修改 `app/api/endpoints/audit.py`，调用 `AuditService`，保留 `AuditEventResponse` 和 `_to_response(...)` 兼容测试入口。
- 新增测试证明 audit endpoint 委托 service，且 service 查询语义保持。
- 更新 `docs/plans/current-status.md`、`docs/plans/handoff.md` 和 daily 快照。

## Non-Goals

- 不修改审计 API 路径。
- 不修改请求参数、状态码或响应字段。
- 不改 `app/core/audit.py` 的写入逻辑。
- 不新增 application 层 audit use case，避免 application 承接 ORM 查询。
- 不重构所有仍含 SQL 的 endpoint，本轮只处理 audit。

## Architecture

目标分层：

- `api/endpoints/audit.py`：HTTP 参数、管理员依赖、`success_response` 包装、`AuditEventResponse` 序列化。
- `services/audit_service.py`：构建审计查询条件、分页查询、总数查询、summary 聚合。
- `core/audit.py`：继续负责审计写入与 details 值序列化。

## Testing

采用 TDD：

1. 先补 endpoint 委托 service 的测试，预期当前失败。
2. 先补 service 查询/summary 行为测试，按当前语义建立保护。
3. 新增 service 并改 endpoint。
4. 跑 audit 相关测试和 endpoint convergence 测试。

推荐验证：

```bash
./venv/bin/python -m pytest tests/test_audit.py tests/test_endpoint_application_convergence.py::TestEndpointApplicationConvergence::test_audit_events_endpoint_delegates_to_service -q
```

## Acceptance

- audit endpoint 不再直接执行 `session.exec(...)` 或构建 SQL statement。
- `AuditEventResponse` 和 `_to_response(...)` 兼容现有测试。
- audit events/search/summary 响应结构保持不变。
- 推荐验证命令通过。
