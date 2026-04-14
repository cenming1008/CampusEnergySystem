#!/usr/bin/env python3
"""
向指定 SVG（静止无功发生器）设备写入模拟遥测数据。

同时写入两张表：
  - svg_telemetry  : 三相电压/电流、无功输出、状态位、故障位、温度等
  - energy_data    : reactive_power、power_factor、voltage、current（供监控实时总览使用）

用法：
  # 查看当前系统中的 SVG 设备列表
  python scripts/python/send_svg_telemetry.py --list

  # 向 device_id=1 的设备发送一条数据
  python scripts/python/send_svg_telemetry.py --id 1

  # 持续发送 30 条，每隔 5 秒一条（模拟实时上报）
  python scripts/python/send_svg_telemetry.py --id 1 --loop 30 --interval 5

  # 补写过去 2 小时的历史数据（每分钟一条，共 120 条）
  python scripts/python/send_svg_telemetry.py --id 1 --backfill 120 --backfill-step 60
"""

import argparse
import math
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import Session, select

from app.core.database import engine
from app.models.tables import Alarm, Device, DeviceControlLog, EnergyData, SVGAssetProfile, SVGTelemetry
from app.services.ingestion_health_service import IngestionHealthService


# ──────────────────────────────────────────────────────────────────────────────
# 数据生成
# ──────────────────────────────────────────────────────────────────────────────

def _wave(base: float, amplitude: float, t: float, period: float = 60.0) -> float:
    """生成带轻微噪声的正弦波形值。"""
    return base + amplitude * math.sin(2 * math.pi * t / period) + random.uniform(-amplitude * 0.1, amplitude * 0.1)


def generate_svg_telemetry(device_id: int, timestamp: datetime, tick: int = 0) -> SVGTelemetry:
    """根据 tick 生成一条逼真的 SVG 遥测记录。"""
    t = float(tick)

    # 三相电压（模拟 380V 线电压，轻微不平衡）
    va = _wave(220.0, 3.0, t, 120)
    vb = _wave(219.5, 3.2, t + 40, 120)
    vc = _wave(220.5, 2.8, t + 80, 120)

    # 三相电流（补偿电流，模拟无功需求变化）
    ia = _wave(48.0, 8.0, t, 90)
    ib = _wave(47.5, 8.5, t + 30, 90)
    ic = _wave(48.5, 7.8, t + 60, 90)

    # 无功输出随负荷周期变化
    reactive_output = _wave(320.0, 40.0, t, 90)
    capacity_util = min(100.0, max(0.0, _wave(65.0, 15.0, t, 90)))
    output_direction = "capacitive" if reactive_output >= 0 else "inductive"

    # 功率因数（补偿后维持在 0.94~0.99）
    pf = min(0.999, max(0.90, _wave(0.97, 0.025, t, 90)))

    # 温度
    cabinet_temp = _wave(38.0, 5.0, t, 180)
    module_temp = _wave(45.0, 6.0, t + 20, 180)
    igbt_temp = _wave(52.0, 7.0, t + 40, 180)
    heatsink_temp = _wave(42.0, 5.5, t + 10, 180)
    dc_bus_voltage = _wave(680.0, 10.0, t, 60)

    return SVGTelemetry(
        device_id=device_id,
        timestamp=timestamp,
        # 三相电压
        voltage_a=round(va, 2),
        voltage_b=round(vb, 2),
        voltage_c=round(vc, 2),
        # 三相电流
        current_a=round(ia, 2),
        current_b=round(ib, 2),
        current_c=round(ic, 2),
        # 基本量测
        frequency=round(_wave(50.0, 0.05, t, 300), 3),
        svg_reactive_output=round(reactive_output, 1),
        capacity_utilization=round(capacity_util, 1),
        output_direction=output_direction,
        # 状态位（正常运行：auto=True, run=True, breaker=True, module/fan/comm OK）
        run_status=True,
        stop_status=False,
        auto_mode=True,
        local_mode=False,
        breaker_status=True,
        module_status=True,
        fan_status=True,
        comm_status=True,
        # 故障位（无故障）
        overvoltage_fault=False,
        undervoltage_fault=False,
        overcurrent_fault=False,
        overtemp_fault=False,
        module_fault=False,
        fan_fault=False,
        comm_fault=False,
        current_fault_code=None,
        current_alarm_code=None,
        # 温度与内部量
        cabinet_temp=round(cabinet_temp, 1),
        module_temp=round(module_temp, 1),
        igbt_temp=round(igbt_temp, 1),
        dc_bus_voltage=round(dc_bus_voltage, 1),
        heatsink_temp=round(heatsink_temp, 1),
    )


