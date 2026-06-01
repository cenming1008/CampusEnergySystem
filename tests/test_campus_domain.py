from dataclasses import dataclass

from app.domain.campus_rules import build_energy_category_summary


@dataclass
class Summary:
    energy_type: str
    total_consumption: float
    load_sum: float
    load_count: int


def test_build_energy_category_summary_sorts_and_preserves_response_shape():
    summaries = [
        Summary("water", 12.3456, 3.0, 0),
        Summary("electricity", 30.1111, 15.0, 3),
        Summary("electricity", 5.0, 2.0, 1),
    ]

    result = build_energy_category_summary(summaries)

    assert result == [
        {
            "energy_category": "electricity",
            "label": "电",
            "total_consumption": 35.111,
            "avg_load": 4.25,
            "ratio": 0.7453,
            "estimated_carbon": 27.562,
        },
        {
            "energy_category": "water",
            "label": "水",
            "total_consumption": 12.346,
            "avg_load": 3.0,
            "ratio": 0.2547,
            "estimated_carbon": 0.0,
        },
    ]
