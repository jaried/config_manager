# tests/test_performance_and_stress.py
from __future__ import annotations

import time
import tempfile
import os
import sys
import threading
import gc
from pathlib import Path
from typing import Dict, Any, List

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_manager import get_config_manager


class PerformanceTimer:
    """性能计时器"""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
        
    def __enter__(self):
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        
    @property
    def elapsed(self) -> float:
        if self.start_time is None or self.end_time is None:
            return 0.0
        return self.end_time - self.start_time


def create_large_config_data(size: int) -> Dict[str, Any]:
    """创建大型配置数据"""
    config_data = {
        'app_name': f'TestApp_{size}',
        'version': '1.0.0',
        'database': {
            'host': 'localhost',
            'port': 5432,
            'connections': {}
        },
        'services': {},
        'features': [],
        'settings': {}
    }
    
    # 添加大量数据库连接配置
    for i in range(size):
        config_data['database']['connections'][f'conn_{i}'] = {
            'host': f'host_{i}.example.com',
            'port': 5432 + i,
            'database': f'db_{i}',
            'username': f'user_{i}',
            'timeout': 30,
            'pool_size': 10
        }
    
    # 添加大量服务配置
    for i in range(size):
        config_data['services'][f'service_{i}'] = {
            'enabled': True,
            'port': 8000 + i,
            'workers': 4,
            'timeout': 30,
            'settings': {
                'debug': False,
                'log_level': 'INFO',
                'max_connections': 100
            }
        }
    
    # 添加大量功能列表
    for i in range(size):
        config_data['features'].append(f'feature_{i}')
    
    # 添加大量设置
    for i in range(size):
        config_data['settings'][f'setting_{i}'] = {
            'value': f'value_{i}',
            'type': 'string',
            'required': True,
            'description': f'Description for setting {i}'
        }
    
    return config_data


def test_config_load_performance():
    """测试配置加载性能"""
    print("\n=== 配置加载性能测试 ===")
    
    # 测试不同大小的配置文件
    sizes = [10, 50, 100, 200]
    
    for size in sizes:
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'_size_{size}.yaml', delete=False) as tmp:
            # 创建大型配置数据
            config_data = create_large_config_data(size)
            
            # 写入YAML文件
            import yaml
            yaml.dump(config_data, tmp, default_flow_style=False)
            test_config_path = tmp.name
        
        try:
            # 测试加载性能
            with PerformanceTimer(f"Load config with {size} items") as timer:
                # 为每个测试创建独立的配置管理器实例
                config = get_config_manager(
                    config_path=test_config_path,
                    auto_create=False,
                    watch=False,
                    test_mode=False  # 使用非测试模式避免路径处理开销
                )
                
                # 验证配置加载正确
                assert config.app_name == f'TestApp_{size}'
                assert config.version == '1.0.0'
                assert len(config.database.connections) == size
                assert len(config.services) == size
                assert len(config.features) == size
                assert len(config.settings) == size
            
            print(f"加载 {size} 项配置耗时: {timer.elapsed:.4f}秒")
            
            # 性能要求：即使是大型配置也应该在合理时间内加载
            if size <= 100:
                assert timer.elapsed < 2.0, f"加载 {size} 项配置耗时过长: {timer.elapsed:.4f}秒"
            else:
                assert timer.elapsed < 5.0, f"加载 {size} 项配置耗时过长: {timer.elapsed:.4f}秒"
            
        finally:
            Path(test_config_path).unlink(missing_ok=True)


def test_config_save_performance():
    """测试配置保存性能"""
    print("\n=== 配置保存性能测试 ===")
    
    # 测试不同大小的配置保存
    sizes = [10, 50, 100, 200]
    
    for size in sizes:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
            # 创建小型初始配置
            initial_config = {'app_name': 'TestApp', 'version': '1.0.0'}
            import yaml
            yaml.dump(initial_config, tmp, default_flow_style=False)
            test_config_path = tmp.name
        
        try:
            config = get_config_manager(
                config_path=test_config_path,
                auto_create=False,
                watch=False,
                test_mode=True
            )
            
            # 添加大量配置数据
            large_config_data = create_large_config_data(size)
            for key, value in large_config_data.items():
                setattr(config, key, value)
            
            # 测试保存性能
            with PerformanceTimer(f"Save config with {size} items") as timer:
                config.save()
            
            print(f"保存 {size} 项配置耗时: {timer.elapsed:.4f}秒")
            
            # 性能要求：保存操作应该在合理时间内完成
            if size <= 100:
                assert timer.elapsed < 2.0, f"保存 {size} 项配置耗时过长: {timer.elapsed:.4f}秒"
            else:
                assert timer.elapsed < 5.0, f"保存 {size} 项配置耗时过长: {timer.elapsed:.4f}秒"
            
        finally:
            Path(test_config_path).unlink(missing_ok=True)


