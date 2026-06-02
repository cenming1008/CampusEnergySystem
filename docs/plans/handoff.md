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
- `alarm_service.py` 第二轮纯规则泄漏点已收口：generic/media threshold managed categories 映射迁入 `domain/alarm_rules.py`，告警生命周期编排仍保留在 service。
- `alarm_service.py` 第三轮纯规则泄漏点已收口：platform communication offline category/message 迁入 `domain/alarm_rules.py`，平台通讯告警创建 / 恢复编排仍保留在 service。
- `device_service.py` 第一轮 profile/default 泄漏点已收口：legacy create registry defaults patch 迁入 `domain/device_payloads.py`，持久化、回滚和重复 SN 兼容仍保留在 service。
- `device_service.py` 第二轮纯规则泄漏点已收口：compensation device category normalization 迁入 `domain/device_payloads.py`，只读对象复制仍保留在 service。
- `device_service.py` 第三轮纯规则泄漏点已收口：pending archive completeness 迁入 `domain/device_payloads.py`，pending 状态流转触发仍保留在 service。
- `device_service.py` 第四轮纯规则泄漏点已收口：effective device type 解析迁入 `domain/device_payloads.py`，service 仅保留兼容包装。
- `device_service.py` 第五轮纯规则泄漏点已收口：read normalization patch 迁入 `domain/device_payloads.py`，SQLModel / 普通对象复制仍保留在 service。
- `device_service.py` 第六轮纯规则泄漏点已收口：pending archive status 迁入 `domain/device_payloads.py`，service 仅保留兼容常量与流程触发。
- `campus_service.py` 第一轮纯聚合泄漏点已收口：energy category summary 迁入 `domain/campus_rules.py`，驾驶舱查询与编排仍保留在 service。
- `campus_service.py` 第二轮纯聚合泄漏点已收口：subitem statistics 迁入 `domain/campus_rules.py`，驾驶舱查询与编排仍保留在 service。
- `campus_service.py` 第三轮纯聚合泄漏点已收口：realtime load trend 迁入 `domain/campus_rules.py`，驾驶舱查询与编排仍保留在 service。
- `campus_service.py` 第四轮纯聚合泄漏点已收口：location rankings 迁入 `domain/campus_rules.py`，位置祖先定位仍由 service 作为 callback 提供。
- `campus_service.py` 第五轮摘要聚合泄漏点已收口：alarm summary 迁入 `domain/campus_rules.py`，告警生命周期与规则触发仍留在 `alarm_service.py`。
- `location_service.py` 第一轮纯规则泄漏点已收口：full_path / level 路径计算迁入 `domain/location_rules.py`，数据库查询与对象赋值仍保留在 service。
- `location_service.py` 第二轮轻量转换泄漏点已收口：location tree node payload 迁入 `domain/location_rules.py`，递归遍历和查询仍保留在 service。
- `location_service.py` 第三轮统计聚合泄漏点已收口：location statistics payload 迁入 `domain/location_rules.py`，设备 / 子位置查询仍保留在 service。
- `app/services/devices/compensation/monitor_service.py` 第一轮纯规则泄漏点已收口：PQ power factor normalization 与 reference line formatting 迁入 `domain/compensation_rules.py`，遥测查询与监控 payload 组装仍保留在 service。
- `app/services/devices/compensation/monitor_service.py` 第二轮纯规则泄漏点已收口：health score primitive rules 迁入 `domain/compensation_rules.py`，健康模型 payload 组装仍保留在 service。
- `app/services/devices/compensation/monitor_service.py` 第三轮纯规则泄漏点已收口：capacitor bank circuit summary 迁入 `domain/compensation_rules.py`，telemetry/profile 字段抽取与监控 payload 组装仍保留在 service。
- `app/services/devices/compensation/monitor_service.py` 第四轮纯规则泄漏点已收口：capacitor bank temperature health 迁入 `domain/compensation_rules.py`，warning margin 配置读取仍保留在 service。
- `app/services/devices/compensation/monitor_service.py` 第五轮纯规则泄漏点已收口：capacitor bank control mode resolution 迁入 `domain/compensation_rules.py`，control log 读取与日志结果归一仍保留在 service。

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
- `./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py::test_threshold_managed_categories_follow_present_payload_fields -q` 通过。
- `./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py tests/test_alarm_service.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_alarm_service.py::TestAlarmService::test_sync_platform_comm_alarm_creates_and_recovers_offline_instance -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py::TestDeviceDomainHelpers::test_build_device_registry_default_patch_normalizes_legacy_compensation_device -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py::TestDeviceDomainHelpers::test_normalize_device_category_maps_legacy_compensation_load -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py tests/test_device_service_round2.py tests/test_device_management_use_cases.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_service_round2.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_domain.py tests/test_device_service_round2.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py tests/test_campus_endpoints.py tests/test_application_use_cases.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_subitem_statistics_groups_by_device_category_and_ignores_missing_devices -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_realtime_load_trend_groups_rows_and_ignores_negative_deltas -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_location_rankings_rolls_summaries_up_to_target_locations -q` 通过。
- `./venv/bin/python -m pytest tests/test_campus_domain.py::test_build_alarm_summary_counts_status_severity_locations_and_latest -q` 通过。
- `./venv/bin/python -m pytest tests/test_location_domain.py tests/test_location_application_use_cases.py tests/test_endpoint_application_convergence.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_location_domain.py::test_build_location_tree_node_preserves_response_shape -q` 通过。
- `./venv/bin/python -m pytest tests/test_location_domain.py::test_build_location_statistics_payload_counts_devices_and_children -q` 通过。
- `./venv/bin/python -m pytest tests/test_compensation_domain.py tests/test_compensation_monitor_service_boundary.py tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_returns_backend_pq_model -q` 通过。
- `./venv/bin/python -m pytest tests/test_compensation_domain.py tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_returns_backend_health_model tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_health_model_defaults_missing_dimensions_to_zero -q` 通过。
- `./venv/bin/python -m pytest tests/test_compensation_domain.py tests/test_compensation_monitor_service_boundary.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_returns_capacitor_bank_compensation_monitor_semantics tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_falls_back_to_profile_then_logs_then_placeholder tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_builds_temperature_health_from_threshold_and_alarm tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_temperature_warning_margin_is_configurable tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_returns_backend_pq_model tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_returns_backend_health_model tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_health_model_defaults_missing_dimensions_to_zero -q` 通过。
- `./venv/bin/python -m pytest tests/test_compensation_domain.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_compensation_monitor_service_boundary.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_builds_temperature_health_from_threshold_and_alarm tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_temperature_warning_margin_is_configurable tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_returns_capacitor_bank_compensation_monitor_semantics -q` 通过。
- `./venv/bin/python -m pytest tests/test_compensation_domain.py tests/test_compensation_monitor_service_boundary.py tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_returns_capacitor_bank_compensation_monitor_semantics tests/test_device_monitor_service.py::TestDeviceMonitorService::test_monitor_overview_capacitor_bank_falls_back_to_profile_then_logs_then_placeholder -q` 通过。

