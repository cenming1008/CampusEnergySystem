# Script Audit

## 审计范围与方法

- 已阅读：`AGENTS.md`、`docs/plans/current-status.md`、`docs/plans/handoff.md`、`docs/guides/script-guidelines.md`
- 已扫描：
  - 根目录 `bin/*.sh`
  - `scripts/shell/*.sh`
  - `scripts/python/*.py`
  - `frontend/package.json` 中全部 `scripts`
  - 项目内 `README.md`、`docs/`、`scripts/README.md`、`scripts/QUICK_REFERENCE.md`、`scripts/SCRIPT_LIST.md`、`bin/README.md` 对脚本的引用
- 结论原则：
  - 优先判断“当前开发是否真的会用”
  - 优先判断“是否仍匹配当前 compose / 目录 / 应用结构”
  - 优先判断“它是正式入口、辅助工具，还是历史噪音”
- 额外发现：
  - 当前仓库没有根级 `Makefile`
  - 当前脚本正式入口实际分散在 `frontend/package.json`、`bin/`、`scripts/shell/`、`scripts/python/`
  - `scripts/shell/status.sh`、部分快捷脚本和若干调试脚本仍带有默认环境容器名假设，和 `docker-compose.dev.yml` / `docker-compose.prod.yml` 并不完全一致

## 一、核心保留脚本

### 1. 前端正式入口

| 脚本 | 用途 | 判断 |
|------|------|------|
| `frontend/package.json#dev` | 启动前端开发服务器 | 当前前端正式入口；与 `frontend/` 结构一致；符合脚本规范；无一次性特征；建议保留。 |
| `frontend/package.json#build` | 前端构建验证 | 当前构建正式入口；与 Vite 结构一致；被前端开发流程隐式依赖；建议保留。 |
| `frontend/package.json#lint` | ESLint 检查 | 当前代码检查入口；与前端结构一致；无重复问题；建议保留。 |
| `frontend/package.json#typecheck` | TypeScript 类型检查 | 当前前端验证入口；与 `vue-tsc` 配置一致；建议保留。 |
| `frontend/package.json#test:unit` | 单元测试 | 当前前端测试入口；与 Vitest 结构一致；建议保留。 |
| `frontend/package.json#test:unit:watch` | 单元测试 watch | 当前本地开发辅助入口；与前端结构一致；建议保留。 |
| `frontend/package.json#test:e2e` | E2E 测试 | 当前 Playwright 入口；仍有明确用途；建议保留。 |
| `frontend/package.json#preview` | 构建后预览 | 标准 Vite 辅助入口；虽然不是高频，但与当前结构一致；建议保留。 |

### 2. `bin/` 快捷入口

| 脚本 | 用途 | 判断 |
|------|------|------|
| `bin/fast_start.sh` | 日常快速启动默认 compose，并可选择顺带起前端 | 被 `README.md`、`bin/README.md` 作为日常入口引用；符合“高频快捷入口”定位；与当前结构大体一致，但依赖 GUI `open /Applications/Docker.app` 且仍包办前端启动；建议保留为快捷入口。 |
| `bin/fast_start_dev.sh` | 开发模式快捷编排：中间件 Docker + 本地前后端 | 被 `bin/README.md` 直接引用；与 `scripts/shell/start_dev_env.sh` 和 `frontend/package.json` 配合关系清晰；仍有实际价值；建议保留。 |
| `bin/run_simulator.sh` | 在容器内执行统一模拟器 | 被 `bin/README.md` 引用；与 `scripts/python/simulator_unified.py` 关系清晰；仍适合做快捷入口；建议保留。 |

### 3. `scripts/shell/` 正式运维与交付入口

