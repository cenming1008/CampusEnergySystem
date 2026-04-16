# Windows RS485 设备模拟链路设计

> 状态：已完成设计确认，待用户审阅后进入实现计划
> 日期：2026-04-16
> 主题：在 Windows 电脑上构建“模拟器 -> 采集器 -> MQTT 网关 -> 平台”的三段式设备模拟链路

## 1. 目标

在一台 Windows 电脑上提供一套可独立运行的三段式脚本，用于模拟补偿器等设备的真实接入流程：

- 模拟器负责造数，并通过 RS485 形态向下游输出设备帧
- 采集器负责从串口读取、解析、校验、重连和缓存
- 网关负责把统一 JSON 转为平台需要的 MQTT 消息并上报

本轮默认只实现：

- `RS485` 作为主输入链路
- `MQTT` 作为唯一正式上行方式
- `GPRS` 只保留后续扩展接口和配置位，不做真实联网实现

## 2. 范围与非目标

### 本轮范围

- 在仓库中新增一个独立目录，承载 Windows 设备链路脚本
- 提供 3 个独立 Python 脚本：
  - `rs485_device_simulator.py`
  - `edge_collector.py`
  - `mqtt_gateway.py`
- 提供统一配置文件和 Windows 运行说明
- 允许使用虚拟串口对在单机完成联调
- 输出的数据能够被当前平台的 MQTT ingest worker 消费

### 非目标

- 不改现有 `scripts/python/device_gateway.py` 主入口
- 不做真实 GPRS 拨号、串口 AT 指令或蜂窝网络适配
- 不做复杂本地数据库缓存，只做轻量缓存
- 不在本轮实现完整工业协议兼容层
- 不把现有补偿器模拟器脚本强行重构进三段结构

## 3. 推荐落点

新增目录：

- `scripts/python/windows_device_stack/`

计划文件：

- `scripts/python/windows_device_stack/rs485_device_simulator.py`
- `scripts/python/windows_device_stack/edge_collector.py`
- `scripts/python/windows_device_stack/mqtt_gateway.py`
- `scripts/python/windows_device_stack/config.example.json`
- `scripts/python/windows_device_stack/README.md`

如需要公共函数，可新增：

- `scripts/python/windows_device_stack/common.py`

## 4. 总体架构

数据流如下：

```text
Windows 模拟器
  -> RS485 虚拟串口帧
  -> 边缘采集器
  -> 统一 JSON
  -> MQTT 网关
  -> MQTT Broker
  -> 平台 mqtt_ingest_worker
```

三层职责必须严格分离：

1. 模拟器只负责“设备视角”的数据生成与串口发帧
2. 采集器只负责“边缘采集视角”的接收、解析、校验、缓存与转发
3. 网关只负责“平台接入视角”的统一格式转换与 MQTT 上报

## 5. 组件设计

### 5.1 模拟器

职责：

- 周期性生成补偿器遥测数据
- 将遥测编码成固定帧格式
- 通过串口输出到下游采集器

输入：

- 设备编码
- 串口号、波特率
- 发送周期
- 场景配置，如 normal、overtemp、harmonic

输出：

- 一帧一条的串口消息

设计约束：

- 模拟器不直接发 MQTT
- 模拟器不感知平台字段
- 帧中保留最小设备协议语义：设备编码、时间戳、关键测点、CRC

### 5.2 采集器

职责：

- 连接指定串口并持续读取帧
- 做分帧、解析、CRC 校验、字段类型转换
- 在串口异常时自动重连
- 把解析后的数据统一为标准 JSON
- 在网关不可用时做轻量缓存

输入：

- 串口号、波特率、超时
- 帧格式配置
- 网关交付目标，例如本地文件队列

输出：

- 标准化 JSON 记录

缓存策略：

- 默认使用 `jsonl` 本地落盘缓存
- 采集成功后写入待发送队列文件
- 网关确认发送成功后再标记或移除

本层边界：

- 不负责 MQTT 协议
- 不负责平台字段兼容
- 不负责 GPRS 网络细节

### 5.3 MQTT 网关

职责：

- 读取采集器产出的统一 JSON
- 映射为平台现有 ingest 可识别的 MQTT payload
- 发往指定 MQTT Broker
- 提供简单失败重试
- 预留 GPRS 传输配置位

输入：

- 统一 JSON 队列
- MQTT Broker 配置
- 主题、认证信息
- 传输模式配置，当前仅正式支持 `mqtt`

输出：

- 发送到 `campus/telemetry` 的 MQTT 消息

GPRS 预留方式：

- 配置中允许声明 `network_mode: wifi | gprs`
- 当前实现中两者最终都走系统网络到 MQTT
- 后续若接真实 GPRS 模块，可在网关层替换连接器，不影响模拟器和采集器

## 6. 串口帧协议

为避免本轮引入真实私有协议，先定义一个仓库内自有的最小演示帧格式。

建议帧结构：

```text
STX|device_code|timestamp|voltage|current|power|reactive_power|power_factor|temperature|scene|CRC|ETX
```

约定：

- `STX` 固定为 `<`
- `ETX` 固定为 `>`
- 字段分隔符为 `|`
- `timestamp` 使用 ISO8601 或 Unix 秒时间戳
- `CRC` 为前面正文的简单 CRC16 或校验和

示例：

