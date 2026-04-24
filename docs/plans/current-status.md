# Current Status

## 当前总目标
- 当前主主题：`设备监控页实时数据语义收敛专题`
- 当前总目标：完成补偿类设备监控语义与补偿扩展接口收敛，并对 `MVP+` 阶段完成结论执行正式收口判断。
- 当前执行依据：
  - /Users/todo/CampusEnergySystem/docs/plans/PLAN-20260413-device-monitor-realtime-semantic-convergence.md

---

## 当前阶段
- [x] 已完成上一轮：补偿器实时监控语义收敛
- [x] 已重开本主题，新增“补偿器专属详情页 UI 优化”执行轮次
- [x] 前端已完成补偿器专属页面布局与组件化实现
- [x] 验收角色已确认本轮达到阶段完成
- [x] 已完成 `reactive_power_compensator -> svg` 代码口径统一与补偿类 endpoint 收敛
- [x] 已完成补偿类设备公共层 `energydata.reactive_power` 入库收敛，并确认 SVG / 电容控制器 MQTT 联调可落库
- [x] 前端已补齐电容补偿控制器专属 latest/history 展示：当前快照、三相功率/电压/电流、谐波、投切回放均已接入
- [x] 已新增电容补偿控制器 `控制台` 入口、参数控制档案接口与监控页参数摘要跳转
- [x] 已完成电容补偿控制器控制台 MVP：真实参数回读入库、控制台启停动作复用设备控制主链
- [x] 已补齐电容补偿控制器参数写入后端预埋：参数键校验、前置条件校验、控制日志留痕、MQTT 结构化下发
- [x] 前端已开放电容补偿控制器控制台受控参数写入入口：仅管理员、仅少数字段、二次确认、accepted 入队提示与日志复用已接通
- [x] 已开放电容补偿控制器控制台其余 3 个演示控制动作：手动投切测试、报警复位、控制模式切换
- [x] 已补齐电容补偿控制器模拟控制回执闭环：控制命令附带 `command_id`、模拟器发送结构化回执、MQTT ingest 可回写 `DeviceControlLog.result`
- [x] 已完成补偿器1监视与控制语义收敛：监视页不再使用伪造运行事件，控制台/事件流/控制日志已统一 `accepted/running/success/failed/timeout/rejected` 状态语义
- [x] 已完成补偿控制器正式协议口径预埋：控制能力返回已包含 `protocol_version`、命令/回执消息类型、控制 topic 模板、回执 topic、超时阈值与支持状态集
- [x] 已完成补偿器1完备性复核：确认当前达到“阶段完成 / 可联调可演示 / MVP+”状态，但暂不认定为真实设备正式完善或协议冻结
- [x] 已修复 Windows 补偿器模拟链路首条设备自动注册误判：`CAP-001` 不再因 `power -> flow_rate` 兼容映射被识别为 `water_meter`
- [x] 已在正式 PLAN 中补充补偿类接口冻结口径与“正式完善”门槛
- [x] 已补充 `2026-04-16` Daily 状态/交接快照，主区与 Daily 归档口径已对齐
- [x] 已修复 `DeviceControlConsole` 前端单测桩件与当前控制台组件接口漂移：控制台视图测试不再误向远程控制面板注入 `logView`
- [x] 已完成 `P1` 第一轮关键监控指标真实化压缩：电容补偿控制器的控制模式、回路投入数、容量利用率已优先消费参数快照回读，不再在“无遥测但有快照”时退回 `configured_fallback / estimated`
- [x] 已继续完成 `P1` 温度健康度收口：电容补偿控制器监控页新增 `temperature_health` 语义，优先基于实时温度、温度告警位和参数上限回读输出“正常 / 接近上限 / 超过上限 / 温度告警 / 待判断”
- [x] 已完成补偿器控制链路 UAT 打磨：控制回执主动推送、控制链路日志、JKWF 解码异常 warning、控制回执超时配置化、SQLite 写参风险启动提示与前端控制日志事件刷新均已落地
- [x] 已完成补偿器真实网关适配系统侧收敛：能力接口新增 `remote_commands / writable_parameters`，默认禁用未确认的 `reset_alarm`，参数写入收窄到 6 个 UAT 低风险字段，控制回执已兼容 `refused/unsupported/invalid` 等真实网关拒绝语义并保护终态不被迟到回执覆盖

