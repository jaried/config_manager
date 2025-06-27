# tests/01_unit_tests/test_config_manager/test_path_configuration.py
from __future__ import annotations
from datetime import datetime

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from is_debug import is_debug

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
    
    def test_detect_debug_mode_with_is_debug_available(self):
        """测试is_debug模块可用时的调试模式检测"""
        with patch('is_debug.is_debug') as mock_is_debug:
            mock_is_debug.return_value = True
            result = DebugDetector.detect_debug_mode()
            assert result is True
            
            mock_is_debug.return_value = False
            result = DebugDetector.detect_debug_mode()
            assert result is False
    
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
    
    def test_format_date(self):
        """测试日期格式化"""
        dt = datetime(2025, 1, 8, 10, 30, 45)
        result = TimeProcessor.format_date(dt)
        assert result == '2025-01-08'
    
    def test_format_time(self):
        """测试时间格式化"""
        dt = datetime(2025, 1, 8, 10, 30, 45)
        result = TimeProcessor.format_time(dt)
        assert result == '103045'
    
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
    
    def test_generate_work_directory_debug_mode(self):
        """测试调试模式下的工作目录生成"""
        generator = PathGenerator()
        temp_base_dir = tempfile.mkdtemp()
        result = generator.generate_work_directory(
            base_dir=temp_base_dir,
            project_name='test_project',
            experiment_name='exp_001',
            debug_mode=True
        )
        expected = str(Path(temp_base_dir) / 'debug' / 'test_project' / 'exp_001')
        assert result == expected
    
    def test_generate_work_directory_production_mode(self):
        """测试生产模式下的工作目录生成"""
        generator = PathGenerator()
        temp_base_dir = tempfile.mkdtemp()
        result = generator.generate_work_directory(
            base_dir=temp_base_dir,
            project_name='test_project',
            experiment_name='exp_001',
            debug_mode=False
        )
        expected = str(Path(temp_base_dir) / 'test_project' / 'exp_001')
        assert result == expected
    
    def test_generate_checkpoint_directories(self):
        """测试检查点目录生成"""
        generator = PathGenerator()
        temp_base_dir = tempfile.mkdtemp()
        work_dir = str(Path(temp_base_dir) / 'test_project' / 'exp_001')
        result = generator.generate_checkpoint_directories(work_dir)
        expected = {
            'paths.checkpoint_dir': str(Path(work_dir) / 'checkpoint'),
            'paths.best_checkpoint_dir': str(Path(work_dir) / 'checkpoint' / 'best')
        }
        assert result == expected
    
    def test_generate_log_directories(self):
        """测试日志目录生成"""
        generator = PathGenerator()
        temp_base_dir = tempfile.mkdtemp()
        work_dir = str(Path(temp_base_dir) / 'test_project' / 'exp_001')
        date_str = '2025-01-08'
        time_str = '103045'
        result = generator.generate_log_directories(work_dir, date_str, time_str)
        expected = {
            'paths.tsb_logs_dir': str(Path(work_dir) / 'tsb_logs' / date_str / time_str),
            'paths.log_dir': str(Path(work_dir) / 'logs' / date_str / time_str)
        }
        assert result == expected


class TestPathValidator:
    """路径验证器测试"""
    
    def test_validate_base_dir_valid_path(self):
        """测试有效基础目录验证"""
        temp_base_dir = tempfile.mkdtemp()
        result = PathValidator.validate_base_dir(temp_base_dir)
        assert result is True
    
    def test_validate_base_dir_invalid_path(self):
        """测试无效基础目录验证"""
        result = PathValidator.validate_base_dir('')
        assert result is False
        
        result = PathValidator.validate_base_dir(None)
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
        
        result = PathValidator.validate_path_format(None)
        assert result is False


class TestDirectoryCreator:
    """目录创建器测试"""
    
    def test_create_directory_success(self):
        """测试成功创建目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = os.path.join(temp_dir, 'test_dir')
            result = DirectoryCreator.create_directory(test_path)
            assert result is True
            assert os.path.exists(test_path)
    
    def test_create_directory_already_exists(self):
        """测试目录已存在的情况"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = DirectoryCreator.create_directory(temp_dir)
            assert result is True
    
    def test_create_path_structure(self):
        """测试创建路径结构"""
        creator = DirectoryCreator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = {
                'work_dir': os.path.join(temp_dir, 'work'),
                'checkpoint_dir': os.path.join(temp_dir, 'checkpoint'),
                'logs_dir': os.path.join(temp_dir, 'logs')
            }
            
            results = creator.create_path_structure(paths)
            
            assert all(results.values())
            for path in paths.values():
                assert os.path.exists(path)


