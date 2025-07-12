from __future__ import annotations
from datetime import datetime
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from src.config_manager.config_manager import ConfigManager, _clear_instances_for_testing, get_config_manager



class TestTC0012006ProtectedFields:
    """测试配置字段保护功能，确保特殊字段不被路径替换"""

    def setup_method(self):
        """每个测试方法执行前的清理"""
        _clear_instances_for_testing()

    def teardown_method(self):
        """每个测试方法执行后的清理"""
        _clear_instances_for_testing()

    def _create_mock_config(self) -> dict:
        """创建标准化的Mock配置对象"""
        return {
            'project_name': "test_project",
            'first_start_time': datetime(2025, 1, 7, 18, 15, 20).isoformat(),
            'test_mode': True,
            'concurrency': 5,
            'timeout': 30,
            
            # 网络相关配置
            'proxy': {
                'http': "http://localhost:3213",
                'https': "https://localhost:3214",
                'url': "http://proxy.example.com:8080"
            },
            
            # HTTP Headers
            'headers': {
                'Accept': "text/html,application/xhtml+xml",
                'Content_Type': "application/json"
            },
            
            # 正则表达式
            'url_validation': {
                'level2_pattern': r"^https?://[^/]+/chapter/\d+$",
                'exclude_image_patterns': [
                    r"\.jpg$", r"\.png$", r"\.gif$"
                ]
            },
            
            # 真正的路径字段  
            'base_dir': "/tmp/original/base/path",
            'work_dir': "/tmp/original/work/path",
            'log_dir': "/tmp/original/log/path"
        }

    @patch('ruamel.yaml.YAML')
    @patch('src.config_manager.core.file_operations.FileOperations.load_config')
    def test_tc0012_006_001_network_urls_not_replaced(self, mock_load_config, mock_yaml):
        """测试网络URL不被路径替换"""
        # 准备
        mock_config = self._create_mock_config()
        mock_load_config.return_value = {'__data__': mock_config, '__type_hints__': {}}
        
        mock_yaml_instance = MagicMock()
        mock_yaml.return_value = mock_yaml_instance
        
        # 执行
        with tempfile.TemporaryDirectory():
            config_manager = ConfigManager(test_mode=True)
            
            # 验证网络URL没有被替换
            assert config_manager.proxy.http == "http://localhost:3213"
            assert config_manager.proxy.https == "https://localhost:3214"
            assert config_manager.proxy.url == "http://proxy.example.com:8080"

    @patch('ruamel.yaml.YAML')
    @patch('src.config_manager.core.file_operations.FileOperations.load_config')
    def test_tc0012_006_002_http_headers_not_replaced(self, mock_load_config, mock_yaml):
        """测试HTTP Headers不被路径替换"""
        # 准备
        mock_config = self._create_mock_config()
        mock_load_config.return_value = {'__data__': mock_config, '__type_hints__': {}}
        
        mock_yaml_instance = MagicMock()
        mock_yaml.return_value = mock_yaml_instance
        
        # 执行
        with tempfile.TemporaryDirectory():
            config_manager = ConfigManager(test_mode=True)
            
            # 验证HTTP Headers没有被替换
            assert config_manager.headers.Accept == "text/html,application/xhtml+xml"
            assert config_manager.headers.Content_Type == "application/json"

    @patch('ruamel.yaml.YAML')
    @patch('src.config_manager.core.file_operations.FileOperations.load_config')
    def test_tc0012_006_003_regex_patterns_not_replaced(self, mock_load_config, mock_yaml):
        """测试正则表达式模式不被路径替换"""
        # 准备
        mock_config = self._create_mock_config()
        mock_load_config.return_value = {'__data__': mock_config, '__type_hints__': {}}
        
        mock_yaml_instance = MagicMock()
        mock_yaml.return_value = mock_yaml_instance
        
        # 执行
        with tempfile.TemporaryDirectory():
            config_manager = ConfigManager(test_mode=True)
            
            # 验证正则表达式没有被替换
            assert config_manager.url_validation.level2_pattern == r"^https?://[^/]+/chapter/\d+$"
            assert config_manager.url_validation.exclude_image_patterns == [
                r"\.jpg$", r"\.png$", r"\.gif$"
            ]

    def test_tc0012_006_004_real_paths_are_replaced(self):
        """测试真正的文件路径被正确替换"""
        # 创建真实的配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""__data__:
  project_name: test_project
  first_start_time: "2025-01-07T18:15:20"
  base_dir: "/tmp/original/base/path"
  work_dir: "/tmp/original/work/path"
  log_dir: "/tmp/original/log/path"
  proxy:
    http: "http://localhost:3213"
    https: "https://localhost:3214"
