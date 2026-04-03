# PLAN-20260403-test-quality-threshold-and-coverage-convergence

> 状态：第三轮返工复验通过，待阶段收口 | 负责人：验收线程 | 更新时间：2026-04-03

---

## 背景

当前总控判断，“测试部分仍然不够，coverage 门槛只有 50%，更像建立基线而不是质量兜底”不属于当前主主题“MQTT 采集进程解耦专题”，应作为新主题独立推进。

本轮探索已审视以下范围：

- `.github/workflows/backend-ci.yml`
- `.github/workflows/frontend-ci.yml`
- `.github/workflows/frontend-e2e.yml`
- `tests/`
- `app/`
- `scripts/shell/release_readiness.sh`
- `scripts/shell/pilot_readiness.sh`
- `frontend/package.json`

核心判断不是“仓库完全没有测试”，而是“当前 coverage 门槛、coverage 统计口径、关键链路测试保护没有收敛成统一质量策略”。

---

## 目标

- 明确当前 coverage 门槛具体落在哪些 CI 或本地入口。
- 判断 50% 更像基线过低，还是测试分布失衡与统计口径偏宽共同造成。
- 锁定第一轮最小闭环：先收敛后端 coverage 统计与关键链路测试，再决定是否扩展到前端。

## 关键结论

### 1. 当前 coverage 门槛入口

- GitHub Actions backend CI 在 `.github/workflows/backend-ci.yml` 中执行：
  - `python -m coverage run -m unittest discover -s tests -p 'test_*.py'`
  - `python -m coverage report --fail-under=50`
  - `python -m coverage xml`
- 当前发布检查与试点就绪入口：
  - `scripts/shell/release_readiness.sh`
  - `scripts/shell/pilot_readiness.sh`
  - 都只执行 `python -m unittest discover`
  - 不执行 coverage 门槛校验

结论：

- 50% 目前主要是 GitHub Actions backend CI 的唯一硬门槛。
- 仓库缺少统一的 coverage 配置文件与统一策略承载点。

### 2. 50% 的真实含义

当前 50% 既是“基线门槛过低”，也是“测试分布失衡 + coverage 统计口径偏宽”的结果，但后两者更值得优先处理。

原因：

- 当前 `coverage report -m` 的 `TOTAL 50%` 把 `tests/test_*.py` 自身也纳入总表，而不是只看 `app/`。
- 这意味着当前门槛并不等价于“业务代码覆盖 50%”。
- 仓库已有 39 个后端测试文件，说明问题不是“完全没测”；问题是测试集中在若干近期热点链路，很多大体量核心模块长期低覆盖。

### 3. 当前最缺的不是单一数字，而是三件事

第一优先：

- coverage 统计口径治理

第二优先：

- 关键链路测试补齐

第三优先：

- 分阶段测试门槛策略

当前不建议第一步就只做：

- 直接提高 `--fail-under`

原因：

- 在 coverage 统计仍混入 `tests/` 且关键链路分布失衡时，单独抬高门槛只会制造噪音，不能真正形成质量兜底。

### 4. 当前已有保护与明显缺口

已有一定保护的链路：

- MQTT ingest / bridge / replay / reliability
- health / runtime / monitoring access
- access control / audit
- user service
- 部分 endpoint semantics

当前明显低覆盖且更适合作为第一轮补测对象的模块：

- `app/services/alarm_service.py`：27%
- `app/api/endpoints/health.py`：26%
- `app/application/device_reporting.py`：42%
- `app/core/database.py`：13%
- `app/services/device_service.py`：36%
- `app/services/energy_service.py`：35%

当前更低覆盖但不建议第一轮就一起拉进来的模块：

- `app/services/inspection_service.py`
- `app/services/location_service.py`
- `app/services/fdd_service.py`
- `app/application/reporting.py`
- `app/api/endpoints/forecast/lstm.py`

原因：

- 这些模块要么体量更大，要么更偏专题能力，不适合作为第一轮最短闭环。

### 5. 当前是否要把前端一起纳入

当前不建议。

原因：

- 前端已有独立 `frontend-ci.yml`、`frontend-e2e.yml`，并存在 unit / e2e 测试入口。
- 当前用户提出的问题直接来源于 backend coverage 门槛与 backend 关键链路保护。
- 第一轮若同时纳入前端，会把主题扩大成全仓测试体系重构，降低收敛速度。

