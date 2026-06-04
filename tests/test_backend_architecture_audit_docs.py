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


def test_app_readme_describes_current_endpoint_layout():
    content = read_doc("app/README.md")

    assert "`ingestion_health.py` | 设备接入健康" in content
    assert "`health.py` | 单设备与概览维度的 MQTT 接入健康状态。" not in content
    assert "`schemas.py` | 能源与碳相关请求/响应模型。" in content
    assert "`constants.py` | 能源与碳相关常量。" in content
    assert "`serializers.py` | 能源与碳相关轻量转换函数。" in content
    assert "`shared.py` | 能源与碳相关请求/响应模型及字段提取工具。" not in content


def test_backend_architecture_inventory_records_latest_compensation_svg_payload_slice():
    content = read_doc("docs/plans/backend-architecture-audit-inventory.md")

    assert "SVG payload metric 来源判断" in content
    assert "build_svg_monitor_payload_parts" in content
