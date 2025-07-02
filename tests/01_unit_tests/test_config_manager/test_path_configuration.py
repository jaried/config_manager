# tests/01_unit_tests/test_config_manager/test_path_configuration.py
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import sys

from src.config_manager import get_config_manager, _clear_instances_for_testing

@pytest.fixture(autouse=True)
def clear_instances_fixture():
    """在每个测试前后自动清理ConfigManager单例"""
    _clear_instances_for_testing()
    yield
    _clear_instances_for_testing()

# 导入被测试的模块
from src.config_manager.core.path_configuration import (
    PathConfigurationManager,
    DebugDetector,
    TimeProcessor,
    PathGenerator,
    PathValidator,
    DirectoryCreator,
    ConfigUpdater,
    PathConfigurationError,
    InvalidPathError,
    DirectoryCreationError,
    TimeParsingError
)



class TestDebugDetector:
    """调试模式检测器测试"""
    
    @pytest.mark.skip(reason="is_debug模块在当前环境不可用")
    def test_detect_debug_mode_with_is_debug_available(self):
        """测试is_debug模块可用时的调试模式检测"""
        pass
    
    def test_detect_debug_mode_with_import_error(self):
        """测试is_debug模块不可用时的调试模式检测"""
        with patch('builtins.__import__', side_effect=ImportError):
            result = DebugDetector.detect_debug_mode()
            assert result is False
    
    def test_get_debug_status_info(self):
        """测试获取调试状态信息"""
        with patch.object(DebugDetector, 'detect_debug_mode', return_value=True):
            info = DebugDetector.get_debug_status_info()
            
            assert 'debug_mode' in info
            assert 'is_debug_available' in info
            assert 'detection_time' in info
            assert info['debug_mode'] is True
            assert info['is_debug_available'] is True



class TestTimeProcessor:
    """时间处理器测试"""
    
    def test_parse_first_start_time_valid_iso(self):
        """测试解析有效的ISO时间格式"""
        test_time = '2025-01-08T10:30:45'
        date_str, time_str = TimeProcessor.parse_first_start_time(test_time)
        
        assert date_str == '2025-01-08'
        assert time_str == '103045'
    
    def test_parse_first_start_time_with_z_suffix(self):
        """测试解析带Z后缀的时间格式"""
        test_time = '2025-01-08T10:30:45Z'
        date_str, time_str = TimeProcessor.parse_first_start_time(test_time)
        
        assert date_str == '2025-01-08'
        assert time_str == '103045'
    
    def test_parse_first_start_time_invalid_format(self):
        """测试解析无效时间格式"""
        with pytest.raises(TimeParsingError):
            TimeProcessor.parse_first_start_time('invalid-time')
    
    # format_date和format_time方法已被移除，测试相应移除
    
    def test_get_current_time_components(self):
        """测试获取当前时间组件"""
        date_str, time_str = TimeProcessor.get_current_time_components()
        
        # 验证格式
        assert len(date_str) == 10  # YYYY-MM-DD
        assert len(time_str) == 6   # HHMMSS
        assert '-' in date_str
        assert date_str.count('-') == 2



class TestPathGenerator:
    """路径生成器测试"""
    
    def test_generate_work_directory_debug_mode(self, tmp_path):
        """测试调试模式下的工作目录生成"""
        generator = PathGenerator()
        result = generator.generate_work_directory(
            base_dir=str(tmp_path),
            project_name='test_project',
            experiment_name='exp_001',
            debug_mode=True
        )
        expected = str(tmp_path / 'debug' / 'test_project' / 'exp_001')
        assert result == expected
    
    def test_generate_work_directory_production_mode(self, tmp_path):
        """测试生产模式下的工作目录生成"""
        generator = PathGenerator()
        result = generator.generate_work_directory(
            base_dir=str(tmp_path),
            project_name='test_project',
            experiment_name='exp_001',
            debug_mode=False
        )
        expected = str(tmp_path / 'test_project' / 'exp_001')
        assert result == expected
    
    def test_generate_checkpoint_directories(self, tmp_path):
        """测试检查点目录生成"""
        generator = PathGenerator()
        work_dir = tmp_path / 'test_project' / 'exp_001'
        result = generator.generate_checkpoint_directories(str(work_dir))
        expected = {
            'paths.checkpoint_dir': str(work_dir / 'checkpoint'),
            'paths.best_checkpoint_dir': str(work_dir / 'checkpoint' / 'best')
        }
        assert result == expected
    
    def test_generate_log_directories(self, tmp_path):
        """测试日志目录生成"""
        generator = PathGenerator()
        work_dir = tmp_path / 'test_project' / 'exp_001'
        date_str = '2025-01-08'
        time_str = '103045'
        result = generator.generate_log_directories(str(work_dir), date_str, time_str)
        expected = {
            'paths.tsb_logs_dir': str(work_dir / 'tsb_logs' / date_str / time_str),
            'paths.log_dir': str(work_dir / 'logs' / date_str / time_str)
        }
        assert result == expected



