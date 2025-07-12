from __future__ import annotations

import pickle
import tempfile
import multiprocessing as mp
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_manager import get_config_manager


def test_config_manager_pickle_issue():
    """测试config_manager对象的pickle序列化问题"""
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        test_config_path = tmp.name
    
    try:
        # 创建配置管理器
        config = get_config_manager(
            config_path=test_config_path,
            auto_create=True,
            watch=False,
            first_start_time=datetime.now()
        )
        
        # 设置一些配置数据
        config.app_name = "TestApp"
        config.database = {
            'host': 'localhost',
            'port': 5432
        }
        config.features = ['feature1', 'feature2']
        
        # 尝试pickle序列化
        try:
            pickle.dumps(config)
            print("✗ config_manager对象意外地可以被pickle序列化")
            return False
        except (TypeError, AttributeError) as e:
            print(f"✓ 验证了问题存在: {e}")
            return True
            
    finally:
        # 清理临时文件
        Path(test_config_path).unlink(missing_ok=True)


def worker_function(config_data):
    """多进程worker函数，处理配置数据"""
    print(f"Worker收到配置: app_name={config_data.app_name}")
    print(f"Worker收到配置: database={config_data.database}")
    print(f"Worker收到配置: features={config_data.features}")
    return f"处理完成，app_name={config_data.app_name}"


def test_multiprocessing_with_config():
    """测试多进程环境下使用配置数据"""
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        test_config_path = tmp.name
    
    try:
        # 创建配置管理器
        config = get_config_manager(
            config_path=test_config_path,
            auto_create=True,
            watch=False,
            first_start_time=datetime.now()
        )
        
        # 设置一些配置数据
        config.app_name = "MultiProcessApp"
        config.database = {
            'host': 'localhost',
            'port': 5432
        }
        config.features = ['feature1', 'feature2']
        
        # 获取可序列化的配置数据
        if hasattr(config, 'get_serializable_data'):
            serializable_config = config.get_serializable_data()
        else:
            print("✗ 配置管理器尚未实现get_serializable_data方法")
            return False
        
        # 尝试在多进程中使用配置数据
        try:
            with mp.Pool(processes=2) as pool:
                results = pool.map(worker_function, [serializable_config, serializable_config])
                print(f"多进程处理结果: {results}")
                return True
        except Exception as e:
            print(f"✗ 多进程处理失败: {e}")
            return False
            
    finally:
        # 清理临时文件
        Path(test_config_path).unlink(missing_ok=True)


if __name__ == '__main__':
    print("=" * 60)
    print("测试config_manager的pickle序列化问题")
    print("=" * 60)
    
    # 测试1：验证当前问题
    print("\n1. 验证pickle序列化问题:")
    test_config_manager_pickle_issue()
    
    # 测试2：测试多进程解决方案
    print("\n2. 测试多进程解决方案:")
    test_multiprocessing_with_config() 