# tests/config_manager/tc0001_002_type_hint_support.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
from pathlib import Path
from src.config_manager.config_manager import get_config_manager


def test_tc0001_002_001_path_type_support():
    """测试路径类型支持"""
    with tempfile.NamedTemporaryFile(suffix='.yaml') as tmpfile:
        cfg = get_config_manager(config_path=tmpfile.name)

        # 设置路径值
        test_path = Path("/path/to/test/directory")
        cfg.set('directory_path', test_path, type_hint=Path)

        # 获取为Path对象
        path_obj = cfg.get_path('directory_path')
        assert isinstance(path_obj, Path)
        assert path_obj == test_path

        # 获取类型提示
        type_name = cfg.get_type_hint('directory_path')
        assert type_name == "Path"
    return


def test_tc0001_002_002_type_conversion():
    """测试类型转换功能"""
    with tempfile.NamedTemporaryFile(suffix='.yaml') as tmpfile:
        cfg = get_config_manager(config_path=tmpfile.name)

        # 设置整数值
        cfg.set('values_integer', "42", type_hint=int)

        # 获取为整数
        int_value = cfg.get('values_integer', as_type=int)
        assert isinstance(int_value, int)
        assert int_value == 42

        # 设置浮点值
        cfg.set('values_float', "3.14", type_hint=float)

        # 获取为浮点数
        float_value = cfg.get('values_float', as_type=float)
        assert isinstance(float_value, float)
        assert float_value == 3.14
    return


def test_tc0001_002_003_invalid_type_conversion():
    """测试无效类型转换"""
    with tempfile.NamedTemporaryFile(suffix='.yaml') as tmpfile:
        cfg = get_config_manager(config_path=tmpfile.name)

        # 设置无法转换的值
        cfg.set('values_invalid', "not_a_number", type_hint=int)

        # 获取时应保留原始值
        value = cfg.get('values_invalid', as_type=int)
        assert value == "not_a_number"
    return