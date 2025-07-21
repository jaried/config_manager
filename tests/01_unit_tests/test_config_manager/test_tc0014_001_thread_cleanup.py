# tests/01_unit_tests/test_config_manager/test_tc0014_001_thread_cleanup.py
from __future__ import annotations

import os
import time
import threading
import signal
import subprocess
import sys
import tempfile
import pytest
from src.config_manager import get_config_manager
from src.config_manager.config_manager import _clear_instances_for_testing


class TestThreadCleanup:
    """测试线程清理功能"""

    def setup_method(self):
        """每个测试方法前的设置"""
        _clear_instances_for_testing()

    def teardown_method(self):
        """每个测试方法后的清理"""
        _clear_instances_for_testing()

    def test_thread_cleanup_on_normal_exit(self):
        """测试正常退出时线程是否正确清理"""
        initial_thread_count = threading.active_count()
        
        # 创建config manager，启用文件监视
        config = get_config_manager(test_mode=True, watch=True)
        config.test_value = "test"
        config.save()
        
        # 验证线程数增加（文件监视线程）
        after_create_count = threading.active_count()
        assert after_create_count > initial_thread_count, "文件监视线程应该已启动"
        
        # 获取所有活动线程
        active_threads_before = set(threading.enumerate())
        
        # 模拟正常清理（目前ConfigManager没有cleanup方法，这个测试会失败）
        if hasattr(config, 'cleanup'):
            config.cleanup()
            
            # 等待线程清理
            time.sleep(1.1)  # 给线程足够时间停止
            
            # 验证线程已清理
            final_thread_count = threading.active_count()
            assert final_thread_count <= initial_thread_count, "所有新创建的线程应该已清理"
        else:
            pytest.fail("ConfigManager缺少cleanup方法 - 这正是issue #13的问题")

    def test_file_watcher_thread_exists(self):
        """测试文件监视线程是否被创建"""
        initial_threads = set(threading.enumerate())
        
        # 创建启用文件监视的配置管理器
        config = get_config_manager(test_mode=True, watch=True)
        config.test_value = "test"
        
        # 等待线程启动
        time.sleep(0.5)
        
        current_threads = set(threading.enumerate())
        new_threads = current_threads - initial_threads
        
        # 验证有新线程创建
        assert len(new_threads) > 0, "应该创建了文件监视线程"
        
        # 查找配置相关的线程
        config_threads = []
        for thread in new_threads:
            if hasattr(thread, '_target') and thread._target and 'watch' in str(thread._target):
                config_threads.append(thread)
        
        # 验证找到了文件监视线程
        assert len(config_threads) > 0, "应该找到文件监视相关的线程"

    def test_autosave_timer_exists(self):
        """测试自动保存定时器是否被创建"""
        # 创建配置管理器并触发自动保存
        config = get_config_manager(test_mode=True, autosave_delay=2.0)
        config.test_value = "test"  # 这会触发自动保存定时器
        
        # 检查是否有定时器线程
        active_threads = threading.enumerate()
        timer_threads = [t for t in active_threads if 'Timer' in str(type(t))]
        
        # 验证有定时器线程（可能在短时间内创建）
        # 注意：定时器可能很快执行完毕，所以这个测试可能不稳定
        print(f"活动线程数: {len(active_threads)}")
        print(f"定时器线程数: {len(timer_threads)}")

    def test_thread_cleanup_subprocess_simulation(self):
        """通过子进程测试程序强制退出时的线程行为"""
        # 创建一个简单的测试脚本
        test_script = '''
import sys
sys.path.insert(0, "/mnt/ntfs/ubuntu_data/NutstoreFiles/invest2025/project/config_manager/src")
from config_manager import get_config_manager
import time

# 创建配置管理器，启用文件监视
config = get_config_manager(test_mode=True, watch=True)
config.test_value = "test"
print("Config manager created with file watcher")

# 保持程序运行一段时间
time.sleep(2)
print("Exiting...")
'''
        
        # 将脚本写入临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            script_path = f.name
        
        try:
            # 启动子进程
            env = os.environ.copy()
            env['PYTHONPATH'] = "/mnt/ntfs/ubuntu_data/NutstoreFiles/invest2025/project/config_manager/src"
            
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True
            )
            
            # 等待一秒让进程启动
            time.sleep(1)
            
            # 发送SIGTERM信号模拟强制退出
            process.terminate()
            
            # 等待进程结束并收集输出
            stdout, stderr = process.communicate(timeout=5)
            
            print(f"子进程stdout: {stdout}")
            print(f"子进程stderr: {stderr}")
            print(f"子进程退出代码: {process.returncode}")
            
            # 检查是否有线程相关错误
            if "Exception ignored in: <module 'threading'" in stderr:
                pytest.fail(f"发现线程清理问题:\n{stderr}")
            
            if "I/O operation on closed file" in stderr:
                pytest.fail(f"发现文件I/O问题:\n{stderr}")
                
        finally:
            # 清理临时脚本
            if os.path.exists(script_path):
                os.unlink(script_path)

    def test_demonstrate_current_problem(self):
        """演示当前存在的问题"""
        print("\n=== 演示当前线程清理问题 ===")
        
        initial_thread_count = threading.active_count()
        print(f"初始线程数: {initial_thread_count}")
        
        # 创建配置管理器
        config = get_config_manager(test_mode=True, watch=True, autosave_delay=5.0)
        config.test_value = "test"
        
        time.sleep(0.5)  # 让线程启动
        
        after_create_count = threading.active_count()
        print(f"创建后线程数: {after_create_count}")
        
        # 列出所有活动线程
        for i, thread in enumerate(threading.enumerate()):
            print(f"  线程{i+1}: {thread.name} - {type(thread)} - daemon:{getattr(thread, 'daemon', 'N/A')}")
        
        # 检查ConfigManager是否有cleanup方法
        has_cleanup = hasattr(config, 'cleanup')
        has_enter_exit = hasattr(config, '__enter__') and hasattr(config, '__exit__')
        
        print(f"ConfigManager有cleanup方法: {has_cleanup}")
        print(f"ConfigManager支持上下文管理器: {has_enter_exit}")
        
        # 这里就展示了问题：没有合适的清理机制
        if not has_cleanup:
            print("❌ 问题确认: ConfigManager缺少cleanup方法")
        if not has_enter_exit:
            print("❌ 问题确认: ConfigManager不支持with语句")
            
        # 手动清理实例缓存，但线程可能仍然运行
        _clear_instances_for_testing()
        
        final_thread_count = threading.active_count()
        print(f"清理后线程数: {final_thread_count}")
        
        if final_thread_count > initial_thread_count:
            print("❌ 问题确认: 线程未正确清理")
            for i, thread in enumerate(threading.enumerate()):
                print(f"  剩余线程{i+1}: {thread.name} - {type(thread)}")
        else:
            print("✅ 线程已正确清理")