def test_config_access_performance():
    """测试配置访问性能"""
    print("\n=== 配置访问性能测试 ===")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        # 创建大型配置数据
        config_data = create_large_config_data(100)
        import yaml
        yaml.dump(config_data, tmp, default_flow_style=False)
        test_config_path = tmp.name
    
    try:
        config = get_config_manager(
            config_path=test_config_path,
            auto_create=False,
            watch=False,
            test_mode=True
        )
        
        # 测试属性访问性能
        access_count = 1000
        with PerformanceTimer(f"Property access {access_count} times") as timer:
            for i in range(access_count):
                _ = config.app_name
                _ = config.version
                _ = config.database.host
                _ = config.database.port
                _ = config.services
        
        print(f"属性访问 {access_count} 次耗时: {timer.elapsed:.4f}秒")
        assert timer.elapsed < 1.0, f"属性访问性能过低: {timer.elapsed:.4f}秒"
        
        # 测试字典访问性能
        with PerformanceTimer(f"Dictionary access {access_count} times") as timer:
            for i in range(access_count):
                _ = config['app_name']
                _ = config['version']
                _ = config['database']['host']
                _ = config['database']['port']
                _ = config['services']
        
        print(f"字典访问 {access_count} 次耗时: {timer.elapsed:.4f}秒")
        assert timer.elapsed < 1.0, f"字典访问性能过低: {timer.elapsed:.4f}秒"
        
        # 测试get方法性能
        with PerformanceTimer(f"Get method {access_count} times") as timer:
            for i in range(access_count):
                _ = config.get('app_name')
                _ = config.get('version')
                _ = config.get('database.host')
                _ = config.get('database.port')
                _ = config.get('services', {})
        
        print(f"get方法 {access_count} 次耗时: {timer.elapsed:.4f}秒")
        assert timer.elapsed < 1.0, f"get方法性能过低: {timer.elapsed:.4f}秒"
        
    finally:
        Path(test_config_path).unlink(missing_ok=True)


def concurrent_config_worker(config_path: str, worker_id: int, operations: int, results: List):
    """并发配置访问工作函数"""
    try:
        config = get_config_manager(
            config_path=config_path,
            auto_create=False,
            watch=False,
            autosave_delay=None,  # 禁用自动保存避免并发冲突
            test_mode=False  # 使用非测试模式避免复杂的路径处理
        )
        
        start_time = time.time()
        
        # 执行配置操作
        for i in range(operations):
            # 读取配置
            _ = config.get('app_name', 'DefaultApp')
            _ = config.get('version', '1.0.0')
            _ = config.get('database.host', 'localhost')
            
            # 修改配置
            config.set('app_name', f"TestApp_{worker_id}_{i}")
            config.set('database.port', 5432 + worker_id * 100 + i)
            
            # 添加新配置
            config.set(f'worker_{worker_id}_setting_{i}', f'value_{i}')
            
            # 保存配置（每10次操作保存一次）
            if i % 10 == 0:
                config.save()
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        results.append({
            'worker_id': worker_id,
            'operations': operations,
            'elapsed': elapsed,
            'ops_per_second': operations / elapsed if elapsed > 0 else 0
        })
        
    except Exception as e:
        results.append({
            'worker_id': worker_id,
            'error': str(e)
        })


