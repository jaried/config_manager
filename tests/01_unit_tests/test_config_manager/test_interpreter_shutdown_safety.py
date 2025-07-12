# tests/01_unit_tests/test_config_manager/test_interpreter_shutdown_safety.py
from __future__ import annotations

import pytest
import threading
import time
import os
import tempfile
import atexit
from unittest.mock import patch, Mock

from src.config_manager import get_config_manager
from src.config_manager.core.autosave_manager import AutosaveManager



class TestInterpreterShutdownSafety:
    """测试解释器关闭时的线程安全性"""

    def setup_method(self):
        """测试前准备"""
        # 使用临时目录进行测试
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "test_config.yaml")

    def teardown_method(self):
        """测试后清理"""
        import shutil
        # 清理整个测试目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_autosave_manager_shutdown_flag(self):
        """测试自动保存管理器的关闭标志功能"""
        autosave_manager = AutosaveManager(autosave_delay=0.1)
        
        # 初始状态应该是False
        assert not autosave_manager._shutdown
        
        # 调用cleanup后应该设置为True
        autosave_manager.cleanup()
        assert autosave_manager._shutdown

    def test_schedule_save_when_shutdown(self):
        """测试在关闭状态下调用schedule_save"""
        autosave_manager = AutosaveManager(autosave_delay=0.1)
        save_callback = Mock(return_value=True)
        
        # 设置关闭状态
        autosave_manager._shutdown = True
        
        # 应该直接返回，不创建定时器
        autosave_manager.schedule_save(save_callback)
        
        # 验证没有创建定时器
        assert autosave_manager._autosave_timer is None
        # 验证没有调用保存回调
        save_callback.assert_not_called()

    def test_schedule_save_handles_runtime_error(self):
        """测试schedule_save处理RuntimeError异常"""
        autosave_manager = AutosaveManager(autosave_delay=0.1)
        save_callback = Mock(return_value=True)
        
        # Mock threading.Timer以抛出RuntimeError
        with patch('threading.Timer') as mock_timer:
            mock_timer.side_effect = RuntimeError("can't create new thread at interpreter shutdown")
            
            # 调用schedule_save，应该捕获异常并设置关闭标志
            autosave_manager.schedule_save(save_callback)
            
            # 验证关闭标志被设置
            assert autosave_manager._shutdown

    def test_schedule_save_handles_other_runtime_errors(self):
        """测试schedule_save处理其他RuntimeError异常"""
        autosave_manager = AutosaveManager(autosave_delay=0.1)
        save_callback = Mock(return_value=True)
        
        # Mock threading.Timer以抛出其他RuntimeError
        with patch('threading.Timer') as mock_timer:
            mock_timer.side_effect = RuntimeError("other runtime error")
            
            # 调用schedule_save，应该重新抛出异常
            with pytest.raises(RuntimeError, match="other runtime error"):
                autosave_manager.schedule_save(save_callback)

    def test_is_interpreter_shutting_down_normal(self):
        """测试正常情况下的解释器状态检查"""
        autosave_manager = AutosaveManager(autosave_delay=0.1)
        
        # 正常情况下应该返回False
        assert not autosave_manager._is_interpreter_shutting_down()

    def test_is_interpreter_shutting_down_exception(self):
        """测试解释器关闭时的状态检查"""
        autosave_manager = AutosaveManager(autosave_delay=0.1)
        
        # Mock gc.get_count以抛出异常
        with patch('gc.get_count') as mock_gc:
            mock_gc.side_effect = Exception("interpreter shutdown")
            
            # 应该返回True
            assert autosave_manager._is_interpreter_shutting_down()

    def test_perform_autosave_when_shutdown(self):
        """测试在关闭状态下执行自动保存"""
        autosave_manager = AutosaveManager(autosave_delay=0.1)
        save_callback = Mock(return_value=True)
        
        # 设置关闭状态
        autosave_manager._shutdown = True
        
        # 调用_perform_autosave，应该直接返回
        autosave_manager._perform_autosave(save_callback)
        
        # 验证没有调用保存回调
        save_callback.assert_not_called()

    def test_perform_autosave_interpreter_shutting_down(self):
        """测试解释器关闭时执行自动保存"""
        autosave_manager = AutosaveManager(autosave_delay=0.1)
        save_callback = Mock(return_value=True)
        
        # Mock解释器关闭检查
        with patch.object(autosave_manager, '_is_interpreter_shutting_down', return_value=True):
            # 调用_perform_autosave，应该直接返回
            autosave_manager._perform_autosave(save_callback)
            
            # 验证没有调用保存回调
            save_callback.assert_not_called()

    def test_cleanup_cancels_timer(self):
        """测试cleanup方法取消定时器"""
        autosave_manager = AutosaveManager(autosave_delay=0.1)
        save_callback = Mock(return_value=True)
        
        # 创建定时器
        autosave_manager.schedule_save(save_callback)
        assert autosave_manager._autosave_timer is not None
        
        # 调用cleanup
        autosave_manager.cleanup()
        
        # 验证定时器被清理
        assert autosave_manager._autosave_timer is None
        assert autosave_manager._shutdown

    def test_config_manager_exit_safety(self):
        """测试配置管理器退出时的安全性"""
        config = get_config_manager(
            config_path=self.config_path,
            auto_create=True, 
            autosave_delay=0.1
        )
        
        # 设置一些值
        config.set('test_key', 'test_value')
        
        # 模拟程序退出场景
        def simulate_exit():
            try:
                config.set('exit_key', 'exit_value')
            except RuntimeError as e:
                # 不应该抛出线程相关的错误
                assert "can't create new thread at interpreter shutdown" not in str(e)
        
        # 模拟解释器关闭状态
        with patch.object(config._autosave_manager, '_is_interpreter_shutting_down', return_value=True):
            simulate_exit()  # 应该正常完成，不抛出异常

    def test_atexit_scenario(self):
        """测试atexit场景下的安全性"""
        config = get_config_manager(
            config_path=self.config_path,
            auto_create=True, 
            autosave_delay=0.1
        )
        
        exit_error = None
        
        def exit_handler():
            nonlocal exit_error
            try:
                config.set('final_key', 'final_value')
            except Exception as e:
                exit_error = e
        
        # 注册退出处理器
        atexit.register(exit_handler)
        
        # 模拟解释器关闭状态
        with patch.object(config._autosave_manager, '_is_interpreter_shutting_down', return_value=True):
            exit_handler()
            
            # 验证没有发生线程相关错误
            assert exit_error is None

    def test_concurrent_shutdown_access(self):
        """测试并发关闭访问的安全性"""
        autosave_manager = AutosaveManager(autosave_delay=0.1)
        save_callback = Mock(return_value=True)
        
        # 创建多个线程同时访问
        def worker():
            try:
                autosave_manager.schedule_save(save_callback)
            except RuntimeError as e:
                # 线程创建错误应该被捕获
                assert "can't create new thread at interpreter shutdown" not in str(e)
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # 同时触发cleanup
        autosave_manager.cleanup()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=1.0)
        
        # 验证最终状态
        assert autosave_manager._shutdown

    def test_double_cleanup_safety(self):
        """测试重复cleanup的安全性"""
        autosave_manager = AutosaveManager(autosave_delay=0.1)
        save_callback = Mock(return_value=True)
        
        # 创建定时器
        autosave_manager.schedule_save(save_callback)
        
        # 多次调用cleanup应该是安全的
        autosave_manager.cleanup()
        autosave_manager.cleanup()
        autosave_manager.cleanup()
        
        # 验证状态一致
        assert autosave_manager._shutdown
        assert autosave_manager._autosave_timer is None

    def test_schedule_save_thread_safety(self):
        """测试schedule_save的线程安全性"""
        autosave_manager = AutosaveManager(autosave_delay=0.1)
        save_callback = Mock(return_value=True)
        
        errors = []
        
        def worker():
            try:
                for _ in range(10):
                    autosave_manager.schedule_save(save_callback)
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)
        
        # 创建多个工作线程
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # 等待一段时间后cleanup
        time.sleep(0.05)
        autosave_manager.cleanup()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=2.0)
        
        # 验证没有线程创建相关的错误
        for error in errors:
            assert "can't create new thread at interpreter shutdown" not in str(error) 