# JKWF-LCD V5.0 协议支持清单

> 结论口径：当前项目对 JKWF-LCD V5.0 的“无功补偿器监视与控制台”已达到 `MVP+ / 可联调可演示`，但**尚未达到协议完整支持**。

## 1. 结论摘要

### 总结论

- 监视能力：`大部分核心能力已支持`
- 控制台只读档案：`大部分已支持`
- 控制台写入能力：`部分支持`
- 远程控制能力：`部分支持`
- 底层协议帧级实现（RS-485 / Modbus 03、10、44 + CRC）：`未在本仓库内直接实现`

### 为什么不是“完整支持”

主要缺口有 4 类：

1. 协议的 2~31 次三相逐次谐波未做完整数据建模与展示。
2. 功能码 `0x44` 的远程手动控制未按“手动/自动 + 相位 + 投切数据”做原生参数化实现。
3. 控制台虽然能展示整套参数快照，但只开放了少量低风险参数写入。
4. 当前控制链路是平台自定义 `campus-control.v1` MQTT 模型，不是仓库内直接实现 JKWF 原始报文主站。

---

## 2. 协议关键点

根据 [JKWF-LCD通讯协议_V5.0.docx](</Users/todo/学习/电气产品项目/JKWF-LCD通讯协议_V5.0.docx>)，本协议关键能力包括：

- 物理与链路层：
  - `RS-485`
  - 可编程地址、波特率
  - 读寄存器功能码 `03`
  - 写寄存器功能码 `10`
  - 远程手动功能码 `44`
  - CRC 校验
- 监视寄存器：
  - `0x00` 状态标志位
  - `0x01~0x03` 投切状态寄存器
  - `0x04~0x1D` 三相功率因数、电压、电流、谐波、电功率、频率、温度
  - `0x1E~0xD1` 三相 2~31 次电压/电流谐波
- 参数寄存器：
  - `0xD2~0xE4` 投切策略、回路配置、保护门限、通讯速率、端子方案、电流极性识别
- 远程控制：
  - `0x44` 需明确下发“手动/自动、相位、投切数据”

---

## 3. 支持矩阵

### 3.1 监视数据

| 协议项 | 当前状态 | 说明 |
| --- | --- | --- |
| `0x00` 状态标志位 | 已支持 | 已解码为各相超前、欠流、过压、谐波越限、温度越限布尔字段。 |
| `0x01~0x03` 投切状态寄存器 | 已支持 | 已解码为 A/B/C 分补与公补 1~24 的 bit mask。 |
| `0x04~0x06` 三相功率因数 | 已支持 | 已入 `CapacitorBankTelemetry`，并可归一到公共层 `power_factor`。 |
| `0x07~0x0C` 三相电压/电流 | 已支持 | 已入专属遥测并可归一到公共层 `voltage/current`。 |
| `0x0D~0x12` 三相谐波电压/电流汇总 | 已支持 | 当前支持的是三相汇总级谐波指标。 |
| `0x13~0x1B` 三相有功/无功/视在功率 | 已支持 | 已入专属遥测并归一无功/有功总量。 |
| `0x1C~0x1D` 频率/温度 | 已支持 | 已有落库与前端展示链路。 |
| `0x1E~0xD1` 三相 2~31 次逐次谐波 | 未支持 | 当前没有逐次谐波字段模型、接口和控制台展示。 |

### 3.2 参数回读与参数档案

| 协议项 | 当前状态 | 说明 |
| --- | --- | --- |
| `0xD2~0xE4` 参数快照落库 | 已支持 | 已有 `CapacitorBankControlProfile` 结构承载。 |
| 参数快照接口 | 已支持 | 已有 `/devices/{id}/compensation/capacitor-bank/control-profile`。 |
| 参数分组展示 | 已支持 | 控制台已按投切策略、回路配置、保护门限、设备配置展示。 |
| 参数来源/新鲜度标识 | 已支持 | 已有 `source`、`snapshot_timestamp`、`source_status`。 |

