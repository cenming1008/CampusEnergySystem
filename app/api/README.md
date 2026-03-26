# MineEnergySystem API（FastAPI）超详细文档

本文档专注描述 `app/api/` 这一层的 API 实现：包括每个路由模块的入口路径、请求参数（Path/Query/Body）、调用到的业务层函数/Service、返回结构与错误处理方式。

## 1. 应用如何挂载 API

在 `app/main.py` 中：
- `app.include_router(websocket_router)`：挂载 WebSocket 路由
- `register_routers(app)`：注册所有 HTTP API 路由（公开/受保护自动区分）

HTTP API 的路由分发逻辑在 `app/api/router_registry.py` 中完成。

## 2. 统一鉴权与路由保护策略

### 2.1 鉴权方式（JWT + OAuth2PasswordBearer）

`app/api/deps.py` 定义了依赖项 `get_current_user`：
- 使用 `OAuth2PasswordBearer(tokenUrl="/auth/login")` 从 `Authorization: Bearer <token>` 获取 token
- 使用 `settings.secret_key` + `settings.algorithm` 通过 `jose.jwt.decode` 解码 token
- token payload 中读取 `sub` 作为用户名
- 再通过 SQLModel 查询 `User.username == username` 获取用户对象
- 失败时抛出 `AuthenticationException`

### 2.2 公开路由 vs 受保护路由

在 `app/api/router_registry.py` 中：
- `PUBLIC_ROUTERS`
  - `health.router`：前缀 `""`（即根下的 `/health`）
  - `auth.router`：前缀 `"/auth"`（即 `/auth/login`）
- `PROTECTED_ROUTERS`
  - 大部分业务模块均加上 `dependencies=[Depends(get_current_user)]`

意味着：受保护路由的请求都需要 `Authorization: Bearer <token>`。

> 注意：部分端点函数内部也会显式 `Depends(get_current_user)`（例如部分数据清理接口），这在逻辑上等价于重复鉴权（不会改变鉴权结论，但会让代码更“显式”）。

## 3. 返回结构约定

`app/core/response.py` 提供：
- `success_response(data=..., message=...)`：
  - `{"success": true, "message": "...", "data": <data>, "code": "SUCCESS"}`
- `error_response(...)`：
  - `{"success": false, "message": "...", "code": "...", "details": ...}`

在 API 代码中：
- 有些端点直接返回 Pydantic Model / List（依赖 FastAPI 的 `response_model`）
- 有些端点会包一层 `success_response(...)`

## 4. 端点限流（429）

`app/core/rate_limit.py` 的 `limit_requests(bucket, max_calls, window_seconds)`：
- 采用进程内固定窗口限流
- 按 `bucket + client_key` 统计访问次数
- 超过阈值抛出 `HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")`

典型用法出现在：
- `endpoints/auth.py`：`bucket="auth-login"`
- `endpoints/devices/management.py`：`bucket="device-control"`
- `endpoints/devices/data.py`：`bucket="device-report"`

## 5. 错误与日志辅助

`app/api/endpoint_utils.py`：
- `bad_request_from_value_error(exc: ValueError) -> HTTPException`
  - 把业务层 `ValueError` 统一转为 `400`，`detail=str(exc)`
- `log_endpoint_exception(message: str, exc: Exception) -> None`
  - 使用 `app.core.logger.logger.exception(...)` 记录未预期异常

## 6. WebSocket

`app/api/websocket.py` 定义：
- WebSocket 路由：`@router.websocket("/ws")`
- 处理逻辑：
  - `manager.connect(websocket)`
  - 循环等待 `websocket.receive_text()`
  - 断开时 `manager.disconnect(websocket)`

异常会记录日志并在 `finally` 中断开连接。

---

## 7. 逐文件说明（app/api/）

下面按文件列出 `app/api/` 下每个 `.py` 的“它实现了什么”。

---

### 7.1 `app/api/__init__.py`

- 该文件只做聚合导出：
  - `from app.api.deps import get_current_user`
  - `from app.core.database import get_session`
- `__all__ = ["get_current_user", "get_session"]`

---

### 7.2 `app/api/deps.py`（依赖注入：鉴权）

实现内容：
- 定义 `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")`
- 实现 `get_current_user(token=..., session=...) -> User`
  - 解码 JWT，读取 `payload["sub"]`
  - 查找 `User` 并返回
  - 解码失败/用户不存在/username 缺失：抛 `AuthenticationException`

对外影响：
- 所有 `router_registry.py` 的“受保护路由”都会依赖它。

---

### 7.3 `app/api/endpoint_utils.py`（端点复用工具）

实现内容：
- `bad_request_from_value_error`
  - 把 `ValueError` 转为 `400`
- `log_endpoint_exception`
  - 把异常写入日志（`logger.exception`）

对外影响：
- 在 `data_generator.py`、`devices/management.py`、`devices/data.py`、`energy/data.py` 等端点中用于统一处理错误。

---

### 7.4 `app/api/router_registry.py`（HTTP 路由注册中心）

实现内容：
- 定义 `PUBLIC_ROUTERS` 与 `PROTECTED_ROUTERS`：
  - 公开：
    - `health.router` 前缀 `""`（`/health`）
    - `auth.router` 前缀 `"/auth"`（`/auth/login`）
  - 受保护（统一加鉴权依赖）：
    - `devices.router` 前缀 `"/devices"`
    - `alarms.router` 前缀 `"/alarms"`
    - `analysis.router` 前缀 `"/analysis"`
    - `fdd.router` 前缀 `"/fdd"`
    - `reports.router` 前缀 `"/reports"`
    - `forecast.router` 前缀 `"/forecast"`
    - `data_generator.router` 前缀 `"/data-generator"`
    - `energy.router` 前缀 `"/energy"`
    - `maintenance.router` 前缀 `"/maintenance"`
    - `locations.router` 前缀 `"/locations"`
    - `device_groups.router` 前缀 `"/device-groups"`
    - `data_cleanup.router` 前缀 `"/data-cleanup"`
    - `inspection.router` 前缀 `"/inspection"`
