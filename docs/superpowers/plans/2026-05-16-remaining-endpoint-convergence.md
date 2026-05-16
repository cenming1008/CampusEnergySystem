# 补齐剩余 endpoint 收敛 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `auth.py` 的 login/refresh/logout 与 `ingestion_health.py` 的 replay 残留在 endpoint 层的编排逻辑下沉到 `app/application/` use case 层。

**Architecture:** 新建 `app/application/auth.py` 承接三个认证 use case；`replay` use case 并入既有 `app/application/telemetry_ingestion.py`。endpoint 收敛为薄入口,只保留 HTTP 关注点。登录限流通过注入闭包 `enforce_rate_limit` 保留原调用顺序,`Request` 不进入 application 层。API 路径、响应字段、审计事件、异常消息全部保持不变。

**Tech Stack:** Python 3、FastAPI、SQLModel、pytest/unittest。

设计依据：`docs/superpowers/specs/2026-05-16-remaining-endpoint-convergence-design.md`

---

## 文件结构

- 新建 `app/application/auth.py` — 认证主流程 use case（login/refresh/logout）
- 修改 `app/api/endpoints/auth.py` — 收敛为薄 endpoint
- 修改 `app/application/telemetry_ingestion.py` — 新增 replay use case
- 修改 `app/api/endpoints/devices/ingestion_health.py` — replay endpoint 收敛 + 清理死导入
- 修改 `app/application/__init__.py` — 导出 4 个新 use case
- 修改 `tests/test_endpoint_application_convergence.py` — 新增 4 个委派测试
- 修改 `tests/test_layer_exports.py` — 新增导出断言
- 修改 `app/application/README.md` — 同步目录与说明

---

## Task 1: 新建 `app/application/auth.py`

**Files:**
- Create: `app/application/auth.py`

- [ ] **Step 1: 创建认证 use case 模块**

创建 `app/application/auth.py`,内容如下（逻辑逐行对应原 `app/api/endpoints/auth.py`,
仅把 `Request` 相关的限流改为注入闭包）：

```python
"""
认证主流程 use case。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from jose import JWTError, jwt
from sqlmodel import Session, select

from app.core.audit import audit_log
from app.core.auth_lock import build_account_lock_message
from app.core.exceptions import AuthenticationException
from app.core.logger import logger
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.core.settings import settings
from app.models.tables import User
from app.services.user_service import UserService


def _build_token_response(user: User) -> dict[str, Any]:
    token_payload = {"sub": user.username, "ver": user.token_version, "role": user.role}
    return {
        "access_token": create_access_token(data=token_payload),
        "refresh_token": create_refresh_token(data=token_payload),
        "token_type": "bearer",
        "role": user.role,
        "must_change_password": user.must_change_password,
    }


def login_use_case(
    session: Session,
    username: str,
    password: str,
    enforce_rate_limit: Callable[[], None],
) -> dict[str, Any]:
    """用户登录主流程：查用户、锁定判定、限流、密码校验、登记成功、签发令牌。"""
    user = session.exec(select(User).where(User.username == username)).first()

    if user and user.locked_until and user.locked_until > datetime.now():
        audit_log("auth.login", user.username, "auth", outcome="failed", reason="locked")
        raise AuthenticationException(build_account_lock_message(user.locked_until))

    enforce_rate_limit()

    if not user or not verify_password(password, user.hashed_password):
        logger.warning(f"登录失败: username={username}")
        failed_user = UserService.register_login_failure(session, username)
        if failed_user and failed_user.locked_until and failed_user.locked_until > datetime.now():
            audit_log("auth.login", username, "auth", outcome="failed", reason="locked")
            raise AuthenticationException(build_account_lock_message(failed_user.locked_until))
        audit_log("auth.login", username, "auth", outcome="failed")
        raise AuthenticationException("用户名或密码错误")

    if not user.is_active:
        audit_log("auth.login", user.username, "auth", outcome="failed", reason="inactive")
        raise AuthenticationException("用户已停用")

    user = UserService.register_login_success(session, user)
    response = _build_token_response(user)
    audit_log(
        "auth.login",
        user.username,
        "auth",
        role=user.role,
        must_change_password=user.must_change_password,
    )
    return response


def refresh_access_token_use_case(session: Session, refresh_token: str) -> dict[str, Any]:
    """使用 refresh token 轮换会话并签发新令牌。"""
    try:
        payload = jwt.decode(
            refresh_token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except JWTError:
        audit_log("auth.refresh", "anonymous", "auth", outcome="failed", reason="invalid_token")
        raise AuthenticationException("刷新令牌无效")

    if payload.get("typ") != "refresh":
        audit_log(
            "auth.refresh",
            str(payload.get("sub") or "anonymous"),
            "auth",
            outcome="failed",
            reason="invalid_type",
        )
        raise AuthenticationException("刷新令牌类型无效")

    username = payload.get("sub")
    if not username:
        raise AuthenticationException("刷新令牌无效")

    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not user.is_active:
        audit_log(
            "auth.refresh",
            username,
            "auth",
            outcome="failed",
            reason="inactive_or_missing",
        )
        raise AuthenticationException("用户不存在或已停用")
    if user.locked_until and user.locked_until > datetime.now():
        audit_log("auth.refresh", user.username, "auth", outcome="failed", reason="locked")
        raise AuthenticationException(build_account_lock_message(user.locked_until))
    if payload.get("ver") != user.token_version:
        audit_log("auth.refresh", user.username, "auth", outcome="failed", reason="token_revoked")
        raise AuthenticationException("刷新令牌已失效，请重新登录")

    user = UserService.rotate_refresh_session(session, user.id)
    response = _build_token_response(user)
    audit_log("auth.refresh", user.username, "auth", role=user.role, rotated=True)
    return response


def logout_use_case(session: Session, current_user: User) -> dict[str, Any]:
    """当前用户登出，吊销现有令牌。"""
    user = UserService.revoke_user_tokens(session, current_user.id)
    audit_log("auth.logout", current_user.username, "auth", role=current_user.role)
    return {
        "success": True,
        "message": "已退出登录",
        "token_version": user.token_version,
    }
```

