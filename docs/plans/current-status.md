# Current Status

## 当前总目标
- 评估当前项目从“煤矿综合能源管理系统”迁移为“园区综合能源管理系统 / 智慧园区 EMS”的可行性
- 梳理哪些能力可以直接复用，哪些只是命名与叙事需要迁移
- 为前端线程和后端线程输出可直接执行的最小迁移任务

---

## 当前阶段
- [x] 分析中
- [x] 前端迁移中
- [x] 后端迁移中
- [x] 已输出迁移分析

---

## 本次目标
- 统一用户可见站点名、默认应用名与入口命名，继续从“煤矿综合能源管理系统”收敛到“园区综合能源管理系统 / Campus EMS”
- 将后端主线业务对象从煤矿叙事迁移到园区 EMS 语境
- 在不推翻现有模型的前提下，补齐园区 / 区域 / 楼栋 / 能源介质 / 分项 / 告警聚合接口
- 保留旧接口兼容，优先新增园区聚合层，并更新 `current-status.md` / `handoff.md`

## 发现的问题
- 后端底座模型已可复用，但缺少一个明确面向“园区 / 区域 / 楼栋 / 能源介质 / 分项 / 告警”的聚合接口层。
- `LocationType` 已有 `building/area/zone`，但还没有 `park/campus/site` 这些园区主线对象表达。
- 旧接口 `/energy/*`、`/locations/*`、`/analysis/{device_id}` 仍偏底座能力，前端若直接拼装，会继续缺少稳定的园区驾驶舱口径。
- 默认应用名仍是“煤矿综合能源管理系统”，会把 OpenAPI 与系统默认描述拉回旧叙事。

## 最近结论
### 探索线程
- 当前项目迁移到园区 EMS 的可行性高。
- 迁移成本整体偏中低，更像“保留底座、迁移叙事”，不是推倒重写。
- 前端绝大部分业务页面、后端绝大部分对象和接口、部署链路、监控链路、权限链路都可以直接复用。
- 真正需要优先迁移的是：
  - 项目名称与主文案
  - 首页与导航主线
  - 园区 / 区域 / 楼栋聚合表达
  - 煤矿数字孪生模块的主线降级

### 前端线程
- 可以直接复用设备、位置、告警、能耗、巡检、维护、报表、系统设置等主页面。
- 首页、登录页、`CampusScene`、菜单与品牌文案是迁移优先级最高的区域。
- 本轮已完成主入口迁移：
  - `Layout.vue` / `router/index.ts` 已切到园区 EMS 菜单与页面标题
  - `Dashboard.vue` 已改为园区能源驾驶舱表达
  - `Login.vue` 已改成园区 EMS 品牌登录页
  - `CampusScene.vue` 已承接“园区总览与实时态势”表达
  - `SystemSettings.vue` 已同步改成园区 EMS 产品说明

### 后端线程
- 可以直接复用位置、设备、能耗、告警、碳排放、维护、巡检、预测、审计、权限、接入健康等底座能力。
- 已完成本轮最小迁移：
  - `LocationType` 新增 `park/campus/site`，位置主线对象可直接表达园区层级
  - 新增 `/campus/*` 聚合接口，服务园区总览、区域/楼栋统计、能源介质占比、分项统计、实时负荷趋势、告警汇总
  - 保留旧 `/energy/*`、`/locations/*`、`/analysis/{device_id}` 接口兼容
  - 默认 `app_name` 与 FastAPI 描述已切换为园区 EMS 语境

---

## 当前阻塞点
- `README.md`、功能文档、部署文档和脚本说明中的煤矿语义仍然较多，后续如果只改页面不改文档，会继续造成认知撕裂。
- 历史 `MineScene` 相关 3D 能力短期不一定删除，但若继续以煤矿命名暴露在主导航，会持续把产品认知拉回矿区方向。
- 若后端后续不补园区 / 区域 / 楼栋聚合接口，前端即使完成文案迁移，也很难真正形成园区 EMS 主线体验。

---

## 当前待办

### 探索线程
- [x] 输出园区 EMS 迁移分析文档
- [x] 给出前后端最小迁移任务
- [x] 更新 `current-status.md` / `handoff.md`

### 前端线程
- [x] 将首页改造成园区能源驾驶舱
- [x] 将“矿区总览”降级或改造为“园区总览”
- [x] 统一菜单、登录页、系统标题和页面文案的园区 EMS 语境

### 后端线程
- [x] 保留现有模型底座，优先补园区 / 区域 / 楼栋聚合接口
- [x] 审视默认配置和对象描述中的煤矿语义，逐步切换到园区 EMS 语境
- [x] 不扩大煤矿专属兼容能力的影响面

---

## 修改文件
- frontend/index.html
- frontend/src/router/index.ts
- frontend/src/layout/Layout.vue
- frontend/src/views/CampusScene.vue
- env.example
- env.local.example
- env.prod.example
- README.md
- app/__init__.py
- app/api/README.md
- monitoring/grafana/provisioning/dashboards/dashboards.yml
- monitoring/grafana/dashboards/campus_overview.json
- monitoring/grafana/dashboards/api_reliability.json
- monitoring/grafana/dashboards/logs_overview.json
- monitoring/grafana/dashboards/mqtt_observability.json
- app/models/tables.py
- app/core/settings.py
- app/main.py
- app/api/endpoints/__init__.py
- app/api/endpoints/locations.py
- app/api/endpoints/campus.py
- app/api/router_registry.py
- app/services/__init__.py
- app/services/campus_service.py
- tests/test_campus_endpoints.py
- tests/test_location_types.py
- docs/plans/current-status.md
- docs/plans/handoff.md

---

## 验证结果
- 已收敛本轮命名范围：优先修改用户可见站点名、默认应用名、路由 URL 与低风险仪表盘文件名，暂未动数据库名、MQTT topic、监控指标前缀等兼容层。
- 已阅读 `docs/guides/product-positioning.md`、`docs/guides/backend-guidelines.md`、`docs/plans/park-ems-migration-analysis.md`。
- 已执行 `python3 -m compileall -q app tests`，编译通过。
- 已执行 `./venv/bin/python -m unittest tests.test_campus_endpoints tests.test_location_types tests.test_layer_exports`，测试通过。
- 已执行 `./venv/bin/python -c "import app.main; print('ok')"`，主应用导入通过。
- 本轮新增园区聚合接口，未删除旧接口，未推翻数据库结构。

---

## 剩余风险
- `CampusService` 当前是兼容型聚合层，区域/楼栋统计和分项统计主要依赖现有 `Location` 祖先链、`Device.device_category` 与 `EnergyData` 汇总，后续若要更精细口径，仍建议补专门的分项模型或统计表。
- MQTT topic、数据库名、指标前缀等深层历史命名本轮未改，避免影响既有运行链路。
- `park/campus/site` 已加入位置类型，但现有存量数据不会自动迁移为这些类型，前端若要展示真实园区层级，还需要配合新增或整理位置数据。
