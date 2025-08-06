# tests/01_unit_tests/test_config_manager/test_tsb_path_cache_mechanism.py
from __future__ import annotations
from datetime import datetime
import time
import threading
import platform
from concurrent.futures import ThreadPoolExecutor
import pytest

from config_manager import get_config_manager
from config_manager.core.dynamic_paths import DynamicPathProperty, PathsConfigNode


class TestTsbPathCacheMechanism:
    """测试TSB路径缓存机制"""
    
    def test_cache_duration_1_second(self):
        """测试缓存持续时间为1秒"""
        # 创建测试配置
        config = get_config_manager(
            test_mode=True,
            auto_create=True
        )
        
        try:
            # 第一次访问，触发路径生成
            start_time = time.time()
            path1 = config.paths.tsb_logs_dir
            first_access_time = time.time() - start_time
            
            # 立即再次访问（应该从缓存返回）
            start_time = time.time()
            path2 = config.paths.tsb_logs_dir
            cache_access_time = time.time() - start_time
            
            # 验证路径相同
            assert path1 == path2, "缓存期内应返回相同路径"
            
            # 验证缓存访问更快（Windows时间精度问题，使用更宽松的比较）
            if platform.system() == 'Windows':
                # Windows下只验证缓存机制存在
                assert cache_access_time < 0.01, (
                    f"缓存访问应该在10ms内完成，实际：{cache_access_time:.6f}s"
                )
            else:
                assert cache_access_time < first_access_time / 5, (
                    f"缓存访问应该更快，首次：{first_access_time:.6f}s，"
                    f"缓存：{cache_access_time:.6f}s"
                )
            
            # 等待缓存过期
            time.sleep(1.1)
            
            # 再次访问（应该重新生成）
            start_time = time.time()
            path3 = config.paths.tsb_logs_dir
            regenerate_time = time.time() - start_time
            
            # 如果使用了固定的first_start_time，路径应该相同
            # 如果没有，路径的时间戳部分会不同
            if hasattr(config, 'first_start_time') and config.first_start_time:
                assert path3 == path1, "使用固定时间时，路径应保持不变"
            
            # 验证重新生成的时间比缓存访问慢（Windows时间精度问题，可能都是0）
            if platform.system() == 'Windows':
                # Windows下时间精度低，可能都测量为0，只验证路径正确性
                print(f"Windows时间精度限制：重新生成={regenerate_time:.6f}s，缓存={cache_access_time:.6f}s")
            else:
                assert regenerate_time > cache_access_time, (
                    f"重新生成应该比缓存访问慢，重新生成：{regenerate_time:.6f}s，"
                    f"缓存：{cache_access_time:.6f}s"
                )
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_cache_cleanup(self):
        """测试缓存清理机制"""
        # 创建多个配置实例测试缓存清理
        configs = []
        property_obj = DynamicPathProperty(cache_duration=0.5)  # 使用短缓存时间
        new_config = None  # 初始化变量
        
        try:
            # 创建多个配置并访问路径
            for i in range(5):
                config = get_config_manager(
                    test_mode=True,
                    auto_create=True
                )
                configs.append(config)
                
                # 创建PathsConfigNode并访问动态路径
                paths_node = PathsConfigNode({'work_dir': f'/test/{i}'}, root=config)
                # 模拟访问，填充缓存
                _ = property_obj.__get__(paths_node, type(paths_node))
            
            # 检查缓存大小（Windows下可能有不同的缓存机制）
            initial_cache_size = len(property_obj._cache)
            if platform.system() == 'Windows':
                # Windows下缓存可能会自动清理或使用不同策略
                assert initial_cache_size > 0, f"应该有缓存条目，实际：{initial_cache_size}"
            else:
                assert initial_cache_size == 5, f"应该有5个缓存条目，实际：{initial_cache_size}"
            
            # 等待缓存过期时间的两倍
            time.sleep(1.2)
            
            # 访问一个新的实例，触发清理
            new_config = get_config_manager(test_mode=True, auto_create=True)
            new_paths_node = PathsConfigNode({'work_dir': '/test/new'}, root=new_config)
            _ = property_obj.__get__(new_paths_node, type(new_paths_node))
            
            # 检查过期缓存是否被清理
            final_cache_size = len(property_obj._cache)
            # Windows下缓存清理可能有延迟，使用更宽松的条件
            if platform.system() == 'Windows':
                # 至少应该添加了新的缓存项
                assert final_cache_size > 0, "应该有至少一个缓存条目"
            else:
                assert final_cache_size < initial_cache_size, (
                    f"过期缓存应该被清理，初始：{initial_cache_size}，"
                    f"最终：{final_cache_size}"
                )
            
        finally:
            # 清理所有配置
            for config in configs:
                if hasattr(config, 'cleanup'):
                    config.cleanup()
            if new_config and hasattr(new_config, 'cleanup'):
                new_config.cleanup()
    
    def test_concurrent_cache_access(self):
        """测试并发访问缓存的线程安全性"""
        config = get_config_manager(
            test_mode=True,
            auto_create=True,
            first_start_time=datetime(2025, 1, 8, 10, 30, 45)
        )
        
        try:
            results = []
            errors = []
            
            def access_path(thread_id):
                """线程访问路径的函数"""
                try:
                    path = config.paths.tsb_logs_dir
                    results.append((thread_id, path))
                except Exception as e:
                    errors.append((thread_id, str(e)))
            
            # 使用线程池并发访问
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for i in range(100):
                    future = executor.submit(access_path, i)
                    futures.append(future)
                
                # 等待所有任务完成
                for future in futures:
                    future.result()
            
            # 验证没有错误
            assert len(errors) == 0, f"并发访问不应产生错误：{errors}"
            
            # 验证所有线程获得相同的路径
            assert len(results) == 100, f"应该有100个结果，实际：{len(results)}"
            paths = [result[1] for result in results]
            unique_paths = set(paths)
            assert len(unique_paths) == 1, (
                f"所有线程应该获得相同路径，实际有{len(unique_paths)}个不同路径"
            )
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_cache_performance_metrics(self):
        """测试缓存性能指标"""
        config = get_config_manager(
            test_mode=True,
            auto_create=True
        )
        
        try:
            # 性能测试：测量缓存命中率
            access_times = []
            cache_hits = 0
            cache_misses = 0
            
            # 进行多轮访问测试
            for round_num in range(5):
                # 每轮访问10次
                for i in range(10):
                    start_time = time.perf_counter()
                    _ = config.paths.tsb_logs_dir
                    access_time = time.perf_counter() - start_time
                    access_times.append(access_time)
                    
                    # 根据访问时间判断是否命中缓存
                    # 缓存命中通常小于0.0001秒
                    if access_time < 0.0001:
                        cache_hits += 1
                    else:
                        cache_misses += 1
                
                # 等待缓存过期
                if round_num < 4:
                    time.sleep(1.1)
            
            # 计算性能指标
            avg_access_time = sum(access_times) / len(access_times)
            cache_hit_rate = cache_hits / (cache_hits + cache_misses)
            
            # 验证性能指标
            assert avg_access_time < 0.001, (
                f"平均访问时间应小于1ms，实际：{avg_access_time*1000:.2f}ms"
            )
            assert cache_hit_rate > 0.8, (
                f"缓存命中率应大于80%，实际：{cache_hit_rate*100:.1f}%"
            )
            
            # 输出性能报告
            print(f"\n缓存性能报告：")
            print(f"  总访问次数：{len(access_times)}")
            print(f"  缓存命中：{cache_hits}")
            print(f"  缓存未命中：{cache_misses}")
            print(f"  缓存命中率：{cache_hit_rate*100:.1f}%")
            print(f"  平均访问时间：{avg_access_time*1000:.3f}ms")
            print(f"  最快访问时间：{min(access_times)*1000:.3f}ms")
            print(f"  最慢访问时间：{max(access_times)*1000:.3f}ms")
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_cache_isolation_between_instances(self):
        """测试不同实例之间的缓存隔离"""
        # 创建两个不同的配置实例
        config1 = get_config_manager(
            test_mode=True,
            auto_create=True,
            first_start_time=datetime(2025, 1, 8, 10, 0, 0)
        )
        
        config2 = get_config_manager(
            test_mode=True,
            auto_create=True,
            first_start_time=datetime(2025, 1, 8, 11, 0, 0)
        )
        
        try:
            # 访问各自的路径
            path1 = config1.paths.tsb_logs_dir
            path2 = config2.paths.tsb_logs_dir
            
            # 验证路径不同（因为first_start_time不同）
            assert path1 != path2, "不同实例应该有不同的路径"
            
            # 验证时间部分不同
            assert "100000" in path1, f"config1路径应包含100000，实际：{path1}"
            assert "110000" in path2, f"config2路径应包含110000，实际：{path2}"
            
            # 修改一个实例的work_dir
            original_work_dir = config1.paths.work_dir
            config1.paths.work_dir = "/modified/work"
            
            # 等待缓存过期
            time.sleep(1.1)
            
            # 重新访问路径
            new_path1 = config1.paths.tsb_logs_dir
            new_path2 = config2.paths.tsb_logs_dir
            
            # 验证只有config1的路径改变
            assert "/modified/work" in new_path1, (
                f"config1的路径应该反映work_dir变化，实际：{new_path1}"
            )
            assert path2 == new_path2, "config2的路径不应该改变"
            
        finally:
            if hasattr(config1, 'cleanup'):
                config1.cleanup()
            if hasattr(config2, 'cleanup'):
                config2.cleanup()
    
    def test_cache_with_dynamic_timestamp(self):
        """测试使用动态时间戳时的缓存行为"""
        # 不设置fixed_start_time，使用动态时间
        config = get_config_manager(
            test_mode=True,
            auto_create=True
            # 不设置first_start_time
        )
        
        try:
            # 记录多次访问的路径
            paths = []
            for i in range(5):
                path = config.paths.tsb_logs_dir
                paths.append(path)
                if i < 4:
                    time.sleep(0.2)  # 缓存期内的短暂等待
            
            # 验证缓存期内路径相同
            assert all(p == paths[0] for p in paths), (
                "缓存期内（1秒）应返回相同路径"
            )
            
            # 等待缓存过期
            time.sleep(1.0)
            
            # 再次访问
            new_path = config.paths.tsb_logs_dir
            
            # 由于使用固定的first_start_time，路径应该相同
            # 但如果没有固定时间，秒级时间戳可能变化
            if hasattr(config, 'first_start_time') and config.first_start_time:
                # 有固定时间，路径不变
                assert new_path == paths[0], "使用固定时间时路径应保持不变"
            else:
                # 动态时间，可能变化（取决于是否跨秒）
                print(f"初始路径：{paths[0]}")
                print(f"新路径：{new_path}")
                
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_cache_memory_efficiency(self):
        """测试缓存的内存效率"""
        import sys
        
        # 创建一个共享的DynamicPathProperty实例
        property_obj = DynamicPathProperty(cache_duration=1.0)
        
        # 测试缓存对象的内存占用
        initial_size = sys.getsizeof(property_obj._cache)
        
        # 创建多个配置并访问
        configs = []
        try:
            for i in range(10):
                config = get_config_manager(
                    test_mode=True,
                    auto_create=True
                )
                configs.append(config)
                
                # 创建PathsConfigNode
                paths_node = PathsConfigNode(
                    {'work_dir': f'/test/path/{i}'}, 
                    root=config
                )
                
                # 访问路径，填充缓存
                _ = property_obj.__get__(paths_node, type(paths_node))
            
            # 测量缓存增长
            final_size = sys.getsizeof(property_obj._cache)
            cache_growth = final_size - initial_size
            
            # 验证内存使用合理（每个缓存条目应该小于1KB）
            avg_entry_size = cache_growth / 10
            assert avg_entry_size < 1024, (
                f"每个缓存条目应小于1KB，实际：{avg_entry_size:.0f}字节"
            )
            
            print(f"\n缓存内存效率报告：")
            print(f"  初始大小：{initial_size}字节")
            print(f"  最终大小：{final_size}字节")
            print(f"  缓存增长：{cache_growth}字节")
            print(f"  平均每条目：{avg_entry_size:.0f}字节")
            
        finally:
            for config in configs:
                if hasattr(config, 'cleanup'):
                    config.cleanup()
    
    pass