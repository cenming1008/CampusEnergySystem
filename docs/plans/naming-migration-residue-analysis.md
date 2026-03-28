# Naming Migration Residue Analysis

## 背景

本分析服务于“命名迁移分层治理”主题，目标不是全仓 rename，而是先识别真正会影响当前线程接力的残留位置。

检索关键词：

- `煤矿`
- `矿井`
- `Mine`
- `MineEnergySystem`
- `瓦斯`
- `通风`
- `排水`
- `mine_energy`
- `mine_backend`
- `mine_mqtt`

## 检索结论

### 1. 关键词命中存在明显噪音

- `MineEnergySystem` 命中很多，但大量来自：
  - Markdown 绝对路径
  - 仓库目录名
  - GitHub 仓库 URL
- 这类命中不应直接归入“当前必须改”。

### 2. 当前真正需要分层的是四类位置

1. 用户可见主入口文案
2. 可延后处理的说明文案 / 脚本输出
3. 历史背景或归档材料
4. 已进入运行时契约的基础设施标识

## 残留分层

### 一、当前必须改

这类位置会直接影响当前产品主线表达，若不先治理，后续前端和文档线程容易继续按煤矿叙事扩张。

- `docs/01-新手入门/快速启动指南.md`
  - 标题仍是 `MineEnergySystem`
  - 正文仍写“煤矿综合能源管理系统”
- `docs/01-新手入门/快速启动指南.md`
  - 收尾文案仍写“成功启动煤矿综合能源管理系统”
- `docs/01-新手入门/安装配置完整指南.md`
  - 标题仍以 `MineEnergySystem` 作为对外文档主名
- 主区计划入口
  - 当前需要切到“命名迁移分层治理”主题，避免后续线程继续按旧主题接力

判断标准：

- 用户第一次进入项目时就会看到
- 会影响产品定位和主题判断
- 修改主要是文案与入口，不牵动运行时契约

建议线程：

- 先交给规范锁口径，再交给前端 / 文档线程实现

### 二、可以延后改

这类位置属于旧命名残留，但不是本轮阻塞；可以在规范锁口径后，按低风险批次处理。

- `scripts/python/init_complete_system.py`
  - 启动日志仍写“煤矿综合能源管理系统 - 完整初始化”
- `scripts/python/simulator_unified.py`
  - 终端输出仍写“煤矿综合能源管理系统 - 统一模拟器”
- `scripts/python/generate_prod_secrets.py`
  - CLI 描述仍写 `MineEnergySystem`
- `scripts/shell/start.sh`
  - 终端标题仍写 `MineEnergySystem 启动脚本`
- `scripts/shell/stop.sh`
  - 终端标题仍写 `MineEnergySystem`
- `scripts/shell/status.sh`
  - 终端标题仍写 `MineEnergySystem 服务状态`
- `scripts/shell/pilot_smoke_test.sh`
  - 冒烟标题仍写 `MineEnergySystem 试点联调冒烟检查`

判断标准：

- 用户可见，但不属于 Web 主入口
- 主要影响脚本体验与品牌一致性
- 改动可局部完成，但当前不是最短闭环

建议线程：

- 规范锁口径后，可拆给后端 / 脚本线程做小批量文案修正

### 三、只需标记为历史背景

这类位置带有明确的历史语义或归档性质，不应纳入当前批次清理，只需在主题里标记为“历史实现背景”。

- `frontend/src/three/mine/MineSceneGenerator.ts`
  - 目录名保留 `mine`
  - 注释中仍有“通风设备”等矿区场景表达
- `docs/archive/plans/park-ems-migration-analysis.md`
  - 已明确把矿区叙事降级为历史背景
- `docs/archive/`
  - 多份归档材料保留迁移前上下文

判断标准：

- 已脱离当前主入口
- 主要提供追溯、历史解释或兼容背景
- 若强行清理，会损失上下文或扩大范围

建议线程：

- 当前只需在规范和 handoff 中标注“历史背景，不作为主线”

### 四、暂时不要动

这类位置已经进入运行时契约、联调命令或观测系统，当前若直接 rename，收益低于风险。

- `docker-compose.yml`
- `docker-compose.dev.yml`
- `docker-compose.prod.yml`
  - `mine_energy_db`
  - `mine_backend`
  - `mine_mqtt`
  - `POSTGRES_DB=mine_energy`
- `env.example`
- `env.prod.example`
  - `MQTT_USERNAME=mine_mqtt`
  - `DATABASE_URL=.../mine_energy`
- `app/core/metrics.py`
  - `mine_mqtt_messages_total`
  - `mine_mqtt_processing_duration_seconds`
- `monitoring/prometheus/alert_rules.yml`
  - `mine_energy_backend`
  - `MineBackendDown`
  - `MineMqttIngestionFailures`
- `monitoring/grafana/dashboards/*.json`
  - 查询表达式依赖 `mine_mqtt_*`
- 各类脚本中的容器名与数据库名判断

判断标准：

- 影响 Docker、数据库、MQTT、Prometheus、Grafana、脚本自动化或联调命令
- 任何 rename 都可能造成破坏性变更
- 必须单独立项，不能在命名探索轮顺手做

建议线程：

- 当前只记录风险，不进入实现
- 后续若真要迁移，必须升级为“规范 -> 探索 -> 后端 / 脚本 -> 验收”的专项主题

## 最强假设

当前最需要解决的不是“煤矿残留还很多”，而是“不同层级的残留被混在同一个 rename 任务里”。只要先把入口文案、历史背景和运行时标识拆开，后续线程就能避免一上来做高风险全仓替换。

## 建议线程路径

- 当前主路径：`探索 -> 规范 -> 前端 -> 验收`
- 可选支路：规范确认后，再拆一轮 `规范 -> 后端/脚本 -> 验收` 处理低风险终端文案
- 不建议当前进入：基础设施命名迁移专项

## 非目标提醒

- 不把 `MineEnergySystem` 的路径命中当成文案问题统一替换
- 不改 Docker 容器名、数据库名、MQTT 用户名、Prometheus 指标名
- 不清理 `docs/archive/`
- 不把 `frontend/src/three/mine/` 扩成 3D 场景重构
