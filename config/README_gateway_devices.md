# 网关设备配置文件说明（gateway_devices.json）

> 本文档说明 `config/` 目录中的设备接入配置文件。若想看整个配置目录的职责，请先看 [README.md](./README.md)。

网关采集器（`scripts/python/device_gateway.py`）启动时会**优先**从本目录的 `gateway_devices.json` 加载设备列表，无需每次改代码。设备按**类别**分组，便于新增和修改。

---

## 如何添加设备

1. 打开 **`config/gateway_devices.json`**。
2. 在对应协议类别下的 **`devices`** 数组中新增一项（复制同类型设备的一项，改字段即可）。
3. 保存文件，**重启网关**（`python scripts/python/device_gateway.py`）后生效。

---

## 配置文件结构

```json
{
  "categories": {
    "modbus_tcp": {
      "_description": "Modbus TCP 电表/仪表",
      "devices": [
        {
          "device_id": 11,
          "device_code": "METER001",
          "name": "智能电表",
          "protocol": "modbus_tcp",
          "host": "192.168.1.100",
          "port": 502,
          "slave_id": 1,
          "registers": { ... }
        }
      ]
    },
    "http": {
      "_description": "HTTP API 设备",
      "devices": [ ... ]
    },
    "serial": {
      "_description": "串口设备",
      "devices": [ ... ]
    }
  }
}
```

- **categories**：按协议或业务分的组，键名可自定义（如 `modbus_tcp`、`A栋电表`）。
- **devices**：该组下的设备列表，每项为一个设备配置对象，格式与原先代码内 `DEVICE_CONFIG` 一致。
- 以 **`_` 开头的键**（如 `_description`）仅作说明，网关会忽略。

---

## 各协议必填/常见字段

| 协议 | 必填 | 其他常用字段 |
|------|------|--------------|
| **modbus_tcp** | device_code, name, protocol, host, port, slave_id, registers | device_id（可选，0 表示后端按 device_code 自动匹配） |
| **http** | device_code, name, protocol, url, field_mapping | device_id（可选） |
| **serial** | device_code, name, protocol, port, baud | 需网关实现 serial 分支后使用 |

---

## 自定义配置文件路径

默认读取 **项目根目录下的 `config/gateway_devices.json`**。若想用其他路径，可设置环境变量：

```bash
export GATEWAY_DEVICES_CONFIG=/path/to/my_devices.json
python scripts/python/device_gateway.py
```

---

## 无配置文件时

若 `config/gateway_devices.json` 不存在或解析失败，网关会使用**代码内的默认配置**（与原先行为一致），并在启动时打印「使用代码内默认设备配置」。