def generate_energy_data(device: Device, timestamp: datetime, tick: int = 0) -> EnergyData:
    """生成对应的 energy_data 记录（供监控实时总览使用）。"""
    t = float(tick)

    reactive_power = _wave(320.0, 40.0, t, 90)
    pf = min(0.999, max(0.90, _wave(0.97, 0.025, t, 90)))
    voltage = _wave(220.0, 3.0, t, 120)
    current = _wave(48.0, 8.0, t, 90)
    flow_rate = abs(reactive_power)  # 有功功率近似（演示用）
    consumption_delta = flow_rate * (1 / 3600)  # 假设按秒累积

    return EnergyData(
        device_id=device.id,
        timestamp=timestamp,
        energy_type=device.energy_type or "electricity",
        consumption=round(consumption_delta, 4),
        flow_rate=round(flow_rate, 2),
        voltage=round(voltage, 2),
        current=round(current, 2),
        power_factor=round(pf, 4),
        reactive_power=round(reactive_power, 2),
        temperature=round(_wave(38.0, 5.0, t, 180), 1),
    )


# ──────────────────────────────────────────────────────────────────────────────
# 运行事件模拟
# ──────────────────────────────────────────────────────────────────────────────

# 全局状态：记录上一次的补偿组数，用于检测投切变化
_prev_level: int = -1
_prev_pf_ok: bool = True


def maybe_emit_events(
    session: Session,
    device: Device,
    tel: SVGTelemetry,
    ed: EnergyData,
    timestamp: datetime,
) -> None:
    """根据本次遥测值，按概率或阈值触发模拟运行事件（控制日志 / 告警）。"""
    global _prev_level, _prev_pf_ok

    util = tel.capacity_utilization or 0.0
    pf = ed.power_factor or 0.0
    total_levels = 8  # 与前端 compensationLevelTotal 保持一致

    current_level = min(total_levels, max(0, round(util / 100 * total_levels)))

    # ── 1. 补偿组投切事件（控制日志）──────────────────────────────────────────
    if _prev_level >= 0 and current_level != _prev_level:
        # 投入
        if current_level > _prev_level:
            for grp in range(_prev_level + 1, current_level + 1):
                log = DeviceControlLog(
                    device_id=device.id,
                    action="start",
                    target_status=True,
                    previous_status=False,
                    operator="EMS 自动策略",
                    command_source="system",
                    result="success",
                    reason=f"自动投入第 {grp} 组补偿（利用率 {util:.1f}%）",
                    created_at=timestamp,
                )
                session.add(log)
        # 切除
        else:
            for grp in range(current_level + 1, _prev_level + 1):
                log = DeviceControlLog(
                    device_id=device.id,
                    action="stop",
                    target_status=False,
                    previous_status=True,
                    operator="EMS 自动策略",
                    command_source="system",
                    result="success",
                    reason=f"自动切除第 {grp} 组补偿（利用率回落至 {util:.1f}%）",
                    created_at=timestamp,
                )
                session.add(log)

    _prev_level = current_level

    # ── 2. 过载告警（利用率 > 90%）────────────────────────────────────────────
    if util > 90.0:
        alarm = Alarm(
            device_id=device.id,
            instance_key=f"svg_overload_{device.id}",
            message=f"补偿容量利用率过高（{util:.1f}%），接近额定上限",
            severity="warning",
            category="threshold",
            source="telemetry",
            timestamp=timestamp,
            last_seen_at=timestamp,
            is_resolved=False,
        )
        session.add(alarm)

    # ── 3. 功率因数恢复事件（PF 从低于 0.93 回升到 ≥ 0.95）─────────────────
    pf_ok = pf >= 0.95
    if not _prev_pf_ok and pf_ok:
        alarm = Alarm(
            device_id=device.id,
            instance_key=None,
            message="功率因数恢复正常",
            severity="info",
            category="recovery",
            source="telemetry",
            timestamp=timestamp,
            is_resolved=True,
            resolved_at=timestamp,
            resolved_by="系统自动",
            handling_note=f"PF 回升至 {pf:.4f}，已达目标区间",
        )
        session.add(alarm)
    elif pf < 0.93 and _prev_pf_ok:
        alarm = Alarm(
            device_id=device.id,
            instance_key=f"svg_low_pf_{device.id}",
            message=f"功率因数偏低（PF={pf:.4f}），低于告警阈值 0.93",
            severity="warning",
            category="threshold",
            source="telemetry",
            timestamp=timestamp,
            last_seen_at=timestamp,
            is_resolved=False,
        )
        session.add(alarm)

    _prev_pf_ok = pf_ok


