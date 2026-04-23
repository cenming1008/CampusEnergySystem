# Application 层说明

本文档描述 `app/application/` 的职责边界、当前模块分工、主调用链以及后续新增 use case 的落点规则。

当前项目产品定位已统一为“园区综合能源管理系统 / 智慧园区 EMS”。  
`application` 层的目标不是做一个新的“大 service 层”，而是把一次完整的用户意图、接口主流程或系统内部工作流，稳定收口成可复用、可测试、可演进的 use case 入口。

---

## 1. 这一层解决什么问题

在当前后端分层中：

- `api/` 负责 HTTP / WebSocket 协议适配
- `services/` 提供稳定业务能力与查询能力
- `repositories/` 负责数据访问
- `domain/` 负责纯业务规则与领域逻辑
- `application/` 负责 use case 编排

`application` 层适合承接以下职责：

- 一次完整业务动作的主流程入口
- 多个 service 之间的调用编排
- 访问前置、权限校验、必要审计的统一收口
- 接口级 DTO / 导出 payload / 响应数据装配
- 面向“用户意图”或“系统工作流”的稳定用例边界

`application` 层不应该承接：

- HTTP 参数解析、`Depends` 注入、状态码拼装
- ORM 查询细节或 SQL 细节
- 纯领域计算本身
- 到处透传、没有编排价值的壳函数

一句话理解：

`application` 关心“这次要完成什么业务动作”；  
`service` 关心“这类能力怎么做”；  
`api` 关心“这个动作怎样通过 HTTP 暴露出去”。

---

## 2. 当前目录结构

```text
app/application/
├── __init__.py
├── analysis.py
├── device_reporting.py
├── energy_management.py
├── reporting.py
└── telemetry_ingestion.py
```

各文件当前定位如下：

| 文件 | 当前职责 | 典型调用方 |
|------|------|------|
| `device_reporting.py` | 设备数据上报、历史查询、统计查询 use case | `api/endpoints/devices/data.py` |
| `analysis.py` | 单设备分析 use case，负责访问前置与结果 DTO 装配 | `api/endpoints/analysis.py` |
| `reporting.py` | 报表查询与 CSV 导出 payload 组装 | `api/endpoints/reports.py` |
| `energy_management.py` | 通用能源统计、碳排放汇总等 use case | `api/endpoints/energy/*` |
| `telemetry_ingestion.py` | 遥测接入内部工作流：接收、落库、告警、健康状态更新、广播数据准备 | MQTT / 接入链路 |
| `__init__.py` | 统一导出 application 对外 use case 入口 | 其他模块 import |

---

## 3. 当前主线 use case 说明

### 3.1 `device_reporting.py`

面向“设备数据主路径”的 use case 集合，当前已承接三类动作：

- `report_device_data_use_case(...)`
- `get_device_data_use_case(...)`
- `get_device_statistics_use_case(...)`

这类 use case 的特点：

- 面向具体设备主线
- 会做统一设备访问校验
- 会决定主流程该调哪个 service
- 会把 endpoint 不该承担的主流程动作收回来

适用场景：

- 前端或外部接口按设备写入一条能耗/流量/电参数据
- 查询设备历史数据
- 查询设备按时间粒度统计结果

当前边界：

- 权限前置放在 use case
- 具体数据保存与统计能力仍由 `DeviceService` / `EnergyService` 提供
- payload 规范化使用 `domain/device_payloads.py`

---

### 3.2 `analysis.py`

面向“设备分析”主路径，当前核心入口为：

- `analyze_device_use_case(...)`

这个 use case 当前承担：

- 设备访问前置
- 调用 `AnalysisService`
- 将 service 输出收口为稳定的分析 DTO

当前返回口径围绕前端主页面直接依赖的字段组织，例如：

- `device_id`
- `is_active`
- `current_power`
- `voltage`
- `current`
- `today_energy`
- `today_cost`

这意味着：

- 设备分析的“接口展示口径”应该优先在 `application` 控制
- `AnalysisService` 更适合专注分析计算和快照获取

---

### 3.3 `reporting.py`

面向“报表导出”主路径，当前包含两类能力：

1. 报表行查询 use case
2. CSV 导出 payload 组装 use case

关键入口包括：

- `list_energy_report_rows_use_case(...)`
- `list_alarm_report_rows_use_case(...)`
- `list_carbon_report_rows_use_case(...)`
- `build_report_csv_export_use_case(...)`

这一层当前负责：

- 统一 `report_type` 分发
- 固定 CSV 表头定义
- 调用 `ReportService` 获取不同报表行数据
- 组装最终的文件名与 CSV 文本内容

这里是典型的 application 适配点，因为：

- endpoint 不应该自己写复杂分支和导出逻辑
- service 不应该关心 HTTP 导出的文件名与表头结构

---

### 3.4 `energy_management.py`

面向通用能源数据与碳排放主线，当前 use case 以“统一入口”形式存在：

- `save_energy_data_use_case(...)`
- `get_energy_statistics_use_case(...)`
- `get_carbon_summary_use_case(...)`
- `list_carbon_emissions_use_case(...)`

目前这一层仍偏轻量，但已经提供了稳定入口，适合继续承接：

- 能源统计口径统一
- 园区 / 区域 / 楼栋聚合前的中间编排
- 多能源介质统一查询入口

---

### 3.5 `telemetry_ingestion.py`

面向“系统内部遥测接入链路”的工作流 use case，当前核心入口：

- `ingest_telemetry_use_case(...)`

该 use case 代表的不是单纯查询，而是一条内部处理流水线。它适合放在 `application` 的原因是：

- 它天然是多步骤工作流
- 会协调多类 service
- 会把最终广播所需的数据结构一次性准备出来

当前关注点包括：

