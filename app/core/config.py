import json
import os

# 自动获取项目根目录 (即 main.py 所在的文件夹)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 获取三次父目录 以保证其可移植性
CONFIG_PATH = os.path.join(BASE_DIR, "config", "settings.json")

def load_thresholds():
    """从 config/settings.json 加载报警阈值配置"""
    try:
        # 检查文件是否存在
        if not os.path.exists(CONFIG_PATH):
            print(f"⚠️ 配置文件未找到: {CONFIG_PATH}")
            return {}
            
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 配置文件读取失败: {e}")
        return {}