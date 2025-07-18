# tests/test_multiprocessing_modes.py
from __future__ import annotations
from datetime import datetime

import pytest
import tempfile
import multiprocessing as mp
import sys
import os
import platform
import pickle
import time
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_manager import get_config_manager


def simple_worker(config_data):
    """简单的worker函数，验证配置数据传递"""
    try:
        # 验证基本属性访问
        app_name = config_data.app_name
        version = config_data.get('version', 'unknown')
        
        # 验证嵌套访问
        db_host = config_data.get('database.host', 'localhost')
        
        # 验证进程信息
        process_name = mp.current_process().name
        start_method = mp.get_start_method()
        
        return {
            'process_name': process_name,
            'start_method': start_method,
            'app_name': app_name,
            'version': version,
            'db_host': db_host,
            'pid': os.getpid(),
            'success': True
        }
    except Exception as e:
        return {
            'process_name': mp.current_process().name,
            'start_method': mp.get_start_method(),
            'error': str(e),
            'success': False
        }


def complex_worker(config_data):
    """复杂的worker函数，测试更多配置操作"""
    try:
        # 测试多种访问方式
        results = {
            'process_name': mp.current_process().name,
            'start_method': mp.get_start_method(),
            'pid': os.getpid(),
            'success': True
        }
        
        # 测试直接属性访问
        results['app_name'] = config_data.app_name
        
        # 测试字典访问
        results['version'] = config_data.get('version', 'unknown')
        
        # 测试嵌套访问
        results['db_config'] = {
            'host': config_data.get('database.host', 'localhost'),
            'port': config_data.get('database.port', 5432),
            'name': config_data.get('database.name', 'test_db')
        }
        
        # 测试路径访问
        results['paths'] = {
            'data_dir': config_data.get('paths.data_dir', '/tmp/data'),
            'log_dir': config_data.get('paths.log_dir', '/tmp/logs')
        }
        
        # 测试列表访问
        results['features'] = config_data.get('features', [])
        
        # 模拟一些计算
        time.sleep(0.1)
        
        return results
    except Exception as e:
        return {
            'process_name': mp.current_process().name,
            'start_method': mp.get_start_method(),
            'error': str(e),
            'success': False
        }


