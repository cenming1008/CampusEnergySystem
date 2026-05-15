# 2026-05-15 电容补偿控制器高次谐波频谱交接快照

## 交接结论
- 本系统已具备逐次谐波谱线的后端承载、MQTT 清洗入库、API 返回和前端展示能力。
- 现场接入时，网关应上报：
  - `voltage_harmonics_a/b/c`
  - `current_harmonics_a/b/c`
- 每个字段为数组，元素格式为 `{ "order": 2..31, "value": finite number }`。
- 准真实联调脚本已新增：`scripts/python/send_capacitor_bank_harmonic_uat_payloads.py`。
- 先打印样例：`./venv/bin/python scripts/python/send_capacitor_bank_harmonic_uat_payloads.py --print-only --timestamp 2026-05-15T14:44:21+08:00`。

## 后端/设备接入注意
- 平台不解析 RS-485 / Modbus 原始帧；网关负责寄存器读取、比例换算和单位统一。
- 非法 `order`、非数值 `value` 会被平台丢弃，不影响整条遥测入库。
- 逐次谱线字段进入 `capacitor_bank_telemetry`，不进入公共 `EnergyData`。

## 前端注意
- `谐波趋势` tab 只展示三相电压 THD 与三相谐波电流历史趋势。
- `高次谐波` tab 只展示最新遥测中的 2~31 次谱线。
- 无逐次谱线时，`高次谐波` tab 显示“当前网关未上报 2~31 次谐波谱线”，不影响旧趋势展示。

## 验收建议
- 用 A 相 5 次电压谐波高于 `voltage_harmonic_threshold` 的 payload 验证柱状图超限着色与摘要。
- 用 B 相缺少电流谱线的 payload 验证空态。
- 用旧 CAP-001 payload 验证原 THD 历史趋势不受影响。
- 用 `invalid_spectrum_items_ignored` payload 验证非法阶次和非数值项会被丢弃，整条遥测仍可入库。
