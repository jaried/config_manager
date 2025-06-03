# tests/conftest.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import os
import sys
import pytest

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(__file__))
src_path = os.path.join(project_root, 'src')

if src_path not in sys.path:
    sys.path.insert(0, src_path)

# 设置pytest配置
def pytest_configure(config):
    """pytest配置"""
    # 设置异步测试的默认循环作用域
    config.option.asyncio_mode = "auto"
    return

# 全局fixture，确保测试环境干净
@pytest.fixture(autouse=True)
def ensure_clean_environment():
    """确保每个测试都有干净的环境"""
    # 在测试前清理
    yield
    # 在测试后清理
    try:
        from config_manager.config_manager import _clear_instances_for_testing
        _clear_instances_for_testing()
    except ImportError:
        # 如果导入失败，忽略
        pass