| 脚本 | 用途 | 判断 |
|------|------|------|
| `scripts/shell/start.sh` | 启动默认 Docker 环境 | 被 `README.md`、`scripts/README.md`、新手文档广泛引用；仍是正式入口；与默认 compose 一致；建议保留。 |
| `scripts/shell/start_dev_env.sh` | 启动开发环境中间件 | 被 `README.md`、新手文档、快捷脚本广泛引用；与 `docker-compose.dev.yml` 一致；建议保留。 |
| `scripts/shell/stop.sh` | 停止默认 Docker 环境 | 与 `start.sh` 成对；仍是正式入口；建议保留。 |
| `scripts/shell/stop_dev_env.sh` | 停止开发环境中间件 | 与 `start_dev_env.sh` 成对；仍有明确用途；建议保留。 |
| `scripts/shell/status.sh` | 查看默认环境状态 | 被速查文档高频引用；仍有明确用途；但只覆盖默认 compose，未覆盖 dev/prod 环境；建议保留并后续校正。 |
| `scripts/shell/test_health.sh` | 调用健康检查接口 | 被 README、故障排查和脚本文档引用；与后端 `/health*` 结构一致；建议保留。 |
| `scripts/shell/backup.sh` | 数据库备份 | 被 README、工业上线文档、数据库文档引用；与当前容器命名兼容默认 prod/dev 检测；建议保留。 |
| `scripts/shell/restore.sh` | 数据库恢复 | 被 README、数据库文档、上线清单引用；与当前备份链路一致；建议保留。 |
| `scripts/shell/restore_drill.sh` | 备份恢复演练并生成记录 | 仍与 `backup.sh`/`restore.sh` 结构一致；具备真实运维价值，但当前主入口引用较弱；建议保留。 |
| `scripts/shell/release_readiness.sh` | 发布前总检查 | 被 `README.md`、`deploy_prod.sh`、上线清单引用；与当前测试、生产 compose、告警模板一致；建议保留。 |
| `scripts/shell/deploy_prod.sh` | 生产部署流程 | 被 README 和部署文档引用；仍是正式部署入口；与 `docker-compose.prod.yml` 一致；建议保留。 |
| `scripts/shell/rollback_prod.sh` | 生产回滚 | 与 `backup.sh`/`restore.sh`/`.env.prod` 链路一致；仍有明确运维价值；建议保留。 |
| `scripts/shell/load_baseline.sh` | 生成容量基线 | 与 `stress_test.py`、`evaluate_capacity_baseline.py`、试点流程脚本一致；被 README 和脚本文档引用；建议保留。 |
| `scripts/shell/pilot_smoke_test.sh` | 试点冒烟验收 | 当前试点验收正式入口之一；与现有健康检查和认证接口一致；建议保留。 |
| `scripts/shell/pilot_readiness.sh` | 试点前 readiness 与证据归档 | 与当前检查链路一致；仍被脚本文档和验收材料使用；建议保留。 |
| `scripts/shell/pilot_drill.sh` | 串联 readiness / baseline / smoke | 与当前试点链路一致；仍有明确用途；建议保留。 |
| `scripts/shell/render_alertmanager_config.sh` | 生成 Alertmanager 配置 | 与生产告警配置链路一致；被 `release_readiness.sh` 间接依赖；建议保留。 |
| `scripts/shell/setup_mqtt_auth.sh` | 生成 Mosquitto 密码文件 | 被 `start_dev_env.sh` 直接依赖；与当前 dev compose 一致；建议保留。 |

### 4. `scripts/python/` 正式工具入口

