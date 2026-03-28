# PLAN-20260328-naming-migration-layering

> 状态：进行中（主入口 + 低风险脚本/后端文案修正已阶段验收通过，主题继续保留） | 负责人：待定 | 更新时间：2026-03-28

---

## 背景

项目产品定位已经收敛到“园区综合能源管理系统 / 智慧园区 EMS”，但仓库内仍残留多类旧命名：

- 用户可见文案中的“煤矿 / 矿区 / Mine”
- 仓库名与绝对路径里的 `MineEnergySystem`
- 运行时标识中的 `mine_energy / mine_backend / mine_mqtt`
- 历史 3D 模块中的 `mine` 目录与矿区场景语义

当前风险不是“还没 rename 干净”，而是这些残留位于不同层级：

1. 有些会直接误导前端和文档线程继续沿用煤矿叙事。
2. 有些只是仓库路径、历史背景或归档材料，不能当作当前阻塞。
3. 有些已经进入 Docker、数据库、监控指标、脚本和默认凭据，贸然替换会引入联调与运维破坏。

因此本轮必须先完成“命名迁移探索、范围分层和线程分流”，而不是直接做全仓 rename。

探索已确认：

- 当前 `docs/plans/` 主主题仍停留在“设备分类与对象分层建模优化”，与本轮“命名迁移分层治理”不是同一主题。
- `MineEnergySystem` 这个关键词在检索结果中大量来自绝对路径和仓库名引用，属于高噪音项，不能直接当作需要改名的语义残留。
- 当前真正需要优先处理的是主入口用户可见命名、主题边界和线程实施顺序，而不是数据库名、容器名、MQTT 用户名或 Prometheus 指标前缀。

---

## 目标

- 建立“命名迁移分层治理”正式 PLAN，避免后续线程把本轮误做成全仓替换。
- 明确哪些残留属于“当前必须改 / 可以延后改 / 只需标记为历史背景 / 暂时不要动”。
- 锁定后续线程路径，默认先走 `探索 -> 规范 -> 前端 -> 验收`，必要时再拆出低风险脚本 / 后端文案修正。
- 为前端、后端、规范线程提供统一边界，避免聊天依赖。

## 正式术语与命名边界

- 中文主名：园区综合能源管理系统
- 英文主名：Campus Energy Management System
- 允许简称：园区 EMS / 智慧园区 EMS
- 禁止作为当前主名继续扩写的旧命名：
  - `MineEnergySystem`
  - `Mine`
  - 煤矿综合能源管理系统
  - 矿区能源管理系统

四类残留口径：

1. 当前必须改：主入口、导航、正式文档、正式计划主题、会误导当前产品定位的对外展示文案
2. 可以延后改：低风险脚本标题、帮助文字、初始化说明、非主入口文案
3. 只需标记为历史背景：归档材料、历史分析、旧 3D 模块与历史矿区语义
4. 暂时不要动：数据库名、容器名、环境变量键名、MQTT 用户名或 topic、Prometheus 指标或告警名、Grafana 查询、脚本依赖的运行时标识

## 非目标

- 不做全仓 rename。
- 不在本轮修改数据库名、容器名、MQTT 用户名、默认 topic、监控指标名或已有告警规则名。
- 不把历史归档、历史分析、历史 3D 模块直接删除。
- 不借本轮顺手展开前后端大规模实现或架构重构。

## 范围

涉及目录或模块：

- `docs/plans/`
- `docs/guides/`
- `README.md`
- `docs/01-新手入门/`
- `frontend/src/views/`
- `frontend/src/layout/`
- `frontend/src/router/`
- `frontend/src/three/mine/`
- `app/core/settings.py`
- `scripts/python/`
- `scripts/shell/`
- `docker-compose.yml`
- `docker-compose.dev.yml`
- `docker-compose.prod.yml`
- `env.example`
- `env.prod.example`
- `monitoring/`

明确不改动：

- `docs/archive/`
- `docs/plans/daily/`
- 设备对象分层主题相关代码实现
- 运行中的数据库 / MQTT / 监控契约

本轮允许动作：

- 锁定正式产品名、英文名、简称和旧命名禁用边界
- 统一主入口、正式计划和接力文档的主题表达
- 为前端 / 文档线程提供“只改用户可见主入口命名”的实施依据

本轮非目标补充：

- 不做仓库目录名、Git 仓库 URL 或绝对路径批量替换
- 不把脚本文案修正升级成脚本入口重构
- 不把历史矿区 3D 模块升级成新的产品主线

## 实施步骤

1. 探索线程先完成残留检索、噪音区分、范围分层，并把线程路径与非目标写回主区。
2. 规范线程锁定正式术语、四类残留分类口径、允许修改层级与禁止触碰层级。
3. 前端线程只处理用户可见主入口命名与导航表达，禁止扩成页面重构或 3D 模块推倒。
4. 后端 / 脚本线程仅在规范锁定后，处理低风险默认文案与说明文字；运行时标识另开后续专题。
5. 验收线程按 PLAN、`current-status.md`、`handoff.md` 核对是否达到“入口命名迁移分层已锁定、实现边界已清楚”的阶段完成。

## 风险与回滚

- 风险：把仓库路径中的 `MineEnergySystem` 误判为产品命名残留
  - 应对：区分“路径 / 仓库名 / 文案 / 运行时标识 / 历史模块”五类位置，优先处理文案和主入口。
- 风险：把 `mine_energy / mine_backend / mine_mqtt` 当作低风险文本替换
  - 应对：本轮将其归类为“暂时不要动”或后续专项，避免破坏脚本、监控、Docker 和联调环境。