---

## 当前阻塞
- 当前无代码阻塞；补偿器控制链路已完成 UAT 打磨，剩余事项集中在真实设备/网关联调、最终验收结论与是否正式收口。

## 当前待办
- [x] 进入阶段收口判断（不默认继续下一轮）
- [x] 规则角色已在正式 PLAN 中写明补偿类接口冻结口径：`/devices/{id}/compensation/svg/*` 与 `/devices/{id}/compensation/capacitor-bank/*`
- [ ] 验收角色确认本主题是否以“`MVP+` 阶段完成但暂不正式完善”的口径继续保留，或正式收口并切换主主题

## 当前验证结论
- `cd /Users/todo/CampusEnergySystem/frontend && npm run build` 已通过。
- 补偿器页面已重构为：顶部状态头部 + 主监控区 + 补偿效果趋势 + 运行事件/状态/档案右栏 + 告警表。
- 当前趋势区默认围绕“补偿效果”展开，电压/电流尽量复用真实趋势，缺口位明确以演示占位承接。
- `reactive_power_compensator -> svg` 口径统一已完成，新补偿扩展接口已收敛为 `/devices/{id}/compensation/svg/*` 与 `/devices/{id}/compensation/capacitor-bank/*`。
- 旧顶层 `/svg`、`/capacitor-bank` endpoint 文件与前端兼容 API 文件已从主线仓库删除；全仓库已无旧模块 import 残留。
- `python3 -m py_compile ...` 通过，`venv/bin/python3 -m pytest tests/test_compensation_device_nested_api.py` 通过（`5 passed`）。
- `./venv/bin/python -m pytest tests/test_device_domain.py -q -k reactive_power` 通过（`1 passed`）。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run build` 已通过，电容补偿控制器专属 history 已接入趋势区。
- `./venv/bin/python -m pytest tests/test_compensation_device_nested_api.py -q` 已通过（`6 passed`）。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run test:unit -- DeviceManager` 已通过（`9 passed`）。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run build` 已通过，新增 `DeviceControlConsole` 路由、台账控制台入口与监控页参数摘要均已纳入构建产物。
- `./venv/bin/python -m pytest tests/test_compensation_device_nested_api.py tests/test_capacitor_bank_ingestion.py tests/test_jkwf_lcd_aliases.py -q` 已通过（`37 passed`）。
- `./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py tests/test_device_monitor_service.py -q` 已通过（`18 passed`）。
- `./venv/bin/python -m pytest tests/test_capacitor_bank_service.py tests/test_compensation_device_nested_api.py tests/test_device_management_use_cases.py -q` 已通过（`17 passed`）。
- `./venv/bin/python -m pytest tests/test_capacitor_bank_ingestion.py tests/test_endpoint_application_convergence.py tests/test_device_monitor_service.py -q` 已通过（`29 passed`）。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run typecheck` 已通过。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run test:unit -- DeviceManager` 已通过（`9 passed`）。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run test:unit -- capacitorBankControlProfile DeviceManager` 已通过（`12 passed`）。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run build` 已通过，控制台受控参数写入入口已纳入构建产物。
- `./venv/bin/python -m pytest tests/test_capacitor_bank_service.py tests/test_compensation_device_nested_api.py tests/test_send_capacitor_bank_telemetry.py -q` 已通过（`20 passed`）。
- `./venv/bin/python -m pytest tests/test_capacitor_bank_service.py tests/test_mqtt_processor.py tests/test_send_capacitor_bank_telemetry.py tests/test_compensation_device_nested_api.py -q` 已通过（`30 passed`）。
- `./venv/bin/python -m pytest tests/test_capacitor_bank_service.py tests/test_device_monitor_service.py tests/test_compensation_device_nested_api.py tests/test_mqtt_processor.py tests/test_send_capacitor_bank_telemetry.py -q` 已通过（`42 passed`）。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run typecheck` 已通过，控制能力新增协议字段与补偿器监视页来源标识已完成类型收敛。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run test:unit -- capacitorBankControlProfile DeviceManager` 已通过（`12 passed`）。
- `./venv/bin/python -m pytest tests/test_device_monitor_service.py tests/test_capacitor_bank_service.py tests/test_compensation_device_nested_api.py tests/test_send_capacitor_bank_telemetry.py -q` 已通过（`34 passed`）。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run test:unit -- capacitorBankControlProfile` 已通过（`3 passed`）。
- `./venv/bin/python -m pytest tests/test_ingestion_reliability.py tests/test_capacitor_bank_ingestion.py tests/test_mqtt_processor.py -q` 已通过（`34 passed`）。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run test:unit -- src/views/__tests__/DeviceControlConsole.test.ts` 已通过（`1 passed`），控制台页面测试桩件已与当前组件分层同步。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run test:unit -- src/views/__tests__/DeviceMonitor.test.ts src/features/device-control/__tests__/useControlConsoleData.test.ts` 已通过（`4 passed`）。
- `./venv/bin/python -m pytest tests/test_compensation_device_contract.py tests/test_compensation_monitor_service_boundary.py tests/test_capacitor_bank_service.py -q` 已通过（`16 passed`）。
- `./venv/bin/python -m pytest tests/test_database_core.py tests/test_device_monitor_service.py -q` 已通过（`21 passed`），已覆盖 `CapacitorBankControlProfile` 新增字段、schema 断言与监控页 profile 回退链路。
- `./venv/bin/python -m pytest tests/test_compensation_device_contract.py tests/test_compensation_monitor_service_boundary.py tests/test_capacitor_bank_service.py tests/test_device_monitor_service.py tests/test_database_core.py -q` 已通过（`37 passed`）。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run test:unit -- src/features/device-monitor/components/compensation/__tests__/viewMapping.test.ts` 已通过（`18 passed`），监控页来源文案已补齐 `profile` 来源。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run test:unit -- DeviceMonitor DeviceControlConsole capacitorBankControlProfile src/features/device-monitor/components/compensation/__tests__/viewMapping.test.ts` 已通过（`25 passed`）。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run typecheck` 已通过。
- `./venv/bin/python -m pytest tests/test_compensation_monitor_service_boundary.py tests/test_device_monitor_service.py tests/test_database_core.py tests/test_capacitor_bank_service.py -q` 已通过（`36 passed`），已覆盖温度健康度的阈值判定与告警位优先级。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run test:unit -- DeviceMonitor src/features/device-monitor/components/compensation/__tests__/viewMapping.test.ts` 已通过（`21 passed`）。
- `env PYTHONPATH=/Users/todo/CampusEnergySystem ./venv/bin/pytest tests/test_capacitor_bank_service.py tests/test_capacitor_bank_control_command_service_boundary.py tests/test_capacitor_bank_parameter_write_service_boundary.py tests/test_capacitor_bank_ingestion.py tests/test_compensation_mqtt_boundary.py tests/test_jkwf_lcd_decoder.py tests/test_alarm_service.py tests/test_scheduler_jobs.py tests/test_startup_checks.py -q` 已通过（`75 passed, 1 warning`），已覆盖控制回执推送、notifier 容错、超时配置、JKWF warning、SQLite 写参风险提示与补偿相关回归。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run test:unit -- --run src/features/device-control/__tests__ src/stores/__tests__/useSocketStore.test.ts` 已通过（`8 files / 27 tests passed`），已覆盖当前设备收到 `device_control_log_update` 后刷新控制日志、非当前设备事件不刷新、既有轮询继续保留。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run typecheck` 已通过。
- `env PYTHONPATH=/Users/todo/CampusEnergySystem ./venv/bin/pytest tests/test_capacitor_bank_service.py tests/test_capacitor_bank_control_command_service_boundary.py tests/test_capacitor_bank_parameter_write_service_boundary.py tests/test_compensation_mqtt_boundary.py tests/test_scheduler_jobs.py tests/test_startup_checks.py tests/test_compensation_device_nested_api.py -q` 已通过（`53 passed, 1 warning`），已覆盖真实网关能力收敛、写参 allowlist、回执拒绝别名、迟到/重复回执终态保护和补偿嵌套路由回归。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run test:unit -- --run src/features/device-control/__tests__ src/stores/__tests__/useSocketStore.test.ts` 已通过（`8 files / 30 tests passed`），已覆盖禁用 `reset_alarm`、按 `writable_parameters` 过滤写参卡片和既有 WebSocket 刷新。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run typecheck` 已通过。
- `git diff --check -- <本轮触碰文件>` 已通过；全仓 `git diff --check` 仍会命中既有文档行尾空格，位置在 `docs/guides/five-role-vibe-coding-framework.md`，不属于本轮改动范围。
- 电容补偿控制器控制台已完成以下最小闭环：
  - MQTT 参数快照可更新 `capacitor_bank_control_profile`
  - `GET /devices/{id}/compensation/capacitor-bank/control-profile` 可返回真实参数值、`source`、`snapshot_timestamp`、`source_status`
  - 控制台“启用/停用控制器”已复用设备既有 toggle 主链与控制日志
  - `POST /devices/{id}/compensation/capacitor-bank/control-profile/write` 已具备后端最小受控链路：参数键/值校验、真实参数回读前置检查、`DeviceControlLog` 留痕、MQTT 结构化下发
  - 前端控制台已开放受控参数写入入口：仅管理员可见，当前只开放投入/切除功率因数、投入/切除延时、过压门限、温度上限门限 6 个低风险字段
  - 所有参数写入均要求二次确认，并明确提示“accepted 入队”不等于设备端执行成功
  - 写入日志区域已兼容参数写入记录展示，不再只识别启停动作
  - 远程控制区 4 个动作已全部可点：
    - 启停 / 使能：真实既有主链
    - 手动投切测试 / 报警复位 / 控制模式切换：当前作为演示控制链路，通过补偿控制器专用远程命令接口下发到模拟器
  - `send_capacitor_bank_telemetry.py` 已支持监听 `campus/control/{device_id}`，并响应 `start` / `stop` / `write_parameter` / `manual_switch_test` / `reset_alarm` / `switch_control_mode`
  - 参数写入与 3 个演示控制动作当前已具备模拟回执闭环：
    - 后端下发 payload 附带 `command_id`
    - 模拟器执行后通过 `campus/telemetry` 发送 `message_type=control_receipt`
    - MQTT ingest 会按 `device_id + command_id` 回写对应 `DeviceControlLog.result`
  - 当前回写结果已支持 `running` / `success` / `failed` / `timeout` / `rejected`