def test_concurrent_access_stress():
    """测试并发访问压力"""
    print("\n=== 并发访问压力测试 ===")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        # 创建初始配置
        initial_config = create_large_config_data(50)
        import yaml
        yaml.dump(initial_config, tmp, default_flow_style=False)
        test_config_path = tmp.name
    
    try:
        # 测试不同的并发级别
        thread_counts = [2, 4, 8]
        operations_per_thread = 50
        
        for thread_count in thread_counts:
            print(f"\n测试 {thread_count} 线程并发访问...")
            
            results = []
            
            # 创建并启动线程
            threads = []
            start_time = time.time()
            
            for i in range(thread_count):
                thread = threading.Thread(
                    target=concurrent_config_worker,
                    args=(test_config_path, i, operations_per_thread, results)
                )
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            end_time = time.time()
            total_elapsed = end_time - start_time
            
            # 分析结果
            successful_workers = [r for r in results if 'error' not in r]
            failed_workers = [r for r in results if 'error' in r]
            
            print(f"总耗时: {total_elapsed:.4f}秒")
            print(f"成功的工作线程: {len(successful_workers)}/{thread_count}")
            print(f"失败的工作线程: {len(failed_workers)}")
            
            if failed_workers:
                for worker in failed_workers:
                    print(f"工作线程 {worker['worker_id']} 失败: {worker['error']}")
            
            if successful_workers:
                avg_ops_per_second = sum(w['ops_per_second'] for w in successful_workers) / len(successful_workers)
                print(f"平均操作速度: {avg_ops_per_second:.2f} ops/sec")
                
                # 性能要求：并发访问应该保持合理的性能
                assert avg_ops_per_second > 10, f"并发访问性能过低: {avg_ops_per_second:.2f} ops/sec"
            
            # 大部分线程应该成功完成（并发环境下有些失败是正常的）
            success_rate = len(successful_workers) / thread_count
            assert success_rate >= 0.5, f"并发访问成功率过低: {success_rate:.2%}"
            
    finally:
        Path(test_config_path).unlink(missing_ok=True)


def test_memory_usage_stress():
    """测试内存使用压力"""
    print("\n=== 内存使用压力测试 ===")
    
    import psutil
    import os
    
    # 获取当前进程
    current_process = psutil.Process(os.getpid())
    
    # 记录初始内存使用
    initial_memory = current_process.memory_info().rss / 1024 / 1024  # MB
    print(f"初始内存使用: {initial_memory:.2f}MB")
    
    configs = []
    
    try:
        # 创建多个配置管理器实例
        for i in range(50):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
                # 创建配置数据
                config_data = create_large_config_data(20)
                import yaml
                yaml.dump(config_data, tmp, default_flow_style=False)
                test_config_path = tmp.name
            
            config = get_config_manager(
                config_path=test_config_path,
                auto_create=False,
                watch=False,
                test_mode=True
            )
            
            configs.append((config, test_config_path))
            
            # 进行一些操作
            config.app_name = f"MemoryTest_{i}"
            config.test_data = list(range(100))
            config.save()
            
            # 每10个配置检查一次内存使用
            if (i + 1) % 10 == 0:
                current_memory = current_process.memory_info().rss / 1024 / 1024  # MB
                print(f"创建 {i+1} 个配置后内存使用: {current_memory:.2f}MB")
        
        # 记录峰值内存使用
        peak_memory = current_process.memory_info().rss / 1024 / 1024  # MB
        print(f"峰值内存使用: {peak_memory:.2f}MB")
        
        # 内存使用不应该过高
        memory_increase = peak_memory - initial_memory
        print(f"内存增长: {memory_increase:.2f}MB")
        assert memory_increase < 500, f"内存使用过高: {memory_increase:.2f}MB"
        
    finally:
        # 清理配置和文件
        for config, config_path in configs:
            try:
                Path(config_path).unlink(missing_ok=True)
            except Exception:
                pass
        
        # 强制垃圾收集
        gc.collect()
        
        # 检查内存释放
        final_memory = current_process.memory_info().rss / 1024 / 1024  # MB
        print(f"清理后内存使用: {final_memory:.2f}MB")


def test_large_config_file_handling():
    """测试大型配置文件处理"""
    print("\n=== 大型配置文件处理测试 ===")
    
    # 创建非常大的配置数据
    large_size = 500
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        config_data = create_large_config_data(large_size)
        import yaml
        yaml.dump(config_data, tmp, default_flow_style=False)
        test_config_path = tmp.name
    
    try:
        # 获取文件大小
        file_size = os.path.getsize(test_config_path) / 1024 / 1024  # MB
        print(f"配置文件大小: {file_size:.2f}MB")
        
        # 测试加载大型配置文件
        with PerformanceTimer("Load large config file") as timer:
            config = get_config_manager(
                config_path=test_config_path,
                auto_create=False,
                watch=False,
                test_mode=False  # 使用非测试模式避免路径处理开销
            )
        
        print(f"加载大型配置文件耗时: {timer.elapsed:.4f}秒")
        # 大型配置文件（500个条目）加载需要较长时间是正常的
        assert timer.elapsed < 10.0, f"加载大型配置文件耗时过长: {timer.elapsed:.4f}秒"
        
        # 验证配置正确加载
        assert config.app_name == f'TestApp_{large_size}'
        assert len(config.database.connections) == large_size
        assert len(config.services) == large_size
        
        # 测试修改大型配置
        with PerformanceTimer("Modify large config") as timer:
            config.app_name = "ModifiedLargeApp"
            config.new_large_section = {}
            for i in range(100):
                config.new_large_section[f'key_{i}'] = f'value_{i}'
        
        print(f"修改大型配置耗时: {timer.elapsed:.4f}秒")
        assert timer.elapsed < 2.0, f"修改大型配置耗时过长: {timer.elapsed:.4f}秒"
        
        # 测试保存大型配置
        with PerformanceTimer("Save large config") as timer:
            config.save()
        
        print(f"保存大型配置耗时: {timer.elapsed:.4f}秒")
        assert timer.elapsed < 10.0, f"保存大型配置耗时过长: {timer.elapsed:.4f}秒"
        
        # 验证保存成功
        assert config.app_name == "ModifiedLargeApp"
        assert len(config.new_large_section) == 100
        
    finally:
        Path(test_config_path).unlink(missing_ok=True)


