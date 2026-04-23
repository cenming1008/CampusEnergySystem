"""JKWF-LCD 容量编码与回路容量展开。"""

from __future__ import annotations

from typing import Optional

CAPACITY_CODE_PATTERNS = {
    0: "1111",
    1: "1222",
    2: "1244",
    3: "1248",
    4: "1233",
    5: "1236",
    6: "1122",
    7: "1124",
    8: "1128",
    9: "1123",
    10: "1126",
    11: "1881",
}


def _distribute_balanced(total: int, buckets: int, max_per_bucket: int) -> list[int]:
    total = max(0, min(total, buckets * max_per_bucket))
    if buckets <= 0:
        return []
    base = total // buckets
    remainder = total % buckets
    return [min(max_per_bucket, base + (1 if index < remainder else 0)) for index in range(buckets)]


def _distribute_sequential(total: int, bucket_sizes: tuple[int, ...]) -> list[int]:
    remaining = max(0, total)
    result: list[int] = []
    for size in bucket_sizes:
        allocated = min(size, remaining)
        result.append(allocated)
        remaining -= allocated
    return result


def resolve_capacity_pattern(capacity_code: str | int | None) -> str:
    if capacity_code is None:
        return CAPACITY_CODE_PATTERNS[0]

    if isinstance(capacity_code, int):
        return CAPACITY_CODE_PATTERNS.get(capacity_code, CAPACITY_CODE_PATTERNS[0])

    normalized = str(capacity_code).strip()
    if not normalized:
        return CAPACITY_CODE_PATTERNS[0]

    if ":" in normalized:
        _, suffix = normalized.split(":", 1)
        digits = "".join(char for char in suffix if char.isdigit())
        if digits:
            return digits

    if normalized.isdigit() and len(normalized) == 1:
        return CAPACITY_CODE_PATTERNS.get(int(normalized), CAPACITY_CODE_PATTERNS[0])

    digits = "".join(char for char in normalized if char.isdigit())
    if digits:
        return digits
    return CAPACITY_CODE_PATTERNS[0]


def expand_capacity_slots(capacity_code: str | int | None, step_kvar: float, count: int) -> list[float]:
    pattern = resolve_capacity_pattern(capacity_code)
    if count <= 0 or not pattern:
        return []
    digits = [max(1, int(char)) for char in pattern]
    slots: list[float] = []
    while len(slots) < count:
        for digit in digits:
            slots.append(round(step_kvar * digit, 4))
            if len(slots) >= count:
                break
    return slots


def build_split_phase_slot_kvar(capacity_code: str | int | None, step_kvar: float, count: int) -> dict[str, list[float]]:
    slot_values = expand_capacity_slots(capacity_code, step_kvar, count)
    phase_keys = ("phase_a_groups", "phase_b_groups", "phase_c_groups")
    phase_capacities = _distribute_balanced(count, buckets=3, max_per_bucket=8)
    phase_slots = {key: [] for key in phase_keys}
    phase_index = 0
    for slot in slot_values:
        attempts = 0
        while attempts < len(phase_keys):
            key = phase_keys[phase_index]
            if len(phase_slots[key]) < phase_capacities[phase_index]:
                phase_slots[key].append(slot)
                phase_index = (phase_index + 1) % len(phase_keys)
                break
            phase_index = (phase_index + 1) % len(phase_keys)
            attempts += 1
    return phase_slots


def build_split_phase_slot_kvar_with_layout(
    capacity_code: str | int | None,
    step_kvar: float,
    phase_counts: tuple[int, int, int],
) -> dict[str, list[float]]:
    normalized_counts = [max(0, min(int(value or 0), 8)) for value in phase_counts]
    slot_values = expand_capacity_slots(capacity_code, step_kvar, sum(normalized_counts))
    cursor = 0
    result: dict[str, list[float]] = {}
    for key, phase_count in zip(("phase_a_groups", "phase_b_groups", "phase_c_groups"), normalized_counts):
        result[key] = slot_values[cursor:cursor + phase_count]
        cursor += phase_count
    return result


def build_common_stage_slot_kvar(capacity_code: str | int | None, step_kvar: float, count: int) -> dict[str, list[float]]:
    slot_values = expand_capacity_slots(capacity_code, step_kvar, count)
    stage_keys = ("common_1_groups", "common_2_groups", "common_3_groups")
    stage_capacities = _distribute_sequential(count, (8, 8, 8))
    stage_slots: dict[str, list[float]] = {}
    cursor = 0
    for key, stage_count in zip(stage_keys, stage_capacities):
        stage_slots[key] = slot_values[cursor:cursor + stage_count]
        cursor += stage_count
    return stage_slots


def build_common_stage_slot_kvar_with_layout(
    capacity_code: str | int | None,
    step_kvar: float,
    stage_counts: tuple[int, int, int],
) -> dict[str, list[float]]:
    normalized_counts = [max(0, min(int(value or 0), 8)) for value in stage_counts]
    slot_values = expand_capacity_slots(capacity_code, step_kvar, sum(normalized_counts))
    cursor = 0
    result: dict[str, list[float]] = {}
    for key, stage_count in zip(("common_1_groups", "common_2_groups", "common_3_groups"), normalized_counts):
        result[key] = slot_values[cursor:cursor + stage_count]
        cursor += stage_count
    return result


def build_capacity_expansion(
    *,
    common_capacity_code: str | int | None,
    split_capacity_code: str | int | None,
    common_step_capacity_kvar: Optional[float],
    split_step_capacity_kvar: Optional[float],
    common_output_circuit_count: Optional[int],
    split_output_circuit_count: Optional[int],
    phase_a_circuit_total_count: Optional[int] = None,
    phase_b_circuit_total_count: Optional[int] = None,
    phase_c_circuit_total_count: Optional[int] = None,
    common_1_circuit_total_count: Optional[int] = None,
    common_2_circuit_total_count: Optional[int] = None,
    common_3_circuit_total_count: Optional[int] = None,
) -> dict[str, dict[str, list[float]]]:
    common_count = int(common_output_circuit_count or 0)
    split_count = int(split_output_circuit_count or 0)
    common_step = float(common_step_capacity_kvar or 0.0)
    split_step = float(split_step_capacity_kvar or 0.0)
    explicit_split_counts = (
        phase_a_circuit_total_count,
        phase_b_circuit_total_count,
        phase_c_circuit_total_count,
    )
    explicit_common_counts = (
        common_1_circuit_total_count,
        common_2_circuit_total_count,
        common_3_circuit_total_count,
    )
    has_explicit_split_layout = any(value is not None for value in explicit_split_counts)
    has_explicit_common_layout = any(value is not None for value in explicit_common_counts)
    return {
        "common_capacity_expansion": (
            build_common_stage_slot_kvar_with_layout(common_capacity_code, common_step, explicit_common_counts)
            if common_step > 0 and has_explicit_common_layout
            else build_common_stage_slot_kvar(common_capacity_code, common_step, common_count)
        ) if common_step > 0 and (common_count > 0 or has_explicit_common_layout) else {
            "common_1_groups": [],
            "common_2_groups": [],
            "common_3_groups": [],
        },
        "split_capacity_expansion": (
            build_split_phase_slot_kvar_with_layout(split_capacity_code, split_step, explicit_split_counts)
            if split_step > 0 and has_explicit_split_layout
            else build_split_phase_slot_kvar(split_capacity_code, split_step, split_count)
        ) if split_step > 0 and (split_count > 0 or has_explicit_split_layout) else {
            "phase_a_groups": [],
            "phase_b_groups": [],
            "phase_c_groups": [],
        },
    }