## 推荐线程路径

- 当前线程路径固定为：`探索 -> 规范 -> 后端 -> 验收`

## 第一轮最小闭环建议

第一轮不建议直接“提高门槛到某个数字”，而建议按以下顺序收敛：

1. 规范线程先锁 coverage 统计边界
   - 第一轮 coverage 总表只针对 `app/`
   - 不再把 `tests/` 自身纳入总覆盖率
2. 规范线程锁第一阶段 fail-under
   - 采用阶段式上调
   - 不做一步到位高门槛
3. 后端线程优先补第一批关键链路测试
   - `alarm_service`
   - `health endpoint`
   - `device_reporting`
   - `database` 关键迁移/兼容入口
   - 视容量追加 `device_service` 或 `energy_service`
4. 验收线程复核
   - coverage 提升是否来自真实 `app/` 覆盖提升
   - 是否优先补了关键链路，而不是用低价值测试刷数字

## 规范收敛结论

### 1. 当前主题名

- 当前主题正式名称锁定为：`测试质量门槛与覆盖率收敛专题`
- 当前问题不是单点 CI 参数，而是测试门槛、统计口径和关键链路保护需要统一质量策略。

### 2. 第一轮 coverage 统计边界

- 第一轮 coverage 只统计 `app/`
- 第一轮不再把 `tests/` 自身算入总 coverage 判断
- 第一轮涉及 coverage 的 CI / 覆盖配置口径必须统一到同一统计边界

### 3. 第一轮 fail-under 策略

- 第一轮 fail-under 采用分阶段提升
- 第一轮先给出最小可执行门槛，不追求一步到位
- 第一轮 fail-under 锁定为：
  - 在 coverage 总表只统计 `app/` 的前提下，先提升到 `55%`
- 该提升必须和关键链路补测挂钩，不能只改数字
- 后续更高门槛应在第一轮验收通过后再进入下一轮拍板

### 4. 第一批关键链路补测范围

- 第一批优先补测：
  - `app/services/alarm_service.py`
  - `app/api/endpoints/health.py`
  - `app/application/device_reporting.py`
  - `app/core/database.py`
- 可选下一批：
  - `app/services/device_service.py`
  - `app/services/energy_service.py`

### 5. 第一轮允许动作

- 收敛 coverage 统计边界到 `app/`
- 调整相关 CI / 覆盖配置，使 coverage 总表不再混入 `tests/`
- 围绕第一批关键链路补最小必要测试
- 在关键链路补测到位后，同步把 fail-under 提升到第一阶段门槛

### 6. 第一轮禁止扩张项

- 不扩成全仓测试体系重建
- 不先统一迁移到 pytest
- 不在第一轮同时纳入前端测试门槛
- 不把所有低覆盖模块一次性拉进来
- 不只改 `fail-under` 数字而不补关键链路测试

### 7. 第一轮验收口径

- coverage 是否已只统计 `app/`
- fail-under 提升是否来自真实业务代码保护增强
- 第一批关键链路是否真的补到了
- 本轮是否仍然只聚焦后端关键链路

## 非目标

- 本轮不改代码。
- 不把本轮扩成全仓测试框架迁移。
- 不先统一切换到 pytest 体系。
- 不在第一轮同时纳入前端 unit / e2e coverage 门槛。
- 不把所有低覆盖模块一次性拉进补测范围。

## 风险与拍板点

### 风险

- 若直接抬高 fail-under，而 coverage 总表仍混入 `tests/`，门槛会继续失真。
- 若第一轮补测名单过大，会迅速变成长周期测试债务治理。
- 若把前端一起纳入，会打散后端质量门槛收敛的最短闭环。

### 需要拍板

- 第一轮 coverage 是否明确只统计 `app/`
- 第一轮 fail-under 是否采用分阶段提升
- 第一轮关键链路补测是否只聚焦后端，不同时纳入前端

---

## 第一轮后端实现结果

