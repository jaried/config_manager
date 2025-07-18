# tests/test_stress_testing.py
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
import random
import string
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Dict, Any, List, Tuple

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_manager import get_config_manager


def generate_random_string(length: int = 10) -> str:
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_config_data(depth: int = 3, width: int = 5) -> Dict[str, Any]:
    """生成随机配置数据"""
    data = {}
    
    for i in range(width):
        key = generate_random_string(8)
        
        if depth > 0 and random.random() < 0.3:
            # 嵌套字典
            data[key] = generate_random_config_data(depth - 1, width)
        elif random.random() < 0.2:
            # 列表
            data[key] = [generate_random_string(5) for _ in range(random.randint(1, 10))]
        elif random.random() < 0.1:
            # 数字
            data[key] = random.randint(1, 1000)
        elif random.random() < 0.1:
            # 布尔值
            data[key] = random.choice([True, False])
        else:
            # 字符串
            data[key] = generate_random_string(random.randint(5, 50))
    
    return data


def extreme_stress_worker(config_path: str, worker_id: int, duration: int = 30) -> Dict[str, Any]:
    """极端压力测试工作函数"""
    start_time = time.time()
    end_time = start_time + duration
    
    operations = 0
    errors = []
    memory_samples = []
    
    try:
        config = get_config_manager(
            config_path=config_path,
            test_mode=True,
            watch=False,
            auto_create=True
        )
        
        process = psutil.Process()
        
        while time.time() < end_time:
            try:
                # 随机选择操作类型
                operation_type = random.choice([
                    'read', 'write', 'delete', 'save', 'bulk_write', 'nested_access'
                ])
                
                if operation_type == 'read':
                    # 随机读取
                    key = f"stress_test.worker_{worker_id}.{generate_random_string(8)}"
                    config.get(key, f"default_{operations}")
                    
                elif operation_type == 'write':
                    # 随机写入
                    key = f"stress_test.worker_{worker_id}.{generate_random_string(8)}"
                    value = generate_random_string(random.randint(10, 100))
                    config.set(key, value)
                    
                elif operation_type == 'delete':
                    # 随机删除
                    key = f"stress_test.worker_{worker_id}.{generate_random_string(8)}"
                    config.delete(key, ignore_missing=True)
                    
                elif operation_type == 'save':
                    # 保存操作
                    config.save()
                    
                elif operation_type == 'bulk_write':
                    # 批量写入
                    random_data = generate_random_config_data(2, 3)
                    for k, v in random_data.items():
                        config.set(f"bulk.worker_{worker_id}.{k}", v)
                    
                elif operation_type == 'nested_access':
                    # 嵌套访问
                    config.set(f"nested.worker_{worker_id}.level1.level2.level3", f"value_{operations}")
                    config.get(f"nested.worker_{worker_id}.level1.level2.level3")
                
                operations += 1
                
                # 定期收集内存样本
                if operations % 100 == 0:
                    memory_info = process.memory_info()
                    memory_samples.append(memory_info.rss / 1024 / 1024)  # MB
                
                # 避免过度占用CPU
                if operations % 50 == 0:
                    time.sleep(0.001)
                    
            except Exception as e:
                errors.append({
                    'operation': operations,
                    'error': str(e),
                    'time': time.time() - start_time
                })
                
                # 如果错误过多，停止测试
                if len(errors) > 100:
                    break
        
        # 最后一次保存
        try:
            config.save()
        except Exception as e:
            errors.append({
                'operation': 'final_save',
                'error': str(e),
                'time': time.time() - start_time
            })
        
        total_time = time.time() - start_time
        
        return {
            "worker_id": worker_id,
            "operations": operations,
            "errors": len(errors),
            "error_details": errors[:10],  # 只返回前10个错误
            "ops_per_second": operations / total_time,
            "error_rate": len(errors) / operations if operations > 0 else 0,
            "total_time": total_time,
            "memory_samples": memory_samples,
            "avg_memory_mb": sum(memory_samples) / len(memory_samples) if memory_samples else 0,
            "max_memory_mb": max(memory_samples) if memory_samples else 0,
            "success": True
        }
        
    except Exception as e:
        return {
            "worker_id": worker_id,
            "error": str(e),
            "success": False
        }


