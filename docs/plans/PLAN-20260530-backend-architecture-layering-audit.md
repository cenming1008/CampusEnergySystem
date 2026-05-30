# PLAN-20260530 Backend Architecture Layering Audit

## 目标

在不改变现有 API 契约、不移动生产代码的第一阶段，完成后端分层架构审计库存，明确 `api / application / services / domain / integrations` 的职责边界、风险文件和后续整改顺序。

## 范围

- 审计 `app/api/endpoints/`、`app/application/`、`app/services/`、`app/domain/`、`app/integrations/`。
- 建立后端架构审计库存文档。
- 补充后端规范中的审计分类口径。
- 增加轻量文档护栏测试，确保审计文档不丢失关键分类。
- 保持园区综合能源管理系统产品方向。

## 非目标

- 不修改公开 API 路径、请求参数、响应模型或状态码。
- 不迁移数据库、MQTT topic、环境变量、容器名或运行时兼容标识。
- 不做全量 service 重构。
- 不把本轮扩成前端改造。
- 不扩张煤矿专属建模或术语。
- 不移动生产代码；生产代码整理必须进入后续分阶段任务。

## 分层口径

- `api/endpoints`：HTTP 参数、依赖注入、响应模型、状态码和极薄异常翻译。
- `application`：用户意图和系统工作流编排、访问前置、审计、默认值和多 service 协作。
- `services`：稳定业务能力、资源读写、状态变化和查询聚合。
- `domain`：纯规则、profile 解析、payload 归一和确定性计算。
- `integrations`：MQTT、厂商协议、外部系统和边界字段映射。

## 审计分类

- `keep`：已符合目标分层，或是明确兼容层。
- `watch`：当前可接受，但不应继续扩大职责。
- `split_candidate`：存在明确职责泄漏、文件膨胀或测试困难，后续可小步整理。
- `plan_required`：风险高或影响面大，必须单独建 PLAN 后再改生产代码。

## 第一阶段交付物

- `docs/plans/backend-architecture-audit-inventory.md`
- `docs/guides/backend-guidelines.md` 的审计分类补充
- `tests/test_backend_architecture_audit_docs.py`

## 验收标准

- 审计库存覆盖主要后端分层目录。
- 每个候选文件都有分类、原因、建议落点和下一步。
- 文档明确禁止第一阶段移动生产代码。
- 轻量 pytest 文档护栏通过。
- 现有 endpoint/application 边界测试仍通过。

## 推荐验证

- `./venv/bin/python -m pytest tests/test_backend_architecture_audit_docs.py -q`
- `./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py tests/test_layer_exports.py -q`
