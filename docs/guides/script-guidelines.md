# 脚本治理规范

> 约束 MineEnergySystem 中脚本的分类、落点、命名、入口与归档方式，避免正式入口、调试脚本和历史遗留混在一起。

---

## 1. 目标

本规范用于解决当前仓库中的几个实际问题：

1. `bin/`、`scripts/`、`frontend/package.json` 同时承载命令入口，边界容易混淆
2. `scripts/python/` 与 `scripts/shell/` 中混有正式脚本、调试脚本、演示脚本和一次性验证脚本
3. 文档中大量直接引用脚本，如果随意移动路径，容易打断现有使用方式

治理目标是：

- 正式入口少而稳定
- 真实实现集中到 `scripts/`
- 调试与演示脚本有清晰标识
- 一次性历史脚本有统一归档去向

---

## 2. 当前仓库的脚本入口分层

基于当前仓库结构，脚本入口分为 4 层：

### 2.1 `frontend/package.json`

这是前端原生 CLI 入口，适合保留前端开发链路命令：

- `npm run dev`
- `npm run build`
- `npm run lint`
- `npm run typecheck`
- `npm run test:unit`
- `npm run test:e2e`

规则：

- 前端构建、校验、测试命令优先保留在 `frontend/package.json`
- 不要把仓库级运维、数据库、部署、模拟器命令塞进前端 `package.json`

### 2.2 `bin/`

这是仓库级“快捷入口层”，当前只适合保留少量高频、给人直接敲的命令，例如：

- `bin/fast_start.sh`
- `bin/fast_start_dev.sh`
- `bin/run_simulator.sh`

规则：

- `bin/` 只放高频快捷壳，不承载复杂业务逻辑
- `bin/` 脚本应尽量包装 `scripts/` 中的正式实现
- 若一个命令不是高频入口，不应新增到 `bin/`

### 2.3 `scripts/shell/`

这是仓库级 Shell 正式实现层，当前承载：

- 服务启停
- 健康检查
- 备份恢复
- 部署发布
- 清理与环境修复

适合保留为正式脚本的示例：

- `start.sh`
- `start_dev_env.sh`
- `stop.sh`
- `status.sh`
- `test_health.sh`
- `backup.sh`
- `restore.sh`
- `deploy_prod.sh`
- `release_readiness.sh`

### 2.4 `scripts/python/`

这是仓库级 Python 工具实现层，当前承载：

- 初始化脚本
- 模拟器
- 网关
- 配置检查
- 压测与验收辅助
- 协议联调工具

适合保留为正式脚本的示例：

- `create_admin.py`
- `init_complete_system.py`
- `check_config.py`
- `check_production_readiness.py`
- `simulator_unified.py`
- `device_gateway.py`
- `evaluate_capacity_baseline.py`

---

## 3. 脚本分类规则

后续新增或整理脚本时，统一分为以下 3 类。

### 3.1 正式脚本

定义：

- 被 README、docs、CI、部署流程或日常协作稳定依赖
- 预期会被重复使用
- 有明确输入输出和适用场景

当前仓库中的典型正式脚本：

- `scripts/shell/start.sh`
- `scripts/shell/start_dev_env.sh`
- `scripts/shell/status.sh`
- `scripts/shell/test_health.sh`
- `scripts/shell/backup.sh`
- `scripts/shell/restore.sh`
- `scripts/shell/deploy_prod.sh`
- `scripts/python/create_admin.py`
- `scripts/python/check_config.py`
- `scripts/python/check_production_readiness.py`
- `scripts/python/init_complete_system.py`
- `scripts/python/simulator_unified.py`
- `scripts/python/device_gateway.py`

### 3.2 调试 / 演示脚本

定义：

- 主要用于联调、协议测试、演示或局部验证
- 不应被当作主入口
- 允许保留，但必须让用途一眼可见

当前仓库中的典型调试 / 演示脚本：

- `demo_*.py`
- `test_http_device.py`
- `test_modbus_tcp.py`
- `test_serial_port.py`
- `mqtt_send_test.py`
- `mqtt_subscriber_template.py`
- `serial_*`
- `stress_test.py`

规则：

- 这类脚本应保留在 `scripts/`，但不应新增到 `bin/`
- 除非团队长期依赖，否则不应放入主 README 的第一层入口

### 3.3 一次性历史脚本

定义：

- 只服务某次迁移、修复、验收或阶段性排查
- 完成后不应继续进入主入口
- 再次使用概率低

判定信号：

- 脚本名带明显阶段性或临时性语义
- 文档只在一次性报告中被引用
- 已被正式脚本替代

规则：

- 不删除正在使用的历史脚本
- 一旦确认不再作为当前入口，应迁入归档区

---

## 4. 目录落点规范

### 4.1 应保留在 `package.json` 的脚本

仅保留与该子项目原生开发工具链强相关的命令。

当前适用范围：

- `frontend/package.json`

适合放入的命令：

- 开发服务器
- 构建
- lint
- typecheck
- unit/e2e 测试

不适合放入的命令：

- 数据库初始化
- 生产部署
- 备份恢复
- MQTT / 串口 / Modbus 联调
- 仓库级启动编排

### 4.2 应保留在 `bin/` 的脚本

满足以下条件时，才考虑进入 `bin/`：

1. 高频
2. 面向人手工执行
3. 命令值得缩短
4. 背后已有稳定正式实现

`bin/` 不应成为第二套脚本实现目录。

### 4.3 应迁移到 `scripts/` 统一管理的脚本

