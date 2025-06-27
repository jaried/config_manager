# tests/01_unit_tests/test_config_manager/test_double_load_fix.py
from __future__ import annotations
from datetime import datetime

import tempfile
import os
import sys
import time
import yaml
import pytest

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from config_manager.config_manager import get_config_manager, _clear_instances_for_testing


class TestDoubleLoadFix:
    """测试配置重复加载修复"""

    def test_existing_config_load(self):
        """测试加载已存在的配置文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'existing_config.yaml')
            
            # 创建已存在的配置文件
            existing_config = {
                '__data__': {
                    'app_name': 'TestApp',
                    'version': '1.0.0',
                    'settings': {
                        'debug': True,
                        'timeout': 30
                    }
                },
                '__type_hints__': {}
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(existing_config, f, default_flow_style=False)
            
            # 清理实例
            _clear_instances_for_testing()
            
            # 创建配置管理器
            cfg = get_config_manager(
                config_path=config_file,
                watch=True,
                auto_create=False,
                autosave_delay=0.1
            )
            
            # 验证配置值正确
            assert cfg.app_name == 'TestApp', "app_name应该正确加载"
            assert cfg.version == '1.0.0', "version应该正确加载"
            assert cfg.settings.debug is True, "settings.debug应该正确加载"
            
            # 等待观察是否有重复加载
            time.sleep(2)
            
            # 再次验证配置值仍然正确
            assert cfg.app_name == 'TestApp', "app_name应该保持正确"
            assert cfg.version == '1.0.0', "version应该保持正确"
            assert cfg.settings.debug is True, "settings.debug应该保持正确"

    def test_new_config_creation(self):
        """测试创建新配置文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'new_config.yaml')
            
            # 清理实例
            _clear_instances_for_testing()
            
            # 创建配置管理器
            cfg = get_config_manager(
                config_path=config_file,
                watch=True,
                auto_create=True,
                autosave_delay=0.1,
                first_start_time=datetime.now()
            )
            
            # 设置一些配置
            cfg.test_value = "new_value"
            cfg.nested = {}
            cfg.nested.deep_value = "deep_new_value"
            
            # 验证配置值正确
            assert cfg.test_value == "new_value", "test_value应该正确"
            assert cfg.nested.deep_value == "deep_new_value", "nested.deep_value应该正确"
            
            # 等待观察是否有重复加载
            time.sleep(2)
            
            # 再次验证配置值仍然正确
            assert cfg.test_value == "new_value", "test_value应该保持正确"
            assert cfg.nested.deep_value == "deep_new_value", "nested.deep_value应该保持正确"

    def test_raw_format_conversion(self):
        """测试原始格式转换"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'raw_config.yaml')
            
            # 创建原始格式的配置文件
            raw_config = {
                'app_name': 'RawApp',
                'version': '2.0.0',
                'settings': {
                    'debug': False,
                    'timeout': 60
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(raw_config, f, default_flow_style=False)
            
            # 清理实例
            _clear_instances_for_testing()
            
            # 创建配置管理器
            cfg = get_config_manager(
                config_path=config_file,
                watch=True,
                auto_create=False,
                autosave_delay=0.1
            )
            
            # 验证配置值正确
            assert cfg.app_name == 'RawApp', "app_name应该正确加载"
            assert cfg.version == '2.0.0', "version应该正确加载"
            assert cfg.settings.debug is False, "settings.debug应该正确加载"
            
            # 等待观察是否有重复加载
            time.sleep(2)
            
            # 再次验证配置值仍然正确
            assert cfg.app_name == 'RawApp', "app_name应该保持正确"
            assert cfg.version == '2.0.0', "version应该保持正确"
            assert cfg.settings.debug is False, "settings.debug应该保持正确"

    def test_no_watch_mode(self):
        """测试不启用文件监视的情况"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'no_watch_config.yaml')
            
            # 清理实例
            _clear_instances_for_testing()
            
            # 创建配置管理器，不启用文件监视
            cfg = get_config_manager(
                config_path=config_file,
                watch=False,  # 不启用文件监视
                auto_create=True,
                autosave_delay=0.1
            )
            
            # 设置配置
            cfg.test_value = "no_watch_value"
            
            # 验证配置值正确
            assert cfg.test_value == "no_watch_value", "test_value应该正确"
            
            # 等待观察
            time.sleep(2)
            
            # 再次验证配置值仍然正确
            assert cfg.test_value == "no_watch_value", "test_value应该保持正确"

    def test_initialization_save_logic(self):
        """测试初始化保存逻辑"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'init_save_config.yaml')
            
            # 清理实例
            _clear_instances_for_testing()
            
            # 创建配置管理器，传入first_start_time
            cfg = get_config_manager(
                config_path=config_file,
                watch=True,
                auto_create=True,
                autosave_delay=0.1,
                first_start_time=datetime.now()  # 这会触发初始化保存
            )
            
            # 验证first_start_time被正确设置
            assert hasattr(cfg, 'first_start_time'), "first_start_time应该存在"
            assert cfg.first_start_time is not None, "first_start_time不应该为None"
            
            # 等待观察
            time.sleep(2)
            
            # 验证配置仍然正确
            assert hasattr(cfg, 'first_start_time'), "first_start_time应该仍然存在"
            assert cfg.first_start_time is not None, "first_start_time不应该变为None" 