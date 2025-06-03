# src/config_manager/__init__.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

# 修正导入路径 - 直接从当前包导入，而不是从 .core 子包
from .config_manager import get_config_manager

__all__ = ['get_config_manager']