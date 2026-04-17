#!/usr/bin/env python3
"""
HTTP 设备单次请求测试（第二步调试用）
不连 MQTT，只验证能否从设备 API 拿到 JSON。

用法：
  pip install requests
  python scripts/python/test_http_device.py --url "http://192.168.1.101/api/data"
"""
import argparse
import json


def main():
    ap = argparse.ArgumentParser(description="HTTP 设备 API 测试")
    ap.add_argument("--url", required=True, help="设备数据接口 URL")
    ap.add_argument("--timeout", type=int, default=5, help="超时秒数")
    args = ap.parse_args()

    try:
        import requests
    except ImportError:
        print("请先安装: pip install requests")
        return

    print(f"请求 GET {args.url} ...")
    try:
        r = requests.get(args.url, timeout=args.timeout)
        print(f"状态码: {r.status_code}")
        if r.status_code != 200:
            print(r.text[:500])
            return
        data = r.json()
        print("✅ 返回 JSON（已格式化）:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("\n请根据字段名在 device_gateway.py 的 field_mapping 里做映射，例如:")
        print('  "flow_rate": "设备返回的流量字段名", "consumption": "设备返回的累计量字段名"')
    except Exception as e:
        print(f"❌ 请求失败: {e}")


if __name__ == "__main__":
    main()
