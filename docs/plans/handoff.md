# Handoff

## 规范 -> 后端
### 任务
- 按 [PLAN-20260327-application-layer-convergence.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-application-layer-convergence.md) 实施 application 层收敛
- 本轮只允许处理 `devices/data`、`analysis`、`reports` 三条主路径

### 已知信息
- 允许修改目录：
  - `app/application/`
  - `app/api/endpoints/devices/data.py`
  - `app/api/endpoints/analysis.py`
  - `app/api/endpoints/reports.py`
  - 与上述主路径直接相关的 services / schemas / tests
- 重点文件：
  - `app/application/device_reporting.py`
  - `app/application/analysis.py`
  - `app/application/reporting.py`
  - `app/services/device_service.py`
  - `app/services/energy_service.py`
  - `app/services/analysis_service.py`
- 探索线程已确认的问题：
  - endpoint 仍承担权限前置、审计、报表分发与导出装配
  - application 仍存在薄透传
  - service 仍承担跨 service 编排、事务协调或接口级 DTO 装配

### 建议处理方式
- endpoint 层职责只保留：
  - HTTP 协议适配
  - 参数解析
  - Depends 注入
  - 调用 application use case
  - 返回 HTTP response
- application 层职责必须承担：
  - use case 编排
  - 跨 service 协调
  - 主流程统一入口
  - DTO / response / export payload 装配
  - 必要事务边界控制
  - 必要运行态可见性收口
- service 层职责必须回收到：
  - 稳定领域能力
  - 查询能力 / 基础业务能力
  - 不承担多个 service 之间的总调度
  - 不承担 endpoint 级协议适配
- 接口兼容要求：
  - 不做大规模接口路径重命名
  - 不无计划调整前端依赖字段
  - 若返回字段确需变化，必须先写回本文件
- 验证要求：
  - 补充或更新与三条主路径直接相关的测试
  - 验证 endpoint 不再直接编排多个 service
  - 验证 application 不再是纯透传
  - 验证主要接口路径保持兼容
- 明确禁止：
  - 不扩展到 `monitoring`、`telemetry_ingestion`、`forecasting`
  - 不改数据库 schema
  - 不顺手统一全项目 service 命名
  - 不顺手重做异常 / 日志 / repository 体系
  - 不把本轮任务扩成全项目 application 化

---

## 规范 -> 前端
### 任务
- 为 `devices/data`、`analysis`、`reports` 三条主路径的后端收敛做联调准备
- 本轮只做最小适配，不做页面大重构

### 已知信息
- 本轮重点接口：
  - `POST /devices/{device_id}/data`
  - `GET /devices/{device_id}/data`
  - `GET /devices/{device_id}/statistics`
  - `GET /analysis/{device_id}`
  - `GET /reports/export_csv`
- 字段原则：
  - 现有主字段默认保持兼容
  - 导出 CSV 的列顺序、列语义、文件命名规则默认不应无说明变化
  - 若 application 收敛导致返回结构调整，后端必须提前写明变更点

### 建议处理方式
- 前端本轮重点关注：
  - 目标接口路径是否保持兼容
  - 返回字段是否仍满足现有调用
  - 报表导出行为是否保持稳定
- 前端本轮不要做：
  - 页面大改版
  - 状态管理重构
  - 因猜测字段变化而提前改接口适配层
- 若联调发现以下情况，必须先回写 handoff 再动代码：
  - 返回字段删除或重命名
  - 异常语义变化
  - CSV 结构变化
  - 原有路径不兼容

---

