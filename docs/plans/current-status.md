# Current Status

## 当前总目标
- 当前主主题：`设备监控页实时数据语义收敛专题`
- 当前总目标：完成补偿类设备监控语义与补偿扩展接口收敛，并进入主题收口判断。
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

---

## 当前阻塞
- 当前无代码阻塞，主题已进入规则/验收收口判断。

## 当前待办
- [x] 进入阶段收口判断（不默认继续下一轮）
- [ ] 规则角色确认是否将补偿类接口约定正式冻结为 `/devices/{id}/compensation/*`
- [ ] 验收角色确认本主题是否正式收口与主区切换

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
- 本地重启 `scripts/python/run_mqtt_ingest_worker.py` 后，补偿类 MQTT 最新联调记录已验证：
  - 设备 `16`（电容控制器）最新 `energydata.reactive_power=-21.4`
  - 设备 `21`（SVG）最新 `energydata.reactive_power=322.68`
  - 两者最新 `mqtt_ingestion_record.status=success`，topic 均为 `campus/telemetry`

## 当前剩余风险
- 当前补偿器页中的“补偿级数 / 控制模式 / 柜内温度健康度”等部分仍含演示占位，后续如接真实字段需新开后端/联调轮次。
- 若仓库外联调脚本、第三方调用或人工调试习惯仍访问旧 `/svg`、`/capacitor-bank`，现在会直接返回 404；这是预期的 breaking cleanup。
- `tests/test_device_domain.py` 仍有 1 个既有断言未跟随当前 `public_fields` 口径更新：`timestamp` 已不在该测试期望中，需要后续单独收敛测试口径。
- 电容补偿控制器专属历史趋势当前已接入，但图例较多；若后续联调认为信息密度过高，可单独再做交互收敛。
- 电容补偿控制器参数写入后端已具备最小受控链路，但尚未实现设备回执/执行结果回写；当前只能做到“accepted 入队”，不能保证设备端已执行成功。
- 电容补偿控制器控制台当前仅开放“启用/停用控制器”和少数字段的受控参数写入；单回路手动投切、模式切换、批量参数下发等高风险动作仍未纳入本轮。
- 当前新开放的“手动投切测试 / 报警复位 / 控制模式切换”仍属于模拟器演示控制链路，不代表已接入真实设备协议；后续接真实设备时仍需按真实协议重接。
- 当前主题已进入阶段收口判断，是否正式收口与主区切换仍需规则/验收角色确认。