- 实现 `register_routers(app: FastAPI) -> None`
  - 遍历公开路由 `app.include_router(...)`
  - 遍历受保护路由时传入 `dependencies=[Depends(get_current_user)]`

---

### 7.5 `app/api/websocket.py`（WebSocket 路由）

实现内容：
- `router = APIRouter()`
- `@router.websocket("/ws") websocket_endpoint`
  - 接入 `app.core.socket_manager.manager`
  - 循环接收文本消息，断开时释放资源

---

### 7.6 `app/api/endpoints/__init__.py`（端点模块聚合）

- 把 `auth/devices/alarms/analysis/.../inspection` 等模块作为导出，供 `router_registry.py` 引用。

---

## 8. 逐文件说明（app/api/endpoints/*）

---

### 8.1 `app/api/endpoints/auth.py`（认证 API）

路由前缀：在 `router_registry.py` 中挂到 `"/auth"`。

接口：
- `POST /auth/login`
  - 输入：`OAuth2PasswordRequestForm`（表单字段：`username`、`password`）
  - 依赖：
    - `session=Depends(get_session)` 获取数据库会话
    - `limit_requests(bucket="auth-login", max_calls=..., window_seconds=...)`
  - 处理：
    - `select(User).where(User.username == form_data.username)`
    - `verify_password(form_data.password, user.hashed_password)`
    - 失败抛 `AuthenticationException("用户名或密码错误")`
    - 成功：`create_access_token(data={"sub": user.username})`
  - 输出：
    - `{"access_token": <jwt>, "token_type": "bearer"}`

---

### 8.2 `app/api/endpoints/health.py`（系统健康检查 API）

路由前缀：公开路由（prefix 为 `""`），因此路径即为 `/health/...`。

接口：
- `GET /health`
  - 输入：无
  - 依赖：`session=Depends(get_session)`
  - 处理：
    - 数据库：执行 `session.exec(select(1)).first()` 判断是否为 `1`
    - Redis：`RedisClient.get_client()` + `await redis.ping()`
    - runtime：`runtime_state.snapshot()` 读取 `mqtt`、`scheduler` 的状态
  - 输出结构（dict）：
    - `status`: `healthy | degraded | unhealthy`
    - `timestamp`
    - `version`: 固定 `"2.0.0"`
    - `services`: `database/redis/mqtt/scheduler` 对应状态
    - `runtime`: runtime_snapshot
- `GET /health/live`
  - 输出：`{"status": "alive", "timestamp": ...}`
- `GET /health/ready`
  - 依赖：`session=Depends(get_session)`
  - 处理：仅检查数据库（`select(1)`）
  - 输出：
    - `ready_status`：`status` 为 `ready` 或 `not_ready`，并带 `checks.database`

---

### 8.3 `app/api/endpoints/alarms.py`（报警管理）

路由前缀：`/alarms`。

接口：
- `GET /alarms/`
  - 查询参数：
    - `limit`（默认 20，最大 100）
    - `device_id`（可选）
    - `resolved`（可选 bool，默认 `False`：即“默认仅看未解决”）
    - `start_time` / `end_time`（可选 datetime）
  - 处理：调用 `AlarmService.list_alarms(...)`
  - 输出：`List[Alarm]`（由 `response_model=List[Alarm]` 控制）
- `POST /alarms/resolve-all?handling_note=...`
  - 查询参数：`handling_note` 可选
  - 依赖：`current_user=Depends(get_current_user)`
  - 处理：`AlarmService.resolve_all_alarms(resolved_by=current_user.username, handling_note=...)`
  - 输出：`success_response(data={"count": count}, message="已解决 {count} 条报警")`
- `POST /alarms/resolve/{alarm_id}?handling_note=...`
  - Path：`alarm_id: int`
  - 依赖：`current_user=Depends(get_current_user)`
  - 处理：
    - `success = AlarmService.resolve_alarm(...)`
    - 若 `success=False`：抛 `HTTPException(404, detail="报警不存在或已解决")`
  - 输出：`success_response(data={"alarm_id": alarm_id}, message="报警已标记为已解决")`

---

### 8.4 `app/api/endpoints/analysis.py`（数据分析）

路由前缀：`/analysis`

接口：
- `GET /analysis/{device_id}`
  - Path：`device_id: int`
  - 依赖：`session=Depends(get_session)`
  - 处理：调用 `analyze_device_use_case(session, device_id)`
  - 输出：直接返回用例返回值（未进行 `success_response` 包装）

---

### 8.5 `app/api/endpoints/fdd.py`（故障诊断）

路由前缀：`/fdd`

接口：
- `GET /fdd/stats`
  - 依赖：`session=Depends(get_session)`
  - 处理：调用 `FDDService.get_fault_diagnosis_stats(session)`
  - 输出：服务返回的统计数据
- `GET /fdd/diagnose/{device_id}`
  - Path：`device_id`
  - 处理：
    - 调用 `FDDService.diagnose_device(session, device_id)`
    - 若返回中包含 `"error"`：抛 `HTTPException(404, detail="设备不存在")`
  - 输出：诊断结果 dict（包含 `device_id/device_name/health_score/suggestions` 等，取决于 service 输出）

---

### 8.6 `app/api/endpoints/reports.py`（报表导出）

路由前缀：`/reports`

接口：
- `GET /reports/export_csv`
  - 依赖：`session=Depends(get_session)`
  - 处理：
    - 创建 `io.StringIO()` 缓冲区与 `csv.writer`
    - 写入表头：`时间/设备ID/设备名称/电压/电流/功率/能耗`
    - 调用 `list_energy_report_rows_use_case(session=session, limit=1000)`
    - 遍历结果并写入 CSV 行（对 timestamp 格式化为 `"%Y-%m-%d %H:%M:%S"`）
  - 输出：
    - `StreamingResponse(iter([output.getvalue()]), media_type="text/csv")`
    - 设置响应头：`Content-Disposition: attachment; filename=energy_report.csv`