class TestPathValidator:
    """路径验证器测试"""
    
    def test_validate_base_dir_valid_path(self, tmp_path):
        """测试有效基础目录验证"""
        result = PathValidator.validate_base_dir(str(tmp_path))
        assert result is True
    
    def test_validate_base_dir_invalid_path(self):
        """测试无效基础目录验证"""
        result = PathValidator.validate_base_dir('')
        assert result is False
        
        result = PathValidator.validate_base_dir(None)  # type: ignore
        assert result is False
    
    def test_validate_path_format_valid(self):
        """测试有效路径格式验证"""
        temp_base_dir = tempfile.mkdtemp()
        test_path = str(Path(temp_base_dir) / 'test')
        result = PathValidator.validate_path_format(test_path)
        assert result is True
    
    def test_validate_path_format_invalid(self):
        """测试无效路径格式验证"""
        result = PathValidator.validate_path_format('')
        assert result is False
        
        result = PathValidator.validate_path_format(None)  # type: ignore
        assert result is False



class TestDirectoryCreator:
    """目录创建器"""

    @pytest.mark.skip(reason="路径不再自动创建，此测试已不适用")
    def test_create_directory_success(self, tmp_path):
        """测试create_directory函数是否能成功创建目录"""
        # 功能已移除，测试不再适用
        pytest.skip("路径不再自动创建，此测试已不适用")

    @pytest.mark.skip(reason="路径不再自动创建，此测试已不适用")
    def test_create_directory_already_exists(self, tmp_path):
        """测试当目录已存在时，create_directory不会抛出异常"""
        # 功能已移除，测试不再适用
        pytest.skip("路径不再自动创建，此测试已不适用")

    @pytest.mark.skip(reason="路径不再自动创建，此测试已不适用")
    def test_create_path_structure(self, tmp_path):
        """测试create_path_structure是否能成功创建所有目录"""
        # 功能已移除，测试不再适用
        pytest.skip("路径不再自动创建，此测试已不适用")



class TestConfigUpdater:
    """配置更新器测试"""
    
    def test_update_path_configurations(self, tmp_path):
        """测试更新路径配置"""
        mock_config = Mock()
        mock_config._data = {}
        
        updater = ConfigUpdater(mock_config)
        
        path_configs = {
            'paths.work_dir': str(tmp_path / 'test'),
            'paths.checkpoint_dir': str(tmp_path / 'test' / 'checkpoint')
        }
        updater.update_path_configurations(path_configs)
        assert mock_config.set.call_count == 2
        mock_config.set.assert_any_call('paths.work_dir', path_configs['paths.work_dir'], autosave=False)
    
    def test_update_debug_mode(self):
        """测试更新调试模式"""
        mock_config = Mock()
        updater = ConfigUpdater(mock_config)
        
        # 测试调用不会抛出异常
        updater.update_debug_mode(True)
        updater.update_debug_mode(False)
        
        # ConfigUpdater的update_debug_mode方法是空实现，主要用于兼容性
        # 实际的debug_mode管理在PathConfigurationManager中



