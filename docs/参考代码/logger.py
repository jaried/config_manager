# src/utils/custom_logger.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import os
import sys
import traceback
from typing import Optional, Any, Dict

import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

LEVEL_VALUE: Dict[str, int] = {
    "EXCEPTION": 60,
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
    "DEBUG_DETAIL": 9,
    "DEBUG_WORKER_SUMMARY": 8,
    "DEBUG_WORKER_DETAIL": 7,
}

_base_start_time: Optional[datetime] = None
_base_run_dir: Optional[str] = None
_worker_start_time_override: Optional[datetime] = None
_worker_run_dir_override: Optional[str] = None

_console_level_value: int = LEVEL_VALUE["INFO"]
_file_level_value: int = LEVEL_VALUE["DEBUG"]


def init_logger_system(
        app_start_time: datetime,
        log_settings: Dict[str, Any],
        base_run_dir: str
) -> None:
    global _base_start_time, _base_run_dir, _console_level_value, _file_level_value
    chosen_start = min(start_time, app_start_time)
    _base_start_time = chosen_start
    _base_run_dir = base_run_dir
    os.makedirs(base_run_dir, exist_ok=True)

    if (console_level := log_settings.get("console_level")) in LEVEL_VALUE:
        _console_level_value = LEVEL_VALUE[console_level]
    if (file_level := log_settings.get("file_level")) in LEVEL_VALUE:
        _file_level_value = LEVEL_VALUE[file_level]


def configure_logging_for_worker_process(
        worker_app_start_time: datetime,
        run_dir: str
) -> None:
    global _worker_start_time_override, _worker_run_dir_override
    _worker_start_time_override = worker_app_start_time
    _worker_run_dir_override = run_dir
    os.makedirs(run_dir, exist_ok=True)


def get_logger(name: Optional[str] = None) -> Logger:
    global _base_start_time, _base_run_dir
    if _base_start_time is None or _base_run_dir is None:
        default_dir = os.path.abspath("logs")
        os.makedirs(default_dir, exist_ok=True)
        init_logger_system(start_time, {}, default_dir)
    return Logger(name)


class Logger:
    def __init__(self, name: Optional[str]) -> None:
        self._name = name or __name__
        self._pid = os.getpid()

    def __call__(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.info(message, *args, **kwargs)

    def _log(
            self,
            level: str,
            message: str,
            *args: Any,
            include_trace: bool = True,
            do_print: bool = True,
            **kwargs: Any
    ) -> None:
        now = datetime.now()
        current_start = _worker_start_time_override or _base_start_time
        current_dir = _worker_run_dir_override or _base_run_dir

        assert current_start and current_dir, "Logger未初始化"

        elapsed = now - current_start
        hours, rem = divmod(elapsed.total_seconds(), 3600)
        minutes, seconds = divmod(rem, 60)
        elapsed_str = f"{int(hours)}:{int(minutes):02d}:{seconds:05.2f}"

        # 直接拼接参数到消息
        full_msg = f"{message} | args:{args} | kwargs:{kwargs}"
        log_line = (
            f"[{self._pid:>6}] {now.strftime('%Y-%m-%d %H:%M:%S')} "
            f"- {elapsed_str} - {level} - {full_msg}"
        )

        # 控制台输出判断
        if do_print and LEVEL_VALUE[level] >= _console_level_value:
            color = Fore.RED if LEVEL_VALUE[level] >= 40 else Fore.YELLOW if LEVEL_VALUE[level] >= 30 else ""
            stream = sys.stderr if LEVEL_VALUE[level] >= 30 else sys.stdout
            print(f"{color}{log_line}{Style.RESET_ALL}", file=stream)

        # 文件写入判断
        if LEVEL_VALUE[level] >= _file_level_value:
            os.makedirs(current_dir, exist_ok=True)
            log_path = os.path.join(current_dir, f"{self._name}_{self._pid}.log")
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(log_line + "\n")
            except Exception:
                if include_trace:
                    traceback.print_exc(file=sys.stderr)

    # 以下日志方法直接透传所有参数
    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("EXCEPTION", message, *args, **kwargs)
        traceback.print_exc(file=sys.stderr)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("CRITICAL", message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("ERROR", message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("WARNING", message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("INFO", message, *args, **kwargs)

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("DEBUG", message, *args, **kwargs)

    def debug_detail(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("DEBUG_DETAIL", message, *args, **kwargs)

    def debug_worker_summary(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("DEBUG_WORKER_SUMMARY", message, *args, **kwargs)

    def debug_worker_detail(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._log("DEBUG_WORKER_DETAIL", message, *args, **kwargs)


logger = get_logger()
