from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_doc(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_backend_architecture_plan_declares_non_goals_and_layers():
    content = read_doc("docs/plans/PLAN-20260530-backend-architecture-layering-audit.md")

    assert "不修改公开 API 路径" in content
    assert "不移动生产代码" in content
    for layer in ["api/endpoints", "application", "services", "domain", "integrations"]:
        assert layer in content


def test_backend_architecture_inventory_contains_all_classifications():
    content = read_doc("docs/plans/backend-architecture-audit-inventory.md")

    for classification in ["`keep`", "`watch`", "`split_candidate`", "`plan_required`"]:
        assert classification in content

    for path in [
        "app/api/endpoints/energy/shared.py",
        "app/services/alarm_service.py",
        "app/services/device_service.py",
        "app/domain/alarm_rule_profiles.py",
        "app/integrations/mqtt/",
    ]:
        assert path in content


def test_backend_guidelines_include_audit_guardrails():
    content = read_doc("docs/guides/backend-guidelines.md")

    assert "后端架构审计分类" in content
    assert "第一阶段架构审计默认只产出计划、库存和护栏测试" in content
    assert "不得继续把 schema、serializer、业务 helper 混合塞入" in content