---

### 8.7 `app/api/endpoints/maintenance.py`（设备维护管理）

路由前缀：`/maintenance`

文件内定义的请求模型：
- `MaintenanceCreateRequest`：创建维护记录（`device_id/maintenance_type/scheduled_time/title/description/operator/created_by`）
- `MaintenanceUpdateRequest`：更新维护记录（可选字段：`scheduled_time/title/description/operator/cost/parts_replaced/result/next_maintenance_date`）
- `MaintenanceStartRequest`：开始维护（`operator` 可选）
- `MaintenanceCompleteRequest`：完成维护（`result/cost/parts_replaced/next_maintenance_date`）
- `MaintenanceCancelRequest`：取消维护（`reason` 可选）

接口：
- `GET /maintenance/`
  - 查询参数：`device_id, maintenance_type, status, start_date, end_date, limit(1-200), offset(>=0)`
  - 处理：`MaintenanceService.get_maintenance_list(...)`
  - 输出：`List[DeviceMaintenance]`（`response_model=List[...]`）
- `GET /maintenance/types`
  - 输出：`success_response(data=[{"value":..., "label":..., "description":...}, ...])`
  - 说明：通过 `MaintenanceType` 枚举与 `_MAINTENANCE_TYPE_META` 组装
- `GET /maintenance/statuses`
  - 输出：`success_response(data=[...])`
  - 说明：通过 `MaintenanceStatus` 枚举与 `_MAINTENANCE_STATUS_META` 组装
- `GET /maintenance/{maintenance_id}`
  - 输出：单条维护记录详情（`MaintenanceService.get_maintenance_by_id`）
- `POST /maintenance/`
  - Body：`MaintenanceCreateRequest`
  - 处理：`MaintenanceService.create_maintenance(...)`
  - 输出：`DeviceMaintenance`
- `PUT /maintenance/{maintenance_id}`
  - Body：`MaintenanceUpdateRequest`
  - 处理：`request.model_dump(exclude_unset=True)` 后调用 `MaintenanceService.update_maintenance(session, maintenance_id, **update_data)`
- `POST /maintenance/{maintenance_id}/start`
  - Body：`MaintenanceStartRequest`
  - 处理：`MaintenanceService.start_maintenance(session, maintenance_id, request.operator)`
- `POST /maintenance/{maintenance_id}/complete`
  - Body：`MaintenanceCompleteRequest`
  - 处理：`MaintenanceService.complete_maintenance(session, maintenance_id, result=..., cost=..., parts_replaced=..., next_maintenance_date=...)`
- `POST /maintenance/{maintenance_id}/cancel`
  - Body：`MaintenanceCancelRequest`
  - 处理：`MaintenanceService.cancel_maintenance(session, maintenance_id, request.reason)`
- `DELETE /maintenance/{maintenance_id}`
  - 处理：`MaintenanceService.delete_maintenance(...)`
  - 输出：`success_response(message="维护记录 {id} 已删除")`

统计与时间类接口：
- `GET /maintenance/device/{device_id}/history?limit=...`
  - 输出：维护历史列表（`MaintenanceService.get_device_maintenance_history`）
- `GET /maintenance/upcoming/list?days=...`
  - 输出：即将到来的维护计划列表
- `GET /maintenance/overdue/list`
  - 输出：逾期维护列表
- `GET /maintenance/statistics/summary?device_id&start_date&end_date`
  - 处理：`MaintenanceService.get_maintenance_statistics(...)`
  - 输出：`success_response(data=stats)`

---

### 8.8 `app/api/endpoints/locations.py`（位置管理）

路由前缀：`/locations`

文件内定义的请求模型：
- `LocationCreateRequest`：创建位置（`name/location_type/parent_id/code/description/area_sqm/manager/contact`）
- `LocationUpdateRequest`：更新位置（所有字段均为可选）
- `DeviceAssignRequest`：把设备分配到位置（`device_id`）

接口：
- `GET /locations/`
  - 查询：`location_type, parent_id, is_active`
  - 输出：`LocationService.get_all_locations(...)`
- `GET /locations/types`
  - 输出：`success_response(data=types)`
  - 说明：`LocationType` 枚举与 `_LOCATION_TYPE_META` 组装
- `GET /locations/roots`
  - 输出：所有顶级位置（`LocationService.get_root_locations`）
- `GET /locations/tree?root_id&max_depth`
  - 输出：`success_response(data=tree)`
- `GET /locations/search?keyword=...`
  - 输出：匹配位置列表（`LocationService.search_locations`）
- `GET /locations/{location_id}`
  - 输出：位置详情（`LocationService.get_location_by_id`）
- `POST /locations/`
  - Body：`LocationCreateRequest`
  - 输出：`LocationService.create_location(...)`
- `PUT /locations/{location_id}`
  - Body：`LocationUpdateRequest`
  - 处理：`request.model_dump(exclude_unset=True)` -> `LocationService.update_location(...)`
- `DELETE /locations/{location_id}?force=false`
  - 处理：`LocationService.delete_location(session, location_id, force=force)`
  - 输出：`success_response(message="位置 {id} 已删除")`

子位置与设备：
- `GET /locations/{location_id}/children?recursive=false`
  - 输出：子位置列表（可选递归）
- `GET /locations/{location_id}/devices?recursive=false&energy_type&is_active`
  - 输出：位置下设备列表
- `POST /locations/{location_id}/devices`
  - Body：`DeviceAssignRequest`
  - 输出：`LocationService.assign_device_to_location(...)`

统计：
- `GET /locations/{location_id}/statistics?recursive=true`
  - 输出：`success_response(data=stats)`

---

