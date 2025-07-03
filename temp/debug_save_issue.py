#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试保存配置问题
"""

import os
import sys
import tempfile

# 添加src路径
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from config_manager.config_manager import get_config_manager

def debug_save_issue():
    """调试保存配置问题"""
    print("=== 开始调试保存配置问题 ===")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        print(f"配置文件路径: {config_file}")
        
        # 获取配置管理器
        cfg = get_config_manager(config_path=config_file, watch=False)
        print(f"配置管理器类型: {type(cfg)}")
        print(f"配置管理器路径: {getattr(cfg, '_config_path', 'NOT_SET')}")
        
        # 检查_data内容
        print(f"_data内容: {getattr(cfg, '_data', 'NOT_FOUND')}")
        
        # 设置一个值
        cfg.test_value = "test_data"
        print(f"设置值后，test_value: {getattr(cfg, 'test_value', 'NOT_FOUND')}")
        print(f"设置值后，_data内容: {getattr(cfg, '_data', 'NOT_FOUND')}")
        
        # 尝试保存
        print("=== 尝试保存配置 ===")
        try:
            saved = cfg.save()
            print(f"保存结果: {saved}")
        except Exception as e:
            print(f"保存时发生异常: {e}")
            import traceback
            traceback.print_exc()
        
        # 检查文件是否创建
        if os.path.exists(config_file):
            print(f"配置文件已创建: {config_file}")
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"文件内容:\n{content}")
        else:
            print(f"配置文件未创建: {config_file}")

if __name__ == "__main__":
    debug_save_issue() 