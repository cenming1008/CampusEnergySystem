"""
能源接口聚合入口
"""

from fastapi import APIRouter

from .carbon import (
    calculate_carbon_manual,
    get_carbon_emissions,
    get_carbon_factors,
    get_carbon_summary,
)
from .carbon import (
    router as carbon_router,
)
from .data import (
    get_energy_data,
    get_energy_statistics,
    get_energy_types,
    save_energy_data,
)
from .data import (
    router as data_router,
)
from .storage import (
    get_storage_comparison,
    get_storage_overview,
)
from .storage import (
    router as storage_router,
)

__all__ = [
    "calculate_carbon_manual",
    "get_carbon_emissions",
    "get_carbon_factors",
    "get_carbon_summary",
    "get_energy_data",
    "get_energy_statistics",
    "get_energy_types",
    "get_storage_comparison",
    "get_storage_overview",
    "save_energy_data",
]

router = APIRouter()
router.include_router(data_router)
router.include_router(carbon_router)
router.include_router(storage_router)
