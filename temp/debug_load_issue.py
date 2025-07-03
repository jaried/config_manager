#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试加载配置问题
"""

import os
import sys
import tempfile

# 添加src路径
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from config_manager.config_manager import get_config_manager

def debug_load_issue():
    """调试加载配置问题"""
    print("=== 开始调试加载配置问题 ===")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        print(f"配置文件路径: {config_file}")
        
        # 获取配置管理器
        cfg = get_config_manager(config_path=config_file, watch=False)
        print(f"配置管理器类型: {type(cfg)}")
        
        # 设置一些测试数据
        cfg.test_value = "test_data"
        cfg.nested = {"level1": {"level2": "deep_value"}}
        cfg.database = {"host": "localhost", "port": 3306}
        
        # 保存配置
        save_result = cfg.save()
        print(f"保存结果: {save_result}")
        
        # 重新加载配置
        print("\n=== 重新加载配置 ===")
        cfg2 = get_config_manager(config_path=config_file, watch=False)
        print(f"重新加载的配置管理器类型: {type(cfg2)}")
        
        # 测试属性访问
        print(f"test_value: {getattr(cfg2, 'test_value', 'NOT_FOUND')}")
        print(f"nested.level1.level2: {getattr(cfg2.nested, 'level1', 'NOT_FOUND')}")
        if hasattr(cfg2.nested, 'level1'):
            print(f"nested.level1.level2: {getattr(cfg2.nested.level1, 'level2', 'NOT_FOUND')}")
        
        # 测试数据库配置
        print(f"database.host: {getattr(cfg2.database, 'host', 'NOT_FOUND')}")
        print(f"database.port: {getattr(cfg2.database, 'port', 'NOT_FOUND')}")
        
        # 检查paths对象
        print(f"paths类型: {type(getattr(cfg2, 'paths', 'NOT_FOUND'))}")
        if hasattr(cfg2, 'paths'):
            print(f"paths.work_dir: {getattr(cfg2.paths, 'work_dir', 'NOT_FOUND')}")

if __name__ == "__main__":
    debug_load_issue() 