## 剩余风险
- 当前已完成架构审计、文档护栏、`energy/shared.py` 低风险 endpoint cleanup、`alarm_service.py` storage、generic/media threshold managed categories 与 platform communication offline category/message 切片、`device_service.py` legacy create registry defaults patch、compensation category normalization、pending archive completeness、effective device type、read normalization patch 与 pending archive status 切片、`campus_service.py` 主要纯聚合 helper 下沉、`location_service.py` path calculation / tree node payload / statistics payload 切片，以及补偿监控 PQ、健康评分基础规则、回路摘要、温度状态与控制模式解析切片；剩余风险集中在尚未处理的厚 service / 大 endpoint 独立泄漏点。
- `energy/shared.py` 仅作为兼容导出保留；后续新增能源 endpoint 契约、常量或转换函数应直接进入明确模块。
- 涉及控制链、权限、接口契约或历史专题边界的整理必须进入 `plan_required` 路径。
- `alarm_service.py` 仍是 `split_candidate`，但已处理 storage、generic/media threshold managed categories 与 platform communication offline category/message 纯规则；后续继续整理时必须一次只选一个独立生命周期、规则 profile 编排或查询编排泄漏点。
- `device_service.py` 仍是 `split_candidate`，但已处理 legacy create registry defaults patch、compensation category normalization、pending archive completeness、effective device type、read normalization patch 与 pending archive status；后续继续整理时必须一次只选一个独立 profile/default 编排、对象复制或持久化边界泄漏点。
- `campus_service.py` 仍是 `split_candidate`，但已处理 energy category summary、subitem statistics、realtime load trend、location rankings 与 alarm summary；后续若继续整理，应先评估查询 / context 编排边界，不再优先寻找纯聚合 helper。
- `location_service.py` 仍是 `split_candidate`，但已处理路径计算、tree node payload 和 statistics payload；后续继续整理时只能再选择位置树遍历或查询编排中的一个独立泄漏点。
- `app/services/devices/compensation/monitor_service.py` 仍是 `split_candidate`，但已处理 PQ 归一、参考线格式、健康评分基础规则、回路摘要、温度状态和控制模式解析；后续如继续整理需重新选择新的独立泄漏点，控制命令链路仍按 `plan_required` 处理。
