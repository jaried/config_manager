# src/demo/cross_platform_demo.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config_manager import get_config_manager
from src.config_manager.core.cross_platform_paths import (
    get_cross_platform_manager, 
    convert_to_multi_platform_config,
    get_platform_path
)


def demonstrate_cross_platform_detection():
    """演示跨平台操作系统检测"""
    print("=" * 60)
    print("跨平台操作系统检测演示")
    print("=" * 60)
    
    # 获取跨平台管理器
    manager = get_cross_platform_manager()
    
    # 显示平台信息
    platform_info = manager.get_platform_info()
    print(f"当前操作系统: {platform_info['current_os']}")
    print(f"操作系统家族: {platform_info['os_family']}")
    print(f"系统平台: {platform_info['platform_system']}")
    print(f"系统版本: {platform_info['platform_release']}")
    print(f"机器架构: {platform_info['platform_machine']}")
    print(f"sys.platform: {platform_info['sys_platform']}")
    print(f"检测时间: {platform_info['detection_time']}")


def demonstrate_path_conversion():
    """演示路径转换功能"""
    print("\n" + "=" * 60)
    print("路径转换功能演示")
    print("=" * 60)
    
    # 测试单一路径转换为多平台配置
    test_paths = [
        "d:\\demo_logs",
        "/home/tony/logs",
        "/Users/tony/logs"
    ]
    
    for path in test_paths:
        print(f"\n原始路径: {path}")
        multi_platform_config = convert_to_multi_platform_config(path, 'base_dir')
        print(f"转换后的多平台配置:")
        for os_name, os_path in multi_platform_config.items():
            print(f"  {os_name}: {os_path}")
    
    # 测试从多平台配置获取当前平台路径
    print(f"\n从多平台配置获取当前平台路径:")
    multi_config = {
        'windows': 'd:\\demo_logs',
        'linux': '/home/tony/logs',
        'ubuntu': '/home/tony/logs',
        'macos': '/Users/tony/logs'
    }
    
    current_path = get_platform_path(multi_config, 'base_dir')
    print(f"当前平台路径: {current_path}")


def demonstrate_config_manager_integration():
    """演示配置管理器集成"""
    print("\n" + "=" * 60)
    print("配置管理器集成演示")
    print("=" * 60)
    
    # 创建配置管理器
    config = get_config_manager(config_path="temp/cross_platform_demo.yaml")
    
    # 1. 设置单一路径，自动转换为多平台格式
    print("\n1. 设置单一路径，自动转换为多平台格式")
    config.set('base_dir', 'd:\\demo_logs')
    
    # 获取base_dir，应该返回当前平台的路径
    current_base_dir = config.get('base_dir')
    print(f"当前平台base_dir: {current_base_dir}")
    
    # 2. 设置多平台配置
    print("\n2. 设置多平台配置")
    multi_platform_base_dir = {
        'windows': 'd:\\multi_logs',
        'linux': '/home/tony/multi_logs',
        'ubuntu': '/home/tony/multi_logs',
        'macos': '/Users/tony/multi_logs'
    }
    config.set('base_dir', multi_platform_base_dir)
    
    # 获取base_dir，应该返回当前平台的路径
    current_base_dir = config.get('base_dir')
    print(f"多平台配置的当前平台base_dir: {current_base_dir}")
    
    # 3. 设置项目配置
    print("\n3. 设置项目配置")
    config.set('project_name', 'cross_platform_demo')
    config.set('experiment_name', 'test_exp')
    
    # 4. 显示生成的路径
    print("\n4. 生成的路径配置")
    try:
        print(f"工作目录: {config.paths.work_dir}")
        print(f"检查点目录: {config.paths.checkpoint_dir}")
        print(f"TensorBoard目录: {config.paths.tensorboard_dir}")
        print(f"日志目录: {config.paths.log_dir}")
        print(f"调试目录: {config.paths.debug_dir}")
    except AttributeError as e:
        print(f"路径配置访问失败: {e}")
    
    # 5. 显示路径配置信息
    print("\n5. 路径配置详细信息")
    try:
        path_info = config.get_path_configuration_info()
        print(f"当前操作系统: {path_info.get('current_os')}")
        print(f"操作系统家族: {path_info.get('os_family')}")
        print(f"调试模式: {path_info.get('debug_mode')}")
        print(f"生成的路径: {path_info.get('generated_paths')}")
    except Exception as e:
        print(f"获取路径配置信息失败: {e}")


def demonstrate_backward_compatibility():
    """演示向后兼容性"""
    print("\n" + "=" * 60)
    print("向后兼容性演示")
    print("=" * 60)
    
    # 创建配置管理器
    config = get_config_manager(config_path="temp/backward_compat_demo.yaml")
    
    # 1. 测试字符串格式的base_dir（向后兼容）
    print("\n1. 测试字符串格式的base_dir")
    config.set('base_dir', 'd:\\backward_logs')
    
    # 验证是否自动转换为多平台格式
    base_dir_value = config._data.get('base_dir')
    print(f"存储的base_dir值: {base_dir_value}")
    
    # 获取时应该返回当前平台路径
    current_path = config.get('base_dir')
    print(f"获取的base_dir: {current_path}")
    
    # 2. 测试其他路径配置
    print("\n2. 测试其他路径配置")
    config.set('work_dir', 'd:\\work')
    config.set('tensorboard_dir', 'd:\\tensorboard')
    
    print(f"work_dir: {config.get('work_dir')}")
    print(f"tensorboard_dir: {config.get('tensorboard_dir')}")


def demonstrate_platform_specific_paths():
    """演示平台特定路径"""
    print("\n" + "=" * 60)
    print("平台特定路径演示")
    print("=" * 60)
    
    # 获取跨平台管理器
    manager = get_cross_platform_manager()
    current_os = manager.get_current_os()
    
    # 显示不同平台的默认路径
    print(f"当前操作系统: {current_os}")
    print("\n各平台默认路径:")
    
    for os_name in ['windows', 'linux', 'ubuntu', 'macos']:
        base_dir = manager.get_default_path('base_dir')
        work_dir = manager.DEFAULT_PATHS[os_name].get('work_dir', '')
        tensorboard_dir = manager.DEFAULT_PATHS[os_name].get('tensorboard_dir', '')
        
        print(f"\n{os_name}:")
        print(f"  base_dir: {base_dir}")
        print(f"  work_dir: {work_dir}")
        print(f"  tensorboard_dir: {tensorboard_dir}")


def main():
    """主函数"""
    print("跨平台路径配置系统演示")
    print("=" * 80)
    
    try:
        # 1. 跨平台操作系统检测
        demonstrate_cross_platform_detection()
        
        # 2. 路径转换功能
        demonstrate_path_conversion()
        
        # 3. 配置管理器集成
        demonstrate_config_manager_integration()
        
        # 4. 向后兼容性
        demonstrate_backward_compatibility()
        
        # 5. 平台特定路径
        demonstrate_platform_specific_paths()
        
        print("\n" + "=" * 80)
        print("演示完成！")
        
    except Exception as e:
        print(f"演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 