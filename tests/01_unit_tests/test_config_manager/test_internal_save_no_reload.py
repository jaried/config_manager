# tests/01_unit_tests/test_config_manager/test_internal_save_no_reload.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch

from src.config_manager import get_config_manager, _clear_instances_for_testing


class TestInternalSaveNoReload:
    """测试内部保存不会触发重新加载功能"""
    
    def setup_method(self):
        """测试前设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_time = datetime(2025, 1, 8, 10, 30, 0)
        # 清理实例
        _clear_instances_for_testing()
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_internal_save_no_reload(self):
        """测试内部保存不会触发重新加载"""
        config_file = os.path.join(self.temp_dir, 'test_internal_save.yaml')
        
        # 创建配置管理器，启用文件监视
        cfg = get_config_manager(
            config_path=config_file,
            watch=True,  # 启用文件监视
            autosave_delay=0.1
        )
        
        # 设置初始配置
        cfg.test_value = "initial_value"
        cfg.nested = {}
        cfg.nested.deep_value = "deep_initial"
        
        # 等待自动保存
        time.sleep(0.5)
        
        # 手动保存
        saved = cfg.save()
        assert saved is True, "保存应该成功"
        
        # 等待一段时间，观察是否触发重新加载
        time.sleep(1.0)
        
        # 验证配置值仍然正确
        current_value = cfg.test_value
        current_nested = cfg.nested.deep_value
        
        assert current_value == "initial_value", "test_value应该保持不变"
        assert current_nested == "deep_initial", "nested.deep_value应该保持不变"
    
    def test_external_file_change_triggers_reload(self):
        """测试外部文件修改会触发重新加载"""
        config_file = os.path.join(self.temp_dir, 'test_external_change.yaml')
        
        # 创建配置管理器，启用文件监视
        cfg = get_config_manager(
            config_path=config_file,
            watch=True,  # 启用文件监视
            autosave_delay=0.1
        )
        
        # 设置初始配置
        cfg.test_value = "initial_value"
        cfg.nested = {}
        cfg.nested.deep_value = "deep_initial"
        
        # 等待自动保存和文件监视器启动
        time.sleep(1.0)
        
        # 记录文件监视器的当前修改时间
        if cfg._watcher:
            watcher_last_mtime = cfg._watcher._last_mtime
            print(f"文件监视器记录的修改时间: {watcher_last_mtime}")
        
        # 记录修改前的文件时间
        initial_mtime = os.path.getmtime(config_file)
        print(f"修改前文件时间: {initial_mtime}")
        
        # 确保文件时间比监视器记录的时间更新
        if cfg._watcher and initial_mtime <= watcher_last_mtime:
            print("等待文件时间更新...")
            time.sleep(1.0)
            initial_mtime = os.path.getmtime(config_file)
            print(f"更新后文件时间: {initial_mtime}")
        
        # 外部修改文件
        external_config = """__data__:
  test_value: external_modified_value
  nested:
    deep_value: external_deep_modified
  external_change: true
