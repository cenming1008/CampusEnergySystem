# Current Status

## 当前总目标
- 完成 MineEnergySystem 脚本体系审计
- 明确正式入口、可合并脚本、历史脚本和删除候选
- 在不直接删除脚本的前提下，为后续脚本收敛提供最小方案

---

## 当前阶段
- [x] 分析中
- [x] 前端处理中
- [x] 后端处理中
- [x] 已完成审计输出

---

## 本次目标
- 整理后端相关 shell / python / 运维脚本
- 优先区分正式脚本、临时脚本和历史脚本
- 收敛与当前后端运行方式不一致的脚本入口
- 更新 `current-status.md` / `handoff.md`

## 发现的问题
- `scripts/shell/status.sh` 原先只覆盖默认 compose 的容器名，不能识别 `docker-compose.dev.yml` 与 `docker-compose.prod.yml`。
- `scripts/python/rebuild_database.py` 仍采用 `SQLModel.metadata.drop_all/create_all` 的历史重建方式，和当前 Alembic 迁移链路冲突，不应继续作为正式入口。
- `scripts/README.md`、`scripts/SCRIPT_LIST.md`、`scripts/python/README.md`、`scripts/QUICK_REFERENCE.md` 与新手文档仍把 `rebuild_database.py` 暴露为可直接使用的日常命令，容易误导。

## 最近结论
### 探索线程
- 已完成脚本全量盘点，并输出 `docs/plans/script-audit.md`。
- 已按“核心保留 / 可合并 / 应归档 / 删除候选”完成分类。
- 已确认当前仓库没有根级 `Makefile`，本轮无需新增或整理后端 Make 入口。

### 规范线程
- `docs/guides/script-guidelines.md` 可继续作为脚本治理规范基础。
- 后续脚本收敛不应直接删除文件，应先改索引和入口层级。

### 后端线程
- 已将历史脚本 `scripts/python/rebuild_database.py` 迁入 `scripts/archive/python/rebuild_database.py`，从正式入口降级。
- 已更新 `scripts/README.md`、`scripts/SCRIPT_LIST.md`、`scripts/python/README.md`、`scripts/QUICK_REFERENCE.md`，不再把数据库重建当作正式后端流程。
- 已将 `docs/01-新手入门/本地开发环境配置.md` 的数据库操作示例改为 Alembic 迁移 + 初始化脚本。
- 已重写 `scripts/shell/status.sh`，支持 `auto|default|dev|prod` 环境识别，并分别展示对应容器与健康检查。

---

## 当前待办

### 探索线程
- [x] 全量扫描脚本文件与入口
- [x] 核对 README / docs / scripts 文档引用
- [x] 输出脚本审计报告
- [x] 更新 `current-status.md` / `handoff.md`

### 前端线程
- [x] 判断 `scripts/shell/start_frontend.sh` 是否停止维护，并统一回到 `frontend/package.json#dev`
- [x] 校对 `bin/fast_start.sh` / `bin/fast_start_dev.sh` 中前端端口和启动提示是否与当前 Vite 配置一致
- [x] 若收敛前端启动入口，同步修正文档中对前端启动方式的描述

### 后端线程
- [x] 校正 `scripts/shell/status.sh` 对 dev / default / prod 三套 compose 环境的识别逻辑
- [x] 复核 `release_readiness.sh`、`pilot_*`、`test_health.sh` 与当前接口/配置是否完全一致
- [x] 评估 `scripts/python/rebuild_database.py` 是否彻底失效并应转删除候选
- [x] 复核 `replay_mqtt_failures.py`、`send_test_alert.py` 与当前后端服务兼容性

---

## 修改文件
- scripts/archive/python/rebuild_database.py
- scripts/shell/status.sh
- scripts/README.md
- scripts/SCRIPT_LIST.md
- scripts/python/README.md
- scripts/QUICK_REFERENCE.md
- docs/01-新手入门/本地开发环境配置.md
- docs/plans/current-status.md
- docs/plans/handoff.md

---

## 验证结果
- 已核对 `app/api/endpoints/health.py`、`app/api/endpoints/auth.py`、`app/api/endpoints/audit.py`，确认 `test_health.sh`、`pilot_smoke_test.sh`、`release_readiness.sh` 所依赖的 `/health*`、`/auth/login`、`/audit/events` 接口仍存在。
- 已核对 `app/core/notifications.py` 与 `app/services/mqtt_reliability_service.py`，确认 `send_test_alert.py`、`replay_mqtt_failures.py` 仍匹配当前后端能力。
- 已核对 `migrations/`、`docker-compose*.yml` 与后端配置，确认 Alembic 已是当前数据库结构维护主链路。
- 已执行 `bash -n scripts/shell/status.sh`，Shell 语法通过。
- 已执行 `python3 -m compileall -q scripts/python scripts/archive/python`，Python 脚本编译通过。

---

## 剩余风险
- `README.md`、`scripts/CHANGELOG.md` 与部分归档文档仍保留 `rebuild_database.py` 历史表述，本轮未继续扩散到全部历史材料。
- `status.sh` 已补环境识别，但尚未在真实运行中的 default/dev/prod 三套环境里逐一做在线验证。
- `scripts/archive/python/rebuild_database.py` 仍保留在仓库供历史排查；若后续确认完全无人依赖，可再转删除候选。
