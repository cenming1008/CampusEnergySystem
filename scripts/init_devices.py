import requests
import sys

# 配置基础地址
BASE_URL = "http://127.0.0.1:8088"
LOGIN_URL = f"{BASE_URL}/auth/login"
DEVICES_URL = f"{BASE_URL}/devices/"

# 管理员账号 
ADMIN_USER = "admin"
ADMIN_PASS = "123456"

# 完整的 10 种煤矿典型设备
new_devices = [
    # 基础设备
    {"id": 1, "name": "智能电表", "sn": "METER-001", "device_type": "meter", "location": "总配电室"},
    {"id": 2, "name": "主通风机", "sn": "FAN-MAIN-01", "device_type": "fan", "location": "回风井"},
    {"id": 3, "name": "中央排水泵", "sn": "PUMP-MAIN-01", "device_type": "pump", "location": "井底车场"},
    {"id": 4, "name": "矿用变压器", "sn": "TRANS-001", "device_type": "transformer", "location": "变电所"},
    {"id": 5, "name": "瓦斯抽放泵", "sn": "GAS-001", "device_type": "pump", "location": "瓦斯泵站"},
    
    # 进阶设备
    {"id": 6, "name": "MG500采煤机", "sn": "SHEARER-001", "device_type": "heavy_machine", "location": "1201工作面"},
    {"id": 7, "name": "皮带输送机", "sn": "BELT-001", "device_type": "conveyor", "location": "主斜井"},
    {"id": 8, "name": "副井提升机", "sn": "HOIST-001", "device_type": "hoist", "location": "副井"},
    {"id": 9, "name": "空气压缩机", "sn": "AIR-001", "device_type": "compressor", "location": "压风机房"},
    {"id": 10, "name": "刮板输送机", "sn": "SCRAPER-001", "device_type": "conveyor", "location": "1201工作面"}
]

def get_access_token():
    """先登录获取 Token"""
    print(f"🔑 正在尝试登录 ({ADMIN_USER})...")
    try:
        # OAuth2 标准表单格式
        payload = {
            "username": ADMIN_USER,
            "password": ADMIN_PASS
        }
        response = requests.post(LOGIN_URL, data=payload)
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print("✅ 登录成功，获取到 Token！")
            return token
        else:
            print(f"❌ 登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 连接服务器失败: {e}")
        return None

def register_devices():
    # 1. 第一步：拿令牌
    token = get_access_token()
    if not token:
        print("🚫 无法继续：未获取到授权。请检查后端是否启动，或账号密码是否正确。")
        return

    # 2. 准备请求头 (Header)
    headers = {
        "Authorization": f"Bearer {token}"  # 👈 关键：这就是通行证
    }

    print("\n--- 开始通过 API 录入设备 ---")
    for dev in new_devices:
        try:
            # 去掉 id 发送，让数据库自增 (前提是已经 Reset 过)
            dev_data = dev.copy()
            if "id" in dev_data:
                del dev_data["id"] 

            # 3. 发送请求时带上 headers
            response = requests.post(DEVICES_URL, json=dev_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"[成功] {data['name']} 已生成 -> ID: {data['id']}")
            elif response.status_code == 400:
                # 你的后端在 SN 重复时返回 400 并直接抛错，这里简单捕获一下
                print(f"[跳过] {dev['name']} 可能已存在 (SN重复)")
            else:
                print(f"[失败] {dev['name']} 状态码: {response.status_code} | {response.text}")
                
        except Exception as e:
            print(f"[错误] {e}")

if __name__ == "__main__":
    register_devices()