> 注意：原 `login` 先生成令牌再写审计,`refresh` 同理。本模块用 `response = _build_token_response(user)` 在 `audit_log` 之前生成令牌,保持原顺序。

- [ ] **Step 2: 验证模块可导入**

Run: `DATABASE_URL="postgresql://tester:secret@localhost/test_db" ./venv/bin/python -c "import app.application.auth as m; print(m.login_use_case, m.refresh_access_token_use_case, m.logout_use_case)"`
Expected: 打印三个函数对象,无 ImportError。

- [ ] **Step 3: Commit**

```bash
git add app/application/auth.py
git commit -m "refactor(application): 新增 auth use case 模块"
```

---

## Task 2: 收敛 `auth.py` endpoint 并加委派测试

**Files:**
- Modify: `app/api/endpoints/auth.py`
- Test: `tests/test_endpoint_application_convergence.py`

- [ ] **Step 1: 在测试文件加入 import**

修改 `tests/test_endpoint_application_convergence.py` 顶部 import 块。
当前为：

```python
from app.api.endpoints import analysis, inspection, locations, maintenance, users
from app.api.endpoints.devices import data as device_data
from app.api.endpoints.devices import management
from app.api.endpoints.devices import monitoring as device_monitoring
```

改为：

```python
from app.api.endpoints import analysis, auth, inspection, locations, maintenance, users
from app.api.endpoints.devices import data as device_data
from app.api.endpoints.devices import ingestion_health
from app.api.endpoints.devices import management
from app.api.endpoints.devices import monitoring as device_monitoring
```

- [ ] **Step 2: 写失败测试**

在 `tests/test_endpoint_application_convergence.py` 的 `TestEndpointApplicationConvergence`
类内、`test_users_change_my_password_endpoint_delegates_to_application` 方法之后,
追加三个方法：

