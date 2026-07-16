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
    assert "Task 3" in status and "具备准入条件" in status
    assert 'revision = "20260716_0002"' in storage_plan
    assert 'down_revision = "20260716_0001"' in storage_plan
