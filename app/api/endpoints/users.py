"""
用户管理 API。
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import ADMIN_ONLY, get_current_user
from app.application.users import (
    change_my_password_use_case,
    change_user_password_use_case,
    create_user_use_case,
    list_users_use_case,
    revoke_user_sessions_use_case,
    set_force_password_reset_use_case,
    unlock_user_use_case,
    update_user_location_scope_use_case,
    update_user_role_use_case,
    update_user_status_use_case,
)
from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import User, UserRole

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
    result = change_my_password_use_case(
        session=session,
        current_user=current_user,
        current_password=request.current_password,
        new_password=request.new_password,
    )
    return success_response(message=result.message)


@router.get("/", response_model=List[UserResponse])
def list_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    return list_users_use_case(session, current_user)


@router.post("/", response_model=UserResponse)
def create_user(
    request: CreateUserRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    return create_user_use_case(
        session=session,
        current_user=current_user,
        username=request.username,
        password=request.password,
        role=request.role,
        is_active=request.is_active,
        location_scope=request.location_scope,
    )


@router.put("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    request: UpdateUserRoleRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    return update_user_role_use_case(session, current_user, user_id, request.role)


@router.put("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    request: UpdateUserStatusRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    return update_user_status_use_case(session, current_user, user_id, request.is_active)


@router.put("/{user_id}/scope", response_model=UserResponse)
def update_user_location_scope(
    user_id: int,
    request: UpdateUserLocationScopeRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    return update_user_location_scope_use_case(session, current_user, user_id, request.location_scope)


@router.put("/{user_id}/password")
def change_user_password(
    user_id: int,
    request: ChangePasswordRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    result = change_user_password_use_case(
        session=session,
        current_user=current_user,
        user_id=user_id,
        new_password=request.new_password,
    )
    return success_response(message=result.message)


@router.post("/{user_id}/revoke-sessions")
def revoke_user_sessions(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    result = revoke_user_sessions_use_case(session, current_user, user_id)
    return success_response(message=result.message)


@router.put("/{user_id}/force-password-reset", response_model=UserResponse)
def force_password_reset(
    user_id: int,
    request: ForcePasswordResetRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    return set_force_password_reset_use_case(
        session,
        current_user,
        user_id,
        request.must_change_password,
    )


@router.post("/{user_id}/unlock", response_model=UserResponse)
def unlock_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    return unlock_user_use_case(session, current_user, user_id)
