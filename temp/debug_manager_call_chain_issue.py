#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试manager中调用链追踪器的问题
"""

import os
import sys
import tempfile

# 添加src路径
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from config_manager.core.call_chain import CallChainTracker
from config_manager.logger.minimal_logger import info

def test_manager_call_chain_issue():
    """测试manager中调用链追踪器的问题"""
    print("=== 测试manager中调用链追踪器的问题 ===")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 设置调用链开关为True
        import config_manager.config_manager as cm_module
        original_switch = cm_module.ENABLE_CALL_CHAIN_DISPLAY
        cm_module.ENABLE_CALL_CHAIN_DISPLAY = True
        
        print(f"调用链开关状态: {cm_module.ENABLE_CALL_CHAIN_DISPLAY}")
        
        # 在get_config_manager级别创建调用链追踪器
        from config_manager.core.call_chain import CallChainTracker
        call_chain_tracker = CallChainTracker()
        
        # 测试调用链追踪器是否正常工作
        test_chain = call_chain_tracker.get_call_chain()
        print(f"get_config_manager级别的调用链: {test_chain}")
        
        # 模拟manager初始化过程
        from config_manager.core.manager import ConfigManagerCore
        manager = ConfigManagerCore()
        
        # 手动设置调用链追踪器
        manager._call_chain_tracker = call_chain_tracker
        
        # 测试在manager中调用链追踪器
        try:
            manager_chain = manager._call_chain_tracker.get_call_chain()
            print(f"manager中的调用链: {manager_chain}")
        except Exception as e:
            print(f"manager中调用链获取失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 恢复原始开关状态
        cm_module.ENABLE_CALL_CHAIN_DISPLAY = original_switch

if __name__ == "__main__":
    test_manager_call_chain_issue() 