### 8.9 `app/api/endpoints/device_groups.py`（设备分组管理）

路由前缀：`/device-groups`

文件内定义的请求模型：
- `DeviceGroupCreateRequest`：创建分组（`name/code/description/group_type/parent_id/manager/contact`）
- `DeviceGroupUpdateRequest`：更新分组（所有字段可选）
- `AddDeviceRequest`：把单设备加入分组（`device_id/note`）
- `BatchAddDevicesRequest`：批量加入分组（`device_ids`）

接口：
- `GET /device-groups/`
  - 查询：`group_type,parent_id,is_active`
  - 输出：`DeviceGroupService.get_all_groups(...)`（List[DeviceGroup]）
- `GET /device-groups/types`
  - 输出：`success_response(data=types)`（固定四类：production/office/critical/backup）
- `GET /device-groups/search?keyword=...`
  - 输出：匹配分组列表
- `GET /device-groups/statistics`
  - 输出：`success_response(data=stats)`
- `GET /device-groups/{group_id}`
  - 输出：分组详情
- `POST /device-groups/`
  - Body：`DeviceGroupCreateRequest`
  - 输出：`DeviceGroupService.create_group(...)`
- `PUT /device-groups/{group_id}`
  - Body：`DeviceGroupUpdateRequest`（`exclude_unset=True`）
- `DELETE /device-groups/{group_id}?force=false`
  - 处理：`DeviceGroupService.delete_group(..., force=force)`
  - 输出：`success_response(message="分组 {id} 已删除")`

分组内设备：
- `GET /device-groups/{group_id}/devices?energy_type&is_active`
  - 输出：设备列表
- `POST /device-groups/{group_id}/devices`
  - Body：`AddDeviceRequest`
  - 输出：`success_response(data={device_id,group_id,joined_at}, message="设备已添加到分组")`
- `POST /device-groups/{group_id}/devices/batch`
  - Body：`BatchAddDevicesRequest`
  - 输出：`success_response(data={"success_count":count,"total":len(device_ids)}, ...)`
- `DELETE /device-groups/{group_id}/devices/{device_id}`
  - 输出：`success_response(message="设备已从分组中移除")`

统计：
- `GET /device-groups/{group_id}/statistics`
  - 输出：`success_response(data=stats)`
- `GET /device-groups/{group_id}/devices/count`
  - 输出：`success_response(data={"count": count})`

---

### 8.10 `app/api/endpoints/data_generator.py`（数据生成：用于训练/测试）

路由前缀：`/data-generator`

文件职责：
- 对接 `app.integrations.forecasting.ForecastAdapter`
- 提供“生成指定设备数据 / 生成全量系统数据 / 清理数据 / 数据统计”的 HTTP 接口

常量：
- `VALID_DATA_TYPES = {"load","solar","wind"}`

接口：
- `POST /data-generator/generate/device/{device_id}`
  - Path：`device_id`
  - Body（使用 `Body(...)` 显式声明并带范围约束）：
    - `days`（默认 60，1-365）
    - `interval_minutes`（默认 60，1-1440）
    - `data_type`（默认 "load"，必须属于 valid 集合）
    - `clear_existing`（是否清除现有数据，默认 false）
  - 处理：
    - `_validate_data_type`：将输入转小写并校验 `load/solar/wind`
    - 调用 `ForecastAdapter.generate_device_data(...)`
  - 成功输出：
    - `success_response(data={device_id,data_type,days,interval_minutes,count}, message="成功生成 {count} 条数据")`
  - 异常：
    - `HTTPException` 直接抛出
    - `ValueError` -> 400（`bad_request_from_value_error`）
    - 其它 -> 记录日志后 500（`HTTPException(500, "生成数据失败")`）
- `POST /data-generator/generate/all`
  - Body：`days`、`interval_minutes`、`clear_existing`
  - 处理：调用 `ForecastAdapter.generate_system_data(...)`
  - 输出：`success_response(data={"days","interval_minutes","total_count"}, message="成功为所有设备生成 ...")`
- `DELETE /data-generator/clear/{device_id}?days=...`
  - Query：`days` 可选（清理最近 N 天，不传则清空所有）
  - 处理：`ForecastAdapter.clear_device_data(session, device_id=device_id, days=days)`
  - 输出：`success_response(data={"device_id":..., "days":...}, message="数据清除完成")`
- `GET /data-generator/stats/{device_id}`
  - 处理：
    - `SELECT COUNT(*) FROM EnergyData.device_id = ...`
    - 查最早/最晚 timestamp（用于推算覆盖天数）
  - 输出：`success_response(data={device_id,total_count,earliest_time,latest_time,days})`

---

## 9. 逐文件说明（app/api/endpoints/devices/*）

---

### 9.1 `app/api/endpoints/devices/__init__.py`（设备 API 聚合入口）

实现：
- 创建 `router = APIRouter()`
- `include_router(...)`：
  - `management_router`
  - `data_router`
  - `health_router`
  - `monitoring_router`

路由前缀由 `router_registry.py` 决定（`/devices`）。

---

### 9.2 `app/api/endpoints/devices/shared.py`（设备共享模型）

定义 Pydantic 请求模型：
- `DeviceCreateRequest`
  - `name, sn, device_type, location, description, rated_capacity`
- `DeviceUpdateRequest`
  - `name, location, description, rated_capacity`（全可选）
- `DeviceDataReportRequest`
  - 上报数据字段：`consumption` 必填，`flow_rate/power/timestamp/voltage/current/...` 等可选

供：
- `management.py` 使用 `DeviceCreateRequest/DeviceUpdateRequest`
- `data.py` 使用 `DeviceDataReportRequest`

---

### 9.3 `app/api/endpoints/devices/management.py`（设备管理）

路由前缀：`/devices`

接口：
- `GET /devices/`
  - 查询：`energy_type, category, is_active`
  - 输出：`DeviceService.get_all_devices(...)`（List[Device]）