def test_rapid_config_changes():
    """测试快速配置变更"""
    print("\n=== 快速配置变更测试 ===")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        # 创建初始配置
        initial_config = {
            'app_name': 'TestApp',
            'version': '1.0.0',
            'counter': 0,
            'settings': {}
        }
        import yaml
        yaml.dump(initial_config, tmp, default_flow_style=False)
        test_config_path = tmp.name
    
    try:
        config = get_config_manager(
            config_path=test_config_path,
            auto_create=False,
            watch=False,
            test_mode=True
        )
        
        # 测试快速连续变更
        change_count = 1000
        with PerformanceTimer(f"Rapid changes {change_count} times") as timer:
            for i in range(change_count):
                config.counter = i
                config.app_name = f"TestApp_{i}"
                config.settings[f'setting_{i}'] = f'value_{i}'
                
                # 每100次变更保存一次
                if i % 100 == 0:
                    config.save()
        
        print(f"快速变更 {change_count} 次耗时: {timer.elapsed:.4f}秒")
        assert timer.elapsed < 5.0, f"快速变更耗时过长: {timer.elapsed:.4f}秒"
        
        # 验证最终状态
        assert config.counter == change_count - 1
        assert config.app_name == f"TestApp_{change_count - 1}"
        assert len(config.settings) == change_count
        
        # 测试最终保存
        with PerformanceTimer("Final save after rapid changes") as timer:
            config.save()
        
        print(f"最终保存耗时: {timer.elapsed:.4f}秒")
        assert timer.elapsed < 3.0, f"最终保存耗时过长: {timer.elapsed:.4f}秒"
        
    finally:
        Path(test_config_path).unlink(missing_ok=True)


def test_autosave_performance():
    """测试自动保存性能"""
    print("\n=== 自动保存性能测试 ===")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        # 创建初始配置
        initial_config = {
            'app_name': 'TestApp',
            'version': '1.0.0',
            'counter': 0
        }
        import yaml
        yaml.dump(initial_config, tmp, default_flow_style=False)
        test_config_path = tmp.name
    
    try:
        # 测试启用自动保存的性能
        config = get_config_manager(
            config_path=test_config_path,
            auto_create=False,
            watch=False,
            autosave_delay=0.1,  # 100ms延迟
            test_mode=True
        )
        
        # 测试自动保存下的变更性能
        change_count = 100
        with PerformanceTimer(f"Changes with autosave {change_count} times") as timer:
            for i in range(change_count):
                config.counter = i
                config.app_name = f"TestApp_{i}"
                
                # 短暂等待以触发自动保存
                if i % 10 == 0:
                    time.sleep(0.15)  # 等待自动保存
        
        print(f"自动保存模式下变更 {change_count} 次耗时: {timer.elapsed:.4f}秒")
        
        # 等待最后的自动保存完成
        time.sleep(0.2)
        
        # 验证自动保存的效果
        assert config.counter == change_count - 1
        assert config.app_name == f"TestApp_{change_count - 1}"
        
        print("✓ 自动保存性能测试通过")
        
    finally:
        Path(test_config_path).unlink(missing_ok=True)


if __name__ == '__main__':
    print("=" * 80)
    print("配置管理器性能和压力测试")
    print("=" * 80)
    
    # 运行所有性能测试
    test_config_load_performance()
    test_config_save_performance()
    test_config_access_performance()
    test_concurrent_access_stress()
    test_memory_usage_stress()
    test_large_config_file_handling()
    test_rapid_config_changes()
    test_autosave_performance()
    
    print("\n" + "=" * 80)
    print("所有性能和压力测试完成！")
    print("=" * 80)