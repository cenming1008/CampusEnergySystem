# Backend Guardrails Sync Design

## Goal

把现有后端规范从“说明口径”推进为“可执行护栏”：同步过时的后端目录说明和审计库存，并用轻量 pytest 防止后续继续向旧 `shared.py` 落点或错误跨层依赖回退。

## Context

当前主主题仍是 `后端架构分层审计与规范整理`。现有规范入口为：

- `docs/guides/backend-guidelines.md`
- `docs/plans/backend-architecture-audit-inventory.md`
- `docs/plans/current-status.md`
- `docs/plans/handoff.md`

上一轮已完成 `app/services/devices/compensation/monitor_service.py` 第八轮 SVG payload 泄漏点收口：SVG 容量利用率、回路摘要和柜温 metric 来源判断迁入 `app/domain/compensation_rules.py`。

本轮扫描发现两个文档同步问题和一个护栏缺口：

- `app/README.md` 仍描述 `devices/shared.py`、`energy/shared.py` 为主要模型/工具文件，容易误导后续新增代码继续放入 catch-all shared。
- `docs/plans/backend-architecture-audit-inventory.md` 未记录补偿监控第八轮 SVG payload 收口。
- 现有护栏测试只覆盖部分文档存在性和 energy endpoint 不直接 import `.shared`，尚未保护 domain 层不反向依赖 api/application/services/integrations。

## Scope

本轮修改范围：

- 更新 `app/README.md` 中 `api/endpoints/devices/` 和 `api/endpoints/energy/` 的目录说明。
- 更新 `docs/plans/backend-architecture-audit-inventory.md` 中补偿监控已完成列表和后续风险描述。
- 扩展 `tests/test_backend_architecture_audit_docs.py`，固定 README 与库存同步要求。
- 新增或扩展轻量架构测试，确保 `app/domain/*.py` 不 import `app.api`、`app.application`、`app.services` 或 `app.integrations`。

## Non-Goals

- 不修改生产代码行为。
- 不调整公开 API 路径、请求参数、响应模型或状态码。
- 不继续拆 service 或 endpoint。
- 不建立新的后端规范文档替代 `backend-guidelines.md`。
- 不处理 `inspection_service.py`、`maintenance_service.py` 或控制命令链路等 `plan_required` 候选项。

## Architecture

本轮以“文档同步 + 测试护栏”为主：

- `app/README.md` 作为后端目录读者入口，必须反映当前 endpoint 分层现状。
- `backend-architecture-audit-inventory.md` 作为后续选题依据，必须同步最新已完成切片。
- pytest 作为最低成本的架构护栏，防止最容易回退的两类问题：旧 shared 落点误导、domain 层反向依赖。

## Testing

采用 TDD：

1. 先写 README / inventory 同步测试，预期失败。
2. 先写 domain import 边界测试，若当前已有违反项则按事实调整为精确边界或列入风险，不盲目改生产代码。
3. 更新文档让测试通过。

推荐验证：

```bash
./venv/bin/python -m pytest tests/test_backend_architecture_audit_docs.py tests/test_model_module_boundaries.py -q
```

## Acceptance

- `app/README.md` 不再把 `energy/shared.py` 描述为能源新增落点，并说明 `schemas.py/constants.py/serializers.py` 的当前分工。
- 审计库存记录补偿监控第八轮 SVG payload 收口。
- 测试能防止 README/库存再次明显落后。
- domain 边界测试覆盖禁止反向依赖 api/application/services/integrations。
- 不改变生产运行行为。