- 本轮控制链路 UAT 打磨新增收敛点：
  - MQTT 控制回执成功更新 `DeviceControlLog` 后，会发布 `device_control_log_update` 实时事件；推送失败只打 warning，不影响回执落库
  - 前端控制台继续保留 2 秒 / 5 秒轮询，同时收到当前设备的控制日志事件时会立即触发刷新
  - 远程控制下发、参数写入下发、回执落库、pending 超时收敛均已补结构化日志
  - JKWF 状态寄存器与投切寄存器非法值会打 warning，并保持“不丢整条 payload”的 fallback 行为
  - 控制回执超时由 `COMPENSATION_CONTROL_RECEIPT_TIMEOUT_SECONDS` 配置驱动，默认仍为 120 秒
  - 启动检查会在 SQLite 且补偿器参数写入能力启用时输出 warning，明确生产环境应使用 PostgreSQL 行级锁语义
- 本轮真实网关适配系统侧新增收敛点：
  - 补偿器能力接口新增 `remote_commands` 与 `writable_parameters`，前端不再只依赖本地参数元数据判断可写
  - `reset_alarm` 默认禁用，原因明确为真实网关暂未提供报警复位寄存器/功能码
  - 参数写入后端强制限制到投入/切除功率因数、投入/切除延时、过压门限、温度上限 6 个低风险字段
  - 控制回执将 `unsupported / not_supported / refused / invalid / reject` 等值归一为 `rejected`
  - 已进入 `success / failed / timeout / rejected` 终态的控制日志不会被迟到的不同结果覆盖；重复相同终态回执幂等跳过
