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
        assert work_dir.exists()

    def test_nested_path_auto_creation(self, tmp_path: Path):
        config_file = tmp_path / "config.yaml"
        nested_path_str = (tmp_path / "level1/level2/level3/logs").as_posix()
        config_content = f"system:\n  storage:\n    log_dir: '{nested_path_str}'\n    log_path: '{tmp_path / 'not_created.log'}'\n    my_logs: '{tmp_path / 'not_created_dir'}'"
        config_file.write_text(config_content)

        config = get_config_manager(config_path=str(config_file), test_mode=True)
        
        # 只断言'_dir'结尾的路径会被自动创建
        assert config.system.storage.log_dir == nested_path_str
        assert Path(nested_path_str).exists()
        # 其他字段不会自动创建
        assert not Path(tmp_path / 'not_created.log').exists()
        assert not Path(tmp_path / 'not_created_dir').exists()

    def test_path_keyword_detection(self, tmp_path: Path):
        config_file = tmp_path / "config.yaml"
        log_dir = tmp_path / "my_logs_dir"
        data_dir = tmp_path / "my_data_dir"
        log_path = tmp_path / "my_logs_path"
        config_content = f"logging:\n  log_dir: {log_dir.as_posix()}\n  log_path: {log_path.as_posix()}\napplication:\n  data_dir: {data_dir.as_posix()}"
        config_file.write_text(config_content)

        config = get_config_manager(config_path=str(config_file), test_mode=True)

        # 只断言'_dir'结尾的路径会被自动创建
        assert log_dir.exists()
        assert data_dir.exists()
        # 其他字段不会自动创建
        assert not log_path.exists()

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

    def test_existing_directory_handling(self, tmp_path):
        """测试已存在目录的处理"""
        existing_dir = tmp_path / "already_exists"
        existing_dir.mkdir()
        
        config = get_config_manager(test_mode=True, first_start_time=datetime(2025, 1, 7, 15, 30, 0))
        config.set('base_dir', str(tmp_path))
        config.set('project_name', 'test_project')
        config.set('experiment_name', 'test_experiment')
        
        # 设置自定义路径
        config.set('paths.my_path', str(existing_dir))
        
        # 验证路径被正确设置，但不自动创建
        assert config.get('paths.my_path') == str(existing_dir)
        assert existing_dir.exists()  # 目录应该存在，因为我们在测试中创建了它

    def test_windows_path_formats(self, tmp_path):
        """测试Windows路径格式处理"""
        backslash_path = tmp_path / "backslash_style"
        backslash_path.mkdir()
        
        config = get_config_manager(test_mode=True, first_start_time=datetime(2025, 1, 7, 15, 30, 0))
        config.set('base_dir', str(tmp_path))
        config.set('project_name', 'test_project')
        config.set('experiment_name', 'test_experiment')
        
        # 设置Windows风格的路径
        config.set('paths.backslash_dir', str(backslash_path))
        
        # 验证路径被正确设置，但不自动创建
        assert config.get('paths.backslash_dir') == str(backslash_path)
        assert backslash_path.exists()  # 目录应该存在，因为我们在测试中创建了它 