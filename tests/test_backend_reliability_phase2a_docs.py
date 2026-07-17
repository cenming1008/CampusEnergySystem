import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_storage_is_the_only_active_main_topic_after_phase2a_acceptance():
    status = read("docs/plans/current-status.md")
    handoff = read("docs/plans/handoff.md")
    assert "当前主主题：`园区光储协同仿真与 EMS 控制`" in status
    assert "当前主题：`园区光储协同仿真与 EMS 控制`" in handoff
    assert "当前主主题：`后端可靠性阶段 2A：确定性迁移基线`" not in status
    assert "当前主题：`后端可靠性阶段 2A：确定性迁移基线`" not in handoff
    assert status.count("当前主主题：") == 1
    assert handoff.count("当前主题：") == 1


def test_storage_task2_completion_is_preserved_in_daily_snapshot():
    status = read("docs/plans/daily/2026-07/2026-07-16-status.md")
    handoff = read("docs/plans/daily/2026-07/2026-07-16-handoff.md")
    assert "园区光储主题暂停快照" in status
    assert "Task 2" in status and "正式完成" in status
    assert "Task 3" in handoff and "阶段 2A" in handoff
    assert "阶段 2A 全部验收通过" in status
    assert "阶段 2A 全部验收通过" in handoff
    assert "三路径验证、开发库重建、启动仅校验和阻断式 CI 门禁" in status
    assert "三路径验证、开发库重建、启动仅校验和阻断式 CI 门禁" in handoff


def test_phase2a_allows_only_three_exact_temporary_databases():
    plan = read("docs/plans/PLAN-20260716-backend-reliability-phase2a.md")
    status = read("docs/plans/current-status.md")
    handoff = read("docs/plans/handoff.md")
    governance = "\n".join((plan, status, handoff))

    allowed_names = {
        "ces_migration_fresh",
        "ces_migration_offline",
        "ces_migration_roundtrip",
    }
    assert (
        "迁移临时验证工具及临时验证流程中的所有破坏性操作只允许针对以下三个精确临时数据库："
        "`ces_migration_fresh`、`ces_migration_offline`、"
        "`ces_migration_roundtrip`。"
    ) in plan
    assert set(re.findall(r"`(ces_migration_[a-z0-9_]+)`", governance)) == allowed_names
    assert "任意 `ces_migration_` 前缀" not in governance
    assert "只允许针对 `ces_migration_` 前缀" not in governance
    assert "Task 8 的 `campus_energy` 重建是临时验证工具之外的独立后置动作" in plan
    assert "三条临时路径全部通过后才允许执行" in plan
    assert "\n- 所有破坏性操作只允许针对以下三个临时数据库" not in governance
    assert "\n- 所有破坏性操作只允许针对三个精确名称的临时库" not in governance
    assert "\n- 所有破坏性操作仅允许三个精确名称的临时数据库" not in governance


def test_storage_resumes_only_after_the_complete_phase2a_gate():
    plan = read("docs/plans/PLAN-20260716-backend-reliability-phase2a.md")
    status = read("docs/plans/current-status.md")
    handoff = read("docs/plans/handoff.md")

    assert "新根 revision：`20260716_0001`" in plan
    assert "后续储能 revision：`20260716_0002`" in plan
    assert "三条临时路径全部通过后才允许执行该动作" in plan
    assert "阶段 2A 全部验收通过" in plan
    assert "三路径验证、开发库重建、启动仅校验和阻断式 CI 门禁" in plan
    assert "阶段 2A 全部验收通过" in status
    assert "阶段 2A 全部验收通过" in handoff


def test_storage_resumes_only_after_phase2a_acceptance():
    status = read("docs/plans/current-status.md")
    storage_plan = read(
        "docs/superpowers/plans/2026-07-16-campus-pv-storage-simulation.md"
    )
    assert "当前主主题：`园区光储协同仿真与 EMS 控制`" in status
    assert re.search(r"(?m)^- \[x\] Task 3[:：].*完成", status)
    assert re.search(r"(?m)^- \[x\] Task 4[:：].*完成", status)
    assert re.search(r"(?m)^- \[x\] Task 5[:：].*完成", status)
    assert re.search(r"(?m)^- \[x\] Task 6[:：].*完成", status)
    assert re.search(r"(?m)^- \[x\] Task 7[:：].*完成", status)
    assert re.search(r"(?m)^- \[x\] Task 8[:：].*完成", status)
    assert re.search(r"(?m)^- \[x\] Task 9[:：].*完成", status)
    assert re.search(r"(?m)^- \[x\] Task 10[:：].*完成", status)
    assert re.search(r"(?m)^- \[x\] Task 11[:：].*完成", status)
    assert re.search(r"(?m)^- \[x\] Task 12[:：].*完成", status)
    assert re.search(r"(?m)^- \[ \] Task 13.*等待", status)
    assert 'revision = "20260716_0002"' in storage_plan
    assert 'down_revision = "20260716_0001"' in storage_plan


