# Backend Service Boundary Guardrails Design

## Goal

补齐后端 import 分层护栏，并收口当前唯一的 service -> application 反向依赖：`DeviceMonitorService.get_monitor_overview()` 不再从 service 层调用 `app.application.device_monitoring`。

## Context

上一轮已新增 domain 层反向依赖护栏，确认 `app/domain/*.py` 不 import `app.api`、`app.application`、`app.services` 或 `app.integrations`。继续扫描发现：

- `app/application` 当前没有 import `app.api`。
- `app/services` 当前唯一反向依赖是 `app/services/device_monitor_service.py` 中的 `from app.application.device_monitoring import get_device_monitor_overview_use_case`。
- `DeviceMonitorService.get_monitor_overview()` 被多处测试作为兼容入口调用，不能直接删除。

## Scope

本轮修改范围：

- 扩展 `tests/test_backend_layer_boundaries.py`，禁止 `app/services/**/*.py` import `app.api` 或 `app.application`。
- 将监控 overview 聚合逻辑放回 `DeviceMonitorService.get_monitor_overview()`。
- 将 `get_device_monitor_overview_use_case(...)` 简化为访问前置 + 调用 service。
- 更新 `app/application/README.md` 中关于兼容 wrapper 的描述。
- 同步 `docs/plans/current-status.md`、`docs/plans/handoff.md` 和 daily 快照。

## Non-Goals

- 不修改公开 API。
- 不修改监控 overview 响应字段。
- 不迁移数据库查询到 repository。
- 不重构设备监控 plugin registry 或 template service。
- 不处理 control command 链路。

## Architecture

目标方向：

- `api/endpoints/devices/monitoring.py`：HTTP 参数、权限依赖、调用 application use case。
- `application/device_monitoring.py`：用户访问前置，然后调用 service。
- `services/device_monitor_service.py`：设备监控 overview 稳定业务能力与聚合能力。
- `domain`：保持纯规则，无外层依赖。

这保持了“application 编排用户意图，service 提供稳定业务能力”的分层，同时避免 service 反向依赖 application。

## Testing

采用 TDD：

1. 先扩展 import 边界测试，预期因 `device_monitor_service.py` import application 失败。
2. 调整 service/application 后，让边界测试通过。
3. 跑设备监控相关测试，确认兼容入口和 HTTP use case 行为保持。

推荐验证：

```bash
./venv/bin/python -m pytest tests/test_backend_layer_boundaries.py tests/test_device_monitor_service.py tests/test_endpoint_application_convergence.py::DeviceMonitoringEndpointConvergenceTest -q
```

## Acceptance

- `app/services/**/*.py` 不再 import `app.api` 或 `app.application`。
- `DeviceMonitorService.get_monitor_overview()` 仍可作为兼容入口返回原有 overview payload。
- `get_device_monitor_overview_use_case(...)` 仍负责访问控制。
- 推荐验证命令通过。
