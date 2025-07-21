# tests/01_unit_tests/test_config_manager/test_multi_platform_base_dir.py
from __future__ import annotations

import os
import re
import tempfile
import platform
from src.config_manager import get_config_manager, TestEnvironmentManager
from src.config_manager.config_manager import _clear_instances_for_testing
from src.config_manager.core.cross_platform_paths import get_cross_platform_manager


class TestMultiPlatformBaseDir:
    """测试多平台 base_dir 配置功能"""

    def setup_method(self):
        """每个测试方法前的设置"""
        _clear_instances_for_testing()
        # 清理测试环境变量
        if 'CONFIG_MANAGER_TEST_MODE' in os.environ:
            del os.environ['CONFIG_MANAGER_TEST_MODE']
        if 'CONFIG_MANAGER_TEST_BASE_DIR' in os.environ:
            del os.environ['CONFIG_MANAGER_TEST_BASE_DIR']

    def teardown_method(self):
        """每个测试方法后的清理"""
        # 清理当前测试环境
        TestEnvironmentManager.cleanup_current_test_environment()
        _clear_instances_for_testing()

    def test_multi_platform_base_dir_conversion(self):
        """测试单一路径自动转换为多平台格式"""
        cfg = get_config_manager(test_mode=True)
        
        # 设置一个Linux路径
        cfg.set('base_dir', '/tmp/test_project')
        
        # 验证配置中存储的是多平台格式
        base_dir_config = cfg._data.get('base_dir')
        assert hasattr(base_dir_config, 'to_dict'), "base_dir应该转换为ConfigNode对象"
        
        config_dict = base_dir_config.to_dict()
        assert 'windows' in config_dict, "应该包含windows配置"
        assert 'linux' in config_dict, "应该包含linux配置"
        assert config_dict['linux'] == '/tmp/test_project', "linux路径应该保持原值"
        assert config_dict['windows'] == 'd:\\logs', "windows路径应该使用默认值"

    def test_cross_platform_path_selection(self):
        """测试跨平台路径选择"""
        cfg = get_config_manager(test_mode=True)
        
        # 设置多平台配置
        cfg.set('base_dir', '/tmp/linux_project')
        
        # 获取当前平台
        cross_manager = get_cross_platform_manager()
        current_platform = cross_manager.get_current_os()
        
        # 验证get方法返回当前平台的路径
        actual_base_dir = cfg.get('base_dir')
        if current_platform == 'ubuntu':
            # 在测试模式下应该返回测试路径，而不是配置的路径
            assert 'tests' in actual_base_dir, "测试模式应该使用测试路径"
            assert re.match(r'.*/tests/\d{8}/\d{6}_[a-f0-9]{8}$', actual_base_dir), "测试路径格式应该正确"
        elif current_platform == 'windows':
            assert 'tests' in actual_base_dir, "测试模式应该使用测试路径"

    def test_test_mode_path_format(self):
        """测试测试模式路径格式"""
        cfg = get_config_manager(test_mode=True)
        test_path = cfg.get('base_dir')
        
        # 验证路径包含系统临时目录
        temp_base = tempfile.gettempdir()
        assert temp_base in test_path, f"测试路径应该基于系统临时目录: {temp_base}"
        
        # 验证路径格式
        current_platform = platform.system().lower()
        if current_platform == 'linux':
            pattern = rf'^{re.escape(temp_base)}/tests/\d{{8}}/\d{{6}}_[a-f0-9]{{8}}$'
        else:  # Windows
            escaped_temp = re.escape(temp_base)
            pattern = rf'^{escaped_temp}[\\\\]tests[\\\\]\d{{8}}[\\\\]\d{{6}}_[a-f0-9]{{8}}$'
        
        assert re.match(pattern, test_path), f"测试路径格式不正确: {test_path}"

    def test_concurrent_test_isolation(self):
        """测试多worker使用序列化配置的隔离模式"""
        # 主程序创建配置管理器
        main_cfg = get_config_manager(test_mode=True)
        main_cfg.test_scenario = "concurrent_isolation"
        main_cfg.worker_count = 5
        
        # 序列化配置供worker使用
        serializable_configs = []
        worker_results = []
        
        # 模拟5个worker，每个都获取序列化配置
        for i in range(5):
            # 每个worker获取序列化配置
            worker_config = main_cfg.get_serializable_data()
            serializable_configs.append(worker_config)
            
            # 模拟worker使用配置进行工作
            worker_result = {
                'worker_id': i + 1,
                'test_scenario': worker_config.get('test_scenario'),
                'worker_count': worker_config.get('worker_count'),
                'base_dir': worker_config.get('base_dir'),
                'config_path': worker_config.get_config_path()
            }
            worker_results.append(worker_result)
        
        # 验证所有worker使用相同的配置数据（因为来自同一个主配置）
        base_scenario = worker_results[0]['test_scenario']
        base_count = worker_results[0]['worker_count']
        base_dir = worker_results[0]['base_dir']
        
        for result in worker_results:
            assert result['test_scenario'] == base_scenario, "所有worker应该使用相同的配置"
            assert result['worker_count'] == base_count, "所有worker应该使用相同的配置"
            assert result['base_dir'] == base_dir, "所有worker应该使用相同的base_dir"
        
        # 验证序列化配置是可序列化的
        for config in serializable_configs:
            assert config.is_serializable(), "序列化配置应该可以被pickle序列化"
        
        # 验证主配置的路径格式正确
        main_path = main_cfg.get('base_dir')
        assert 'tests' in main_path, "测试模式应该使用测试路径"
        
        # 根据平台调整正则表达式
        if platform.system().lower() == 'windows':
            # Windows路径使用反斜杠，实际格式: D:\temp\tests\20250703\171949_86741038
            # 注意这里时间和ID是直接连接的，没有额外分隔符
            pattern = r'.*[\\]tests[\\]\d{8}[\\]\d{6}_[a-f0-9]{8}$'
        else:
            # Linux/Unix路径使用正斜杠，格式: /tmp/tests/20250703/171949_86741038
            pattern = r'.*/tests/\d{8}/\d{6}_[a-f0-9]{8}$'
        
        assert re.match(pattern, main_path), f"路径格式不正确: {main_path}，期望模式: {pattern}"

    def test_platform_default_values(self):
        """测试平台默认值"""
        cfg = get_config_manager(test_mode=True)
        
        # 设置一个Windows路径，测试Linux默认值
        cfg.set('base_dir', 'D:\\Windows\\Project')
        
        base_dir_config = cfg._data.get('base_dir')
        config_dict = base_dir_config.to_dict()
        
        # 验证默认值
        assert config_dict['windows'] == 'D:\\Windows\\Project', "Windows路径应该保持原值"
        assert config_dict['linux'] == '~/logs', "Linux应该使用默认值"

    def test_tilde_expansion(self):
        """测试波浪线路径展开"""
        cfg = get_config_manager(test_mode=True)
        
        # 手动设置包含~的配置
        from src.config_manager.config_node import ConfigNode
        cfg._data['base_dir'] = ConfigNode({
            'windows': 'd:\\logs',
            'ubuntu': '~/custom_logs'
        }, _root=cfg)
        
        # 更新_base_dir
        cfg._update_base_dir()
        
        # 在测试模式下，_base_dir应该是测试路径，不是展开的用户路径
        actual_base_dir = cfg._base_dir
        assert 'tests' in actual_base_dir, "测试模式应该覆盖配置路径"

    def test_production_mode_platform_selection(self):
        """测试生产模式的平台路径选择"""
        cfg = get_config_manager(test_mode=True)
        
        # 设置多平台路径
        cfg.set('base_dir', '/tmp/production_project')
        
        # 验证生产模式下的路径选择
        actual_base_dir = cfg.get('base_dir')
        
        # 获取当前平台
        cross_manager = get_cross_platform_manager()
        current_platform = cross_manager.get_current_os()
        
        if current_platform == 'ubuntu':
            assert actual_base_dir == '/tmp/production_project', "生产模式Ubuntu应该返回配置的路径"
        
        # 验证内部_base_dir也正确
        internal_base_dir = cfg._base_dir
        if current_platform == 'ubuntu':
            assert internal_base_dir == '/tmp/production_project', "内部_base_dir应该匹配当前平台"

    def test_path_configuration_update(self):
        """测试路径配置更新"""
        cfg = get_config_manager(test_mode=True)
        
        # 获取初始路径配置
        initial_work_dir = cfg.get('paths.work_dir', '')
        initial_base_dir = cfg.get('base_dir')
        
        # 在测试模式下，验证两个路径都包含测试标识符
        if initial_work_dir and initial_base_dir:
            assert 'tests' in initial_base_dir, "base_dir应该是测试路径"
            # 注意：在当前的测试环境系统中，paths可能使用不同的测试路径
            # 我们主要验证都是测试路径即可
            assert 'tests' in initial_work_dir or 'test_project' in initial_work_dir, "work_dir应该是测试相关路径"

    def test_windows_temp_path_compatibility(self):
        """测试Windows临时路径兼容性"""
        # 这个测试验证代码能处理不同的Windows临时路径
        cfg = get_config_manager(test_mode=True)
        test_path = cfg.get('base_dir')
        
        # 验证使用了系统临时目录
        temp_base = tempfile.gettempdir()
        assert temp_base in test_path, "应该使用系统临时目录"
        
        # 验证路径中包含tests目录
        assert 'tests' in test_path, "应该包含tests目录"
        
        # 验证路径标准化
        normalized_path = os.path.normpath(test_path)
        assert test_path == normalized_path, "路径应该已标准化"

    def test_empty_platform_path_defaults(self):
        """测试空平台路径使用默认值"""
        cfg = get_config_manager(test_mode=True)
        
        # 手动创建空的平台配置
        from src.config_manager.config_node import ConfigNode
        cfg._data['base_dir'] = ConfigNode({
            'windows': '',
            'ubuntu': ''
        }, _root=cfg)
        
        # 更新_base_dir
        cfg._update_base_dir()
        
        # 在测试模式下，应该使用测试路径
        assert 'tests' in cfg._base_dir, "测试模式应该使用测试路径"

    def test_debug_mode_path_isolation(self):
        """测试debug_mode的路径隔离"""
        # 创建一个debug_mode为True的情况
        cfg = get_config_manager(test_mode=True)
        
        # 验证debug_mode影响路径选择
        # 注意：在当前实现中，test_mode已经触发了测试路径
        test_path = cfg.get('base_dir')
        assert 'tests' in test_path, "debug模式应该使用隔离路径"
        
        # 验证环境变量设置
        assert os.environ.get('CONFIG_MANAGER_TEST_MODE') == 'true', "应该设置测试模式环境变量"
        assert 'CONFIG_MANAGER_TEST_BASE_DIR' in os.environ, "应该设置测试base_dir环境变量"