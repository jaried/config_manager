# src/tools/verify_imports.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from config_manager.config_manager import ConfigManager

    print("✓ 导入成功")

    # 测试 build 方法
    test_dict = {'key': 'value'}
    result = ConfigManager.build(test_dict)
    print(f"✓ ConfigManager.build 成功，结果类型: {type(result)}")

    print("🎉 所有验证通过！")

except Exception as e:
    print(f"❌ 验证失败: {e}")
    import traceback

    traceback.print_exc()