## 前端 -> 后端
### 当前建议
- 若前端在联调 `devices/data`、`analysis`、`reports` 时发现字段或异常语义与既有调用不一致，应直接按接口逐条反馈，不要抽象成“大面积前端改造需求”
- 若前端仍依赖旧返回结构，需明确指出是“兼容依赖”，便于后端决定保持兼容还是补充适配层
- 前端已完成依赖审计，当前高优先级联调点如下：
  - `GET /devices/{device_id}/data`
    - 受影响模块：`frontend/src/api/telemetry.ts`、`frontend/src/features/dashboard/composables/useDashboardRealtime.ts`
    - 当前依赖字段：`timestamp`、`flow_rate`
    - 隐式假设：返回仍是“按时间排序的数组”，元素里至少有可解析的 `timestamp`；`flow_rate` 缺失时前端按 `0` 处理
    - 联调提醒：若后端改成 wrapped payload、分页对象或字段改名，必须提前说明
  - `GET /analysis/{device_id}`
    - 受影响模块：`frontend/src/api/telemetry.ts`、`frontend/src/features/dashboard/composables/useDashboardRealtime.ts`、`frontend/src/views/CampusScene.vue`
    - 当前依赖字段：`device_id`、`is_active`、`current_power`、`voltage`、`current`、`today_energy`、`today_cost`
    - 隐式假设：数值字段可直接参与 `Math.abs`、`toFixed` 和状态判断；缺失值会按 `0` 降级
    - 联调提醒：上述字段原则上不要轻易改名；若需调整精度、空值语义或成功/失败结构，必须提前通知
  - `GET /reports/export_csv`
    - 受影响模块：`frontend/src/api/report.ts`、`frontend/src/views/Report.vue`
    - 当前依赖行为：返回可下载 blob；路径与查询参数保持不变；默认文件名规则为 `{report_type}_{YYYYMMDD}.csv`
    - 联调提醒：CSV 列顺序、列语义、编码、`Content-Disposition` 文件名规则若变化，必须提前说明
- 前端建议的最小兼容方式：
  - `devices/data` 与 `analysis` 若必须改返回包装，优先继续保留当前字段名，并允许前端在 api 层解包
  - `reports/export_csv` 优先继续返回 200 + CSV 流，不要切成 JSON 下载任务对象
  - 若后端需要新增 application 层聚合口径，请新增接口，不要直接挤占当前三条兼容接口的主字段语义

---

## 后端 -> 前端
### 当前建议
- 本轮已完成 application 收敛的接口：
  - `POST /devices/{device_id}/data`
  - `GET /devices/{device_id}/data`
  - `GET /devices/{device_id}/statistics`
  - `GET /analysis/{device_id}`
  - `GET /reports/export_csv`
- 已收敛后的调用主线：
  - `devices/data`: endpoint -> `app.application.device_reporting` -> `DeviceService` / `EnergyService`
  - `analysis`: endpoint -> `app.application.analysis` -> `AnalysisService`
  - `reports`: endpoint -> `app.application.reporting` -> `ReportService` / `EnergyRepository`
- 对前端保持兼容的内容：
  - 请求参数未改
  - 主要返回字段未删、未改名
  - `GET /devices/{device_id}/statistics` 仍返回 `success_response(data=...)`
  - `GET /reports/export_csv` 仍返回 CSV 流，文件名规则仍为 `{report_type}_{date}.csv`
  - CSV 列语义和主要列顺序保持不变
- 前端联调建议：
  - 现有页面默认无需改接口路径
  - 若发现 `analysis` 数值显示与旧逻辑存在细微舍入差异，先按字段逐项确认，不要直接扩大为页面重构
  - 若发现报表导出文件名、列头或编码异常，优先核对 `reports/export_csv` 行为，不要先改前端下载逻辑
- 本轮需要前端注意的细微变化：
  - `analysis` 返回仍兼容原字段，但其 DTO 现在由 application 装配，舍入口径固定为 `current_power` 2 位、`voltage` 1 位、`current` 2 位、`today_energy` 2 位、`today_cost` 2 位
  - `reports` 的类型分发和 CSV 组装已转移到 application，若后续新增报表类型，应从 application 层接入，不要再假设 endpoint 内部分支

## 后端 -> 规范
### 当前建议
- 本轮已按 [PLAN-20260327-application-layer-convergence.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-application-layer-convergence.md) 的既定边界实施，无需新增规范。
- 若后续要继续推进 application 收敛，建议保持“按主路径逐条收口”的节奏，不要把本轮结果误解为全项目 application 化已完成。

---

## 探索 -> 规范
### 摘要归档
- 当前问题不是“没有 application 目录”，而是“application use case 过薄、endpoint 过重、service 职责上浮”。
- 第一批只收敛三条主路径：
  - 设备数据上报 / 查询 / 统计
  - 设备分析
  - 报表导出
- 目标是形成清晰的 `endpoint -> application -> service/repository` 调用链，而不是做全项目分层重构。

---

## 规范 -> 全局
### 执行约束
- 本轮核心是“主路径统一”，不是“代码搬家”
- PLAN、`current-status.md`、`handoff.md` 必须一起维护，关键决策不能只留在聊天记录里
- 若 application 收敛未完成，优先保持兼容，不继续扩张范围
