# Compensation Monitor SVG Payload Design

## Goal

整理 `app/services/devices/compensation/monitor_service.py` 中 SVG 监控 payload 的确定性计算逻辑，把容量利用率、回路摘要和柜温来源判断下沉到 `app/domain/compensation_rules.py`，让 service 层继续只负责查询、设备族服务调用和最终响应装配。

## Context

当前主主题为 `后端架构分层审计与规范整理`。仓库已有正式执行依据：

- `docs/plans/PLAN-20260530-backend-architecture-layering-audit.md`
- `docs/plans/backend-architecture-audit-inventory.md`
- `docs/guides/backend-guidelines.md`

现有库存已将 `app/services/devices/compensation/monitor_service.py` 标记为 `split_candidate`。前几轮已经把补偿监控中的 PQ 归一、健康评分基础规则、回路摘要、温度状态、控制模式解析、控制日志模式解析和 SVG 控制模式解析迁入 `app/domain/compensation_rules.py`。

本轮继续沿用同一方向，但只处理一个低风险泄漏点：SVG monitor 中内联的容量利用率、回路摘要和柜温 metric 来源判断。

## Scope

本轮修改范围：

- 在 `app/domain/compensation_rules.py` 新增 SVG monitor payload 纯规则 helper。
- 在 `app/services/devices/compensation/monitor_service.py` 中调用该 helper，减少 `_build_svg_monitor()` 内的确定性计算。
- 在 `tests/test_compensation_domain.py` 中补充 domain helper 测试。
- 复用 `tests/test_compensation_monitor_service_boundary.py` 验证 service 响应形状不变。

## Non-Goals

- 不修改公开 API 路径、请求参数、响应字段或状态码。
- 不移动数据库模型、仓库查询或 service package 结构。
- 不触碰电容补偿控制器远程控制命令链路。
- 不拆整个 `monitor_service.py`。
- 不把 SVG 专属能力扩张为新的接口契约。
- 不继续扩张煤矿专属概念。

## Architecture

目标分层保持为：

- `service`：读取 SVG telemetry、读取 SVG profile、调用 SVG capability service、组装最终 monitor payload。
- `domain`：根据 telemetry/profile/realtime/device 基础值计算 SVG monitor 的稳定 payload 片段。

新增 domain helper 建议命名为 `build_svg_monitor_payload_parts(...)`，接收普通值而不是 ORM 对象：

- `capacity_utilization`
- `profile_module_count`
- `rated_capacity`
- `reactive_power`
- `cabinet_temperature`
- `realtime_temperature`

返回结构包含：

- `capacity_utilization_metric`
- `cabinet_temperature_metric`
- `compensation_level_metric`
- `circuit_summary`

service 层保留 `control_mode`、`capabilities_summary`、`profile_status` 和最终 dict 装配，避免 domain 反向依赖 SVG service 或 HTTP 展示层。

## Data Flow

1. `CompensationMonitorService._build_svg_monitor()` 查询最新 SVG telemetry。
2. service 查询 SVG operations profile。
3. service 从对象上读取 profile module count、telemetry capacity utilization、telemetry cabinet temperature、设备 rated capacity 和 realtime fallback 值。
4. service 调用 `build_svg_monitor_payload_parts(...)`。
5. service 使用返回片段组装原有 monitor payload。

## Compatibility

本轮必须保持 SVG monitor 响应形状不变：

- `subtype`
- `control_mode`
- `circuit_summary`
- `profile_status`
- `key_metrics.capacity_utilization`
- `key_metrics.cabinet_temperature`
- `key_metrics.compensation_level`
- `capabilities_summary`
- `status_tags`

当 telemetry 缺失时，现有 fallback 行为保持：

- 若存在 `rated_capacity > 0` 且 `reactive_power` 可用，容量利用率使用估算值，source 为 `estimated`，state 为 `mock`。
- 若无法估算，容量利用率 source/state 均为 `missing`。
- 若 profile module count 可用，`total_count` 使用该值。
- 若容量利用率与 `total_count` 都可用，计算 `running_count`。
- 柜温优先使用 telemetry，缺失时使用 realtime temperature，再缺失时 source/state 为 `missing`。

## Testing

新增 domain 测试覆盖：

- SVG telemetry 容量利用率与 profile module count 同时存在时，生成 live circuit summary 和 compensation level。
- SVG telemetry 容量利用率缺失但设备额定容量和实时无功可用时，生成 estimated/mock 容量利用率。
- SVG telemetry 柜温缺失但 realtime temperature 可用时，柜温 metric 使用 realtime/live。
- 全部缺失时，容量和柜温保持 missing 状态。

保留 service 边界测试：

- `tests/test_compensation_monitor_service_boundary.py::TestCompensationMonitorServiceBoundary::test_build_monitor_marks_svg_as_read_only_capability`

推荐验证命令：

```bash
./venv/bin/python -m pytest tests/test_compensation_domain.py tests/test_compensation_monitor_service_boundary.py -q
```

## Acceptance

- 新 helper 无 DB、HTTP、service import。
- `CompensationMonitorService._build_svg_monitor()` 中 SVG payload 计算明显减少。
- 公开响应结构保持不变。
- 推荐验证命令通过。
- `docs/plans/current-status.md` 和 `docs/plans/handoff.md` 在实现完成后按标准轮同步本轮切片结论。
