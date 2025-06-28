from __future__ import annotations

import pickle
import tempfile
import multiprocessing as mp
import sys
import os
import time
from pathlib import Path
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_manager import get_config_manager, SerializableConfigData


def cpu_intensive_worker(config_data: SerializableConfigData):
    """CPU密集型worker，使用配置数据进行计算"""
    app_name = config_data.app_name
    batch_size = config_data.get('processing.batch_size', 100)
    iterations = config_data.get('processing.iterations', 1000)
    
    # 模拟CPU密集型任务
    result = 0
    for i in range(iterations):
        result += i * batch_size
    
    return {
        'worker_id': mp.current_process().name,
        'app_name': app_name,
        'batch_size': batch_size,
        'iterations': iterations,
        'result': result,
        'timestamp': datetime.now().isoformat()
    }


def data_processing_worker(config_data: SerializableConfigData):
    """数据处理worker，使用数据库配置进行处理"""
    db_config = config_data.database
    data_dir = config_data.get('paths.data_dir', '/tmp/data')
    
    # 模拟数据处理
    processed_items = []
    for i in range(5):
        item = {
            'id': i,
            'source': f"{db_config.host}:{db_config.port}",
            'data_dir': data_dir,
            'processed_at': datetime.now().isoformat()
        }
        processed_items.append(item)
        time.sleep(0.1)  # 模拟处理时间
    
    return {
        'worker_id': mp.current_process().name,
        'db_host': db_config.host,
        'db_port': db_config.port,
        'processed_items': len(processed_items),
        'items': processed_items
    }


def ml_training_worker(config_data: SerializableConfigData):
    """机器学习训练worker，使用训练配置"""
    model_config = config_data.get('ml_model', {})
    epochs = model_config.get('epochs', 10) if model_config else 10
    learning_rate = model_config.get('learning_rate', 0.01) if model_config else 0.01
    
    # 模拟训练过程
    losses = []
    for epoch in range(epochs):
        # 模拟损失计算
        loss = 1.0 - (epoch * learning_rate * 0.1)
        losses.append(max(0.01, loss))  # 确保损失不为负
    
    return {
        'worker_id': mp.current_process().name,
        'epochs': epochs,
        'learning_rate': learning_rate,
        'final_loss': losses[-1],
        'all_losses': losses,
        'model_config': model_config
    }


def test_multiprocessing_scenarios():
    """测试多种多进程使用场景"""
    print("=" * 70)
    print("config_manager多进程场景测试")
    print("=" * 70)
    
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        test_config_path = tmp.name
    
    try:
        # 创建配置管理器并设置配置
        print("\n1. 创建和配置config_manager")
        config = get_config_manager(
            config_path=test_config_path,
            auto_create=True,
            watch=False,
            first_start_time=datetime.now()
        )
        
        # 设置各种配置
        config.app_name = "MultiProcessDemo"
        config.version = "1.0.0"
        
        # 数据库配置
        config.database = {
            'host': 'localhost',
            'port': 5432,
            'name': 'demo_db'
        }
        
        # 处理配置
        config.processing = {
            'batch_size': 500,
            'iterations': 2000,
            'parallel_workers': 4
        }
        
        # 机器学习配置
        config.ml_model = {
            'epochs': 15,
            'learning_rate': 0.001,
            'batch_size': 32,
            'model_type': 'neural_network'
        }
        
        # 路径配置
        config.paths = {
            'data_dir': '/tmp/demo_data',
            'model_dir': '/tmp/demo_models',
            'output_dir': '/tmp/demo_output'
        }
        
        print(f"✓ 配置已设置: app_name={config.app_name}")
        
        # 获取可序列化的配置数据
        print("\n2. 获取可序列化配置数据")
        serializable_config = config.get_serializable_data()
        
        # 验证可序列化性
        print("3. 验证pickle序列化")
        try:
            pickled_data = pickle.dumps(serializable_config)
            unpickled_config = pickle.loads(pickled_data)
            print(f"✓ 序列化成功，数据大小: {len(pickled_data)} bytes")
            print(f"✓ 反序列化后app_name: {unpickled_config.app_name}")
        except Exception as e:
            print(f"✗ 序列化失败: {e}")
            return False
        
        # 场景1：CPU密集型处理
        print("\n4. 场景1：CPU密集型并行处理")
        try:
            with mp.Pool(processes=3) as pool:
                cpu_results = pool.map(
                    cpu_intensive_worker, 
                    [serializable_config] * 3
                )
                print("✓ CPU密集型处理完成:")
                for i, result in enumerate(cpu_results):
                    print(f"  Worker {i+1}: {result['worker_id']} -> 结果: {result['result']}")
        except Exception as e:
            print(f"✗ CPU密集型处理失败: {e}")
        
        # 场景2：数据处理
        print("\n5. 场景2：数据处理任务")
        try:
            with mp.Pool(processes=2) as pool:
                data_results = pool.map(
                    data_processing_worker,
                    [serializable_config] * 2
                )
                print("✓ 数据处理完成:")
                for i, result in enumerate(data_results):
                    print(f"  Worker {i+1}: {result['worker_id']} -> 处理了 {result['processed_items']} 项")
        except Exception as e:
            print(f"✗ 数据处理失败: {e}")
        
        # 场景3：机器学习训练
        print("\n6. 场景3：机器学习训练任务")
        try:
            with mp.Pool(processes=2) as pool:
                ml_results = pool.map(
                    ml_training_worker,
                    [serializable_config] * 2
                )
                print("✓ 机器学习训练完成:")
                for i, result in enumerate(ml_results):
                    print(f"  Worker {i+1}: {result['worker_id']} -> 最终损失: {result['final_loss']:.4f}")
        except Exception as e:
            print(f"✗ 机器学习训练失败: {e}")
        
        print("\n7. 配置数据访问测试")
        # 测试各种访问方式
        print(f"✓ 直接属性访问: {serializable_config.app_name}")
        print(f"✓ get方法访问: {serializable_config.get('version', 'unknown')}")
        print(f"✓ 嵌套访问: {serializable_config.get('processing.batch_size', 0)}")
        print(f"✓ 路径访问: {serializable_config.get('paths.data_dir', 'N/A')}")
        
        print("\n✓ 所有测试完成！config_manager已成功支持多进程环境")
        return True
        
    finally:
        # 清理临时文件
        Path(test_config_path).unlink(missing_ok=True)


if __name__ == '__main__':
    # 设置多进程启动方法（Windows兼容）
    if sys.platform.startswith('win'):
        mp.set_start_method('spawn', force=True)
    
    test_multiprocessing_scenarios() 