- 新增 [.coveragerc](/Users/todo/MineEnergySystem/.coveragerc)，coverage 统计口径统一只收敛到 `app/`。
- 更新 [backend-ci.yml](/Users/todo/MineEnergySystem/.github/workflows/backend-ci.yml)，将 backend CI 的 `fail-under` 从 `50%` 提升到 `55%`。
- 第一批关键链路已完成最小必要补测：
  - [alarm_service.py](/Users/todo/MineEnergySystem/app/services/alarm_service.py)
  - [health.py](/Users/todo/MineEnergySystem/app/api/endpoints/health.py)
  - [device_reporting.py](/Users/todo/MineEnergySystem/app/application/device_reporting.py)
  - [database.py](/Users/todo/MineEnergySystem/app/core/database.py)
- 对应新增 / 扩展的测试文件为：
  - [test_database_core.py](/Users/todo/MineEnergySystem/tests/test_database_core.py)
  - [test_device_reporting_use_case.py](/Users/todo/MineEnergySystem/tests/test_device_reporting_use_case.py)
  - [test_alarm_service.py](/Users/todo/MineEnergySystem/tests/test_alarm_service.py)
  - [test_application_use_cases.py](/Users/todo/MineEnergySystem/tests/test_application_use_cases.py)

## 第一轮验收结论

### 阶段结论

- 第一轮最小闭环已成立，可进入阶段收口判断。
- 本轮验收通过，不需要打回后端、探索或规范。

### 通过依据

- coverage 总表已收敛到 `app/`，不再混入 `tests/`。
- `55%` 的门槛提升来自真实业务代码保护增强，而不是靠测试代码稀释或简单参数调整。
- 第一批关键链路补测已覆盖：
  - `app/services/alarm_service.py`
  - `app/api/endpoints/health.py`
  - `app/application/device_reporting.py`
  - `app/core/database.py`
- 当前范围仍严格停留在后端关键链路与 backend CI coverage 门槛收敛，没有扩成全仓测试体系重建。

### 验证记录

- `PYTHONPATH=. venv/bin/python -m unittest tests.test_database_core tests.test_device_reporting_use_case tests.test_alarm_service tests.test_health_endpoint tests.test_application_use_cases`
- `PYTHONPATH=. venv/bin/python -m coverage erase && PYTHONPATH=. venv/bin/python -m coverage run -m unittest discover -s tests -p 'test_*.py' && PYTHONPATH=. venv/bin/python -m coverage report --fail-under=55 && PYTHONPATH=. venv/bin/python -m coverage xml`
- 结果：
  - 目标补测集：`34 tests OK`
  - 全量后端测试：`175 tests OK`
  - `app/` coverage：`56%`

### 当前剩余风险

- 第一轮只完成了“口径收敛 + 首批关键链路补测 + fail-under 提升到 55%”，不等于整个后端测试体系已完成收敛。
- `app/core/database.py` 虽已明显改善，但仍有不少运行时 schema sync SQL 分支未被覆盖，本轮只做到第一批最小保护。
- `release_readiness.sh` 与 `pilot_readiness.sh` 仍只执行 `unittest`，尚未统一接入 coverage 门槛；当前质量硬门槛仍以 backend CI 为主。

## 第二轮规范收敛结论

### 1. 第二轮正式名称

- 第二轮正式名称锁定为：`第二批关键链路补测 + backend coverage 继续分阶段提升`

### 2. 第二轮范围

- 围绕第二批关键链路补最小必要测试
- 在真实补测基础上继续抬高 backend coverage 门槛
- 判断是否把 coverage 门槛最小接入：
  - `scripts/shell/release_readiness.sh`
  - `scripts/shell/pilot_readiness.sh`

### 3. 第二轮主目标

- 围绕第二批关键链路补最小必要测试
- 在真实补测基础上继续抬高 backend coverage 门槛
- 为发布检查与试点就绪入口判断是否应最小接入 coverage 门槛提供执行边界

### 4. 第二批关键链路范围

- 第二批优先候选锁定为：
  - `app/services/device_service.py`
  - `app/services/energy_service.py`

### 5. 第二轮允许动作

- 围绕第二批关键链路补测试
- 在后端真实覆盖改善基础上继续提升 fail-under
- 评估并最小接入 readiness / pilot 脚本中的 coverage 门槛，但只允许：
  - 复用现有 coverage 配置与现有后端测试入口
  - 作为 shell 正式入口的最小一致性补齐
  - 不额外引入新测试框架或新脚本体系

