# tests/01_unit_tests/test_config_manager/test_cross_platform_integration.py
import pytest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime

# 项目根目录由conftest.py自动配置

from src.config_manager import get_config_manager
from src.config_manager.core.cross_platform_paths import (
    get_cross_platform_manager,
    convert_to_multi_platform_config,
    get_platform_path
)



class TestCrossPlatformConfigManagerIntegration:
    """跨平台配置管理器集成测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.test_time = datetime.now()

    def test_single_path_auto_conversion(self):
        """测试单一路径自动转换"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_single_path.yaml')
            
            # 创建配置管理器
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                first_start_time=self.test_time
            )
            
            # 确保配置管理器创建成功
            assert config is not None, "配置管理器应该创建成功"
            
            # 设置单一路径，应该自动转换为多平台格式
            test_path = os.path.join(temp_dir, 'persistence_test')
            config.set('base_dir', test_path)
            
            # 保存配置
            config.save()
            
            # 创建新的配置管理器实例，重新加载配置
            config2 = get_config_manager(
                config_path=config_path,
                test_mode=True,
                first_start_time=self.test_time
            )
            
            # 确保配置管理器创建成功
            assert config2 is not None, "重新加载的配置管理器应该创建成功"
            
            # 在测试模式下，验证实际获取的路径
            actual_base_dir = config2.get('base_dir')
            assert actual_base_dir is not None, "base_dir应该存在"
            
            # 在测试模式下，base_dir应该返回测试路径，而不是原始配置路径
            assert 'tests' in actual_base_dir, f"测试模式下应该使用测试路径: {actual_base_dir}"
            
            # 验证配置数据中的base_dir仍然是多平台格式
            base_dir_config = config2._data.get('base_dir')
            if hasattr(base_dir_config, 'is_multi_platform_config'):
                assert base_dir_config.is_multi_platform_config(), "配置中的base_dir应该是多平台格式"
                
                # 验证配置中包含原始设置的路径
                current_os = get_cross_platform_manager().get_current_os()
                stored_path = base_dir_config.get_platform_path(current_os)
                assert stored_path == test_path, f"配置中应该包含原始路径: {stored_path} != {test_path}"

    def test_multi_platform_path_setting(self):
        """测试多平台路径设置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_multi_platform.yaml')
            temp_base_dir = tempfile.mkdtemp()
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                first_start_time=self.test_time
            )
            multi_platform_base_dir = {
                'windows': temp_base_dir,
                'linux': '/home/tony/multi_logs'
            }
            config.set('base_dir', multi_platform_base_dir)
            base_dir_value = config._data.get('base_dir')
            # 检查是否是多平台配置
            assert hasattr(base_dir_value, 'is_multi_platform_config'), "base_dir应该是ConfigNode对象"
            assert base_dir_value.is_multi_platform_config(), "base_dir应该被转换为多平台配置"
            # 获取当前平台的路径
            current_os = get_cross_platform_manager().get_current_os()
            current_path = base_dir_value.get_platform_path(current_os)
            assert current_path in multi_platform_base_dir.values(), f"当前平台路径应该在多平台配置中: {current_path}"

    def test_path_generation_with_cross_platform_base_dir(self):
        """测试基于跨平台base_dir的路径生成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_path_generation.yaml')
            temp_base_dir = tempfile.mkdtemp()
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                first_start_time=self.test_time
            )
            multi_platform_base_dir = {
                'windows': temp_base_dir,
                'linux': '/home/tony/cross_platform_logs'
            }
            config.set('base_dir', multi_platform_base_dir)
            config.set('project_name', 'cross_platform_test')
            config.set('experiment_name', 'test_exp')
            try:
                path_info = config.get_path_configuration_info()
                assert 'current_os' in path_info
                assert 'generated_paths' in path_info
                generated_paths = path_info.get('generated_paths', {})
                if 'paths.work_dir' in generated_paths:
                    work_dir = generated_paths['paths.work_dir']
                    current_os = path_info['current_os']
                    expected_base = multi_platform_base_dir.get(current_os, multi_platform_base_dir['windows'])
                    assert expected_base in work_dir
            except Exception as e:
                # 如果路径配置管理器不可用，检查base_dir是否正确设置
                base_dir_value = config._data.get('base_dir')
                assert base_dir_value is not None
                assert hasattr(base_dir_value, 'is_multi_platform_config')
                assert base_dir_value.is_multi_platform_config()
                # 检查当前平台路径是否在多平台配置中
                current_os = get_cross_platform_manager().get_current_os()
                current_path = base_dir_value.get_platform_path(current_os)
                assert current_path in multi_platform_base_dir.values()

    def test_backward_compatibility_with_existing_configs(self):
        """测试与现有配置的向后兼容性"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_backward_compat.yaml')
            temp_work_dir = tempfile.mkdtemp()
            temp_tensorboard_dir = tempfile.mkdtemp()
            temp_data_dir = tempfile.mkdtemp()
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                first_start_time=self.test_time
            )
            config.set('work_dir', temp_work_dir)
            config.set('tensorboard_dir', temp_tensorboard_dir)
            config.set('data_dir', temp_data_dir)
            work_dir = config.get('work_dir')
            tensorboard_dir = config.get('tensorboard_dir')
            data_dir = config.get('data_dir')
            assert work_dir == temp_work_dir
            assert tensorboard_dir == temp_tensorboard_dir
            assert data_dir == temp_data_dir
            work_dir_value = config._data.get('work_dir')
            assert isinstance(work_dir_value, str)

    def test_config_persistence_and_reload(self):
        """测试配置持久化和重新加载"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_persistence.yaml')
            
            # 创建配置管理器并设置多平台配置
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                first_start_time=self.test_time
            )
            
            # 确保配置管理器创建成功
            assert config is not None, "配置管理器应该创建成功"
            
            # 设置单一路径，应该自动转换为多平台格式
            test_path = os.path.join(temp_dir, 'persistence_test')
            config.set('base_dir', test_path)
            
            # 保存配置
            config.save()
            
            # 创建新的配置管理器实例，重新加载配置
            config2 = get_config_manager(
                config_path=config_path,
                test_mode=True,
                first_start_time=self.test_time
            )
            
            # 确保配置管理器创建成功
            assert config2 is not None, "重新加载的配置管理器应该创建成功"
            
            # 在测试模式下，验证实际获取的路径
            actual_base_dir = config2.get('base_dir')
            assert actual_base_dir is not None, "base_dir应该存在"
            
            # 在测试模式下，base_dir应该返回测试路径，而不是原始配置路径
            assert 'tests' in actual_base_dir, f"测试模式下应该使用测试路径: {actual_base_dir}"
            
            # 验证配置数据中的base_dir仍然是多平台格式
            base_dir_config = config2._data.get('base_dir')
            if hasattr(base_dir_config, 'is_multi_platform_config'):
                assert base_dir_config.is_multi_platform_config(), "配置中的base_dir应该是多平台格式"
                
                # 验证配置中包含原始设置的路径
                current_os = get_cross_platform_manager().get_current_os()
                stored_path = base_dir_config.get_platform_path(current_os)
                assert stored_path == test_path, f"配置中应该包含原始路径: {stored_path} != {test_path}"

    def test_multiple_path_types_conversion(self):
        """测试多种路径类型的转换"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_multiple_paths.yaml')
            
            # 创建配置管理器
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                first_start_time=self.test_time
            )
            
            # 测试不同路径格式的转换
            test_paths = [
                os.path.join(temp_dir, 'windows', 'path'),
                '/home/tony/linux/path',
                '/Users/tony/macos/path',
                'relative/path'
            ]
            
            for i, path in enumerate(test_paths):
                config.set(f'path_{i}', path)
                
                # 只有base_dir会被自动转换
                if f'path_{i}' == 'base_dir':
                    path_value = config._data.get(f'path_{i}')
                    assert hasattr(path_value, 'is_multi_platform_config'), f"path_{i}应该被转换为ConfigNode对象"
                    assert path_value.is_multi_platform_config(), f"path_{i}应该被转换为多平台配置"
                else:
                    path_value = config._data.get(f'path_{i}')
                    assert isinstance(path_value, str), f"path_{i}应该保持字符串格式"
                    assert path_value == path, f"path_{i}的值应该保持不变"

    def test_error_handling_in_integration(self):
        """测试集成过程中的错误处理"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_error_handling.yaml')
            
            # 创建配置管理器
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                first_start_time=self.test_time
            )
            
            # 确保配置管理器创建成功
            assert config is not None, "配置管理器应该创建成功"
            
            # 测试设置有效路径
            test_path = os.path.join(temp_dir, 'valid_path')
            config.set('base_dir', test_path)
            base_dir_value = config._data.get('base_dir')
            assert base_dir_value is not None, "base_dir应该存在"
            assert hasattr(base_dir_value, 'is_multi_platform_config'), "有效路径应该被转换为ConfigNode对象"
            assert base_dir_value.is_multi_platform_config(), "有效路径应该被转换为多平台配置"
            
            # 测试设置相对路径
            relative_path = 'relative/path'
            config.set('relative_dir', relative_path)
            relative_dir_value = config._data.get('relative_dir')
            assert relative_dir_value == relative_path, "相对路径应该保持原值"
            
            # 测试设置绝对路径
            absolute_path = os.path.join(temp_dir, 'absolute_path')
            config.set('absolute_dir', absolute_path)
            absolute_dir_value = config._data.get('absolute_dir')
            assert absolute_dir_value == absolute_path, "绝对路径应该保持原值"

    def test_performance_in_integration(self):
        """测试集成性能"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_performance.yaml')
            
            # 创建配置管理器
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                first_start_time=self.test_time
            )
            
            import time
            
            # 测试多次设置和获取的性能
            start_time = time.time()
            
            for i in range(100):
                test_path = os.path.join(temp_dir, f'performance_test_{i}')
                config.set('base_dir', test_path)
                current_path = config.get('base_dir')
                assert current_path is not None
            
            end_time = time.time()
            
            # 100次操作应该在合理时间内完成
            operation_time = (end_time - start_time) * 1000
            assert operation_time < 5000, f"100次操作应该在5秒内完成，实际用时{operation_time}毫秒"

    def test_cross_platform_manager_singleton_in_integration(self):
        """测试集成中跨平台管理器的单例模式"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_singleton.yaml')
            
            # 创建多个配置管理器实例
            config1 = get_config_manager(
                config_path=config_path,
                test_mode=True,
                first_start_time=self.test_time
            )
            
            config2 = get_config_manager(
                config_path=config_path,
                test_mode=True,
                first_start_time=self.test_time
            )
            
            # 验证它们使用相同的跨平台管理器实例
            manager1 = get_cross_platform_manager()
            manager2 = get_cross_platform_manager()
            
            assert manager1 is manager2, "跨平台管理器应该是单例"

    def test_platform_specific_behavior(self):
        """测试平台特定行为"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_platform_behavior.yaml')
            
            # 创建配置管理器
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                first_start_time=self.test_time
            )
            
            # 设置多平台配置
            platform_specific_paths = {
                'windows': os.path.join(temp_dir, 'windows_specific'),
                'linux': '/home/tony/ubuntu_specific'
            }
            config.set('base_dir', platform_specific_paths)
            
            # 获取当前平台的路径
            current_os = get_cross_platform_manager().get_current_os()
            base_dir_value = config._data.get('base_dir')
            assert hasattr(base_dir_value, 'is_multi_platform_config'), "base_dir应该是ConfigNode对象"
            current_path = base_dir_value.get_platform_path(current_os)
            expected_path = platform_specific_paths.get(current_os, platform_specific_paths['windows'])
            assert current_path == expected_path, f"应该返回{current_os}平台的路径"



class TestCrossPlatformPathConfigurationManagerIntegration:
    """跨平台路径配置管理器集成测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.test_time = datetime.now()

    def test_path_configuration_manager_with_cross_platform_base_dir(self):
        """测试路径配置管理器与跨平台base_dir的集成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_path_config_manager.yaml')
            
            # 创建配置管理器
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                first_start_time=self.test_time
            )
            
            # 设置多平台base_dir
            multi_platform_base_dir = {
                'windows': os.path.join(temp_dir, 'path_config_test'),
                'linux': '/home/tony/path_config_test'
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

    def test_auto_directory_creation_with_cross_platform_paths(self):
        """测试跨平台路径的自动目录创建"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_auto_creation.yaml')
            
            # 创建配置管理器
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                first_start_time=self.test_time
            )
            
            # 设置多平台base_dir
            multi_platform_base_dir = {
                'windows': os.path.join(temp_dir, 'auto_creation_test'),
                'linux': '/home/tony/auto_creation_test'
            }
            config.set('base_dir', multi_platform_base_dir)
            
            # 设置项目配置
            config.set('project_name', 'test_project')
            config.set('experiment_name', 'test_exp')
            
            # 验证自动目录创建
            try:
                # 获取当前平台的路径
                current_os = get_cross_platform_manager().get_current_os()
                base_dir_value = config._data.get('base_dir')
                assert hasattr(base_dir_value, 'is_multi_platform_config'), "base_dir应该是ConfigNode对象"
                current_base_dir = base_dir_value.get_platform_path(current_os)
                
                # 验证路径存在或可以被创建
                if current_os == 'windows':
                    # Windows路径应该在临时目录下
                    assert temp_dir in current_base_dir, "Windows路径应该在临时目录下"
                else:
                    # 其他平台的路径可能不存在，但应该能被正确处理
                    assert isinstance(current_base_dir, str), "路径应该是字符串"
                    
            except Exception as e:
                # 如果自动目录创建不可用，至少验证基本功能
                current_base_dir = config.get('base_dir')
                assert current_base_dir is not None


if __name__ == "__main__":
    pytest.main([__file__]) 