```python
    @patch("app.api.endpoints.auth.login_use_case")
    def test_auth_login_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        request = SimpleNamespace()
        form_data = SimpleNamespace(username="alice", password="StrongPass123!")
        expected = {"access_token": "a", "token_type": "bearer"}
        mock_use_case.return_value = expected

        result = auth.login(request=request, form_data=form_data, session=session)

        self.assertIs(result, expected)
        mock_use_case.assert_called_once()
        kwargs = mock_use_case.call_args.kwargs
        self.assertIs(kwargs["session"], session)
        self.assertEqual(kwargs["username"], "alice")
        self.assertEqual(kwargs["password"], "StrongPass123!")
        self.assertTrue(callable(kwargs["enforce_rate_limit"]))

    @patch("app.api.endpoints.auth.refresh_access_token_use_case")
    def test_auth_refresh_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        request = SimpleNamespace(refresh_token="rt-123")
        expected = {"access_token": "new"}
        mock_use_case.return_value = expected

        result = auth.refresh_access_token(request=request, session=session)

        self.assertIs(result, expected)
        mock_use_case.assert_called_once_with(session=session, refresh_token="rt-123")

    @patch("app.api.endpoints.auth.logout_use_case")
    def test_auth_logout_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="alice", role="viewer")
        expected = {"success": True, "message": "已退出登录", "token_version": 3}
        mock_use_case.return_value = expected

        result = auth.logout(current_user=current_user, session=session)

        self.assertIs(result, expected)
        mock_use_case.assert_called_once_with(session=session, current_user=current_user)
```

- [ ] **Step 3: 运行测试确认失败**

Run: `./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py -k auth -q`
Expected: FAIL —— `auth.login` 当前不调用 `login_use_case`,patch 目标 `app.api.endpoints.auth.login_use_case` 不存在会报 `AttributeError`。

- [ ] **Step 4: 收敛 endpoint**

把 `app/api/endpoints/auth.py` 整体替换为：

```python
"""
认证API端点
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import get_current_user
from app.application.auth import (
    login_use_case,
    logout_use_case,
    refresh_access_token_use_case,
)
from app.core.database import get_session
from app.core.rate_limit import limit_requests
from app.core.settings import settings
from app.models.tables import User

router = APIRouter()


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


def _enforce_auth_login_rate_limit(request: Request) -> None:
    limit_requests(
        bucket="auth-login",
        max_calls=settings.auth_rate_limit_count,
        window_seconds=settings.auth_rate_limit_window_seconds,
    )(request)


@router.post("/login")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    """用户登录"""
    return login_use_case(
        session=session,
        username=form_data.username,
        password=form_data.password,
        enforce_rate_limit=lambda: _enforce_auth_login_rate_limit(request),
    )


@router.post("/refresh")
def refresh_access_token(
    request: RefreshTokenRequest,
    session: Session = Depends(get_session),
):
    """使用 refresh token 获取新的 access token。"""
    return refresh_access_token_use_case(session=session, refresh_token=request.refresh_token)


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """当前用户登出，并使现有令牌失效。"""
    return logout_use_case(session=session, current_user=current_user)
```

- [ ] **Step 5: 运行委派测试确认通过**

Run: `./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py -k auth -q`
Expected: PASS（3 passed）。

- [ ] **Step 6: 运行认证回归测试**

Run: `./venv/bin/python -m pytest tests/test_auth_deps.py tests/test_auth_lock_message.py tests/test_user_service.py tests/test_websocket_auth.py -q`
Expected: 全部 PASS（无失败）。

- [ ] **Step 7: Commit**

```bash
git add app/api/endpoints/auth.py tests/test_endpoint_application_convergence.py
git commit -m "refactor(api): auth endpoint 收敛到 application use case"
```

---

## Task 3: 在 `telemetry_ingestion.py` 新增 replay use case

**Files:**
- Modify: `app/application/telemetry_ingestion.py`

- [ ] **Step 1: 补充 import**

修改 `app/application/telemetry_ingestion.py` 的 import 块。
当前为：

```python
from app.application.device_reporting import report_device_data_ingestion_use_case
from app.services.alarm_service import AlarmService
from app.services.ingestion_health_service import IngestionHealthService
from app.services.mqtt_models import TelemetryBroadcastData
```

改为：

```python
from app.application.device_reporting import report_device_data_ingestion_use_case
from app.core.audit import audit_log
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.integrations.mqtt.processor import parse_payload, process_payload_dict
from app.models.tables import MqttIngestionStatus
from app.services.alarm_service import AlarmService
from app.services.ingestion_health_service import IngestionHealthService
from app.services.mqtt_models import TelemetryBroadcastData
from app.services.mqtt_reliability_service import MqttReliabilityService
```

- [ ] **Step 2: 追加 replay use case**

