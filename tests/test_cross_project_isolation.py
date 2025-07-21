# tests/test_cross_project_isolation.py
from __future__ import annotations

import os
import tempfile

from config_manager import get_config_manager


class TestCrossProjectIsolation:
    """测试跨项目配置隔离"""

    def test_different_config_paths_create_separate_instances(self):
        """测试不同配置路径创建独立实例"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建两个不同的配置文件路径
            config_path_a = os.path.join(temp_dir, "project_a", "config.yaml")
            config_path_b = os.path.join(temp_dir, "project_b", "config.yaml")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path_a), exist_ok=True)
            os.makedirs(os.path.dirname(config_path_b), exist_ok=True)
            
            # 创建两个配置管理器实例
            config_a = get_config_manager(config_path=config_path_a, auto_create=True, test_mode=True)
            config_b = get_config_manager(config_path=config_path_b, auto_create=True, test_mode=True)
            
            # 验证它们是不同的实例
            assert config_a is not config_b, "不同配置路径应该创建不同的实例"
            
            # 设置不同的配置值
            config_a.project_name = "project_a"
            config_a.unique_value_a = "value_from_a"
            
            config_b.project_name = "project_b"
            config_b.unique_value_b = "value_from_b"
            
            # 验证配置隔离
            assert config_a.project_name == "project_a"
            assert config_b.project_name == "project_b"
            
            # 验证一个项目的配置不会影响另一个项目
            assert hasattr(config_a, 'unique_value_a')
            assert not hasattr(config_a, 'unique_value_b')
            
            assert hasattr(config_b, 'unique_value_b')
            assert not hasattr(config_b, 'unique_value_a')

    def test_same_config_path_reuses_instance(self):
        """测试相同配置路径复用实例"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "shared", "config.yaml")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # 创建两个使用相同路径的配置管理器
            config_1 = get_config_manager(config_path=config_path, auto_create=True, test_mode=True)
            config_2 = get_config_manager(config_path=config_path, auto_create=True, test_mode=True)
            
            # 验证它们是同一个实例
            assert config_1 is config_2, "相同配置路径应该复用实例"

    def test_production_cache_key_generation(self):
        """测试生产模式缓存键生成"""
        from config_manager.config_manager import ConfigManager
        
        # 测试显式路径
        cache_key_1 = ConfigManager._generate_production_cache_key("/path/to/config.yaml")
        cache_key_2 = ConfigManager._generate_production_cache_key("/path/to/config.yaml")
        cache_key_3 = ConfigManager._generate_production_cache_key("/different/path/config.yaml")
        
        # 相同路径应该生成相同缓存键
        assert cache_key_1 == cache_key_2
        
        # 不同路径应该生成不同缓存键
        assert cache_key_1 != cache_key_3
        
        # 测试None路径（默认路径）
        cache_key_none_1 = ConfigManager._generate_production_cache_key(None)
        cache_key_none_2 = ConfigManager._generate_production_cache_key(None)
        
        # 相同的None应该生成相同缓存键
        assert cache_key_none_1 == cache_key_none_2

    def test_prevent_cross_project_pollution(self):
        """测试防止跨项目配置污染"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 模拟bakamh项目配置
            bakamh_config_path = os.path.join(temp_dir, "bakamh", "config.yaml")
            os.makedirs(os.path.dirname(bakamh_config_path), exist_ok=True)
            
            # 模拟alpha_backtrader项目配置
            alpha_config_path = os.path.join(temp_dir, "alpha_backtrader", "config.yaml")
            os.makedirs(os.path.dirname(alpha_config_path), exist_ok=True)
            
            # 创建bakamh配置
            bakamh_config = get_config_manager(config_path=bakamh_config_path, auto_create=True, test_mode=True)
            bakamh_config.project_name = "bakamh"
            bakamh_config.titls = ["manga1", "manga2"]  # 模拟漫画标题
            bakamh_config.camoufox = {"intelligent_mode": True}  # 模拟浏览器配置
            
            # 创建alpha_backtrader配置
            alpha_config = get_config_manager(config_path=alpha_config_path, auto_create=True, test_mode=True)
            alpha_config.project_name = "alpha_backtrader"
            alpha_config.strategy_name = "test_strategy"
            
            # 验证配置完全隔离
            assert bakamh_config.project_name == "bakamh"
            assert alpha_config.project_name == "alpha_backtrader"
            
            # 验证bakamh的特定配置不会污染alpha_backtrader
            assert hasattr(bakamh_config, 'titls')
            assert hasattr(bakamh_config, 'camoufox')
            assert not hasattr(alpha_config, 'titls'), "alpha_backtrader不应该有bakamh的titls配置"
            assert not hasattr(alpha_config, 'camoufox'), "alpha_backtrader不应该有bakamh的camoufox配置"
            
            # 验证alpha_backtrader的配置不会污染bakamh
            assert hasattr(alpha_config, 'strategy_name')
            assert not hasattr(bakamh_config, 'strategy_name'), "bakamh不应该有alpha_backtrader的strategy_name配置"