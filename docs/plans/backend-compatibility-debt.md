# Backend Compatibility Debt

> 本文记录后端当前必须保留的兼容层与后续可删除的历史残留。目标是把“现在不能动的运行时兼容契约”和“满足条件后可以清理的旧入口 / 旧字段 / 旧语义”分开管理，避免在功能收敛时误删现场链路。

## 维护口径

- 新增主流程优先使用当前园区 EMS 语义：`device_subtype`、`device_category`、`energy_type`、`location_id`、`campus/device/{device_code}/telemetry`、`Alarm.source=device_native/platform_rule/platform_comm`。
- 本文列出的兼容项默认可以继续保留，但不得继续扩大成新主流程。
- 删除任何兼容项前，必须先确认当前谁在用、是否有替代契约、是否已完成迁移公告或数据治理，并跑完对应测试。
- 若兼容项已进入现场网关、数据库 schema、前端展示或外部 API，不能在普通重构中顺手删除。

## 债务清单

### 1. `app/services/mqtt_processor.py`

**类型**：必须保留的兼容层，后续可在外部调用方全部迁移后删除。

**为什么保留**

- 当前真实主实现已迁到 `app/integrations/mqtt/processor.py`。
- `app/services/mqtt_processor.py` 作为旧导入路径代理，继续导出 `process_payload`、`process_payload_dict`、`FIELD_ALIASES`、`persist_device_data` 等符号，避免历史测试、脚本或外部调用仍从 `app.services.mqtt_processor` 导入时直接断裂。

**当前谁在用**

- 后端测试仍覆盖旧路径，例如 MQTT processor、ingestion reliability、失败重放等相关测试。
- 可能存在外部脚本、运维工具或历史集成代码继续按 `app.services.mqtt_processor` 导入。

**删除前需要满足什么条件**

- 仓库内不再有任何生产代码、测试、脚本从 `app.services.mqtt_processor` 导入。
- 外部调用方已统一迁移到 `app.integrations.mqtt.processor`。
- 至少经过一个版本周期声明旧路径废弃，并确认现场 MQTT 接入、失败重放、接入流水查询不依赖旧路径。

**删除前要跑哪些测试**

- `./venv/bin/python -m pytest tests/test_mqtt_processor.py tests/test_ingestion_reliability.py tests/test_replay_mqtt_failures.py -q`
- `./venv/bin/python -m pytest tests/test_device_ingestion_routes.py tests/test_mqtt_contracts.py -q`

### 2. `/devices/legacy`

**类型**：必须保留的 HTTP 兼容入口，后续可在客户端迁移完成后删除。

**为什么保留**

- 当前新建设备主入口已是智能创建接口 `POST /devices/`，通过 application 层和设备类型 registry 归一 `device_type/device_subtype/device_category/energy_type`。
- `POST /devices/legacy` 仍接收完整 `Device` 模型，服务旧客户端或历史调试方式，避免旧表单 / 脚本直接失效。

**当前谁在用**

- 路由仍在 `app/api/endpoints/devices/management.py`。
- application 层仍提供 `create_device_legacy_use_case` 并记录 `device.create_legacy` 审计。
- 可能仍有本地调试脚本、旧前端构建或外部导入工具使用完整 `Device` payload。

**删除前需要满足什么条件**

- 所有设备创建调用方迁移到 `POST /devices/`。
- 不再有客户端提交完整 `Device` ORM 形态 payload。
- 已确认设备创建审计、补偿设备 subtype 归一、SVG operations profile 等新入口能力覆盖旧入口使用场景。
- OpenAPI / 文档 / 前端 API 客户端不再暴露 `/devices/legacy`。

**删除前要跑哪些测试**

- `./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py tests/test_device_management_use_cases.py -q`
- `./venv/bin/python -m pytest tests/test_compensation_device_nested_api.py tests/test_capacitor_bank_service.py -q`

### 3. `Device.device_type` 旧字段