在 `app/application/telemetry_ingestion.py` 文件末尾追加：

```python
def replay_mqtt_ingestion_record_use_case(
    session: Session,
    record_id: int,
    operator_username: str,
) -> dict[str, Any]:
    """人工重放一条失败/死信状态的 MQTT 接入记录。"""
    record = MqttReliabilityService.get_record_by_id(session, record_id)
    if not record:
        raise ResourceNotFoundException("MQTT接入记录", record_id)
    if record.status not in (MqttIngestionStatus.FAILED, MqttIngestionStatus.DEAD_LETTER):
        raise ValidationException("仅失败或死信状态的消息允许人工重放")
    if not record.raw_payload:
        raise ValidationException("该消息未保存原始 payload，无法重放")

    payload = parse_payload(record.raw_payload)
    if payload is None:
        raise ValidationException("原始 payload 已损坏，无法重放")

    message = process_payload_dict(payload, topic=record.topic, raw_payload=record.raw_payload)
    MqttReliabilityService.mark_replayed(session, record)
    session.commit()
    audit_log(
        "mqtt.replay_record",
        operator_username,
        f"mqtt_ingestion_record:{record_id}",
        status_before=record.status,
        device_id=record.device_id,
        replay_count=record.replay_count,
        retry_count=record.retry_count,
    )
    return {
        "record_id": record_id,
        "replayed": True,
        "status_before": record.status,
        "replay_count": record.replay_count,
        "retry_count": record.retry_count,
        "broadcast": message.to_dict() if message else None,
    }
```

> 注意：原 endpoint 在 `mark_replayed` + `commit` 之后才读取 `record.status / replay_count / retry_count`。本 use case 保持完全相同的读取时机,不要把这些读取提前。

- [ ] **Step 3: 验证模块可导入**

Run: `DATABASE_URL="postgresql://tester:secret@localhost/test_db" ./venv/bin/python -c "from app.application.telemetry_ingestion import replay_mqtt_ingestion_record_use_case as f; print(f)"`
Expected: 打印函数对象,无 ImportError。

- [ ] **Step 4: Commit**

```bash
git add app/application/telemetry_ingestion.py
git commit -m "refactor(application): 新增 MQTT 接入记录重放 use case"
```

---

## Task 4: 收敛 `ingestion_health.py` replay endpoint 并加委派测试

**Files:**
- Modify: `app/api/endpoints/devices/ingestion_health.py`
- Test: `tests/test_endpoint_application_convergence.py`

- [ ] **Step 1: 写失败测试**

在 `tests/test_endpoint_application_convergence.py` 的 `TestEndpointApplicationConvergence`
类内、`test_auth_logout_endpoint_delegates_to_application` 方法之后,追加：

```python
    @patch("app.api.endpoints.devices.ingestion_health.replay_mqtt_ingestion_record_use_case")
    def test_ingestion_replay_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="admin", role="admin")
        mock_use_case.return_value = {"record_id": 5, "replayed": True}

        result = ingestion_health.replay_mqtt_ingestion_record(
            record_id=5,
            session=session,
            current_user=current_user,
        )

        self.assertEqual(result["data"], {"record_id": 5, "replayed": True})
        mock_use_case.assert_called_once_with(
            session=session,
            record_id=5,
            operator_username="admin",
        )
```

- [ ] **Step 2: 运行测试确认失败**

Run: `./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py -k ingestion_replay -q`
Expected: FAIL —— patch 目标 `app.api.endpoints.devices.ingestion_health.replay_mqtt_ingestion_record_use_case` 当前不存在,报 `AttributeError`。

- [ ] **Step 3: 收敛 endpoint**

修改 `app/api/endpoints/devices/ingestion_health.py`。

(a) import 块。当前为：

```python
from app.api.endpoint_utils import bad_request_from_value_error
from app.api.deps import ADMIN_ONLY, get_current_user
from app.core.access_control import ensure_device_access, get_allowed_device_ids
from app.core.audit import audit_log
from app.core.database import get_session
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.core.response import success_response
from app.integrations.mqtt.processor import parse_payload, process_payload_dict
from app.models.tables import MqttIngestionStatus, User
from app.services.ingestion_health_service import IngestionHealthService
from app.services.mqtt_reliability_service import MqttReliabilityService

from .health_serializers import serialize_ingestion_record
```