- 风险：前端线程顺手把 3D 矿区模块扩成大改版
  - 应对：本轮只允许降级入口、改口径或加历史标记，不做场景引擎重构。
- 风险：主区继续停留在旧主题，导致后续线程接错棒
  - 应对：本轮直接切换 `current-status.md` 与 `handoff.md` 到命名迁移主题。

## 验收标准

- [x] 已明确本轮不属于“设备分类与对象分层建模优化”当前主主题，而是独立的命名迁移主题。
- [x] 已锁定正式中文主名、英文主名和允许简称。
- [x] 已明确四类残留的判断标准与代表位置。
- [x] 已明确 `MineEnergySystem` 检索结果中的路径噪音问题。
- [x] 已明确本轮优先线程路径和禁止扩张项。
- [x] 已明确哪些入口适合交给前端，哪些运行时标识必须延后或暂不处理。
- [x] `PLAN`、`current-status.md`、`handoff.md` 三者对主题、范围和线程路径保持一致。

## 阶段验收结论（2026-03-28）

- 验收范围：
  - README、文档中心、新手入口、`frontend/README.md` 与主区文档中的主入口命名修正
  - 低风险脚本标题、帮助文案、初始化说明、少量后端部署说明与 `app/README.md` 的旧产品名修正
  - 不把运行时 `mine_*` 标识、历史兼容目录、仓库名、Git URL 与绝对路径噪音纳入本轮必改范围
- 验收结果：本轮“主入口命名修正 + 低风险脚本/后端文案修正”已达到阶段完成。
- 已确认：
  - 正式中文主名统一为“园区综合能源管理系统”。
  - 正式英文主名统一为“Campus Energy Management System”。
  - README、文档中心、快速启动指南、安装配置完整指南、`frontend/README.md` 的主入口文案已切换到园区 EMS 口径。
  - `scripts/shell/start.sh`、`stop.sh`、`status.sh`、`pilot_smoke_test.sh`，`bin/fast_start*.sh`，`scripts/python/init_complete_system.py`、`simulator_unified.py`、`generate_prod_secrets.py --help`，以及 `app/README.md`、系统启动完整指南、工业上线清单、试点发布与现场演练手册中的低风险文案已切换到园区 EMS 口径。
  - `frontend/src/layout/`、`frontend/src/router/` 与 `frontend/src/views/Login.vue` 未检出旧“煤矿 / 矿区 / Mine”主入口文案。
  - 本轮工作树改动未触碰 Docker、数据库、环境变量、MQTT、Prometheus、Grafana、脚本契约或 `frontend/src/three/mine/` 目录本体。
  - 已执行 `cd frontend && npm run build`，通过。
  - 已执行 `python3 scripts/python/generate_prod_secrets.py --help`，帮助输出显示新产品名。
- 不满足正式收口的原因：
  - 当前主题虽已完成这一轮阶段目标，但仓库内仍有少量需继续判定的剩余命中，分别落在独立部署文档、历史背景说明、仓库路径噪音与冻结的运行时兼容标识层，尚不足以支持“整个命名迁移主题正式结束”。
  - `MineEnergySystem`、绝对路径、Git URL、`mine_*` 运行时标识仍会在仓库中持续出现，当前 PLAN 仍需保留为执行依据，避免后续线程误做全仓 rename。
- 当前验收结论：
  - 阶段结论：通过。
  - 主题结论：暂不正式收口，继续保留“命名迁移分层治理”为当前执行主题。

## 进度记录

- 2026-03-28：探索线程确认本轮任务不属于当前主区“设备分类与对象分层建模优化”主题，需新开“命名迁移分层治理”正式 PLAN。
- 2026-03-28：探索线程完成关键词残留检索，确认 `MineEnergySystem` 大量命中来自绝对路径与仓库名，不能直接视为待迁移语义残留。
- 2026-03-28：探索线程确认当前建议路径为 `探索 -> 规范 -> 前端 -> 验收`，后端 / 脚本仅在规范锁口径后处理低风险默认文案，运行时标识迁移不纳入本轮。
- 2026-03-28：规范线程锁定正式产品名、允许简称、旧命名禁用边界与四类残留口径；本轮继续采用 `规范 -> 前端 -> 验收` 主路径，后端 / 脚本只保留为可选低风险支路。
- 2026-03-28：前端线程完成 README、文档中心、新手入口与 `frontend/README.md` 的主入口命名修正，并明确未触碰运行时 `mine_*` 标识。
- 2026-03-28：验收线程复核正式 PLAN、`current-status.md`、`handoff.md` 与目标入口文件，确认本轮“用户可见主入口命名修正”阶段通过；`npm run build` 通过，但主题仍不满足正式收口条件。
- 2026-03-28：后端 / 脚本线程完成低风险脚本标题、帮助文案、初始化说明与少量部署文案修正；验收线程复核目标文件、定向 `git diff --name-only` 改动范围、`generate_prod_secrets.py --help` 与前端构建，确认“主入口 + 低风险脚本/后端文案修正”阶段通过，但主题继续保留。

## 相关文档

- [docs/guides/product-positioning.md](/Users/todo/MineEnergySystem/docs/guides/product-positioning.md)
- [docs/guides/five-thread-vibe-coding-framework.md](/Users/todo/MineEnergySystem/docs/guides/five-thread-vibe-coding-framework.md)
- [docs/plans/naming-migration-residue-analysis.md](/Users/todo/MineEnergySystem/docs/plans/naming-migration-residue-analysis.md)
- [docs/plans/current-status.md](/Users/todo/MineEnergySystem/docs/plans/current-status.md)
- [docs/plans/handoff.md](/Users/todo/MineEnergySystem/docs/plans/handoff.md)