以下脚本若未来新增，默认都应放入 `scripts/`：

- 仓库级 shell 运维命令
- Python 初始化与管理工具
- 协议联调与设备接入工具
- 发布、验收、回滚、备份、恢复工具
- 模拟器、网关、压测和验证工具

简单说：

- 不是前端原生命令，就优先考虑 `scripts/`
- 不是高频快捷壳，就不要放 `bin/`

---

## 5. 命名规范

### 5.1 Shell 脚本

使用小写蛇形或动宾短语，统一放在 `scripts/shell/`：

- `start.sh`
- `start_dev_env.sh`
- `backup.sh`
- `release_readiness.sh`

建议：

- 启停类：`start_*`、`stop_*`、`restart_*`
- 检查类：`check_*`、`test_*`、`*_readiness`
- 发布维护类：`deploy_*`、`rollback_*`、`cleanup_*`

### 5.2 Python 脚本

统一使用小写下划线，放在 `scripts/python/`：

- `create_admin.py`
- `init_complete_system.py`
- `device_gateway.py`

建议：

- 演示：`demo_*`
- 协议联调：`test_*`
- 主动发送验证：`*_send_test.py`
- 模拟：`*_sim.py`、`simulator_*`
- 生产检查：`check_*`、`evaluate_*`

### 5.3 避免的命名

- `temp_*`
- `final_*`
- `new_*`
- `v2_*`
- `fix_*_20260327.py`

这类命名通常意味着脚本已经带有一次性历史语义，应改成职责名，或直接进入归档区。

---

## 6. 正式入口规则

以下位置才应被视为“正式入口”：

1. `frontend/package.json` 中稳定维护的前端命令
2. `bin/` 中极少数高频快捷命令
3. `scripts/README.md`、`scripts/shell/README.md`、`scripts/python/README.md` 中列出的正式脚本
4. 被 README、docs 主入口、CI 或发布流程稳定引用的脚本

不应作为正式入口的内容：

- 某个历史文档里的临时命令
- 某次问题排查中临时拼出来的脚本
- 只用于个人本地调试的命令

如果一个脚本要成为正式入口，至少要满足：

1. 有清晰用途
2. 有稳定路径
3. 有 README 或 guide 中的说明
4. 不依赖一次性上下文

---

## 7. 归档规则

当前仓库还没有独立的 `scripts/archive/`，但后续若执行脚本收敛，建议按以下方式处理：

- `scripts/archive/python/`
- `scripts/archive/shell/`

归档触发条件：

1. 已被正式脚本替代
2. 仅服务历史迁移或阶段性验收
3. 文档已不再把它作为当前入口
4. 仍有少量历史参考价值，不适合直接删除

删除候选脚本的处理顺序：

1. 先从 README、guide、流程文档中下架
2. 再迁入 `scripts/archive/`
3. 观察一个维护周期后，再决定是否永久删除

在真正建立 `scripts/archive/` 前，不要随意删除仍在文档中出现的脚本。

---

## 8. 当前仓库的建议保留策略

### 8.1 保留为正式入口

- `frontend/package.json` 中现有开发、构建、校验、测试命令
- `bin/fast_start.sh`
- `bin/fast_start_dev.sh`
- `bin/run_simulator.sh`
- `scripts/shell/start.sh`
- `scripts/shell/start_dev_env.sh`
- `scripts/shell/status.sh`
- `scripts/shell/test_health.sh`
- `scripts/shell/backup.sh`
- `scripts/shell/restore.sh`
- `scripts/shell/deploy_prod.sh`
- `scripts/shell/release_readiness.sh`
- `scripts/python/create_admin.py`
- `scripts/python/check_config.py`
- `scripts/python/check_production_readiness.py`
- `scripts/python/init_complete_system.py`
- `scripts/python/simulator_unified.py`
- `scripts/python/device_gateway.py`

### 8.2 保留但降级为调试/演示

- `scripts/python/demo_*.py`
- `scripts/python/test_*.py`
- `scripts/python/mqtt_send_test.py`
- `scripts/python/mqtt_subscriber_template.py`
- `scripts/python/serial_*`
- `scripts/python/stress_test.py`
- `scripts/shell/check_websocket.sh`
- `scripts/shell/check_mac_env.sh`
- `scripts/shell/start_frontend.sh`

### 8.3 后续优先人工确认

- 是否需要把 `scripts/QUICK_REFERENCE.md` 与 `scripts/SCRIPT_LIST.md` 继续同时维护
- 是否需要为历史性脚本单独建立 `scripts/archive/`
- 是否存在文档仍引用但脚本文件已不存在的情况，应先校正文档再决定脚本治理动作

---

## 9. 维护要求

新增或整理脚本时，至少同步检查：

1. 是否放对目录
2. 是否属于正式入口还是调试脚本
3. 是否需要更新 `scripts/README.md`
4. 是否需要更新 `bin/README.md`
5. 是否需要更新相关文档中的命令示例

不允许的做法：

- 在多个目录放同一脚本的不同实现
- 只改脚本不改文档入口
- 把一次性命令直接写进主 README 当作长期入口
- 把仓库级运维命令塞进 `frontend/package.json`

---

## 10. 相关文档

- [AGENTS.md](../../AGENTS.md)
- [scripts/README.md](../../scripts/README.md)
- [scripts/shell/README.md](../../scripts/shell/README.md)
- [scripts/python/README.md](../../scripts/python/README.md)
- [bin/README.md](../../bin/README.md)
