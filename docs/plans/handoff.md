# Handoff

## 当前主题

- 当前主题：`园区光储协同仿真与 EMS 控制`。
- 正式 PLAN：`docs/plans/PLAN-20260716-campus-pv-storage-simulation.md`。
- 详细实施计划：`docs/superpowers/plans/2026-07-16-campus-pv-storage-simulation.md`。
- 收敛设计：`docs/superpowers/specs/2026-07-17-single-storage-system-convergence-design.md`。
- 当前目标：Task 15 代码与离线验收已经完成；交现场验收角色取得开发库升级授权、恢复 MQTT 健康并完成只读 preview、真实 MQTT 与人工页面验收。

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
- Task 11 已完成确定性 96 时段日前 MILP 优化器，提交为 `48b91c90`；聚焦 `6 passed`，完整后端 `817 passed, 2 skipped, 7 warnings`。
- Task 12 已完成计划原子替换、EMS 安全执行、每日任务与三条嵌套 API，提交为 `b10991d5`；完整后端 `829 passed, 2 skipped, 7 warnings`。
- Task 13 已完成园区级光储总览、同输入三策略重放、权限过滤、来源/时效/计划状态与显式响应模型，提交为 `e0508eed`；完整后端 `842 passed, 2 skipped, 7 warnings`。
- Task 14 已完成原有 `/energy` 页面光储 EMS 工作区、权限门禁和异步状态保护，提交为 `cdd0bbda`，审查修复为 `be8ae66b`、`bd645552`、`2f681a8d`；聚焦 `31 passed`，typecheck 与 build 通过。
- Task 15 代码与离线验收提交为 `4290f7e3`；精确设备 cutover、确定性演示、适配器替换测试和真实设备交接文档已落地。
- 新增聚焦 `6 passed`、储能回归 `190 passed`、完整后端 `848 passed, 2 skipped, 7 warnings`，覆盖率 `76%`；前端聚焦 `31 passed`，typecheck、build 与 Compose 配置通过。

## 下一棒：现场验收 Task 15

1. 开发库当前仍为 `20260716_0001`，public 26 表且缺少 `storage_asset_profile`/`storage_dispatch_plan`；必须先取得明确授权，再按 Alembic 升级到 `20260717_0003` 并复核。
2. MQTT 容器当前 unhealthy；先恢复 broker 健康，再做真实遥测、控制回执和来源切换联调。
3. 对目标设备只执行 `storage_cutover.py --preview` 并保存三个计数；本交接不授权 `--execute`。
4. 人工检查原 `StorageMonitorView` 和现有 `/energy` 光储 EMS 工作区的来源、功率方向、回执生命周期、空值/错误态和笔记本布局。
5. 全部现场证据通过后完成详细计划 Step 9-12、daily 快照与主题正式收口。

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

- 本轮完成 Task 15 代码与离线验收，但不擅自升级开发库、不修复 MQTT 容器、不执行 cutover `--execute`，也不伪造人工页面验收。
- Redis、readiness、rate limit 和部署顺序仍不在当前 Task 15 范围内；MQTT health 仅作为现场验收前置 blocker 记录。
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
- Task 11：通过并正式完成。
- Task 12：通过并正式完成。
- Task 13：通过并正式完成。
- Task 14：通过并正式完成。
- Task 15：代码与离线验收通过，现场验收待执行。
