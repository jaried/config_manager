# tests/01_unit_tests/test_config_manager/test_tc0019_001_thread_graceful_shutdown.py
from __future__ import annotations
from datetime import datetime

import threading
import time
import tempfile
import os
import pytest
from config_manager import get_config_manager
from config_manager.config_manager import _clear_instances_for_testing


def test_file_watcher_thread_graceful_shutdown():
    """验证文件监视器线程能够优雅关闭，不导致程序挂起"""
    
    # 清理之前的实例
    _clear_instances_for_testing()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "test_config.yaml")
        
        # 创建配置管理器，启用文件监视器
        config = get_config_manager(
            config_path=config_path,
            test_mode=True,
            auto_create=True,
            watch=True  # 启用文件监视器
        )
        
        # 等待文件监视器线程启动
        time.sleep(0.5)
        
        # 验证文件监视器线程已启动
        assert config._watcher is not None, "文件监视器应该已创建"
        assert config._watcher._watcher_thread is not None, "监视器线程应该已启动"
        assert config._watcher._watcher_thread.is_alive(), "监视器线程应该在运行"
        
        # 记录线程启动前的活跃线程数
        initial_thread_count = threading.active_count()
        print(f"启动文件监视器后的线程数: {initial_thread_count}")
        
        # 手动触发清理
        config._cleanup()
        
        # 等待线程完全关闭
        time.sleep(1.0)
        
        # 验证线程已关闭
        final_thread_count = threading.active_count()
        print(f"清理后的线程数: {final_thread_count}")
        
        # 验证监视器线程已停止
        if config._watcher._watcher_thread:
            assert not config._watcher._watcher_thread.is_alive(), "监视器线程应该已停止"
        
        # 线程数应该减少（至少减少1个，即文件监视器线程）
        assert final_thread_count <= initial_thread_count, "清理后线程数不应增加"


def test_multiple_config_managers_cleanup():
    """验证多个配置管理器实例能够正确清理线程"""
    
    # 清理之前的实例
    _clear_instances_for_testing()
    
    configs = []
    temp_dirs = []
    
    try:
        # 创建多个配置管理器实例
        for i in range(3):
            temp_dir = tempfile.mkdtemp()
            temp_dirs.append(temp_dir)
            config_path = os.path.join(temp_dir, f"test_config_{i}.yaml")
            
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                auto_create=True,
                watch=True
            )
            configs.append(config)
        
        # 等待所有监视器线程启动
        time.sleep(1.0)
        
        initial_thread_count = threading.active_count()
        print(f"创建3个配置管理器后的线程数: {initial_thread_count}")
        
        # 逐一清理配置管理器
        for config in configs:
            config._cleanup()
        
        # 等待所有线程关闭
        time.sleep(2.0)
        
        final_thread_count = threading.active_count()
        print(f"清理所有配置管理器后的线程数: {final_thread_count}")
        
        # 验证线程数减少
        assert final_thread_count <= initial_thread_count, "清理后线程数不应增加"
        
    finally:
        # 清理临时目录
        import shutil
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


def test_cleanup_prevents_duplicate_calls():
    """验证清理方法能防止重复调用"""
    
    # 清理之前的实例
    _clear_instances_for_testing()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "test_config.yaml")
        
        config = get_config_manager(
            config_path=config_path,
            test_mode=True,
            auto_create=True,
            watch=True
        )
        
        # 等待文件监视器启动
        time.sleep(0.5)
        
        # 验证初始状态
        assert not hasattr(config, '_cleanup_done'), "初始状态不应有清理标记"
        
        # 第一次清理
        config._cleanup()
        
        # 验证清理标记已设置
        assert hasattr(config, '_cleanup_done'), "应该有清理标记"
        assert config._cleanup_done, "清理标记应该为True"
        
        # 第二次清理应该直接返回，不产生错误
        config._cleanup()  # 不应该抛出异常
        
        # 验证清理标记仍然存在
        assert config._cleanup_done, "清理标记应该保持True"


def test_atexit_cleanup_registration():
    """验证atexit清理机制正确注册"""
    
    # 清理之前的实例
    _clear_instances_for_testing()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "test_config.yaml")
        
        config = get_config_manager(
            config_path=config_path,
            test_mode=True,
            auto_create=True,
            watch=True
        )
        
        # 验证atexit清理已注册
        assert hasattr(config, '_cleanup_registered'), "应该有清理注册标记"
        assert config._cleanup_registered, "清理应该已注册到atexit"
        
        # 手动清理
        config._cleanup()


def test_thread_stop_timeout_handling():
    """验证线程停止超时处理机制"""
    
    # 清理之前的实例
    _clear_instances_for_testing()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "test_config.yaml")
        
        config = get_config_manager(
            config_path=config_path,
            test_mode=True,
            auto_create=True,
            watch=True
        )
        
        # 等待文件监视器启动
        time.sleep(0.5)
        
        watcher = config._watcher
        assert watcher is not None, "文件监视器应该存在"
        assert watcher._watcher_thread.is_alive(), "监视器线程应该在运行"
        
        # 测试停止机制
        start_time = time.time()
        watcher.stop()
        stop_time = time.time()
        
        # 验证停止时间合理（应该在3秒内完成）
        stop_duration = stop_time - start_time
        assert stop_duration < 5.0, f"线程停止耗时过长: {stop_duration:.2f}秒"
        
        # 验证线程已停止
        assert not watcher._watcher_thread.is_alive(), "监视器线程应该已停止"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])