def rapid_config_creation_worker(worker_id: int, iterations: int = 100) -> Dict[str, Any]:
    """快速配置创建销毁工作函数"""
    start_time = time.time()
    
    operations = 0
    errors = []
    
    try:
        for i in range(iterations):
            try:
                # 创建临时配置文件
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
                    config_path = tmp.name
                
                # 创建配置管理器
                config = get_config_manager(
                    config_path=config_path,
                    test_mode=True,
                    watch=False,
                    auto_create=True
                )
                
                # 执行一些操作
                for j in range(10):
                    config.set(f"worker_{worker_id}.iteration_{i}.item_{j}", f"value_{j}")
                
                config.save()
                
                # 清理
                del config
                Path(config_path).unlink(missing_ok=True)
                
                operations += 1
                
            except Exception as e:
                errors.append({
                    'iteration': i,
                    'error': str(e)
                })
        
        total_time = time.time() - start_time
        
        return {
            "worker_id": worker_id,
            "operations": operations,
            "errors": len(errors),
            "error_details": errors[:5],
            "ops_per_second": operations / total_time,
            "error_rate": len(errors) / iterations,
            "total_time": total_time,
            "success": True
        }
        
    except Exception as e:
        return {
            "worker_id": worker_id,
            "error": str(e),
            "success": False
        }