class TestConfigUpdater:
    """配置更新器测试"""
    
    def test_update_path_configurations(self):
        """测试更新路径配置"""
        mock_config = Mock()
        # 配置Mock对象的_data属性
        mock_config._data = {}
        
        updater = ConfigUpdater(mock_config)
        
        with tempfile.TemporaryDirectory() as temp_base_dir:
            path_configs = {
                'paths.work_dir': str(Path(temp_base_dir) / 'test'),
                'paths.checkpoint_dir': str(Path(temp_base_dir) / 'test' / 'checkpoint')
            }
            updater.update_path_configurations(path_configs)
            assert mock_config.set.call_count == 2
            mock_config.set.assert_any_call('paths.work_dir', path_configs['paths.work_dir'], autosave=False)
            mock_config.set.assert_any_call('paths.checkpoint_dir', path_configs['paths.checkpoint_dir'], autosave=False)
    
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
        
        # 设置基本属性
        mock_config.base_dir = 'd:\\logs'
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
        
        with patch.object(DebugDetector, 'detect_debug_mode', return_value=False):
            manager = PathConfigurationManager(mock_config)
            manager.initialize_path_configuration()
            
            # 验证调用了相关方法
            assert mock_config.set.called
    
    def test_initialize_path_configuration_with_is_debug_error(self):
        """测试is_debug模块不可用时的初始化"""
        mock_config = self._create_mock_config()
        # 配置Mock对象的_data属性
        mock_config._data = {}
        
        with patch.object(DebugDetector, 'detect_debug_mode', side_effect=ImportError):
            manager = PathConfigurationManager(mock_config)
            manager.initialize_path_configuration()
            
            # 应该继续执行，不抛出异常
            assert mock_config.set.called
    
    def test_generate_all_paths(self):
        """测试生成所有路径配置"""
        mock_config = self._create_mock_config()
        
        manager = PathConfigurationManager(mock_config)
        paths = manager.generate_all_paths()
        
        # 验证返回的路径配置
        assert 'paths.work_dir' in paths
        assert 'paths.checkpoint_dir' in paths
        assert 'paths.best_checkpoint_dir' in paths
        assert 'paths.debug_dir' in paths
        assert 'paths.tsb_logs_dir' in paths
        assert 'paths.log_dir' in paths
    
    def test_generate_all_paths_with_cache(self):
        """测试带缓存的路径生成"""
        mock_config = self._create_mock_config()
        
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
        
        manager = PathConfigurationManager(mock_config)
        manager.generate_all_paths()  # 建立缓存
        
        manager.invalidate_cache()
        
        assert manager._cache_valid is False
        assert len(manager._path_cache) == 0
    
    def test_validate_path_configuration_success(self):
        """测试路径配置验证成功"""
        mock_config = self._create_mock_config()
        
        manager = PathConfigurationManager(mock_config)
        result = manager.validate_path_configuration()
        
        assert result is True
    
    def test_create_directories(self):
        """测试创建目录结构"""
        mock_config = self._create_mock_config()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_config.base_dir = temp_dir
            
            manager = PathConfigurationManager(mock_config)
            results = manager.create_directories(create_all=True)
            
            # 验证创建结果
            assert isinstance(results, dict)
            assert len(results) > 0
    
    def test_get_path_info(self):
        """测试获取路径配置信息"""
        mock_config = self._create_mock_config()
        
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
        
        with patch.object(DebugDetector, 'detect_debug_mode', return_value=True):
            manager = PathConfigurationManager(mock_config)
            manager.update_debug_mode()
            
            # 验证缓存被清除
            assert manager._cache_valid is False


class TestPathConfigurationIntegration:
    """路径配置集成测试"""
    
    def test_full_path_configuration_flow(self):
        """测试完整路径配置流程"""
        mock_config = Mock()
        
        # 设置属性访问
        mock_config.base_dir = 'd:\\logs'
        mock_config.project_name = 'integration_test'
        mock_config.experiment_name = 'exp_integration'
        mock_config.debug_mode = True
        mock_config.first_start_time = '2025-01-08T15:30:00'
        
        with patch.object(DebugDetector, 'detect_debug_mode', return_value=True):
            manager = PathConfigurationManager(mock_config)
            manager.initialize_path_configuration()
            
            # 获取生成的路径
            paths = manager.generate_all_paths()
            
            # 验证调试模式路径
            expected_work_dir = str(Path('d:\\logs') / 'debug' / 'integration_test' / 'exp_integration')
            assert paths['paths.work_dir'] == expected_work_dir
            
            # 验证时间基础的日志目录
            assert '2025-01-08' in paths['paths.tsb_logs_dir']
            assert '153000' in paths['paths.tsb_logs_dir']
    
    def test_debug_production_mode_switching(self):
        """测试调试/生产模式切换"""
        mock_config = Mock()
        mock_config.base_dir = 'd:\\logs'
        mock_config.project_name = 'switch_test'
        mock_config.experiment_name = 'exp_switch'
        mock_config.first_start_time = '2025-01-08T16:00:00'
        
        manager = PathConfigurationManager(mock_config)
        
        # 测试调试模式
        mock_config.debug_mode = True
        paths_debug = manager.generate_all_paths()
        assert 'debug' in paths_debug['paths.work_dir']
        
        # 切换到生产模式
        manager.invalidate_cache()
        mock_config.debug_mode = False
        paths_prod = manager.generate_all_paths()
        assert 'debug' not in paths_prod['paths.work_dir']
        
        # 验证路径不同
        assert paths_debug['paths.work_dir'] != paths_prod['paths.work_dir']


if __name__ == '__main__':
    pytest.main([__file__]) 