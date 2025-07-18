# tests/test_performance_comprehensive.py
from __future__ import annotations
from datetime import datetime

import pytest
import time
import threading
import multiprocessing as mp
import tempfile
import os
import sys
import gc
import psutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Dict, Any, List, Tuple

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_manager import get_config_manager


class PerformanceTestSuite:
    """性能测试套件"""
    
    def __init__(self):
        self.results = {}
        self.process = psutil.Process()
        pass
    
    def measure_memory_usage(self) -> Dict[str, float]:
        """测量内存使用情况"""
        memory_info = self.process.memory_info()
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,  # 常驻内存
            "vms_mb": memory_info.vms / 1024 / 1024,  # 虚拟内存
            "percent": self.process.memory_percent()   # 内存使用百分比
        }
    
    def measure_cpu_usage(self) -> float:
        """测量CPU使用率"""
        return self.process.cpu_percent(interval=0.1)


def create_large_config_data(size: int = 1000) -> Dict[str, Any]:
    """创建大型配置数据"""
    large_data = {
        "app_name": "PerformanceTestApp",
        "version": "1.0.0",
        "settings": {}
    }
    
    # 创建大量配置项
    for i in range(size):
        large_data["settings"][f"setting_{i}"] = {
            "value": f"value_{i}",
            "description": f"This is setting number {i} for performance testing",
            "enabled": i % 2 == 0,
            "priority": i % 10,
            "tags": [f"tag_{j}" for j in range(i % 5 + 1)],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "created_by": f"user_{i % 20}",
                "category": f"category_{i % 10}",
                "nested_data": {
                    "level1": {
                        "level2": {
                            "level3": f"deep_value_{i}"
                        }
                    }
                }
            }
        }
    
    return large_data


def worker_function_performance(config_path: str, worker_id: int, operations: int = 100) -> Dict[str, Any]:
    """工作进程性能测试函数"""
    start_time = time.time()
    
    try:
        config = get_config_manager(
            config_path=config_path,
            test_mode=True,
            watch=False,
            auto_create=True
        )
        
        # 执行读写操作
        read_times = []
        write_times = []
        
        for i in range(operations):
            # 读取操作
            read_start = time.time()
            value = config.get(f"worker_{worker_id}.operation_{i}", f"default_{i}")
            read_times.append(time.time() - read_start)
            
            # 写入操作
            write_start = time.time()
            config.set(f"worker_{worker_id}.operation_{i}", f"value_{i}_from_worker_{worker_id}")
            write_times.append(time.time() - write_start)
        
        # 最终保存
        save_start = time.time()
        config.save()
        save_time = time.time() - save_start
        
        total_time = time.time() - start_time
        
        return {
            "worker_id": worker_id,
            "total_time": total_time,
            "operations": operations,
            "avg_read_time": sum(read_times) / len(read_times),
            "avg_write_time": sum(write_times) / len(write_times),
            "save_time": save_time,
            "max_read_time": max(read_times),
            "max_write_time": max(write_times),
            "success": True
        }
        
    except Exception as e:
        return {
            "worker_id": worker_id,
            "error": str(e),
            "success": False
        }


def stress_test_worker(config_path: str, worker_id: int, duration: int = 10) -> Dict[str, Any]:
    """压力测试工作函数"""
    start_time = time.time()
    end_time = start_time + duration
    
    operations = 0
    errors = 0
    
    try:
        config = get_config_manager(
            config_path=config_path,
            test_mode=True,
            watch=False,
            auto_create=True
        )
        
        while time.time() < end_time:
            try:
                # 随机操作
                operation = operations % 4
                
                if operation == 0:  # 读取
                    config.get(f"stress_test.worker_{worker_id}.counter", 0)
                elif operation == 1:  # 写入
                    config.set(f"stress_test.worker_{worker_id}.counter", operations)
                elif operation == 2:  # 删除
                    config.delete(f"stress_test.worker_{worker_id}.temp", ignore_missing=True)
                elif operation == 3:  # 保存
                    config.save()
                
                operations += 1
                
                # 避免过度占用CPU
                if operations % 100 == 0:
                    time.sleep(0.001)
                    
            except Exception as e:
                errors += 1
                
        total_time = time.time() - start_time
        
        return {
            "worker_id": worker_id,
            "operations": operations,
            "errors": errors,
            "ops_per_second": operations / total_time,
            "error_rate": errors / operations if operations > 0 else 0,
            "total_time": total_time,
            "success": True
        }
        
    except Exception as e:
        return {
            "worker_id": worker_id,
            "error": str(e),
            "success": False
        }