- 本轮监视与控制语义新增收敛点：
  - 监视页中“当前模式 / 补偿容量利用率 / 柜内温度”已显式标注真实采集、参数回读、估算/占位、缺测来源，不再默认给出伪造默认值
  - 控制台日志、监控页事件流、控制台最近结果已统一状态文案：`已入队`、`设备执行中`、`执行成功`、`执行失败`、`设备回执超时`、`设备拒绝执行`
  - 超过约定阈值未收到回执的待定控制日志会自动转为 `timeout`
  - 参数写入后端现已补充离线前置校验；前端对快照过期但允许写入的场景已补充风险提示
  - 当前时间范围内无真实运行事件时，监视页不再使用示例事件冒充真实记录，而是明确展示“暂无真实运行事件”
- 本地重启 `scripts/python/run_mqtt_ingest_worker.py` 后，补偿类 MQTT 最新联调记录已验证：
  - 设备 `16`（电容控制器）最新 `energydata.reactive_power=-21.4`
  - 设备 `21`（SVG）最新 `energydata.reactive_power=322.68`
  - 两者最新 `mqtt_ingestion_record.status=success`，topic 均为 `campus/telemetry`
- 本地数据库实设备核验已确认：
  - `补偿器1` 对应设备 `16`，当前设备类型为 `capacitor_bank_controller`
  - 最新公共层遥测存在：`reactive_power=-20.5`、`power_factor=0.9759`
  - 最新专属遥测存在：`temperature=35.1`、`circuit_state_common_1=1`
  - 最新参数快照存在：`source=telemetry`、`switch_on_power_factor=95.0`
  - 最近控制记录已存在成功样本：`reset_alarm -> success`、`manual_switch_test -> success`、`switch_control_mode -> success`
