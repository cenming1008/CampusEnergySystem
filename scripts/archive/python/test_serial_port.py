#!/usr/bin/env python3
"""
串口单次读取测试（第二步调试用）
不连 MQTT，只验证串口能否打开、能否收到数据。

用法：
  pip install pyserial
  python scripts/python/test_serial_port.py --port /dev/cu.usbserial-xxx [--baud 9600] [--lines 5]
  Mac 查端口: ls /dev/cu.*   Linux: ls /dev/ttyUSB*
"""
import argparse


def main():
    ap = argparse.ArgumentParser(description="串口读取测试")
    ap.add_argument("--port", required=True, help="串口设备路径，如 /dev/cu.usbserial-xxx 或 /dev/ttyUSB0")
    ap.add_argument("--baud", type=int, default=9600, help="波特率，默认 9600")
    ap.add_argument("--lines", type=int, default=5, help="读几行后退出，默认 5")
    args = ap.parse_args()

    try:
        import serial
    except ImportError:
        print("请先安装: pip install pyserial")
        return

    print(f"打开 {args.port} @ {args.baud}，读 {args.lines} 行...")
    try:
        ser = serial.Serial(args.port, args.baud, timeout=2)
    except Exception as e:
        print(f"❌ 打开串口失败: {e}")
        print("   请检查: 端口是否插好、路径是否正确、权限 (sudo chmod 666 设备路径)")
        return
    n = 0
    while n < args.lines:
        line = ser.readline()
        if line:
            try:
                text = line.decode("utf-8", errors="replace").strip()
                print(f"   [{n+1}] {text}")
            except Exception:
                print(f"   [{n+1}] (hex) {line.hex()}")
            n += 1
    ser.close()
    print("✅ 串口能收到数据。根据设备协议解析每行/每帧，再在 device_gateway.py 里实现 protocol: serial 的读取与 JSON 组装。")

if __name__ == "__main__":
    main()