- `GET /devices/types`
  - 输出：`success_response(data=DeviceService.get_device_types())`
- `GET /devices/types/{device_type}`
  - 若不存在：抛 `HTTPException(404, "设备类型不存在")`
  - 输出：`success_response(data=info)`
- `POST /devices/`
  - Body：`DeviceCreateRequest`
  - 处理：`DeviceService.create_device_smart(...)`
  - 错误：
    - `ValueError` -> 400（`bad_request_from_value_error`）
    - 其它 -> 500（`log_endpoint_exception` + `HTTPException(500, "创建设备失败")`）
- `POST /devices/legacy`
  - Body：`device: Device`（直接用 `Device` 模型）
  - 输出：`DeviceService.create_device(session, device)`
- `GET /devices/{device_id}`
  - 输出：`DeviceService.get_device_by_id(session, device_id)`
- `PUT /devices/{device_id}`
  - Body：`DeviceUpdateRequest`
  - 输出：`DeviceService.update_device(...)`
- `DELETE /devices/{device_id}`
  - 处理：
    - 查询 `device = DeviceService.get_device_by_id(...)`
    - 删除 `DeviceService.delete_device(...)`
  - 输出：`success_response(message="设备 {device.name} 已删除")`
- `POST /devices/{device_id}/toggle?active=...&reason=...`
  - 查询/参数：
    - `active: bool`（必填）
    - `reason: Optional[str]`（可选）
  - 依赖：
    - `current_user=Depends(get_current_user)`
    - `limit_requests(bucket="device-control", max_calls=..., window_seconds=...)`
  - 处理：
    - `device = DeviceService.toggle_device_status(..., operator=current_user.username, reason=..., command_source="api")`
    - `publish_control_command(device.id, "start" if active else "stop")`
  - 输出：`device`（直接返回 Device 模型）

---

### 9.4 `app/api/endpoints/devices/data.py`（设备数据接口）

路由前缀：`/devices`

接口：
- `POST /devices/{device_id}/data`
  - Body：`DeviceDataReportRequest`
  - 依赖：
    - 限流：`limit_requests(bucket="device-report", max_calls=..., window_seconds=...)`
  - 处理：
    - `report_device_data_use_case(session, device_id, data=req.model_dump(exclude_none=True), timestamp=req.timestamp)`
  - 错误：
    - `ValueError` -> 400
    - 其它 -> 记录日志后 500
  - 输出：`response_model=EnergyData`
- `GET /devices/{device_id}/data`
  - 查询：
    - `start_time/end_time` 可选
    - `limit`（默认 1000，1-10000）
  - 输出：`List[EnergyData]`
  - 处理：`get_device_data_use_case(...)`
- `GET /devices/{device_id}/statistics`
  - 查询：
    - `start_time/end_time` 必填
    - `period_type`（默认 `"day"`，支持 hour/day/month/year）
  - 输出：`success_response(data=stats)`

---

### 9.5 `app/api/endpoints/devices/monitoring.py`（设备监控接口）

路由前缀：`/devices`

接口（全部使用 `success_response`）：
- `GET /devices/{device_id}/monitor/overview`
  - 调用：`DeviceMonitorService.get_monitor_overview(session, device_id)`
- `GET /devices/{device_id}/monitor/realtime`
  - 调用：`DeviceMonitorService.get_latest_realtime(...)`
- `GET /devices/{device_id}/monitor/runtime-status`
  - 调用：`DeviceMonitorService.get_runtime_status(...)`
- `GET /devices/{device_id}/monitor/trend?start_time&end_time&limit`
  - 调用：`DeviceMonitorService.get_trend_summary(..., limit=...)`
- `GET /devices/{device_id}/monitor/alarms?resolved&start_time&end_time&limit`
  - 调用：`AlarmService.list_alarms(...)`
  - 返回结构：`success_response(data={"items": [...]})`
- `GET /devices/{device_id}/monitor/control-logs?start_time&end_time&limit`
  - 调用：`DeviceMonitorService.get_control_logs(...)`
  - 返回结构：`success_response(data={"items": [...]})`
- `GET /devices/{device_id}/monitor/status-history?hours&limit`
  - 调用：`DeviceMonitorService.get_status_history(session, device_id, hours=..., limit=...)`
  - 返回结构：`success_response(data={"items": [...]})`

---

### 9.6 `app/api/endpoints/devices/health.py`（设备接入健康）

路由前缀：`/devices`

接口：
- `GET /devices/{device_id}/ingestion-health`
  - 调用：`IngestionHealthService.get_device_health(session, device_id)`
  - `ValueError` -> 400
  - 输出：`success_response(data=health)`
- `GET /devices/ingestion-health/overview`
  - 调用：`IngestionHealthService.list_device_health(session)`
  - 输出：`success_response(data={"items": ...})`

---

## 10. 逐文件说明（app/api/endpoints/energy/*）

---

### 10.1 `app/api/endpoints/energy/__init__.py`（能源 API 聚合入口）

实现：
- `router = APIRouter()`
- include：
  - `data_router`（`energy/data.py`）
  - `carbon_router`（`energy/carbon.py`）

路由前缀：`/energy`

---

### 10.2 `app/api/endpoints/energy/shared.py`（能源共享模型与常量）

定义：
- `EnergyDataCreate`
  - 字段：`device_id, energy_type, consumption, flow_rate, timestamp`
  - 可选额外字段：`voltage/current/power_factor/pressure/temperature/supply_temp/return_temp/heat_flow`
- `CarbonSummaryResponse`：`total_carbon` + `by_energy_type: dict`
- `EnergyStatisticsResponse`：
  - `total_consumption, avg_consumption, avg_flow_rate, peak_flow_rate, data_count`
- `ENERGY_DATA_OPTIONAL_FIELDS`
  - 列出可选能量字段名（便于从请求模型动态拼装 kwargs）