__type_hints__: {}
""")
            config_file = f.name

        try:
            # 执行 - 使用get_config_manager函数确保test_mode逻辑被正确调用
            config_manager = get_config_manager(config_path=config_file, test_mode=True)
            
            # 根据任务6，test_mode现在只修改base_dir
            # 验证base_dir确实被替换了（不等于原始值）
            assert config_manager.base_dir != "/tmp/original/base/path", f"base_dir应该被替换，但仍然是: {config_manager.base_dir}"
            
            # 验证替换后的路径包含测试环境路径
            # 标准化路径格式进行比较，处理Windows路径的反斜杠和正斜杠混合问题
            normalized_base_dir = str(config_manager.base_dir).replace('\\', '/').replace('//', '/')
            
            # 检查路径包含测试环境特征
            assert 'temp' in normalized_base_dir.lower() or 'tmp' in normalized_base_dir.lower(), f"base_dir应该包含temp或tmp: {normalized_base_dir}"
            assert 'tests' in normalized_base_dir, f"base_dir应该包含tests: {normalized_base_dir}"
            
            # work_dir会因为向后兼容性自动同步paths.work_dir，所以会被测试模式替换
            # 验证work_dir被替换到测试环境
            assert config_manager.work_dir != "/tmp/original/work/path", f"work_dir应该因向后兼容而被替换，但仍然是: {config_manager.work_dir}"
            assert 'tests' in config_manager.work_dir, f"work_dir应该包含tests路径: {config_manager.work_dir}"
            
            # log_dir不被test_mode自动替换，保持原值
            assert config_manager.log_dir == "/tmp/original/log/path"
            
            # 验证网络URL没有被替换
            assert config_manager.proxy.http == "http://localhost:3213"
            assert config_manager.proxy.https == "https://localhost:3214"
            
        finally:
            assert config_file.startswith(tempfile.gettempdir()), f"禁止删除非临时文件: {config_file}"
            os.unlink(config_file)

    def test_tc0012_006_005_is_protected_field_network(self):
        """测试网络相关字段保护识别"""
        pytest.skip("_is_protected_field方法已被移除（任务6：简化test_mode逻辑）")

    def test_tc0012_006_006_is_protected_field_headers(self):
        """测试HTTP Headers字段保护识别"""
        pytest.skip("_is_protected_field方法已被移除（任务6：简化test_mode逻辑）")

    def test_tc0012_006_007_is_protected_field_regex(self):
        """测试正则表达式字段保护识别"""
        pytest.skip("_is_protected_field方法已被移除（任务6：简化test_mode逻辑）")

    def test_tc0012_006_008_is_path_like_excludes_urls(self):
        """测试路径识别排除URL"""
        pytest.skip("_is_path_like方法已被移除（任务6：简化test_mode逻辑）")

    def test_tc0012_006_009_complex_config_protection(self):
        """测试复杂配置结构中的字段保护"""
        # 确保开始时清理所有实例
        _clear_instances_for_testing()
        
        # 使用tempfile.mkstemp创建临时文件，避免文件句柄问题
        import tempfile
        import os
        
        fd, config_file = tempfile.mkstemp(suffix='.yaml', text=True)
        try:
            # 写入配置内容
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write("""__data__:
  project_name: test_project
  first_start_time: "2025-01-07T18:15:20"
  network:
    proxy_url: "http://proxy.company.com:8080"
    log_dir: "/var/log/network"
  validation:
    url_pattern: "^https://[^/]+/api/v\\\\d+/"
    config_file: "/etc/validation/rules.yaml"
  headers:
    User_Agent: "Mozilla/5.0 (compatible; Bot/1.0)"
    log_path: "/tmp/headers.log"
__type_hints__: {}
""")
            
            # 执行前再次清理，确保获得全新的实例
            _clear_instances_for_testing()
            config_manager = ConfigManager(config_path=config_file, test_mode=True)
            
            # 验证保护的字段没有被替换
            assert config_manager.network.proxy_url == "http://proxy.company.com:8080"
            assert config_manager.validation.url_pattern == r"^https://[^/]+/api/v\d+/"
            assert config_manager.headers.User_Agent == "Mozilla/5.0 (compatible; Bot/1.0)"
            
            # 根据任务6，test_mode现在只修改base_dir，其他路径不再自动替换
            assert config_manager.network.log_dir == "/var/log/network"
            assert config_manager.validation.config_file == "/etc/validation/rules.yaml"
            assert config_manager.headers.log_path == "/tmp/headers.log"
            
        finally:
            # 清理临时文件
            if os.path.exists(config_file):
                assert config_file.startswith(tempfile.gettempdir()), f"禁止删除非临时文件: {config_file}"
                os.unlink(config_file)
            # 清理ConfigManager实例
            _clear_instances_for_testing() 