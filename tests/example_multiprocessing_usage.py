#!/usr/bin/env python3
"""
config_manager多进程使用示例
==========================

这个示例展示如何在多进程环境中使用config_manager：
1. 创建配置管理器并设置配置
2. 获取可序列化的配置数据
3. 在多进程worker中使用配置数据

使用方法：
直接运行此脚本，或者复制相关代码到您的项目中。
"""

from __future__ import annotations

import multiprocessing as mp
import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime

# 如果在其他项目中使用，请根据实际情况调整导入路径
# 当前路径适用于config_manager项目内部测试
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from config_manager import get_config_manager, SerializableConfigData
except ImportError as e:
    print(f"❌ 导入config_manager失败: {e}")
    print("请确保config_manager已正确安装或调整导入路径")
    sys.exit(1)


def worker_task_example(config_data: SerializableConfigData):
    """
    示例worker函数 - 展示如何在worker中使用配置数据
    
    Args:
        config_data: 可序列化的配置数据对象
    
    Returns:
        dict: 处理结果
    """
    worker_name = mp.current_process().name
    
    # 1. 直接属性访问
    app_name = config_data.app_name
    
    # 2. 使用get方法（支持默认值）
    batch_size = config_data.get('processing.batch_size', 100)
    max_workers = config_data.get('processing.max_workers', 4)
    
    # 3. 访问嵌套配置
    db_host = config_data.database.host
    db_port = config_data.database.port
    
    # 4. 访问路径配置
    output_dir = config_data.get('paths.output_dir', '/tmp/output')
    
    # 模拟一些处理工作
    result_data = []
    for i in range(batch_size):
        item = {
            'id': i,
            'worker': worker_name,
            'app': app_name,
            'db_connection': f"{db_host}:{db_port}",
            'processed_at': datetime.now().isoformat()
        }
        result_data.append(item)
    
    return {
        'worker_name': worker_name,
        'app_name': app_name,
        'processed_items': len(result_data),
        'batch_size': batch_size,
        'max_workers': max_workers,
        'output_dir': output_dir,
        'sample_data': result_data[:3]  # 只返回前3个作为示例
    }


def setup_test_config():
    """
    设置测试配置
    
    Returns:
        tuple: (config_manager, temp_config_path)
    """
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        temp_config_path = tmp.name
    
    print(f"📁 创建临时配置文件: {temp_config_path}")
    
    # 创建配置管理器
    config = get_config_manager(
        config_path=temp_config_path,
        auto_create=True,      # 自动创建配置文件
        watch=False,           # 多进程环境建议关闭文件监视
        first_start_time=datetime.now()
    )
    
    # 设置应用配置
    config.app_name = "MultiProcessApp"
    config.version = "1.0.0"
    config.environment = "test"
    
    # 设置数据库配置
    config.database = {
        'host': 'localhost',
        'port': 5432,
        'name': 'test_db',
        'timeout': 30
    }
    
    # 设置处理配置
    config.processing = {
        'batch_size': 50,
        'max_workers': 4,
        'timeout': 60,
        'retry_attempts': 3
    }
    
    # 设置路径配置
    config.paths = {
        'data_dir': '/tmp/data',
        'output_dir': '/tmp/output',
        'log_dir': '/tmp/logs',
        'cache_dir': '/tmp/cache'
    }
    
    # 设置业务配置
    config.business = {
        'enable_feature_x': True,
        'max_items_per_request': 1000,
        'api_rate_limit': 100
    }
    
    print("✅ 配置设置完成")
    return config, temp_config_path


