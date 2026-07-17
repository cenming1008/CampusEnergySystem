from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DETAILED_PLAN = ROOT / "docs/superpowers/plans/2026-07-16-campus-pv-storage-simulation.md"
FORMAL_PLAN = ROOT / "docs/plans/PLAN-20260716-campus-pv-storage-simulation.md"
STATUS = ROOT / "docs/plans/current-status.md"
HANDOFF = ROOT / "docs/plans/handoff.md"
CONVERGENCE_SPEC = "docs/superpowers/specs/2026-07-17-single-storage-system-convergence-design.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_all_active_storage_plans_reference_the_single_system_spec():
    for path in (DETAILED_PLAN, FORMAL_PLAN, STATUS, HANDOFF):
        assert CONVERGENCE_SPEC in read(path)


def test_detailed_plan_reuses_existing_pages_instead_of_creating_parallel_routes():
    plan = read(DETAILED_PLAN)

    assert "frontend/src/views/StorageEnergy.vue" not in plan
    assert "frontend/src/router/__tests__/storageEnergyRoute.test.ts" not in plan
    assert "Add `/storage-energy`" not in plan
    assert "frontend/src/views/EnergyManagement.vue" in plan
    assert "frontend/src/features/energy-management/storage-ems/StorageEmsWorkspace.vue" in plan
    assert "现有“能耗分析”页面" in plan


def test_detailed_plan_preserves_completed_work_and_adds_cutover_acceptance():
    plan = read(DETAILED_PLAN)

    for task_number in range(1, 6):
        task_start = plan.index(f"## Task {task_number}:")
        next_task = plan.index(f"## Task {task_number + 1}:")
        task = plan[task_start:next_task]
        assert "- [ ]" not in task

    assert "## Task 6:" in plan
    task6_start = plan.index("## Task 6:")
    task7_start = plan.index("## Task 7:")
    assert "- [ ]" not in plan[task6_start:task7_start]
    task8_start = plan.index("## Task 8:")
    assert "- [ ]" not in plan[task7_start:task8_start]
    task9_start = plan.index("## Task 9:")
    assert "- [ ]" not in plan[task8_start:task9_start]
    task10_start = plan.index("## Task 10:")
    assert "- [ ]" not in plan[task9_start:task10_start]
    task11_start = plan.index("## Task 11:")
    assert "- [ ]" not in plan[task10_start:task11_start]
    task12_start = plan.index("## Task 12:")
    assert "- [ ]" not in plan[task11_start:task12_start]
    task13_start = plan.index("## Task 13:")
    assert "- [ ]" not in plan[task12_start:task13_start]
    task14_start = plan.index("## Task 14:")
    assert "- [ ]" not in plan[task13_start:task14_start]
    task15_start = plan.index("## Task 15:")
    assert "- [ ]" not in plan[task14_start:task15_start]
    assert "simulation_cutover_service.py" in plan
    assert "storage_cutover.py" in plan
    assert "tests/test_storage_simulation_cutover.py" in plan
    assert "ems_auto_enabled" in plan
    assert "simulation_run_id" in plan


def test_status_and_handoff_keep_task15_field_acceptance_as_the_only_next_storage_task():
    status = read(STATUS)
    handoff = read(HANDOFF)

    assert "Task 5：通过并正式完成" in status
    assert "Task 6：通过并正式完成" in status
    assert "Task 7：通过并正式完成" in status
    assert "Task 8：通过并正式完成" in status
    assert "Task 9：通过并正式完成" in status
    assert "Task 10：通过并正式完成" in status
    assert "Task 11：通过并正式完成" in status
    assert "Task 12：通过并正式完成" in status
    assert "Task 13：通过并正式完成" in status
    assert "Task 14：通过并正式完成" in status
    assert "Task 15：代码与离线验收完成；现场验收待执行" in status
    assert "下一棒：现场验收 Task 15" in handoff
    assert "下一棒：前端 Task 14" not in handoff
    assert "下一棒：后端储能 Task 13" not in handoff
    assert "下一棒：后端储能 Task 12" not in handoff
    assert "下一棒：后端储能 Task 11" not in handoff
    assert "下一棒：前端 Task 10" not in handoff
    assert "下一棒：后端储能 Task 9" not in handoff
