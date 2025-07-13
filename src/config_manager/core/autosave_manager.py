# src/config_manager/core/autosave_manager.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import threading
from typing import Callable
from ..logger import info, warning, error


class AutosaveManager:
    """自动保存管理器"""

    def __init__(self, autosave_delay: float):
        self._autosave_delay = autosave_delay
        self._autosave_timer = None
        self._autosave_lock = threading.Lock()
        self._shutdown = False

    def schedule_save(self, save_callback: Callable[[], bool]):
        """安排自动保存任务"""
        # 检查解释器是否正在关闭或已经关闭
        if self._shutdown or self._is_interpreter_shutting_down():
            return
            
        with self._autosave_lock:
            # 再次检查状态（防止在获取锁的过程中状态发生变化）
            if self._shutdown or self._is_interpreter_shutting_down():
                return
                
            if self._autosave_timer:
                self._autosave_timer.cancel()

            try:
                self._autosave_timer = threading.Timer(
                    self._autosave_delay,
                    self._perform_autosave,
                    args=(save_callback,)
                )
                self._autosave_timer.daemon = True
                self._autosave_timer.start()
            except RuntimeError as e:
                # 如果无法创建线程（比如解释器关闭），忽略错误
                if "can't create new thread at interpreter shutdown" in str(e):
                    self._shutdown = True
                    return
                else:
                    raise
        return

    def _is_interpreter_shutting_down(self) -> bool:
        """检查Python解释器是否正在关闭"""
        try:
            # 尝试导入gc模块，如果失败说明解释器正在关闭
            import gc
            # 检查是否可以调用gc相关功能
            gc.get_count()
            return False
        except Exception:
            return True

    def _perform_autosave(self, save_callback: Callable[[], bool]):
        """执行自动保存"""
        try:
            # 检查是否在关闭状态
            if self._shutdown or self._is_interpreter_shutting_down():
                return
                
            saved = save_callback()
            if saved:
                info("配置已自动保存")
            else:
                info("自动保存跳过：无数据")
        except Exception as e:
            error(f"自动保存失败: {str(e)}")
        finally:
            with self._autosave_lock:
                self._autosave_timer = None
        return

    def cleanup(self):
        """清理自动保存定时器"""
        self._shutdown = True
        with self._autosave_lock:
            if self._autosave_timer:
                self._autosave_timer.cancel()
                self._autosave_timer = None
        return