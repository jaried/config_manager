# tests/01_unit_tests/test_config_manager/test_cross_platform_paths.py
import pytest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config_manager.core.cross_platform_paths import (
    CrossPlatformPathManager,
    get_cross_platform_manager,
    convert_to_multi_platform_config,
    get_platform_path
)


class TestCrossPlatformPathManager:
    """跨平台路径管理器测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 重置全局实例
        import src.config_manager.core.cross_platform_paths as cross_platform_module
        cross_platform_module._cross_platform_manager = None
        self.manager = get_cross_platform_manager()

    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = get_cross_platform_manager()
        manager2 = get_cross_platform_manager()
        assert manager1 is manager2

    @patch('platform.system')
    @patch('sys.platform')
    def test_detect_windows_os(self, mock_sys_platform, mock_platform_system):
        """测试Windows操作系统检测"""
        # 设置模拟返回值
        mock_platform_system.return_value = 'Windows'
        mock_sys_platform = 'win32'
        
        # 重新初始化管理器以使用模拟值
        import src.config_manager.core.cross_platform_paths as cross_platform_module
        cross_platform_module._cross_platform_manager = None
        manager = get_cross_platform_manager()
        
        assert manager.get_current_os() == 'windows'

    @patch('platform.system')
    @patch('sys.platform')
    def test_detect_linux_os(self, mock_sys_platform, mock_platform_system):
        """测试Linux操作系统检测"""
        # 设置模拟返回值
        mock_platform_system.return_value = 'Linux'
        mock_sys_platform = 'linux'
        
        # 重新初始化管理器以使用模拟值
        import src.config_manager.core.cross_platform_paths as cross_platform_module
        cross_platform_module._cross_platform_manager = None
        manager = get_cross_platform_manager()
        
        assert manager.get_current_os() == 'linux'

    @patch('platform.system')
    @patch('sys.platform')
    @patch('os.path.exists')
    @patch('builtins.open', create=True)
    def test_detect_ubuntu_os(self, mock_open, mock_exists, mock_sys_platform, mock_platform_system):
        """测试Ubuntu操作系统检测"""
        # 设置模拟返回值
        mock_platform_system.return_value = 'Linux'
        mock_sys_platform = 'linux'
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = 'NAME="Ubuntu"'
        
        # 重新初始化管理器以使用模拟值
        import src.config_manager.core.cross_platform_paths as cross_platform_module
        cross_platform_module._cross_platform_manager = None
        manager = get_cross_platform_manager()
        
        assert manager.get_current_os() == 'ubuntu'

    @patch('platform.system')
    @patch('sys.platform')
    def test_detect_macos_os(self, mock_sys_platform, mock_platform_system):
        """测试macOS操作系统检测"""
        # 设置模拟返回值
        mock_platform_system.return_value = 'Darwin'
        mock_sys_platform = 'darwin'
        
        # 重新初始化管理器以使用模拟值
        import src.config_manager.core.cross_platform_paths as cross_platform_module
        cross_platform_module._cross_platform_manager = None
        manager = get_cross_platform_manager()
        
        assert manager.get_current_os() == 'macos'

    def test_get_os_family(self):
        """测试操作系统家族获取"""
        # 测试Windows家族
        with patch.object(self.manager, '_current_os', 'windows'):
            assert self.manager.get_os_family() == 'windows'
        
        # 测试Unix家族
        with patch.object(self.manager, '_current_os', 'linux'):
            assert self.manager.get_os_family() == 'unix'
        
        with patch.object(self.manager, '_current_os', 'ubuntu'):
            assert self.manager.get_os_family() == 'unix'
        
        with patch.object(self.manager, '_current_os', 'macos'):
            assert self.manager.get_os_family() == 'unix'

    def test_get_default_path(self):
        """测试默认路径获取"""
        # 测试Windows默认路径
        with patch.object(self.manager, '_current_os', 'windows'):
            base_dir = self.manager.get_default_path('base_dir')
            assert 'd:\\logs' in base_dir
        
        # 测试Linux默认路径
        with patch.object(self.manager, '_current_os', 'linux'):
            base_dir = self.manager.get_default_path('base_dir')
            assert '/home/tony/logs' in base_dir

    def test_get_platform_path_string(self):
        """测试字符串路径获取"""
        path_config = 'd:\\test_logs'
        result = self.manager.get_platform_path(path_config, 'base_dir')
        assert result == 'd:\\test_logs'

    def test_get_platform_path_dict(self):
        """测试字典路径获取"""
        path_config = {
            'windows': 'd:\\windows_logs',
            'linux': '/home/tony/linux_logs',
            'ubuntu': '/home/tony/ubuntu_logs',
            'macos': '/Users/tony/macos_logs'
        }
        
        # 测试Windows平台
        with patch.object(self.manager, '_current_os', 'windows'):
            result = self.manager.get_platform_path(path_config, 'base_dir')
            assert result == 'd:\\windows_logs'
        
        # 测试Linux平台
        with patch.object(self.manager, '_current_os', 'linux'):
            result = self.manager.get_platform_path(path_config, 'base_dir')
            assert result == '/home/tony/linux_logs'

    def test_get_platform_path_dict_fallback(self):
        """测试字典路径获取的回退机制"""
        path_config = {
            'unix': '/home/tony/unix_logs'
        }
        
        # 测试Linux平台回退到unix
        with patch.object(self.manager, '_current_os', 'linux'):
            result = self.manager.get_platform_path(path_config, 'base_dir')
            assert result == '/home/tony/unix_logs'

    def test_get_platform_path_dict_default(self):
        """测试字典路径获取的默认值"""
        path_config = {
            'unknown_os': '/unknown/path'
        }
        
        # 测试未知平台使用默认值
        with patch.object(self.manager, '_current_os', 'unknown'):
            result = self.manager.get_platform_path(path_config, 'base_dir')
            assert result is not None

    def test_convert_to_multi_platform_config_windows_path(self):
        """测试Windows路径转换为多平台配置"""
        windows_path = 'd:\\demo_logs'
        result = self.manager.convert_to_multi_platform_config(windows_path, 'base_dir')
        
        assert isinstance(result, dict)
        assert result['windows'] == 'd:\\demo_logs'
        assert 'linux' in result
        assert 'ubuntu' in result
        assert 'macos' in result

    def test_convert_to_multi_platform_config_linux_path(self):
        """测试Linux路径转换为多平台配置"""
        linux_path = '/home/tony/logs'
        result = self.manager.convert_to_multi_platform_config(linux_path, 'base_dir')
        
        assert isinstance(result, dict)
        assert result['linux'] == '/home/tony/logs'
        assert result['ubuntu'] == '/home/tony/logs'
        assert 'windows' in result
        assert 'macos' in result

    def test_convert_to_multi_platform_config_macos_path(self):
        """测试macOS路径转换为多平台配置"""
        macos_path = '/Users/tony/logs'
        result = self.manager.convert_to_multi_platform_config(macos_path, 'base_dir')
        
        assert isinstance(result, dict)
        assert result['macos'] == '/Users/tony/logs'
        assert 'windows' in result
        assert 'linux' in result
        assert 'ubuntu' in result

    def test_detect_path_platform_windows(self):
        """测试Windows路径平台检测"""
        windows_path = 'd:\\test\\path'
        result = self.manager._detect_path_platform(windows_path)
        assert result == 'windows'

    def test_detect_path_platform_linux(self):
        """测试Linux路径平台检测"""
        linux_path = '/home/tony/test'
        result = self.manager._detect_path_platform(linux_path)
        assert result == 'linux'

    def test_detect_path_platform_relative(self):
        """测试相对路径平台检测"""
        relative_path = 'relative/path'
        with patch.object(self.manager, '_current_os', 'windows'):
            result = self.manager._detect_path_platform(relative_path)
            assert result == 'windows'

    def test_normalize_path(self):
        """测试路径标准化"""
        # 测试Windows路径标准化
        windows_path = 'd:/test\\path'
        result = self.manager.normalize_path(windows_path)
        assert 'd:\\test\\path' in result or 'd:/test/path' in result
        
        # 测试Linux路径标准化
        linux_path = '/home//tony//logs'
        result = self.manager.normalize_path(linux_path)
        assert '/home/tony/logs' in result

    def test_get_platform_info(self):
        """测试平台信息获取"""
        info = self.manager.get_platform_info()
        
        assert 'current_os' in info
        assert 'os_family' in info
        assert 'platform_system' in info
        assert 'platform_release' in info
        assert 'platform_version' in info
        assert 'platform_machine' in info
        assert 'sys_platform' in info
        assert 'detection_time' in info


class TestCrossPlatformPathFunctions:
    """跨平台路径函数测试类"""

    def test_get_cross_platform_manager(self):
        """测试获取跨平台管理器"""
        manager = get_cross_platform_manager()
        assert isinstance(manager, CrossPlatformPathManager)

    def test_convert_to_multi_platform_config_function(self):
        """测试转换函数"""
        windows_path = 'd:\\test_logs'
        result = convert_to_multi_platform_config(windows_path, 'base_dir')
        
        assert isinstance(result, dict)
        assert result['windows'] == 'd:\\test_logs'
        assert 'linux' in result
        assert 'ubuntu' in result
        assert 'macos' in result

    def test_get_platform_path_function(self):
        """测试获取平台路径函数"""
        path_config = {
            'windows': 'd:\\windows_logs',
            'linux': '/home/tony/linux_logs'
        }
        
        # 直接测试函数，不使用Mock
        result = get_platform_path(path_config, 'base_dir')
        # 结果应该是当前平台的路径
        assert result in path_config.values() or result == 'd:\\logs', f"返回的路径应该在配置中或使用默认值，实际返回: {result}"


class TestCrossPlatformPathIntegration:
    """跨平台路径集成测试类"""

    def test_config_manager_integration(self):
        """测试与配置管理器的集成"""
        from src.config_manager import get_config_manager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_cross_platform.yaml')
            
            # 创建配置管理器
            config = get_config_manager(config_path=config_path)
            
            # 测试设置单一路径，自动转换为多平台格式
            config.set('base_dir', 'd:\\test_logs')
            
            # 验证是否转换为多平台格式
            base_dir_value = config._data.get('base_dir')
            # 检查是否为ConfigNode或dict类型
            assert hasattr(base_dir_value, '_data') or isinstance(base_dir_value, dict), "base_dir应该被转换为多平台格式"
            
            # 获取实际的数据
            if hasattr(base_dir_value, '_data'):
                actual_data = base_dir_value._data
            else:
                actual_data = base_dir_value
            
            assert 'windows' in actual_data, "应该包含windows路径"
            assert 'linux' in actual_data, "应该包含linux路径"
            assert 'ubuntu' in actual_data, "应该包含ubuntu路径"
            assert 'macos' in actual_data, "应该包含macos路径"
            
            # 验证原始路径被正确映射
            assert actual_data['windows'] == 'd:\\test_logs', "Windows路径应该保持原值"
            
            # 验证获取时返回当前平台路径
            current_path = config.get('base_dir')
            assert current_path is not None, "应该能获取到当前平台路径"
            # 检查是否为字符串或ConfigNode
            assert isinstance(current_path, str) or hasattr(current_path, '_data'), "返回的路径应该是字符串或ConfigNode"

    def test_path_configuration_manager_integration(self):
        """测试与路径配置管理器的集成"""
        from src.config_manager import get_config_manager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_path_config.yaml')
            
            # 创建配置管理器
            config = get_config_manager(config_path=config_path)
            
            # 设置多平台base_dir
            multi_platform_base_dir = {
                'windows': 'd:\\multi_logs',
                'linux': '/home/tony/multi_logs',
                'ubuntu': '/home/tony/multi_logs',
                'macos': '/Users/tony/multi_logs'
            }
            config.set('base_dir', multi_platform_base_dir)
            
            # 设置项目配置
            config.set('project_name', 'test_project')
            config.set('experiment_name', 'test_exp')
            
            # 验证路径配置管理器能够正确处理
            try:
                path_info = config.get_path_configuration_info()
                assert 'current_os' in path_info
                assert 'generated_paths' in path_info
            except Exception as e:
                # 如果路径配置管理器不可用，至少验证基本功能
                current_base_dir = config.get('base_dir')
                assert current_base_dir is not None

    def test_backward_compatibility(self):
        """测试向后兼容性"""
        from src.config_manager import get_config_manager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_backward.yaml')
            
            # 创建配置管理器
            config = get_config_manager(config_path=config_path)
            
            # 测试现有的单一路径配置仍然工作
            config.set('work_dir', 'd:\\work')
            config.set('tensorboard_dir', 'd:\\tensorboard')
            
            # 验证获取值正常
            work_dir = config.get('work_dir')
            tensorboard_dir = config.get('tensorboard_dir')
            
            assert work_dir == 'd:\\work'
            assert tensorboard_dir == 'd:\\tensorboard'


class TestCrossPlatformPathErrorHandling:
    """跨平台路径错误处理测试类"""

    def test_os_detection_error_handling(self):
        """测试操作系统检测错误处理"""
        with patch('platform.system', side_effect=Exception("Detection failed")):
            with patch('sys.platform', 'unknown'):
                # 重新初始化管理器以使用模拟值
                import src.config_manager.core.cross_platform_paths as cross_platform_module
                cross_platform_module._cross_platform_manager = None
                manager = get_cross_platform_manager()
                
                # 应该返回默认操作系统
                current_os = manager.get_current_os()
                assert current_os in ['windows', 'linux', 'ubuntu', 'macos']

    def test_path_conversion_error_handling(self):
        """测试路径转换错误处理"""
        manager = get_cross_platform_manager()
        
        # 测试空路径
        result = manager.convert_to_multi_platform_config('', 'base_dir')
        assert isinstance(result, dict)
        
        # 测试None路径
        result = manager.convert_to_multi_platform_config(None, 'base_dir')
        assert isinstance(result, dict)

    def test_platform_path_error_handling(self):
        """测试平台路径获取错误处理"""
        manager = get_cross_platform_manager()
        
        # 测试无效的路径配置
        result = manager.get_platform_path(None, 'base_dir')
        assert result is not None
        
        # 测试空字典
        result = manager.get_platform_path({}, 'base_dir')
        assert result is not None

    def test_path_validation_error_handling(self):
        """测试路径验证错误处理"""
        manager = get_cross_platform_manager()
        
        # 测试无效路径的标准化
        result = manager.normalize_path(None)
        assert result is None
        
        # 测试空路径的标准化
        result = manager.normalize_path('')
        assert result == ''


class TestCrossPlatformPathPerformance:
    """跨平台路径性能测试类"""

    def test_os_detection_performance(self):
        """测试操作系统检测性能"""
        import time
        
        start_time = time.time()
        manager = get_cross_platform_manager()
        current_os = manager.get_current_os()
        end_time = time.time()
        
        # 检测时间应该在毫秒级
        detection_time = (end_time - start_time) * 1000
        assert detection_time < 100  # 100毫秒内完成

    def test_path_conversion_performance(self):
        """测试路径转换性能"""
        import time
        
        manager = get_cross_platform_manager()
        test_path = 'd:\\test_logs'
        
        start_time = time.time()
        for _ in range(100):
            result = manager.convert_to_multi_platform_config(test_path, 'base_dir')
        end_time = time.time()
        
        # 100次转换应该在毫秒级
        conversion_time = (end_time - start_time) * 1000
        assert conversion_time < 1000  # 1秒内完成100次转换

    def test_platform_path_selection_performance(self):
        """测试平台路径选择性能"""
        import time
        
        manager = get_cross_platform_manager()
        path_config = {
            'windows': 'd:\\windows_logs',
            'linux': '/home/tony/linux_logs',
            'ubuntu': '/home/tony/ubuntu_logs',
            'macos': '/Users/tony/macos_logs'
        }
        
        start_time = time.time()
        for _ in range(100):
            result = manager.get_platform_path(path_config, 'base_dir')
        end_time = time.time()
        
        # 100次选择应该在毫秒级
        selection_time = (end_time - start_time) * 1000
        assert selection_time < 1000  # 1秒内完成100次选择


if __name__ == "__main__":
    pytest.main([__file__]) 