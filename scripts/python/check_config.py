#!/usr/bin/env python3
"""
配置检查脚本
用于验证配置是否正确加载和设置
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from app.core.settings import settings
    
    print("=" * 60)
    print("📋 配置检查报告")
    print("=" * 60)
    
    # 检查必需配置
    print("\n✅ 必需配置项：")
    required_ok = True
    
    if not settings.database_url:
        print("  ❌ DATABASE_URL: 未设置")
        required_ok = False
    else:
        print(f"  ✅ DATABASE_URL: {settings.database_url[:50]}...")
    
    if not settings.secret_key:
        print("  ❌ SECRET_KEY: 未设置")
        required_ok = False
    elif settings.secret_key == "campus-energy-system-secret-key-change-me":
        print("  ⚠️  SECRET_KEY: 使用默认值（生产环境请修改！）")
    elif len(settings.secret_key) < 32:
        print(f"  ⚠️  SECRET_KEY: 长度不足32字符（当前: {len(settings.secret_key)}）")
    else:
        print(f"  ✅ SECRET_KEY: 已设置（长度: {len(settings.secret_key)}）")
    
    # 显示其他重要配置
    print("\n📊 其他配置项：")
    print(f"  应用名称: {settings.app_name}")
    print(f"  应用版本: {settings.app_version}")
    print(f"  调试模式: {settings.debug}")
    print(f"  服务器地址: {settings.host}:{settings.port}")
    print(f"  工作进程数: {settings.workers}")
    print(f"  热重载: {settings.reload}")
    print(f"  Redis URL: {settings.redis_url}")
    print(f"  MQTT Broker: {settings.mqtt_broker}:{settings.mqtt_port}")
    print(f"  CORS来源: {settings.cors_origins}")
    print(f"  日志级别: {settings.log_level}")
    
    # 总结
    print("\n" + "=" * 60)
    if required_ok:
        print("✅ 配置检查通过！")
        sys.exit(0)
    else:
        print("❌ 配置检查失败：缺少必需配置项")
        print("\n💡 提示：")
        print("  1. 复制 env.example 为 .env")
        print("  2. 编辑 .env 文件，设置必需配置项")
        print("  3. 重新运行此脚本验证")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ 配置加载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
