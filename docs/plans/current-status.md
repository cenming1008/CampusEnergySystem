# Current Status

## 当前总目标
- 当前主主题：`后端架构分层审计与规范整理`
- 当前总目标：在不改变 API 契约、不移动生产代码的第一阶段，完成后端分层审计库存和规范护栏，为后续小步代码整理提供执行依据。
- 当前执行依据：
  - `docs/plans/PLAN-20260530-backend-architecture-layering-audit.md`
  - `docs/superpowers/specs/2026-05-30-backend-architecture-audit-design.md`

---

## 当前阶段
- [x] 建立正式后端架构分层审计 PLAN。
- [x] 建立后端架构审计库存。
- [x] 补充后端规范中的审计分类口径。
- [x] 增加轻量文档护栏测试。
- [x] 执行最小验证并给出阶段验收判断。
- [x] 第一轮低风险 endpoint cleanup 已选择 `app/api/endpoints/energy/shared.py`。
- [x] `energy/shared.py` 已拆分为 `schemas.py`、`constants.py`、`serializers.py`，并保留兼容导出。
- [x] 能源 endpoint 已改为直接从明确模块导入，不再从 `.shared` 导入。
- [x] `alarm_service.py` 第一轮纯规则泄漏点已收口：storage managed categories 映射迁入 `domain/alarm_rules.py`。
- [x] `alarm_service.py` 第二轮纯规则泄漏点已收口：generic/media threshold managed categories 映射迁入 `domain/alarm_rules.py`。
- [x] `device_service.py` 第一轮 profile/default 泄漏点已收口：legacy create registry defaults patch 迁入 `domain/device_payloads.py`。
- [x] `device_service.py` 第二轮纯规则泄漏点已收口：compensation device category normalization 迁入 `domain/device_payloads.py`。
- [x] `campus_service.py` 第一轮纯聚合泄漏点已收口：energy category summary 迁入 `domain/campus_rules.py`。
- [x] `campus_service.py` 第二轮纯聚合泄漏点已收口：subitem statistics 迁入 `domain/campus_rules.py`。
- [x] `campus_service.py` 第三轮纯聚合泄漏点已收口：realtime load trend 迁入 `domain/campus_rules.py`。
- [x] `campus_service.py` 第四轮纯聚合泄漏点已收口：location rankings 迁入 `domain/campus_rules.py`。
- [x] `campus_service.py` 第五轮摘要聚合泄漏点已收口：alarm summary 迁入 `domain/campus_rules.py`。
- [x] `location_service.py` 第一轮纯规则泄漏点已收口：full_path / level 路径计算迁入 `domain/location_rules.py`。
- [x] `location_service.py` 第二轮轻量转换泄漏点已收口：location tree node payload 迁入 `domain/location_rules.py`。
- [x] `location_service.py` 第三轮统计聚合泄漏点已收口：location statistics payload 迁入 `domain/location_rules.py`。

## 当前阻塞
- 当前无代码阻塞。

## 当前待办
- [ ] 若继续进入下一轮生产代码整理，先从 `docs/plans/backend-architecture-audit-inventory.md` 选择一个剩余 `split_candidate`，不重复处理已完成的 `energy/shared.py`。
- [ ] 对涉及控制链、权限、接口契约或历史专题边界的候选项，先建立单独 `PLAN-*.md`。
- [ ] 后续代码整理必须保持 API 契约兼容，并补充对应测试。

## 当前验证结论
- `./venv/bin/python -m pytest tests/test_backend_architecture_audit_docs.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py tests/test_layer_exports.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_energy_endpoint_layering.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_energy_endpoint_semantics.py tests/test_endpoint_application_convergence.py tests/test_energy_service_round2.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py::test_storage_managed_categories_follow_present_payload_fields -q` 通过。
- `./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py::test_threshold_managed_categories_follow_present_payload_fields -q` 通过。
- `./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py tests/test_alarm_service.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py::TestDeviceDomainHelpers::test_build_device_registry_default_patch_normalizes_legacy_compensation_device -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py::TestDeviceDomainHelpers::test_normalize_device_category_maps_legacy_compensation_load -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py tests/test_device_service_round2.py tests/test_device_management_use_cases.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_energy_category_summary_sorts_and_preserves_response_shape -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py tests/test_campus_endpoints.py tests/test_application_use_cases.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_subitem_statistics_groups_by_device_category_and_ignores_missing_devices -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_realtime_load_trend_groups_rows_and_ignores_negative_deltas -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_location_rankings_rolls_summaries_up_to_target_locations -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_alarm_summary_counts_status_severity_locations_and_latest -q` 通过。
- `./venv/bin/python -m pytest tests/test_location_domain.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_location_domain.py tests/test_location_application_use_cases.py tests/test_endpoint_application_convergence.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_location_domain.py::test_build_location_tree_node_preserves_response_shape -q` 通过。
- `./venv/bin/python -m pytest tests/test_location_domain.py::test_build_location_statistics_payload_counts_devices_and_children -q` 通过。

## 当前验收判断
- 第一阶段可判定：后端架构分层审计主题已建立正式 PLAN。
- 第一阶段可判定：审计库存已覆盖主要后端分层目录，并明确 `keep/watch/split_candidate/plan_required` 分类。
- 第一阶段审计本身未移动生产代码；随后完成的 `energy/shared.py` 低风险 endpoint cleanup 仅调整模块导入和兼容导出，未改变 API 契约。
- 第一阶段可判定：后续生产代码整理必须按单一泄漏点小步执行，必要时单独建立 PLAN。

## 当前剩余风险
- 当前已完成架构审计、文档护栏、`energy/shared.py` 低风险 endpoint cleanup、`alarm_service.py` storage 与 generic/media threshold managed categories 切片、`device_service.py` legacy create registry defaults patch 与 compensation category normalization 切片、`campus_service.py` 主要纯聚合 helper 下沉，以及 `location_service.py` path calculation / tree node payload / statistics payload 切片；剩余风险集中在尚未处理的厚 service / 大 endpoint 独立泄漏点。
- 若后续进入代码移动，必须按候选文件另起小步计划和测试闭环。