def test_storage_task12_is_complete_and_task13_handoff_is_ready():
    status = read("docs/plans/current-status.md")
    handoff = read("docs/plans/handoff.md")
    governance = "\n".join((status, handoff))

    assert re.search(r"(?m)^- \[x\] Task 3[:：].*完成", status)
    assert re.search(r"(?m)^- Task 3[:：]通过并正式完成", governance)
    assert re.search(r"(?m)^- \[x\] Task 4[:：].*完成", status)
    assert re.search(r"(?m)^- Task 4[:：]通过并正式完成", governance)
    assert re.search(r"(?m)^- \[x\] Task 5[:：].*完成", status)
    assert re.search(r"(?m)^- Task 5[:：]通过并正式完成", governance)
    assert re.search(r"(?m)^- \[x\] Task 6[:：].*完成", status)
    assert re.search(r"(?m)^- Task 6[:：]通过并正式完成", governance)
    assert re.search(r"(?m)^- \[x\] Task 7[:：].*完成", status)
    assert re.search(r"(?m)^- Task 7[:：]通过并正式完成", governance)
    assert re.search(r"(?m)^- \[x\] Task 8[:：].*完成", status)
    assert re.search(r"(?m)^- Task 8[:：]通过并正式完成", governance)
    assert re.search(r"(?m)^- \[x\] Task 9[:：].*完成", status)
    assert re.search(r"(?m)^- Task 9[:：]通过并正式完成", governance)
    assert re.search(r"(?m)^- \[x\] Task 10[:：].*完成", status)
    assert re.search(r"(?m)^- Task 10[:：]通过并正式完成", governance)
    assert re.search(r"(?m)^- \[x\] Task 11[:：].*完成", status)
    assert re.search(r"(?m)^- Task 11[:：]通过并正式完成", governance)
    assert re.search(r"(?m)^- \[x\] Task 12[:：].*完成", status)
    assert re.search(r"(?m)^- Task 12[:：]通过并正式完成", governance)
    assert "下一棒：后端储能 Task 13" in handoff
    assert "Task 13：已解除依赖，交后端储能角色执行" in handoff
    assert not re.search(r"(?m)^- \[x\] Task 13[:：]", governance)


def test_storage_plans_lock_the_accepted_migration_boundary():
    formal = read("docs/plans/PLAN-20260716-campus-pv-storage-simulation.md")
    detailed = read(
        "docs/superpowers/plans/2026-07-16-campus-pv-storage-simulation.md"
    )
    plans = "\n".join((formal, detailed))

    assert "./venv/bin/" not in plans
    assert "20260716_0012" not in plans
    assert "20260515_0011" not in plans
    assert "20260716_0001 -> 20260716_0002 -> 20260717_0003" in formal
    assert 'revision = "20260716_0002"' in detailed
    assert 'down_revision = "20260716_0001"' in detailed
    for plan in (formal, detailed):
        assert "基础 `storage_telemetry`" in plan
        assert "不得重建" in plan


def test_storage_task3_plan_requires_contract_red_before_implementation():
    detailed = read(
        "docs/superpowers/plans/2026-07-16-campus-pv-storage-simulation.md"
    )

    contract_red = detailed.index("Write failing migration contract tests")
    model_implementation = detailed.index("Add focused SQLModel contracts")
    migration_implementation = detailed.index("Write the deterministic migration")
    assert contract_red < model_implementation < migration_implementation
    assert "eight approved telemetry extensions" in detailed
    assert "export PATH=/Users/todo/CampusEnergySystem/venv/bin:$PATH" in detailed
    assert "export DATABASE_URL=" in detailed
    assert "export MIGRATION_ADMIN_URL=" in detailed
    assert "python scripts/python/verify_postgres_migrations.py" in detailed
    assert "--keep-success" in detailed
    assert "--cleanup" in detailed
    assert "public.energydata" in detailed
