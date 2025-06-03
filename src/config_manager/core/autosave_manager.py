# src/config_manager/core/autosave_manager.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import threading
from typing import Callable


class AutosaveManager:
    """自动保存管理器"""

    def __init__(self, autosave_delay: float):
        self._autosave_delay = autosave_delay
        self._autosave_timer = None
        self._autosave_lock = threading.Lock()

    def schedule_save(self, save_callback: Callable[[], bool]):
        """安排自动保存任务"""
        with self._autosave_lock:
            if self._autosave_timer:
                self._autosave_timer.cancel()

            self._autosave_timer = threading.Timer(
                self._autosave_delay,
                self._perform_autosave,
                args=(save_callback,)
            )
            self._autosave_timer.daemon = True
            self._autosave_timer.start()
        return

    def _perform_autosave(self, save_callback: Callable[[], bool]):
        """执行自动保存"""
        try:
            saved = save_callback()
            if saved:
                print("配置已自动保存")
            else:
                print("自动保存跳过：无数据")
        except Exception as e:
            print(f"自动保存失败: {str(e)}")
        finally:
            with self._autosave_lock:
                self._autosave_timer = None
        return

    def cleanup(self):
        """清理自动保存定时器"""
        with self._autosave_lock:
            if self._autosave_timer:
                self._autosave_timer.cancel()
                self._autosave_timer = None
        return