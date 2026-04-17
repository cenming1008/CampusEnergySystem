#!/usr/bin/env python3
"""
Modbus TCP 单次读取测试（第二步调试用）
不连 MQTT，只验证能否从设备读到寄存器值。

用法：
  pip install pymodbus
  python scripts/python/test_modbus_tcp.py --host 192.168.1.100 [--port 502] [--slave 1] [--addr 0] [--count 4]
"""
import argparse

def main():
    ap = argparse.ArgumentParser(description="Modbus TCP 读寄存器测试")
    ap.add_argument("--host", required=True, help="设备 IP")
    ap.add_argument("--port", type=int, default=502, help="端口，默认 502")
    ap.add_argument("--slave", type=int, default=1, help="从站地址，默认 1")
    ap.add_argument("--addr", type=int, default=0, help="起始寄存器地址，默认 0")
    ap.add_argument("--count", type=int, default=4, help="读几个寄存器（float32 要 2 个），默认 4")
    args = ap.parse_args()

    try:
        from pymodbus.client import ModbusTcpClient
    except ImportError:
        print("请先安装: pip install pymodbus")
        return

    print(f"连接 {args.host}:{args.port} 从站={args.slave} 地址={args.addr} 数量={args.count} ...")
    client = ModbusTcpClient(args.host, port=args.port)
    if not client.connect():
        print("❌ 连接失败，请检查 IP、端口、网络")
        return
    result = client.read_holding_registers(address=args.addr, count=args.count, slave=args.slave)
    client.close()
    if result.isError():
        print(f"❌ 读取失败: {result}")
        return
    print(f"✅ 原始寄存器值: {result.registers}")
    print("   若为 float32，需连续 2 个寄存器，按设备手册的字节序解码。")
    print("   把正确的 address/count/slave 填到 device_gateway.py 的 DEVICE_CONFIG 里即可。")


if __name__ == "__main__":
    main()