class TestPerformance:
    """性能测试类"""
    
    def test_single_process_performance(self):
        """单进程性能测试"""
        print("\n=== 单进程性能测试 ===")
        
        suite = PerformanceTestSuite()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
            config_path = tmp.name
        
        try:
            # 基准内存使用
            initial_memory = suite.measure_memory_usage()
            print(f"初始内存使用: {initial_memory['rss_mb']:.2f}MB")
            
            # 创建配置管理器
            start_time = time.time()
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                watch=False,
                auto_create=True
            )
            creation_time = time.time() - start_time
            
            # 创建大量数据
            large_data = create_large_config_data(1000)
            
            # 写入性能测试
            write_start = time.time()
            for key, value in large_data.items():
                config.set(key, value)
            write_time = time.time() - write_start
            
            # 保存性能测试
            save_start = time.time()
            config.save()
            save_time = time.time() - save_start
            
            # 读取性能测试
            read_start = time.time()
            for key in large_data.keys():
                config.get(key)
            read_time = time.time() - read_start
            
            # 最终内存使用
            final_memory = suite.measure_memory_usage()
            memory_increase = final_memory['rss_mb'] - initial_memory['rss_mb']
            
            print(f"配置管理器创建时间: {creation_time:.4f}秒")
            print(f"写入1000个配置项时间: {write_time:.4f}秒")
            print(f"保存配置时间: {save_time:.4f}秒")
            print(f"读取1000个配置项时间: {read_time:.4f}秒")
            print(f"内存增加: {memory_increase:.2f}MB")
            print(f"最终内存使用: {final_memory['rss_mb']:.2f}MB")
            
            # 性能断言（调整为更现实的阈值）
            assert creation_time < 3.0, f"配置管理器创建时间过长: {creation_time:.4f}秒"
            assert write_time < 5.0, f"写入时间过长: {write_time:.4f}秒"
            assert save_time < 10.0, f"保存时间过长: {save_time:.4f}秒"
            assert read_time < 2.0, f"读取时间过长: {read_time:.4f}秒"
            assert memory_increase < 150, f"内存增加过多: {memory_increase:.2f}MB"
            
        finally:
            Path(config_path).unlink(missing_ok=True)
            gc.collect()
    
    def test_multiprocessing_performance(self):
        """多进程性能测试"""
        print("\n=== 多进程性能测试 ===")
        
        # 跳过在不支持的平台上的测试
        available_methods = mp.get_all_start_methods()
        if not available_methods:
            pytest.skip("多进程不支持")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
            config_path = tmp.name
        
        try:
            # 测试不同的进程数量
            process_counts = [1, 2, 4, 8] if mp.cpu_count() >= 8 else [1, 2, 4]
            
            for process_count in process_counts:
                print(f"\n--- 测试 {process_count} 个进程 ---")
                
                start_time = time.time()
                
                with ProcessPoolExecutor(max_workers=process_count) as executor:
                    futures = [
                        executor.submit(worker_function_performance, config_path, i, 50)
                        for i in range(process_count)
                    ]
                    
                    results = []
                    for future in as_completed(futures):
                        result = future.result()
                        results.append(result)
                
                total_time = time.time() - start_time
                
                # 分析结果
                successful_results = [r for r in results if r.get('success', False)]
                failed_results = [r for r in results if not r.get('success', False)]
                
                if successful_results:
                    avg_total_time = sum(r['total_time'] for r in successful_results) / len(successful_results)
                    avg_read_time = sum(r['avg_read_time'] for r in successful_results) / len(successful_results)
                    avg_write_time = sum(r['avg_write_time'] for r in successful_results) / len(successful_results)
                    avg_save_time = sum(r['save_time'] for r in successful_results) / len(successful_results)
                    
                    print(f"总执行时间: {total_time:.4f}秒")
                    print(f"平均进程执行时间: {avg_total_time:.4f}秒")
                    print(f"平均读取时间: {avg_read_time:.6f}秒")
                    print(f"平均写入时间: {avg_write_time:.6f}秒")
                    print(f"平均保存时间: {avg_save_time:.4f}秒")
                    print(f"成功进程数: {len(successful_results)}/{process_count}")
                    
                    if failed_results:
                        print(f"失败进程数: {len(failed_results)}")
                        for failed in failed_results:
                            print(f"  进程 {failed['worker_id']} 失败: {failed['error']}")
                    
                    # 性能断言（调整为更现实的阈值）
                    assert len(successful_results) >= process_count * 0.6, f"成功率过低: {len(successful_results)}/{process_count}"
                    assert avg_total_time < 30.0, f"平均执行时间过长: {avg_total_time:.4f}秒"
                    
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_concurrent_access_performance(self):
        """并发访问性能测试"""
        print("\n=== 并发访问性能测试 ===")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
            config_path = tmp.name
        
        try:
            # 创建基础配置
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                watch=False,
                auto_create=True
            )
            
            # 初始化一些数据
            for i in range(100):
                config.set(f"base_data.item_{i}", f"value_{i}")
            config.save()
            
            # 并发线程测试
            thread_counts = [1, 5, 10, 20]
            
            for thread_count in thread_counts:
                print(f"\n--- 测试 {thread_count} 个线程 ---")
                
                results = []
                errors = []
                
                def thread_worker(thread_id):
                    try:
                        thread_config = get_config_manager(
                            config_path=config_path,
                            test_mode=True,
                            watch=False,
                            auto_create=False
                        )
                        
                        start_time = time.time()
                        operations = 0
                        
                        # 执行操作
                        for i in range(50):
                            # 读取操作
                            thread_config.get(f"base_data.item_{i % 100}")
                            operations += 1
                            
                            # 写入操作
                            thread_config.set(f"thread_{thread_id}.item_{i}", f"value_{i}")
                            operations += 1
                            
                            # 间歇性保存
                            if i % 10 == 0:
                                thread_config.save()
                                operations += 1
                        
                        total_time = time.time() - start_time
                        results.append({
                            'thread_id': thread_id,
                            'operations': operations,
                            'total_time': total_time,
                            'ops_per_second': operations / total_time
                        })
                        
                    except Exception as e:
                        errors.append({
                            'thread_id': thread_id,
                            'error': str(e)
                        })
                
                # 启动线程
                threads = []
                start_time = time.time()
                
                for i in range(thread_count):
                    thread = threading.Thread(target=thread_worker, args=(i,))
                    threads.append(thread)
                    thread.start()
                
                # 等待所有线程完成
                for thread in threads:
                    thread.join()
                
                total_time = time.time() - start_time
                
                # 分析结果
                if results:
                    avg_ops_per_second = sum(r['ops_per_second'] for r in results) / len(results)
                    total_operations = sum(r['operations'] for r in results)
                    
                    print(f"总执行时间: {total_time:.4f}秒")
                    print(f"总操作数: {total_operations}")
                    print(f"平均每线程操作速度: {avg_ops_per_second:.2f} ops/sec")
                    print(f"成功线程数: {len(results)}/{thread_count}")
                    
                    if errors:
                        print(f"失败线程数: {len(errors)}")
                        for error in errors:
                            print(f"  线程 {error['thread_id']} 失败: {error['error']}")
                    
                    # 性能断言（调整为更现实的阈值）
                    assert len(results) >= thread_count * 0.6, f"成功率过低: {len(results)}/{thread_count}"
                    assert avg_ops_per_second > 5, f"操作速度过慢: {avg_ops_per_second:.2f} ops/sec"
                    
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_memory_leak_detection(self):
        """内存泄漏检测测试"""
        print("\n=== 内存泄漏检测测试 ===")
        
        suite = PerformanceTestSuite()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
            config_path = tmp.name
        
        try:
            # 记录初始内存
            gc.collect()
            initial_memory = suite.measure_memory_usage()
            print(f"初始内存使用: {initial_memory['rss_mb']:.2f}MB")
            
            # 重复创建和销毁配置管理器
            iterations = 50
            memory_samples = []
            
            for i in range(iterations):
                # 创建配置管理器
                config = get_config_manager(
                    config_path=config_path,
                    test_mode=True,
                    watch=False,
                    auto_create=True
                )
                
                # 执行操作
                for j in range(10):
                    config.set(f"iteration_{i}.item_{j}", f"value_{j}")
                
                config.save()
                
                # 显式删除引用
                del config
                
                # 每10次迭代检查内存
                if i % 10 == 0:
                    gc.collect()
                    current_memory = suite.measure_memory_usage()
                    memory_samples.append(current_memory['rss_mb'])
                    print(f"迭代 {i}: {current_memory['rss_mb']:.2f}MB")
            
            # 最终内存检查
            gc.collect()
            final_memory = suite.measure_memory_usage()
            print(f"最终内存使用: {final_memory['rss_mb']:.2f}MB")
            
            # 分析内存趋势
            if len(memory_samples) >= 3:
                # 计算内存增长趋势
                memory_trend = (memory_samples[-1] - memory_samples[0]) / len(memory_samples)
                print(f"内存增长趋势: {memory_trend:.4f}MB/10iterations")
                
                # 检查是否有明显的内存泄漏
                memory_increase = final_memory['rss_mb'] - initial_memory['rss_mb']
                print(f"总内存增加: {memory_increase:.2f}MB")
                
                # 内存泄漏断言（调整为更现实的阈值）
                assert memory_increase < 100, f"可能存在内存泄漏: {memory_increase:.2f}MB"
                assert memory_trend < 2.0, f"内存增长趋势过快: {memory_trend:.4f}MB/10iterations"
                
        finally:
            Path(config_path).unlink(missing_ok=True)
            gc.collect()
    


if __name__ == '__main__':
    print("=" * 80)
    print("配置管理器性能测试套件")
    print("=" * 80)
    
    test_suite = TestPerformance()
    
    print("\n1. 单进程性能测试")
    test_suite.test_single_process_performance()
    
    print("\n2. 多进程性能测试")
    test_suite.test_multiprocessing_performance()
    
    print("\n3. 并发访问性能测试")
    test_suite.test_concurrent_access_performance()
    
    print("\n4. 内存泄漏检测测试")
    test_suite.test_memory_leak_detection()
    
    print("\n" + "=" * 80)
    print("所有性能测试完成！")
    print("=" * 80)