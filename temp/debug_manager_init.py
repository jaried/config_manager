#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试manager初始化过程
"""

import os
import sys

# 添加src路径
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from config_manager.core.call_chain import CallChainTracker
from config_manager.logger.minimal_logger import info

def test_manager_init():
    """测试manager初始化过程"""
    print("=== 测试manager初始化过程 ===")
    
    # 模拟manager初始化
    tracker = CallChainTracker()
    
    # 在初始化时测试调用链
    try:
        test_chain = tracker.get_call_chain()
        print(f"初始化时调用链: {test_chain}")
        
        # 模拟manager中的日志调用
        info("初始化时调用链: {}", test_chain)
        
        # 检查调用链是否为空
        if not test_chain or test_chain == "{}":
            print("警告：调用链为空或格式错误")
            
            # 尝试获取详细信息
            try:
                debug_info = tracker.get_detailed_call_info()
                print(f"详细信息: {debug_info}")
            except Exception as e:
                print(f"获取详细信息失败: {e}")
        
    except Exception as e:
        print(f"调用链获取失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_manager_init() 