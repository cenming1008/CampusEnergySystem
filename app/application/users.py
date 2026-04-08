"""
用户主流程 use case。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlmodel import Session

from app.core.audit import audit_log
from app.models.tables import User
from app.services.user_service import UserService


@dataclass(frozen=True)
class UserActionResult:
    message: str


def _normalize_location_scope(location_scope: Optional[str]) -> Optional[str]:
    normalized = location_scope.strip() if location_scope else ""
    return normalized or None


def list_users_use_case(
    session: Session,
    current_user: User,
) -> list[User]:
    users = UserService.list_users(session)
    audit_log("user.list", current_user.username, "user:*", role=current_user.role)
    return users


def create_user_use_case(
    session: Session,
    current_user: User,
    username: str,
    password: str,
    role: str,
    is_active: bool = True,
    location_scope: Optional[str] = None,
) -> User:
    user = UserService.create_user(
        session=session,
        username=username,
        password=password,
        role=role,
        is_active=is_active,
        location_scope=_normalize_location_scope(location_scope),
    )
    audit_log("user.create", current_user.username, f"user:{user.username}", role=role)
    return user


def update_user_role_use_case(
    session: Session,
    current_user: User,
    user_id: int,
    role: str,
) -> User:
    user = UserService.update_user_role(
        session=session,
        user_id=user_id,
        role=role,
        acting_user=current_user,
    )
    audit_log("user.update_role", current_user.username, f"user:{user.username}", role=role)
    return user


def update_user_status_use_case(
    session: Session,
    current_user: User,
    user_id: int,
    is_active: bool,
) -> User:
    user = UserService.set_user_active(
        session=session,
        user_id=user_id,
        is_active=is_active,
        acting_user=current_user,
    )
    audit_log("user.update_status", current_user.username, f"user:{user.username}", is_active=is_active, role=current_user.role)
    return user


def update_user_location_scope_use_case(
    session: Session,
    current_user: User,
    user_id: int,
    location_scope: Optional[str],
) -> User:
    normalized_scope = _normalize_location_scope(location_scope)
    user = UserService.update_location_scope(
        session=session,
        user_id=user_id,
        location_scope=normalized_scope,
    )
    audit_log("user.update_scope", current_user.username, f"user:{user.username}", location_scope=normalized_scope, role=current_user.role)
    return user


def change_user_password_use_case(
    session: Session,
    current_user: User,
    user_id: int,
    new_password: str,
) -> UserActionResult:
    user = UserService.change_password(
        session=session,
        user_id=user_id,
        new_password=new_password,
    )
    audit_log("user.change_password", current_user.username, f"user:{user.username}", role=current_user.role)
    return UserActionResult(message=f"用户 {user.username} 密码已更新")


def revoke_user_sessions_use_case(
    session: Session,
    current_user: User,
    user_id: int,
) -> UserActionResult:
    user = UserService.revoke_user_tokens(session=session, user_id=user_id)
    audit_log("user.revoke_sessions", current_user.username, f"user:{user.username}", role=current_user.role)
    return UserActionResult(message=f"用户 {user.username} 已被强制下线")


def set_force_password_reset_use_case(
    session: Session,
    current_user: User,
    user_id: int,
    must_change_password: bool,
) -> User:
    user = UserService.set_force_password_reset(
        session=session,
        user_id=user_id,
        must_change_password=must_change_password,
    )
    audit_log(
        "user.force_password_reset",
        current_user.username,
        f"user:{user.username}",
        must_change_password=must_change_password,
        role=current_user.role,
    )
    return user


def unlock_user_use_case(
    session: Session,
    current_user: User,
    user_id: int,
) -> User:
    user = UserService.unlock_user(session=session, user_id=user_id)
    audit_log("user.unlock", current_user.username, f"user:{user.username}", role=current_user.role)
    return user


def change_my_password_use_case(
    session: Session,
    current_user: User,
    current_password: str,
    new_password: str,
) -> UserActionResult:
    UserService.change_own_password(
        session=session,
        user_id=current_user.id,
        current_password=current_password,
        new_password=new_password,
    )
    audit_log("user.change_own_password", current_user.username, f"user:{current_user.username}", role=current_user.role)
    return UserActionResult(message="密码已更新")
