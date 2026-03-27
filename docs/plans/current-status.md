# Current Status

## 当前总目标
- 完成 MineEnergySystem 脚本体系审计
- 明确正式入口、可合并脚本、历史脚本和删除候选
- 在不直接删除脚本的前提下，为后续脚本收敛提供最小方案

---

## 当前阶段
- [x] 分析中
- [ ] 前端处理中
- [ ] 后端处理中
- [x] 已完成审计输出

---

## 本次目标
- 全量扫描 `bin/`、`scripts/shell/`、`scripts/python/`、`frontend/package.json#scripts`
- 判断脚本是否仍被 README / docs / 开发流程使用
- 判断脚本是否仍匹配当前 compose、前端、后端结构
- 输出脚本审计报告并更新交接文档

## 发现的问题
- 当前脚本入口过多，正式入口与示例/调试/历史脚本混在一起。
- `scripts/shell/status.sh`、部分快捷脚本和调试脚本仍按默认 compose 容器名工作，和 `docker-compose.dev.yml` / `docker-compose.prod.yml` 不完全对齐。
- `scripts/shell/start_frontend.sh` 与 `frontend/package.json#dev` 存在明显重复，不符合最新脚本分层规范。
- `scripts/python/rebuild_database.py` 仍保留“全新系统重建数据库”的历史语义，已与当前 Alembic 迁移流程存在冲突风险。
- 多个 `demo_*`、`serial_*`、`test_*` 脚本仍有一定历史价值，但不应继续占据主脚本入口。

## 最近结论
### 探索线程
- 已完成脚本全量盘点，并输出 `docs/plans/script-audit.md`。
- 已按“核心保留 / 可合并 / 应归档 / 删除候选”完成分类。
- 已确认当前仓库没有根级 `Makefile`，正式前端脚本入口应继续收敛在 `frontend/package.json`。

### 规范线程
- `docs/guides/script-guidelines.md` 可继续作为脚本治理规范基础。
- 后续脚本收敛不应直接删除文件，应先改索引和入口层级。

---

## 当前待办

### 探索线程
- [x] 全量扫描脚本文件与入口
- [x] 核对 README / docs / scripts 文档引用
- [x] 输出脚本审计报告
- [x] 更新 `current-status.md` / `handoff.md`

### 前端线程
- [ ] 判断 `scripts/shell/start_frontend.sh` 是否停止维护，并统一回到 `frontend/package.json#dev`
- [ ] 校对 `bin/fast_start.sh` / `bin/fast_start_dev.sh` 中前端端口和启动提示是否与当前 Vite 配置一致
- [ ] 若收敛前端启动入口，同步修正文档中对前端启动方式的描述

### 后端线程
- [ ] 校正 `scripts/shell/status.sh` 对 dev / default / prod 三套 compose 环境的识别逻辑
- [ ] 复核 `release_readiness.sh`、`pilot_*`、`test_health.sh` 与当前接口/配置是否完全一致
- [ ] 评估 `scripts/python/rebuild_database.py` 是否彻底失效并应转删除候选
- [ ] 复核 `replay_mqtt_failures.py`、`send_test_alert.py` 与当前后端服务兼容性

---

## 修改文件
- docs/plans/script-audit.md
- docs/plans/current-status.md
- docs/plans/handoff.md

---

## 验证结果
- 已扫描到 `bin/*.sh` 3 个、`scripts/shell/*.sh` 22 个、`scripts/python/*.py` 22 个。
- 已核对 `frontend/package.json` 中 8 个前端脚本入口。
- 已确认当前仓库无根级 `Makefile`。
- 已核对 README、`docs/`、`scripts/README.md`、`scripts/QUICK_REFERENCE.md`、`scripts/SCRIPT_LIST.md`、`bin/README.md` 中的主要脚本引用。
- 本轮仅做静态审计与文档更新，未执行脚本、未改业务代码。

---

## 剩余风险
- 当前分类以静态引用和实现结构为主，未逐个执行脚本，因此“仍可运行”和“仍应作为正式入口”是两个不同层面的判断。
- 删除候选脚本中可能仍有个别团队成员私下使用，后续处理前需要人工确认。
- 脚本文档中仍有部分旧容器名和旧场景表述，后续收敛时需要同步修正索引和 README。
