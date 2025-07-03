#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试调用链追踪器
"""

import os
import sys

# 添加src路径
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from config_manager.core.call_chain import CallChainTracker

def test_call_chain():
    """测试调用链追踪器"""
    print("=== 测试调用链追踪器 ===")
    
    tracker = CallChainTracker()
    
    # 测试获取调用链
    chain = tracker.get_call_chain()
    print(f"调用链: {chain}")
    
    # 测试环境信息
    env_info = tracker._get_environment_info()
    print(f"环境信息: {env_info}")
    
    # 测试详细调用信息
    try:
        debug_info = tracker.get_detailed_call_info()
        print(f"详细信息: {debug_info}")
    except Exception as e:
        print(f"获取详细信息失败: {e}")

if __name__ == "__main__":
    test_call_chain() 