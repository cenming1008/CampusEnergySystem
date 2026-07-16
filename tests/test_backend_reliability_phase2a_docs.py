from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_phase2a_is_the_only_active_main_topic():
    status = read("docs/plans/current-status.md")
    handoff = read("docs/plans/handoff.md")
    assert "当前主主题：`后端可靠性阶段 2A：确定性迁移基线`" in status
    assert "当前主题：`后端可靠性阶段 2A：确定性迁移基线`" in handoff
    assert "园区光储协同仿真与 EMS 控制`。" not in status


def test_storage_task2_completion_is_preserved_in_daily_snapshot():
    status = read("docs/plans/daily/2026-07/2026-07-16-status.md")
    handoff = read("docs/plans/daily/2026-07/2026-07-16-handoff.md")
    assert "园区光储主题暂停快照" in status
    assert "Task 2" in status and "正式完成" in status
    assert "Task 3" in handoff and "阶段 2A" in handoff
