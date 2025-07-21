# tests/01_unit_tests/test_config_manager/test_tc0020_001_filewatcher_daemon_issue.py
"""
TC0020-001: FileWatcher daemon线程问题TDD测试

这个测试用于复现和验证FileWatcher线程daemon设置导致程序挂起的问题。
测试确保FileWatcher线程被正确设置为daemon=True，以便程序能正常退出。
"""
import os
import subprocess
import tempfile
import threading
import time
from pathlib import Path

import pytest
from config_manager import get_config_manager
from config_manager.core.watcher import FileWatcher


class TestFileWatcherDaemonIssue:
    """FileWatcher daemon线程问题测试"""

    def test_filewatcher_thread_daemon_setting(self):
        """测试FileWatcher线程是否正确设置为daemon线程"""
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_config_path = f.name
            f.write("test_config: true\n")

        try:
            # 创建FileWatcher实例
            watcher = FileWatcher()
            
            # 定义回调函数
            callback_called = threading.Event()
            def test_callback():
                callback_called.set()
            
            # 启动监视器
            watcher.start(temp_config_path, test_callback)
            
            # 等待线程启动
            time.sleep(0.1)
            
            # 验证线程存在且正在运行
            assert watcher._watcher_thread is not None
            assert watcher._watcher_thread.is_alive()
            
            # ❌ 这里应该失败，因为当前代码设置了daemon=False
            # 修复后应该改为daemon=True
            assert watcher._watcher_thread.daemon is True, \
                "FileWatcher线程必须设置为daemon=True以允许程序正常退出"
            
            # 停止监视器
            watcher.stop()
            
            # 等待线程结束
            time.sleep(0.2)
            assert not watcher._watcher_thread.is_alive()
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_config_path)
            except:
                pass

    def test_config_manager_thread_analysis(self):
        """测试config_manager创建的线程分析"""
        # 记录测试开始前的线程数
        initial_thread_count = threading.active_count()
        initial_threads = {t.name: t.daemon for t in threading.enumerate()}
        
        # 使用test_mode避免干扰生产环境
        config = get_config_manager(test_mode=True, watch=True)
        
        # 等待线程启动
        time.sleep(0.2)
        
        # 分析新创建的线程
        current_threads = {t.name: (t.daemon, t.is_alive()) for t in threading.enumerate()}
        new_threads = {}
        
        for name, (daemon, alive) in current_threads.items():
            if name not in initial_threads and alive:
                new_threads[name] = daemon
                print(f"新线程: {name}, daemon={daemon}, alive={alive}")
        
        # 查找FileWatcher线程
        filewatcher_threads = [name for name in new_threads.keys() 
                             if '_watch_file' in name or 'FileWatcher' in name or name.startswith('Thread-')]
        
        # ❌ 验证所有新创建的线程都应该是daemon线程
        for thread_name in new_threads:
            daemon_status = new_threads[thread_name]
            assert daemon_status is True, \
                f"线程 {thread_name} 必须是daemon线程 (daemon={daemon_status})"

    def test_program_exit_simulation_with_config_watcher(self):
        """模拟使用config_manager文件监视的程序退出场景"""
        # 创建测试脚本
        test_script = """
import sys
import os
import threading
import time

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src'))

from config_manager import get_config_manager

def main():
    print("程序启动，创建config_manager实例")
    
    # 创建配置管理器，启用文件监视
    config = get_config_manager(test_mode=True, watch=True)
    
    print(f"主线程和活跃线程数: {threading.active_count()}")
    
    # 列出所有活跃线程
    for thread in threading.enumerate():
        print(f"线程: {thread.name}, daemon={thread.daemon}, alive={thread.is_alive()}")
    
    print("程序即将退出...")
    # 主程序逻辑完成，应该能正常退出
    print("程序正常退出成功!")

if __name__ == '__main__':
    main()
"""
        
        # 写入临时脚本文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            script_path = f.name
            f.write(test_script)
        
        try:
            # 运行脚本并设置超时
            result = subprocess.run([
                'python', script_path
            ], capture_output=True, text=True, timeout=10)
            
            # ❌ 程序应该能在10秒内正常退出
            # 如果daemon=False，程序会挂起直到超时
            assert result.returncode == 0, \
                f"程序应该正常退出，但返回码为{result.returncode}\n" \
                f"stdout: {result.stdout}\n" \
                f"stderr: {result.stderr}"
                
            assert "程序正常退出成功!" in result.stdout, \
                "程序应该能执行完main()函数并正常退出"
            
        except subprocess.TimeoutExpired:
            # ❌ 超时说明程序挂起了（daemon=False导致的）
            pytest.fail("程序在10秒内未能退出，可能由于非daemon线程挂起")
        finally:
            # 清理临时文件
            try:
                os.unlink(script_path)
            except:
                pass