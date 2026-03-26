"""
仓储层公共能力。
"""

from __future__ import annotations

from typing import TypeVar

from sqlmodel import Session


ModelT = TypeVar("ModelT")


class BaseRepository:
    """为各仓储提供统一的持久化辅助方法。"""

    @staticmethod
    def save_model(session: Session, model: ModelT, *, commit: bool = True) -> ModelT:
        session.add(model)
        if commit:
            session.commit()
            session.refresh(model)
        else:
            session.flush()
        return model

    @staticmethod
    def delete_model(session: Session, model: ModelT, *, commit: bool = True) -> None:
        session.delete(model)
        if commit:
            session.commit()
        else:
            session.flush()
