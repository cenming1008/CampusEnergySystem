# Handoff

## 当前主题
- 当前主主题：`后端架构分层审计与规范整理`
- 当前执行依据：
  - `docs/plans/PLAN-20260530-backend-architecture-layering-audit.md`
  - `docs/superpowers/specs/2026-05-30-backend-architecture-audit-design.md`

---

## 阶段结论
- 已确认本主题第一阶段定位为后端架构审计与规范护栏。
- 第一阶段不移动生产代码，不改变 API 契约。
- 审计分类固定为 `keep / watch / split_candidate / plan_required`。

## 下一棒
- 规则/预判角色：
  - 建立 `docs/plans/backend-architecture-audit-inventory.md`。
  - 按分层目录给出候选文件分类、原因、建议落点和下一步。
- 后端角色：
  - 仅在审计文档和护栏测试范围内执行。
  - 不在本阶段拆 service、不改 endpoint 行为。
- 验收角色：
  - 核对文档是否覆盖主要后端分层。
  - 核对测试是否能防止审计文档关键字段丢失。

## 已验证
- `./venv/bin/python -m pytest tests/test_backend_architecture_audit_docs.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py tests/test_layer_exports.py -q` 通过。

## 剩余风险
- 本阶段只完成架构审计和文档护栏，不解决厚 service 或大 endpoint 的具体代码债。
- `energy/shared.py`、`alarm_service.py`、`device_service.py`、`campus_service.py` 等候选项需要按后续小步计划处理。
- 涉及控制链、权限、接口契约或历史专题边界的整理必须进入 `plan_required` 路径。
