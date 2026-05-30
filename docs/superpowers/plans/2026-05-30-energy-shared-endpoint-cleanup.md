# Energy Shared Endpoint Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the energy endpoint `shared.py` catch-all into explicit schemas, constants, and serializer/helper modules without changing public API behavior.

**Architecture:** Keep the `app/api/endpoints/energy/` router structure unchanged. Move Pydantic request/response models to `schemas.py`, catalog constants to `constants.py`, and the optional-field extraction helper to `serializers.py`; then update `data.py` and `carbon.py` imports. Keep `shared.py` as a temporary compatibility shim only if needed by external imports, but ensure endpoint modules no longer import from it.

**Tech Stack:** Python, FastAPI, Pydantic, pytest, existing CampusEnergySystem backend endpoint tests.

---

### Task 1: Add Boundary Test For Energy Shared Cleanup

**Files:**
- Create: `tests/test_energy_endpoint_layering.py`

- [ ] **Step 1: Write the failing boundary test**

Create `tests/test_energy_endpoint_layering.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_source(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_energy_endpoint_modules_do_not_import_shared_catch_all():
    for relative_path in [
        "app/api/endpoints/energy/data.py",
        "app/api/endpoints/energy/carbon.py",
    ]:
        source = read_source(relative_path)
        assert "from .shared import" not in source


def test_energy_explicit_layer_modules_exist():
    for relative_path in [
        "app/api/endpoints/energy/schemas.py",
        "app/api/endpoints/energy/constants.py",
        "app/api/endpoints/energy/serializers.py",
    ]:
        assert (ROOT / relative_path).exists()
```

- [ ] **Step 2: Run the new test to verify RED**

Run:

```bash
./venv/bin/python -m pytest tests/test_energy_endpoint_layering.py -q
```

Expected: fail because `data.py` and `carbon.py` still import from `.shared`, and the new explicit module files do not exist yet.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_energy_endpoint_layering.py
git commit -m "test: capture energy endpoint shared boundary"
```

### Task 2: Split Energy Shared Module Into Explicit Modules

**Files:**
- Create: `app/api/endpoints/energy/schemas.py`
- Create: `app/api/endpoints/energy/constants.py`
- Create: `app/api/endpoints/energy/serializers.py`
- Modify: `app/api/endpoints/energy/shared.py`
- Modify: `app/api/endpoints/energy/data.py`
- Modify: `app/api/endpoints/energy/carbon.py`
- Test: `tests/test_energy_endpoint_layering.py`

- [ ] **Step 1: Create schemas.py**

Create `app/api/endpoints/energy/schemas.py`:

```python
"""
能源接口请求与响应模型
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EnergyDataCreate(BaseModel):
    """能源数据创建模型"""

    device_id: int
    energy_type: str
    consumption: float
    flow_rate: Optional[float] = None
    timestamp: Optional[datetime] = None
    voltage: Optional[float] = None
    current: Optional[float] = None
    power_factor: Optional[float] = None
    reactive_power: Optional[float] = None
    pressure: Optional[float] = None
    temperature: Optional[float] = None
    supply_temp: Optional[float] = None
    return_temp: Optional[float] = None
    heat_flow: Optional[float] = None


class CarbonSummaryResponse(BaseModel):
    """碳排放汇总响应"""

    total_carbon: float
    by_energy_type: dict
    boundary: Optional[str] = None
    calculation_method: Optional[str] = None
    is_accounting_grade: Optional[bool] = None
    note: Optional[str] = None
    summary_basis: Optional[str] = None


class EnergyStatisticsResponse(BaseModel):
    """能源统计响应"""

    total_consumption: float
    avg_consumption: float
    avg_flow_rate: float
    peak_flow_rate: float
    data_count: int
    consumption_unit: Optional[str] = None
    flow_unit: Optional[str] = None
    consumption_semantics: Optional[str] = None
    consumption_stat_basis: Optional[str] = None
    flow_semantics: Optional[str] = None
    flow_stat_basis: Optional[str] = None
    meter_reset_suspected: Optional[bool] = None
    data_object_kind: Optional[str] = None
    point_kind: Optional[str] = None
    public_fields: Optional[list[str]] = None
    specialized_fields: Optional[list[str]] = None
    null_field_rule: Optional[str] = None


class EnergyOverviewResponse(BaseModel):
    """多能源管理聚合响应。"""

    statistics: dict
    carbon_summary: CarbonSummaryResponse
    overview_boundary: Optional[str] = None
    unit_rule: Optional[str] = None
    cross_energy_mix_allowed: Optional[bool] = None
    field_boundary_rule: Optional[str] = None
    energy_profiles: Optional[dict] = None
    # 合并自原 /analysis/overview 的分析字段；当 include_analysis=False 时为 None
    time_window: Optional[dict] = None
    scope: Optional[dict] = None
    summary: Optional[dict] = None
    trend: Optional[dict] = None
    comparison: Optional[dict] = None
    ranking: Optional[dict] = None
    anomaly: Optional[dict] = None
    insights: Optional[list] = None
```

- [ ] **Step 2: Create constants.py**

Create `app/api/endpoints/energy/constants.py`:

```python
"""
能源接口常量
"""

ENERGY_TYPE_OPTIONS = [
    {"value": "electricity", "label": "电力", "unit": "kWh", "flow_unit": "kW"},
    {"value": "water", "label": "水", "unit": "m³", "flow_unit": "m³/h"},
    {"value": "gas", "label": "燃气", "unit": "m³", "flow_unit": "m³/h"},
    {"value": "heat", "label": "热力", "unit": "GJ", "flow_unit": "GJ/h"},
    {"value": "cooling", "label": "冷气", "unit": "kWh", "flow_unit": "kW"},
    {"value": "steam", "label": "蒸汽", "unit": "t", "flow_unit": "t/h"},
]


ENERGY_DATA_OPTIONAL_FIELDS = (
    "voltage",
    "current",
    "power_factor",
    "reactive_power",
    "pressure",
    "temperature",
    "supply_temp",
    "return_temp",
    "heat_flow",
)
```

- [ ] **Step 3: Create serializers.py**

Create `app/api/endpoints/energy/serializers.py`:

```python
"""
能源接口轻量转换函数
"""

from __future__ import annotations

from .constants import ENERGY_DATA_OPTIONAL_FIELDS
from .schemas import EnergyDataCreate


def extract_optional_energy_fields(data: EnergyDataCreate) -> dict:
    return {
        field: value
        for field in ENERGY_DATA_OPTIONAL_FIELDS
        if (value := getattr(data, field)) is not None
    }
```

- [ ] **Step 4: Replace shared.py with compatibility exports**

Replace `app/api/endpoints/energy/shared.py` with:

```python
"""
能源接口兼容导出

