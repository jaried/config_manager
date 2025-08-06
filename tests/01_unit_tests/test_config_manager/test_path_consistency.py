# tests/01_unit_tests/test_config_manager/test_path_consistency.py
from __future__ import annotations
from datetime import datetime
import os
import sys
import tempfile
import shutil
import threading
import time
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.path_test_helper import PathTestHelper
from config_manager import get_config_manager


class TestPathConsistency:
    """测试路径一致性功能"""
    
    def setup_method(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_tensorboard_dir_consistency(self):
        """测试tensorboard_dir与tsb_logs_dir的一致性"""
        # 创建配置管理器
        config = get_config_manager(
            test_mode=True,
            auto_create=True,
            first_start_time=datetime(2025, 1, 15, 10, 30, 45)
        )
        
        try:
            # 获取路径
            tsb_dir = config.paths.tsb_logs_dir
            tb_dir = config.paths.tensorboard_dir
            
            # 验证路径相等
            assert tb_dir == tsb_dir, "tensorboard_dir应该等于tsb_logs_dir"
            
            # 验证路径格式
            # 使用PathTestHelper进行平台无关的路径检查
            PathTestHelper.assert_path_contains(tsb_dir, "/tsb_logs/")
            PathTestHelper.assert_path_contains(tsb_dir, "/2025/03/0115/103045")  # 1月15日是第3周
            
            # 连续访问多次，确保一致性
            for i in range(10):
                assert config.paths.tensorboard_dir == config.paths.tsb_logs_dir, f"第{i+1}次访问时路径不一致"
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_readonly_tensorboard_dir(self):
        """测试tensorboard_dir的只读特性"""
        config = get_config_manager(test_mode=True, auto_create=True)
        
        try:
            # 尝试直接设置应该失败
            with pytest.raises(AttributeError) as exc_info:
                config.paths.tensorboard_dir = "/new/path"
            
            assert "只读属性" in str(exc_info.value)
            
            # 尝试通过set方法设置也应该失败
            with pytest.raises(AttributeError):
                config.set("paths.tensorboard_dir", "/new/path")
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_dynamic_path_update(self):
        """测试动态路径更新（缓存机制）"""
        config = get_config_manager(test_mode=True, auto_create=True)
        
        try:
            # 获取初始路径
            initial_tsb = config.paths.tsb_logs_dir
            initial_tb = config.paths.tensorboard_dir
            
            # 验证初始一致性
            assert initial_tb == initial_tsb
            
            # 多次访问应该返回相同的路径（缓存期内）
            for _ in range(5):
                assert config.paths.tsb_logs_dir == initial_tsb
                assert config.paths.tensorboard_dir == initial_tb
            
            # 等待缓存过期
            time.sleep(1.1)
            
            # 再次获取路径
            new_tsb = config.paths.tsb_logs_dir
            new_tb = config.paths.tensorboard_dir
            
            # 验证新的一致性
            assert new_tb == new_tsb
            
            # 如果使用了固定的first_start_time，路径不会改变
            # 这个测试主要验证缓存机制和一致性，而不是时间戳变化
            if hasattr(config, 'first_start_time') and config.first_start_time:
                # 使用固定时间，路径应该相同
                assert initial_tsb == new_tsb, "使用固定first_start_time时路径应保持不变"
            else:
                # 否则时间戳可能会更新（取决于系统时间的精度）
                pass
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_multithread_access(self):
        """测试多线程访问的一致性"""
        config = get_config_manager(test_mode=True, auto_create=True)
        results = {'consistent': True, 'errors': []}
        
        def access_paths(thread_id):
            """在线程中访问路径"""
            try:
                for i in range(50):
                    tsb = config.paths.tsb_logs_dir
                    tb = config.paths.tensorboard_dir
                    
                    if tb != tsb:
                        results['consistent'] = False
                        results['errors'].append(f"线程{thread_id}第{i}次访问不一致: tb={tb}, tsb={tsb}")
                    
                    # 短暂休眠，增加并发冲突的可能性
                    time.sleep(0.001)
                    
            except Exception as e:
                results['consistent'] = False
                results['errors'].append(f"线程{thread_id}异常: {e}")
        
        try:
            # 创建多个线程
            threads = []
            for i in range(5):
                thread = threading.Thread(target=access_paths, args=(i,))
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join(timeout=10)
            
            # 验证结果
            assert results['consistent'], f"多线程访问不一致: {results['errors']}"
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_work_dir_dependency(self):
        """测试tsb_logs_dir对work_dir的依赖"""
        config = get_config_manager(test_mode=True, auto_create=True)
        
        try:
            # 获取初始路径
            initial_work_dir = config.paths.work_dir
            initial_tsb = config.paths.tsb_logs_dir
            
            # 验证tsb_logs_dir包含work_dir
            # 规范化路径后进行比较
            norm_tsb = PathTestHelper.normalize_path(initial_tsb)
            norm_work = PathTestHelper.normalize_path(initial_work_dir)
            assert norm_tsb.startswith(norm_work), "tsb_logs_dir应该在work_dir下"
            
            # 验证路径结构
            relative_path = norm_tsb[len(norm_work):].lstrip('/')
            parts = relative_path.split('/')
            
            assert parts[0] == "tsb_logs", "第一级应该是tsb_logs"
            assert len(parts[1]) == 4 and parts[1].isdigit(), "第二级应该是4位年份"
            assert len(parts[2]) == 2 and parts[2].isdigit(), "第三级应该是2位周数"
            assert len(parts[3]) == 4 and parts[3].isdigit(), "第四级应该是4位月日"
            assert len(parts[4]) == 6 and parts[4].isdigit(), "第五级应该是6位时间"
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_first_start_time_usage(self):
        """测试first_start_time在路径生成中的使用"""
        # 测试指定的first_start_time
        fixed_time = datetime(2025, 7, 1, 12, 0, 0)  # 7月1日，大约第27周
        config = get_config_manager(
            test_mode=True,
            auto_create=True,
            first_start_time=fixed_time
        )
        
        try:
            tsb_dir = config.paths.tsb_logs_dir
            
            # 验证使用了指定的时间
            PathTestHelper.assert_path_contains(
                tsb_dir, 
                "/2025/27/0701/120000", 
                f"应该使用指定的first_start_time生成路径，实际: {tsb_dir}"
            )
            
            # 多次访问应该使用相同的时间（在缓存期内）
            for _ in range(3):
                assert config.paths.tsb_logs_dir == tsb_dir
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_path_normalization(self):
        """测试路径规范化"""
        config = get_config_manager(test_mode=True, auto_create=True)
        
        try:
            tsb_dir = config.paths.tsb_logs_dir
            tb_dir = config.paths.tensorboard_dir
            
            # 路径应该是规范化的（没有多余的斜杠等）
            assert "//" not in tsb_dir, "路径不应包含双斜杠"
            assert not tsb_dir.endswith("/"), "路径不应以斜杠结尾"
            
            # 两个路径应该使用相同的规范化
            assert tsb_dir == tb_dir
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_error_handling(self):
        """测试错误处理"""
        # 创建一个没有work_dir的配置
        config = get_config_manager(test_mode=True, auto_create=False)
        
        try:
            # 如果work_dir不存在，应该能优雅处理
            if not hasattr(config.paths, 'work_dir'):
                with pytest.raises((ValueError, AttributeError)):
                    _ = config.paths.tsb_logs_dir
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_cache_performance(self):
        """测试缓存性能"""
        config = get_config_manager(test_mode=True, auto_create=True)
        
        try:
            # 预热
            _ = config.paths.tsb_logs_dir
            
            # 测试缓存访问性能
            start_time = time.time()
            for _ in range(1000):
                _ = config.paths.tsb_logs_dir
            cached_time = time.time() - start_time
            
            # 等待缓存过期
            time.sleep(1.1)
            
            # 测试非缓存访问性能（只测一次，避免重新缓存）
            start_time = time.time()
            _ = config.paths.tsb_logs_dir
            uncached_time = time.time() - start_time
            
            # 缓存访问应该明显更快
            print(f"缓存访问1000次耗时: {cached_time:.4f}秒")
            print(f"非缓存访问1次耗时: {uncached_time:.4f}秒")
            
            # 平均每次缓存访问应该远快于非缓存访问
            assert (cached_time / 1000) < uncached_time, "缓存访问应该更快"
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()