- `extract_optional_energy_fields(data: EnergyDataCreate) -> dict`
  - 遍历上述 optional 字段，仅当值非 None 时返回对应键值对

---

### 10.3 `app/api/endpoints/energy/data.py`（能源数据与统计）

路由前缀：`/energy`

接口：
- `POST /energy/data`
  - Body：`EnergyDataCreate`
  - 处理：
    - 调用 `save_energy_data_use_case(...)`
    - 将可选字段通过 `extract_optional_energy_fields(data)` 展开传入
  - 错误：
    - `ValueError` -> 400
    - 其它 -> 记录日志后 500
  - 输出：`EnergyData`（`response_model=EnergyData`）
- `GET /energy/data/{device_id}`
  - 查询：`energy_type, start_time, end_time, limit`
  - 输出：`List[EnergyData]`
  - 处理：`EnergyService.get_energy_data(...)`（直接返回 List）
- `GET /energy/statistics`
  - 查询：
    - `energy_type`、`start_time`、`end_time` 必填
    - `device_id` 可选（系统级统计传 None）
    - `period_type` 默认 `"day"`（hour/day/month/year）
  - 输出：`EnergyStatisticsResponse`（由 `response_model` 限定形状）
  - 处理：`get_energy_statistics_use_case(...)`
- `GET /energy/types`
  - 输出：dict
    - `energy_types`: 列出 EnergyType 对应 label/unit
    - `device_categories`: 列出 DeviceCategory 对应 label
  - 处理逻辑：在函数内部直接从 `app.models.tables` 引用枚举并组装

---

### 10.4 `app/api/endpoints/energy/carbon.py`（碳排放接口）

路由前缀：`/energy`

接口：
- `GET /energy/carbon/emissions`
  - 查询：`device_id` 可选、`energy_type` 可选、`start_time/end_time` 可选
  - 输出：`List[CarbonEmission]`
  - 处理：`list_carbon_emissions_use_case(...)`
- `GET /energy/carbon/summary`
  - 查询：`start_time/end_time` 必填，`device_id` 可选
  - 输出：`CarbonSummaryResponse`
  - 处理：`get_carbon_summary_use_case(...)`
- `GET /energy/carbon/factors`
  - 输出：包含
    - `carbon_factors`: `{energy_type: {factor:<...>, unit:"kg CO2/<unit>"} }`
    - `description`: 固定说明文案
  - 处理：使用 `CARBON_FACTORS` 与 `ENERGY_UNITS`
- `POST /energy/carbon/calculate`
  - 查询参数（使用 Query）：`energy_type`、`consumption`
  - 输出：`success_response(data=calculate_manual_carbon(...))`

---

## 11. 逐文件说明（app/api/endpoints/forecast/*）

---

### 11.1 `app/api/endpoints/forecast/__init__.py`（预测 API 聚合入口）

实现：
- `router = APIRouter()`
- include：
  - `basic_router`（`forecast/basic.py`）
  - `lstm_router`（`forecast/lstm.py`）
  - `admin_router`（`forecast/admin.py`）
- 另外引入了共享工具函数（`validate_prediction_type`、`get_forecast_adapter_or_503`），但在当前文件中主要用于内部封装 `_validate_prediction_type/_get_forecast_adapter`（不直接暴露为端点）。

路由前缀：`/forecast`

---

### 11.2 `app/api/endpoints/forecast/shared.py`（预测共享工具）

职责：
- 处理预测模块是否可用（依赖导入）
- 统一校验预测类型与序列化预测结果

关键逻辑：
- 通过 try/except 判断：
  - `ForecastAdapter` 是否可用（来自 `app.integrations.forecasting`）
  - `LSTM_AVAILABLE` 是否可用（来自 `lstm_forecast`）
- 常量：
  - `VALID_PREDICTION_TYPES={"load","solar","wind"}`
  - `RENEWABLE_PREDICTION_TYPES={"solar","wind"}`
- `ensure_forecast_available()`：不可用 -> `HTTPException(503, "预测模块不可用")`
- `ensure_lstm_available()`：不可用 -> 503，并提示安装 TensorFlow/SciKit-Learn
- `validate_prediction_type(prediction_type, allowed_types=VALID_PREDICTION_TYPES)`
  - lower-case 并校验是否在允许集合
  - 不在则抛 `HTTPException(400, "prediction_type 必须是 '...'" )`
- `get_forecast_adapter_or_503()`：
  - 返回 `get_forecast_adapter()`；初始化失败 -> 503
- `serialize_prediction(prediction: Prediction, include_id=False, include_actual=False) -> dict`
  - 输出字段：`forecast_time, predicted_value, confidence, algorithm, created_at`
  - 可选：`id/device_id`、`actual_value`

---

### 11.3 `app/api/endpoints/forecast/basic.py`（预测基础接口）

路由前缀：`/forecast`

接口：
- `POST /forecast/load`
  - Query：
    - `device_id`（可选）：设备级负荷；不传则预测系统总负荷
    - `hours`（1-168，默认 24）
    - `algorithm`（可选：`lstm/moving_average/linear_regression`）
  - 处理：
    - 调用 `forecast_load_use_case(session, device_id, hours, algorithm)`
    - 返回 `success_response(data=payload, message="成功生成 {count} 个预测点")`
  - 异常：
    - 其它异常 -> 500（`HTTPException(500, "负荷预测失败")`）
- `POST /forecast/renewable/{prediction_type}`
  - Path：`prediction_type`（必须是 solar/wind）
  - Query：
    - `device_id` 可选
    - `hours`（1-168，默认 24）
    - `algorithm` 可选
  - 处理：
    - `validate_prediction_type(prediction_type, RENEWABLE_PREDICTION_TYPES)`
    - 调用 `forecast_load_use_case(...)`
    - 写入 `payload["prediction_type"]=...`
    - 输出 message 文案区分 `光伏`/`风电`
