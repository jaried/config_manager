#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试my_project的情况"""

import tempfile
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config_manager import get_config_manager, _clear_instances_for_testing

def test_my_project_scenario():
    """测试配置文件中project_name为my_project的情况"""
    print("=== 测试配置文件中project_name为my_project的情况 ===")
    
    # 清理实例
    _clear_instances_for_testing()
    
    # 创建一个project_name为my_project的配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write("""__data__:
  project_name: my_project
  app_name: 期货交易PL系统
  version: 1.0.0
  first_start_time: "2025-06-13T23:19:16.337878"
__type_hints__: {}
""")
        config_path = f.name
    
    try:
        print(f"创建的配置文件路径: {config_path}")
        
        # 读取配置文件内容验证
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"配置文件内容:\n{content}")
        
        # 使用test_mode=True创建配置管理器
        fixed_time = datetime(2025, 6, 13, 23, 19, 16)
        print(f"使用固定时间: {fixed_time}")
        
        cfg = get_config_manager(config_path=config_path, test_mode=True, first_start_time=fixed_time)
        
        test_path = cfg.get_config_file_path()
        project_name = cfg.project_name
        
        print(f"测试配置路径: {test_path}")
        print(f"配置中的project_name: {project_name}")
        
        # 检查路径中使用的project_name
        path_parts = test_path.replace('\\', '/').split('/')
        for i, part in enumerate(path_parts):
            if part == 'src' and i > 0:
                path_project_name = path_parts[i - 1]
                print(f"路径中的project_name: {path_project_name}")
                break
        
        # 模拟测试用例的断言
        print(f"\n模拟测试断言:")
        print(f"assert config.project_name == 'FuturesTradingPL'")
        print(f"实际值: '{project_name}'")
        print(f"期望值: 'FuturesTradingPL'")
        
        if project_name == 'FuturesTradingPL':
            print("✓ 测试通过")
        else:
            print("✗ 测试失败")
            print(f"AssertionError: assert '{project_name}' == 'FuturesTradingPL'")
        
        return test_path, project_name
        
    finally:
        # 清理临时文件
        if os.path.exists(config_path):
            os.unlink(config_path)

if __name__ == "__main__":
    test_my_project_scenario() 