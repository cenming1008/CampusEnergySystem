# Script Audit

## 一、总体判断

当前脚本体系不属于“完全失控”，也不是“已经规范可以完全放着不管”。更准确的判断是：结构已经成型，但文档和入口仍混乱。

优点比较明确。仓库已经自然形成了四层入口：
- `frontend/package.json` 负责前端原生命令
- `bin/` 负责少量快捷入口
- `scripts/shell/` 负责仓库级 shell 工具
- `scripts/python/` 负责 Python 管理、模拟、接入和调试工具

而且仓库里已经开始出现“降级归档”的意识，例如 `scripts/archive/python/rebuild_database.py` 和 `scripts/archive/shell/start_frontend.sh`，这说明项目不是没有治理，而是已经开始治理。

主要问题也很集中：
- 入口边界已经有规则，但文档没有完全跟上
- `bin/` 与 `scripts/` 的关系说明大体正确，但仍存在双入口并存、推荐层级不够统一的问题
- `scripts/python/` 里仍混杂正式工具、演示脚本、一次性接入调试脚本
- 脚本清单和目录 README 的统计数字、覆盖范围、定位描述不一致
- 前端脚本本身不乱，但缺少统一聚合校验入口，文档里也还有旧端口表述

综合判断：
- 当前状态属于：结构已成型，但文档和入口仍混乱
- 换成更直白的话，就是：已经“有体系”，但还没有“完全收口”

## 二、当前脚本结构梳理

### 1. 快捷入口层

`bin/` 当前承担的是“给人直接敲的短命令”职责，定位基本合理。

现有 3 个脚本：
- `fast_start.sh`
- `fast_start_dev.sh`
- `run_simulator.sh`

从数量上看，`bin/` 仍然是精简的，没有膨胀成第二套正式实现层。这一点是好的。

但问题在于，`bin/README.md` 虽然把自己定义为“快捷入口层”，文档中仍把它和 `scripts/` 讲成两套都可直接推荐的入口，导致使用者不容易判断：
- `./bin/fast_start.sh` 是“日常快捷入口”
- 还是 `./scripts/shell/start.sh` 才是更正式的事实来源

结论：
- `bin/` 作为快捷层是合理的
- 但文档上还没有把“快捷入口”和“正式实现入口”的优先级讲透

### 2. 完整工具层

#### `scripts/shell/`

这一层定位本来应该最清楚：仓库级 shell 正式工具层。

实际目录里共有 27 个 shell 脚本，包括：
- 启停类：`start.sh`、`start_dev_env.sh`、`stop.sh`、`stop_dev_env.sh`
- 检查类：`status.sh`、`test_health.sh`、`pilot_*`、`load_baseline.sh`
- 维护部署类：`backup.sh`、`restore.sh`、`rollback_prod.sh`、`deploy_prod.sh`、`release_readiness.sh`
- 辅助类：`check_websocket.sh`、`check_mac_env.sh`、`install_dependencies.sh`
- 清理/本地修复类：`cleanup_*`、`fix_venv.sh`、`uninstall_local_services.sh`
- 但还包含 `restore_drill.sh`、`render_alertmanager_config.sh`、`setup_mqtt_auth.sh` 这类清单文档并未完整覆盖的脚本

定位不算混乱，但“正式入口”和“辅助脚本”还没有被文档严格区分。

#### `scripts/python/`

这一层问题更明显。实际目录里共有 24 个 Python 脚本，混杂了 4 类内容：
- 正式工具：`create_admin.py`、`init_complete_system.py`、`check_config.py`、`check_production_readiness.py`
- 运行工具：`simulator_unified.py`、`device_gateway.py`
- 运维/验证工具：`stress_test.py`、`evaluate_capacity_baseline.py`、`send_test_alert.py`、`replay_mqtt_failures.py`
- 历史演示 / 接入调试 / 学习型脚本：`demo_*`、`test_*`、`serial_*`、`mqtt_subscriber_template.py`

这说明 `scripts/python/` 还不是一个纯粹的“正式工具层”，而是“正式工具 + 接入调试 + 历史演示”的混合层。

#### `archive/`

`scripts/archive/` 已经开始承担“降级区”职责，这是积极信号。

当前已有：
- `scripts/archive/python/rebuild_database.py`
- `scripts/archive/shell/start_frontend.sh`

但目前 archive 还只是个开始，不是完整策略。很多明显更适合归档的脚本仍然暴露在正式目录中，例如：
- `demo_*.py`
- `serial_*.py`
- `test_http_device.py`
- `test_modbus_tcp.py`
- `test_serial_port.py`

结论：
- `scripts/shell/` 和 `scripts/python/` 的大方向是清楚的
- 但“正式 / 辅助 / 历史”边界还没有真正落实到目录和文档层