class TestPathConfigurationManager:
    """路径配置管理器测试"""
    
    def _create_mock_config(self):
        """创建Mock配置对象"""
        mock_config = Mock()
        
        # 设置基本属性 - 使用系统临时路径
        temp_dir = tempfile.mkdtemp()
        mock_config.base_dir = temp_dir
        mock_config.project_name = 'test_project'
        mock_config.experiment_name = 'exp_001'
        mock_config.debug_mode = False
        mock_config.first_start_time = '2025-01-08T10:30:45'
        
        return mock_config
    
    def test_initialize_path_configuration_success(self):
        """测试成功初始化路径配置"""
        mock_config = self._create_mock_config()
        # 配置Mock对象的_data属性
        mock_config._data = {}
        mock_config.is_test_mode = Mock(return_value=False)
        
        with patch.object(DebugDetector, 'detect_debug_mode', return_value=False):
            manager = PathConfigurationManager(mock_config)
            manager.initialize_path_configuration()
            
            # 验证paths被设置
            assert hasattr(mock_config, 'paths')
    
    def test_initialize_path_configuration_with_is_debug_error(self):
        """测试is_debug模块不可用时的初始化"""
        mock_config = self._create_mock_config()
        # 配置Mock对象的_data属性
        mock_config._data = {}
        mock_config.is_test_mode = Mock(return_value=False)
        
        with patch.object(DebugDetector, 'detect_debug_mode', side_effect=ImportError):
            manager = PathConfigurationManager(mock_config)
            manager.initialize_path_configuration()
            
            # 应该继续执行，不抛出异常
            assert hasattr(mock_config, 'paths')
    
    def test_generate_all_paths(self):
        """测试生成所有路径配置"""
        mock_config = self._create_mock_config()
        mock_config.is_test_mode = Mock(return_value=False)
        
        manager = PathConfigurationManager(mock_config)
        paths = manager.generate_all_paths()
        
        # 验证返回的路径配置
        assert isinstance(paths, dict)
        assert 'paths' in paths
        assert isinstance(paths['paths'], dict)
        assert all(isinstance(path, str) for path in paths['paths'].values())
        assert all(len(path) > 0 for path in paths['paths'].values())
        assert all(Path(path).is_absolute() for path in paths['paths'].values())
        
        # 验证所有必需的路径都存在
        assert 'work_dir' in paths['paths']
        assert 'checkpoint_dir' in paths['paths']
        assert 'best_checkpoint_dir' in paths['paths']
        assert 'debug_dir' in paths['paths']
        assert 'tsb_logs_dir' in paths['paths']
        assert 'log_dir' in paths['paths']
    
    def test_generate_all_paths_with_cache(self):
        """测试带缓存的路径生成"""
        mock_config = self._create_mock_config()
        mock_config.is_test_mode = Mock(return_value=False)
        
        manager = PathConfigurationManager(mock_config)
        
        # 第一次调用
        paths1 = manager.generate_all_paths()
        
        # 第二次调用应该使用缓存
        paths2 = manager.generate_all_paths()
        
        assert paths1 == paths2
        assert manager._cache_valid is True
    
    def test_invalidate_cache(self):
        """测试缓存失效"""
        mock_config = self._create_mock_config()
        mock_config.is_test_mode = Mock(return_value=False)
        
        manager = PathConfigurationManager(mock_config)
        manager.generate_all_paths()  # 建立缓存
        
        manager.invalidate_cache()
        
        assert manager._cache_valid is False
        assert len(manager._path_cache) == 0
    
    def test_validate_path_configuration_success(self):
        """测试路径配置验证成功"""
        mock_config = self._create_mock_config()
        mock_config.is_test_mode = Mock(return_value=False)
        # 添加get方法以返回正确的值
        mock_config.get = Mock(side_effect=lambda key: getattr(mock_config, key, None))
        
        manager = PathConfigurationManager(mock_config)
        paths = manager.generate_all_paths()
        
        # 验证所有生成的路径都是有效的字符串
        assert isinstance(paths, dict)
        assert 'paths' in paths
        assert isinstance(paths['paths'], dict)
        assert all(isinstance(path, str) for path in paths['paths'].values())
        assert all(len(path) > 0 for path in paths['paths'].values())
        assert all(Path(path).is_absolute() for path in paths['paths'].values())
        
        result = manager.validate_path_configuration()
        assert result is True
    
    def test_create_directories(self):
        """测试创建目录结构"""
        pytest.skip("路径自动创建功能已被移除（任务2）")
    
    def test_get_path_info(self):
        """测试获取路径配置信息"""
        mock_config = self._create_mock_config()
        mock_config.is_test_mode = Mock(return_value=False)
        
        with patch.object(DebugDetector, 'get_debug_status_info', return_value={'debug_mode': False}):
            manager = PathConfigurationManager(mock_config)
            info = manager.get_path_info()
            
            # 检查基本信息
            assert 'current_os' in info
            assert 'os_family' in info
            assert 'base_dir' in info
            assert 'project_name' in info
            assert 'experiment_name' in info
            assert 'debug_mode' in info
            assert 'platform_info' in info
            assert 'generated_paths' in info
    
    def test_update_debug_mode(self):
        """测试更新调试模式"""
        mock_config = self._create_mock_config()
        mock_config.is_test_mode = Mock(return_value=False)
        
        with patch.object(DebugDetector, 'detect_debug_mode', return_value=True):
            manager = PathConfigurationManager(mock_config)
            # 首先生成一些路径来建立缓存
            manager.generate_all_paths()
            assert manager._cache_valid is True
            
            # 然后更新debug模式
            manager.update_debug_mode()
            
            # 验证缓存被清除（update_debug_mode已经没有失效缓存的逻辑）
            # 因为debug_mode是动态属性，不需要失效缓存
            assert manager._cache_valid is True



