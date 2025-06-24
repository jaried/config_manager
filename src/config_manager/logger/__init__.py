# src/config_manager/logger/__init__.py
from __future__ import annotations

from .minimal_logger import MinimalLogger, debug, info, warning, error, critical

__all__ = ['MinimalLogger', 'debug', 'info', 'warning', 'error', 'critical'] 