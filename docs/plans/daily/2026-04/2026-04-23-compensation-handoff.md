# 2026-04-23 Compensation Handoff

## 当前主题
- `设备监控页实时数据语义收敛专题` 的 `P1` 第一轮字段真实化收口

## 当前结论
- 已确认根因不是“监控聚合不会用 profile”，而是 `CapacitorBankControlProfile` 模型与数据库列不完整，导致 MQTT 已提取的参数快照字段在写入阶段被静默丢弃。
- 当前已补齐模型、schema sync、必需列断言、控制档案响应 schema 与监控聚合优先级。
- 当前已实际压缩的监控来源：
  - `control_mode`
  - `circuit_summary.running_count`
  - `capacity_utilization`
  - `temperature_health`
- 前端补偿监控来源文案已同步支持 `profile` 来源，避免 UI 继续把“参数快照回读”误标为估算值。

## 下一棒
- 交给后端/设备联调角色：
  - 结合真实设备或网关报文确认 `control_mode / running_circuit_count` 的快照字段是否与现场协议长期一致
  - 结合真实设备或网关报文确认 `temp_alarm / temperature_upper_limit` 是否长期稳定可用，必要时重调温度健康度判定规则
- 交给验收角色：
  - 重新判断 `P1` 是否已达到“关键监控指标第一阶段真实化已通过，剩余只保留更高门槛问题”的阶段结论
  - 不要把本轮通过误判成“正式交付完成”

## 禁止扩张
- 不把本轮 profile 回退收口顺手扩成补偿器全链路大重构。
- 不因为 `P1` 第一轮已通过，就跳过真实设备/网关协议闭环验证。
- 不在没有联调证据的前提下，把高风险控制动作边界默认为可开放。