| 脚本 | 用途 | 判断 |
|------|------|------|
| `scripts/python/create_admin.py` | 创建管理员账号 | 被 README、部署文档广泛引用；与当前用户模型和密码强度约束一致；建议保留。 |
| `scripts/python/init_complete_system.py` | 初始化开发/演示数据 | 被新手与启动文档广泛引用；仍匹配当前开发体验；建议保留。 |
| `scripts/python/check_config.py` | 检查运行配置 | 被 `release_readiness.sh`、`pilot_readiness.sh` 和文档引用；仍与当前 settings 结构一致；建议保留。 |
| `scripts/python/check_production_readiness.py` | 检查生产配置护栏 | 被 README、部署脚本、上线清单引用；仍匹配当前生产配置结构；建议保留。 |
| `scripts/python/simulator_unified.py` | 统一设备模拟器 | 被 README、新手文档、`bin/run_simulator.sh` 高强度引用；仍是当前开发与演示核心工具；建议保留。 |
| `scripts/python/device_gateway.py` | 真实设备接入网关参考实现 | 被架构、功能、配置文档广泛引用；仍与当前 MQTT 接入模式一致；建议保留。 |
| `scripts/python/stress_test.py` | HTTP 压测工具 | 与 `load_baseline.sh`、部署流程一致；当前仍有正式用途；建议保留。 |
| `scripts/python/evaluate_capacity_baseline.py` | 容量基线判定 | 被 `load_baseline.sh` 调用；与当前试点验收流程一致；建议保留。 |
| `scripts/python/send_test_alert.py` | 发送测试告警 | 与当前通知服务、试点验收材料一致；仍有明确用途；建议保留。 |
| `scripts/python/replay_mqtt_failures.py` | 重放 MQTT 失败/死信记录 | 与当前 `mqtt_reliability` 代码结构一致；README 已引用；建议保留。 |
| `scripts/python/generate_prod_secrets.py` | 生成生产密钥片段 | 与 `.env.prod` 流程一致；虽然引用不多，但仍有明确运维价值；建议保留。 |
| `scripts/python/mqtt_send_test.py` | 发送 MQTT 测试消息 | 被试点验收、设备接入调试场景引用；与当前 MQTT 主题和认证结构一致；建议保留。 |

## 二、建议合并的脚本

| 脚本 | 用途 | 判断 |
|------|------|------|
| `scripts/shell/start_frontend.sh` | 启动前端并自动安装依赖、处理端口 | 仍能工作，但与 `frontend/package.json#dev` 重复；脚本规范也要求前端原生命令留在 `frontend/package.json`；建议将“如何启动前端”收敛回前端 README 与 `npm run dev`，此脚本后续并入文档或快捷入口。 |
| `scripts/shell/restart_backend.sh` | 重启后端容器 | 只有一层 `docker compose restart backend` 包装；当前脚本价值低于文档命令；与当前结构一致但重复度高；建议并入运维文档或 `status.sh` 提示。 |
| `scripts/shell/rebuild_backend.sh` | 重建后端容器 | 只有一层 `docker compose build/up` 包装；和文档命令重复；建议并入运维文档。 |
| `scripts/shell/install_dependencies.sh` | 创建 venv 并安装依赖 | 内容有价值，但更像 onboarding 流程而不是长期独立入口；与 README / 新手文档主题重复；建议合并进开发环境安装文档。 |
| `scripts/shell/check_websocket.sh` | WebSocket 诊断 | 有一定排查价值，但与 `test_health.sh`、故障排查文档主题重叠；且默认端口和默认 compose 假设较强；建议并入故障排查指南。 |
| `scripts/shell/check_mac_env.sh` | macOS 环境检查 | 只适用于单平台，本身是 onboarding 辅助；仍有价值，但不宜作为长期通用入口；建议并入新手文档的 macOS 节。 |
| `scripts/python/generate_training_data.py` | 生成训练数据 | 功能仍有价值，但应并入 `lstm_forecast` 或预测功能工作流文档，不宜在脚本入口层单独突出；建议合并说明文档。 |
| `scripts/python/mqtt_subscriber_template.py` | MQTT 订阅模板骨架 | 更像示例片段，不像正式工具；与接入文档主题重叠；建议改为文档示例或 `docs/examples/`。 |

## 三、建议归档的脚本