def test_multiprocessing_config():
    """
    测试多进程配置传递的主函数
    """
    print("=" * 60)
    print("config_manager多进程测试示例")
    print("=" * 60)
    
    config = None
    temp_config_path = None
    
    try:
        # 1. 设置配置
        print("\n🔧 步骤1: 设置配置")
        config, temp_config_path = setup_test_config()
        
        # 2. 获取可序列化的配置数据
        print("\n📦 步骤2: 获取可序列化配置数据")
        serializable_config = config.get_serializable_data()
        
        # 验证序列化
        import pickle
        pickled_size = len(pickle.dumps(serializable_config))
        print(f"✅ 配置数据可以序列化，大小: {pickled_size} bytes")
        
        # 3. 测试单个worker
        print("\n🔨 步骤3: 测试单个worker")
        single_result = worker_task_example(serializable_config)
        print("✅ 单worker测试成功:")
        print(f"   - 应用名: {single_result['app_name']}")
        print(f"   - 处理项数: {single_result['processed_items']}")
        print(f"   - 输出目录: {single_result['output_dir']}")
        
        # 4. 测试多进程
        print("\n🚀 步骤4: 测试多进程worker")
        num_processes = 3
        
        with mp.Pool(processes=num_processes) as pool:
            # 将相同的配置数据传递给多个worker
            config_list = [serializable_config] * num_processes
            results = pool.map(worker_task_example, config_list)
        
        print(f"✅ 多进程测试成功，{num_processes}个worker完成:")
        for i, result in enumerate(results, 1):
            print(f"   Worker {i}: {result['worker_name']} - 处理了 {result['processed_items']} 项")
        
        # 5. 验证结果一致性
        print("\n🔍 步骤5: 验证结果一致性")
        first_app_name = results[0]['app_name']
        first_batch_size = results[0]['batch_size']
        
        all_same_app = all(r['app_name'] == first_app_name for r in results)
        all_same_batch = all(r['batch_size'] == first_batch_size for r in results)
        
        if all_same_app and all_same_batch:
            print("✅ 所有worker使用了相同的配置数据")
        else:
            print("❌ worker之间配置数据不一致")
        
        print("\n🎉 测试完成！config_manager成功支持多进程环境")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理临时文件
        if temp_config_path and Path(temp_config_path).exists():
            try:
                Path(temp_config_path).unlink()
                print(f"🧹 清理临时文件: {temp_config_path}")
            except Exception as e:
                print(f"⚠️  清理临时文件失败: {e}")


def demonstrate_config_access_patterns(config_data: SerializableConfigData):
    """
    演示各种配置访问模式
    
    Args:
        config_data: 配置数据对象
    """
    print("\n📖 配置访问模式示例:")
    
    # 1. 直接属性访问
    print(f"1. 直接属性: config_data.app_name = '{config_data.app_name}'")
    
    # 2. 字典风格访问
    print(f"2. 字典访问: config_data['version'] = '{config_data['version']}'")
    
    # 3. get方法（带默认值）
    unknown_key = config_data.get('unknown_key', 'default_value')
    print(f"3. get方法: config_data.get('unknown_key', 'default_value') = '{unknown_key}'")
    
    # 4. 嵌套访问
    batch_size = config_data.get('processing.batch_size', 100)
    print(f"4. 嵌套访问: config_data.get('processing.batch_size', 100) = {batch_size}")
    
    # 5. 复杂对象访问
    db_config = config_data.database
    print(f"5. 复杂对象: config_data.database.host = '{db_config.host}'")
    
    # 6. 检查键是否存在
    has_database = 'database' in config_data
    print(f"6. 键存在检查: 'database' in config_data = {has_database}")


if __name__ == '__main__':
    # Windows下需要设置多进程启动方法
    if sys.platform.startswith('win'):
        mp.set_start_method('spawn', force=True)
    
    # 运行主测试
    success = test_multiprocessing_config()
    
    if success:
        print("\n" + "=" * 60)
        print("🎯 如何在您的项目中使用:")
        print("=" * 60)
        print("1. 安装或导入config_manager模块")
        print("2. 创建配置管理器: config = get_config_manager(...)")
        print("3. 设置配置: config.your_setting = value")
        print("4. 获取可序列化数据: serializable_config = config.get_serializable_data()")
        print("5. 传递给worker: pool.map(your_worker_function, [serializable_config]*n)")
        print("6. 在worker中使用: config_data.your_setting")
        
        # 演示配置访问模式
        temp_config, temp_path = setup_test_config()
        try:
            serializable = temp_config.get_serializable_data()
            demonstrate_config_access_patterns(serializable)
        finally:
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)
    
    sys.exit(0 if success else 1) 