#!/usr/bin/env python3
"""
虚拟串口对通讯演示
在一对 socat 创建的 PTY 上，用两个终端分别运行「读」和「写」，验证二者能通讯。

用法（先在一个终端运行 socat，再开两个终端）：
  # 终端 1：读端，会阻塞等待数据
  python scripts/python/serial_pair_demo.py read /dev/ttys008

  # 终端 2：写端，发几行后退出
  python scripts/python/serial_pair_demo.py write /dev/ttys009

PTY 设备名以你 socat 输出的为准（如 ttys008 / ttys009）。
"""
import argparse
import sys

def main():
    ap = argparse.ArgumentParser(description="虚拟串口对：读端或写端")
    ap.add_argument("mode", choices=["read", "write"], help="read=只读一端, write=只写一端")
    ap.add_argument("port", help="串口设备路径，如 /dev/ttys008")
    ap.add_argument("--baud", type=int, default=9600, help="波特率（PTY 下无实际作用）")
    ap.add_argument("--lines", type=int, default=5, help="write 模式时发送几行后退出")
    args = ap.parse_args()

    try:
        import serial
    except ImportError:
        print("请先安装: pip install pyserial")
        sys.exit(1)

    try:
        ser = serial.Serial(args.port, args.baud, timeout=2)
    except Exception as e:
        print(f"打开 {args.port} 失败: {e}")
        sys.exit(1)

    if args.mode == "read":
        print(f"读端已打开 {args.port}，等待数据（Ctrl+C 退出）...")
        n = 0
        try:
            while True:
                line = ser.readline()
                if line:
                    try:
                        text = line.decode("utf-8", errors="replace").strip()
                        n += 1
                        print(f"  [{n}] {text}")
                    except Exception:
                        print(f"  [{n}] (hex) {line.hex()}")
        except KeyboardInterrupt:
            print("\n读端已退出")
        finally:
            ser.close()

    else:  # write
        print(f"写端已打开 {args.port}，发送 {args.lines} 行后退出...")
        try:
            for i in range(1, args.lines + 1):
                msg = f"VOLTAGE=220.{i}\r\n"
                ser.write(msg.encode("utf-8"))
                print(f"  已发送: {msg.strip()}")
            print("写端发送完成，退出")
        finally:
            ser.close()

if __name__ == "__main__":
    main()
