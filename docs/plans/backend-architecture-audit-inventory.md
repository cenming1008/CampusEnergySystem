# Backend Architecture Audit Inventory

> 第一阶段库存只做事实归类，不批准批量移动生产代码。

## 分类口径

| 分类 | 含义 | 后续动作 |
| --- | --- | --- |
| `keep` | 已符合目标分层，或是明确兼容层 | 保持现状，后续避免无意义改动 |
| `watch` | 当前可接受，但不应继续扩大职责 | 新增逻辑时优先寻找更清晰落点 |
| `split_candidate` | 存在明确职责泄漏、文件膨胀或测试困难 | 后续小步计划中处理一个具体泄漏点 |
| `plan_required` | 风险高或影响面大 | 单独建立 PLAN 后再动生产代码 |

## API Endpoint 层

| 文件 | 分类 | 原因 | 建议落点 | 下一步 |
| --- | --- | --- | --- | --- |
| `app/api/endpoints/devices/` | `keep` | 已按设备主域拆分为 management/data/monitoring/ingestion_health/补偿/储能等职责文件 | 继续作为复杂 endpoint 域目录样板 | 新增设备接口优先复用该分层 |
| `app/api/endpoints/energy/shared.py` | `keep` | 已拆为 `schemas.py`、`constants.py`、`serializers.py`，`shared.py` 仅保留兼容导出 | 新代码直接导入明确模块 | 后续不再向 `shared.py` 添加新职责 |
| `app/api/endpoints/campus.py` | `watch` | 文件较大，但已有 `app/application/campus.py` 承接聚合 use case | 保持 endpoint 极薄，新增聚合进 application | 新增前先查是否已有 use case |
| `app/api/endpoints/locations.py` | `watch` | 文件较大，但已有 `app/application/locations.py` | 位置树裁剪和统计优先放 application | 只在出现具体泄漏时拆 |
| `app/api/endpoints/inspection.py` | `watch` | 历史较厚，但 application convergence 已完成一轮 | application/inspection.py | 不回头重做，新增动作优先 use case |
| `app/api/endpoints/maintenance.py` | `watch` | 历史较厚，但 application convergence 已完成一轮 | application/maintenance.py | 不回头重做，新增动作优先 use case |
| `app/api/endpoints/users.py` | `keep` | 已有 users use case 收口关键写操作 | application/users.py | 避免 auth/session 越界 |

## Application 层

| 文件 | 分类 | 原因 | 建议落点 | 下一步 |
| --- | --- | --- | --- | --- |
| `app/application/README.md` | `keep` | 已清晰说明 application/use case 职责 | 持续作为分层说明入口 | 新增 use case 后同步 |
| `app/application/device_monitoring.py` | `keep` | 承接设备监控 overview 主流程 | 保持 HTTP overview 优先入口 | 不把监控分发重新堆回 endpoint |
| `app/application/energy_management.py` | `keep` | 承接能源 overview 多 service 编排 | 保持聚合查询入口 | 与 energy endpoint cleanup 配套审计 |
| `app/application/inspection.py` | `watch` | 文件较大，但是已通过专题收口的 workflow 层 | 保持 workflow 价值，避免空壳扩张 | 只在新增巡检主流程时调整 |
| `app/application/reporting.py` | `watch` | 文件较大但职责集中在报表与 CSV payload | reporting use case | 非报表导出逻辑不要加入 |

## Service 层

