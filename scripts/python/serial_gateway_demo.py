import serial

PORT = "/dev/ttys008"
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=1)
print(f"网关端已打开 {PORT}，等待帧...")

try:
    while True:
        line = ser.readline()
        if not line:
            continue
        text = line.decode("utf-8", errors="replace").strip()
        print("收到原始行:", text)

        # 解析：按 ; 分割，再按 = 分割
        fields = {}
        for part in text.split(";"):
            if "=" in part:
                k, v = part.split("=", 1)
                fields[k] = v

        device_code = fields.get("DEV")
        voltage = float(fields.get("V", 0) or 0)
        current = float(fields.get("I", 0) or 0)
        power   = float(fields.get("P", 0) or 0)
        energy  = float(fields.get("E", 0) or 0)

        print("解析结果:",
              device_code, voltage, current, power, energy)
except KeyboardInterrupt:
    print("网关端结束")
finally:
    ser.close()