#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

from src.config_manager import get_config_manager

def test_get_method():
    """测试get方法"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, 'test_debug.yaml')
        
        # 创建配置管理器，启用文件监视器
        config = get_config_manager(config_path=config_path, watch=True)
        print(f"Config created: {config is not None}")
        
        # 设置base_dir
        test_path = os.path.join(temp_dir, 'test_logs')
        print(f"Setting base_dir to: {test_path}")
        config.set('base_dir', test_path)
        
        # 检查set后的状态
        print(f"After set - base_dir exists: {'base_dir' in config._data}")
        if 'base_dir' in config._data:
            print(f"After set - base_dir value: {config._data['base_dir']}")
            print(f"After set - base_dir type: {type(config._data['base_dir'])}")
        
        # 手动保存配置
        print("Manually saving config...")
        config.save()
        
        # 检查保存的文件内容
        if os.path.exists(config_path):
            print("Saved file content:")
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content)
        
        # 获取base_dir
        current_path = config.get('base_dir')
        print(f"Got base_dir after save: {current_path}")
        
        # 创建新的配置管理器实例，模拟重新加载
        print("Creating new config manager instance...")
        config2 = get_config_manager(config_path=config_path, watch=False)
        reloaded_path = config2.get('base_dir')
        print(f"Got base_dir after reload: {reloaded_path}")

if __name__ == "__main__":
    test_get_method() 