改为（移除 replay 收敛后不再使用的 `audit_log` / `ResourceNotFoundException` /
`ValidationException` / `parse_payload` / `process_payload_dict` / `MqttIngestionStatus`,
新增 `replay_mqtt_ingestion_record_use_case`）：

```python
from app.api.endpoint_utils import bad_request_from_value_error
from app.api.deps import ADMIN_ONLY, get_current_user
from app.application.telemetry_ingestion import replay_mqtt_ingestion_record_use_case
from app.core.access_control import ensure_device_access, get_allowed_device_ids
from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import User
from app.services.ingestion_health_service import IngestionHealthService
from app.services.mqtt_reliability_service import MqttReliabilityService

from .health_serializers import serialize_ingestion_record
```

(b) 把 `replay_mqtt_ingestion_record` 路由函数（当前 endpoint 文件第 109-148 行）整体替换为：

```python
@router.post("/ingestion-records/{record_id}/replay")
def replay_mqtt_ingestion_record(
    record_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    return success_response(
        data=replay_mqtt_ingestion_record_use_case(
            session=session,
            record_id=record_id,
            operator_username=current_user.username,
        )
    )
```

其余路由函数（`get_device_ingestion_health`、`list_device_ingestion_health`、
`list_mqtt_ingestion_records`、`list_device_ingestion_records`）保持不变。

- [ ] **Step 4: 运行委派测试确认通过**

Run: `./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py -k ingestion_replay -q`
Expected: PASS（1 passed）。

- [ ] **Step 5: 运行接入回归测试**

Run: `./venv/bin/python -m pytest tests/test_ingestion_reliability.py tests/test_device_ingestion_health_endpoints.py tests/test_device_ingestion_routes.py tests/test_mqtt_reliability_service.py -q`
Expected: 全部 PASS（无失败）。

- [ ] **Step 6: Commit**

```bash
git add app/api/endpoints/devices/ingestion_health.py tests/test_endpoint_application_convergence.py
git commit -m "refactor(api): MQTT 接入记录重放 endpoint 收敛到 application use case"
```

---

## Task 5: 更新 application 层导出与 layer 测试

**Files:**
- Modify: `app/application/__init__.py`
- Test: `tests/test_layer_exports.py`

- [ ] **Step 1: 写失败测试**

修改 `tests/test_layer_exports.py` 的 `test_application_exports_key_use_cases` 方法,
在现有断言之后追加：

```python
        self.assertTrue(callable(application.login_use_case))
        self.assertTrue(callable(application.refresh_access_token_use_case))
        self.assertTrue(callable(application.logout_use_case))
        self.assertTrue(callable(application.replay_mqtt_ingestion_record_use_case))
```

- [ ] **Step 2: 运行测试确认失败**

Run: `./venv/bin/python -m pytest tests/test_layer_exports.py::TestLayerExports::test_application_exports_key_use_cases -q`
Expected: FAIL —— `module 'app.application' has no attribute 'login_use_case'`。

- [ ] **Step 3: 更新 `__init__.py` 导出**

修改 `app/application/__init__.py`。

(a) 在 `from app.application.analysis import analyze_device_use_case` 之后、
`from app.application.campus import (` 之前,新增一行：

```python
from app.application.auth import (
    login_use_case,
    logout_use_case,
    refresh_access_token_use_case,
)
```

(b) 把 `telemetry_ingestion` 的 import 块。当前为：

```python
from app.application.telemetry_ingestion import (
    TelemetryIngestionResult,
    ingest_telemetry_use_case,
)
```

改为：

```python
from app.application.telemetry_ingestion import (
    TelemetryIngestionResult,
    ingest_telemetry_use_case,
    replay_mqtt_ingestion_record_use_case,
)
```

(c) 在 `__all__` 列表中追加四个名字（放在列表末尾、`"update_location_use_case",` 之后即可）：

```python
    "login_use_case",
    "logout_use_case",
    "refresh_access_token_use_case",
    "replay_mqtt_ingestion_record_use_case",
```

- [ ] **Step 4: 运行测试确认通过**

Run: `./venv/bin/python -m pytest tests/test_layer_exports.py -q`
Expected: PASS（4 passed）。

