# temp/config_serialization_demo.py
from __future__ import annotations

import pickle
import json
import tempfile
import multiprocessing as mp
from datetime import datetime
from pathlib import Path

from config_manager import get_config_manager


def worker_function(config_data):
    """工作进程函数 - 必须在模块级别定义"""
    worker_id = mp.current_process().name
    
    # 访问配置数据
    app_name = config_data.app_name
    worker_count = config_data.worker_count
    db_host = config_data.database.host
    batch_size = config_data.task_config.batch_size
    
    # 模拟处理
    result = {
        'worker': worker_id,
        'app_name': app_name,
        'worker_count': worker_count,
        'db_host': db_host,
        'batch_size': batch_size,
        'processed_items': batch_size * 2
    }
    
    return result


def demo_basic_serialization():
    """演示基本的序列化功能"""
    print("=== 基本序列化功能演示 ===")
    
    # 1. 创建配置管理器
    config = get_config_manager(
        config_path="temp/demo_config.yaml",
        auto_create=True,
        watch=False
    )
    
    # 2. 设置配置数据
    config.app_name = "SerializationDemo"
    config.version = "1.0.0"
    config.database = {
        'host': 'localhost',
        'port': 5432,
        'name': 'testdb'
    }
    config.features = ['feature1', 'feature2', 'feature3']
    config.settings = {
        'debug': True,
        'timeout': 30,
        'max_workers': 4
    }
    
    # 3. 检查原始ConfigManager是否可序列化
    print(f"原始ConfigManager可序列化: {config.is_pickle_serializable()}")
    
    # 4. 获取可序列化的配置数据
    serializable_config = config.get_serializable_data()
    print(f"可序列化配置数据可序列化: {serializable_config.is_serializable()}")
    
    # 5. 演示pickle序列化
    try:
        pickled_data = pickle.dumps(serializable_config)
        print(f"✅ pickle序列化成功，数据大小: {len(pickled_data)} 字节")
        
        # 反序列化
        deserialized_config = pickle.loads(pickled_data)
        print(f"✅ pickle反序列化成功")
        print(f"   应用名: {deserialized_config.app_name}")
        print(f"   数据库主机: {deserialized_config.database.host}")
        
    except Exception as e:
        print(f"❌ pickle序列化失败: {e}")
    
    print()


def demo_access_methods():
    """演示配置访问方法"""
    print("=== 配置访问方法演示 ===")
    
    # 创建配置
    config = get_config_manager(
        config_path="temp/access_demo.yaml",
        auto_create=True,
        watch=False
    )
    
    config.app_name = "AccessDemo"
    config.database = {
        'host': 'localhost',
        'port': 5432,
        'credentials': {
            'username': 'admin',
            'password': 'secret'
        }
    }
    config.features = ['auth', 'logging', 'caching']
    
    # 获取可序列化数据
    serializable_config = config.get_serializable_data()
    
    # 1. 属性访问
    print("1. 属性访问:")
    print(f"   app_name: {serializable_config.app_name}")
    print(f"   database.host: {serializable_config.database.host}")
    print(f"   database.credentials.username: {serializable_config.database.credentials.username}")
    
    # 2. 字典访问
    print("\n2. 字典访问:")
    print(f"   config['app_name']: {serializable_config['app_name']}")
    print(f"   config['database']['host']: {serializable_config['database']['host']}")
    
    # 3. get方法访问
    print("\n3. get方法访问:")
    print(f"   get('app_name'): {serializable_config.get('app_name')}")
    print(f"   get('database.host'): {serializable_config.get('database.host')}")
    print(f"   get('nonexistent', 'default'): {serializable_config.get('nonexistent', 'default')}")
    print(f"   get('database.port', 3306, as_type=int): {serializable_config.get('database.port', 3306, as_type=int)}")
    
    # 4. 检查键是否存在
    print("\n4. 键存在性检查:")
    print(f"   'app_name' in config: {'app_name' in serializable_config}")
    print(f"   'nonexistent' in config: {'nonexistent' in serializable_config}")
    
    # 5. 迭代访问
    print("\n5. 迭代访问:")
    print(f"   keys(): {list(serializable_config.keys())}")
    print(f"   values(): {list(serializable_config.values())}")
    
    print()


