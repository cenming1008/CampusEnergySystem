# PLAN-20260518 统一告警规则框架

## 目标

在保留现有告警表、接口、前端展示和设备接入流程的前提下，把告警逻辑推进为“统一生命周期 + 设备差异化规则配置”。

## 范围

- 保留 `Alarm.source=device_native/platform_rule/platform_comm` 三类来源。
- 保留告警生命周期：创建、刷新、系统恢复、人工处理。
- 保留 `instance_key=device_id:source:category` 的稳定实例键。
- 第一阶段接入非补偿类设备通用电压 / 电流阈值规则配置。
- 第二阶段接入电容补偿控制器平台推导规则配置。
- 第三阶段接入介质表计公共字段平台规则配置。
- 第四阶段接入储能设备基础平台规则配置。
- 配置覆盖顺序固定为：`default -> device_categories -> device_subtypes -> devices`。
- 保留旧 `default/device_thresholds` 阈值配置兼容。

## 非目标

- 不新增数据库表。
- 不改变现有告警 API。
- 不迁移历史 `source=telemetry` 告警。
- 不把补偿类专属告警规则改成通用阈值；补偿设备原生状态位、故障码、告警码仍保持 `device_native`。
- 不在前端新增核心告警判定逻辑。

## 第一阶段落点

- 新增规则解析层：`app/domain/alarm_rule_profiles.py`。
- `AlarmService.check_and_create_alarm()` 通过规则解析层获取启停状态和阈值。
- `config/settings.json` 增加 `alarm_rules.platform_rules.generic_thresholds` 示例。
- 文档补充平台规则配置层说明。

## 第二阶段落点

- `resolve_capacitor_bank_profile()` 解析 `alarm_rules.platform_rules.capacitor_bank`。
- 电容补偿控制器平台推导规则支持 `default -> device_categories -> device_subtypes -> devices` 覆盖。
- `profile_data` 中的设备参数快照继续作为基础输入，规则配置可覆盖参数快照。
- `enabled=false` 只关闭 `platform_rule` 推导，不屏蔽设备原生状态位、告警位或故障码。
- `config/settings.json` 增加 `alarm_rules.platform_rules.capacitor_bank` 示例。

## 第三阶段落点

- `resolve_media_threshold_profile()` 解析 `alarm_rules.platform_rules.media_thresholds`。
- 介质表计平台规则支持 `flow_rate_min/max`、`pressure_min/max`、`temperature_min/max`。
- `media_thresholds` 默认关闭，必须按设备类别、子型或单设备显式启用。
- 命中规则统一生成 `platform_rule` 来源告警，类别为 `flow_rate_out_of_range`、`pressure_out_of_range`、`temperature_out_of_range`。

## 第四阶段落点

- `resolve_storage_threshold_profile()` 解析 `alarm_rules.platform_rules.storage`。
- 储能平台规则支持 `soc_min/max`、`soh_min`、`cell_temp_max`、`active_power_abs_max`。
- `storage` 默认关闭，必须按设备类别、子型或单设备显式启用。
- 新增 `AlarmService.check_storage_faults()` 作为储能专属告警检测入口；当前不改储能 API 或前端。

## 验收标准

- 非补偿类设备仍可按默认阈值生成 `platform_rule` 告警。
- `device_categories.<category>.enabled=false` 可关闭对应设备类型的通用阈值告警。
- `devices.<device_id>` 可覆盖类型和默认阈值。
- 补偿设备仍不套用通用电压 / 电流阈值告警。
- 电容补偿控制器 `capacitor_bank.enabled=false` 时，温度门限、过压门限、谐波门限和过补偿推导不生成 `platform_rule` 告警。
- 电容补偿控制器原生状态位仍生成 `device_native` 告警，不受 `capacitor_bank.enabled=false` 影响。
- 水表等介质表计在 `media_thresholds` 显式启用后，可按压力、温度或流量上下限创建并恢复平台规则告警。
- 储能设备在 `storage` 显式启用后，可按 SOC、SOH、最高电芯温度和充放电功率创建并恢复平台规则告警。
- 既有告警生命周期测试保持通过。

## 后续阶段建议

- 评估是否需要管理端配置界面或规则 API。
- 后续如新增更多设备族，继续补充平台规则声明，而不是在页面侧推导告警。