| 脚本 | 用途 | 判断 |
|------|------|------|
| `scripts/python/demo_unified_system.py` | 历史统一系统演示 | 与当前代码仍大体可对齐，但明显属于演示性质；不是当前开发或运维正式入口；与 `init_complete_system.py`、功能文档存在主题重叠；建议归档。 |
| `scripts/python/demo_device_group.py` | 设备分组演示 | 仍对应现有能力，但主要服务于历史功能展示；不适合作为当前入口；建议归档。 |
| `scripts/python/demo_location.py` | 位置管理演示 | 与当前能力相关，但属于历史演示脚本；建议归档。 |
| `scripts/python/demo_maintenance.py` | 维护管理演示 | 与当前能力相关，但属于历史演示脚本；建议归档。 |
| `scripts/python/test_http_device.py` | HTTP 设备单次调试 | 仍与 `device_gateway.py` 调试场景一致，但属于接入期一次性调试工具，不应继续在主脚本入口占高权重；建议归档到接入调试工具区。 |
| `scripts/python/test_modbus_tcp.py` | Modbus TCP 调试 | 同上，保留历史与接入价值，但不应作为主入口；建议归档。 |
| `scripts/python/test_serial_port.py` | 串口调试 | 同上，建议归档。 |
| `scripts/python/serial_device_sim.py` | 串口设备模拟 | 明显是联调演示脚本；与当前主开发流程关系弱；建议归档。 |
| `scripts/python/serial_gateway_demo.py` | 串口网关演示 | 明显是历史调试/演示脚本；建议归档。 |
| `scripts/python/serial_pair_demo.py` | 虚拟串口对演示 | 更偏学习/演示工具；对当前主开发帮助有限；建议归档。 |
| `scripts/shell/cleanup_logs.sh` | 清理本地日志 | 有一定维护价值，但当前主日志链路更多依赖 Docker / 观测栈；引用弱；适合作为历史辅助脚本归档。 |
| `scripts/shell/uninstall_local_services.sh` | 停止本机 brew 服务 | 强平台相关且针对早期“本地服务切 Docker”场景；当前已非主流程；建议归档。 |

## 四、删除候选脚本

| 脚本 | 用途 | 判断 |
|------|------|------|
| `scripts/python/rebuild_database.py` | 直接删表重建数据库 | 明显带有“全新系统/历史重构期”痕迹；绕过 Alembic 与当前迁移流程；风险高、与当前生产护栏不一致；仍被少量旧文档引用，但不应继续保留为可见入口；建议删除候选，处理前先人工确认无人依赖。 |
| `scripts/shell/fix_venv.sh` | 删除并重建虚拟环境 | 强机器本地化、破坏性较强；未见 README/当前流程正式引用；与 `install_dependencies.sh` 和手工 `python -m venv` 重复；建议删除候选。 |
| `scripts/shell/cleanup_docker.sh` | 交互式删除容器/卷/镜像 | 破坏性强、与当前更规范的 `docker compose down` 和运维文档重复；还引用历史“Docker清理与本地运行指南”语境；建议删除候选，若保留也应至少先移出主清单。 |

## 五、建议收敛后的正式入口

- 前端入口：
  - `frontend/package.json#dev`
  - `frontend/package.json#build`
  - `frontend/package.json#lint`
  - `frontend/package.json#typecheck`
  - `frontend/package.json#test:unit`
  - `frontend/package.json#test:e2e`
- 快捷入口：
  - `bin/fast_start.sh`
  - `bin/fast_start_dev.sh`
  - `bin/run_simulator.sh`
- Shell 正式入口：
  - `scripts/shell/start.sh`
  - `scripts/shell/start_dev_env.sh`
  - `scripts/shell/stop.sh`
  - `scripts/shell/stop_dev_env.sh`
  - `scripts/shell/status.sh`
  - `scripts/shell/test_health.sh`
  - `scripts/shell/backup.sh`
  - `scripts/shell/restore.sh`
  - `scripts/shell/release_readiness.sh`
  - `scripts/shell/deploy_prod.sh`
  - `scripts/shell/rollback_prod.sh`
  - `scripts/shell/load_baseline.sh`
  - `scripts/shell/pilot_smoke_test.sh`
  - `scripts/shell/pilot_readiness.sh`
  - `scripts/shell/pilot_drill.sh`
