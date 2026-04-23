# tests

`tests/` 当前保持单层目录，默认通过 `unittest discover` 发现：

```bash
./venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

在没有同步调整覆盖率脚本、CI 和文档引用之前，不建议直接把现有测试拆到子目录或批量重命名。

## 当前分组

### 鉴权与权限
- `test_access_control.py`
- `test_audit.py`
- `test_auth_deps.py`
- `test_monitoring_access.py`
- `test_security_headers.py`
- `test_user_application_use_cases.py`
- `test_user_service.py`

### 系统与应用
- `test_alarm_endpoints.py`
- `test_alarm_service.py`
- `test_application_use_cases.py`
- `test_campus_endpoints.py`
- `test_database_core.py`
- `test_endpoint_application_convergence.py`
- `test_endpoint_utils.py`
- `test_health_endpoint.py`
- `test_inspection_maintenance_use_cases.py`
- `test_layer_exports.py`
- `test_location_types.py`
- `test_main_middleware.py`
- `test_maintenance_service.py`
- `test_metrics.py`
- `test_notifications.py`
- `test_reports_integration.py`
- `test_runtime_controls.py`
- `test_scheduler_jobs.py`
- `test_scheduler_service.py`
- `test_startup_checks.py`

### 能源与分析
- `test_analysis_service.py`
- `test_capacity_baseline.py`
- `test_energy_domain.py`
- `test_energy_endpoint_semantics.py`
- `test_energy_service_round2.py`

### MQTT 与采集
- `test_capacitor_bank_ingestion.py`
- `test_device_ingestion_health_endpoints.py`
- `test_ingestion_health_service.py`
- `test_ingestion_reliability.py`
- `test_mqtt_contracts.py`
- `test_mqtt_processor.py`
- `test_mqtt_realtime_bridge.py`
- `test_mqtt_reliability_service.py`
- `test_replay_mqtt_failures.py`

### 补偿与电容柜
- `test_capacitor_bank_service.py`
- `test_compensation_device_contract.py`
- `test_compensation_device_nested_api.py`
- `test_jkwf_capacity.py`
- `test_jkwf_lcd_aliases.py`
- `test_jkwf_lcd_decoder.py`
- `test_send_capacitor_bank_telemetry.py`

### 设备与表计
- `test_device_domain.py`
- `test_device_endpoint_semantics.py`
- `test_device_management_use_cases.py`
- `test_device_monitor_service.py`
- `test_device_reporting_use_case.py`
- `test_device_service_round2.py`
- `test_windows_device_stack_collector.py`
- `test_windows_device_stack_common.py`
- `test_windows_device_stack_gateway.py`
- `test_windows_device_stack_runtime.py`

### 实时与 WebSocket
- `test_websocket_auth.py`

### 其他
- `test_data_cleanup_service.py`

## 命名约定

- 新增测试继续使用 `test_*.py`，否则不会被当前发现规则拾取。
- 文件名优先表达业务域或被测模块，不要使用临时阶段名。
- 新增测试优先沿用现有主线语义：园区、区域、楼栋、设备、表计、能耗、告警、实时监控。
- 如果测试只验证一个明确用例，优先使用 `use_case`；如果覆盖多个流程，再使用 `use_cases`。

## 当前整理建议

下面这些文件不是现在就删，而是后续可优先收口的候选：

- `test_device_service_round2.py`
- `test_energy_service_round2.py`

原因：
- `round2` 这类阶段性命名不利于长期维护。
- 更适合在后续重构时按稳定职责改成明确名称，再同步更新引用。

下面这些名字暂时可接受，但后续新增时不要继续扩散：

- `test_device_reporting_use_case.py`
- `test_application_use_cases.py`
- `test_user_application_use_cases.py`
- `test_device_management_use_cases.py`
- `test_inspection_maintenance_use_cases.py`

原因：
- 单复数风格目前并不完全统一。
- 现阶段先保持兼容，避免为命名整洁打断现有脚本和文档。

## 后续如果要继续整理

建议顺序：

1. 先统一命名，再考虑移动目录。
2. 调整前先同步检查 `scripts/shell/run_backend_coverage.sh`、CI 和 `docs/` 中的直接引用。
3. 真要拆目录时，优先按业务域拆，而不是按作者或阶段拆。