- `GET /forecast/latest/{prediction_type}`
  - Query：
    - `device_id` 可选
    - `limit`（1-168，默认 24）
  - 处理：
    - `validate_prediction_type(prediction_type)`
    - 调用 `list_latest_predictions_use_case(...)`
    - 逐条 `serialize_prediction(p)`
  - 输出：`success_response(data={"predictions":[...], "count": ...})`
- `GET /forecast/accuracy/{prediction_type}`
  - Query：`device_id` 可选，`days`（1-30，默认 7）
  - 处理：`evaluate_prediction_accuracy_use_case(...)`
  - 输出：`success_response(data=accuracy, message="预测准确性评估")`
- `GET /forecast/history/{prediction_type}`
  - Query：
    - `device_id` 可选
    - `start_time/end_time` 可选
    - `limit`（默认 100，1-1000）
  - 处理：
    - 用 SQLModel 查询 `Prediction`，按 `created_at desc` 排序并 limit
    - 序列化时 `include_id=True, include_actual=True`
  - 输出：`success_response(data={"predictions":[...], "count": ...})`

---

### 11.4 `app/api/endpoints/forecast/lstm.py`（LSTM 训练/评估/版本管理）

路由前缀：`/forecast`

公共约束：
- 每个端点开头都会调用 `ensure_lstm_available()`（不可用则直接 503）
- `prediction_type` 都会通过 `validate_prediction_type(prediction_type)` 校验

接口：
- `POST /forecast/lstm/train`
  - Body：
    - `prediction_type`（必填）
    - `device_id`（可选）
    - `days`（默认 60，30-365）
    - `params`（可选 dict）
    - `retrain`（bool，是否强制重新训练）
    - `use_multivariate`（bool，是否使用多变量预测）
    - `version`（可选，如 v1.0.0）
  - 处理：`train_lstm_model_use_case(...)`
  - 输出：`success_response(data=result, message="LSTM模型训练完成")`
- `GET /forecast/lstm/evaluate/{prediction_type}`
  - Query：`device_id` 可选，`test_days`（默认 7，1-30）
  - 输出：`success_response(data=evaluation, message="LSTM模型评估完成")`
- `GET /forecast/lstm/versions/{prediction_type}`
  - Query：`device_id` 可选
  - 处理：
    - 初始化 adapter：`get_forecast_adapter_or_503()`
    - 调用 `adapter.list_versions(prediction_type, device_id)`
  - 输出：`success_response(data={"versions":..., "count": len(...)})`
- `POST /forecast/lstm/versions/{prediction_type}/activate`
  - Body：
    - `version`（必填）
    - `device_id`（可选）
  - 处理：`adapter.set_active_version(...)`
  - 若激活失败：`HTTPException(404, detail="版本不存在")`
  - 输出：`success_response(data={"version": version, "is_active": True}, ...)`
- `GET /forecast/lstm/versions/{prediction_type}/compare`
  - Query：`version1`、`version2` 必填，`device_id` 可选
  - 输出：`success_response(data=comparison, message="版本对比完成")`
- `POST /forecast/lstm/hyperparameter-search`
  - Body：
    - `prediction_type`（必填）
    - `device_id`（可选）
    - `days`（训练数据天数，默认 60）
  - 处理流程（端点内固定网格搜索）：
    - sequence_lengths = [24, 48]
    - lstm_units_list = [[64, 32], [128, 64]]
    - dropout_rates = [0.2, 0.3]
    - epochs_list = [30, 50]
    - 对所有组合：
      - 构造 params（含 batch_size=32、validation_split=0.2、patience=10）
      - 调用 `adapter.train_lstm_model(... retrain=True ...)`
      - 收集 `val_loss/train_loss/epochs_trained`
      - 根据 `val_loss` 维护 best_score/best_params
    - 返回 top 10 结果及最佳参数
  - 输出：`success_response(data={best_params,best_score,all_results,total_tested}, message="超参数搜索完成")`

---

### 11.5 `app/api/endpoints/forecast/admin.py`（预测管理：定时任务）

路由前缀：`/forecast`

接口：
- `GET /forecast/scheduler/jobs`
  - 依赖：`session=Depends(get_session)`（该参数仅用于注入，不在端点内部直接使用 session）
  - 处理：
    - 延迟导入 `from app.services.scheduler_service import get_jobs`
    - 调用 `jobs = get_jobs()`
  - 输出：`success_response(data={"jobs": jobs, "count": len(jobs)}, message="获取定时任务列表成功")`

---

## 12. 逐文件说明（app/api/endpoints/data_cleanup/*）

---

### 12.1 `app/api/endpoints/data_cleanup/__init__.py`（数据清理聚合入口）

实现：
- `router = APIRouter()`
- `include_router(basic_router)`
- `include_router(admin_router)`

路由前缀：`/data-cleanup`

---

### 12.2 `app/api/endpoints/data_cleanup/basic.py`（数据清理基础接口）

路由前缀：`/data-cleanup`

接口：
- `GET /data-cleanup/test`
  - 输出：`{"status":"ok","message":"数据清理API端点正常工作"}`
- `POST /data-cleanup/cleanup`
  - Query：
    - `hours`（默认 1，1-24）
  - 依赖：
    - `session=Depends(get_session)`
    - `current_user=Depends(get_current_user)`（端点内部显式鉴权）
  - 处理流程：
    1. 计算 `cutoff_time = now - timedelta(hours=hours)`
    2. 组装 `results`：
       - `energy_data/alarm_data/carbon_emission` 初始化为 0
       - `errors=[]`
    3. EnergyData 清理：
       - 优先尝试 TimescaleDB `drop_chunks('energydata', INTERVAL '{hours} hours')`
       - 失败则退回 `DELETE FROM energydata WHERE timestamp < :cutoff_time` 统计数量
    4. Alarm 清理：
       - `DELETE FROM alarm WHERE timestamp < :cutoff_time AND is_resolved = true`
    5. CarbonEmission 清理：
       - 优先尝试 TimescaleDB `drop_chunks('carbon_emission', INTERVAL '{hours} hours')`
       - 失败则 `DELETE FROM carbon_emission WHERE timestamp < :cutoff_time`
    6. `total_deleted = energy_data + alarm_data + carbon_emission`
    7. 设置 `status`：
       - `success`：`total_deleted > 0` 或 `errors` 为空
       - `partial`：否则
  - 输出：
    - `success_response(data=results, message="清理完成：共删除 {total_deleted} 条记录")`
  - 异常：整体捕获抛 `HTTPException(500, "数据清理失败")`

