"""
能源接口聚合入口
"""

from fastapi import APIRouter

from .carbon import (
    calculate_carbon_manual,
    get_carbon_emissions,
    get_carbon_factors,
    get_carbon_summary,
    router as carbon_router,
)
from .data import (
    get_energy_data,
    get_energy_statistics,
    get_energy_types,
    save_energy_data,
    router as data_router,
)

router = APIRouter()
router.include_router(data_router)
router.include_router(carbon_router)
