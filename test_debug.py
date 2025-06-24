#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import traceback

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    print("1. 开始导入...")
    from config_manager import get_config_manager
    print("2. 导入成功")
    
    print("3. 开始创建ConfigManager...")
    # 直接创建ConfigManager实例，跳过get_config_manager函数
    from config_manager.config_manager import ConfigManager
    
    print("4. 创建实例...")
    cfg = ConfigManager('test.yaml', auto_create=True)
    print("5. 实例创建成功")
    
    print("6. 测试基本操作...")
    cfg.test_value = "hello"
    print("7. 设置值成功")
    
    print("✓ 所有测试通过")
    
except Exception as e:
    print(f"✗ 错误: {e}")
    traceback.print_exc() 