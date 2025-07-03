#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试在manager的initialize方法中调用链追踪器的状态
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

def test_initialize_call_chain():
    """测试在manager的initialize方法中调用链追踪器的状态"""
    print("=== 测试在manager的initialize方法中调用链追踪器的状态 ===")
    
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
            
            # 模拟initialize方法中的调用链追踪器测试
            from config_manager.config_manager import ENABLE_CALL_CHAIN_DISPLAY
            if ENABLE_CALL_CHAIN_DISPLAY:
                print("=== 模拟initialize方法中的调用链追踪器测试 ===")
                try:
                    # 检查调用链追踪器是否被重新创建
                    print(f"调用链追踪器ID: {id(manager._call_chain_tracker)}")
                    print(f"原始调用链追踪器ID: {id(call_chain_tracker)}")
                    print(f"是否相同: {manager._call_chain_tracker is call_chain_tracker}")
                    
                    test_chain = manager._call_chain_tracker.get_call_chain()
                    print(f"initialize方法中的调用链: {test_chain}")
                    
                    # 如果调用链为空，尝试重新获取
                    if not test_chain or test_chain == "{}":
                        print("调用链为空，尝试重新获取...")
                        # 重新设置调用链追踪器
                        manager._call_chain_tracker = call_chain_tracker
                        test_chain = manager._call_chain_tracker.get_call_chain()
                        print(f"重新设置后的调用链: {test_chain}")
                    
                except Exception as e:
                    print(f"initialize方法中调用链获取失败: {e}")
                    import traceback
                    traceback.print_exc()
            
        except Exception as e:
            print(f"manager中调用链获取失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 恢复原始开关状态
        cm_module.ENABLE_CALL_CHAIN_DISPLAY = original_switch

if __name__ == "__main__":
    test_initialize_call_chain() 