### 3.3 参数写入

| 协议项 | 当前状态 | 说明 |
| --- | --- | --- |
| 后端写入规格 `0xD2~0xE4` | 已支持 | 后端已为全部参数定义寄存器键与校验规格。 |
| 前端开放全部参数写入 | 未支持 | 目前只开放少量低风险参数。 |
| 已开放的前端写入参数 | 部分支持 | `投入/切除功率因数`、`投入/切除延时`、`过压门限`、`温度上限门限`。 |
| 离线/无回读前置校验 | 已支持 | 离线或无真实回读时拒绝写入。 |
| accepted/running/success/failed/timeout/rejected 回执语义 | 已支持 | 平台控制日志与前端状态文案已统一。 |

### 3.4 远程控制

| 协议项 | 当前状态 | 说明 |
| --- | --- | --- |
| 启停/使能 | 已支持 | 复用了设备既有启停主链。 |
| `reset_alarm` | 部分支持 | 有平台动作与模拟器回执，但不是协议文档里的原生功能码定义。 |
| `switch_control_mode` | 部分支持 | 当前是平台抽象动作。 |
| `manual_switch_test` | 部分支持 | 当前只是演示动作，不是完整 `0x44` 参数化手动控制。 |
| `0x44` 原生“手动/自动 + 相位 + 投切数据” | 未支持 | 未看到对应请求模型、服务参数和设备侧报文编排。 |

### 3.5 协议栈实现

| 协议项 | 当前状态 | 说明 |
| --- | --- | --- |
| RS-485 物理层/串口主站 | 未支持 | 当前仓库主要消费 MQTT 网关上报。 |
| Modbus 功能码 `03/10/44` 原始报文编解码 | 未支持 | 未见仓库内直接构帧、解析应答、处理异常码。 |
| CRC 低字节/高字节校验 | 未支持 | 未见 JKWF 原始帧级 CRC 处理。 |
| 网关映射后接入 MQTT | 已支持 | 当前 JKWF 集成明确是“通过 MQTT 网关接入”。 |

---

## 4. 已支持证据

### 4.1 状态位与投切寄存器解码

- `0x00` 状态位解码已实现：[app/integrations/jkwf_lcd/decoder.py](/Users/todo/CampusEnergySystem/app/integrations/jkwf_lcd/decoder.py:25)
- `0x01~0x03` 投切状态解码已实现：[app/integrations/jkwf_lcd/decoder.py](/Users/todo/CampusEnergySystem/app/integrations/jkwf_lcd/decoder.py:54)

### 4.2 MQTT 字段映射与专属遥测提取

- JKWF 字段别名映射已覆盖状态位、投切寄存器、参数快照核心字段：[app/integrations/mqtt/processor.py](/Users/todo/CampusEnergySystem/app/integrations/mqtt/processor.py:118)
- 电容补偿控制器专属遥测字段集合：[app/integrations/mqtt/processor.py](/Users/todo/CampusEnergySystem/app/integrations/mqtt/processor.py:411)
- 参数快照字段集合：[app/integrations/mqtt/processor.py](/Users/todo/CampusEnergySystem/app/integrations/mqtt/processor.py:433)

### 4.3 数据模型

- 监视遥测表已覆盖三相功率、谐波汇总、状态位、投切状态：[app/models/tables.py](/Users/todo/CampusEnergySystem/app/models/tables.py:718)
- 参数档案表已覆盖 `0xD2~0xE4` 对应参数：[app/models/tables.py](/Users/todo/CampusEnergySystem/app/models/tables.py:799)

### 4.4 参数写入与控制链路

- 后端写入规格已定义全部参数寄存器：[app/services/capacitor_bank_service.py](/Users/todo/CampusEnergySystem/app/services/capacitor_bank_service.py:62)
- 控制能力元信息、协议版本、回执语义已提供：[app/services/capacitor_bank_service.py](/Users/todo/CampusEnergySystem/app/services/capacitor_bank_service.py:180)
- 控制台前端只读参数与写入入口已实现：[frontend/src/views/DeviceControlConsole.vue](/Users/todo/CampusEnergySystem/frontend/src/views/DeviceControlConsole.vue:700)