### 6. 第二轮禁止扩张项

- 不扩成全仓测试体系重建
- 不先统一迁移到 pytest
- 不同时纳入前端 coverage 门槛治理
- 不把所有低覆盖模块一次性拉进来
- 不把第二轮写成长期测试治理大全

### 7. 第二轮验收口径

- 第二批关键链路是否真的补到了
- fail-under 提升是否来自真实业务代码保护增强
- readiness / pilot 脚本若被纳入，是否保持最小闭环
- 本轮是否仍然只聚焦后端测试质量收敛

---

## 第二轮后端实现结果

- 新增 [test_device_service_round2.py](/Users/todo/MineEnergySystem/tests/test_device_service_round2.py)，补 `create_device_smart()`、`create_device()`、`update_device()`、`get_device_by_id()`、`get_device_data()`、`get_device_statistics()`、`get_device_type_info()` 等关键分支。
- 新增 [test_energy_service_round2.py](/Users/todo/MineEnergySystem/tests/test_energy_service_round2.py)，补 `list_energy_type_catalog()`、`get_energy_type_profile()`、`save_energy_data()`、`calculate_carbon_emission()`、`get_statistics_by_type()`、`get_carbon_summary()`、`save_statistics()` 等关键分支。
- 新增统一入口 [run_backend_coverage.sh](/Users/todo/MineEnergySystem/scripts/shell/run_backend_coverage.sh)，复用现有 `.coveragerc` 与 `coverage run -m unittest discover -s tests -p 'test_*.py'`。
- 更新 [backend-ci.yml](/Users/todo/MineEnergySystem/.github/workflows/backend-ci.yml)，将 backend `fail-under` 从 `55%` 提升到 `57%`，并改为调用统一 coverage 脚本。
- 更新 [release_readiness.sh](/Users/todo/MineEnergySystem/scripts/shell/release_readiness.sh) 与 [pilot_readiness.sh](/Users/todo/MineEnergySystem/scripts/shell/pilot_readiness.sh)，最小接入同一 coverage 门槛入口，没有新建第二套规则。

## 第二轮验收结论

### 阶段结论

- 第二轮最小闭环已成立，可进入阶段收口判断。
- 本轮验收通过，不需要打回后端、探索或规范。

### 通过依据

- 第二批关键链路补测已真实落到：
  - `app/services/device_service.py`
  - `app/services/energy_service.py`
- `57%` 的 backend `fail-under` 提升来自真实业务代码保护增强，而不是只改数字：
  - `app/services/device_service.py`: `48% -> 90%`
  - `app/services/energy_service.py`: `66% -> 88%`
  - `app/` 总 coverage：`56% -> 57%`
- `release_readiness.sh` / `pilot_readiness.sh` 已最小复用统一 coverage 入口，没有长出第二套独立门槛体系。
- 当前范围仍严格停留在后端测试质量收敛专题内，没有扩成全仓测试治理。

### 验证记录

- `PYTHONPATH=. venv/bin/python -m unittest tests.test_device_service_round2 tests.test_energy_service_round2 tests.test_device_monitor_service tests.test_ingestion_reliability`
- `PYTHONPATH=. venv/bin/python -m coverage erase && PYTHONPATH=. venv/bin/python -m coverage run -m unittest discover -s tests -p 'test_*.py' && PYTHONPATH=. venv/bin/python -m coverage report --include='app/*' -m`
- `BACKEND_COVERAGE_FAIL_UNDER=57 BACKEND_COVERAGE_XML=false bash ./scripts/shell/run_backend_coverage.sh`
- `bash -n scripts/shell/run_backend_coverage.sh scripts/shell/release_readiness.sh scripts/shell/pilot_readiness.sh`
- 结果：
  - 第二批目标补测：`33 tests OK`
  - 全量后端测试：`193 tests OK`
  - `app/` coverage：`57%`

### 当前剩余风险

- 第二轮只完成了“第二批关键链路补测 + `57%` 门槛 + readiness/pilot 最小接入”，不等于整个后端测试体系已完全收敛。
- `release_readiness.sh` 与 `pilot_readiness.sh` 虽已复用统一 coverage 入口，但当前仍缺少整条 readiness / pilot 流程的更长链路演练。
- 仍有不少低覆盖模块未纳入当前轮次，本轮不应被误读为批准全仓测试治理。

