# src/demo/path_configuration_demo.py
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


def demonstrate_path_configuration():
    """演示路径配置模块功能"""
    print("=" * 60)
    print("路径配置模块演示")
    print("=" * 60)
    
    # 1. 创建配置管理器
    print("\n1. 创建配置管理器...")
    config = get_config_manager(test_mode=True)
    
    # 2. 设置基础配置
    print("\n2. 设置基础配置...")
    config.project_name = "ml_project_demo"
    config.experiment_name = "experiment_001"
    config.base_dir = "d:\\demo_logs"
    
    print(f"项目名称: {config.project_name}")
    print(f"实验名称: {config.experiment_name}")
    print(f"基础目录: {config.base_dir}")
    
    # 3. 显示调试模式状态
    print("\n3. 调试模式状态...")
    try:
        debug_mode = config.debug_mode
        print(f"调试模式: {debug_mode}")
    except AttributeError:
        print("调试模式未设置")
    
    # 4. 显示生成的路径配置
    print("\n4. 生成的路径配置...")
    try:
        print(f"工作目录: {config.paths.work_dir}")
        print(f"检查点目录: {config.paths.checkpoint_dir}")
        print(f"最佳检查点目录: {config.paths.best_checkpoint_dir}")
        print(f"TensorBoard日志目录: {config.paths.tsb_logs_dir}")
        print(f"普通日志目录: {config.paths.log_dir}")
    except AttributeError as e:
        print(f"路径配置访问失败: {e}")
    
    # 5. 获取路径配置信息
    print("\n5. 路径配置详细信息...")
    try:
        path_info = config.get_path_configuration_info()
        
        if path_info:
            print("调试信息:")
            debug_info = path_info.get('debug_info', {})
            for key, value in debug_info.items():
                print(f"  {key}: {value}")
            
            print("\n缓存状态:")
            cache_status = path_info.get('cache_status', {})
            for key, value in cache_status.items():
                print(f"  {key}: {value}")
        else:
            print("无法获取路径配置信息")
    except Exception as e:
        print(f"获取路径配置信息失败: {e}")
    
    # 6. 测试路径目录创建
    print("\n6. 测试路径目录创建...")
    try:
        # 创建工作目录
        work_dir_result = config.create_path_directories(create_all=False)
        print(f"工作目录创建结果: {work_dir_result}")
        
        # 创建所有目录
        all_dirs_result = config.create_path_directories(create_all=True)
        print(f"所有目录创建结果: {all_dirs_result}")
    except Exception as e:
        print(f"目录创建失败: {e}")
    
    # 7. 测试调试模式更新
    print("\n7. 测试调试模式更新...")
    try:
        print("更新调试模式...")
        config.update_debug_mode()
        print(f"更新后的调试模式: {config.debug_mode}")
    except Exception as e:
        print(f"调试模式更新失败: {e}")
    
    # 8. 显示配置文件内容
    print("\n8. 当前配置文件内容...")
    try:
        config_path = config.get_config_path()
        print(f"配置文件路径: {config_path}")
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print("配置文件内容:")
            print("-" * 40)
            print(content)
            print("-" * 40)
        else:
            print("配置文件不存在")
    except Exception as e:
        print(f"读取配置文件失败: {e}")


def demonstrate_path_generation_scenarios():
    """演示不同场景下的路径生成"""
    print("\n" + "=" * 60)
    print("路径生成场景演示")
    print("=" * 60)
    
    scenarios = [
        {
            "name": "机器学习项目 - 调试模式",
            "config": {
                "project_name": "ml_research",
                "experiment_name": "bert_fine_tuning",
                "base_dir": "d:\\ml_experiments",
                "debug_mode": True
            }
        },
        {
            "name": "机器学习项目 - 生产模式",
            "config": {
                "project_name": "ml_research", 
                "experiment_name": "bert_fine_tuning",
                "base_dir": "d:\\ml_experiments",
                "debug_mode": False
            }
        },
        {
            "name": "深度学习项目",
            "config": {
                "project_name": "computer_vision",
                "experiment_name": "object_detection_v2",
                "base_dir": "e:\\deep_learning",
                "debug_mode": False
            }
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print("-" * 40)
        
        try:
            # 创建临时配置管理器
            config = get_config_manager(config_path=f"temp_config_{i}.yaml", test_mode=True)
            
            # 设置配置
            for key, value in scenario['config'].items():
                config.set(key, value)
            
            # 显示生成的路径
            print(f"项目: {config.project_name}")
            print(f"实验: {config.experiment_name}")
            print(f"调试模式: {config.debug_mode}")
            print(f"工作目录: {config.paths.work_dir}")
            print(f"检查点目录: {config.paths.checkpoint_dir}")
            print(f"日志目录: {config.paths.log_dir}")
            
        except Exception as e:
            print(f"场景演示失败: {e}")


def demonstrate_time_based_directories():
    """演示基于时间的目录生成"""
    print("\n" + "=" * 60)
    print("时间基础目录演示")
    print("=" * 60)
    
    try:
        config = get_config_manager(config_path="time_demo_config.yaml", test_mode=True)
        
        # 设置基础配置
        config.project_name = "time_demo"
        config.experiment_name = "exp_time"
        config.base_dir = "d:\\time_logs"
        
        # 设置不同的启动时间
        test_times = [
            "2025-01-08T09:30:00",
            "2025-01-08T14:45:30", 
            "2025-01-08T20:15:45"
        ]
        
        for i, test_time in enumerate(test_times, 1):
            print(f"\n{i}. 启动时间: {test_time}")
            print("-" * 30)
            
            # 设置启动时间
            config.first_start_time = test_time
            
            # 显示生成的时间基础目录
            print(f"TensorBoard日志: {config.paths.tsb_logs_dir}")
            print(f"普通日志: {config.paths.log_dir}")
            
            # 解析时间组件
            from src.config_manager.core.path_configuration import TimeProcessor
            date_str, time_str = TimeProcessor.parse_first_start_time(test_time)
            print(f"解析结果 - 日期: {date_str}, 时间: {time_str}")
            
    except Exception as e:
        print(f"时间基础目录演示失败: {e}")


def main():
    """主函数"""
    print("路径配置模块完整演示")
    print("=" * 80)
    
    try:
        # 基础功能演示
        demonstrate_path_configuration()
        
        # 场景演示
        demonstrate_path_generation_scenarios()
        
        # 时间基础目录演示
        demonstrate_time_based_directories()
        
        print("\n" + "=" * 80)
        print("演示完成！")
        
    except Exception as e:
        print(f"演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 