### 4.5 已有测试

- 解码器测试：[tests/test_jkwf_lcd_decoder.py](/Users/todo/CampusEnergySystem/tests/test_jkwf_lcd_decoder.py:1)
- MQTT 字段别名测试：[tests/test_jkwf_lcd_aliases.py](/Users/todo/CampusEnergySystem/tests/test_jkwf_lcd_aliases.py:1)
- 摄取与落库测试：[tests/test_capacitor_bank_ingestion.py](/Users/todo/CampusEnergySystem/tests/test_capacitor_bank_ingestion.py:1)
- 控制服务测试：[tests/test_capacitor_bank_service.py](/Users/todo/CampusEnergySystem/tests/test_capacitor_bank_service.py:1)

---

## 5. 明确缺口

### 5.1 逐次谐波未完整支持

协议文档明确支持三相电压和三相电流的 `2~31` 次谐波数据，但当前仓库只承接了：

- `voltage_thd_a/b/c`
- `current_harmonic_a/b/c`

这更像“汇总级谐波指标”，不是协议完整寄存器集。

### 5.2 手动投切 `0x44` 未做原生参数化

协议要求的远程手动功能至少应显式表达：

- 手动/自动
- 相位（A/B/C/共补）
- 投切数据（不投不切 / 投入 / 切除）

当前项目里只有：

- `manual_switch_test`
- `reset_alarm`
- `switch_control_mode`

因此只能算平台控制动作，不算协议 `0x44` 的完整实现。

### 5.3 前端控制台未开放全部可写参数

虽然参数元信息中列了整套 `0xD2~0xE4`，但前端实际可写入口只筛出了带 `editable: true` 的少数字段：

- `switch_on_power_factor`
- `switch_off_power_factor`
- `switch_on_delay_seconds`
- `switch_off_delay_seconds`
- `overvoltage_threshold`
- `temperature_upper_limit`

其余寄存器当前仍是只读快照。

### 5.4 仓库内没有 JKWF 原始协议主站实现

当前项目的 JKWF 集成说明明确是：

- “支持通过 MQTT 网关接入 JKWF-LCD V5.0 协议设备数据”

因此仓库本身不是协议主站，不直接负责：

- 03/10/44 原始帧构造
- CRC
- RS-485 通讯状态机
- 原始异常应答处理

---

## 6. 推荐口径

对内建议使用下面这句：

> 当前项目已对 JKWF-LCD V5.0 实现监视与控制台的 `MVP+` 支持：核心监视量、状态位、投切状态、参数快照、少量受控写入和模拟控制回执已经打通；但逐次谐波、原生 `0x44` 手动投切、全量参数写入和原始 RS-485/Modbus 协议栈仍未完整实现，因此不能宣称“完整支持该协议”。

对外或对设备厂家联调时，建议更保守：

> 当前平台已支持通过网关接入 JKWF-LCD 设备的核心监视数据与部分远程控制能力，完整协议适配仍需按真实网关/设备报文继续联调确认。

---

## 7. 后续补齐建议

如需把口径升级到“接近完整支持”，建议按下面顺序推进：

1. 建立逐次谐波数据模型：
   - 至少明确 2~31 次三相电压/电流谐波的存储与接口策略
2. 明确 `0x44` 的平台契约：
   - 增加 `mode / phase / action` 请求模型
   - 明确与设备/网关的映射方式
3. 明确哪些 `0xD2~0xE4` 参数允许在控制台开放：
   - 按低风险、中风险、高风险分层
4. 若目标是“协议完整支持”而不是“网关映射支持”：
   - 单独立项实现 JKWF 原始帧级适配层，含 `03/10/44` 与 CRC

