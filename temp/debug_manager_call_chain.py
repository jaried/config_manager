#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试manager中的调用链使用
"""

import os
import sys

# 添加src路径
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from config_manager.core.call_chain import CallChainTracker
from config_manager.logger.minimal_logger import info

def test_manager_call_chain():
    """测试manager中的调用链使用"""
    print("=== 测试manager中的调用链使用 ===")
    
    tracker = CallChainTracker()
    
    # 模拟manager中的调用
    try:
        test_chain = tracker.get_call_chain()
        print(f"原始调用链: {test_chain}")
        
        # 模拟manager中的日志调用
        info("初始化时调用链: {}", test_chain)
        
    except Exception as e:
        print(f"调用链获取失败: {e}")

if __name__ == "__main__":
    test_manager_call_chain() 