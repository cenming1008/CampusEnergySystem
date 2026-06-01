# Handoff

## 当前主题
- 当前主主题：`后端架构分层审计与规范整理`
- 当前执行依据：
  - `docs/plans/PLAN-20260530-backend-architecture-layering-audit.md`
  - `docs/superpowers/specs/2026-05-30-backend-architecture-audit-design.md`

---

## 阶段结论
- 已确认本主题第一阶段定位为后端架构审计与规范护栏。
- 第一阶段审计本身未移动生产代码；随后完成的 `energy/shared.py` 低风险 endpoint cleanup 仅调整模块导入和兼容导出，未改变 API 契约。
- 审计分类固定为 `keep / watch / split_candidate / plan_required`。
- 第一轮低风险 endpoint cleanup 已完成：`energy/shared.py` 拆为 `schemas.py`、`constants.py`、`serializers.py`，endpoint 新代码不再从 `.shared` 导入。
- `alarm_service.py` 第一轮纯规则泄漏点已收口：storage managed categories 映射迁入 `domain/alarm_rules.py`，告警生命周期编排仍保留在 service。

## 下一棒
- 规则/预判角色：
  - 后续进入生产代码整理前，先从 `docs/plans/backend-architecture-audit-inventory.md` 选择单一候选项。
  - 若候选项为 `plan_required`，必须先建立或更新正式 `PLAN-*.md`。
- 后端角色：
  - 每轮只处理一个具体职责泄漏点，不做批量 service / endpoint 搬迁。
  - 保持 API 路径、请求参数、响应模型和状态码兼容。
  - 按候选项选择对应测试，必要时先补测试再改生产代码。
- 验收角色：
  - 核对本阶段是否仍只停留在审计和护栏。
  - 后续每个生产代码整理阶段都要重新核对非目标和兼容边界。

## 已验证
- `./venv/bin/python -m pytest tests/test_backend_architecture_audit_docs.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py tests/test_layer_exports.py -q` 通过。

## 剩余风险
- 当前已完成审计、文档护栏和 `energy/shared.py` 低风险 endpoint cleanup；其余厚 service 或大 endpoint 代码债仍未处理。
- `energy/shared.py` 仅作为兼容导出保留；后续新增能源 endpoint 契约、常量或转换函数应直接进入明确模块。
- 涉及控制链、权限、接口契约或历史专题边界的整理必须进入 `plan_required` 路径。
- `alarm_service.py` 仍是 `split_candidate`，但本轮只处理 storage managed categories 纯映射；后续继续整理时仍必须一次只选一个独立规则泄漏点。
