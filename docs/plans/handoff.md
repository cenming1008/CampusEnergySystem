# Handoff

## 当前主题

- 当前主题：`园区光储协同仿真与 EMS 控制`。
- 正式 PLAN：`docs/plans/PLAN-20260716-campus-pv-storage-simulation.md`。
- 详细实施计划：`docs/superpowers/plans/2026-07-16-campus-pv-storage-simulation.md`。
- 收敛设计：`docs/superpowers/specs/2026-07-17-single-storage-system-convergence-design.md`。
- 当前目标：交后端储能角色执行 Task 11 日前 MILP 优化器，不提前展开 Task 12 或后续任务。

## 已完成与准入

- Task 1、Task 2 已正式完成；Task 2 纯领域实现提交保留至 `efbbe808`。
- 后端可靠性阶段 2A 全部验收通过并完成治理交还，现作为已完成依赖和历史证据保留，不是第二个活跃主主题。
- 阶段 2A 验收提交为 `2c738e61`，补证据提交为 `735ea5c0` 与 `0f22eb60`；共同结构指纹 SHA-256 为 `9f52eafa4140a7328074fa3c6fa4414fe3107a5fa49cbca23a34de60b5acf42c`。
- `campus_energy` 位于 `20260716_0001`，public 表 26 张，`public.energydata` 为 hypertable，启动仅校验。
- Task 3 已完成，提交为 `aa97e3ad`；三条 migration 路径各 682 个对象且共同指纹为 `b81c0db6aaef07fad85a7b617b005e99e1aaafee382e06da6f378eea6d4cbaec`。
- 三条路径均到 `20260716_0002`，均保留 `energydata` hypertable；两张新增表和八个扩展列已核对。
- 全量后端 `740 passed, 5 warnings`，Task 3 Ruff 通过。
- 实际开发库 `campus_energy` 仍在 `20260716_0001`，`storage_asset_profile` 与 `storage_dispatch_plan` 尚未应用。
- Task 4 已完成，提交为 `0e1fd1bc`；完整环境全量后端 `742 passed, 5 warnings`，Task 4 Ruff 通过。
- 仿真扩展 payload 已保持负功率放电符号，并完成三个设备 state 键到持久化 status 列的显式映射。
- Task 5 已完成：五个确定性场景、固定 seed、加速时钟、双控制主题、模拟回执、优雅停止与 `--print-only` 均已落地。
- Task 5 聚焦测试 `12 passed`，完整环境全量后端 `754 passed, 7 warnings`；变更文件 Ruff 与差异检查通过。
- Python 设置与三份环境模板中的储能 EMS/仿真开关均默认关闭；模拟 payload 强制标记 `data_source=simulated`。
- Task 6 已完成：独立储能控制状态机、类别感知 MQTT 回执、每分钟超时收敛及旧补偿路径兼容均已落地。
- Task 6 聚焦与兼容回归 `40 passed, 2 warnings`；完整后端 `767 passed, 2 skipped, 7 warnings`。
- Task 7 已完成 `20260717_0003` 四列/两索引增量、资产档案服务、双层自动门禁和原有储能嵌套 API 扩展。
- Task 7 三条 PostgreSQL migration 路径均为 688 个对象；完整后端 `783 passed, 2 skipped, 7 warnings`。
- Task 8 已完成安全优先纯规则、双门禁 EMS 编排和默认关闭的 60 秒任务；完整后端 `801 passed, 2 skipped, 7 warnings`。
- Task 9 已完成模拟器命令执行、稳定运行标识、终态幂等和独立故障注入；聚焦 `19 passed`，完整后端 `811 passed, 2 skipped, 7 warnings`。
- Task 10 已完成原有储能设备工作台增强，提交为 `a83cbc49`；相关回归 `27 passed`，typecheck、build 与变更文件 ESLint 通过。

## 下一棒：后端储能 Task 11

1. 在 `requirements.txt` 与 `constraints-ci.txt` 固定同一兼容 PuLP 版本，不引入商业求解器。
2. 先写确定性 96 时段 RED，覆盖结果长度、SOC/功率/效率约束、正充负放符号与可复现性。
3. 优化器保持纯领域边界；Task 11 不写调度计划表，也不下发控制命令。
4. 完成聚焦测试、依赖检查、全量后端回归和 Ruff 后再交 Task 12。
5. 真实联调前仍需显式升级开发库到 `20260717_0003`，但 Task 11 纯优化实现本身不要求改动数据库。

## 固定业务契约

- `device_category=storage`。
- `device_subtype=battery_energy_storage_system`。
- 正功率充电、负功率放电。
- 模拟数据必须带 `data_source=simulated`。
- 真实厂商网关未来使用同一契约并标记 `data_source=real`；平台只替换适配器。
- 只保留原有 `StorageMonitorView` 和现有 `EnergyManagement` 路由，后续不得创建模拟版页面或 `/storage-energy` 路由。
- 自动控制全局和单设备均默认关闭，人工接管优先。
- 控制回执必须区分已接收、执行中、成功和失败，不能用入队替代设备执行成功。

## 本轮边界

- 本轮只完成 Task 10，不开始 Task 11 后端代码。
- Redis、MQTT health、readiness、rate limit 和部署顺序仍不在当前 Task 11 范围内。
- 主工作树的用户改动 `app/api/README.md` 不得触碰。

## 交接结论

- 园区光储是唯一活跃主主题。
- Task 3：通过并正式完成。
- Task 4：通过并正式完成。
- Task 5：通过并正式完成。
- Task 6：通过并正式完成。
- Task 7：通过并正式完成。
- Task 8：通过并正式完成。
- Task 9：通过并正式完成。
- Task 10：通过并正式完成。
- Task 11：已解除依赖，交后端储能角色执行。