### 3. 前端脚本入口

`frontend/package.json` 当前本身是清晰的。

已有脚本：
- `dev`
- `build`
- `lint`
- `typecheck`
- `preview`
- `test:unit`
- `test:unit:watch`
- `test:e2e`

这组脚本没有明显的命名混乱，也没有塞入仓库级运维命令，说明前端入口层比仓库级脚本层更干净。

但仍有两个问题：
- 缺少一个统一聚合检查入口，例如 `check`
- 文档层对前端入口的表述还没完全收敛，仓库里仍能看到 `5173` 的旧端口叙事，而当前前端实际运行习惯已经更多指向 `3000`

结论：
- `frontend/package.json` 本身清晰
- 缺的是一个统一校验入口，以及文档层的统一口径

## 三、发现的问题

- `bin/README.md` 对 `bin/` 的定位是“快捷入口层”，这个定位本身正确，但它仍把 `scripts/` 描述成“完整工具集（31 个脚本）”。当前实际数量已经明显不止这个数字，说明定位文本和事实没有同步。文件：[bin/README.md](/Users/todo/MineEnergySystem/bin/README.md)

- `scripts/README.md` 写的是“Shell 正式脚本 21 个、Python 脚本 21 个、已归档 2 个”，但实际目录下分别有 27 个 shell 脚本、24 个 python 脚本、2 个 archive 脚本。说明统计口径已经不一致，而且没有解释哪些脚本被排除在“正式脚本”计数之外。文件：[scripts/README.md](/Users/todo/MineEnergySystem/scripts/README.md)

- `scripts/SCRIPT_LIST.md` 并没有覆盖全部实际脚本。例如实际存在的 `restore_drill.sh`、`render_alertmanager_config.sh`、`setup_mqtt_auth.sh` 没被列入清单；实际存在的 `check_production_readiness.py` 也没有进 Python 清单。这意味着“完整脚本清单”并不完整。文件：[scripts/SCRIPT_LIST.md](/Users/todo/MineEnergySystem/scripts/SCRIPT_LIST.md)

- `scripts/shell/README.md` 和 `scripts/SCRIPT_LIST.md` 都把 `restart_backend.sh`、`rebuild_backend.sh` 继续作为一层独立脚本入口暴露，但这两个脚本本质上只是 `docker compose` 命令包装，是否值得继续作为正式入口并没有在文档中说明清楚。文件：[scripts/shell/README.md](/Users/todo/MineEnergySystem/scripts/shell/README.md)

- `scripts/python/README.md` 仍把 `demo_*`、`serial_*`、`test_*` 和正式工具并列展示，虽然分类有分组，但从入口感知上仍然是“一整层都可直接使用”的感觉，没有明显的降级提示。文件：[scripts/python/README.md](/Users/todo/MineEnergySystem/scripts/python/README.md)

- `archive/` 已经出现，但归档策略没有彻底落地。`start_frontend.sh` 和 `rebuild_database.py` 已归档，说明项目已经知道要做降级；但很多同样应降级的历史演示和单次调试脚本还留在正式目录里，边界不一致。目录：[scripts/archive](/Users/todo/MineEnergySystem/scripts/archive)

- `README.md` 以及多份新手文档仍在使用 `5173` 的旧前端端口叙事，例如 [README.md](/Users/todo/MineEnergySystem/README.md) 里仍有 `http://localhost:5173` 和 `CORS_ORIGINS=["http://localhost:5173", ...]` 相关表述。这会让脚本入口、文档入口、实际前端运行口径不一致。

- `frontend/package.json` 已经有 `lint`、`typecheck`、`test:unit`、`test:e2e`，但没有一个统一的 `check` 或类似聚合命令，导致“前端检查入口”仍然分散在多条命令上。文件：[frontend/package.json](/Users/todo/MineEnergySystem/frontend/package.json)

- `bin/` 与 `scripts/shell/` 的关系虽然基本正确，但 `README.md`、`bin/README.md`、`scripts/README.md` 三者对“日常推荐入口”“完整入口”“事实来源”的层级感还不够统一，容易形成双入口并存。文件：[README.md](/Users/todo/MineEnergySystem/README.md)、[bin/README.md](/Users/todo/MineEnergySystem/bin/README.md)、[scripts/README.md](/Users/todo/MineEnergySystem/scripts/README.md)

- 当前脚本体系已经出现“正式入口”“快捷入口”“归档脚本”三个概念，但没有形成统一、可执行的清单边界。换句话说，规范方向已经存在，落地不彻底。文件：[scripts/README.md](/Users/todo/MineEnergySystem/scripts/README.md)、[scripts/SCRIPT_LIST.md](/Users/todo/MineEnergySystem/scripts/SCRIPT_LIST.md)

## 四、问题分级