```text
<CAP-001|2026-04-16T10:30:00|221.4|12.8|4.60|-2.30|0.95|35.2|normal|A13F>
```

这样做的原因：

- 人眼可读，方便 Windows 现场排查
- 结构简单，适合先跑通三段链路
- 后续可替换为 Modbus RTU 或厂家协议而不改三层职责

## 7. 统一 JSON 协议

采集器输出的统一 JSON 作为采集层与网关层之间的唯一契约。

建议结构：

```json
{
  "device_code": "CAP-001",
  "timestamp": "2026-04-16T10:30:00",
  "source": "rs485_collector",
  "transport": "rs485",
  "metrics": {
    "voltage": 221.4,
    "current": 12.8,
    "power": 4.6,
    "reactive_power": -2.3,
    "power_factor": 0.95,
    "temperature": 35.2
  },
  "meta": {
    "scene": "normal",
    "port": "COM6",
    "baudrate": 9600
  },
  "raw": {
    "frame": "<CAP-001|...|A13F>",
    "crc_ok": true
  }
}
```

约束：

- 采集器层统一只输出这一种结构
- 网关层不能依赖串口原始格式
- 后续增加 GPRS 或其他输入时，仍复用同一 JSON 契约

## 8. MQTT 上报协议

网关将统一 JSON 转换为平台当前可消费的 payload。

建议最小上报结构：

```json
{
  "device_code": "CAP-001",
  "timestamp": "2026-04-16T10:30:00",
  "voltage": 221.4,
  "current": 12.8,
  "power": 4.6,
  "reactive_power": -2.3,
  "power_factor": 0.95,
  "temperature": 35.2
}
```

主题默认：

- `campus/telemetry`

说明：

- 先优先兼容现有平台 ingest 能力
- `device_id` 不强依赖本地脚本提前知道，允许平台按 `device_code` 解析

## 9. 配置设计

建议提供单独配置文件 `config.example.json`，核心项如下：

```json
{
  "simulator": {
    "device_code": "CAP-001",
    "serial_port": "COM5",
    "baudrate": 9600,
    "interval_seconds": 3,
    "profile": "normal"
  },
  "collector": {
    "serial_port": "COM6",
    "baudrate": 9600,
    "timeout_seconds": 1,
    "cache_file": "./runtime/collector_queue.jsonl"
  },
  "gateway": {
    "network_mode": "wifi",
    "transport": "mqtt",
    "mqtt_broker": "127.0.0.1",
    "mqtt_port": 1883,
    "mqtt_username": "campus_mqtt",
    "mqtt_password": "campus_mqtt_secret_2026",
    "mqtt_topic": "campus/telemetry",
    "queue_file": "./runtime/collector_queue.jsonl"
  }
}
```

配置原则：

- 单机运行时尽量不依赖仓库主配置
- 保留与现有平台默认 MQTT 口径一致的默认值
- GPRS 保留配置位，但不在本轮使用

## 10. 错误处理

### 模拟器

- 串口不可写时明确报错并持续重试
- 输出日志包含设备编码、场景、发送时间

### 采集器

- 半帧、坏帧、CRC 错误要记录并丢弃
- 串口断开时自动重连
- 网关队列文件不可写时要明确告警

### 网关

- MQTT 连接失败时重试
- 单条发送失败时保留原始 JSON，不丢消息
- 转换失败时单独记录坏数据，避免堵塞全部队列

## 11. Windows 运行方式

预期运行环境：

- Windows 10/11
- Python 3.10+
- `pyserial`
- `paho-mqtt`

推荐联调方式：

1. 安装虚拟串口工具，创建一对成对串口，例如 `COM5 <-> COM6`
2. 运行模拟器，向 `COM5` 写帧
3. 运行采集器，从 `COM6` 读帧并写入本地队列
4. 运行 MQTT 网关，将队列内容发到 Broker
5. 启动平台 `mqtt_ingest_worker` 观察入库

## 12. 测试策略

单元测试优先覆盖：

- 帧编码/解码
- CRC 校验
- 统一 JSON 映射
- MQTT payload 映射

集成测试优先覆盖：

- 模拟器生成一条帧，采集器可成功解析
- 采集器输出 JSON 后，网关可成功读取并转换
- 网关发出的 MQTT payload 满足当前 ingest 预期字段

本轮实现时采用 TDD：

- 先写协议与映射测试
- 再写最小实现
- 最后做 Windows 联调说明

## 13. 风险与后续扩展

当前风险：

- Windows 虚拟串口环境依赖本机配置，首次联调可能受驱动影响
- 当前演示帧协议不是实际厂家协议，后续真实接入仍需替换解析器
- 轻量文件队列适合演示和单机验证，不适合高吞吐正式生产

后续扩展方向：

- 在采集器层增加 Modbus RTU 解析器
- 在网关层增加真实 GPRS 模块适配器
- 在统一 JSON 中加入更多补偿器专属字段
- 与现有 `send_capacitor_bank_telemetry.py` 做场景参数复用

## 14. 实现建议

推荐按以下顺序进入实现：

1. 先锁定公共协议与测试样例
2. 先做模拟器的发帧与采集器的收帧闭环
3. 再做统一 JSON 队列
4. 最后做 MQTT 网关上报

这样可以确保每一步都可单独验证，不会三层同时改动导致排错困难。