| 文件 | 分类 | 原因 | 建议落点 | 下一步 |
| --- | --- | --- | --- | --- |
| `app/services/alarm_service.py` | `split_candidate` | 告警生命周期、平台规则触发和设备族判断可能继续膨胀 | 纯规则进入 `domain`，生命周期留 service | 后续单独锁定一个规则泄漏点 |
| `app/services/device_service.py` | `split_candidate` | 设备主档、profile/default、统计和兼容能力集中 | profile/default 归一可进入 domain 或设备子服务 | 后续按一个具体职责拆 |
| `app/services/campus_service.py` | `split_candidate` | 驾驶舱聚合计算与查询能力较集中 | 纯聚合计算 helper 可下沉 domain/application | 后续先补聚合行为测试 |
| `app/services/location_service.py` | `split_candidate` | 位置树、统计、设备归属能力集中 | workflow 进 application，纯树计算可进 domain | 后续按位置树或统计单点处理 |
| `app/services/inspection_service.py` | `plan_required` | 文件大且已被 previous convergence 处理过，贸然拆容易回头重做 | 需先复核现有 application 边界 | 单独 PLAN 后处理 |
| `app/services/maintenance_service.py` | `plan_required` | 文件大且涉及状态流转与统计 | 需先复核现有 application 边界 | 单独 PLAN 后处理 |
| `app/services/devices/compensation/monitor_service.py` | `split_candidate` | 补偿监控专属能力较厚 | 设备族 service package | 按补偿监控单一职责小步整理 |
| `app/services/devices/compensation/capacitor_bank/control_command_service.py` | `plan_required` | 控制命令链路风险高，涉及现场控制语义 | 保持设备族服务，任何拆分必须有控制链测试 | 单独 PLAN 后处理 |

## Domain 层

| 文件 | 分类 | 原因 | 建议落点 | 下一步 |
| --- | --- | --- | --- | --- |
| `app/domain/alarm_rule_profiles.py` | `keep` | 规则 profile 解析样板清晰 | 继续承接平台规则 profile | 新设备族规则优先补这里或相邻 domain |
| `app/domain/alarm_rules.py` | `watch` | 文件较大但属于纯规则集合 | 后续可转 package | 只有增长压力明确时再拆 |
| `app/domain/compensation_rules.py` | `keep` | 补偿设备监控纯规则落点，当前承接 PQ 归一、参考线格式与健康评分基础规则 | 继续承接补偿监控纯计算 | 保持无 DB/HTTP/service 依赖 |
| `app/domain/energy_rules.py` | `watch` | 文件较大但属于能源规则 | 后续可转 package | 保持无 DB/HTTP |
| `app/domain/analysis_rules.py` | `watch` | 文件较大但属于分析规则 | 后续可转 package | 保持无 DB/HTTP |
| `app/domain/device_payloads.py` | `keep` | payload 归一职责明确 | 继续作为接入 payload 规则入口 | 新协议 alias 不直接塞 endpoint |

## Integrations 层

| 文件/目录 | 分类 | 原因 | 建议落点 | 下一步 |
| --- | --- | --- | --- | --- |
| `app/integrations/mqtt/` | `keep` | MQTT 边界职责明确 | 保持协议/传输边界 | 业务规则不要倒灌 |
| `app/integrations/jkwf_lcd/` | `keep` | 厂商协议解码边界明确 | 保持 vendor adapter | 工程值规则与业务告警分离 |

## 第一批建议执行顺序

已完成：

- `energy/shared.py` 已拆为 `schemas.py`、`constants.py`、`serializers.py`，`shared.py` 仅保留兼容导出。

后续建议：

