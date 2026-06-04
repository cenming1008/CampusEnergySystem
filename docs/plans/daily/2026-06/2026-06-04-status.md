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
- [x] `alarm_service.py` 第三轮纯规则泄漏点已收口：platform communication offline category/message 迁入 `domain/alarm_rules.py`。
- [x] `alarm_service.py` 第四轮纯规则泄漏点已收口：alarm recovery decision 迁入 `domain/alarm_rules.py`。
- [x] `alarm_service.py` 第五轮纯规则泄漏点已收口：generic threshold compensation skip decision 迁入 `domain/alarm_rules.py`。
- [x] `device_service.py` 第一轮 profile/default 泄漏点已收口：legacy create registry defaults patch 迁入 `domain/device_payloads.py`。
- [x] `device_service.py` 第二轮纯规则泄漏点已收口：compensation device category normalization 迁入 `domain/device_payloads.py`。
- [x] `device_service.py` 第三轮纯规则泄漏点已收口：pending archive completeness 迁入 `domain/device_payloads.py`。
- [x] `device_service.py` 第四轮纯规则泄漏点已收口：effective device type 解析迁入 `domain/device_payloads.py`。
- [x] `device_service.py` 第五轮纯规则泄漏点已收口：read normalization patch 迁入 `domain/device_payloads.py`。
- [x] `device_service.py` 第六轮纯规则泄漏点已收口：pending archive status 迁入 `domain/device_payloads.py`。
- [x] `device_service.py` 第七轮纯规则泄漏点已收口：update identity patch 迁入 `domain/device_payloads.py`。
- [x] `device_service.py` 第八轮对象复制泄漏点已收口：read normalization view 迁入 `domain/device_payloads.py`。
- [x] `device_service.py` 第九轮 profile payload 泄漏点已收口：semantic profile payload 迁入 `domain/device_payloads.py`。
- [x] `campus_service.py` 第一轮纯聚合泄漏点已收口：energy category summary 迁入 `domain/campus_rules.py`。
- [x] `campus_service.py` 第二轮纯聚合泄漏点已收口：subitem statistics 迁入 `domain/campus_rules.py`。
- [x] `campus_service.py` 第三轮纯聚合泄漏点已收口：realtime load trend 迁入 `domain/campus_rules.py`。
- [x] `campus_service.py` 第四轮纯聚合泄漏点已收口：location rankings 迁入 `domain/campus_rules.py`。
- [x] `campus_service.py` 第五轮摘要聚合泄漏点已收口：alarm summary 迁入 `domain/campus_rules.py`。
- [x] `campus_service.py` 第六轮纯聚合泄漏点已收口：site entities / hierarchy summary 迁入 `domain/campus_rules.py`。
- [x] `campus_service.py` 第七轮纯聚合泄漏点已收口：period energy summaries 迁入 `domain/campus_rules.py`。
- [x] `campus_service.py` 第八轮纯规则泄漏点已收口：ancestor location lookup 迁入 `domain/campus_rules.py`。
- [x] `location_service.py` 第一轮纯规则泄漏点已收口：full_path / level 路径计算迁入 `domain/location_rules.py`。
- [x] `location_service.py` 第二轮轻量转换泄漏点已收口：location tree node payload 迁入 `domain/location_rules.py`。
- [x] `location_service.py` 第三轮统计聚合泄漏点已收口：location statistics payload 迁入 `domain/location_rules.py`。
- [x] `location_service.py` 第四轮树遍历泄漏点已收口：location tree traversal 迁入 `domain/location_rules.py`。
- [x] `location_service.py` 第五轮查询决策泄漏点已收口：location reference match 迁入 `domain/location_rules.py`。
- [x] `app/services/devices/compensation/monitor_service.py` 第一轮纯规则泄漏点已收口：PQ power factor normalization 与 reference line formatting 迁入 `domain/compensation_rules.py`。
- [x] `app/services/devices/compensation/monitor_service.py` 第二轮纯规则泄漏点已收口：health score primitive rules 迁入 `domain/compensation_rules.py`。
- [x] `app/services/devices/compensation/monitor_service.py` 第三轮纯规则泄漏点已收口：capacitor bank circuit summary 迁入 `domain/compensation_rules.py`。
- [x] `app/services/devices/compensation/monitor_service.py` 第四轮纯规则泄漏点已收口：capacitor bank temperature health 迁入 `domain/compensation_rules.py`。
- [x] `app/services/devices/compensation/monitor_service.py` 第五轮纯规则泄漏点已收口：capacitor bank control mode resolution 迁入 `domain/compensation_rules.py`。
- [x] `app/services/devices/compensation/monitor_service.py` 第六轮纯规则泄漏点已收口：capacitor bank control log mode parsing 迁入 `domain/compensation_rules.py`。
- [x] `app/services/devices/compensation/monitor_service.py` 第七轮纯规则泄漏点已收口：SVG control mode resolution 迁入 `domain/compensation_rules.py`。
- [x] `app/services/devices/compensation/monitor_service.py` 第八轮 SVG payload 泄漏点已收口：SVG 容量利用率、回路摘要和柜温 metric 来源判断迁入 `domain/compensation_rules.py`。
- [x] 后端规范护栏同步已完成：`app/README.md` 与审计库存已同步当前 endpoint/domain 分层，并新增 README / inventory 新鲜度与 domain 反向依赖护栏测试。
- [x] 后端 service 边界护栏已完成：新增 service 禁止反向依赖 api/application 的测试，并将 `DeviceMonitorService.get_monitor_overview()` 改为 service 自有聚合能力，application 仅保留访问前置。

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
- `./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_alarm_service.py::TestAlarmService::test_sync_platform_comm_alarm_creates_and_recovers_offline_instance -q` 通过。
- `./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py::test_compute_alarm_recovery_decision_backfills_instance_key_and_skips_active_hits -q` 先失败于缺少 `compute_alarm_recovery_decision`，补实现后通过。
- `./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py tests/test_alarm_service.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py::test_should_skip_generic_threshold_detection_for_compensation_category_only -q` 先失败于缺少 `should_skip_generic_threshold_detection`，补实现后通过。
- `./venv/bin/python -m pytest tests/test_alarm_service.py::TestAlarmService::test_general_threshold_alarm_skips_compensation_devices -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py::TestDeviceDomainHelpers::test_build_device_registry_default_patch_normalizes_legacy_compensation_device -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py::TestDeviceDomainHelpers::test_normalize_device_category_maps_legacy_compensation_load -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py tests/test_device_service_round2.py tests/test_device_management_use_cases.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_service_round2.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py tests/test_device_service_round2.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py::TestDeviceDomainHelpers::test_build_device_update_identity_patch_normalizes_type_and_adds_missing_unit tests/test_device_domain.py::TestDeviceDomainHelpers::test_build_device_update_identity_patch_preserves_existing_unit -q` 先失败于缺少 `build_device_update_identity_patch`，补实现后通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py tests/test_device_service_round2.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py::TestDeviceDomainHelpers::test_with_device_read_normalization_returns_patched_read_view_without_mutating_source tests/test_device_domain.py::TestDeviceDomainHelpers::test_with_device_read_normalization_returns_same_object_when_no_patch_needed -q` 先失败于缺少 `with_device_read_normalization`，补实现后通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py tests/test_device_service_round2.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py::TestDeviceDomainHelpers::test_build_device_semantic_profile_preserves_device_profile_payload_shape -q` 先失败于缺少 `build_device_semantic_profile`，补实现后通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_service_round2.py::DeviceServiceRound2Test::test_get_device_semantic_profile_uses_normalized_category -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_energy_category_summary_sorts_and_preserves_response_shape -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py tests/test_campus_endpoints.py tests/test_application_use_cases.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_subitem_statistics_groups_by_device_category_and_ignores_missing_devices -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_realtime_load_trend_groups_rows_and_ignores_negative_deltas -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_location_rankings_rolls_summaries_up_to_target_locations -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_alarm_summary_counts_status_severity_locations_and_latest -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_site_entities_prefers_site_types_and_derives_roots_when_missing tests/test_campus_domain.py::test_build_hierarchy_summary_counts_locations_devices_and_meters -q` 先失败于缺少 `build_hierarchy_summary`，补实现后通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py tests/test_campus_endpoints.py tests/test_application_use_cases.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_period_energy_summaries_groups_rows_and_flags_meter_reset -q` 先失败于缺少 `build_period_energy_summaries`，补实现后通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py tests/test_campus_endpoints.py tests/test_application_use_cases.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py::test_find_ancestor_location_walks_parent_chain_and_handles_missing_nodes -q` 先失败于缺少 `find_ancestor_location`，补实现后通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py tests/test_campus_endpoints.py tests/test_application_use_cases.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_location_domain.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_location_domain.py tests/test_location_application_use_cases.py tests/test_endpoint_application_convergence.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_location_domain.py::test_build_location_tree_node_preserves_response_shape -q` 通过。
- `./venv/bin/python -m pytest tests/test_location_domain.py::test_build_location_statistics_payload_counts_devices_and_children -q` 通过。
- `./venv/bin/python -m pytest tests/test_location_domain.py::test_build_location_tree_recurses_until_max_depth_with_service_callbacks -q` 先失败于缺少 `build_location_tree`，补实现后通过。
- `./venv/bin/python -m pytest tests/test_location_domain.py tests/test_location_application_use_cases.py tests/test_endpoint_application_convergence.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_location_domain.py::test_resolve_location_reference_match_prefers_full_path_then_code_and_unique_name -q` 先失败于缺少 `resolve_location_reference_match`，补实现后通过。
- `./venv/bin/python -m pytest tests/test_location_domain.py tests/test_location_application_use_cases.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_compensation_domain.py tests/test_compensation_monitor_service_boundary.py tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_returns_backend_pq_model -q` 通过。
- `./venv/bin/python -m pytest tests/test_compensation_domain.py tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_returns_backend_health_model tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_health_model_defaults_missing_dimensions_to_zero -q` 通过。
- `./venv/bin/python -m pytest tests/test_compensation_domain.py tests/test_compensation_monitor_service_boundary.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_returns_capacitor_bank_compensation_monitor_semantics tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_falls_back_to_profile_then_logs_then_placeholder tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_builds_temperature_health_from_threshold_and_alarm tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_temperature_warning_margin_is_configurable tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_returns_backend_pq_model tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_returns_backend_health_model tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_health_model_defaults_missing_dimensions_to_zero -q` 通过。
- `./venv/bin/python -m pytest tests/test_compensation_domain.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_compensation_monitor_service_boundary.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_builds_temperature_health_from_threshold_and_alarm tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_temperature_warning_margin_is_configurable tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_returns_capacitor_bank_compensation_monitor_semantics -q` 通过。
- `./venv/bin/python -m pytest tests/test_compensation_domain.py tests/test_compensation_monitor_service_boundary.py tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_returns_capacitor_bank_compensation_monitor_semantics tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_falls_back_to_profile_then_logs_then_placeholder -q` 通过。
- `./venv/bin/python -m pytest tests/test_compensation_domain.py::test_resolve_capacitor_bank_control_log_mode_accepts_only_successful_mode_logs -q` 先失败于缺少 `resolve_capacitor_bank_control_log_mode`，补实现后通过。
- `./venv/bin/python -m pytest tests/test_compensation_monitor_service_boundary.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_compensation_domain.py::test_resolve_svg_control_mode_preserves_telemetry_and_placeholder_payloads -q` 先失败于缺少 `resolve_svg_control_mode`，补实现后通过。
- `./venv/bin/python -m pytest tests/test_compensation_monitor_service_boundary.py::TestCompensationMonitorServiceBoundary::test_build_monitor_marks_svg_as_read_only_capability -q` 通过。
- `./venv/bin/python -m pytest tests/test_compensation_domain.py::test_build_svg_monitor_payload_parts_uses_telemetry_and_profile_counts -q` 先失败于缺少 `build_svg_monitor_payload_parts`，补实现后通过。
- `./venv/bin/python -m pytest tests/test_compensation_domain.py tests/test_compensation_monitor_service_boundary.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_backend_architecture_audit_docs.py::test_app_readme_describes_current_endpoint_layout tests/test_backend_architecture_audit_docs.py::test_backend_architecture_inventory_records_latest_compensation_svg_payload_slice -q` 先失败于 README / inventory 过时，补同步后通过。
- `./venv/bin/python -m pytest tests/test_backend_architecture_audit_docs.py tests/test_backend_layer_boundaries.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_backend_layer_boundaries.py::test_service_layer_does_not_import_api_or_application_layers -q` 先失败于 `app/services/device_monitor_service.py imports app.application.device_monitoring`，调整分层后通过。
- `./venv/bin/python -m pytest tests/test_backend_layer_boundaries.py tests/test_device_monitor_service.py tests/test_endpoint_application_convergence.py::TestEndpointApplicationConvergence::test_device_monitor_overview_endpoint_delegates_to_application -q` 通过。