**类型**：必须保留的数据库兼容字段，短期不得删除。

**为什么保留**

- `Device` 模型明确把 `device_type` 标为“兼容旧字段”；当前第一批对象边界仍通过 `device_type / device_subtype / device_category / energy_type` 组合表达。
- 监控模板、分析、报表、设备 registry、补偿设备 subtype 归一仍广泛读取 `device_type`。
- 历史数据中存在 `reactive_power_compensator`、`compensation` 等旧类型，当前通过 alias 归一到 `capacitor_bank_controller`。

**当前谁在用**

- `app/domain/device_payloads.py` 的 `normalize_device_type_alias`、`resolve_device_identity`、`describe_device_type_semantics`。
- `DeviceMonitorService`、`MonitorTemplateService`、`AnalysisService`、`ReportService`、设备创建 / 更新 use case。
- 前端和导出报表仍展示或依赖设备类型语义。

**删除前需要满足什么条件**

- 建立新的稳定主类型字段或独立设备族 / 点位模型，并完成全量数据迁移。
- 所有读取路径改为以 `device_subtype + device_category + energy_type` 或新模型为准。
- 历史 `device_type` alias 已完成一次性迁移或有只读归档策略。
- 报表、监控、分析、MQTT 入库、设备创建和更新接口均不再需要 `device_type`。

**删除前要跑哪些测试**

- `./venv/bin/python -m pytest tests/test_device_monitor_service.py tests/test_analysis_service.py tests/test_energy_service_round2.py -q`
- `./venv/bin/python -m pytest tests/test_device_management_use_cases.py tests/test_application_use_cases.py tests/test_capacitor_bank_ingestion.py -q`
- `cd frontend && npm run test:unit -- DeviceMonitor.test.ts viewMapping.test.ts`

### 4. MQTT 字段别名

**类型**：必须保留的现场接入兼容层，后续可按协议版本逐步收敛。

**为什么保留**

- 现场网关和历史 payload 已存在多种字段命名，例如 `sn/device_sn/meter_code -> device_code`、`ts/time/collect_time -> timestamp`、`active_power/kw -> power`、`meter_reading/cum_value -> consumption`。
- 设备 registry 还定义设备类型内的 `compatible_aliases`，如 `power -> flow_rate`、`kvar -> reactive_power`、冷热量表功率字段兼容等。
- 补偿设备还有专属别名和逐次谐波扁平字段折叠逻辑，用于兼容已上线网关。

**当前谁在用**

- `app/integrations/mqtt/payloads.py` 的 `FIELD_ALIASES` 与 `apply_field_aliases`。
- `app/core/device_registry.py` 的 `compatible_aliases`。
- `app/integrations/mqtt/compensation.py` 及补偿 / 储能 / 电表接入相关测试。
- 现场 MQTT 网关，特别是已跑通的 `CAP-001` 和历史 `campus/telemetry` payload。

**删除前需要满足什么条件**

- MQTT 协议引入强制版本字段，例如 `protocol_version=campus-mqtt.v1`，并明确 canonical 字段集。
- 现场网关全部升级为 canonical payload，不再上报旧字段别名。
- 接入流水中连续一个验收周期未出现旧别名字段。
- 文档、UAT payload 脚本和网关侧示例全部更新。

**删除前要跑哪些测试**

- `./venv/bin/python -m pytest tests/test_mqtt_processor.py tests/test_mqtt_contracts.py tests/test_device_ingestion_routes.py -q`
- `./venv/bin/python -m pytest tests/test_capacitor_bank_ingestion.py tests/test_compensation_mqtt_boundary.py tests/test_capacitor_bank_harmonic_uat_payloads.py -q`
- `./venv/bin/python scripts/python/send_capacitor_bank_harmonic_uat_payloads.py --print-only`

### 5. 告警旧 `source=telemetry`

**类型**：历史数据兼容展示，短期必须保留读取兼容，不再作为新告警主来源扩张。

**为什么保留**