- Windows 模拟链路设备 `CAP-001` 已执行本地矫正：
  - `device_type/device_subtype` 已改为 `capacitor_bank_controller`
  - `device_category` 已改为 `compensation`
  - 既有 `energydata` 的 `energy_type` 已从 `water` 修正为 `electricity`
  - 最新样本已验证为电气语义：`2026-04-16 15:49:57`，`flow_rate=4.73`、`reactive_power=-2.53`、`power_factor=0.882`

## 当前验收判断
- 若验收标准是“补偿器1监控页与控制台是否已经能工作，且本地模拟联调是否闭环”，当前可判定为通过。
- 若验收标准是“是否已经达到真实设备正式完善、所有关键字段均为真实采集、所有高风险控制均已开放且协议冻结”，当前不可判定为通过。
- 当前主区正式口径统一为：补偿器1已达到 `MVP+` 阶段完成，适合按“通过当前轮次、保留真实联调后续动作”的方式执行收口判断；在真实设备 / 网关联调完成前，不认定为正式完善。

## 正式交付缺口清单
- `P0 / 设备联调`：完成真实设备或真实网关控制回执联调，确认正式 `topic`、`payload`、`command_id` 关联键是否继续复用当前口径。
- `P0 / 验收`：至少完成一轮真实设备侧参数写入与远程控制闭环验证，确认日志最终态、失败态、拒绝态、超时态都能稳定落库。
- `P1 / 后端`：将当前仍为 `placeholder / estimated / configured_fallback / mock` 的关键监控指标继续压缩到只剩明确允许的演示字段，重点是控制模式、容量利用率、柜内温度健康度。
- `P1 / 后端` 当前进度：控制模式、回路投入数、容量利用率、温度健康度已完成收口；剩余重点已从“字段来源真实化”转向“真实设备协议闭环”和“高风险动作边界”。
- `P1 / 前端`：在真实字段补齐后，继续收敛监控页来源标识与展示权重，避免估算值与真实值在视觉上同权。
- `P1 / 规则`：明确高风险控制动作边界，决定“继续关闭并写入正式限制”还是“真实联调后正式开放”，不要长期停留在演示态。
- `P2 / 前端测试`：继续把补偿控制台与监控页的视图测试保持为当前组件分层口径，避免后续再出现测试桩件滞后于页面结构的假红。
- 推荐执行顺序：先做真实协议闭环，再做真实字段收口，最后再做高风险动作开放判断与最终验收。