- 接入健康状态记录
- 单条遥测数据落库
- 告警触发
- 广播 payload 构造

这类内部工作流是 `application` 层非常典型的承载对象。

---

## 4. 当前推荐调用链

### HTTP 主路径

推荐链路：

```text
endpoint -> application use case -> service / repository -> model / result
```

例如：

```text
GET /analysis/{device_id}
  -> app/api/endpoints/analysis.py
  -> analyze_device_use_case(...)
  -> AnalysisService.analyze_device(...)
```

```text
GET /reports/export_csv
  -> app/api/endpoints/reports.py
  -> build_report_csv_export_use_case(...)
  -> ReportService.list_*_report_rows(...)
```

```text
POST /devices/{device_id}/data
  -> app/api/endpoints/devices/data.py
  -> report_device_data_use_case(...)
  -> DeviceService / EnergyService
```

### 系统内部主路径

推荐链路：

```text
integration / worker -> application use case -> service -> broadcast / result
```

例如：

```text
MQTT 消息
  -> 接入处理器
  -> ingest_telemetry_use_case(...)
  -> AlarmService / IngestionHealthService / 数据保存能力
```

---

## 5. 这一层和其他层怎么分工

### `application` vs `api`

应该放在 `api`：

- `APIRouter`
- `Depends`
- 查询参数定义
- `HTTPException`
- `StreamingResponse`
- 请求体验证

应该放在 `application`：

- 权限前置的统一收口
- 主流程编排
- 导出 payload 组装
- 面向前端主流程的 DTO 装配

判断方法：

如果去掉 HTTP 之后，这段逻辑仍然成立，它大概率应该在 `application`。  
如果这段逻辑只有在 FastAPI 路由里才成立，它大概率应该留在 `api`。

### `application` vs `service`

应该放在 `service`：

- 单类稳定业务能力
- 查询能力
- 对单个聚合或单类对象的操作
- 可复用的基础业务规则执行

应该放在 `application`：

- 协调多个 service
- 统一业务入口
- 决定主流程先后顺序
- 组织最终对外返回结构

判断方法：

如果这段逻辑可以被多个 use case 复用，它更像 `service`。  
如果它只是在完成“一次完整动作”，它更像 `application`。

### `application` vs `domain`

应该放在 `domain`：

- 与框架无关的纯规则
- 可单独测试的纯逻辑
- 领域对象规范化与业务约束

应该放在 `application`：

- 调用领域规则并把它放进完整工作流里

---

## 6. 新增 use case 的落点规则

后续新增功能时，优先按下面顺序判断是否需要进入 `application`：

### 6.1 适合新增到 `application` 的情况

- 一个 endpoint 需要协调多个 service 才能完成
- 一个流程既要做校验，又要查数据，又要装配导出内容
- 一个内部任务包含多个步骤和副作用
- 一个页面主流程需要稳定、可复用的聚合结果
- 一个主路径需要对外提供“统一入口”

### 6.2 不适合新增到 `application` 的情况

- 只是把 service 包一层透传
- 只是一个简单查询，且没有编排价值
- 只是某个 service 的内部私有辅助函数
- 只是 HTTP 参数转换

### 6.3 新增文件前先问自己

1. 这是一个完整业务动作，还是一个可复用能力？
2. 它是否需要协调多个 service 或外部适配器？
3. 它是否需要统一装配返回 DTO / 导出 payload？
4. 如果没有 application，这段逻辑会不会继续堆回 endpoint？

如果 2、3、4 的答案大多是“会”，通常就该进入 `application`。

---

## 7. 命名建议

当前目录以“按业务主路径拆文件”为主，这个方向建议继续保持。

推荐命名：

- 文件名：用业务主线命名  
  例如：`device_reporting.py`、`reporting.py`
- 用例函数：`xxx_use_case`
- 返回结构：优先小而明确，可用 `dataclass` 或稳定字典口径

不建议：

- `utils.py`
- `manager.py`
- `handler.py`
- `process.py`

除非其职责非常明确，否则这些名字很容易再次把边界做模糊。

---

## 8. 当前已知边界现状

截至当前仓库状态，`devices/data`、`analysis`、`reports` 三条主路径已经完成第一批收敛，但 `application` 层整体仍不是“全项目已完成态”。

仍需注意：

- `energy_management.py` 整体还偏轻量，后续如出现更复杂园区聚合流程，可继续增强
- `telemetry_ingestion.py` 属于内部主流程，后续如果接入链路继续扩展，应继续保持它作为统一工作流入口
- `three` 等前端主线页面如果需要稳定聚合口径，后端应优先新增稳定 use case / 聚合接口，而不是把逻辑继续堆回 endpoint

---

## 9. 推荐协作方式

当后端线程要改一条主路径时，建议按下面顺序工作：

1. 先确认这个动作是不是 use case，而不是 service helper
2. 先确认 endpoint 是否已经过重
3. 把主流程收口到 `application`
4. 只把稳定能力留给 `service`
5. 保持接口兼容
6. 更新测试
7. 回写 `docs/plans/current-status.md` 与 `docs/plans/handoff.md`

---

## 10. 相关文件

- [app/README.md](/Users/todo/MineEnergySystem/app/README.md)
- [app/application/__init__.py](/Users/todo/MineEnergySystem/app/application/__init__.py)
- [docs/guides/backend-guidelines.md](/Users/todo/MineEnergySystem/docs/guides/backend-guidelines.md)
- [docs/plans/PLAN-20260327-application-layer-convergence.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260327-application-layer-convergence.md)
- [docs/plans/current-status.md](/Users/todo/MineEnergySystem/docs/plans/current-status.md)
- [docs/plans/handoff.md](/Users/todo/MineEnergySystem/docs/plans/handoff.md)
