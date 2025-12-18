import requests

API_URL = "http://127.0.0.1:8088/devices/"

# 完整的 10 种煤矿典型设备
new_devices = [
    # 基础设备 (你之前可能已经加过 1-5 了，重复加也没事，代码会跳过或报错忽略)
    {"id": 1, "name": "智能电表", "sn": "METER-001", "device_type": "meter", "location": "总配电室"},
    {"id": 2, "name": "主通风机", "sn": "FAN-MAIN-01", "device_type": "fan", "location": "回风井"},
    {"id": 3, "name": "中央排水泵", "sn": "PUMP-MAIN-01", "device_type": "pump", "location": "井底车场"},
    {"id": 4, "name": "矿用变压器", "sn": "TRANS-001", "device_type": "transformer", "location": "变电所"},
    {"id": 5, "name": "瓦斯抽放泵", "sn": "GAS-001", "device_type": "pump", "location": "瓦斯泵站"},
    
    # --- 新增的进阶设备 ---
    {"id": 6, "name": "MG500采煤机", "sn": "SHEARER-001", "device_type": "heavy_machine", "location": "1201工作面"},
    {"id": 7, "name": "皮带输送机", "sn": "BELT-001", "device_type": "conveyor", "location": "主斜井"},
    {"id": 8, "name": "副井提升机", "sn": "HOIST-001", "device_type": "hoist", "location": "副井"},
    {"id": 9, "name": "空气压缩机", "sn": "AIR-001", "device_type": "compressor", "location": "压风机房"},
    {"id": 10, "name": "刮板输送机", "sn": "SCRAPER-001", "device_type": "conveyor", "location": "1201工作面"}
]

def register_devices():
    print("--- 开始录入全套煤矿设备 ---")
    for dev in new_devices:
        try:
            # 注意：我在上面加上了 id 字段，为了确保和 settings.json 对应
            # 但通常数据库 ID 是自动生成的。为了演示方便，我们这里依赖名字或顺序
            # 最好是先清空数据库再跑，或者手动去数据库核对 ID。
            
            # 这里我们去掉 id 字段发送，让数据库自动生成，
            # *关键* 是要按照顺序录入，这样 采煤机 就会是 ID 6
            dev_data = dev.copy()
            if "id" in dev_data:
                del dev_data["id"] 

            response = requests.post(API_URL, json=dev_data)
            if response.status_code == 200:
                data = response.json()
                print(f"[成功] {data['name']} 已生成 -> ID: {data['id']}")
            else:
                print(f"[跳过] {dev['name']} 可能已存在")
        except Exception as e:
            print(f"[错误] {e}")

if __name__ == "__main__":
    register_devices()