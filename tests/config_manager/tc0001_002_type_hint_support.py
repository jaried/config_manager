# tests/config_manager/tc0001_002_type_hint_support.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import os
from pathlib import Path
from src.config_manager.config_manager import get_config_manager, _clear_instances_for_testing


@pytest.fixture(autouse=True)
def cleanup_instances():
    """每个测试后清理实例"""
    yield
    _clear_instances_for_testing()
    return


def test_tc0001_002_001_path_type_support():
    """测试路径类型支持"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False)

        test_path = Path("/path/to/test/directory")
        cfg.set('directory_path', test_path, type_hint=Path)

        path_obj = cfg.get_path('directory_path')
        assert isinstance(path_obj, Path)
        assert path_obj == test_path

        type_name = cfg.get_type_hint('directory_path')
        assert type_name == "Path"
    return


def test_tc0001_002_002_type_conversion():
    """测试类型转换功能"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False)

        cfg.set('values_integer', "42", type_hint=int)

        int_value = cfg.get('values_integer', as_type=int)
        assert isinstance(int_value, int)
        assert int_value == 42

        cfg.set('values_float', "3.14", type_hint=float)

        float_value = cfg.get('values_float', as_type=float)
        assert isinstance(float_value, float)
        assert float_value == 3.14
    return


def test_tc0001_002_003_invalid_type_conversion():
    """测试无效类型转换"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(config_path=config_file, watch=False)

        cfg.set('values_invalid', "not_a_number", type_hint=int)

        value = cfg.get('values_invalid', as_type=int)
        assert value == "not_a_number"
    return