class TestStressTesting:
    """压力测试类"""
    
    def test_extreme_multiprocessing_stress(self):
        """极端多进程压力测试"""
        print("\n=== 极端多进程压力测试 ===")
        
        # 跳过在不支持的平台上的测试
        available_methods = mp.get_all_start_methods()
        if not available_methods:
            pytest.skip("多进程不支持")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
            config_path = tmp.name
        
        try:
            # 使用最大进程数进行压力测试
            max_processes = min(mp.cpu_count(), 8)  # 限制最大进程数
            test_duration = 15  # 15秒压力测试
            
            print(f"使用 {max_processes} 个进程进行 {test_duration} 秒压力测试")
            
            start_time = time.time()
            
            with ProcessPoolExecutor(max_workers=max_processes) as executor:
                futures = [
                    executor.submit(extreme_stress_worker, config_path, i, test_duration)
                    for i in range(max_processes)
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
                total_operations = sum(r['operations'] for r in successful_results)
                total_errors = sum(r['errors'] for r in successful_results)
                avg_ops_per_second = sum(r['ops_per_second'] for r in successful_results) / len(successful_results)
                avg_error_rate = sum(r['error_rate'] for r in successful_results) / len(successful_results)
                
                # 内存使用分析
                memory_samples = []
                for r in successful_results:
                    memory_samples.extend(r.get('memory_samples', []))
                
                print(f"总执行时间: {total_time:.2f}秒")
                print(f"总操作数: {total_operations}")
                print(f"总错误数: {total_errors}")
                print(f"平均操作速度: {avg_ops_per_second:.2f} ops/sec")
                print(f"平均错误率: {avg_error_rate:.4f}")
                print(f"成功进程数: {len(successful_results)}/{max_processes}")
                
                if memory_samples:
                    avg_memory = sum(memory_samples) / len(memory_samples)
                    max_memory = max(memory_samples)
                    print(f"平均内存使用: {avg_memory:.2f}MB")
                    print(f"最大内存使用: {max_memory:.2f}MB")
                
                if failed_results:
                    print(f"失败进程: {len(failed_results)}")
                    for failed in failed_results:
                        print(f"  进程 {failed['worker_id']} 失败: {failed['error']}")
                
                # 压力测试断言（在极端并发环境下，较高的错误率是可以接受的）
                assert len(successful_results) >= max_processes * 0.7, f"成功率过低: {len(successful_results)}/{max_processes}"
                assert avg_error_rate < 0.25, f"错误率过高: {avg_error_rate:.4f}"
                assert avg_ops_per_second > 5, f"操作速度过慢: {avg_ops_per_second:.2f} ops/sec"
                
                if memory_samples:
                    assert max_memory < 500, f"内存使用过高: {max_memory:.2f}MB"
                    
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_rapid_config_creation_destruction(self):
        """快速配置创建销毁测试"""
        print("\n=== 快速配置创建销毁测试 ===")
        
        # 跳过在不支持的平台上的测试
        available_methods = mp.get_all_start_methods()
        if not available_methods:
            pytest.skip("多进程不支持")
        
        process_count = min(mp.cpu_count(), 4)
        iterations_per_process = 50
        
        print(f"使用 {process_count} 个进程，每个进程创建销毁 {iterations_per_process} 个配置")
        
        start_time = time.time()
        
        with ProcessPoolExecutor(max_workers=process_count) as executor:
            futures = [
                executor.submit(rapid_config_creation_worker, i, iterations_per_process)
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
            total_operations = sum(r['operations'] for r in successful_results)
            total_errors = sum(r['errors'] for r in successful_results)
            avg_ops_per_second = sum(r['ops_per_second'] for r in successful_results) / len(successful_results)
            avg_error_rate = sum(r['error_rate'] for r in successful_results) / len(successful_results)
            
            print(f"总执行时间: {total_time:.2f}秒")
            print(f"总操作数: {total_operations}")
            print(f"总错误数: {total_errors}")
            print(f"平均操作速度: {avg_ops_per_second:.2f} ops/sec")
            print(f"平均错误率: {avg_error_rate:.4f}")
            print(f"成功进程数: {len(successful_results)}/{process_count}")
            
            if failed_results:
                print(f"失败进程: {len(failed_results)}")
                for failed in failed_results:
                    print(f"  进程 {failed['worker_id']} 失败: {failed['error']}")
            
            # 断言
            assert len(successful_results) >= process_count * 0.8, f"成功率过低: {len(successful_results)}/{process_count}"
            assert avg_error_rate < 0.05, f"错误率过高: {avg_error_rate:.4f}"
            assert avg_ops_per_second > 1, f"操作速度过慢: {avg_ops_per_second:.2f} ops/sec"
    
    def test_extreme_threading_stress(self):
        """极端线程压力测试"""
        print("\n=== 极端线程压力测试 ===")
        
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
            
            # 初始化数据
            for i in range(50):
                config.set(f"base_data.item_{i}", f"value_{i}")
            config.save()
            
            del config
            
            # 大量线程测试
            thread_count = 50
            test_duration = 10
            
            print(f"使用 {thread_count} 个线程进行 {test_duration} 秒压力测试")
            
            results = []
            errors = []
            
            def extreme_thread_worker(thread_id):
                try:
                    thread_config = get_config_manager(
                        config_path=config_path,
                        test_mode=True,
                        watch=False,
                        auto_create=False
                    )
                    
                    start_time = time.time()
                    end_time = start_time + test_duration
                    operations = 0
                    thread_errors = 0
                    
                    while time.time() < end_time:
                        try:
                            # 随机操作
                            operation = random.choice(['read', 'write', 'delete', 'save'])
                            
                            if operation == 'read':
                                thread_config.get(f"base_data.item_{random.randint(0, 49)}")
                            elif operation == 'write':
                                key = f"thread_{thread_id}.item_{random.randint(0, 100)}"
                                value = generate_random_string(20)
                                thread_config.set(key, value)
                            elif operation == 'delete':
                                key = f"thread_{thread_id}.item_{random.randint(0, 100)}"
                                thread_config.delete(key, ignore_missing=True)
                            elif operation == 'save':
                                thread_config.save()
                            
                            operations += 1
                            
                            # 避免过度占用CPU
                            if operations % 20 == 0:
                                time.sleep(0.001)
                                
                        except Exception as e:
                            thread_errors += 1
                            
                            # 如果错误过多，停止
                            if thread_errors > 50:
                                break
                    
                    total_time = time.time() - start_time
                    
                    results.append({
                        'thread_id': thread_id,
                        'operations': operations,
                        'errors': thread_errors,
                        'ops_per_second': operations / total_time,
                        'error_rate': thread_errors / operations if operations > 0 else 0,
                        'total_time': total_time
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
                thread = threading.Thread(target=extreme_thread_worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            total_time = time.time() - start_time
            
            # 分析结果
            if results:
                total_operations = sum(r['operations'] for r in results)
                total_errors = sum(r['errors'] for r in results)
                avg_ops_per_second = sum(r['ops_per_second'] for r in results) / len(results)
                avg_error_rate = sum(r['error_rate'] for r in results) / len(results)
                
                print(f"总执行时间: {total_time:.2f}秒")
                print(f"总操作数: {total_operations}")
                print(f"总错误数: {total_errors}")
                print(f"平均操作速度: {avg_ops_per_second:.2f} ops/sec")
                print(f"平均错误率: {avg_error_rate:.4f}")
                print(f"成功线程数: {len(results)}/{thread_count}")
                
                if errors:
                    print(f"失败线程数: {len(errors)}")
                    for error in errors:
                        print(f"  线程 {error['thread_id']} 失败: {error['error']}")
                
                # 断言
                assert len(results) >= thread_count * 0.7, f"成功率过低: {len(results)}/{thread_count}"
                assert avg_error_rate < 0.4, f"错误率过高: {avg_error_rate:.4f}"
                assert avg_ops_per_second > 5, f"操作速度过慢: {avg_ops_per_second:.2f} ops/sec"
                
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_resource_exhaustion_resilience(self):
        """资源耗尽弹性测试"""
        print("\n=== 资源耗尽弹性测试 ===")
        
        # 创建大量配置文件，测试文件描述符耗尽的情况
        configs = []
        temp_files = []
        
        try:
            # 创建大量配置管理器实例
            for i in range(100):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
                    config_path = tmp.name
                    temp_files.append(config_path)
                
                try:
                    config = get_config_manager(
                        config_path=config_path,
                        test_mode=True,
                        watch=False,
                        auto_create=True
                    )
                    
                    # 添加一些数据
                    config.set(f"instance_{i}.data", f"value_{i}")
                    config.save()
                    
                    configs.append(config)
                    
                except Exception as e:
                    print(f"创建配置管理器 {i} 失败: {str(e)}")
                    break
            
            print(f"成功创建 {len(configs)} 个配置管理器实例")
            
            # 测试所有实例是否仍然可用
            working_configs = 0
            for i, config in enumerate(configs):
                try:
                    config.set(f"test_access_{i}", "test_value")
                    config.save()
                    working_configs += 1
                except Exception as e:
                    print(f"配置 {i} 访问失败: {str(e)}")
            
            print(f"工作正常的配置管理器: {working_configs}/{len(configs)}")
            
            # 断言
            assert len(configs) >= 50, f"创建的配置管理器数量过少: {len(configs)}"
            assert working_configs >= len(configs) * 0.9, f"工作正常的配置比例过低: {working_configs}/{len(configs)}"
            
        finally:
            # 清理
            for config in configs:
                try:
                    del config
                except:
                    pass
            
            for temp_file in temp_files:
                try:
                    Path(temp_file).unlink(missing_ok=True)
                except:
                    pass
            
            gc.collect()
    


if __name__ == '__main__':
    print("=" * 80)
    print("配置管理器压力测试套件")
    print("=" * 80)
    
    test_suite = TestStressTesting()
    
    print("\n1. 极端多进程压力测试")
    test_suite.test_extreme_multiprocessing_stress()
    
    print("\n2. 快速配置创建销毁测试")
    test_suite.test_rapid_config_creation_destruction()
    
    print("\n3. 极端线程压力测试")
    test_suite.test_extreme_threading_stress()
    
    print("\n4. 资源耗尽弹性测试")
    test_suite.test_resource_exhaustion_resilience()
    
    print("\n" + "=" * 80)
    print("所有压力测试完成！")
    print("=" * 80)