- 旧告警表 `Alarm.source` 默认值为 `telemetry`，历史数据可能仍保留该来源。
- 当前新告警边界已收敛为 `device_native/platform_rule/platform_comm`，但不做历史数据迁移。
- 前端已把旧 `telemetry` 显示为“历史遥测”，避免旧告警在告警中心变成未知来源。

**当前谁在用**

- 数据库历史告警行。
- `frontend/src/features/alarm/sourceLabels.ts` 对 `telemetry` 的兼容标签。
- `AlarmService` 的部分 helper 默认参数仍为 `source="telemetry"`，主要服务历史兼容和未显式传 source 的旧调用路径。
- 设备监控测试中仍有历史 recent alarms source 兼容断言。

**删除前需要满足什么条件**

- 完成历史告警 source 数据迁移，把旧 `telemetry` 明确映射到 `device_native`、`platform_rule` 或归档来源。
- 后端所有新告警创建路径显式传入三类新 source。
- 前端确认不再需要“历史遥测”标签。
- 数据库 schema 默认值不再是 `telemetry`，且旧行已清理或归档。

**删除前要跑哪些测试**

- `./venv/bin/python -m pytest tests/test_alarm_service.py tests/test_alarm_endpoints.py tests/test_ingestion_health_service.py tests/test_scheduler_jobs.py -q`
- `./venv/bin/python -m pytest tests/test_device_monitor_service.py -q`
- `cd frontend && npm run test:unit -- sourceLabels.test.ts DeviceMonitor.test.ts`

### 6. 历史 `Device.location` 字符串字段

**类型**：必须保留的数据库兼容字段，后续可在 `location_id` 全面稳定后降级或删除。

**为什么保留**

- 当前规范位置关系是 `Device.location_id -> Location`，但 `Device.location` 仍作为“设备位置（兼容旧版，字符串描述）”保留。
- 设备创建 / 更新仍接受 `location` 文本，并通过 `LocationService.resolve_location_reference` 尽量解析为 `location_id/full_path`。
- 历史设备、报表、监控概览和旧客户端可能仍读取或显示字符串位置。

**当前谁在用**

- `DeviceService._resolve_location_fields` 在创建 / 更新设备时处理 `location` 文本。
- `DeviceMonitorService` 返回 overview 中的 `location` 字段。
- 设备管理 endpoint schema 仍包含 `location`。
- 巡检 / 维护等历史表单中也有位置描述字段，但与 `Device.location` 删除不是同一件事。

**删除前需要满足什么条件**

- 所有设备都有可信 `location_id`，且 `Location.full_path` 能覆盖显示需求。
- 前端、报表、监控、导出和外部 API 全部改为读取 `location_id/full_path` 或位置对象。
- 旧客户端不再提交 `location` 文本创建设备或更新设备。
- 完成历史数据校准，无法解析的位置文本有归档或人工处理方案。

**删除前要跑哪些测试**

- `./venv/bin/python -m pytest tests/test_device_service_round2.py tests/test_device_management_use_cases.py tests/test_endpoint_application_convergence.py -q`
- `./venv/bin/python -m pytest tests/test_device_monitor_service.py tests/test_location_application_use_cases.py tests/test_location_types.py -q`
- `cd frontend && npm run test:unit -- DeviceMonitor.test.ts`

## 清理顺序建议

1. 先清理纯导入兼容：`app/services/mqtt_processor.py`，前提是仓库和外部调用都迁移到 canonical 模块。
2. 再下线 HTTP 旧入口：`/devices/legacy`，前提是所有创建调用都迁移到智能创建入口。
3. 再收敛 MQTT 字段别名，必须依赖协议版本和现场网关升级。
4. 再处理历史告警 `source=telemetry`，建议通过迁移脚本或归档策略完成，不建议运行时硬删除兼容标签。
5. 最后评估数据库字段级债务：`Device.location` 和 `Device.device_type`。这两项牵涉 schema、历史数据、前端展示和报表，必须单独立项。
