# Current Status

## 当前总目标

- 当前主主题：`后端可靠性基线与渐进式解耦治理`
- 当前总目标：先恢复可信测试、CI、迁移和运行基线，再按依赖顺序治理 MQTT 循环、事务所有权和剩余分层债务。
- 当前执行依据：
  - `docs/plans/PLAN-20260610-backend-reliability-progressive-decoupling.md`
  - `docs/superpowers/specs/2026-06-10-backend-reliability-and-decoupling-design.md`
  - `docs/superpowers/plans/2026-06-10-backend-reliability-phase1.md`

---

## 当前阶段

- [x] 完成后端框架规范性、整齐度、可修改性和低耦合审查。
- [x] 确认采用“最终目标彻底治理、执行过程渐进收敛”的路径。
- [x] 完成并审核五阶段技术设计。
- [x] 建立新的重量级主 PLAN。
- [x] 编写阶段 1 逐文件、逐测试、逐提交实施计划。
- [ ] 执行阶段 1：可信测试与 CI 基线。
- [ ] 阶段 1 验收通过后设计阶段 2：迁移、部署与运行可靠性。

## 当前阻塞

- 无方案阻塞。
- 当前全量 pytest 有 4 个已定位失败，必须作为阶段 1 第一项修复。
- 当前 Alembic 离线验证失败属于阶段 2；阶段 1 自动化 CI 时只能显式标记为非阻塞诊断，不得伪装为已通过。

## 当前待办

1. 按 `2026-06-10-backend-reliability-phase1.md` 执行 AnalysisService 回归修复。
2. 将 coverage 和 CI 统一到完整 pytest 测试人口。
3. 拆分 runtime/dev 依赖并建立 CI constraints。
4. 建立 Ruff 历史基线和新增债务门禁。
5. 完成阶段 1 全量验收并记录 CI 运行证据。

## 当前验证结论

- 设计文档已完成占位符、范围、兼容边界和阶段门禁自审。
- 当前审计基线：
  - pytest 收集 541 项。
  - 全量结果为 537 passed、4 failed。
  - 架构专项测试 33 passed。
  - `unittest discover` 只运行 475 项，证明旧 CI 测试人口不完整。
  - Ruff 当前存在历史问题，阶段 1 采用 no-new-debt 基线，不做无关批量修复。
  - Alembic offline upgrade 当前失败，归入阶段 2。

## 当前剩余风险

- 阶段 1 尚未执行，当前分支不能视为后端可靠性基线已恢复。
- CI 自动触发后会扩大执行频率，需要确保测试、依赖锁和 Ruff baseline 在同一提交中闭环。
- migration diagnostic 在阶段 1 暂时非阻塞；阶段 2 未恢复阻塞门禁前，不能宣称部署链可靠。
- MQTT、事务和大型 service 暂未改动，必须等待对应阶段计划。

## 当前验收判断

- 技术设计：通过。
- 实施计划：已完成，待选择执行方式。
- 生产代码：本轮未修改。
- 当前主题：已从后端架构审计切换为后端可靠性与渐进式解耦治理。