- Python 正式入口：
  - `scripts/python/create_admin.py`
  - `scripts/python/init_complete_system.py`
  - `scripts/python/check_config.py`
  - `scripts/python/check_production_readiness.py`
  - `scripts/python/simulator_unified.py`
  - `scripts/python/device_gateway.py`
  - `scripts/python/stress_test.py`
  - `scripts/python/evaluate_capacity_baseline.py`
  - `scripts/python/send_test_alert.py`
  - `scripts/python/replay_mqtt_failures.py`
  - `scripts/python/generate_prod_secrets.py`
  - `scripts/python/mqtt_send_test.py`

## 六、目录收敛建议

- 应继续留在 `frontend/package.json` 的：
  - 前端开发、构建、lint、typecheck、单测、E2E
- 应继续留在 `bin/` 的：
  - 高频快捷入口，仅保留 `fast_start.sh`、`fast_start_dev.sh`、`run_simulator.sh`
- 应继续留在 `scripts/shell/` 的：
  - 启停、状态、备份恢复、发布、试点验收、环境生成类正式脚本
- 应继续留在 `scripts/python/` 的：
  - 管理员创建、数据初始化、模拟器、网关、配置检查、压测、基线判定、通知和重放类正式工具
- 建议迁出主入口、转文档或示例的：
  - `start_frontend.sh`
  - `restart_backend.sh`
  - `rebuild_backend.sh`
  - `check_websocket.sh`
  - `check_mac_env.sh`
  - `mqtt_subscriber_template.py`
  - `generate_training_data.py`
- 建议进入归档区的：
  - 全部 `demo_*.py`
  - 串口演示与单次接入调试脚本
  - `cleanup_logs.sh`
  - `uninstall_local_services.sh`

## 七、需要前端线程处理的事项

- 校正 `scripts/shell/start_frontend.sh` 的角色定位：
  - 决定是否停止维护该脚本，统一回到 `cd frontend && npm run dev`
- 核对 `README.md`、新手文档、前端文档中对前端启动方式的表述：
  - 避免同时把 `start_frontend.sh` 和 `frontend/package.json#dev` 都当正式入口
- 校对 `bin/fast_start.sh`、`bin/fast_start_dev.sh` 与当前 Vite 端口说明是否完全一致

## 八、需要后端线程处理的事项

- 校正 `scripts/shell/status.sh`：
  - 当前只覆盖默认 compose 容器名，未统一覆盖 dev/prod 环境
- 复核 `scripts/shell/test_health.sh`、`pilot_*`、`release_readiness.sh`：
  - 确认接口路径、返回结构、生产检查项仍与当前后端一致
- 评估 `scripts/python/rebuild_database.py`：
  - 当前已引入 Alembic，需确认该脚本是否彻底失效并可以转删除候选
- 评估 `scripts/python/replay_mqtt_failures.py`、`send_test_alert.py`：
  - 确认与当前可靠性与通知服务仍保持兼容

## 九、最小整理方案

1. 先修索引，不删脚本：
   - 在 `scripts/README.md`、`scripts/SCRIPT_LIST.md`、`scripts/QUICK_REFERENCE.md` 中明确“正式入口 / 示例 / 历史工具”三级定位
2. 再收敛重复入口：
   - 把 `start_frontend.sh`、`restart_backend.sh`、`rebuild_backend.sh` 从“主入口”降级为文档命令或并入其他脚本说明
3. 最后再处理归档与删除候选：
   - 先归档 `demo_*`、串口演示、单次接入调试脚本
   - 再人工确认 `rebuild_database.py`、`fix_venv.sh`、`cleanup_docker.sh` 是否还有隐性使用者

