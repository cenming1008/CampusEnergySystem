"""
用户管理服务。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session

from app.core.exceptions import ConflictException, ResourceNotFoundException, ValidationException
from app.core.security import get_password_hash, validate_password_strength, verify_password
from app.core.settings import settings
from app.models.tables import User, UserRole
from app.repositories.user_repository import UserRepository


class UserService:
    """用户管理服务。"""

    @staticmethod
    def list_users(session: Session) -> list[User]:
        return UserRepository.list_users(session)

    @staticmethod
    def get_user_by_id(session: Session, user_id: int) -> User:
        user = UserRepository.get_by_id(session, user_id)
        if not user:
            raise ResourceNotFoundException("用户", user_id)
        return user

    @staticmethod
    def create_user(
        session: Session,
        username: str,
        password: str,
        role: str,
        is_active: bool = True,
        location_scope: Optional[str] = None,
    ) -> User:
        if UserRepository.get_by_username(session, username):
            raise ConflictException(f"用户名 {username} 已存在")
        UserService._validate_role(role)
        validate_password_strength(password)

        user = User(
            username=username,
            hashed_password=get_password_hash(password),
            role=role,
            is_active=is_active,
            location_scope=location_scope,
            must_change_password=True,
            last_password_changed_at=datetime.now(),
        )
        return UserRepository.save(session, user)

    @staticmethod
    def update_user_role(
        session: Session,
        user_id: int,
        role: str,
        acting_user: User,
    ) -> User:
        user = UserService.get_user_by_id(session, user_id)
        UserService._validate_role(role)
        if user.username == acting_user.username and role != UserRole.ADMIN:
            raise ValidationException("不能移除当前管理员自己的 admin 角色")
        user.role = role
        return UserRepository.save(session, user)

    @staticmethod
    def set_user_active(
        session: Session,
        user_id: int,
        is_active: bool,
        acting_user: User,
    ) -> User:
        user = UserService.get_user_by_id(session, user_id)
        if user.username == acting_user.username and not is_active:
            raise ValidationException("不能停用当前登录用户")
        user.is_active = is_active
        return UserRepository.save(session, user)

    @staticmethod
    def change_password(
        session: Session,
        user_id: int,
        new_password: str,
        require_password_change: bool = False,
        increment_token_version: bool = True,
    ) -> User:
        user = UserService.get_user_by_id(session, user_id)
        validate_password_strength(new_password)
        user.hashed_password = get_password_hash(new_password)
        user.must_change_password = require_password_change
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_password_changed_at = datetime.now()
        if increment_token_version:
            user.token_version += 1
        return UserRepository.save(session, user)

    @staticmethod
    def update_location_scope(
        session: Session,
        user_id: int,
        location_scope: Optional[str],
    ) -> User:
        user = UserService.get_user_by_id(session, user_id)
        user.location_scope = location_scope.strip() if location_scope else None
        return UserRepository.save(session, user)

    @staticmethod
    def change_own_password(
        session: Session,
        user_id: int,
        current_password: str,
        new_password: str,
    ) -> User:
        user = UserService.get_user_by_id(session, user_id)
        if not verify_password(current_password, user.hashed_password):
            raise ValidationException("当前密码不正确")
        validate_password_strength(new_password)
        user.hashed_password = get_password_hash(new_password)
        user.must_change_password = False
        user.failed_login_attempts = 0
        user.locked_until = None
        user.token_version += 1
        user.last_password_changed_at = datetime.now()
        return UserRepository.save(session, user)

    @staticmethod
    def register_login_failure(session: Session, username: str) -> Optional[User]:
        user = UserRepository.get_by_username(session, username)
        if not user:
            return None
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= settings.auth_max_failed_attempts:
            user.locked_until = datetime.now() + timedelta(minutes=settings.auth_lock_minutes)
        return UserRepository.save(session, user)

    @staticmethod
    def register_login_success(session: Session, user: User) -> User:
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now()
        return UserRepository.save(session, user)

    @staticmethod
    def revoke_user_tokens(session: Session, user_id: int) -> User:
        user = UserService.get_user_by_id(session, user_id)
        user.token_version += 1
        return UserRepository.save(session, user)

    @staticmethod
    def rotate_refresh_session(session: Session, user_id: int) -> User:
        """轮换 refresh 会话，同时使旧 access/refresh 令牌失效。"""
        user = UserService.get_user_by_id(session, user_id)
        user.token_version += 1
        user.last_login_at = datetime.now()
        return UserRepository.save(session, user)

    @staticmethod
    def set_force_password_reset(
        session: Session,
        user_id: int,
        must_change_password: bool,
    ) -> User:
        user = UserService.get_user_by_id(session, user_id)
        user.must_change_password = must_change_password
        return UserRepository.save(session, user)

    @staticmethod
    def unlock_user(session: Session, user_id: int) -> User:
        user = UserService.get_user_by_id(session, user_id)
        user.failed_login_attempts = 0
        user.locked_until = None
        return UserRepository.save(session, user)

    @staticmethod
    def _validate_role(role: str) -> None:
        valid_roles = {item.value for item in UserRole}
        if role not in valid_roles:
            raise ValidationException(f"无效角色: {role}。有效值: {', '.join(sorted(valid_roles))}")