# ──────────────────────────────────────────────────────────────────────────────
# 写入逻辑
# ──────────────────────────────────────────────────────────────────────────────

def upsert_telemetry(session: Session, tel: SVGTelemetry) -> None:
    """写入 svg_telemetry，主键冲突则覆盖更新。"""
    existing = session.get(SVGTelemetry, (tel.device_id, tel.timestamp))
    if existing:
        for field, val in tel.model_dump(exclude={"device_id", "timestamp"}).items():
            setattr(existing, field, val)
        session.add(existing)
    else:
        session.add(tel)


def upsert_energy(session: Session, ed: EnergyData) -> None:
    """写入 energy_data，主键冲突则覆盖更新。"""
    existing = session.exec(
        select(EnergyData).where(
            EnergyData.device_id == ed.device_id,
            EnergyData.timestamp == ed.timestamp,
        )
    ).first()
    if existing:
        for field, val in ed.model_dump(exclude={"device_id", "timestamp"}).items():
            setattr(existing, field, val)
        session.add(existing)
    else:
        session.add(ed)


def ensure_asset_profile(session: Session, device: Device) -> None:
    """若 svg_asset_profile 不存在则自动创建一条模拟运维档案。"""
    existing = session.exec(
        select(SVGAssetProfile).where(SVGAssetProfile.device_id == device.id)
    ).first()
    if existing:
        return

    from datetime import date
    profile = SVGAssetProfile(
        device_id=device.id,
        model_number="SVG-400/10-T3",
        rated_voltage=380.0,
        rated_frequency=50.0,
        comm_address=f"MB-{device.id:03d}",
        software_version="V3.2.1",
        hardware_version="HW-2024A",
        protocol_version="Modbus-RTU",
        module_count=8,
        single_module_capacity=50.0,
        device_label_zh=device.name or f"SVG补偿器{device.id}",
        asset_number=f"FA-SVG-{device.id:04d}",
        fixed_asset_code=f"GD-2024-{device.id:04d}",
        asset_group="无功补偿设备",
        distribution_room="1号配电室",
        distribution_cabinet="MCC-3柜",
        circuit="SVG专用回路",
        area="动力区",
        building="综合能源楼",
        install_date=date(2024, 3, 15),
        commission_date=date(2024, 4, 1),
        field_number=f"SVG-F{device.id:02d}",
        om_responsible="李工",
        inspection_responsible="王工",
        department="能源管理部",
        management_unit="园区运维中心",
        contact_phone="021-88888888",
        warranty_expiry=date(2027, 4, 1),
        maintenance_cycle_days=90,
        device_group="无功补偿组",
        device_tree_level="三级",
        monitor_screen_position="配电室SVG监控屏",
        alarm_policy="standard",
        device_alias=f"SVG#{device.id}",
        display_name=device.name,
    )
    session.add(profile)
    session.commit()
    print(f"  ✅ 已自动创建 SVG 运维档案（device_id={device.id}）")