### P1：必须尽快处理

- `scripts/SCRIPT_LIST.md` 不是完整清单，已经失去“事实来源”资格。清单缺失 `restore_drill.sh`、`render_alertmanager_config.sh`、`setup_mqtt_auth.sh`、`check_production_readiness.py` 等实际脚本，优先级最高。
- `scripts/README.md`、`bin/README.md` 的统计数字与实际目录不一致，属于高可见度误导。
- `README.md` 和新手文档仍存在 `5173` 旧端口叙事，影响启动入口和联调口径统一。

### P2：建议近期处理

- `scripts/python/` 中正式工具、演示脚本、一次性调试脚本混杂，目录边界还不够清楚。
- `bin/` 与 `scripts/shell/` 的优先级说明不够统一，存在双入口并存感。
- `restart_backend.sh`、`rebuild_backend.sh` 这类轻包装脚本是否仍值得作为正式入口，需要明确口径。
- 归档策略未彻底执行，已有 archive 但还没有把一批明显历史脚本降级出去。

### P3：可以后续优化

- 前端 scripts 缺少统一 `check` 聚合命令。
- `scripts/python/README.md`、`scripts/shell/README.md` 的分类还可以更细，比如明确标出“正式入口”“辅助调试”“历史兼容”。
- `scripts/CHANGELOG.md`、归档文档里仍有旧脚本和旧端口表述，但这些不属于第一批必须收口的高风险入口。

## 五、建议的规范化方向

### 1. 入口收口

- 把 `bin/` 明确为“快捷入口层”，只保留极少数高频命令
- 把 `scripts/` 明确为“正式实现层”
- 在主文档里明确：
  - 日常快速启动看 `bin/`
  - 正式实现和完整能力看 `scripts/`

### 2. 文档统一

- 先把 `scripts/SCRIPT_LIST.md` 修成真正的事实来源
- 再让 `README.md`、`bin/README.md`、`scripts/README.md`、子目录 README 全部引用同一套统计和分类口径
- 同步修正旧端口、旧推荐命令、旧路径

### 3. 脚本分类优化

- `scripts/shell/` 内部建议区分：
  - 正式入口
  - 运维辅助
  - 本地环境修复/清理
- `scripts/python/` 内部建议区分：
  - 正式工具
  - 演示脚本
  - 接入调试脚本
  - 历史脚本

### 4. 归档策略

- 继续使用 `scripts/archive/`
- 下一批最适合降级的目标是：
  - `demo_*.py`
  - `serial_*.py`
  - `test_http_device.py`
  - `test_modbus_tcp.py`
  - `test_serial_port.py`
- 先降级文档入口，再决定是否移动文件

### 5. 前端 scripts 优化

- 保持前端原生命令都在 `frontend/package.json`
- 增加一个统一检查入口，例如 `check`
- 文档统一只推荐：
  - `npm run dev`
  - `npm run build`
  - `npm run check`
  - `npm run test:e2e`

### 6. 后续新增脚本的准入规则

- 新脚本先判断属于哪一层：
  - 前端原生命令：进 `frontend/package.json`
  - 仓库级正式实现：进 `scripts/`
  - 高频快捷入口：少量进入 `bin/`
  - 一次性任务：优先写 `docs/plans/`，必要时再临时放脚本
- 若不是长期维护对象，不要直接暴露在正式清单里

## 六、建议的最终目标结构

- `bin/` 只保留极少数快捷入口
- `scripts/` 作为唯一正式实现层
- `scripts/archive/` 作为历史降级区
- `frontend/package.json` 提供前端统一检查入口
- `scripts/SCRIPT_LIST.md` 成为唯一脚本事实来源
- `README.md`、`bin/README.md`、`scripts/README.md`、子目录 README 全部引用同一套脚本分层口径

更具体地说，理想状态应该是：
- 用户要“快速跑起来”，看 `bin/`
- 用户要“正式执行某项能力”，看 `scripts/`
- 用户要“了解全量脚本”，只看 `scripts/SCRIPT_LIST.md`
- 用户要“追历史”，看 `scripts/archive/`

## 七、执行建议

1. 先统一 `README.md` 和新手文档中的旧路径、旧端口、旧入口表述。
2. 再修 `scripts/SCRIPT_LIST.md`，让它成为真实完整的脚本事实来源。
3. 再统一 `bin/README.md`、`scripts/README.md`、`scripts/shell/README.md`、`scripts/python/README.md` 的统计数字和分类口径。
4. 再收口 `bin/` 与 `scripts/` 的边界，把“快捷入口”和“正式实现层”写清楚。
5. 再处理 `scripts/python/` 里的演示脚本、接入调试脚本和 archive 策略。
6. 最后补前端统一检查入口，例如 `check`，把前端脚本入口也收口完成。

