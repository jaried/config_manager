#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import os
import time
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config_manager.config_manager import get_config_manager, _clear_instances_for_testing

def test_reload_debug():
    """调试reload问题"""
    _clear_instances_for_testing()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        print(f"配置文件路径: {config_file}")
        
        # 创建配置管理器
        cfg = get_config_manager(config_path=config_file, watch=False)
        
        # 设置值
        cfg.persistence_test = 'save_me'
        print(f"设置后的值: {cfg.persistence_test}")
        print(f"_data内容: {dict(cfg._data)}")
        
        # 等待自动保存
        time.sleep(0.3)
        
        # 手动保存
        saved = cfg.save()
        print(f"保存结果: {saved}")
        
        # 查看保存的文件内容
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print('=== 保存的配置文件内容 ===')
                print(content)
                print('=== 结束 ===')
        else:
            print("配置文件不存在！")
        
        # 测试重新加载
        print("\n=== 测试重新加载 ===")
        reloaded = cfg.reload()
        print(f'Reload结果: {reloaded}')
        print(f'重新加载后_data内容: {dict(cfg._data)}')
        print(f'重新加载后persistence_test值: {cfg.get("persistence_test")}')
        
        # 尝试直接访问属性
        try:
            direct_value = cfg.persistence_test
            print(f'直接访问属性值: {direct_value}')
        except AttributeError as e:
            print(f'直接访问属性失败: {e}')

if __name__ == '__main__':
    test_reload_debug() 