def send_one(session: Session, device: Device, timestamp: datetime, tick: int) -> None:
    tel = generate_svg_telemetry(device.id, timestamp, tick)
    ed = generate_energy_data(device, timestamp, tick)
    upsert_telemetry(session, tel)
    upsert_energy(session, ed)
    maybe_emit_events(session, device, tel, ed, timestamp)
    IngestionHealthService.mark_ingestion_success(session, device.id, timestamp)
    session.commit()
    print(
        f"  [{timestamp.strftime('%H:%M:%S')}] "
        f"Va={tel.voltage_a}V  Vb={tel.voltage_b}V  Vc={tel.voltage_c}V  "
        f"Ia={tel.current_a}A  Ib={tel.current_b}A  Ic={tel.current_c}A  "
        f"Q={tel.svg_reactive_output}kVAR  PF={ed.power_factor}  "
        f"cabinet={tel.cabinet_temp}°C"
    )


# ──────────────────────────────────────────────────────────────────────────────
# 命令行入口
# ──────────────────────────────────────────────────────────────────────────────

def list_svg_devices(session: Session) -> None:
    devices = session.exec(
        select(Device).where(Device.device_type == "svg")
    ).all()
    if not devices:
        print("⚠️  系统中尚无 svg 类型的设备。")
        return
    print(f"\n{'ID':>4}  {'序列号':<16}  {'名称':<20}  {'位置':<20}  {'额定容量'}")
    print("-" * 75)
    for d in devices:
        print(f"{d.id:>4}  {d.sn or '--':<16}  {d.name:<20}  {d.location or '--':<20}  {d.rated_capacity or '--'} kVAR")
    print()


def main() -> None:
    ap = argparse.ArgumentParser(description="向 SVG 设备写入模拟遥测数据")
    ap.add_argument("--list", action="store_true", help="列出系统中所有 SVG 设备")
    ap.add_argument("--id", type=int, dest="device_id", help="目标设备 ID")
    ap.add_argument("--sn", dest="device_sn", help="目标设备序列号（与 --id 二选一）")
    ap.add_argument("--loop", type=int, default=1, help="发送条数（默认 1，0=无限循环）")
    ap.add_argument("--interval", type=float, default=3.0, help="连续发送时的间隔秒数（默认 3）")
    ap.add_argument("--backfill", type=int, default=0, help="补写历史条数（从当前时间向前）")
    ap.add_argument("--backfill-step", type=int, default=60, help="补写历史时每条的时间间隔（秒，默认 60）")
    args = ap.parse_args()

    with Session(engine) as session:
        if args.list:
            list_svg_devices(session)
            return

        # 定位设备
        if args.device_id:
            device = session.get(Device, args.device_id)
        elif args.device_sn:
            device = session.exec(select(Device).where(Device.sn == args.device_sn)).first()
        else:
            print("❌ 请指定 --id 或 --sn，或使用 --list 查看可用设备")
            ap.print_help()
            return

        if not device:
            print(f"❌ 设备未找到")
            return
        if device.device_type != "svg":
            print(f"⚠️  设备 {device.name}（{device.device_type}）不是 SVG 类型，仍继续写入...")

        print(f"\n▶  目标设备: [{device.id}] {device.name}  SN={device.sn}  额定容量={device.rated_capacity} kVAR")
        ensure_asset_profile(session, device)

        # 补写历史数据
        if args.backfill > 0:
            print(f"\n📅 补写历史数据：{args.backfill} 条，步长 {args.backfill_step}s")
            base_time = datetime.now() - timedelta(seconds=args.backfill * args.backfill_step)
            for i in range(args.backfill):
                ts = base_time + timedelta(seconds=i * args.backfill_step)
                send_one(session, device, ts, tick=i)
            print(f"✅ 补写完成，共写入 {args.backfill} 条历史记录\n")
            return

        # 实时发送
        count = 0
        infinite = args.loop == 0
        total = args.loop
        print(f"\n📡 开始发送{'（无限循环，Ctrl+C 停止）' if infinite else f'，共 {total} 条'}\n")
        try:
            while infinite or count < total:
                send_one(session, device, datetime.now(), tick=count)
                count += 1
                if infinite or count < total:
                    time.sleep(args.interval)
        except KeyboardInterrupt:
            print(f"\n⏹  已停止，共发送 {count} 条")
            return

        print(f"\n✅ 完成，共发送 {count} 条\n")


if __name__ == "__main__":
    main()
