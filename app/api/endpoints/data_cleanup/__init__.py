"""
数据清理接口聚合入口
"""

from fastapi import APIRouter

from .admin import (
    cleanup_all_data,
    get_cleanup_stats,
    router as admin_router,
)
from .basic import cleanup_data, test_cleanup_endpoint, router as basic_router

router = APIRouter()
router.include_router(basic_router)
router.include_router(admin_router)
