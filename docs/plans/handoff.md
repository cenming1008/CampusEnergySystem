# Handoff

## 当前主题
- 当前主主题：`设备监控页实时数据语义收敛专题`
- 当前执行依据：
  - /Users/todo/CampusEnergySystem/docs/plans/PLAN-20260413-device-monitor-realtime-semantic-convergence.md

---

## 阶段结论
- 主题已从“阶段收口候选”重开到“补偿器专属详情页 UI 优化”轮次。
- 前端已完成补偿器专属工业监控页实现，验收已通过。
- `reactive_power_compensator -> svg` 代码口径统一已完成，补偿类接口已统一收敛到设备主线下的 `/devices/{id}/compensation/*`。
- 旧顶层 `/svg`、`/capacitor-bank` endpoint 与前端兼容 API 文件已删除，新嵌套路由只依赖共享 schema 层。
- 演示占位已明确标注，若需接真实字段需新开联调/后端轮次。
- 补偿类设备公共层 `energydata.reactive_power` 已补齐：
  - 根因是 `app/domain/device_payloads.py` 的 `OPTIONAL_REPORT_FIELDS` 之前未包含 `reactive_power`
  - 修复后需重启本地 `mqtt_ingest_worker` 才会生效
  - 当前已用真实 MQTT 联调确认设备 `16` / `21` 的最新公共层无功功率均可入库
- 前端已不再只消费电容控制器 `latest`：
  - `latest` 用于三相电气量、投切状态、状态摘要、采样时间等当前快照
  - `history` 已接入专属趋势区，覆盖三相功率、三相电压、三相电流、谐波、投切回放
- 本轮已新增电容补偿控制器控制台最小闭环：
  - 台账页对 `capacitor_bank_controller` 显示 `控制台` 入口
  - 新增 `/devices/{id}/console` 控制台页，承载设备概览、远程控制区、参数管理只读清单、真实控制日志
  - 新增后端参数档案接口 `/devices/{id}/compensation/capacitor-bank/control-profile`
  - 监控页侧栏新增“控制参数摘要”，并提供跳转控制台入口
  - MQTT 参数快照可更新 `capacitor_bank_control_profile`，控制台不再是纯空壳
  - 控制台“启用/停用控制器”已接到现有设备 toggle 主链，并复用 `DeviceControlLog`
  - 参数写入接口已从纯占位升级为后端受控链路：支持参数键校验、真实回读前置检查、控制日志留痕与 MQTT 结构化下发
  - 前端控制台现已开放受控参数写入入口：
    - 仅 `admin` 可见并允许提交
    - 仅开放 6 个低风险字段：投入/切除功率因数、投入/切除延时、过压门限、温度上限门限
    - 提交前必须二次确认，并明确提示“accepted 入队”不等于设备端执行成功
    - 控制日志区域已能识别 `write:*` 参数写入记录
- 控制台当前能力边界明确：
  - `supports_read=true`
  - `supports_write=true`
  - `supports_remote_control=true`
  - 当前前端只开放“启用/停用控制器”与少数字段受控写入这两类低风险入口
  - 当前仍未完成设备回执/执行结果回写，写入请求只保证“accepted 入队”，不保证设备端已成功执行

## 下一棒
- 下一棒交给规则角色确认补偿类接口正式口径：只保留 `/devices/{id}/compensation/svg/*` 与 `/devices/{id}/compensation/capacitor-bank/*`。
- 下一棒交给验收/设备联调角色：
  - 验收确认“仅管理员 + 仅少数字段 + 二次确认”的前端开放边界是否通过
  - 设备/网关联调继续补参数写入回执或结果回写，把前端状态从“accepted 入队”升级为“结果可见”
