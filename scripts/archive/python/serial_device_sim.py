import time
import serial

PORT = "/dev/ttys009"   # 设备端虚拟串口
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=1)
print(f"设备端已打开 {PORT}，开始周期发送帧...")

device_code = "SENSOR001"

try:
    i = 0
    while True:
        voltage = 220.0
        current = 5.0 + i * 0.1
        power = voltage * current / 1000.0
        energy = 1000.0 + i * 10

        frame = f"DEV={device_code};V={voltage:.1f};I={current:.2f};P={power:.3f};E={energy:.1f}\r\n"
        ser.write(frame.encode("utf-8"))
        print("发送帧:", frame.strip())
        i += 1
        time.sleep(2)  # 每 2 秒一帧
except KeyboardInterrupt:
    print("设备模拟结束")
finally:
    ser.close()