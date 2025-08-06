# tests/test_config_manager/test_tsb_path_integration.py
from __future__ import annotations
from datetime import datetime
import os
import tempfile
import shutil
import threading
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import pytest

from config_manager import get_config_manager
from config_manager.serializable_config import SerializableConfigData


# 模块级工作进程函数，用于多进程测试
def worker_process(config_data, process_id):
    """工作进程函数 - 必须在模块级定义以支持pickle序列化"""
    try:
        # 从序列化数据重建配置
        config = SerializableConfigData.from_dict(config_data)
        
        # 访问路径
        tsb_path = config.paths.tsb_logs_dir
        tb_path = config.paths.tensorboard_dir
        
        # 返回结果
        return {
            'process_id': process_id,
            'tsb_path': tsb_path,
            'tb_path': tb_path,
            'equal': tsb_path == tb_path
        }
    except Exception as e:
        return {
            'process_id': process_id,
            'error': str(e)
        }


class TestTsbPathIntegration:
    """TSB路径功能的集成测试"""
    
    def test_complete_path_generation_workflow(self):
        """测试完整的路径生成工作流"""
        # 设置测试环境
        test_time = datetime(2025, 3, 15, 14, 30, 45)
        
        # 创建配置管理器
        config = get_config_manager(
            test_mode=True,
            auto_create=True,
            first_start_time=test_time
        )
        
        try:
            # 1. 验证基础路径设置
            assert hasattr(config, 'paths'), "配置应该有paths属性"
            assert hasattr(config.paths, 'work_dir'), "paths应该有work_dir属性"
            
            # 2. 验证TSB日志路径生成
            tsb_path = config.paths.tsb_logs_dir
            assert isinstance(tsb_path, str), "tsb_logs_dir应返回字符串"
            
            # 3. 验证路径格式
            # 2025年3月15日是第11周
            expected_components = ['tsb_logs', '2025', '11', '0315', '143045']
            for component in expected_components:
                assert component in tsb_path, (
                    f"路径应包含'{component}'，实际路径：{tsb_path}"
                )
            
            # 4. 验证tensorboard_dir等于tsb_logs_dir
            tb_path = config.paths.tensorboard_dir
            assert tb_path == tsb_path, (
                f"tensorboard_dir应等于tsb_logs_dir\n"
                f"tsb: {tsb_path}\n"
                f"tb: {tb_path}"
            )
            
            # 5. 验证路径的完整性
            assert tsb_path.startswith(config.paths.work_dir), (
                "TSB路径应该在work_dir下"
            )
            
            # 6. 验证路径创建
            os.makedirs(tsb_path, exist_ok=True)
            assert os.path.exists(tsb_path), "应该能创建TSB日志目录"
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_multiprocess_path_consistency(self):
        """测试多进程环境下的路径一致性"""
        # 创建主配置
        main_config = get_config_manager(
            test_mode=True,
            auto_create=True,
            first_start_time=datetime(2025, 1, 8, 16, 0, 0),
            watch=False  # 多进程环境关闭文件监视
        )
        
        try:
            # 获取可序列化的配置数据
            config_data = main_config.get_serializable_data().to_dict()
            
            # 使用进程池执行
            with ProcessPoolExecutor(max_workers=4) as executor:
                futures = []
                for i in range(10):
                    future = executor.submit(worker_process, config_data, i)
                    futures.append(future)
                
                # 收集结果
                results = []
                for future in futures:
                    result = future.result()
                    results.append(result)
            
            # 验证结果
            errors = [r for r in results if 'error' in r]
            assert len(errors) == 0, f"不应有错误：{errors}"
            
            # 验证所有进程获得相同的路径
            tsb_paths = [r['tsb_path'] for r in results]
            unique_tsb_paths = set(tsb_paths)
            assert len(unique_tsb_paths) == 1, (
                f"所有进程应获得相同的TSB路径，实际有{len(unique_tsb_paths)}个"
            )
            
            # 验证tensorboard_dir等于tsb_logs_dir
            all_equal = all(r['equal'] for r in results)
            assert all_equal, "所有进程中tensorboard_dir都应等于tsb_logs_dir"
            
        finally:
            if hasattr(main_config, 'cleanup'):
                main_config.cleanup()
    
    def test_path_with_config_reload(self):
        """测试配置重新加载后的路径行为"""
        # 创建临时配置文件
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_config.yaml')
            
            # 第一次创建配置
            config1 = get_config_manager(
                config_path=config_path,
                auto_create=True,
                first_start_time=datetime(2025, 1, 8, 17, 30, 0),
                autosave_delay=0.1
            )
            
            try:
                # 设置一些配置值
                config1.set('project_name', 'test_project')
                config1.set('experiment_name', 'test_exp')
                
                # 访问路径触发生成
                tsb_path1 = config1.paths.tsb_logs_dir
                tb_path1 = config1.paths.tensorboard_dir
                
                # 验证相等
                assert tb_path1 == tsb_path1
                
                # 等待自动保存
                import time
                time.sleep(0.2)
                
                # 关闭第一个配置
                if hasattr(config1, 'cleanup'):
                    config1.cleanup()
                
                # 重新加载配置
                config2 = get_config_manager(
                    config_path=config_path,
                    auto_create=False
                )
                
                try:
                    # 验证配置值保持
                    assert config2.project_name == 'test_project'
                    assert config2.experiment_name == 'test_exp'
                    
                    # 访问路径
                    tsb_path2 = config2.paths.tsb_logs_dir
                    tb_path2 = config2.paths.tensorboard_dir
                    
                    # 验证tensorboard_dir仍等于tsb_logs_dir
                    assert tb_path2 == tsb_path2
                    
                    # 路径格式应该一致
                    assert '/tsb_logs/' in tsb_path2
                    assert '/tsb_logs/' in tb_path2
                    
                finally:
                    if hasattr(config2, 'cleanup'):
                        config2.cleanup()
                        
            except Exception as e:
                if hasattr(config1, 'cleanup'):
                    config1.cleanup()
                raise e
    
    def test_path_generation_performance(self):
        """测试路径生成的性能"""
        import time
        
        config = get_config_manager(
            test_mode=True,
            auto_create=True
        )
        
        try:
            # 预热
            _ = config.paths.tsb_logs_dir
            
            # 性能测试
            iterations = 1000
            
            # 测试缓存命中性能
            start_time = time.perf_counter()
            for _ in range(iterations):
                _ = config.paths.tsb_logs_dir
            cache_time = time.perf_counter() - start_time
            
            # 等待缓存过期并测试重新生成性能
            time.sleep(1.1)
            regenerate_times = []
            for i in range(10):
                start_time = time.perf_counter()
                _ = config.paths.tsb_logs_dir
                regenerate_times.append(time.perf_counter() - start_time)
                if i < 9:
                    time.sleep(1.1)  # 确保每次都重新生成
            
            # 计算性能指标
            avg_cache_time = cache_time / iterations * 1000  # 转换为毫秒
            avg_regenerate_time = sum(regenerate_times) / len(regenerate_times) * 1000
            
            print(f"\n路径生成性能报告：")
            print(f"  缓存访问：{avg_cache_time:.3f}ms/次 ({iterations}次)")
            print(f"  重新生成：{avg_regenerate_time:.3f}ms/次 (10次)")
            print(f"  性能比率：{avg_regenerate_time/avg_cache_time:.1f}x")
            
            # 验证性能要求
            assert avg_cache_time < 0.01, (
                f"缓存访问应小于0.01ms/次，实际：{avg_cache_time:.3f}ms"
            )
            assert avg_regenerate_time < 1.0, (
                f"重新生成应小于1ms/次，实际：{avg_regenerate_time:.3f}ms"
            )
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_concurrent_thread_access(self):
        """测试多线程并发访问"""
        config = get_config_manager(
            test_mode=True,
            auto_create=True,
            first_start_time=datetime(2025, 1, 8, 18, 0, 0)
        )
        
        try:
            results = []
            errors = []
            
            def thread_worker(thread_id):
                """线程工作函数"""
                try:
                    # 每个线程访问100次
                    paths = []
                    for _ in range(100):
                        tsb = config.paths.tsb_logs_dir
                        tb = config.paths.tensorboard_dir
                        paths.append((tsb, tb))
                    
                    # 验证所有访问结果一致
                    first_tsb, first_tb = paths[0]
                    all_same = all(
                        tsb == first_tsb and tb == first_tb
                        for tsb, tb in paths
                    )
                    
                    results.append({
                        'thread_id': thread_id,
                        'success': all_same,
                        'sample_path': first_tsb
                    })
                except Exception as e:
                    errors.append({
                        'thread_id': thread_id,
                        'error': str(e)
                    })
            
            # 创建并启动线程
            threads = []
            for i in range(10):
                thread = threading.Thread(target=thread_worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            # 验证结果
            assert len(errors) == 0, f"不应有错误：{errors}"
            assert len(results) == 10, f"应有10个结果，实际：{len(results)}"
            
            # 验证所有线程获得相同路径
            sample_paths = [r['sample_path'] for r in results]
            unique_paths = set(sample_paths)
            assert len(unique_paths) == 1, (
                f"所有线程应获得相同路径，实际有{len(unique_paths)}个"
            )
            
            # 验证所有线程的一致性检查都通过
            all_success = all(r['success'] for r in results)
            assert all_success, "所有线程的路径访问应保持一致"
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_path_with_different_platforms(self):
        """测试跨平台路径处理"""
        # 保存原始的os.name
        original_os_name = os.name
        original_sep = os.sep
        
        try:
            # 测试Windows路径模拟
            os.name = 'nt'
            os.sep = '\\'
            
            config_win = get_config_manager(
                test_mode=True,
                auto_create=True
            )
            
            try:
                win_tsb_path = config_win.paths.tsb_logs_dir
                win_tb_path = config_win.paths.tensorboard_dir
                
                # 验证路径包含正确的组件（不检查分隔符，因为os.path会处理）
                assert 'tsb_logs' in win_tsb_path, (
                    f"路径应包含tsb_logs目录，实际：{win_tsb_path}"
                )
                assert win_tb_path == win_tsb_path
                
            finally:
                if hasattr(config_win, 'cleanup'):
                    config_win.cleanup()
            
            # 测试Unix路径
            os.name = 'posix'
            os.sep = '/'
            
            config_unix = get_config_manager(
                test_mode=True,
                auto_create=True
            )
            
            try:
                unix_tsb_path = config_unix.paths.tsb_logs_dir
                unix_tb_path = config_unix.paths.tensorboard_dir
                
                # 验证Unix路径格式
                assert '/tsb_logs/' in unix_tsb_path, (
                    f"Unix路径应使用正斜杠，实际：{unix_tsb_path}"
                )
                assert unix_tb_path == unix_tsb_path
                
            finally:
                if hasattr(config_unix, 'cleanup'):
                    config_unix.cleanup()
                    
        finally:
            # 恢复原始设置
            os.name = original_os_name
            os.sep = original_sep
    
    def test_path_with_large_scale_access(self):
        """测试大规模访问场景"""
        config = get_config_manager(
            test_mode=True,
            auto_create=True
        )
        
        try:
            # 使用线程池进行大规模并发访问
            access_count = 10000
            thread_count = 50
            
            paths_collected = []
            
            def access_paths(count):
                """访问路径并收集结果"""
                local_paths = []
                for _ in range(count):
                    tsb = config.paths.tsb_logs_dir
                    tb = config.paths.tensorboard_dir
                    local_paths.append((tsb, tb))
                return local_paths
            
            # 执行并发访问
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                futures = []
                per_thread = access_count // thread_count
                
                for _ in range(thread_count):
                    future = executor.submit(access_paths, per_thread)
                    futures.append(future)
                
                # 收集结果
                for future in futures:
                    paths_collected.extend(future.result())
            
            # 验证结果
            assert len(paths_collected) == access_count, (
                f"应收集{access_count}个路径对"
            )
            
            # 验证所有路径相等
            first_tsb, first_tb = paths_collected[0]
            all_equal = all(
                tsb == first_tsb and tb == first_tb and tsb == tb
                for tsb, tb in paths_collected
            )
            assert all_equal, "所有访问应返回相同且相等的路径对"
            
            print(f"\n大规模访问测试完成：")
            print(f"  总访问次数：{access_count}")
            print(f"  并发线程数：{thread_count}")
            print(f"  路径一致性：通过")
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    pass