def create_test_config():
    """创建测试配置"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        test_config_path = tmp.name
    
    config = get_config_manager(
        config_path=test_config_path,
        auto_create=True,
        watch=False,
        test_mode=True
    )
    
    # 设置测试配置数据
    config.app_name = "MultiProcessModeTest"
    config.version = "1.0.0"
    config.database = {
        'host': 'localhost',
        'port': 5432,
        'name': 'test_db'
    }
    config.paths = {
        'data_dir': '/tmp/test_data',
        'log_dir': '/tmp/test_logs'
    }
    config.features = ['feature1', 'feature2', 'feature3']
    
    return config, test_config_path


def test_multiprocessing_start_method_detection():
    """测试多进程启动方法检测"""
    # 获取当前平台支持的启动方法
    available_methods = mp.get_all_start_methods()
    current_method = mp.get_start_method()
    
    print(f"当前平台: {platform.system()}")
    print(f"可用的启动方法: {available_methods}")
    print(f"当前启动方法: {current_method}")
    
    # 验证不同平台的预期方法
    if platform.system() == 'Windows':
        assert 'spawn' in available_methods
        assert current_method == 'spawn'  # Windows默认使用spawn
    else:
        # Unix-like系统
        assert 'fork' in available_methods
        assert 'spawn' in available_methods
        # 默认方法可能是fork或spawn，取决于Python版本
        assert current_method in available_methods


@pytest.mark.parametrize("start_method", ["fork", "spawn", "forkserver"])
def test_multiprocessing_modes(start_method):
    """测试不同的多进程启动模式"""
    # 检查当前平台是否支持指定的启动方法
    available_methods = mp.get_all_start_methods()
    if start_method not in available_methods:
        pytest.skip(f"启动方法 '{start_method}' 在当前平台不支持")
    
    print(f"\n测试启动方法: {start_method}")
    
    # 创建测试配置
    config, test_config_path = create_test_config()
    
    try:
        # 获取可序列化的配置数据
        serializable_config = config.get_serializable_data()
        
        # 验证配置数据可以被pickle序列化
        pickled_data = pickle.dumps(serializable_config)
        unpickled_config = pickle.loads(pickled_data)
        assert unpickled_config.app_name == "MultiProcessModeTest"
        
        # 创建具有指定启动方法的上下文
        ctx = mp.get_context(start_method)
        
        # 测试简单的多进程处理
        with ctx.Pool(processes=2) as pool:
            results = pool.map(simple_worker, [serializable_config] * 2)
            
            # 验证结果
            assert len(results) == 2
            for result in results:
                assert result['success'] is True
                assert result['start_method'] == start_method
                assert result['app_name'] == "MultiProcessModeTest"
                assert result['version'] == "1.0.0"
                assert result['db_host'] == "localhost"
                assert isinstance(result['pid'], int)
                assert result['pid'] > 0
        
        print(f"✓ 简单worker测试通过 (启动方法: {start_method})")
        
        # 测试复杂的多进程处理
        with ctx.Pool(processes=3) as pool:
            results = pool.map(complex_worker, [serializable_config] * 3)
            
            # 验证结果
            assert len(results) == 3
            for result in results:
                assert result['success'] is True
                assert result['start_method'] == start_method
                assert result['app_name'] == "MultiProcessModeTest"
                assert result['db_config']['host'] == "localhost"
                assert result['db_config']['port'] == 5432
                assert result['paths']['data_dir'] == "/tmp/test_data"
                assert result['features'] == ['feature1', 'feature2', 'feature3']
        
        print(f"✓ 复杂worker测试通过 (启动方法: {start_method})")
        
    finally:
        # 清理测试文件
        Path(test_config_path).unlink(missing_ok=True)


def test_multiprocessing_performance_comparison():
    """测试不同多进程模式的性能对比"""
    # 创建测试配置
    config, test_config_path = create_test_config()
    
    try:
        serializable_config = config.get_serializable_data()
        
        # 测试不同启动方法的性能
        performance_results = {}
        
        for start_method in mp.get_all_start_methods():
            print(f"\n测试 {start_method} 模式性能...")
            
            ctx = mp.get_context(start_method)
            start_time = time.time()
            
            # 执行多进程任务
            with ctx.Pool(processes=2) as pool:
                results = pool.map(simple_worker, [serializable_config] * 4)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # 验证所有结果都成功
            assert all(r['success'] for r in results)
            
            performance_results[start_method] = {
                'execution_time': execution_time,
                'workers_count': len(results),
                'success_rate': sum(1 for r in results if r['success']) / len(results)
            }
            
            print(f"  执行时间: {execution_time:.3f}s")
            print(f"  成功率: {performance_results[start_method]['success_rate']*100:.1f}%")
        
        # 输出性能对比
        print("\n性能对比结果:")
        for method, stats in performance_results.items():
            print(f"  {method}: {stats['execution_time']:.3f}s (成功率: {stats['success_rate']*100:.1f}%)")
        
        # 验证所有模式都有合理的性能
        for method, stats in performance_results.items():
            assert stats['execution_time'] < 10.0  # 10秒内完成
            assert stats['success_rate'] == 1.0    # 100%成功率
        
    finally:
        Path(test_config_path).unlink(missing_ok=True)


def error_worker(config_data):
    """故意产生错误的worker"""
    try:
        # 故意访问不存在的属性
        _ = config_data.non_existent_attribute
        return {'success': True}
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'start_method': mp.get_start_method()
        }


def test_multiprocessing_error_handling():
    """测试多进程模式下的错误处理"""
    
    # 创建测试配置
    config, test_config_path = create_test_config()
    
    try:
        serializable_config = config.get_serializable_data()
        
        # 测试每种启动方法的错误处理
        for start_method in mp.get_all_start_methods():
            print(f"\n测试 {start_method} 模式错误处理...")
            
            ctx = mp.get_context(start_method)
            
            with ctx.Pool(processes=2) as pool:
                results = pool.map(error_worker, [serializable_config] * 2)
            
            # 验证错误被正确处理
            assert len(results) == 2
            for result in results:
                assert result['success'] is False
                assert 'error' in result
                assert result['start_method'] == start_method
                print(f"  错误信息: {result['error']}")
        
        print("✓ 错误处理测试通过")
        
    finally:
        Path(test_config_path).unlink(missing_ok=True)


def test_multiprocessing_large_config():
    """测试大型配置数据的多进程处理"""
    # 创建大型配置
    config, test_config_path = create_test_config()
    
    try:
        # 添加大量配置数据
        config.large_data = {
            f'key_{i}': f'value_{i}' * 100  # 每个值约500字节
            for i in range(100)  # 100个键值对，总共约50KB
        }
        
        config.large_list = list(range(1000))  # 1000个整数
        
        serializable_config = config.get_serializable_data()
        
        # 测试大型数据的序列化
        pickled_data = pickle.dumps(serializable_config)
        data_size = len(pickled_data)
        print(f"序列化后数据大小: {data_size} bytes")
        
        # 测试不同启动方法处理大型数据
        for start_method in mp.get_all_start_methods():
            print(f"\n测试 {start_method} 模式处理大型配置...")
            
            ctx = mp.get_context(start_method)
            start_time = time.time()
            
            with ctx.Pool(processes=2) as pool:
                results = pool.map(simple_worker, [serializable_config] * 2)
            
            end_time = time.time()
            
            # 验证结果
            assert all(r['success'] for r in results)
            print(f"  处理时间: {end_time - start_time:.3f}s")
        
        print("✓ 大型配置处理测试通过")
        
    finally:
        Path(test_config_path).unlink(missing_ok=True)


if __name__ == '__main__':
    print("=" * 70)
    print("多进程启动模式全面测试")
    print("=" * 70)
    
    # 检测当前环境
    test_multiprocessing_start_method_detection()
    
    print("\n" + "=" * 70)
    print("测试各种启动模式")
    print("=" * 70)
    
    # 测试每种可用的启动方法
    for method in mp.get_all_start_methods():
        print(f"\n{'='*20} 测试 {method.upper()} 模式 {'='*20}")
        try:
            # 临时设置启动方法进行测试
            original_method = mp.get_start_method()
            
            # 创建测试配置
            config, test_config_path = create_test_config()
            
            try:
                serializable_config = config.get_serializable_data()
                ctx = mp.get_context(method)
                
                with ctx.Pool(processes=2) as pool:
                    results = pool.map(simple_worker, [serializable_config] * 2)
                
                success_count = sum(1 for r in results if r['success'])
                print(f"✓ {method} 模式测试完成: {success_count}/{len(results)} 成功")
                
            finally:
                Path(test_config_path).unlink(missing_ok=True)
                
        except Exception as e:
            print(f"✗ {method} 模式测试失败: {e}")
    
    print("\n" + "=" * 70)
    print("性能对比测试")
    print("=" * 70)
    test_multiprocessing_performance_comparison()
    
    print("\n" + "=" * 70)
    print("错误处理测试")
    print("=" * 70)
    test_multiprocessing_error_handling()
    
    print("\n" + "=" * 70)
    print("大型配置测试")
    print("=" * 70)
    test_multiprocessing_large_config()
    
    print("\n" + "=" * 70)
    print("所有测试完成!")
    print("=" * 70)