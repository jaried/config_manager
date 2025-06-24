# src/config_manager/logger/minimal_logger.py
from __future__ import annotations
import os
from datetime import datetime
import inspect

LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

_start_time = datetime.now()

class MinimalLogger:
    def __init__(self, name="confmgr", level="INFO"):
        self.name = name[:8] if len(name) > 8 else name
        self._pid = os.getpid()
        self._console_level = LEVELS.get(level.upper(), LEVELS["INFO"])

    def _log(self, level, message, *args, **kwargs):
        if LEVELS[level] < self._console_level:
            return
        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        elapsed = now - _start_time
        total_seconds = elapsed.total_seconds()
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds_int = divmod(remainder, 60)
        fractional_seconds = total_seconds - (hours * 3600 + minutes * 60)
        elapsed_str = f"{hours}:{minutes:02d}:{fractional_seconds:05.2f}"
        formatted_message = message.format(*args, **kwargs) if args or kwargs else message

        # 获取logger调用者的真实代码行号和函数名
        frame = inspect.currentframe()
        outer_frames = inspect.getouterframes(frame)
        lineno = 0
        func_name = 'unknown'
        for record in outer_frames:
            if 'minimal_logger.py' not in record.filename:
                lineno = record.lineno
                func_name = record.function
                break

        func_name = func_name[:8]
        log_line = (
            f"[{self._pid:>6} | {func_name:<8}: {lineno:>4} ] "
            f"{timestamp} | {elapsed_str} | {level:^5} | {formatted_message}"
        )
        print(log_line)

    def debug(self, message, *args, **kwargs):
        self._log("DEBUG", message, *args, **kwargs)
    def info(self, message, *args, **kwargs):
        self._log("INFO", message, *args, **kwargs)
    def warning(self, message, *args, **kwargs):
        self._log("WARNING", message, *args, **kwargs)
    def error(self, message, *args, **kwargs):
        self._log("ERROR", message, *args, **kwargs)
    def critical(self, message, *args, **kwargs):
        self._log("CRITICAL", message, *args, **kwargs)

# 默认全局logger，级别为INFO
_logger = MinimalLogger("confmgr", level="INFO")

def debug(message, *args, **kwargs):
    _logger.debug(message, *args, **kwargs)
def info(message, *args, **kwargs):
    _logger.info(message, *args, **kwargs)
def warning(message, *args, **kwargs):
    _logger.warning(message, *args, **kwargs)
def error(message, *args, **kwargs):
    _logger.error(message, *args, **kwargs)
def critical(message, *args, **kwargs):
    _logger.critical(message, *args, **kwargs) 