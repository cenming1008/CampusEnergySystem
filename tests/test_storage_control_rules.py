import math

from app.domain.storage_control_rules import StorageRuleInput, decide_storage_power


def test_fault_overrides_pv_surplus_and_peak_shaving():
    decision = decide_storage_power(
        StorageRuleInput(
            load_kw=420,
            pv_kw=500,
            tariff="peak",
            soc=60,
            temperature_c=58,
            bms_state="fault",
            pcs_state="running",
            grid_connected=True,
        )
    )

    assert decision.target_power_kw == 0
    assert decision.reason_code == "safety_fault"


def test_pv_surplus_charges_before_tariff_rule():
    decision = decide_storage_power(
        StorageRuleInput(
            load_kw=100,
            pv_kw=180,
            tariff="peak",
            soc=50,
            temperature_c=30,
            bms_state="normal",
            pcs_state="running",
            grid_connected=True,
            available_charge_kw=250,
        )
    )

    assert decision.target_power_kw == 80
    assert decision.reason_code == "pv_surplus"


def test_demand_limit_discharge_is_negative():
    decision = decide_storage_power(
        StorageRuleInput(
            load_kw=420,
            pv_kw=20,
            tariff="flat",
            demand_limit_kw=300,
            soc=70,
            temperature_c=30,
            bms_state="normal",
            pcs_state="running",
            grid_connected=True,
            available_discharge_kw=250,
        )
    )

    assert decision.target_power_kw == -100
    assert decision.reason_code == "demand_limit"


def test_deadband_and_soc_hysteresis_prevent_small_or_unsafe_commands():
    deadband = decide_storage_power(
        StorageRuleInput(load_kw=100, pv_kw=103, soc=50, available_charge_kw=250)
    )
    charge_latched = decide_storage_power(
        StorageRuleInput(
            load_kw=100,
            pv_kw=180,
            soc=87,
            available_charge_kw=250,
            current_target_power_kw=0,
        )
    )
    discharge_latched = decide_storage_power(
        StorageRuleInput(
            load_kw=400,
            pv_kw=0,
            demand_limit_kw=300,
            soc=12,
            available_discharge_kw=250,
            current_target_power_kw=0,
        )
    )

    assert deadband.target_power_kw == 0
    assert deadband.reason_code == "idle_deadband"
    assert charge_latched.reason_code == "soc_charge_hysteresis"
    assert discharge_latched.reason_code == "soc_discharge_hysteresis"


def test_minimum_durations_and_direction_change_require_standby():
    keep_running = decide_storage_power(
        StorageRuleInput(
            load_kw=100,
            pv_kw=180,
            soc=50,
            available_charge_kw=250,
            current_target_power_kw=-50,
            seconds_since_last_transition=30,
            minimum_run_seconds=120,
        )
    )
    direction_stop = decide_storage_power(
        StorageRuleInput(
            load_kw=100,
            pv_kw=180,
            soc=50,
            available_charge_kw=250,
            current_target_power_kw=-50,
            seconds_since_last_transition=180,
            minimum_run_seconds=120,
        )
    )
    standby = decide_storage_power(
        StorageRuleInput(
            load_kw=100,
            pv_kw=180,
            soc=50,
            available_charge_kw=250,
            current_target_power_kw=0,
            previous_nonzero_target_power_kw=-50,
            seconds_since_last_transition=20,
            direction_change_standby_seconds=60,
        )
    )

    assert keep_running.target_power_kw == -50
    assert keep_running.reason_code == "minimum_run_duration"
    assert direction_stop.target_power_kw == 0
    assert direction_stop.reason_code == "direction_change_standby"
    assert standby.target_power_kw == 0
    assert standby.reason_code == "direction_change_standby"


def test_tariff_rule_runs_after_pv_and_demand_rules():
    peak = decide_storage_power(
        StorageRuleInput(
            load_kw=200,
            pv_kw=20,
            tariff="peak",
            soc=60,
            available_discharge_kw=80,
        )
    )
    valley = decide_storage_power(
        StorageRuleInput(
            load_kw=200,
            pv_kw=20,
            tariff="valley",
            soc=50,
            available_charge_kw=60,
        )
    )

    assert peak.target_power_kw == -80
    assert peak.reason_code == "tariff_peak"
    assert valley.target_power_kw == 60
    assert valley.reason_code == "tariff_valley"


def test_non_finite_rule_input_fails_safe():
    decision = decide_storage_power(
        StorageRuleInput(load_kw=math.nan, pv_kw=10, soc=50, available_charge_kw=100)
    )

    assert decision.target_power_kw == 0
    assert decision.reason_code == "safety_invalid_input"
