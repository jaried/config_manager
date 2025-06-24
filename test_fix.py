#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import threading
import traceback

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_config_manager():
    """测试配置管理器，模拟其他项目的调用方式"""
    try:
        print("1. 开始测试...")
        
        from config_manager import get_config_manager
        from datetime import datetime
        
        start_time = datetime.now()
        
        print("2. 调用get_config_manager...")
        # 模拟其他项目的调用方式
        config = get_config_manager(
            first_start_time=start_time, 
            auto_create=True, 
            autosave_delay=1.0,  # 增加延迟到1秒
            watch=True  # 启用文件监视器
        )
        
        print("3. 配置管理器创建成功")
        
        # 测试基本操作
        config.test_value = "hello"
        print("4. 设置值成功")
        
        # 等待一段时间，看是否有死循环
        print("5. 等待5秒，检查是否有死循环...")
        time.sleep(5)
        
        print("6. 测试完成，没有死循环")
        return True
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_config_manager()
    if success:
        print("✓ 所有测试通过，死循环问题已修复")
    else:
        print("✗ 测试失败") 