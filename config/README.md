# config 目录说明

`config/` 用来存放“项目运行时会读取的本地配置文件”。

这里的配置和 `.env` 不一样：

- `.env` 负责环境变量，比如数据库地址、端口、密钥
- `config/` 负责结构化 JSON 配置，比如报警阈值、网关设备清单

## 当前文件

| 文件 | 用途 | 读取方 |
|------|------|--------|
| `settings.json` | 报警阈值配置 | `AlarmService.load_thresholds()` |
| `gateway_devices.json` | 网关采集设备清单 | `scripts/python/device_gateway.py` |
| `README_gateway_devices.md` | 网关设备配置说明 | 人工查看 |

## 推荐理解

### 1. `settings.json`

这是“业务阈值配置”。

当前主要给报警逻辑使用，例如：
- 默认电压上下限
- 默认电流上限
- 某些设备的单独阈值覆盖

对应代码位置：
- [app/services/alarm_service.py](/Users/todo/MineEnergySystem/app/services/alarm_service.py)

### 2. `gateway_devices.json`

这是“外部设备接入配置”。

当前主要给设备网关采集脚本使用，例如：
- Modbus TCP 设备地址
- HTTP 设备接口地址
- 串口设备参数
- 字段映射、寄存器配置

对应代码位置：
- [scripts/python/device_gateway.py](/Users/todo/MineEnergySystem/scripts/python/device_gateway.py)

## 使用建议

- 改报警阈值：编辑 `settings.json`
- 改真实设备接入：编辑 `gateway_devices.json`
- 改数据库、端口、JWT、MQTT 地址：编辑 `.env`，不是这里

## 后续整理原则

这个目录建议继续保持“小而清楚”：

- 只放运行时 JSON 配置
- 每个 JSON 最好只负责一类事情
- 配套说明文档放在同目录或 docs 中
- 不把脚本、日志、备份文件混进来
