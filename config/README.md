# config 目录说明

`config/` 用来存放“项目运行时会读取的本地配置文件”。

这里的配置和 `.env` 不一样：

- `.env` 负责环境变量，比如数据库地址、端口、密钥
- `config/` 负责系统侧运行时会读取的结构化 JSON 配置，比如报警阈值

## 当前文件

| 文件 | 用途 | 读取方 |
|------|------|--------|
| `settings.json` | 报警阈值配置 | `AlarmService.load_thresholds()` |

## 推荐理解

### `settings.json`

这是“业务阈值配置”。

当前主要给报警逻辑使用，例如：
- 默认电压上下限
- 默认电流上限
- 某些设备的单独阈值覆盖

对应代码位置：
- [app/services/alarm_service.py](/Users/todo/CampusEnergySystem/app/services/alarm_service.py)

## 设备侧网关配置边界

当前系统侧以 MQTT 入站消息作为设备接入边界，不再维护本地设备采集网关清单。
Modbus、串口、HTTP 轮询等设备侧网关配置应由设备侧网关或现场工控机工程维护，不放在本系统侧 `config/` 目录中。

## 使用建议

- 改报警阈值：编辑 `settings.json`
- 改真实设备接入：调整设备侧网关或工控机工程，并确保 MQTT topic / payload 与系统侧约定一致
- 改数据库、端口、JWT、MQTT 地址：编辑 `.env`，不是这里

## 后续整理原则

这个目录建议继续保持“小而清楚”：

- 只放系统侧运行时实际读取的 JSON 配置
- 每个 JSON 最好只负责一类事情
- 配套说明文档放在同目录或 docs 中
- 不把脚本、日志、备份文件混进来
