"""
用户管理 API。
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import ADMIN_ONLY, get_current_user
from app.core.audit import audit_log
from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import User, UserRole
from app.services.user_service import UserService

router = APIRouter()


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    location_scope: Optional[str] = None
    is_active: bool
    must_change_password: bool = False
    failed_login_attempts: int = 0
    locked_until: Optional[str] = None


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field(default=UserRole.VIEWER)
    location_scope: Optional[str] = Field(default=None, description="逗号分隔的位置ID范围")
    is_active: bool = True


class UpdateUserRoleRequest(BaseModel):
    role: str


class UpdateUserStatusRequest(BaseModel):
    is_active: bool


class UpdateUserLocationScopeRequest(BaseModel):
    location_scope: Optional[str] = Field(default=None, description="逗号分隔的位置ID范围，留空表示不限制")


class ChangePasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=128)


class ForcePasswordResetRequest(BaseModel):
    must_change_password: bool = True


class ChangeOwnPasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=6, max_length=128)


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return success_response(
        data={
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
            "location_scope": current_user.location_scope,
            "is_active": current_user.is_active,
            "must_change_password": current_user.must_change_password,
            "failed_login_attempts": current_user.failed_login_attempts,
            "locked_until": current_user.locked_until.isoformat() if current_user.locked_until else None,
        }
    )


@router.put("/me/password")
def change_my_password(
    request: ChangeOwnPasswordRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    UserService.change_own_password(
        session=session,
        user_id=current_user.id,
        current_password=request.current_password,
        new_password=request.new_password,
    )
    audit_log("user.change_own_password", current_user.username, f"user:{current_user.username}")
    return success_response(message="密码已更新")


@router.get("/", response_model=List[UserResponse])
def list_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    audit_log("user.list", current_user.username, "user:*", role=current_user.role)
    return UserService.list_users(session)


@router.post("/", response_model=UserResponse)
def create_user(
    request: CreateUserRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    user = UserService.create_user(
        session=session,
        username=request.username,
        password=request.password,
        role=request.role,
        is_active=request.is_active,
        location_scope=request.location_scope,
    )
    audit_log("user.create", current_user.username, f"user:{user.username}", role=request.role)
    return user


@router.put("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    request: UpdateUserRoleRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    user = UserService.update_user_role(
        session=session,
        user_id=user_id,
        role=request.role,
        acting_user=current_user,
    )
    audit_log("user.update_role", current_user.username, f"user:{user.username}", role=request.role)
    return user


@router.put("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    request: UpdateUserStatusRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    user = UserService.set_user_active(
        session=session,
        user_id=user_id,
        is_active=request.is_active,
        acting_user=current_user,
    )
    audit_log("user.update_status", current_user.username, f"user:{user.username}", is_active=request.is_active)
    return user


@router.put("/{user_id}/scope", response_model=UserResponse)
def update_user_location_scope(
    user_id: int,
    request: UpdateUserLocationScopeRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    user = UserService.update_location_scope(
        session=session,
        user_id=user_id,
        location_scope=request.location_scope,
    )
    audit_log("user.update_scope", current_user.username, f"user:{user.username}", location_scope=request.location_scope)
    return user


@router.put("/{user_id}/password")
def change_user_password(
    user_id: int,
    request: ChangePasswordRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    user = UserService.change_password(
        session=session,
        user_id=user_id,
        new_password=request.new_password,
    )
    audit_log("user.change_password", current_user.username, f"user:{user.username}")
    return success_response(message=f"用户 {user.username} 密码已更新")


@router.post("/{user_id}/revoke-sessions")
def revoke_user_sessions(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    user = UserService.revoke_user_tokens(session=session, user_id=user_id)
    audit_log("user.revoke_sessions", current_user.username, f"user:{user.username}")
    return success_response(message=f"用户 {user.username} 已被强制下线")


@router.put("/{user_id}/force-password-reset", response_model=UserResponse)
def force_password_reset(
    user_id: int,
    request: ForcePasswordResetRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    user = UserService.set_force_password_reset(
        session=session,
        user_id=user_id,
        must_change_password=request.must_change_password,
    )
    audit_log(
        "user.force_password_reset",
        current_user.username,
        f"user:{user.username}",
        must_change_password=request.must_change_password,
    )
    return user


@router.post("/{user_id}/unlock", response_model=UserResponse)
def unlock_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    user = UserService.unlock_user(session=session, user_id=user_id)
    audit_log("user.unlock", current_user.username, f"user:{user.username}")
    return user
