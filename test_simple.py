#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from config_manager import get_config_manager
    print("✓ 导入成功")
    
    # 测试基本功能
    cfg = get_config_manager('test.yaml', auto_create=True)
    print("✓ 创建成功")
    
    # 测试基本操作
    cfg.test_value = "hello"
    print("✓ 设置值成功")
    
    print("✓ 所有测试通过")
    
except Exception as e:
    print(f"✗ 错误: {e}")
    import traceback
    traceback.print_exc() 