def demo_multiprocessing():
    """演示多进程环境下的使用"""
    print("=== 多进程环境演示 ===")
    
    # 创建配置
    config = get_config_manager(
        config_path="temp/mp_demo.yaml",
        auto_create=True,
        watch=False
    )
    
    config.app_name = "MultiProcessDemo"
    config.worker_count = 4
    config.database = {
        'host': 'localhost',
        'port': 5432
    }
    config.task_config = {
        'batch_size': 100,
        'timeout': 30
    }
    
    # 获取可序列化数据
    serializable_config = config.get_serializable_data()
    
    # 启动多进程
    try:
        with mp.Pool(processes=2) as pool:
            results = pool.map(worker_function, [serializable_config, serializable_config])
        
        print("✅ 多进程执行成功:")
        for i, result in enumerate(results, 1):
            print(f"   Worker {i}:")
            print(f"     进程名: {result['worker']}")
            print(f"     应用名: {result['app_name']}")
            print(f"     数据库: {result['db_host']}")
            print(f"     批处理大小: {result['batch_size']}")
            print(f"     处理项目数: {result['processed_items']}")
            
    except Exception as e:
        print(f"❌ 多进程执行失败: {e}")
        print("   注意: 在Windows上可能需要使用 'if __name__ == \"__main__\":' 保护")
    
    print()


def demo_advanced_features():
    """演示高级功能"""
    print("=== 高级功能演示 ===")
    
    # 创建配置
    config = get_config_manager(
        config_path="temp/advanced_demo.yaml",
        auto_create=True,
        watch=False
    )
    
    config.app_name = "AdvancedDemo"
    config.version = "2.0.0"
    config.features = ['feature1', 'feature2']
    
    # 获取可序列化数据
    serializable_config = config.get_serializable_data()
    
    # 1. 克隆配置
    print("1. 配置克隆:")
    cloned_config = serializable_config.clone()
    print(f"   原始配置: {serializable_config.app_name}")
    print(f"   克隆配置: {cloned_config.app_name}")
    print(f"   是否为同一对象: {serializable_config is cloned_config}")
    
    # 2. 转换为字典
    print("\n2. 转换为字典:")
    config_dict = serializable_config.to_dict()
    print(f"   字典类型: {type(config_dict)}")
    print(f"   字典内容: {config_dict}")
    
    # 3. 性能测试
    print("\n3. 性能测试:")
    import time
    
    # 序列化性能
    start_time = time.time()
    pickled_data = pickle.dumps(serializable_config)
    serialize_time = time.time() - start_time
    
    # 反序列化性能
    start_time = time.time()
    deserialized = pickle.loads(pickled_data)
    deserialize_time = time.time() - start_time
    
    print(f"   序列化耗时: {serialize_time:.4f}秒")
    print(f"   反序列化耗时: {deserialize_time:.4f}秒")
    print(f"   数据大小: {len(pickled_data)} 字节")
    
    # 4. 错误处理
    print("\n4. 错误处理:")
    try:
        # 访问不存在的属性
        nonexistent = serializable_config.nonexistent_attribute
    except AttributeError as e:
        print(f"   ✅ 正确捕获属性错误: {e}")
    
    try:
        # 访问不存在的键
        nonexistent = serializable_config['nonexistent_key']
    except KeyError as e:
        print(f"   ✅ 正确捕获键错误: {e}")
    
    print()


def demo_json_serialization():
    """演示JSON序列化（通过字典转换）"""
    print("=== JSON序列化演示 ===")
    
    # 创建配置
    config = get_config_manager(
        config_path="temp/json_demo.yaml",
        auto_create=True,
        watch=False
    )
    
    config.app_name = "JSONDemo"
    config.version = "1.0.0"
    config.database = {
        'host': 'localhost',
        'port': 5432
    }
    config.features = ['feature1', 'feature2']
    
    # 获取可序列化数据
    serializable_config = config.get_serializable_data()
    
    # 转换为字典
    config_dict = serializable_config.to_dict()
    
    # JSON序列化
    try:
        json_data = json.dumps(config_dict, indent=2, ensure_ascii=False)
        print("✅ JSON序列化成功:")
        print(json_data)
        
        # JSON反序列化
        deserialized_dict = json.loads(json_data)
        print(f"\n✅ JSON反序列化成功，应用名: {deserialized_dict['app_name']}")
        
    except Exception as e:
        print(f"❌ JSON序列化失败: {e}")
    
    print()


def main():
    """主函数"""
    print("🚀 Config对象序列化使用演示")
    print("=" * 50)
    
    # 创建临时目录
    Path("temp").mkdir(exist_ok=True)
    
    try:
        # 运行各种演示
        demo_basic_serialization()
        demo_access_methods()
        demo_multiprocessing()
        demo_advanced_features()
        demo_json_serialization()
        
        print("✅ 所有演示完成！")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 