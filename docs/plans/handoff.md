# Handoff

## 当前主题
- 当前主主题：设备分类与对象分层建模优化
- 当前执行依据：
  - [PLAN-20260328-device-classification-modeling-optimization.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-optimization.md)
  - [PLAN-20260328-device-classification-modeling-audit.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260328-device-classification-modeling-audit.md)（保留为探索输入，不替代正式 PLAN）

---

## 规范 / 验收 -> 前端
### 当前任务
- 若继续推进本主题，前端只做真实联调核对和最小兼容修正，不新开页面重构。

### 当前仍有行动价值的信息
- 不要再把 `device_type` 单独当成完整对象模型。
- 不要继续通过 `device_type / device_category / energy_type` 和 `EnergyData` 宽表字段“是否有值”直接猜对象语义。
- 联调时优先核对后端已补的对象语义字段与边界字段，包括：
  - `object_role`
  - `metering_role`
  - `point_kind`
  - `measurement_subject`
  - `public_fields`
  - `specialized_fields`
  - `null_field_rule`
  - `device_object_boundary`

### 仅允许的下一步
- 核对 `DeviceManager.vue`、`EnergyManagement.vue`、`Dashboard.vue`、`CampusScene.vue` 是否仍误把旧字段当完整语义。
- 若发现兼容问题，只补最小消费说明或最小适配，不扩成页面改版。

---

## 规范 / 验收 -> 后端
### 当前任务
- 若继续推进本主题，后端只处理真实联调暴露的兼容问题，不扩张新 schema 设计。

### 当前仍有行动价值的信息
- 当前必须继续以兼容层方式维护第一批对象语义，不把本轮误判为“已完成独立 meter / point / relation schema”。
- 若联调继续暴露问题，优先核对两类风险：
  - `device_registry` 已声明字段与 schema / payload / model 实际承接能力是否一致
  - 接口返回是否仍会诱导前端用旧标签和宽表字段猜对象语义

### 仅允许的下一步
- 只做兼容修正、边界说明补齐、返回语义澄清。
- 不做接口路径重命名。
- 不做全量数据库 schema 重构。

---

## 验收 -> 规范
### 当前任务
- 在下一次验收动作中，判断本主题是否正式收口，以及 audit 是否继续保留在 `docs/plans/`。

### 验收关注点
- 正式 PLAN 是否仍能独立承担执行依据。
- `current-status.md`、`handoff.md`、正式 PLAN 三者是否继续一致。
- 是否还存在必须保留在主区的行动项；若无，应执行主题收口判断。

---

## 每日归档入口

- [2026-03-27 交接快照](./daily/2026-03/2026-03-27-handoff.md)
- [2026-03-28 交接快照](./daily/2026-03/2026-03-28-handoff.md)
