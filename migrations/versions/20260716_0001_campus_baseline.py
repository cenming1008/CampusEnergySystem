"""campus deterministic baseline

Revision ID: 20260716_0001
Revises:
Create Date: 2026-07-16 12:59:07.343734
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260716_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
    op.create_table(
        "audit_event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("target", sa.String(), nullable=False),
        sa.Column("outcome", sa.String(), nullable=False),
        sa.Column("actor_role", sa.String(), nullable=True),
        sa.Column("details", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_event_action"), "audit_event", ["action"], unique=False)
    op.create_index(op.f("ix_audit_event_actor"), "audit_event", ["actor"], unique=False)
    op.create_index(op.f("ix_audit_event_actor_role"), "audit_event", ["actor_role"], unique=False)
    op.create_index(op.f("ix_audit_event_created_at"), "audit_event", ["created_at"], unique=False)
    op.create_index(op.f("ix_audit_event_outcome"), "audit_event", ["outcome"], unique=False)
    op.create_index(op.f("ix_audit_event_target"), "audit_event", ["target"], unique=False)
    op.create_table(
        "device_group",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("group_type", sa.String(), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("manager", sa.String(), nullable=True),
        sa.Column("contact", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["device_group.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_device_group_code"), "device_group", ["code"], unique=True)
    op.create_index(
        op.f("ix_device_group_group_type"), "device_group", ["group_type"], unique=False
    )
    op.create_index(op.f("ix_device_group_name"), "device_group", ["name"], unique=False)
    op.create_table(
        "inspection_route",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("estimated_duration", sa.Integer(), nullable=True),
        sa.Column("device_count", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_inspection_route_name"), "inspection_route", ["name"], unique=False)
    op.create_table(
        "location",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("location_type", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("full_path", sa.String(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("area_sqm", sa.Float(), nullable=True),
        sa.Column("manager", sa.String(), nullable=True),
        sa.Column("contact", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["location.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_location_code"), "location", ["code"], unique=True)
    op.create_index(op.f("ix_location_full_path"), "location", ["full_path"], unique=False)
    op.create_index(op.f("ix_location_location_type"), "location", ["location_type"], unique=False)
    op.create_index(op.f("ix_location_name"), "location", ["name"], unique=False)
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("location_scope", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), nullable=False),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("token_version", sa.Integer(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("last_password_changed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_last_login_at"), "user", ["last_login_at"], unique=False)
    op.create_index(op.f("ix_user_locked_until"), "user", ["locked_until"], unique=False)
    op.create_index(op.f("ix_user_role"), "user", ["role"], unique=False)
    op.create_index(op.f("ix_user_username"), "user", ["username"], unique=True)
    op.create_table(
        "device",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("sn", sa.String(), nullable=False),
        sa.Column("device_type", sa.String(), nullable=False),
        sa.Column("device_subtype", sa.String(), nullable=True),
        sa.Column("device_category", sa.String(), nullable=False),
        sa.Column("energy_type", sa.String(), nullable=False),
        sa.Column("archive_status", sa.String(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("rated_capacity", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["location.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_device_archive_status"), "device", ["archive_status"], unique=False)
    op.create_index(op.f("ix_device_device_category"), "device", ["device_category"], unique=False)
    op.create_index(op.f("ix_device_device_subtype"), "device", ["device_subtype"], unique=False)
    op.create_index(op.f("ix_device_device_type"), "device", ["device_type"], unique=False)
    op.create_index(op.f("ix_device_energy_type"), "device", ["energy_type"], unique=False)
    op.create_index(op.f("ix_device_location_id"), "device", ["location_id"], unique=False)
    op.create_index(op.f("ix_device_name"), "device", ["name"], unique=False)
    op.create_index(op.f("ix_device_sn"), "device", ["sn"], unique=True)
    op.create_table(
        "inspection_plan",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("route_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("plan_type", sa.String(), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("execution_time", sa.String(), nullable=True),
        sa.Column("schedule_config", sa.String(), nullable=True),
        sa.Column("assigned_to", sa.String(), nullable=True),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["route_id"],
            ["inspection_route.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_inspection_plan_route_id"), "inspection_plan", ["route_id"], unique=False
    )
    op.create_table(
        "alarm",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("instance_key", sa.String(), nullable=True),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("recovered_at", sa.DateTime(), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by", sa.String(), nullable=True),
        sa.Column("handling_note", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alarm_category"), "alarm", ["category"], unique=False)
    op.create_index(op.f("ix_alarm_device_id"), "alarm", ["device_id"], unique=False)
    op.create_index(op.f("ix_alarm_instance_key"), "alarm", ["instance_key"], unique=False)
    op.create_index(op.f("ix_alarm_last_seen_at"), "alarm", ["last_seen_at"], unique=False)
    op.create_index(op.f("ix_alarm_recovered_at"), "alarm", ["recovered_at"], unique=False)
    op.create_index(op.f("ix_alarm_resolved_at"), "alarm", ["resolved_at"], unique=False)
    op.create_index(op.f("ix_alarm_severity"), "alarm", ["severity"], unique=False)
    op.create_index(op.f("ix_alarm_timestamp"), "alarm", ["timestamp"], unique=False)
    op.create_table(
        "capacitor_bank_control_profile",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("switch_on_power_factor", sa.Float(), nullable=True),
        sa.Column("switch_off_power_factor", sa.Float(), nullable=True),
        sa.Column("switch_on_delay_seconds", sa.Integer(), nullable=True),
        sa.Column("switch_off_delay_seconds", sa.Integer(), nullable=True),
        sa.Column("common_output_circuit_count", sa.Integer(), nullable=True),
        sa.Column("split_output_circuit_count", sa.Integer(), nullable=True),
        sa.Column("phase_a_circuit_total_count", sa.Integer(), nullable=True),
        sa.Column("phase_b_circuit_total_count", sa.Integer(), nullable=True),
        sa.Column("phase_c_circuit_total_count", sa.Integer(), nullable=True),
        sa.Column("common_1_circuit_total_count", sa.Integer(), nullable=True),
        sa.Column("common_2_circuit_total_count", sa.Integer(), nullable=True),
        sa.Column("common_3_circuit_total_count", sa.Integer(), nullable=True),
        sa.Column("phase_a_capacity_steps_kvar_json", sa.String(), nullable=True),
        sa.Column("phase_b_capacity_steps_kvar_json", sa.String(), nullable=True),
        sa.Column("phase_c_capacity_steps_kvar_json", sa.String(), nullable=True),
        sa.Column("common_1_capacity_steps_kvar_json", sa.String(), nullable=True),
        sa.Column("common_2_capacity_steps_kvar_json", sa.String(), nullable=True),
        sa.Column("common_3_capacity_steps_kvar_json", sa.String(), nullable=True),
        sa.Column("phase_a_circuit_running_count", sa.Integer(), nullable=True),
        sa.Column("phase_b_circuit_running_count", sa.Integer(), nullable=True),
        sa.Column("phase_c_circuit_running_count", sa.Integer(), nullable=True),
        sa.Column("common_group_1_running_count", sa.Integer(), nullable=True),
        sa.Column("common_group_2_running_count", sa.Integer(), nullable=True),
        sa.Column("common_group_3_running_count", sa.Integer(), nullable=True),
        sa.Column("split_circuit_running_count", sa.Integer(), nullable=True),
        sa.Column("common_circuit_running_count", sa.Integer(), nullable=True),
        sa.Column("running_circuit_count", sa.Integer(), nullable=True),
        sa.Column("control_mode", sa.String(), nullable=True),
        sa.Column("auto_on_elapsed_seconds", sa.Integer(), nullable=True),
        sa.Column("auto_off_elapsed_seconds", sa.Integer(), nullable=True),
        sa.Column("last_auto_action", sa.String(), nullable=True),
        sa.Column("common_capacity_code", sa.String(), nullable=True),
        sa.Column("split_capacity_code", sa.String(), nullable=True),
        sa.Column("common_step_capacity_kvar", sa.Float(), nullable=True),
        sa.Column("split_step_capacity_kvar", sa.Float(), nullable=True),
        sa.Column("ct_primary_current", sa.Integer(), nullable=True),
        sa.Column("overvoltage_threshold", sa.Float(), nullable=True),
        sa.Column("voltage_harmonic_threshold", sa.Float(), nullable=True),
        sa.Column("current_harmonic_threshold", sa.Float(), nullable=True),
        sa.Column("temperature_upper_limit", sa.Float(), nullable=True),
        sa.Column("alarm_drive_event", sa.String(), nullable=True),
        sa.Column("baud_rate", sa.Integer(), nullable=True),
        sa.Column("terminal_assignment_scheme", sa.String(), nullable=True),
        sa.Column("current_polarity_identification_enabled", sa.Boolean(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("snapshot_timestamp", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_capacitor_bank_control_profile_device_id"),
        "capacitor_bank_control_profile",
        ["device_id"],
        unique=True,
    )
    op.create_table(
        "capacitor_bank_telemetry",
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("voltage_a", sa.Float(), nullable=True),
        sa.Column("voltage_b", sa.Float(), nullable=True),
        sa.Column("voltage_c", sa.Float(), nullable=True),
        sa.Column("current_a", sa.Float(), nullable=True),
        sa.Column("current_b", sa.Float(), nullable=True),
        sa.Column("current_c", sa.Float(), nullable=True),
        sa.Column("power_factor_a", sa.Float(), nullable=True),
        sa.Column("power_factor_b", sa.Float(), nullable=True),
        sa.Column("power_factor_c", sa.Float(), nullable=True),
        sa.Column("active_power_a", sa.Float(), nullable=True),
        sa.Column("active_power_b", sa.Float(), nullable=True),
        sa.Column("active_power_c", sa.Float(), nullable=True),
        sa.Column("reactive_power_a", sa.Float(), nullable=True),
        sa.Column("reactive_power_b", sa.Float(), nullable=True),
        sa.Column("reactive_power_c", sa.Float(), nullable=True),
        sa.Column("apparent_power_a", sa.Float(), nullable=True),
        sa.Column("apparent_power_b", sa.Float(), nullable=True),
        sa.Column("apparent_power_c", sa.Float(), nullable=True),
        sa.Column("voltage_thd_a", sa.Float(), nullable=True),
        sa.Column("voltage_thd_b", sa.Float(), nullable=True),
        sa.Column("voltage_thd_c", sa.Float(), nullable=True),
        sa.Column("current_harmonic_a", sa.Float(), nullable=True),
        sa.Column("current_harmonic_b", sa.Float(), nullable=True),
        sa.Column("current_harmonic_c", sa.Float(), nullable=True),
        sa.Column("voltage_harmonics_a", sa.JSON(), nullable=True),
        sa.Column("voltage_harmonics_b", sa.JSON(), nullable=True),
        sa.Column("voltage_harmonics_c", sa.JSON(), nullable=True),
        sa.Column("current_harmonics_a", sa.JSON(), nullable=True),
        sa.Column("current_harmonics_b", sa.JSON(), nullable=True),
        sa.Column("current_harmonics_c", sa.JSON(), nullable=True),
        sa.Column("frequency", sa.Float(), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("leading_a", sa.Boolean(), nullable=True),
        sa.Column("leading_b", sa.Boolean(), nullable=True),
        sa.Column("leading_c", sa.Boolean(), nullable=True),
        sa.Column("undercurrent_a", sa.Boolean(), nullable=True),
        sa.Column("undercurrent_b", sa.Boolean(), nullable=True),
        sa.Column("undercurrent_c", sa.Boolean(), nullable=True),
        sa.Column("overvoltage_alarm_a", sa.Boolean(), nullable=True),
        sa.Column("overvoltage_alarm_b", sa.Boolean(), nullable=True),
        sa.Column("overvoltage_alarm_c", sa.Boolean(), nullable=True),
        sa.Column("voltage_thd_alarm_a", sa.Boolean(), nullable=True),
        sa.Column("voltage_thd_alarm_b", sa.Boolean(), nullable=True),
        sa.Column("voltage_thd_alarm_c", sa.Boolean(), nullable=True),
        sa.Column("current_thd_alarm_a", sa.Boolean(), nullable=True),
        sa.Column("current_thd_alarm_b", sa.Boolean(), nullable=True),
        sa.Column("current_thd_alarm_c", sa.Boolean(), nullable=True),
        sa.Column("temp_alarm", sa.Boolean(), nullable=True),
        sa.Column("circuit_state_phase_a", sa.Integer(), nullable=True),
        sa.Column("circuit_state_phase_b", sa.Integer(), nullable=True),
        sa.Column("circuit_state_phase_c", sa.Integer(), nullable=True),
        sa.Column("circuit_state_common_1", sa.Integer(), nullable=True),
        sa.Column("circuit_state_common_2", sa.Integer(), nullable=True),
        sa.Column("circuit_state_common_3", sa.Integer(), nullable=True),
        sa.Column("phase_a_circuit_running_count", sa.Integer(), nullable=True),
        sa.Column("phase_b_circuit_running_count", sa.Integer(), nullable=True),
        sa.Column("phase_c_circuit_running_count", sa.Integer(), nullable=True),
        sa.Column("common_group_1_running_count", sa.Integer(), nullable=True),
        sa.Column("common_group_2_running_count", sa.Integer(), nullable=True),
        sa.Column("common_group_3_running_count", sa.Integer(), nullable=True),
        sa.Column("split_circuit_running_count", sa.Integer(), nullable=True),
        sa.Column("common_circuit_running_count", sa.Integer(), nullable=True),
        sa.Column("running_circuit_count", sa.Integer(), nullable=True),
        sa.Column("control_mode", sa.String(), nullable=True),
        sa.Column("auto_on_elapsed_seconds", sa.Integer(), nullable=True),
        sa.Column("auto_off_elapsed_seconds", sa.Integer(), nullable=True),
        sa.Column("last_auto_action", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.PrimaryKeyConstraint("device_id", "timestamp"),
    )
    op.create_table(
        "carbon_emission",
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("energy_type", sa.String(), nullable=False),
        sa.Column("energy_consumption", sa.Float(), nullable=False),
        sa.Column("consumption_unit", sa.String(), nullable=False),
        sa.Column("carbon_factor", sa.Float(), nullable=False),
        sa.Column("carbon_emission", sa.Float(), nullable=False),
        sa.Column("scope", sa.Integer(), nullable=True),
        sa.Column("calculation_method", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.PrimaryKeyConstraint("device_id", "timestamp"),
    )
    op.create_index(
        op.f("ix_carbon_emission_energy_type"), "carbon_emission", ["energy_type"], unique=False
    )
    op.create_index(
        op.f("ix_carbon_emission_timestamp"), "carbon_emission", ["timestamp"], unique=False
    )
    op.create_table(
        "device_control_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("target_status", sa.Boolean(), nullable=False),
        sa.Column("previous_status", sa.Boolean(), nullable=True),
        sa.Column("operator", sa.String(), nullable=True),
        sa.Column("command_source", sa.String(), nullable=False),
        sa.Column("result", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_device_control_log_action"), "device_control_log", ["action"], unique=False
    )
    op.create_index(
        op.f("ix_device_control_log_created_at"), "device_control_log", ["created_at"], unique=False
    )
    op.create_index(
        op.f("ix_device_control_log_device_id"), "device_control_log", ["device_id"], unique=False
    )
    op.create_index(
        op.f("ix_device_control_log_result"), "device_control_log", ["result"], unique=False
    )
    op.create_table(
        "device_group_membership",
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.Column("note", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["device_group.id"],
        ),
        sa.PrimaryKeyConstraint("device_id", "group_id"),
    )
    op.create_table(
        "device_ingestion_health",
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(), nullable=True),
        sa.Column("last_failure_reason", sa.String(), nullable=True),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False),
        sa.Column("total_messages", sa.Integer(), nullable=False),
        sa.Column("total_failures", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.PrimaryKeyConstraint("device_id"),
    )
    op.create_index(
        op.f("ix_device_ingestion_health_last_failure_at"),
        "device_ingestion_health",
        ["last_failure_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_device_ingestion_health_last_message_at"),
        "device_ingestion_health",
        ["last_message_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_device_ingestion_health_last_success_at"),
        "device_ingestion_health",
        ["last_success_at"],
        unique=False,
    )
    op.create_table(
        "device_maintenance",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("maintenance_type", sa.String(), nullable=False),
        sa.Column("scheduled_time", sa.DateTime(), nullable=False),
        sa.Column("actual_start_time", sa.DateTime(), nullable=True),
        sa.Column("actual_end_time", sa.DateTime(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("operator", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("parts_replaced", sa.String(), nullable=True),
        sa.Column("result", sa.String(), nullable=True),
        sa.Column("next_maintenance_date", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_device_maintenance_device_id"), "device_maintenance", ["device_id"], unique=False
    )
    op.create_index(
        op.f("ix_device_maintenance_maintenance_type"),
        "device_maintenance",
        ["maintenance_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_device_maintenance_scheduled_time"),
        "device_maintenance",
        ["scheduled_time"],
        unique=False,
    )
    op.create_index(
        op.f("ix_device_maintenance_status"), "device_maintenance", ["status"], unique=False
    )
    op.create_table(
        "energy_statistics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=True),
        sa.Column("energy_type", sa.String(), nullable=False),
        sa.Column("stat_time", sa.DateTime(), nullable=False),
        sa.Column("period_type", sa.String(), nullable=False),
        sa.Column("total_consumption", sa.Float(), nullable=False),
        sa.Column("avg_flow_rate", sa.Float(), nullable=True),
        sa.Column("peak_flow_rate", sa.Float(), nullable=True),
        sa.Column("unit_price", sa.Float(), nullable=True),
        sa.Column("total_cost", sa.Float(), nullable=True),
        sa.Column("total_carbon", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_energy_statistics_device_id"), "energy_statistics", ["device_id"], unique=False
    )
    op.create_index(
        op.f("ix_energy_statistics_energy_type"), "energy_statistics", ["energy_type"], unique=False
    )
    op.create_index(
        op.f("ix_energy_statistics_period_type"), "energy_statistics", ["period_type"], unique=False
    )
    op.create_index(
        op.f("ix_energy_statistics_stat_time"), "energy_statistics", ["stat_time"], unique=False
    )
    op.create_table(
        "energydata",
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("energy_type", sa.String(), nullable=False),
        sa.Column("consumption", sa.Float(), nullable=False),
        sa.Column("flow_rate", sa.Float(), nullable=True),
        sa.Column("voltage", sa.Float(), nullable=True),
        sa.Column("current", sa.Float(), nullable=True),
        sa.Column("power_factor", sa.Float(), nullable=True),
        sa.Column("reactive_power", sa.Float(), nullable=True),
        sa.Column("pressure", sa.Float(), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("supply_temp", sa.Float(), nullable=True),
        sa.Column("return_temp", sa.Float(), nullable=True),
        sa.Column("heat_flow", sa.Float(), nullable=True),
        sa.Column("quality_index", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.PrimaryKeyConstraint("device_id", "timestamp"),
    )
    op.create_index(op.f("ix_energydata_energy_type"), "energydata", ["energy_type"], unique=False)
    op.create_index(op.f("ix_energydata_timestamp"), "energydata", ["timestamp"], unique=False)
    op.execute(
        "SELECT create_hypertable('energydata', 'timestamp', "
        "if_not_exists => TRUE, migrate_data => FALSE)"
    )
    op.create_table(
        "inspection_point",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("route_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("check_items", sa.String(), nullable=True),
        sa.Column("qr_code", sa.String(), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.ForeignKeyConstraint(
            ["route_id"],
            ["inspection_route.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("qr_code"),
    )
    op.create_index(
        op.f("ix_inspection_point_route_id"), "inspection_point", ["route_id"], unique=False
    )
    op.create_table(
        "inspection_task",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=True),
        sa.Column("route_id", sa.Integer(), nullable=False),
        sa.Column("task_no", sa.String(), nullable=False),
        sa.Column("task_date", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("inspector", sa.String(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("total_points", sa.Integer(), nullable=False),
        sa.Column("completed_points", sa.Integer(), nullable=False),
        sa.Column("abnormal_count", sa.Integer(), nullable=False),
        sa.Column("remark", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["inspection_plan.id"],
        ),
        sa.ForeignKeyConstraint(
            ["route_id"],
            ["inspection_route.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_inspection_task_route_id"), "inspection_task", ["route_id"], unique=False
    )
    op.create_index(op.f("ix_inspection_task_status"), "inspection_task", ["status"], unique=False)
    op.create_index(
        op.f("ix_inspection_task_task_date"), "inspection_task", ["task_date"], unique=False
    )
    op.create_index(op.f("ix_inspection_task_task_no"), "inspection_task", ["task_no"], unique=True)
    op.create_table(
        "mqtt_ingestion_record",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fingerprint", sa.String(), nullable=False),
        sa.Column("payload_hash", sa.String(), nullable=False),
        sa.Column("raw_payload", sa.String(), nullable=True),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("topic", sa.String(), nullable=True),
        sa.Column("telemetry_timestamp", sa.DateTime(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error_reason", sa.String(), nullable=True),
        sa.Column("duplicate_count", sa.Integer(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("next_retry_at", sa.DateTime(), nullable=True),
        sa.Column("replay_count", sa.Integer(), nullable=False),
        sa.Column("last_replayed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_mqtt_ingestion_record_device_id"),
        "mqtt_ingestion_record",
        ["device_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mqtt_ingestion_record_fingerprint"),
        "mqtt_ingestion_record",
        ["fingerprint"],
        unique=True,
    )
    op.create_index(
        op.f("ix_mqtt_ingestion_record_last_replayed_at"),
        "mqtt_ingestion_record",
        ["last_replayed_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mqtt_ingestion_record_last_seen_at"),
        "mqtt_ingestion_record",
        ["last_seen_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mqtt_ingestion_record_next_retry_at"),
        "mqtt_ingestion_record",
        ["next_retry_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mqtt_ingestion_record_payload_hash"),
        "mqtt_ingestion_record",
        ["payload_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mqtt_ingestion_record_received_at"),
        "mqtt_ingestion_record",
        ["received_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mqtt_ingestion_record_status"), "mqtt_ingestion_record", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_mqtt_ingestion_record_telemetry_timestamp"),
        "mqtt_ingestion_record",
        ["telemetry_timestamp"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mqtt_ingestion_record_topic"), "mqtt_ingestion_record", ["topic"], unique=False
    )
    op.create_table(
        "storage_telemetry",
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("soc", sa.Float(), nullable=True),
        sa.Column("soh", sa.Float(), nullable=True),
        sa.Column("active_power", sa.Float(), nullable=True),
        sa.Column("reactive_power", sa.Float(), nullable=True),
        sa.Column("dc_voltage", sa.Float(), nullable=True),
        sa.Column("dc_current", sa.Float(), nullable=True),
        sa.Column("ac_voltage_a", sa.Float(), nullable=True),
        sa.Column("ac_voltage_b", sa.Float(), nullable=True),
        sa.Column("ac_voltage_c", sa.Float(), nullable=True),
        sa.Column("ac_current_a", sa.Float(), nullable=True),
        sa.Column("ac_current_b", sa.Float(), nullable=True),
        sa.Column("ac_current_c", sa.Float(), nullable=True),
        sa.Column("frequency", sa.Float(), nullable=True),
        sa.Column("cell_temp_max", sa.Float(), nullable=True),
        sa.Column("cell_temp_min", sa.Float(), nullable=True),
        sa.Column("cell_temp_avg", sa.Float(), nullable=True),
        sa.Column("run_state", sa.String(), nullable=True),
        sa.Column("control_mode", sa.String(), nullable=True),
        sa.Column("fault_code", sa.Integer(), nullable=True),
        sa.Column("alarm_code", sa.Integer(), nullable=True),
        sa.Column("charge_energy_today", sa.Float(), nullable=True),
        sa.Column("discharge_energy_today", sa.Float(), nullable=True),
        sa.Column("charge_energy_total", sa.Float(), nullable=True),
        sa.Column("discharge_energy_total", sa.Float(), nullable=True),
        sa.Column("cycle_count", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.PrimaryKeyConstraint("device_id", "timestamp"),
    )
    op.create_table(
        "svg_asset_profile",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("model_number", sa.String(), nullable=True),
        sa.Column("rated_voltage", sa.Float(), nullable=True),
        sa.Column("rated_frequency", sa.Float(), nullable=True),
        sa.Column("comm_address", sa.String(), nullable=True),
        sa.Column("software_version", sa.String(), nullable=True),
        sa.Column("hardware_version", sa.String(), nullable=True),
        sa.Column("protocol_version", sa.String(), nullable=True),
        sa.Column("module_count", sa.Integer(), nullable=True),
        sa.Column("single_module_capacity", sa.Float(), nullable=True),
        sa.Column("device_label_zh", sa.String(), nullable=True),
        sa.Column("asset_number", sa.String(), nullable=True),
        sa.Column("fixed_asset_code", sa.String(), nullable=True),
        sa.Column("qr_code_number", sa.String(), nullable=True),
        sa.Column("asset_group", sa.String(), nullable=True),
        sa.Column("distribution_room", sa.String(), nullable=True),
        sa.Column("distribution_cabinet", sa.String(), nullable=True),
        sa.Column("circuit", sa.String(), nullable=True),
        sa.Column("area", sa.String(), nullable=True),
        sa.Column("building", sa.String(), nullable=True),
        sa.Column("install_date", sa.Date(), nullable=True),
        sa.Column("commission_date", sa.Date(), nullable=True),
        sa.Column("field_number", sa.String(), nullable=True),
        sa.Column("om_responsible", sa.String(), nullable=True),
        sa.Column("inspection_responsible", sa.String(), nullable=True),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("management_unit", sa.String(), nullable=True),
        sa.Column("contact_phone", sa.String(), nullable=True),
        sa.Column("warranty_expiry", sa.Date(), nullable=True),
        sa.Column("maintenance_cycle_days", sa.Integer(), nullable=True),
        sa.Column("device_group", sa.String(), nullable=True),
        sa.Column("device_tree_level", sa.String(), nullable=True),
        sa.Column("monitor_screen_position", sa.String(), nullable=True),
        sa.Column("alarm_policy", sa.String(), nullable=True),
        sa.Column("device_alias", sa.String(), nullable=True),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_svg_asset_profile_device_id"), "svg_asset_profile", ["device_id"], unique=True
    )
    op.create_table(
        "svg_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("model_number", sa.String(), nullable=True),
        sa.Column("rated_voltage", sa.Float(), nullable=True),
        sa.Column("rated_frequency", sa.Float(), nullable=True),
        sa.Column("comm_address", sa.String(), nullable=True),
        sa.Column("software_version", sa.String(), nullable=True),
        sa.Column("hardware_version", sa.String(), nullable=True),
        sa.Column("protocol_version", sa.String(), nullable=True),
        sa.Column("module_count", sa.Integer(), nullable=True),
        sa.Column("single_module_capacity", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_svg_config_device_id"), "svg_config", ["device_id"], unique=True)
    op.create_table(
        "svg_telemetry",
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("voltage_a", sa.Float(), nullable=True),
        sa.Column("voltage_b", sa.Float(), nullable=True),
        sa.Column("voltage_c", sa.Float(), nullable=True),
        sa.Column("current_a", sa.Float(), nullable=True),
        sa.Column("current_b", sa.Float(), nullable=True),
        sa.Column("current_c", sa.Float(), nullable=True),
        sa.Column("frequency", sa.Float(), nullable=True),
        sa.Column("svg_reactive_output", sa.Float(), nullable=True),
        sa.Column("capacity_utilization", sa.Float(), nullable=True),
        sa.Column("output_direction", sa.String(), nullable=True),
        sa.Column("run_status", sa.Boolean(), nullable=True),
        sa.Column("stop_status", sa.Boolean(), nullable=True),
        sa.Column("auto_mode", sa.Boolean(), nullable=True),
        sa.Column("local_mode", sa.Boolean(), nullable=True),
        sa.Column("breaker_status", sa.Boolean(), nullable=True),
        sa.Column("module_status", sa.Boolean(), nullable=True),
        sa.Column("fan_status", sa.Boolean(), nullable=True),
        sa.Column("comm_status", sa.Boolean(), nullable=True),
        sa.Column("overvoltage_fault", sa.Boolean(), nullable=True),
        sa.Column("undervoltage_fault", sa.Boolean(), nullable=True),
        sa.Column("overcurrent_fault", sa.Boolean(), nullable=True),
        sa.Column("overtemp_fault", sa.Boolean(), nullable=True),
        sa.Column("module_fault", sa.Boolean(), nullable=True),
        sa.Column("fan_fault", sa.Boolean(), nullable=True),
        sa.Column("comm_fault", sa.Boolean(), nullable=True),
        sa.Column("current_fault_code", sa.String(), nullable=True),
        sa.Column("current_alarm_code", sa.String(), nullable=True),
        sa.Column("cabinet_temp", sa.Float(), nullable=True),
        sa.Column("module_temp", sa.Float(), nullable=True),
        sa.Column("igbt_temp", sa.Float(), nullable=True),
        sa.Column("dc_bus_voltage", sa.Float(), nullable=True),
        sa.Column("heatsink_temp", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.PrimaryKeyConstraint("device_id", "timestamp"),
    )
    op.create_table(
        "inspection_record",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("point_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=True),
        sa.Column("result", sa.String(), nullable=False),
        sa.Column("check_time", sa.DateTime(), nullable=False),
        sa.Column("check_details", sa.String(), nullable=True),
        sa.Column("meter_reading", sa.Float(), nullable=True),
        sa.Column("abnormal_description", sa.String(), nullable=True),
        sa.Column("abnormal_level", sa.String(), nullable=True),
        sa.Column("images", sa.String(), nullable=True),
        sa.Column("is_handled", sa.Boolean(), nullable=False),
        sa.Column("handle_result", sa.String(), nullable=True),
        sa.Column("inspector", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["device.id"],
        ),
        sa.ForeignKeyConstraint(
            ["point_id"],
            ["inspection_point.id"],
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["inspection_task.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_inspection_record_point_id"), "inspection_record", ["point_id"], unique=False
    )
    op.create_index(
        op.f("ix_inspection_record_task_id"), "inspection_record", ["task_id"], unique=False
    )
    op.create_index(
        "idx_energydata_device_timestamp",
        "energydata",
        ["device_id", sa.text("timestamp DESC")],
        unique=False,
    )
    op.create_index(
        "idx_energydata_energy_type_timestamp",
        "energydata",
        ["energy_type", sa.text("timestamp DESC")],
        unique=False,
    )
    op.create_index(
        "idx_alarm_device_resolved_timestamp",
        "alarm",
        ["device_id", "is_resolved", sa.text("timestamp DESC")],
        unique=False,
    )
    op.create_index(
        "idx_alarm_instance_recovered_last_seen",
        "alarm",
        ["instance_key", "recovered_at", sa.text("last_seen_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_device_ingestion_health_last_success",
        "device_ingestion_health",
        [sa.text("last_success_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_device_ingestion_health_last_failure",
        "device_ingestion_health",
        [sa.text("last_failure_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_audit_event_action_created_at",
        "audit_event",
        ["action", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_audit_event_actor_created_at",
        "audit_event",
        ["actor", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_audit_event_outcome_created_at",
        "audit_event",
        ["outcome", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_mqtt_ingestion_record_device_received",
        "mqtt_ingestion_record",
        ["device_id", sa.text("received_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_mqtt_ingestion_record_status_received",
        "mqtt_ingestion_record",
        ["status", sa.text("received_at DESC")],
        unique=False,
    )
    op.create_index(
        "idx_mqtt_ingestion_record_next_retry_at",
        "mqtt_ingestion_record",
        ["next_retry_at"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_index(
        "idx_mqtt_ingestion_record_next_retry_at", table_name="mqtt_ingestion_record"
    )
    op.drop_index(
        "idx_mqtt_ingestion_record_status_received", table_name="mqtt_ingestion_record"
    )
    op.drop_index(
        "idx_mqtt_ingestion_record_device_received", table_name="mqtt_ingestion_record"
    )
    op.drop_index("idx_audit_event_outcome_created_at", table_name="audit_event")
    op.drop_index("idx_audit_event_actor_created_at", table_name="audit_event")
    op.drop_index("idx_audit_event_action_created_at", table_name="audit_event")
    op.drop_index(
        "idx_device_ingestion_health_last_failure", table_name="device_ingestion_health"
    )
    op.drop_index(
        "idx_device_ingestion_health_last_success", table_name="device_ingestion_health"
    )
    op.drop_index("idx_alarm_instance_recovered_last_seen", table_name="alarm")
    op.drop_index("idx_alarm_device_resolved_timestamp", table_name="alarm")
    op.drop_index("idx_energydata_energy_type_timestamp", table_name="energydata")
    op.drop_index("idx_energydata_device_timestamp", table_name="energydata")
    op.drop_index(op.f("ix_inspection_record_task_id"), table_name="inspection_record")
    op.drop_index(op.f("ix_inspection_record_point_id"), table_name="inspection_record")
    op.drop_table("inspection_record")
    op.drop_table("svg_telemetry")
    op.drop_index(op.f("ix_svg_config_device_id"), table_name="svg_config")
    op.drop_table("svg_config")
    op.drop_index(op.f("ix_svg_asset_profile_device_id"), table_name="svg_asset_profile")
    op.drop_table("svg_asset_profile")
    op.drop_table("storage_telemetry")
    op.drop_index(op.f("ix_mqtt_ingestion_record_topic"), table_name="mqtt_ingestion_record")
    op.drop_index(
        op.f("ix_mqtt_ingestion_record_telemetry_timestamp"), table_name="mqtt_ingestion_record"
    )
    op.drop_index(op.f("ix_mqtt_ingestion_record_status"), table_name="mqtt_ingestion_record")
    op.drop_index(op.f("ix_mqtt_ingestion_record_received_at"), table_name="mqtt_ingestion_record")
    op.drop_index(op.f("ix_mqtt_ingestion_record_payload_hash"), table_name="mqtt_ingestion_record")
    op.drop_index(
        op.f("ix_mqtt_ingestion_record_next_retry_at"), table_name="mqtt_ingestion_record"
    )
    op.drop_index(op.f("ix_mqtt_ingestion_record_last_seen_at"), table_name="mqtt_ingestion_record")
    op.drop_index(
        op.f("ix_mqtt_ingestion_record_last_replayed_at"), table_name="mqtt_ingestion_record"
    )
    op.drop_index(op.f("ix_mqtt_ingestion_record_fingerprint"), table_name="mqtt_ingestion_record")
    op.drop_index(op.f("ix_mqtt_ingestion_record_device_id"), table_name="mqtt_ingestion_record")
    op.drop_table("mqtt_ingestion_record")
    op.drop_index(op.f("ix_inspection_task_task_no"), table_name="inspection_task")
    op.drop_index(op.f("ix_inspection_task_task_date"), table_name="inspection_task")
    op.drop_index(op.f("ix_inspection_task_status"), table_name="inspection_task")
    op.drop_index(op.f("ix_inspection_task_route_id"), table_name="inspection_task")
    op.drop_table("inspection_task")
    op.drop_index(op.f("ix_inspection_point_route_id"), table_name="inspection_point")
    op.drop_table("inspection_point")
    op.drop_index(op.f("ix_energydata_timestamp"), table_name="energydata")
    op.drop_index(op.f("ix_energydata_energy_type"), table_name="energydata")
    op.drop_table("energydata")
    op.drop_index(op.f("ix_energy_statistics_stat_time"), table_name="energy_statistics")
    op.drop_index(op.f("ix_energy_statistics_period_type"), table_name="energy_statistics")
    op.drop_index(op.f("ix_energy_statistics_energy_type"), table_name="energy_statistics")
    op.drop_index(op.f("ix_energy_statistics_device_id"), table_name="energy_statistics")
    op.drop_table("energy_statistics")
    op.drop_index(op.f("ix_device_maintenance_status"), table_name="device_maintenance")
    op.drop_index(op.f("ix_device_maintenance_scheduled_time"), table_name="device_maintenance")
    op.drop_index(op.f("ix_device_maintenance_maintenance_type"), table_name="device_maintenance")
    op.drop_index(op.f("ix_device_maintenance_device_id"), table_name="device_maintenance")
    op.drop_table("device_maintenance")
    op.drop_index(
        op.f("ix_device_ingestion_health_last_success_at"), table_name="device_ingestion_health"
    )
    op.drop_index(
        op.f("ix_device_ingestion_health_last_message_at"), table_name="device_ingestion_health"
    )
    op.drop_index(
        op.f("ix_device_ingestion_health_last_failure_at"), table_name="device_ingestion_health"
    )
    op.drop_table("device_ingestion_health")
    op.drop_table("device_group_membership")
    op.drop_index(op.f("ix_device_control_log_result"), table_name="device_control_log")
    op.drop_index(op.f("ix_device_control_log_device_id"), table_name="device_control_log")
    op.drop_index(op.f("ix_device_control_log_created_at"), table_name="device_control_log")
    op.drop_index(op.f("ix_device_control_log_action"), table_name="device_control_log")
    op.drop_table("device_control_log")
    op.drop_index(op.f("ix_carbon_emission_timestamp"), table_name="carbon_emission")
    op.drop_index(op.f("ix_carbon_emission_energy_type"), table_name="carbon_emission")
    op.drop_table("carbon_emission")
    op.drop_table("capacitor_bank_telemetry")
    op.drop_index(
        op.f("ix_capacitor_bank_control_profile_device_id"),
        table_name="capacitor_bank_control_profile",
    )
    op.drop_table("capacitor_bank_control_profile")
    op.drop_index(op.f("ix_alarm_timestamp"), table_name="alarm")
    op.drop_index(op.f("ix_alarm_severity"), table_name="alarm")
    op.drop_index(op.f("ix_alarm_resolved_at"), table_name="alarm")
    op.drop_index(op.f("ix_alarm_recovered_at"), table_name="alarm")
    op.drop_index(op.f("ix_alarm_last_seen_at"), table_name="alarm")
    op.drop_index(op.f("ix_alarm_instance_key"), table_name="alarm")
    op.drop_index(op.f("ix_alarm_device_id"), table_name="alarm")
    op.drop_index(op.f("ix_alarm_category"), table_name="alarm")
    op.drop_table("alarm")
    op.drop_index(op.f("ix_inspection_plan_route_id"), table_name="inspection_plan")
    op.drop_table("inspection_plan")
    op.drop_index(op.f("ix_device_sn"), table_name="device")
    op.drop_index(op.f("ix_device_name"), table_name="device")
    op.drop_index(op.f("ix_device_location_id"), table_name="device")
    op.drop_index(op.f("ix_device_energy_type"), table_name="device")
    op.drop_index(op.f("ix_device_device_type"), table_name="device")
    op.drop_index(op.f("ix_device_device_subtype"), table_name="device")
    op.drop_index(op.f("ix_device_device_category"), table_name="device")
    op.drop_index(op.f("ix_device_archive_status"), table_name="device")
    op.drop_table("device")
    op.drop_index(op.f("ix_user_username"), table_name="user")
    op.drop_index(op.f("ix_user_role"), table_name="user")
    op.drop_index(op.f("ix_user_locked_until"), table_name="user")
    op.drop_index(op.f("ix_user_last_login_at"), table_name="user")
    op.drop_table("user")
    op.drop_index(op.f("ix_location_name"), table_name="location")
    op.drop_index(op.f("ix_location_location_type"), table_name="location")
    op.drop_index(op.f("ix_location_full_path"), table_name="location")
    op.drop_index(op.f("ix_location_code"), table_name="location")
    op.drop_table("location")
    op.drop_index(op.f("ix_inspection_route_name"), table_name="inspection_route")
    op.drop_table("inspection_route")
    op.drop_index(op.f("ix_device_group_name"), table_name="device_group")
    op.drop_index(op.f("ix_device_group_group_type"), table_name="device_group")
    op.drop_index(op.f("ix_device_group_code"), table_name="device_group")
    op.drop_table("device_group")
    op.drop_index(op.f("ix_audit_event_target"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_outcome"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_created_at"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_actor_role"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_actor"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_action"), table_name="audit_event")
    op.drop_table("audit_event")
    # ### end Alembic commands ###
