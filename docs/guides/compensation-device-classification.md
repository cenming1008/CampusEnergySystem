# 无功功率补偿设备归类规范

## 1. 适用范围

本规范仅用于无功功率补偿设备族的统一归类，当前正式覆盖：

- `svg`
- `capacitor_bank_controller`

预留但本轮未落地：

- `apf`
- `hybrid_compensation`

## 2. 归类模型

无功补偿设备统一采用六层模型：

1. 业务主类：`device_category = compensation`
2. 技术子型：`device_subtype = svg | capacitor_bank_controller`
3. 公共遥测层：跨补偿子型共享的公共监控语义
4. 专属遥测层：仅某个补偿子型具备的实时扩展字段
5. 参数快照层：设备回读的参数、门限、模式和容量配置
6. 控制与回执层：动作命令、执行状态、失败原因和设备回执

默认要求：

- 新建或归一后的补偿设备必须落到 `compensation + device_subtype`
- 不允许直接用厂家型号名作为 `device_subtype`
- 不允许把协议寄存器名直接暴露成业务公共字段
- 不允许把参数回读、控制回执混进公共遥测层

## 3. 历史兼容映射

- `reactive_power_compensator -> capacitor_bank_controller`
- `compensation -> capacitor_bank_controller`

兼容目标：

- 旧设备在读取时仍可识别为 `device_category = compensation`
- 若旧数据只保留 `device_type`，系统仍应补出规范 `device_subtype`

## 4. 公共遥测层

所有补偿类设备统一对外提供以下公共语义：

- `timestamp`
- `voltage`
- `current`
- `power_factor`
- `reactive_power`
- `flow_rate`
- `temperature`

语义约定：

- `reactive_power` 表示当前总无功功率
- `power_factor` 表示当前综合功率因数
- `flow_rate` 继续承接“当前有功/负荷展示位”
- 若原始报文只有三相量，应先做聚合归一，再补到公共层

## 5. 专属遥测层

### `svg`

保留在 SVG 专属遥测层的字段包括：

- 输出能力：`svg_reactive_output`, `capacity_utilization`, `output_direction`
- 运行状态：`run_status`, `stop_status`, `auto_mode`, `local_mode`, `breaker_status`, `module_status`, `fan_status`, `comm_status`
- 故障告警：`overvoltage_fault`, `undervoltage_fault`, `overcurrent_fault`, `overtemp_fault`, `module_fault`, `fan_fault`, `comm_fault`, `current_fault_code`, `current_alarm_code`
- 内部量：`cabinet_temp`, `module_temp`, `igbt_temp`, `dc_bus_voltage`, `heatsink_temp`
- 运维状态：`svg_operations_profile`

### `capacitor_bank_controller`

保留在电容补偿控制器专属遥测层的字段包括：

- 三相功率：`active_power_a/b/c`, `reactive_power_a/b/c`, `apparent_power_a/b/c`
- 三相质量：`voltage_thd_a/b/c`, `current_harmonic_a/b/c`
- 状态位：`leading_a/b/c`, `undercurrent_a/b/c`, `overvoltage_alarm_a/b/c`, `voltage_thd_alarm_a/b/c`, `current_thd_alarm_a/b/c`, `temp_alarm`
- 投切状态：`circuit_state_phase_a/b/c`, `circuit_state_common_1/2/3`

## 6. 参数快照层

参数快照层用于承接设备回读或网关同步的配置类数据，不属于实时遥测层。

电容补偿控制器当前已落地：

- `CapacitorBankControlProfile`
- 参数来源：`source`
- 参数时间：`snapshot_timestamp`
- 来源状态：`source_status`
- 典型参数：投入/切除功率因数、投入/切除延时、过压门限、温度上限、控制模式、运行回路数、容量配置

要求：

- 参数快照必须标明来源与时间
- 前端展示参数换算值时必须能区分真实遥测、参数回读、估算或占位
- 新增补偿子型若需要参数回读，应优先建立独立参数快照模型或明确复用边界

## 7. 控制与回执层

控制与回执层用于承接远程动作、参数写入、执行状态和设备侧回执，不属于公共遥测层。

当前补偿控制状态集统一为：

- `accepted`
- `running`
- `success`
- `failed`
- `timeout`
- `rejected`

要求：

- “命令已入队”只能表示 `accepted`，不得直接当作执行成功
- 控制日志必须保留动作、目标设备、请求参数、结果状态和失败原因
- 参数写入与远程控制应使用可关联的命令标识，例如 `command_id`
- 真实设备或网关协议未联调前，不得把模拟回执口径认定为正式协议冻结

## 8. 接口组织

公共设备主资源继续走：

- `/devices/*`

补偿类扩展统一挂载：

- `/devices/{id}/compensation/svg/*`
- `/devices/{id}/compensation/capacitor-bank/*`

旧顶层 `/svg`、`/capacitor-bank` 不再作为正式入口。

## 9. 后续扩展要求

未来新增补偿子型时，必须同时定义：

- 规范 `device_subtype`
- 它为何属于 `compensation`
- 公共层字段如何由原始报文归一得到
- 专属遥测字段落在哪个独立模型中
- 是否需要参数快照层
- 是否需要控制与回执层
- 前端是复用公共补偿页还是新增子型专属面板

若以上内容缺失，则视为“分类未完成”，不能直接接入主线页面或 API 契约。
