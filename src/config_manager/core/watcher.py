# src/config_manager/core/watcher.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import os
import time
import threading
from typing import Callable


class FileWatcher:
    """文件监视器"""

    def __init__(self):
        self._watcher_thread = None
        self._stop_watcher = threading.Event()
        self._last_mtime = 0
        self._config_path = None
        self._callback = None
        self._internal_save_flag = False  # 内部保存标志
        self._internal_save_start_time = 0  # 内部保存开始时间

    def start(self, config_path: str, callback: Callable[[], None]):
        """启动文件监视"""
        if self._watcher_thread is not None and self._watcher_thread.is_alive():
            return

        self._config_path = config_path
        self._callback = callback
        self._stop_watcher.clear()

        # 记录初始修改时间
        if os.path.exists(config_path):
            self._last_mtime = os.path.getmtime(config_path)

        self._watcher_thread = threading.Thread(
            target=self._watch_file,
            daemon=True  # 设为daemon线程，允许程序正常退出
        )
        self._watcher_thread.start()
        print("配置文件监视器已启动")
        return

    def stop(self):
        """停止文件监视"""
        self._stop_watcher.set()
        if self._watcher_thread and self._watcher_thread.is_alive():
            # 尝试优雅停止，由于使用了可中断等待，应该能快速响应
            self._watcher_thread.join(timeout=1.5)
            if self._watcher_thread.is_alive():
                print("⚠️  文件监视器线程未能在1.5秒内停止")
        return

    def set_internal_save_flag(self, flag: bool):
        """设置内部保存标志"""
        self._internal_save_flag = flag
        # 如果设置为True，记录设置时间，用于延迟重置
        if flag:
            self._internal_save_start_time = time.time()
        return

    def _watch_file(self):
        """监视配置文件变化"""
        while not self._stop_watcher.is_set():
            try:
                # 检查内部保存标志是否需要超时重置（5秒后自动重置）
                if self._internal_save_flag and time.time() - self._internal_save_start_time > 5:
                    self._internal_save_flag = False
                    print("⚠️  内部保存标志超时重置")
                
                if os.path.exists(self._config_path):
                    current_mtime = os.path.getmtime(self._config_path)
                    if current_mtime > self._last_mtime:
                        # 检查是否是内部保存
                        if self._internal_save_flag:
                            # 检查时间窗口：如果修改时间距离标志设置时间过长（超过2秒），认为是外部修改
                            time_since_flag_set = time.time() - self._internal_save_start_time
                            if time_since_flag_set > 2.0:
                                # 时间窗口过长，认为是外部修改，重置标志并触发重新加载
                                print(f"📁 检测到延迟外部文件变化（{time_since_flag_set:.1f}s），触发重新加载")
                                self._internal_save_flag = False
                                self._callback()
                                self._last_mtime = current_mtime
                            else:
                                # 是内部保存，只更新修改时间，不触发回调
                                self._last_mtime = current_mtime
                                print(f"🔒 跳过内部保存触发的文件变化检测")
                                # 检测到内部保存后立即重置标志
                                self._internal_save_flag = False
                        else:
                            # 是外部变化，触发回调重新加载
                            print(f"📁 检测到外部文件变化，触发重新加载")
                            self._callback()
                            self._last_mtime = current_mtime
                # 使用可中断的等待，立即响应停止信号
                self._stop_watcher.wait(timeout=1.0)
            except Exception as e:
                print(f"监视配置出错: {str(e)}")
                # 异常情况下也使用可中断等待，而不是阻塞睡眠
                self._stop_watcher.wait(timeout=2.0)
        return