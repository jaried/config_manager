# src/demo/demo_path_replacement.py
from __future__ import annotations
import os
import tempfile
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.config_manager.config_manager import ConfigManager

def demo_path_replacement():
    """演示test_mode下的全路径替换功能"""
    print("=== ConfigManager 路径替换功能演示 ===\n")
    
    # 1. 演示路径字段检测
    print("1. 路径字段检测功能:")
    test_cases = [
        ('base_dir', 'd:/logs/'),
        ('work_dir', '/home/user/work'),
        ('log_path', 'C:/logs/app.log'),
        ('port', '8080'),
        ('timeout', '30'),
        ('data_directory', './data'),
        ('name', 'application')
    ]
    
    for field, value in test_cases:
        is_path = ConfigManager._is_path_field(field, value)
        print(f"  {field}: '{value}' -> {'✓ 路径字段' if is_path else '✗ 非路径字段'}")
    
    print("\n2. 路径格式检测功能:")
    path_cases = [
        'C:/Windows/System32',
        'D:\\data\\files',
        '/usr/local/bin',
        './config',
        '../parent/dir',
        'localhost',
        '8080',
        'true'
    ]
    
    for path in path_cases:
        is_path_like = ConfigManager._is_path_like(path)
        print(f"  '{path}' -> {'✓ 路径格式' if is_path_like else '✗ 非路径格式'}")
    
    # 3. 演示路径替换
    print("\n3. 路径替换功能:")
    test_base_dir = os.path.join(tempfile.gettempdir(), 'demo_test_env')
    temp_base = tempfile.gettempdir()
    
    # 创建测试配置数据
    config_data = {
        '__data__': {
            'base_dir': 'd:/logs/',
            'work_dir': 'd:/logs/bakamh',
            'log_dir': 'd:/logs/bakamh/logs',
            'data_dir': 'd:/logs/bakamh/data',
            'temp_dir': 'C:/temp/bakamh',
            'cache_dir': '/var/cache/bakamh',
            'backup_dir': './backup',
            'custom_path': '/usr/local/bin/tool',
            'nested': {
                'storage_dir': 'd:/storage/files',
                'output_dir': 'C:/output',
                'paths_list': [
                    'd:/path1',
                    'C:/path2',
                    './relative/path',
                    'not_a_path_value'
                ]
            },
            'non_path_field': 'not_a_path',
            'port': 8080,
            'timeout': 30
        }
    }
    
    print(f"  测试环境基础路径: {test_base_dir}")
    print("  原始配置数据:")
    print_config_paths(config_data['__data__'], "    ")
    
    print("\n  执行路径替换...")
    ConfigManager._replace_all_paths_in_config(config_data['__data__'], test_base_dir, temp_base)
    
    print("\n  替换后的配置数据:")
    print_config_paths(config_data['__data__'], "    ")
    
    # 4. 演示路径转换
    print("\n4. 路径转换功能:")
    conversion_cases = [
        'd:/logs/bakamh',
        './data',
        '/tmp/existing/path',
        'not_a_path',
        'C:/Windows/System32',
        '../parent/dir'
    ]
    
    for original_path in conversion_cases:
        converted = ConfigManager._convert_to_test_path(original_path, test_base_dir, temp_base)
        print(f"  '{original_path}' -> '{converted}'")
    
    print("\n=== 演示完成 ===")

def print_config_paths(config_data, indent=""):
    """递归打印配置中的路径信息"""
    for key, value in config_data.items():
        if isinstance(value, dict):
            print(f"{indent}{key}:")
            print_config_paths(value, indent + "  ")
        elif isinstance(value, list):
            print(f"{indent}{key}: {value}")
        else:
            print(f"{indent}{key}: {value}")

if __name__ == "__main__":
    demo_path_replacement() 