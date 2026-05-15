"""
补偿类设备专属模型。

只承载补偿设备族的专属遥测、参数快照和运维档案模型；
公共设备、公共遥测和通用控制模型仍保留在 app.models.tables。
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class SVGConfig(SQLModel, table=True):
    """SVG 静态设备参数（每台设备一条）。"""

    __tablename__ = "svg_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: int = Field(foreign_key="device.id", unique=True, index=True, description="关联设备ID")

    # 基础设备参数
    model_number: Optional[str] = Field(default=None, description="设备型号")
    rated_voltage: Optional[float] = Field(default=None, description="额定电压 (V)")
    rated_frequency: Optional[float] = Field(default=None, description="额定频率 (Hz)")
    comm_address: Optional[str] = Field(default=None, description="通信地址")
    software_version: Optional[str] = Field(default=None, description="软件版本")
    hardware_version: Optional[str] = Field(default=None, description="硬件版本")
    protocol_version: Optional[str] = Field(default=None, description="协议版本")
    module_count: Optional[int] = Field(default=None, description="模块数量")
    single_module_capacity: Optional[float] = Field(default=None, description="单模块容量 (kVAR)")

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SVGTelemetry(SQLModel, table=True):
    """SVG 时序扩展数据（与 EnergyData 同频写入）。"""

    __tablename__ = "svg_telemetry"

    device_id: int = Field(foreign_key="device.id", primary_key=True, description="关联设备ID")
    timestamp: datetime = Field(primary_key=True, description="数据时间戳")

    # 三相电压 (V)
    voltage_a: Optional[float] = Field(default=None, description="A相电压 (V)")
    voltage_b: Optional[float] = Field(default=None, description="B相电压 (V)")
    voltage_c: Optional[float] = Field(default=None, description="C相电压 (V)")

    # 三相电流 (A)
    current_a: Optional[float] = Field(default=None, description="A相电流 (A)")
    current_b: Optional[float] = Field(default=None, description="B相电流 (A)")
    current_c: Optional[float] = Field(default=None, description="C相电流 (A)")

    frequency: Optional[float] = Field(default=None, description="频率 (Hz)")
    svg_reactive_output: Optional[float] = Field(default=None, description="SVG当前输出无功 (kVAR)")
    capacity_utilization: Optional[float] = Field(default=None, description="容量利用率 (%)")
    output_direction: Optional[str] = Field(default=None, description="输出方向：inductive/capacitive")

    # 状态位
    run_status: Optional[bool] = Field(default=None, description="运行状态")
    stop_status: Optional[bool] = Field(default=None, description="停机状态")
    auto_mode: Optional[bool] = Field(default=None, description="自动模式 (True=自动, False=手动)")
    local_mode: Optional[bool] = Field(default=None, description="本地模式 (True=本地, False=远方)")
    breaker_status: Optional[bool] = Field(default=None, description="断路器状态")
    module_status: Optional[bool] = Field(default=None, description="模块状态")
    fan_status: Optional[bool] = Field(default=None, description="风机状态")
    comm_status: Optional[bool] = Field(default=None, description="通信状态")

    # 告警故障位
    overvoltage_fault: Optional[bool] = Field(default=None, description="过压故障")
    undervoltage_fault: Optional[bool] = Field(default=None, description="欠压故障")
    overcurrent_fault: Optional[bool] = Field(default=None, description="过流故障")
    overtemp_fault: Optional[bool] = Field(default=None, description="过温故障")
    module_fault: Optional[bool] = Field(default=None, description="模块故障")
    fan_fault: Optional[bool] = Field(default=None, description="风机故障")
    comm_fault: Optional[bool] = Field(default=None, description="通信故障")
    current_fault_code: Optional[str] = Field(default=None, description="当前故障代码")
    current_alarm_code: Optional[str] = Field(default=None, description="当前告警代码")

    # 温度和内部量
    cabinet_temp: Optional[float] = Field(default=None, description="柜内温度 (°C)")
    module_temp: Optional[float] = Field(default=None, description="模块温度 (°C)")
    igbt_temp: Optional[float] = Field(default=None, description="IGBT温度 (°C)")
    dc_bus_voltage: Optional[float] = Field(default=None, description="直流母线电压 (V)")
    heatsink_temp: Optional[float] = Field(default=None, description="散热器温度 (°C)")


class CapacitorBankTelemetry(SQLModel, table=True):
    """
    电容补偿控制器（JKWF-LCD）时序扩展数据。

    与 EnergyData 同频写入，存储 JKWF-LCD 协议特有字段：
    三相功率（有功/无功/视在）、电压/电流 THD、状态标志位、电容回路投切状态。
    """

    __tablename__ = "capacitor_bank_telemetry"

    device_id: int = Field(foreign_key="device.id", primary_key=True, description="关联设备ID")
    timestamp: datetime = Field(primary_key=True, description="数据时间戳")

    # 三相电压 (V) / 电流 (A)
    voltage_a: Optional[float] = Field(default=None, description="A相电压 (V)")
    voltage_b: Optional[float] = Field(default=None, description="B相电压 (V)")
    voltage_c: Optional[float] = Field(default=None, description="C相电压 (V)")
    current_a: Optional[float] = Field(default=None, description="A相电流 (A)")
    current_b: Optional[float] = Field(default=None, description="B相电流 (A)")
    current_c: Optional[float] = Field(default=None, description="C相电流 (A)")

    # 三相功率因数
    power_factor_a: Optional[float] = Field(default=None, description="A相功率因数")
    power_factor_b: Optional[float] = Field(default=None, description="B相功率因数")
    power_factor_c: Optional[float] = Field(default=None, description="C相功率因数")

    # 三相有功功率 (kW)
    active_power_a: Optional[float] = Field(default=None, description="A相有功功率 (kW)")
    active_power_b: Optional[float] = Field(default=None, description="B相有功功率 (kW)")
    active_power_c: Optional[float] = Field(default=None, description="C相有功功率 (kW)")

    # 三相无功功率 (kvar)，正值=感性，负值=容性补偿输出
    reactive_power_a: Optional[float] = Field(default=None, description="A相无功功率 (kvar)")
    reactive_power_b: Optional[float] = Field(default=None, description="B相无功功率 (kvar)")
    reactive_power_c: Optional[float] = Field(default=None, description="C相无功功率 (kvar)")

    # 三相视在功率 (kVA)
    apparent_power_a: Optional[float] = Field(default=None, description="A相视在功率 (kVA)")
    apparent_power_b: Optional[float] = Field(default=None, description="B相视在功率 (kVA)")
    apparent_power_c: Optional[float] = Field(default=None, description="C相视在功率 (kVA)")

    # 电压谐波 THD (%)
    voltage_thd_a: Optional[float] = Field(default=None, description="A相电压THD (%)")
    voltage_thd_b: Optional[float] = Field(default=None, description="B相电压THD (%)")
    voltage_thd_c: Optional[float] = Field(default=None, description="C相电压THD (%)")

    # 谐波电流幅值 (A)
    current_harmonic_a: Optional[float] = Field(default=None, description="A相谐波电流幅值 (A)")
    current_harmonic_b: Optional[float] = Field(default=None, description="B相谐波电流幅值 (A)")
    current_harmonic_c: Optional[float] = Field(default=None, description="C相谐波电流幅值 (A)")
    voltage_harmonics_a: Optional[list[dict[str, Any]]] = Field(default=None, sa_column=Column(JSON, nullable=True), description="A相2-31次电压谐波谱线")
    voltage_harmonics_b: Optional[list[dict[str, Any]]] = Field(default=None, sa_column=Column(JSON, nullable=True), description="B相2-31次电压谐波谱线")
    voltage_harmonics_c: Optional[list[dict[str, Any]]] = Field(default=None, sa_column=Column(JSON, nullable=True), description="C相2-31次电压谐波谱线")
    current_harmonics_a: Optional[list[dict[str, Any]]] = Field(default=None, sa_column=Column(JSON, nullable=True), description="A相2-31次电流谐波谱线")
    current_harmonics_b: Optional[list[dict[str, Any]]] = Field(default=None, sa_column=Column(JSON, nullable=True), description="B相2-31次电流谐波谱线")
    current_harmonics_c: Optional[list[dict[str, Any]]] = Field(default=None, sa_column=Column(JSON, nullable=True), description="C相2-31次电流谐波谱线")

    # 系统参数
    frequency: Optional[float] = Field(default=None, description="系统频率 (Hz)")
    temperature: Optional[float] = Field(default=None, description="柜内温度 (°C)")

    # 状态标志位（从寄存器 0x00 解码）
    leading_a: Optional[bool] = Field(default=None, description="A相超前（True=超前/容性，False=滞后/感性）")
    leading_b: Optional[bool] = Field(default=None, description="B相超前")
    leading_c: Optional[bool] = Field(default=None, description="C相超前")
    undercurrent_a: Optional[bool] = Field(default=None, description="A相欠流告警")
    undercurrent_b: Optional[bool] = Field(default=None, description="B相欠流告警")
    undercurrent_c: Optional[bool] = Field(default=None, description="C相欠流告警")
    overvoltage_alarm_a: Optional[bool] = Field(default=None, description="A相过压告警")
    overvoltage_alarm_b: Optional[bool] = Field(default=None, description="B相过压告警")
    overvoltage_alarm_c: Optional[bool] = Field(default=None, description="C相过压告警")
    voltage_thd_alarm_a: Optional[bool] = Field(default=None, description="A相电压谐波超限告警")
    voltage_thd_alarm_b: Optional[bool] = Field(default=None, description="B相电压谐波超限告警")
    voltage_thd_alarm_c: Optional[bool] = Field(default=None, description="C相电压谐波超限告警")
    current_thd_alarm_a: Optional[bool] = Field(default=None, description="A相电流谐波超限告警")
    current_thd_alarm_b: Optional[bool] = Field(default=None, description="B相电流谐波超限告警")
    current_thd_alarm_c: Optional[bool] = Field(default=None, description="C相电流谐波超限告警")
    temp_alarm: Optional[bool] = Field(default=None, description="温度超限告警")

    # 电容回路投切状态（各 8-bit，每个 bit 对应一路，1=已投入，0=已切除）
    circuit_state_phase_a: Optional[int] = Field(default=None, description="A相分补回路投切状态（bit mask，8路）")
    circuit_state_phase_b: Optional[int] = Field(default=None, description="B相分补回路投切状态")
    circuit_state_phase_c: Optional[int] = Field(default=None, description="C相分补回路投切状态")
    circuit_state_common_1: Optional[int] = Field(default=None, description="公补回路 1-8 投切状态")
    circuit_state_common_2: Optional[int] = Field(default=None, description="公补回路 9-16 投切状态")
    circuit_state_common_3: Optional[int] = Field(default=None, description="公补回路 17-24 投切状态")
    phase_a_circuit_running_count: Optional[int] = Field(default=None, description="A相分补当前投入回路数")
    phase_b_circuit_running_count: Optional[int] = Field(default=None, description="B相分补当前投入回路数")
    phase_c_circuit_running_count: Optional[int] = Field(default=None, description="C相分补当前投入回路数")
    common_group_1_running_count: Optional[int] = Field(default=None, description="公补 1 组当前投入回路数")
    common_group_2_running_count: Optional[int] = Field(default=None, description="公补 2 组当前投入回路数")
    common_group_3_running_count: Optional[int] = Field(default=None, description="公补 3 组当前投入回路数")
    split_circuit_running_count: Optional[int] = Field(default=None, description="分补当前投入回路总数")
    common_circuit_running_count: Optional[int] = Field(default=None, description="公补当前投入回路总数")
    running_circuit_count: Optional[int] = Field(default=None, description="当前投入回路总数")
    control_mode: Optional[str] = Field(default=None, description="控制模式：auto/manual")
    auto_on_elapsed_seconds: Optional[int] = Field(default=None, description="自动投入已累计等待秒数")
    auto_off_elapsed_seconds: Optional[int] = Field(default=None, description="自动切除已累计等待秒数")
    last_auto_action: Optional[str] = Field(default=None, description="最近一次自动投切动作")


class CapacitorBankControlProfile(SQLModel, table=True):
    """电容补偿控制器参数档案（只读快照，供控制台展示）。"""

    __tablename__ = "capacitor_bank_control_profile"

    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: int = Field(foreign_key="device.id", unique=True, index=True, description="关联设备ID")

    switch_on_power_factor: Optional[float] = Field(default=None, description="投入功率因数")
    switch_off_power_factor: Optional[float] = Field(default=None, description="切除功率因数")
    switch_on_delay_seconds: Optional[int] = Field(default=None, description="投入延时时间（秒）")
    switch_off_delay_seconds: Optional[int] = Field(default=None, description="切除延时时间（秒）")

    common_output_circuit_count: Optional[int] = Field(default=None, description="共补输出回路数")
    split_output_circuit_count: Optional[int] = Field(default=None, description="分补输出回路数")
    phase_a_circuit_total_count: Optional[int] = Field(default=None, description="A相分补配置回路数")
    phase_b_circuit_total_count: Optional[int] = Field(default=None, description="B相分补配置回路数")
    phase_c_circuit_total_count: Optional[int] = Field(default=None, description="C相分补配置回路数")
    common_1_circuit_total_count: Optional[int] = Field(default=None, description="公补 1-8 配置回路数")
    common_2_circuit_total_count: Optional[int] = Field(default=None, description="公补 9-16 配置回路数")
    common_3_circuit_total_count: Optional[int] = Field(default=None, description="公补 17-24 配置回路数")
    phase_a_capacity_steps_kvar_json: Optional[str] = Field(default=None, description="A相分补每路容量数组（JSON）")
    phase_b_capacity_steps_kvar_json: Optional[str] = Field(default=None, description="B相分补每路容量数组（JSON）")
    phase_c_capacity_steps_kvar_json: Optional[str] = Field(default=None, description="C相分补每路容量数组（JSON）")
    common_1_capacity_steps_kvar_json: Optional[str] = Field(default=None, description="公补 1-8 每路容量数组（JSON）")
    common_2_capacity_steps_kvar_json: Optional[str] = Field(default=None, description="公补 9-16 每路容量数组（JSON）")
    common_3_capacity_steps_kvar_json: Optional[str] = Field(default=None, description="公补 17-24 每路容量数组（JSON）")
    phase_a_circuit_running_count: Optional[int] = Field(default=None, description="A相分补当前投入回路数")
    phase_b_circuit_running_count: Optional[int] = Field(default=None, description="B相分补当前投入回路数")
    phase_c_circuit_running_count: Optional[int] = Field(default=None, description="C相分补当前投入回路数")
    common_group_1_running_count: Optional[int] = Field(default=None, description="公补 1-8 当前投入回路数")
    common_group_2_running_count: Optional[int] = Field(default=None, description="公补 9-16 当前投入回路数")
    common_group_3_running_count: Optional[int] = Field(default=None, description="公补 17-24 当前投入回路数")
    split_circuit_running_count: Optional[int] = Field(default=None, description="分补当前投入回路数")
    common_circuit_running_count: Optional[int] = Field(default=None, description="共补当前投入回路数")
    running_circuit_count: Optional[int] = Field(default=None, description="当前总投入回路数")
    control_mode: Optional[str] = Field(default=None, description="控制模式：auto/manual")
    auto_on_elapsed_seconds: Optional[int] = Field(default=None, description="自动投入已累计等待秒数")
    auto_off_elapsed_seconds: Optional[int] = Field(default=None, description="自动切除已累计等待秒数")
    last_auto_action: Optional[str] = Field(default=None, description="最近一次自动投切动作")
    common_capacity_code: Optional[str] = Field(default=None, description="共补容量编码")
    split_capacity_code: Optional[str] = Field(default=None, description="分补容量编码")
    common_step_capacity_kvar: Optional[float] = Field(default=None, description="共补阶梯容量（kVar）")
    split_step_capacity_kvar: Optional[float] = Field(default=None, description="分补阶梯容量（kVar）")

    ct_primary_current: Optional[int] = Field(default=None, description="互感器一次值")
    overvoltage_threshold: Optional[float] = Field(default=None, description="过压保护门限（V）")
    voltage_harmonic_threshold: Optional[float] = Field(default=None, description="电压谐波门限（%）")
    current_harmonic_threshold: Optional[float] = Field(default=None, description="电流谐波门限（A）")
    temperature_upper_limit: Optional[float] = Field(default=None, description="温度上限门限（°C）")

    alarm_drive_event: Optional[str] = Field(default=None, description="报警驱动事件")
    baud_rate: Optional[int] = Field(default=None, description="通讯速率")
    terminal_assignment_scheme: Optional[str] = Field(default=None, description="端子分配方案")
    current_polarity_identification_enabled: Optional[bool] = Field(default=None, description="电流极性识别")
    source: Optional[str] = Field(default=None, description="参数来源：telemetry/gateway/manual")
    snapshot_timestamp: Optional[datetime] = Field(default=None, description="参数快照采集时间")

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SVGAssetProfile(SQLModel, table=True):
    """SVG 运维档案（运维人员维护，每台设备一条）。"""

    __tablename__ = "svg_asset_profile"

    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: int = Field(foreign_key="device.id", unique=True, index=True, description="关联设备ID")

    # 基础设备参数（原 svg_config，现并入统一运维档案）
    model_number: Optional[str] = Field(default=None, description="设备型号")
    rated_voltage: Optional[float] = Field(default=None, description="额定电压 (V)")
    rated_frequency: Optional[float] = Field(default=None, description="额定频率 (Hz)")
    comm_address: Optional[str] = Field(default=None, description="通信地址")
    software_version: Optional[str] = Field(default=None, description="软件版本")
    hardware_version: Optional[str] = Field(default=None, description="硬件版本")
    protocol_version: Optional[str] = Field(default=None, description="协议版本")
    module_count: Optional[int] = Field(default=None, description="模块数量")
    single_module_capacity: Optional[float] = Field(default=None, description="单模块容量 (kVAR)")

    # 资产管理类
    device_label_zh: Optional[str] = Field(default=None, description="设备中文标签")
    asset_number: Optional[str] = Field(default=None, description="资产编号")
    fixed_asset_code: Optional[str] = Field(default=None, description="固定资产编码")
    qr_code_number: Optional[str] = Field(default=None, description="设备二维码编号")
    asset_group: Optional[str] = Field(default=None, description="所属资产组")

    # 现场安装类
    distribution_room: Optional[str] = Field(default=None, description="所属配电室")
    distribution_cabinet: Optional[str] = Field(default=None, description="所属配电柜")
    circuit: Optional[str] = Field(default=None, description="所属回路")
    area: Optional[str] = Field(default=None, description="所属区域")
    building: Optional[str] = Field(default=None, description="所属楼栋")
    install_date: Optional[date] = Field(default=None, description="安装日期")
    commission_date: Optional[date] = Field(default=None, description="投运日期")
    field_number: Optional[str] = Field(default=None, description="现场编号")

    # 管理责任类
    om_responsible: Optional[str] = Field(default=None, description="运维负责人")
    inspection_responsible: Optional[str] = Field(default=None, description="巡检负责人")
    department: Optional[str] = Field(default=None, description="所属部门")
    management_unit: Optional[str] = Field(default=None, description="管理单位")
    contact_phone: Optional[str] = Field(default=None, description="联系电话")
    warranty_expiry: Optional[date] = Field(default=None, description="保修到期时间")
    maintenance_cycle_days: Optional[int] = Field(default=None, description="维护周期（天）")

    # 平台建模类
    device_group: Optional[str] = Field(default=None, description="设备分组")
    device_tree_level: Optional[str] = Field(default=None, description="设备树层级")
    monitor_screen_position: Optional[str] = Field(default=None, description="监控画面位置")
    alarm_policy: Optional[str] = Field(default=None, description="告警归属策略")
    device_alias: Optional[str] = Field(default=None, description="设备别名")
    display_name: Optional[str] = Field(default=None, description="上位机显示名称")

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