---

### 12.3 `app/api/endpoints/data_cleanup/admin.py`（数据清理管理接口）

路由前缀：`/data-cleanup`

接口：
- `POST /data-cleanup/cleanup-all`
  - 依赖：
    - `session=Depends(get_session)`
    - `current_user=Depends(get_current_user)`（显式鉴权）
  - 处理：
    1. 计算 `energydata` 总量，并 `TRUNCATE TABLE energydata CASCADE`
    2. 清理 `alarm`（只清理已解决）：`DELETE FROM alarm WHERE is_resolved = true`
    3. 统计 `carbon_emission` 总量，并 `TRUNCATE TABLE carbon_emission CASCADE`
    4. `status`：
       - `success`：`errors` 为空
       - `partial`：存在 errors
  - 输出：`success_response(data=results, message="清除完成：共删除 {total_deleted} 条记录")`
- `GET /data-cleanup/stats`
  - 依赖：`session=Depends(get_session)` + `current_user=Depends(get_current_user)`
  - 处理：`from app.services.data_cleanup_service import get_data_statistics` -> `stats = get_data_statistics()`
  - 输出：`success_response(data=stats)`

---

## 13. 逐文件说明（app/api/endpoints/devices/相关之外的接口）

---

### 13.1 `app/api/endpoints/inspection.py`（巡检运维）

路由前缀：`/inspection`

文件内定义的请求模型：
- `RouteCreateRequest` / `RouteUpdateRequest`
- `PointCreateRequest` / `PointUpdateRequest`
- `PlanCreateRequest` / `PlanUpdateRequest`
- `TaskCreateRequest`
- `RecordSubmitRequest`（提交巡检记录）

接口组：

1) 巡检路线（Routes）
- `GET /inspection/routes?is_active&offset&limit`
  - 输出：`InspectionService.get_all_routes(...)`
- `POST /inspection/routes`
  - Body：`RouteCreateRequest`
  - 输出：`InspectionService.create_route(...)`
- `GET /inspection/routes/{route_id}`
  - 输出：`InspectionService.get_route_by_id(...)`
- `GET /inspection/routes/{route_id}/points`
  - 输出：`InspectionService.get_route_points(...)`
- `PUT /inspection/routes/{route_id}`
  - Body：`RouteUpdateRequest`
  - 处理：`model_dump` 后构造 `update_fields`（仅保留非 None）
  - 输出：`InspectionService.update_route(...)`
- `DELETE /inspection/routes/{route_id}?force=false`
  - 处理：`InspectionService.delete_route(..., force=force)`
  - 输出：`success_response(message="删除成功")`

2) 巡检点（Points）
- `POST /inspection/points`
  - Body：`PointCreateRequest`
  - 输出：`InspectionService.add_point_to_route(...)`
- `PUT /inspection/points/{point_id}`
  - Body：`PointUpdateRequest` -> 仅传非 None 字段
- `DELETE /inspection/points/{point_id}`
  - 输出：`success_response(message="删除成功")`

3) 巡检计划（Plans）
- `GET /inspection/plans?is_active&offset&limit`
- `POST /inspection/plans`
- `GET /inspection/plans/{plan_id}`
- `PUT /inspection/plans/{plan_id}`
- `DELETE /inspection/plans/{plan_id}?force=false`
  - 输出：`success_response(message="删除成功")`

4) 巡检任务（Tasks）
- `GET /inspection/tasks?status&inspector&start_date&end_date&limit`
- `GET /inspection/tasks/today`
- `GET /inspection/tasks/pending?limit`
- `POST /inspection/tasks`
- `GET /inspection/tasks/{task_id}`
- `POST /inspection/tasks/{task_id}/start?inspector=...`
- `POST /inspection/tasks/{task_id}/complete?remark=...`
- `GET /inspection/tasks/{task_id}/records`

5) 巡检记录（Records）
- `POST /inspection/records`
  - Body：`RecordSubmitRequest`
  - 处理：`InspectionService.submit_inspection_record(...)`

统计：
- `GET /inspection/statistics?start_date&end_date`
  - 输出：`success_response(data=stats)`

---

### 13.2 `app/api/endpoints/*` 中其它入口（已在前文逐文件列出）

`app/api/endpoints/analysis.py`、`app/api/endpoints/fdd.py`、`app/api/endpoints/reports.py`、`app/api/endpoints/alarms.py`、`app/api/endpoints/maintenance.py`、`app/api/endpoints/locations.py`、`app/api/endpoints/device_groups.py`、`app/api/endpoints/data_generator.py` 的接口清单已在前文对应章节逐一给出。

---

## 14. 快速核对：最终 HTTP 路径（从 prefix 推导）

路由最终路径由两层拼接：
- 第一层：`router_registry.py` 给每个 router 设定 prefix（例如 `/devices`）
- 第二层：各 endpoint 文件内 `@router.get/post/...("/xxx")` 定义相对路径

因此你在阅读文档时可以用这个规则快速核对：
- 例如 `endpoints/devices/management.py` 的 `@router.get("/")` 在 `/devices` prefix 下最终就是 `GET /devices/`
- `endpoints/forecast/basic.py` 的 `@router.post("/load")` 在 `/forecast` prefix 下最终就是 `POST /forecast/load`