- [ ] **Step 5: Commit**

```bash
git add app/application/__init__.py tests/test_layer_exports.py
git commit -m "refactor(application): 导出 auth 与 replay use case"
```

---

## Task 6: 更新 `app/application/README.md`

**Files:**
- Modify: `app/application/README.md`

- [ ] **Step 1: 目录结构加 `auth.py`**

在第 2 节的目录树代码块中,把 `├── analysis.py` 之后加入一行,使其变为：

```text
├── __init__.py
├── analysis.py
├── auth.py
├── campus.py
```

- [ ] **Step 2: 目录职责表加一行**

在第 2 节“各文件当前定位”表格中,`analysis.py` 行之后插入一行：

```text
| `auth.py` | 用户登录、刷新令牌、登出等认证主流程 use case | `api/endpoints/auth.py` |
```

- [ ] **Step 3: 新增 auth 主线说明小节**

在第 3 节,把 `### 3.10 telemetry_ingestion.py` 小节之后追加一节：

```text
### 3.11 `auth.py`

面向“用户认证主流程”的 use case，当前承接：

- `login_use_case(...)`
- `refresh_access_token_use_case(...)`
- `logout_use_case(...)`

这一层负责把用户查询、账号锁定判定、密码校验、登录失败计数、令牌签发和认证审计从
endpoint 中收口。登录限流依赖 HTTP `Request`，通过注入 `enforce_rate_limit` 闭包保留在
api 层，use case 只在原步骤位置调用它，不感知 `Request`。
```

- [ ] **Step 4: telemetry_ingestion 小节补 replay 入口**

在第 3 节 `### 3.10 telemetry_ingestion.py` 小节的“当前核心入口”列表,
把原来的单条目扩展为：

```text
该 use case 代表的不是单纯查询，而是一条内部处理流水线，当前核心入口：

- `ingest_telemetry_use_case(...)`：单条遥测的落库、告警与健康状态更新工作流。
- `replay_mqtt_ingestion_record_use_case(...)`：人工重放失败/死信状态的 MQTT 接入记录。
```

- [ ] **Step 5: 更新第 8 节边界现状**

在第 8 节,把首段“截至当前仓库状态…”一句中的已收敛主路径列表补上 `auth`，
并在“仍需注意”列表追加一条：

```text
- `auth.py` 已承接登录/刷新/登出主流程；登录限流闭包是唯一保留在 endpoint 的 HTTP 关注点，新增认证动作时不要把编排堆回 endpoint
- `replay_mqtt_ingestion_record_use_case` 已并入 `telemetry_ingestion.py`；MQTT 接入链路的人工运维动作继续放这里，不要回堆到 `ingestion_health.py` endpoint
```

- [ ] **Step 6: Commit**

```bash
git add app/application/README.md
git commit -m "docs(application): 补充 auth 与 replay use case 说明"
```

---

## Task 7: 全量回归验证

**Files:** 无（仅运行测试）

- [ ] **Step 1: 运行收敛与分层测试**

Run: `./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py tests/test_layer_exports.py -q`
Expected: 全部 PASS（含新增的 4 个委派测试与 layer 导出断言）。

- [ ] **Step 2: 运行认证与接入回归**

Run: `./venv/bin/python -m pytest tests/test_auth_deps.py tests/test_auth_lock_message.py tests/test_user_service.py tests/test_websocket_auth.py tests/test_ingestion_reliability.py tests/test_device_ingestion_health_endpoints.py tests/test_device_ingestion_routes.py tests/test_mqtt_reliability_service.py -q`
Expected: 全部 PASS。

- [ ] **Step 3: 确认 endpoint 已收敛薄化**

Run: `grep -nE "select\(|verify_password|jwt\.decode|process_payload_dict|parse_payload|audit_log" app/api/endpoints/auth.py app/api/endpoints/devices/ingestion_health.py`
Expected: 无输出（两个 endpoint 文件均已不含 ORM 查询、令牌校验、payload 处理与审计调用）。

---

## 完成标准

- 七个 Task 全部提交。
- Task 7 三步验证全部满足。
- `auth.py` 与 `ingestion_health.py` 的目标 handler 已收敛为薄入口。
- API 路径、响应字段、审计事件、异常消息均未变化（由认证与接入回归测试保证）。