新代码应优先从 schemas.py、constants.py 或 serializers.py 导入。
"""

from __future__ import annotations

from .constants import ENERGY_DATA_OPTIONAL_FIELDS, ENERGY_TYPE_OPTIONS
from .schemas import (
    CarbonSummaryResponse,
    EnergyDataCreate,
    EnergyOverviewResponse,
    EnergyStatisticsResponse,
)
from .serializers import extract_optional_energy_fields

__all__ = [
    "CarbonSummaryResponse",
    "ENERGY_DATA_OPTIONAL_FIELDS",
    "ENERGY_TYPE_OPTIONS",
    "EnergyDataCreate",
    "EnergyOverviewResponse",
    "EnergyStatisticsResponse",
    "extract_optional_energy_fields",
]
```

- [ ] **Step 5: Update data.py imports**

In `app/api/endpoints/energy/data.py`, replace:

```python
from .shared import (
    ENERGY_TYPE_OPTIONS,
    EnergyDataCreate,
    EnergyOverviewResponse,
    EnergyStatisticsResponse,
    extract_optional_energy_fields,
)
```

with:

```python
from .constants import ENERGY_TYPE_OPTIONS
from .schemas import EnergyDataCreate, EnergyOverviewResponse, EnergyStatisticsResponse
from .serializers import extract_optional_energy_fields
```

- [ ] **Step 6: Update carbon.py imports**

In `app/api/endpoints/energy/carbon.py`, replace:

```python
from .shared import CarbonSummaryResponse
```

with:

```python
from .schemas import CarbonSummaryResponse
```

- [ ] **Step 7: Run the new boundary test to verify GREEN**

Run:

```bash
./venv/bin/python -m pytest tests/test_energy_endpoint_layering.py -q
```

Expected: pass with `2 passed`.

- [ ] **Step 8: Run energy endpoint regression tests**

Run:

```bash
./venv/bin/python -m pytest tests/test_energy_endpoint_semantics.py tests/test_endpoint_application_convergence.py tests/test_energy_service_round2.py -q
```

Expected: pass. Existing urllib3/LibreSSL warnings are acceptable if all tests pass.

- [ ] **Step 9: Commit the split**

```bash
git add app/api/endpoints/energy/schemas.py app/api/endpoints/energy/constants.py app/api/endpoints/energy/serializers.py app/api/endpoints/energy/shared.py app/api/endpoints/energy/data.py app/api/endpoints/energy/carbon.py
git commit -m "refactor: split energy endpoint shared module"
```

### Task 3: Update Audit Status For Energy Shared Cleanup

**Files:**
- Modify: `docs/plans/backend-architecture-audit-inventory.md`
- Modify: `docs/plans/current-status.md`
- Modify: `docs/plans/handoff.md`

- [ ] **Step 1: Update audit inventory classification**

In `docs/plans/backend-architecture-audit-inventory.md`, change the `app/api/endpoints/energy/shared.py` row from:

```markdown
| `app/api/endpoints/energy/shared.py` | `split_candidate` | `shared.py` 名称容易继续吸收 schema、serializer 和 helper | `energy/schemas.py`、`energy/serializers.py` 或局部 helper | 后续第一轮 endpoint cleanup 优先审计 |
```

to:

```markdown
| `app/api/endpoints/energy/shared.py` | `keep` | 已拆为 `schemas.py`、`constants.py`、`serializers.py`，`shared.py` 仅保留兼容导出 | 新代码直接导入明确模块 | 后续不再向 `shared.py` 添加新职责 |
```

- [ ] **Step 2: Update current-status.md**

In `docs/plans/current-status.md`, add these checklist items under `## 当前阶段`:

```markdown
- [x] 第一轮低风险 endpoint cleanup 已选择 `app/api/endpoints/energy/shared.py`。
- [x] `energy/shared.py` 已拆分为 `schemas.py`、`constants.py`、`serializers.py`，并保留兼容导出。
- [x] 能源 endpoint 已改为直接从明确模块导入，不再从 `.shared` 导入。
```

Replace `## 当前验证结论` with:

```markdown
## 当前验证结论
- `./venv/bin/python -m pytest tests/test_backend_architecture_audit_docs.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_endpoint_application_convergence.py tests/test_layer_exports.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_energy_endpoint_layering.py -q` 通过。
- `./venv/bin/python -m pytest tests/test_energy_endpoint_semantics.py tests/test_endpoint_application_convergence.py tests/test_energy_service_round2.py -q` 通过。
```

- [ ] **Step 3: Update handoff.md**

In `docs/plans/handoff.md`, add this bullet under `## 阶段结论`:

```markdown
- 第一轮低风险 endpoint cleanup 已完成：`energy/shared.py` 拆为 `schemas.py`、`constants.py`、`serializers.py`，endpoint 新代码不再从 `.shared` 导入。
```

In `## 剩余风险`, replace the `energy/shared.py` risk with:

```markdown
- `energy/shared.py` 仅作为兼容导出保留；后续新增能源 endpoint 契约、常量或转换函数应直接进入明确模块。
```

- [ ] **Step 4: Run documentation marker check**

Run:

```bash
rg -n "energy/shared.py|schemas.py|constants.py|serializers.py|test_energy_endpoint_layering" docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md
```

Expected: inventory, current status, and handoff all mention the energy shared cleanup and the new modules.

- [ ] **Step 5: Commit documentation updates**

```bash
git add docs/plans/backend-architecture-audit-inventory.md docs/plans/current-status.md docs/plans/handoff.md
git commit -m "docs: record energy shared cleanup"
```

### Task 4: Final Verification

**Files:**
- No file changes expected unless verification reveals a problem.

- [ ] **Step 1: Run the full planned check**

Run:

```bash
./venv/bin/python -m pytest tests/test_energy_endpoint_layering.py tests/test_energy_endpoint_semantics.py tests/test_endpoint_application_convergence.py tests/test_energy_service_round2.py tests/test_backend_architecture_audit_docs.py -q
```

Expected: all tests pass. Existing urllib3/LibreSSL warnings are acceptable if all tests pass.

- [ ] **Step 2: Check imports no longer use shared in endpoint modules**

Run:

```bash
rg -n "from \\.shared import" app/api/endpoints/energy/data.py app/api/endpoints/energy/carbon.py
```

Expected: no output and exit code 1 because neither endpoint module imports `.shared`.

- [ ] **Step 3: Check git status**

Run:

```bash
git status --short
```

Expected: only unrelated pre-existing untracked files remain. In the current workspace, `.understand-anything/` may remain untracked and should not be touched unless the user explicitly asks.
