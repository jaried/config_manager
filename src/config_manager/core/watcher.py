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
            daemon=True
        )
        self._watcher_thread.start()
        print("配置文件监视器已启动")
        return

    def stop(self):
        """停止文件监视"""
        self._stop_watcher.set()
        if self._watcher_thread and self._watcher_thread.is_alive():
            self._watcher_thread.join(timeout=1.0)
        return

    def _watch_file(self):
        """监视配置文件变化"""
        while not self._stop_watcher.is_set():
            try:
                if os.path.exists(self._config_path):
                    current_mtime = os.path.getmtime(self._config_path)
                    if current_mtime > self._last_mtime:
                        self._callback()
                        self._last_mtime = current_mtime
                time.sleep(1)
            except Exception as e:
                print(f"监视配置出错: {str(e)}")
                time.sleep(5)
        return