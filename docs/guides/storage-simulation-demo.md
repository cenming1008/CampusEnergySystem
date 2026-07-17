# 储能仿真演示与真实适配器交接

## 1. 边界

园区 EMS 只保留一套储能业务模型、接口和页面。当前模拟器模拟平台验收所需的 BMS/PCS 状态与控制生命周期；未来厂商网关实现同一 MQTT 契约并将 `data_source` 改为 `real`，不新建第二套储能 API、页面或数据库模型。

真实设备完成现场验收前，全局 `STORAGE_EMS_ENABLED` 和设备级 `ems_auto_enabled` 必须保持关闭。模拟器不能替代厂商保护逻辑、寄存器映射、符号/倍率确认和真实 BMS/PCS 联调。

## 2. 精确启动命令

先启动开发基础设施、后端和独立 MQTT 入站 worker：

```bash
docker compose -f docker-compose.dev.yml up -d
PATH=/Users/todo/CampusEnergySystem/venv/bin:$PATH python -m alembic upgrade head
PATH=/Users/todo/CampusEnergySystem/venv/bin:$PATH python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8088
PATH=/Users/todo/CampusEnergySystem/venv/bin:$PATH python scripts/python/run_mqtt_ingest_worker.py
```

开发库必须由操作者明确升级；演示和自动验收脚本不会替你升级、重建或清理真实开发库。

安全打印一条模拟 payload（不连接 MQTT）：

```bash
PATH=/Users/todo/CampusEnergySystem/venv/bin:$PATH python scripts/python/storage_simulator.py \
  --device-code STO-001 --scenario sunny_workday --speed 60 --seed 20260716 --print-only
```

先执行 `bash scripts/shell/gen_dev_mqtt_certs.sh --force-passwd`，将生成的 `.env.local.mqtt` 合并到本地 `.env`。其中 `MQTT_STORAGE_USERNAME=sto-001` 与 `MQTT_STORAGE_PASSWORD` 是模拟器专用设备凭据；`ingest-worker` 是只读采集账号，不能用于发布设备遥测。

启用 `STORAGE_SIMULATION_ENABLED=True` 后，去掉 `--print-only` 可连接配置中的 MQTT broker。系统遥测 topic 为 `campus/device/STO-001/telemetry`，设备控制 topic 为 `campus/control/STO-001`，仅模拟器使用的场景控制 topic 为 `campus/simulation/STO-001/control`。后端 Web 进程不会替代独立入站 worker，真实 MQTT 验收必须同时运行该 worker。

运行不连接 MQTT、不会删除数据的压缩日演示：

```bash
PATH=/Users/todo/CampusEnergySystem/venv/bin:$PATH python scripts/python/run_storage_demo.py \
  --scenario sunny_workday --speed 5760 --seed 20260716 \
  --output-dir artifacts/storage-demo
```

输出包括 `storage-demo-raw.json`、`storage-demo-raw.csv` 和 `storage-demo-summary.json`。本地演示的时间轴与 `simulation_run_id` 由场景和 seed 确定，同一输入生成逐字一致的三份 artifact；真实 MQTT 模拟器仍使用实时戳和每次启动唯一的 UUID。任何验收不变量失败时脚本返回非零状态；所有策略结果由原始序列计算，不写死收益提升。

## 3. 页面与场景

- 原储能设备页继续使用既有设备详情中的 `StorageMonitorView`，设备身份与路由不变。
- 园区级策略比较继续使用现有 `/energy` 能耗分析页中的“光储 EMS”工作区，不新增导航或独立储能页面。
- 五个固定场景：`sunny_workday`、`cloudy_workday`、`weekend_low_load`、`pv_surplus`、`evening_peak`。
- 功率符号：正功率充电，负功率放电。
- 所有模拟遥测必须持久化 `data_source=simulated` 和 `simulation_run_id`；真实网关必须使用 `data_source=real` 且不得伪造模拟运行标识。

## 4. 指标定义

- `grid_import_kwh` / `grid_export_kwh`：15 分钟原始序列积分得到的购电量/上网电量。
- `cost`：电量、电需量、电池退化和弃光惩罚分项之和。
- `peak_grid_kw`：全日网侧进口功率最大值。
- `pv_self_use_rate`：光伏发电中未弃光部分占比。
- `curtailment_kwh`：无法被负荷、储能或外送消纳的光伏电量。
- `throughput_kwh` / `equivalent_cycles`：储能充放电绝对功率积分及按两倍额定能量折算的等效循环。
- `terminal_soc`：应用硬边界后的日末 SOC。
- `feasible_slot_rate`：请求功率无需被物理边界裁剪的时段比例。
- `plan_execution_rate`：只有真实执行证据时才有值；纯策略重放保持 `null`。

## 5. Canonical MQTT fields

真实网关和模拟器必须提供同一规范字段：

```text
device_code, timestamp, device_category=storage,
device_subtype=battery_energy_storage_system, energy_type=electricity,
data_source, soc, soh, active_power, target_active_power,
available_charge_power, available_discharge_power,
bms_state, pcs_state, grid_connection_state, run_state, control_mode,
cell_temp_max, cell_temp_min, cell_temp_avg, fault_code, alarm_code
```

平台持久化时将 `bms_state`、`pcs_state`、`grid_connection_state` 映射为 `bms_status`、`pcs_status`、`grid_status`。厂商网关负责把厂商寄存器、倍率、枚举和告警位转换到上述字段；平台业务服务不承载厂商协议分支。

控制回执必须按 `accepted -> running -> success|failed|rejected|timeout` 表达生命周期，入队不等于执行成功。现场接入必须验证厂商的充放电符号、功率倍率、SOC/温度边界、故障与保护语义，再考虑开启自动控制。

## 6. 安全 cutover preview

先停止模拟器，并等待至少 5 分钟确认没有新的 simulated 遥测。只读预览：

```bash
PATH=/Users/todo/CampusEnergySystem/venv/bin:$PATH python scripts/python/storage_cutover.py \
  --device-code STO-001 --preview
```

预览只统计该精确设备的 simulated 遥测、simulated 计划，以及 `command_source=storage-control-api` 且结构化 `reason.data_source=simulated` 的控制日志。它不会删除设备档案、资产档案、权限、真实记录或其他设备数据。

执行模式刻意要求操作人和预览所得三个计数；计数漂移、设备级自动控制仍开启、模拟器仍活跃或目标不是 storage 时零删除。自动演示与发布验证禁止调用 `--execute`。

## 7. 故障排查

- 没有遥测：检查仿真门禁、broker/TLS/账号和三个 topic 是否混用，再查看 MQTT 接入记录。
- 发布被拒绝：确认模拟器使用 `MQTT_STORAGE_USERNAME=sto-001`，不要复用只读 `ingest-worker`。
- 来源显示错误：检查 payload 的 `data_source`；真实网关不得沿用 `simulated` 或 `simulation_run_id`。
- 功率方向相反：停止控制，先在厂商网关确认符号和倍率；平台固定正充负放。
- 命令一直 pending：检查设备回执是否带同一 `command_id`，并区分 accepted、running 和终态。
- cutover 被拒绝：关闭设备级自动控制、停止模拟器、等待活跃窗口结束并重新 preview；不要绕过计数漂移门禁。
- 表不存在：开发库可能尚未升级到 `20260717_0003`。由操作者按迁移流程确认后升级，不用演示脚本重建数据库。