1. 已完成：`alarm_service.py` 中 storage managed categories 纯映射已迁入 `domain/alarm_rules.py`。
2. 已完成：`alarm_service.py` 中 generic/media threshold managed categories 纯映射已迁入 `domain/alarm_rules.py`。
3. 已完成：`alarm_service.py` 中 platform communication offline category/message 纯规则已迁入 `domain/alarm_rules.py`，service 仅保留创建 / 恢复编排。
4. `alarm_service.py` 后续如继续整理，只能再选择告警生命周期、规则 profile 编排或查询编排中的一个独立泄漏点。
5. 已完成：`device_service.py` 中 legacy create registry defaults patch 已迁入 `domain/device_payloads.py`。
6. 已完成：`device_service.py` 中 compensation device category normalization 已迁入 `domain/device_payloads.py`，service 仅保留只读对象复制。
7. 已完成：`device_service.py` 中 pending archive completeness 纯规则已迁入 `domain/device_payloads.py`，service 仅保留状态流转触发。
8. 已完成：`device_service.py` 中 effective device type 解析已迁入 `domain/device_payloads.py`，service 仅保留兼容包装。
9. 已完成：`device_service.py` 中 read normalization patch 纯规则已迁入 `domain/device_payloads.py`，service 仅保留 SQLModel / 普通对象复制。
10. 已完成：`device_service.py` 中 pending archive status 纯规则已迁入 `domain/device_payloads.py`，service 仅保留兼容常量与流程触发。
11. 已完成：`device_service.py` 中 update identity patch 纯规则已迁入 `domain/device_payloads.py`，service 仅保留对象赋值与持久化。
12. `device_service.py` 后续如继续整理，只能再选择一个独立 profile/default 编排、对象复制或持久化边界泄漏点。
13. 已完成：`campus_service.py` 中 energy category summary 纯聚合已迁入 `domain/campus_rules.py`，`analysis_service.py` 的能源分类标签依赖同步改为 domain 来源。
14. 已完成：`campus_service.py` 中 subitem statistics 纯聚合已迁入 `domain/campus_rules.py`，`analysis_service.py` 的分项标签依赖同步改为 domain 来源。
15. 已完成：`campus_service.py` 中 realtime load trend 纯聚合已迁入 `domain/campus_rules.py`。
16. 已完成：`campus_service.py` 中 location rankings 纯聚合已迁入 `domain/campus_rules.py`，位置祖先定位仍由 service 作为 callback 提供。
17. 已完成：`campus_service.py` 中 alarm summary 摘要聚合已迁入 `domain/campus_rules.py`，告警生命周期与规则触发仍留在 `alarm_service.py`。
18. 已完成：`campus_service.py` 中 site entities / hierarchy summary 纯聚合已迁入 `domain/campus_rules.py`，context 构建、数据库查询与驾驶舱编排仍留 service。
19. 已完成：`campus_service.py` 中 period energy summaries 纯聚合已迁入 `domain/campus_rules.py`，能源行查询仍留 service。
20. 已完成：`campus_service.py` 中 ancestor location lookup 纯规则已迁入 `domain/campus_rules.py`，service 仅传入 context 和 target types。
21. `campus_service.py` 后续如继续整理，应优先评估查询 / context 编排是否仍需拆分，不再把纯聚合 helper 作为主要风险。
22. 已完成：`location_service.py` 中 full_path / level 路径计算已迁入 `domain/location_rules.py`，数据库查询与对象赋值仍留 service。
23. 已完成：`location_service.py` 中 location tree node payload 已迁入 `domain/location_rules.py`，递归遍历和查询仍留 service。
24. 已完成：`location_service.py` 中 location statistics payload 与设备计数聚合已迁入 `domain/location_rules.py`，设备 / 子位置查询仍留 service。
25. `location_service.py` 后续如继续整理，只能再选择位置树遍历或查询编排中的一个独立泄漏点。
26. 已完成：`app/services/devices/compensation/monitor_service.py` 中 PQ power factor normalization 与 reference line formatting 已迁入 `domain/compensation_rules.py`。
27. 已完成：`app/services/devices/compensation/monitor_service.py` 中 health score primitive rules 已迁入 `domain/compensation_rules.py`，健康模型 payload 组装仍留 service。
28. 已完成：`app/services/devices/compensation/monitor_service.py` 中 capacitor bank circuit summary 纯规则已迁入 `domain/compensation_rules.py`，telemetry/profile 字段抽取与监控 payload 组装仍留 service。
29. 已完成：`app/services/devices/compensation/monitor_service.py` 中 capacitor bank temperature health 纯规则已迁入 `domain/compensation_rules.py`，warning margin 配置读取仍留 service。
30. 已完成：`app/services/devices/compensation/monitor_service.py` 中 capacitor bank control mode resolution 纯规则已迁入 `domain/compensation_rules.py`，control log 读取与日志结果归一仍留 service。
31. `app/services/devices/compensation/monitor_service.py` 后续如继续整理，需重新选择新的独立泄漏点；控制命令相关逻辑保持 `plan_required` 边界。

## 第一阶段禁止项

- 禁止批量移动 service。
- 禁止调整公开接口契约。
- 禁止借审计整理运行时命名。
- 禁止把已完成的 application convergence 专题回头重做。
