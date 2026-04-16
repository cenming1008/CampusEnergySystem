# Windows RS485 设备栈

这个目录包含一套面向 Windows 的、最小可运行的 RS485 设备链路。

当前包含的辅助模块：

- `rs485_device_simulator.py`：生成确定性的模拟遥测数据，并输出 RS485 风格帧
- `edge_collector.py`：从串口读取帧、做标准化处理，并写入 JSONL 队列记录
- `mqtt_gateway.py`：读取队列记录，并将平台侧 payload 发布到 MQTT

这些辅助模块现在已经接上了轻量的 `--config` CLI 入口，因此模拟器、采集器和网关都可以在 Windows 上作为独立的常驻进程运行。

## 安装依赖

请使用 Python 3.10+ 环境，并安装这套链路运行所需的两个依赖包：

```bash
python -m pip install pyserial paho-mqtt
```

如果你是在仓库自带虚拟环境中工作，先激活虚拟环境，再执行上面的安装命令。

## 准备虚拟 COM 口

请先在 Windows 上创建一对成对的虚拟串口，例如：

- `COM5 <-> COM6`

其中一端给模拟器使用，另一端给采集器使用。具体端口号可以不同，但示例配置默认假设：

- 模拟器使用 `COM5`
- 采集器使用 `COM6`

## 示例配置

可以从 `config.example.json` 开始，按需复制成你自己的本地运行配置，再修改端口、队列路径或 MQTT 地址。

示例配置中的 MQTT topic 与平台 ingest 契约保持一致：

- `campus/telemetry`

## 运行流程

完整链路如下：

1. 启动 MQTT Broker，并确认能够连通。
2. 启动模拟器，占用虚拟串口的一端。
3. 启动采集器，占用配对串口的另一端。
4. 启动网关，让它持续消费 JSONL 队列并发布到 MQTT。

启动命令：

```bash
python scripts/python/windows_device_stack/rs485_device_simulator.py --config scripts/python/windows_device_stack/config.example.json
python scripts/python/windows_device_stack/edge_collector.py --config scripts/python/windows_device_stack/config.example.json
python scripts/python/windows_device_stack/mqtt_gateway.py --config scripts/python/windows_device_stack/config.example.json
```

三个进程会读取同一个 JSON 配置文件，但只消费各自对应的配置段：

- `simulator`：打开配置中的串口，生成确定性测点，转换成 RS485 帧，并按 `interval_seconds` 周期持续写入
- `collector`：打开配置中的串口，持续读取字节流，直到识别出完整的 `<...>` 帧；随后解析测点，向 `collector.cache_file` 追加一条 JSONL 记录；若发生临时串口打开失败或运行时异常，会按 `retry_interval_seconds` 做重试
- `gateway`：轮询 `gateway.queue_file`，只发布尚未读取过的行到 MQTT；同时把字节偏移游标持久化到 `gateway.cursor_file`；若发生临时 MQTT 连接失败或运行时异常，会按 `retry_interval_seconds` 做重试

## 验证方式

链路跑起来后，可以重点检查这些信号：

- 采集器队列文件持续写入 JSONL 记录
- 网关持续向 `campus/telemetry` 发布消息
- 平台 ingest worker 能收到 `device_code`、`reactive_power`、`power_factor`、`temperature` 等字段

## 说明

- 运行队列文件建议放在 `./runtime/` 或其他本地可写目录下
- 相对路径形式的队列文件和游标文件，都会以配置文件所在目录为基准做解析
- 运行时的时间戳来自模拟器每次循环时的当前系统时间；`tick` 只用于影响确定性的波形变化，不再用于人为推进未来时间
- 当前这套链路中的网关正式上行方式只支持 MQTT；GPRS 目前只保留配置占位
- 三个脚本被刻意拆开，目的是让每一层后续都可以独立替换
- `pyserial` 只会在模拟器和采集器真正进入运行路径时按需导入
- `paho-mqtt` 只会在网关真正进入运行路径时按需导入
- 采集器当前默认使用“以 `<` 开始、以 `>` 结束”为完整帧边界的演示协议，不包含更复杂的异常恢复逻辑
- 采集器和网关当前使用的是最小固定间隔重试，不是完整的退避重连框架
- 只要保留 `gateway.cursor_file`，网关就能避免在当前运行期间以及后续重启后重复发布已经消费过的队列记录
