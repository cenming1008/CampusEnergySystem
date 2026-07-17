# Handoff

## 当前主题

- 当前主题：`园区光储协同仿真与 EMS 控制`。
- 正式 PLAN：`docs/plans/PLAN-20260716-campus-pv-storage-simulation.md`。
- 详细实施计划：`docs/superpowers/plans/2026-07-16-campus-pv-storage-simulation.md`。
- 收敛设计：`docs/superpowers/specs/2026-07-17-single-storage-system-convergence-design.md`。
- 当前目标：交后端储能角色执行 Task 6，不提前展开 Task 7 或后续任务。

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

## 下一棒：后端储能 Task 6

1. 先添加储能命令生命周期与分类回执测试，确认缺失 service/dispatcher 形成有效 RED。
2. 只支持 `set_active_power`、`set_control_mode`、`stop`，并固定 accepted/running/terminal 状态集合。
3. 校验有限功率、资产额定功率边界、manual/rule/day_ahead 来源、auto/manual 模式及每设备单个 pending 命令。
4. 复用 `DeviceControlLog`、现有 MQTT publisher、行锁和实时事件；分类 dispatcher 必须保留电容补偿旧行为。
5. 增加只处理 `storage-control-api` pending 日志的超时任务；真实运行联调前仍需升级开发库到 `20260716_0002`。
6. 结构化 `reason` 必须记录最新遥测 `data_source` 和可选 `simulation_run_id`；不能以设备编号推断模拟来源。

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

- 本轮只完成 Task 5，不开始 Task 6 生产代码。
- Redis、MQTT health、readiness、rate limit 和部署顺序仍不在当前 Task 6 范围内。
- 主工作树的用户改动 `app/api/README.md` 不得触碰。

## 交接结论

- 园区光储是唯一活跃主主题。
- Task 3：通过并正式完成。
- Task 4：通过并正式完成。
- Task 5：通过并正式完成。
- Task 6：已解除依赖，交后端储能角色执行。
