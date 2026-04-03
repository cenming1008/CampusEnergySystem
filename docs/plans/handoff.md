# Handoff

## 当前主题
- 当前主主题：测试质量门槛与覆盖率收敛专题
- 当前执行依据：
  - [PLAN-20260403-test-quality-threshold-and-coverage-convergence.md](/Users/todo/MineEnergySystem/docs/plans/PLAN-20260403-test-quality-threshold-and-coverage-convergence.md)

---

## 规范结论
### 当前任务
- 规范线程已完成第三轮边界锁定；前两轮已通过并保留当前主题，下一棒可直接交后端，路径固定为 `规范 -> 后端 -> 验收`。

### 当前结论
- 本轮不再属于“MQTT 采集进程解耦专题”，应切为独立测试主题。
- 当前问题不能简单定义为“把 coverage fail-under 从 50 提高”。
- 更准确的主问题是：测试门槛、统计口径和关键链路保护需要统一质量策略。
- 当前 backend CI 的 `50%` 来自 `.github/workflows/backend-ci.yml`，且 coverage 总表把 `tests/` 自身纳入统计，存在被测试代码抬高总覆盖率的问题。
- 发布检查与试点就绪脚本当前只跑 `unittest`，没有统一 coverage 门槛策略。
- 第一轮已完成并通过验收：
  - coverage 只统计 `app/`
  - `tests/` 不再算入总 coverage 判断
  - backend CI fail-under 已提升到 `55%`
  - 第一批关键链路已完成最小必要补测
- 第二轮已完成并通过验收：
  - `device_service`、`energy_service` 第二批关键链路补测已到位
  - backend fail-under 已提升到 `57%`
  - `run_backend_coverage.sh` 已成为统一 coverage 入口
  - `release_readiness.sh` / `pilot_readiness.sh` 已最小接通统一 coverage 入口
- 第三轮正式名称锁定为：`统一 coverage 入口的 readiness / pilot 实战演练与门槛生效验证`
- 第三轮主目标锁定为：
  - 验证统一 coverage 入口在 `release_readiness.sh` / `pilot_readiness.sh` 中是否真实生效
  - 验证脚本接入没有长出第二套门槛体系
  - 在真实演练基础上补最小必要修复

---

## 规范 -> 后端
### 当前任务
- 后端线程已完成第三轮返工复核，下一棒交验收线程。

### 当前仍有行动价值的信息
- 第三轮仍严格停留在后端测试质量收敛范围内，不扩大到前端或全仓测试体系。
- 当前统一 coverage 入口已经存在并被最小接通：
  - [run_backend_coverage.sh](/Users/todo/MineEnergySystem/scripts/shell/run_backend_coverage.sh)
  - [release_readiness.sh](/Users/todo/MineEnergySystem/scripts/shell/release_readiness.sh)
  - [pilot_readiness.sh](/Users/todo/MineEnergySystem/scripts/shell/pilot_readiness.sh)
  - [backend-ci.yml](/Users/todo/MineEnergySystem/.github/workflows/backend-ci.yml)
- 第三轮只允许围绕这些现有入口做真实演练与最小修正，不允许另起新规则。
- 第三轮后端已完成的事实证据：
  - `release_readiness.sh` 已真实执行到 `Backend coverage gate`
  - `pilot_readiness.sh` 在合格 env 下已真实执行到 `backend_coverage_gate`
  - `pilot_readiness.sh` 失败路径现在也会写 `summary.md`
  - `pilot_readiness.sh` 的通过证据位于：
    - `/tmp/pilot_readiness_pass_20260403/summary.md`
    - `/tmp/pilot_readiness_pass_20260403/logs/backend_coverage_gate.log`
  - `pilot_readiness.sh` 使用 `env.prod.example` 的失败证据位于：
    - `/tmp/pilot_readiness_fail_20260403/summary.md`
- 第三轮返工复核新增证据：
  - `bash ./scripts/shell/run_backend_coverage.sh`：`TOTAL 57%`
  - `bash ./scripts/shell/release_readiness.sh`：`TOTAL 57%`
  - `BACKEND_COVERAGE_FAIL_UNDER=57 BACKEND_COVERAGE_XML=true bash ./scripts/shell/run_backend_coverage.sh`：`TOTAL 57%` 且生成 `coverage.xml`
  - 当前工作区未发现 `release_readiness.sh` / `pilot_readiness.sh` / `backend-ci.yml` 在 coverage 测试集、参数或 fail-under 上存在分叉

### 仅允许的下一步
- 由验收线程复核第三轮返工后是否达到阶段完成。
- 若需打回后端，只能围绕第三轮现有脚本接线、失败摘要或门槛生效证据做小修。
- 不允许在验收后反向扩成新一轮大规模补测或新门槛体系。

### 禁止扩张
- 不把本轮直接扩成全仓测试体系重建。
- 不先做大规模测试重构。
- 不先统一迁移到 pytest。
- 不纳入前端 coverage 治理。
- 不顺手开启大批低覆盖模块补测。
- 不重新设计另一套脚本门槛体系。
- 不把第三轮写成长期测试平台建设。

### 打回条件
- 发现 `release_readiness.sh` / `pilot_readiness.sh` 实际没有复用统一 coverage 入口。
- 发现真实脚本链路中的 coverage 门槛并未按 `57%` 生效。
- 发现脚本演练必须新建第二套门槛规则或新脚本体系才能继续。
- 发现真实演练问题已经扩大成新一轮大规模补测或全仓测试治理。
- 若再次复现 `TOTAL 56%`，但无法提供与当前工作区不同的测试集、参数或快照差异。

## 交给验收
### 当前任务
- 当前第三轮上一轮验收已完成并打回；后端已完成返工复核，下一棒直接交验收。

### 当前验收结论
- 上一轮验收打回点是：`release_readiness.sh` 的真实链路结果被记录为 `TOTAL ... 56%`，与主区“已按 57% 通过”的既有口径不一致。
- 当前返工后需要验收重点复核：
  - `release_readiness.sh` 在当前工作区是否稳定为 `TOTAL 57%`
  - `run_backend_coverage.sh`、`release_readiness.sh`、CI 同构 coverage 命令是否仍共用同一统一入口
  - 若验收仍拿到 `56%`，是否能给出与当前工作区不同的测试集、参数或快照差异证据

---

## 每日归档入口

- [2026-03-27 交接快照](./daily/2026-03/2026-03-27-handoff.md)
- [2026-03-28 交接快照](./daily/2026-03/2026-03-28-handoff.md)