## 第三轮规范收敛结论

### 1. 第三轮正式名称

- 第三轮正式名称锁定为：`统一 coverage 入口的 readiness / pilot 实战演练与门槛生效验证`

### 2. 第三轮范围

- 验证统一 coverage 入口在 `release_readiness.sh` / `pilot_readiness.sh` 中是否真实生效
- 验证脚本接入没有长出第二套门槛体系
- 在真实演练基础上补最小必要修复
- 当前不把第三轮转成新一轮大规模补测

### 3. 第三轮主目标

- 验证统一 coverage 入口在 readiness / pilot 链路中真实生效
- 验证脚本接入后仍保持同源门槛规则
- 在真实演练基础上，只修正脚本接线、参数传递、失败口径、输出摘要等最小问题

### 4. 第三轮允许动作

- 跑通 readiness / pilot 脚本中的 coverage 入口
- 修正脚本接线、参数传递、失败口径、输出摘要等最小问题
- 补必要测试或脚本级验证
- 保持复用 `scripts/shell/run_backend_coverage.sh`

### 5. 第三轮禁止扩张项

- 不扩成全仓测试体系治理
- 不重新设计另一套脚本门槛体系
- 不顺手开启大批低覆盖模块补测
- 不纳入前端 coverage 治理
- 不迁移 pytest
- 不把第三轮写成长期测试平台建设

### 6. 第三轮验收口径

- `release_readiness.sh` / `pilot_readiness.sh` 是否真实复用统一 coverage 入口
- 覆盖门槛是否在真实脚本链路中有效
- 是否没有长出第二套独立规则
- 本轮是否仍然停留在后端测试质量收敛专题范围内

---

## 第三轮验收结论

### 阶段结论

- 第三轮返工复验已通过，可进入阶段收口判断。
- 当前工作区下，`run_backend_coverage.sh`、`release_readiness.sh` 与 CI 同构 coverage 命令都已稳定给出 `TOTAL 57%`，主区口径现已与真实结果对齐。

### 通过项

- `release_readiness.sh` 确实真实执行到了统一 coverage 入口 `scripts/shell/run_backend_coverage.sh`，且当前工作区稳定返回 `TOTAL 57%`。
- `pilot_readiness.sh` 在合格 env 下确实执行到了 `backend_coverage_gate`，并复用了同一 coverage 入口。
- `pilot_readiness.sh` 失败路径现在也会生成 `summary.md`，满足最小摘要证据要求。
- 当前没有长出第二套独立 coverage 规则，脚本侧仍只有 `run_backend_coverage.sh` 这一套门槛入口。
- `BACKEND_COVERAGE_FAIL_UNDER=57 BACKEND_COVERAGE_XML=true bash ./scripts/shell/run_backend_coverage.sh` 当前工作区也稳定返回 `TOTAL 57%`，并正常生成 `coverage.xml`。

### 未通过项

- 当前复验未发现新的未通过项。

### 验证记录

- `bash ./scripts/shell/run_backend_coverage.sh`
- `bash ./scripts/shell/release_readiness.sh`
- `BACKEND_COVERAGE_FAIL_UNDER=57 BACKEND_COVERAGE_XML=true bash ./scripts/shell/run_backend_coverage.sh`
- `bash ./scripts/shell/release_readiness.sh`
- `bash ./scripts/shell/pilot_readiness.sh --env-file env.prod.example --artifact-dir /tmp/pilot_readiness_fail_20260403`
- `bash ./scripts/shell/pilot_readiness.sh --env-file /tmp/pilot_env_20260403.t9BjjJ --artifact-dir /tmp/pilot_readiness_pass_20260403`
- `bash -n scripts/shell/pilot_readiness.sh`
- `/tmp/pilot_readiness_fail_20260403/summary.md`
- `/tmp/pilot_readiness_pass_20260403/summary.md`
- `/tmp/pilot_readiness_pass_20260403/logs/backend_coverage_gate.log`

### 打回要求

- 当前无需打回后端。
- 下一步仅进入阶段收口判断，不允许借机扩成新一轮大规模补测、pytest 迁移或第二套脚本规则设计。