__type_hints__: {}"""

        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(external_config)
        
        # 记录修改后的文件时间
        updated_mtime = os.path.getmtime(config_file)
        print(f"修改后文件时间: {updated_mtime}")
        print(f"文件时间变化: {updated_mtime - initial_mtime}")
        
        # 等待文件监视器检测到变化（增加等待时间）
        print("等待文件监视器检测外部变化...")
        time.sleep(3.0)  # 增加等待时间
        
        # 验证外部修改是否被检测到
        updated_value = cfg.test_value
        updated_nested = cfg.nested.deep_value
        external_change = cfg.get('external_change', False)
        
        print(f"检测到的 test_value: {updated_value}")
        print(f"检测到的 nested.deep_value: {updated_nested}")
        print(f"检测到的 external_change: {external_change}")
        
        assert updated_value == "external_modified_value", "外部修改的test_value应该被检测到"
        assert updated_nested == "external_deep_modified", "外部修改的nested.deep_value应该被检测到"
        assert external_change is True, "外部添加的external_change应该被检测到"
    
    def test_autosave_no_reload(self):
        """测试自动保存不会触发重新加载"""
        config_file = os.path.join(self.temp_dir, 'test_autosave.yaml')
        
        # 创建配置管理器，启用文件监视和自动保存
        cfg = get_config_manager(
            config_path=config_file,
            watch=True,  # 启用文件监视
            autosave_delay=0.1  # 快速自动保存
        )
        
        # 设置初始配置
        cfg.autosave_test = "autosave_initial"
        cfg.nested = {}
        cfg.nested.autosave_deep = "autosave_deep_initial"
        
        # 等待自动保存
        time.sleep(0.5)
        
        # 再次修改配置
        cfg.autosave_test = "autosave_modified"
        cfg.nested.autosave_deep = "autosave_deep_modified"
        
        # 等待自动保存
        time.sleep(0.5)
        
        # 验证配置值正确
        current_value = cfg.autosave_test
        current_nested = cfg.nested.autosave_deep
        
        assert current_value == "autosave_modified", "自动保存后的值应该正确"
        assert current_nested == "autosave_deep_modified", "自动保存后的嵌套值应该正确"
    
    def test_multiple_saves_no_reload(self):
        """测试多次保存不会触发重新加载"""
        config_file = os.path.join(self.temp_dir, 'test_multiple_saves.yaml')
        
        # 创建配置管理器，启用文件监视
        cfg = get_config_manager(
            config_path=config_file,
            watch=True,  # 启用文件监视
            autosave_delay=0.1
        )
        
        # 设置初始配置
        cfg.multiple_test = "value_1"
        
        # 多次保存
        for i in range(3):
            cfg.multiple_test = f"value_{i+1}"
            saved = cfg.save()
            assert saved is True, f"第{i+1}次保存应该成功"
            time.sleep(0.2)  # 短暂等待
        
        # 验证最终值正确
        final_value = cfg.multiple_test
        assert final_value == "value_3", "多次保存后的最终值应该正确"
    
    def test_file_watcher_internal_flag(self):
        """测试文件监视器的内部保存标志机制"""
        config_file = os.path.join(self.temp_dir, 'test_watcher_flag.yaml')
        
        # 创建配置管理器，启用文件监视
        cfg = get_config_manager(
            config_path=config_file,
            watch=True,  # 启用文件监视
            autosave_delay=0.1
        )
        
        # 验证文件监视器存在
        assert cfg._watcher is not None, "文件监视器应该存在"
        
        # 验证内部保存标志方法存在
        assert hasattr(cfg._watcher, 'set_internal_save_flag'), "文件监视器应该有set_internal_save_flag方法"
        
        # 测试设置标志
        cfg._watcher.set_internal_save_flag(True)
        assert cfg._watcher._internal_save_flag is True, "内部保存标志应该被正确设置"
        
        cfg._watcher.set_internal_save_flag(False)
        assert cfg._watcher._internal_save_flag is False, "内部保存标志应该被正确重置"
    
    def test_save_without_watcher(self):
        """测试没有文件监视器时的保存行为"""
        config_file = os.path.join(self.temp_dir, 'test_no_watcher.yaml')
        
        # 创建配置管理器，禁用文件监视
        cfg = get_config_manager(
            config_path=config_file,
            watch=False,  # 禁用文件监视
            autosave_delay=0.1
        )
        
        # 验证文件监视器不存在
        assert cfg._watcher is None, "文件监视器应该不存在"
        
        # 设置配置并保存
        cfg.no_watcher_test = "no_watcher_value"
        saved = cfg.save()
        assert saved is True, "没有文件监视器时保存应该成功"
        
        # 验证配置值正确
        current_value = cfg.no_watcher_test
        assert current_value == "no_watcher_value", "没有文件监视器时的配置值应该正确"
    
    def test_concurrent_save_and_watch(self):
        """测试并发保存和监视的情况"""
        config_file = os.path.join(self.temp_dir, 'test_concurrent.yaml')
        
        # 创建配置管理器，启用文件监视
        cfg = get_config_manager(
            config_path=config_file,
            watch=True,  # 启用文件监视
            autosave_delay=0.05  # 快速自动保存
        )
        
        # 快速连续修改配置
        for i in range(5):
            cfg.concurrent_test = f"concurrent_value_{i+1}"
            time.sleep(0.1)  # 短暂等待
        
        # 等待所有自动保存完成
        time.sleep(0.5)
        
        # 验证最终值正确
        final_value = cfg.concurrent_test
        assert final_value == "concurrent_value_5", "并发保存后的最终值应该正确"
    
    def test_file_modification_timing(self):
        """测试文件修改时间检测的准确性"""
        config_file = os.path.join(self.temp_dir, 'test_timing.yaml')
        
        # 创建配置管理器，启用文件监视
        cfg = get_config_manager(
            config_path=config_file,
            watch=True,  # 启用文件监视
            autosave_delay=0.1
        )
        
        # 记录初始修改时间
        initial_mtime = os.path.getmtime(config_file)
        
        # 保存配置
        cfg.timing_test = "timing_value"
        saved = cfg.save()
        assert saved is True, "保存应该成功"
        
        # 验证文件修改时间已更新
        updated_mtime = os.path.getmtime(config_file)
        assert updated_mtime > initial_mtime, "文件修改时间应该已更新"
        
        # 验证配置值正确
        current_value = cfg.timing_test
        assert current_value == "timing_value", "保存后的配置值应该正确" 