## 当前验收判断
- 第一阶段可判定：后端架构分层审计主题已建立正式 PLAN。
- 第一阶段可判定：审计库存已覆盖主要后端分层目录，并明确 `keep/watch/split_candidate/plan_required` 分类。
- 第一阶段审计本身未移动生产代码；随后完成的 `energy/shared.py` 低风险 endpoint cleanup 仅调整模块导入和兼容导出，未改变 API 契约。
- 第一阶段可判定：后续生产代码整理必须按单一泄漏点小步执行，必要时单独建立 PLAN。

## 当前剩余风险
- 当前已完成架构审计、文档护栏、`energy/shared.py` 低风险 endpoint cleanup、`alarm_service.py` storage、generic/media threshold managed categories、platform communication offline category/message、alarm recovery decision 与 generic threshold compensation skip decision 切片、`device_service.py` legacy create registry defaults patch、compensation category normalization、pending archive completeness、effective device type、read normalization patch、read normalization view、pending archive status、update identity patch 与 semantic profile payload 切片、`campus_service.py` 主要纯聚合 helper、site entities、hierarchy summary、period energy summaries 与 ancestor location lookup 下沉、`location_service.py` path calculation / tree node payload / statistics payload / tree traversal / location reference match 切片，以及补偿监控 PQ、健康评分基础规则、回路摘要、温度状态、控制模式解析、控制日志模式解析、SVG 控制模式解析与 SVG payload metric 来源判断切片；剩余风险集中在尚未处理的厚 service / 大 endpoint 独立泄漏点。
- 当前规范护栏已覆盖 README/库存同步和 domain 禁止反向依赖 api/application/services/integrations；endpoint/application/service 更细的 import 边界仍可后续按单独切片补充。
- 当前 service 护栏已覆盖禁止反向依赖 api/application；后续如补更细边界，应优先评估 endpoint 是否只做 HTTP 适配、application 是否避免直接承接 SQL/ORM 查询。
- 若后续进入代码移动，必须按候选文件另起小步计划和测试闭环。