## 当前剩余风险
- 当前补偿器页的控制模式、回路投入数、容量利用率、温度健康度已优先切到真实遥测或参数快照回读；但这仍不等于真实设备/网关控制协议已经冻结。
- 若仓库外联调脚本、第三方调用或人工调试习惯仍访问旧 `/svg`、`/capacitor-bank`，现在会直接返回 404；这是预期的 breaking cleanup。
- `tests/test_device_domain.py` 仍有 1 个既有断言未跟随当前 `public_fields` 口径更新：`timestamp` 已不在该测试期望中，需要后续单独收敛测试口径。
- 电容补偿控制器专属历史趋势当前已接入，但图例较多；若后续联调认为信息密度过高，可单独再做交互收敛。
- 当前未知设备若只上报通用电气字段（`voltage/current/power/reactive_power/power_factor`）而未显式携带 `device_type/device_subtype`，自动注册现在会回落到 `load`，不会再误判成 `water_meter`；若后续希望自动识别为补偿器，仍需补充更明确的设备类型口径或专属特征字段。
- 当前控制回执闭环仍基于模拟器约定消息，不代表真实设备协议已经冻结；后续若接入真实网关/设备，仍需按真实回执报文重接。
- 电容补偿控制器控制台当前仅开放“启用/停用控制器”和少数字段的受控参数写入；单回路手动投切、模式切换、批量参数下发等高风险动作仍未纳入本轮。
- 当前新开放的“手动投切测试 / 报警复位 / 控制模式切换”虽已按正式命令/回执结构收敛，但设备端执行仍主要依赖模拟器；后续接真实设备时仍需按真实网关协议联调。
- 当前 `timeout` 仍按固定超时阈值推断，尚未接入真实设备侧“已接收但稍后执行”的长耗时状态策略。
- 当前 `timeout` 阈值已配置化，但真实设备侧若存在长耗时执行或延迟回执，仍需在真实联调后决定是否扩展为动作级超时策略。
- 当前参数写入并发保护仍依赖数据库行级锁和 pending 写入拒绝；若生产确认使用 SQLite 或多 API 实例高并发写参，需要单独引入 Redis/数据库级分布式锁方案。
- 当前系统侧已按真实网关能力禁用 `reset_alarm`；若后续工控网关脚本补齐报警复位寄存器/功能码，需要新开一轮重新开放能力并补真实回归。
- `baud_rate`、容量编码、极性识别等参数仍保留只读展示或协议元数据，不开放写入；需等工控脚本编码规则确认后再评估。
- 历史控制日志中仍能看到停留在 `accepted` 的旧记录；这说明旧命令或未回执场景仍存在，不能将“当前主链可闭环”外推为“所有历史命令均已闭环”。
- 当前主题已完成规则补口与 Daily 归档；最终是否正式收口与主区切换仍需验收角色拍板。
