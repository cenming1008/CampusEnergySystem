"""
用户数据访问。
"""

from __future__ import annotations

from typing import Optional

from sqlmodel import Session, select

from app.models.tables import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """用户仓储。"""

    @staticmethod
    def get_by_id(session: Session, user_id: int) -> Optional[User]:
        return session.get(User, user_id)

    @staticmethod
    def get_by_username(session: Session, username: str) -> Optional[User]:
        return session.exec(select(User).where(User.username == username)).first()

    @staticmethod
    def list_users(session: Session) -> list[User]:
        statement = select(User).order_by(User.id)
        return list(session.exec(statement).all())

    @staticmethod
    def save(session: Session, user: User) -> User:
        return UserRepository.save_model(session, user)
