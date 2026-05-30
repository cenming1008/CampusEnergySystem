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