class TestPathConfigurationIntegration:
    """路径配置集成测试"""

    @pytest.mark.skip(reason="路径生成逻辑已重构，此测试已不适用")
    def test_full_path_configuration_flow_safe(self, tmp_path):
        """测试完整的路径配置流程（安全模式）"""
        # 功能逻辑已改变，测试不再适用
        pytest.skip("路径生成逻辑已重构，此测试已不适用")

    @pytest.mark.skip(reason="路径生成逻辑已重构，此测试已不适用")
    def test_debug_production_mode_switching_safe(self):
        """测试调试模式和生产模式切换的安全性"""
        # 功能逻辑已改变，测试不再适用
        pytest.skip("路径生成逻辑已重构，此测试已不适用")



class TestPathConfiguration:
    """路径配置单元测试"""
    
    def test_paths_are_generated_automatically_by_get_config_manager(self, tmp_path):
        """新增测试：验证 get_config_manager 是否自动生成路径"""
        config_file = tmp_path / "config.yaml"
        config_content = f"project_name: auto_gen_test\nbase_dir: {tmp_path.as_posix()}"
        config_file.write_text(config_content)
        
        config = get_config_manager(config_path=str(config_file))
        
        assert hasattr(config, 'paths')
        assert hasattr(config.paths, 'work_dir')
        assert "auto_gen_test" in str(config.paths.work_dir)

    def test_paths_are_resolved_correctly(self, tmp_path):
        """测试路径是否能被正确解析"""
        config_file = tmp_path / "config.yaml"
        base_dir = tmp_path
        
        config_content = f"""
project_name: my_project
base_dir: {base_dir.as_posix()}
        """
        config_file.write_text(config_content)
        
        config = get_config_manager(config_path=str(config_file))

        assert Path(config.paths.work_dir).is_absolute()
        assert "my_project" in str(config.paths.work_dir)
        
        # 验证目录已自动创建（任务9功能）
        assert Path(config.paths.work_dir).exists()

    @patch('src.config_manager.core.path_configuration.DebugDetector.detect_debug_mode', return_value=True)
    def test_debug_paths_are_used_in_debug_mode(self, mock_debug_detect, tmp_path):
        """测试在调试模式下，是否使用调试路径"""
        config_file = tmp_path / "config.yaml"
        
        config_content = f"""
project_name: my_project
base_dir: {tmp_path.as_posix()}
        """
        config_file.write_text(config_content)
        
        config = get_config_manager(config_path=str(config_file))

        work_dir = Path(config.paths.work_dir)
        assert 'debug' in work_dir.parts


if __name__ == '__main__':
    pytest.main() 