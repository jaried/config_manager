#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试完整的manager初始化过程
"""

import os
import sys
import tempfile

# 添加src路径
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from config_manager.config_manager import get_config_manager
from config_manager.logger.minimal_logger import info

def test_full_manager_init():
    """测试完整的manager初始化过程"""
    print("=== 测试完整的manager初始化过程 ===")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        
        # 模拟测试中的调用
        try:
            # 设置调用链开关为True
            import config_manager.config_manager as cm_module
            original_switch = cm_module.ENABLE_CALL_CHAIN_DISPLAY
            cm_module.ENABLE_CALL_CHAIN_DISPLAY = True
            
            print(f"调用链开关状态: {cm_module.ENABLE_CALL_CHAIN_DISPLAY}")
            
            # 创建manager
            cfg = get_config_manager(
                config_path=config_file,
                watch=False,
                autosave_delay=0.1
            )
            
            if cfg:
                print("✓ Manager创建成功")
                
                # 设置一个配置项
                cfg.test_item = "test_value"
                
                # 保存配置
                cfg.save()
                
                print("✓ 配置保存成功")
            else:
                print("✗ Manager创建失败")
                
        except Exception as e:
            print(f"✗ 初始化失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 恢复原始开关状态
            cm_module.ENABLE_CALL_CHAIN_DISPLAY = original_switch

if __name__ == "__main__":
    test_full_manager_init() 