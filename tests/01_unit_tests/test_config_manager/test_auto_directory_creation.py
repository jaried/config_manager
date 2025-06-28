# tests/01_unit_tests/test_config_manager/test_auto_directory_creation.py
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import sys
import shutil

from src.config_manager import get_config_manager, _clear_instances_for_testing

@pytest.fixture(autouse=True)
def clear_instances_fixture():
    """在每个测试前后自动清理ConfigManager单例"""
    _clear_instances_for_testing()
    yield
    _clear_instances_for_testing()

class TestAutoDirectoryCreation:
    @patch('is_debug.is_debug', return_value=True)
    def test_paths_namespace_auto_creation(self, mock_is_debug, tmp_path: Path):
        config_path = tmp_path / "config.yaml"
        base_dir = tmp_path / "base"
        config_content = f"base_dir: {base_dir.as_posix()}\nproject_name: AutoDirTest\nexperiment_name: exp1"
        config_path.write_text(config_content)
        
        config = get_config_manager(config_path=str(config_path), test_mode=True)
        
        work_dir = Path(config.paths.work_dir)
        assert 'debug' in work_dir.parts
        assert 'AutoDirTest' in work_dir.parts
        assert not work_dir.exists()

    def test_nested_path_auto_creation(self, tmp_path: Path):
        config_file = tmp_path / "config.yaml"
        nested_path_str = (tmp_path / "level1/level2/level3/logs").as_posix()
        config_content = f"system:\n  storage:\n    log_dir: '{nested_path_str}'"
        config_file.write_text(config_content)

        config = get_config_manager(config_path=str(config_file), test_mode=True)
        
        assert config.system.storage.log_dir == nested_path_str
        assert not Path(nested_path_str).exists()

    def test_path_keyword_detection(self, tmp_path: Path):
        config_file = tmp_path / "config.yaml"
        log_dir = tmp_path / "my_logs"
        data_dir = tmp_path / "my_data"
        config_content = f"logging:\n  log_dir: {log_dir.as_posix()}\napplication:\n  data_dir: {data_dir.as_posix()}"
        config_file.write_text(config_content)

        config = get_config_manager(config_path=str(config_file), test_mode=True)

        assert not log_dir.exists()
        assert not data_dir.exists()
        
    def test_non_path_values_ignored(self, tmp_path: Path):
        output_file = tmp_path / "output.txt"
        config_content = f"output:\n  file_name: {output_file.as_posix()}"
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)

        config = get_config_manager(config_path=str(config_file), test_mode=True)

        assert not output_file.exists()

    @patch('is_debug.is_debug', return_value=False)
    @patch('os.makedirs', side_effect=PermissionError("Permission denied"))
    def test_permission_error_handling(self, mock_makedirs, mock_is_debug, tmp_path: Path):
        pytest.skip("路径不再自动创建，此测试已不适用")

    def test_existing_directory_handling(self, tmp_path: Path):
        config_file = tmp_path / "config.yaml"
        existing_dir = tmp_path / "already_exists"
        existing_dir.mkdir()
        
        config_content = f"paths:\n  my_path: {existing_dir.as_posix()}"
        config_file.write_text(config_content)
        
        config = get_config_manager(config_path=str(config_file), test_mode=True)
        
        assert Path(config.paths.my_path).exists()

    @patch('is_debug.is_debug', return_value=False)
    def test_windows_path_formats(self, mock_is_debug, tmp_path: Path):
        backslash_path = tmp_path / 'backslash_style'
        mixed_path = tmp_path / 'mixed_style'
        config_content = f'paths:\n  backslash_dir: "{str(backslash_path)}"\n  mixed_dir: "{str(mixed_path).replace(os.sep, "/")}/sub"'
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_content)

        config = get_config_manager(config_path=str(config_file), test_mode=True)
        
        assert not Path(config.paths.backslash_dir).exists()
        assert not Path(config.paths.mixed_dir).exists() 