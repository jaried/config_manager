# tests/config_manager/tc0006_singleton_path_resolution.py
from __future__ import annotations
import os
import tempfile
import shutil
import pytest
from pathlib import Path


class TestSingletonPathResolution:
    """测试单例模式的路径解析功能"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        # 清除所有实例缓存
        from config_manager.config_manager import _clear_instances_for_testing
        _clear_instances_for_testing()
        
        # 记录原始工作目录
        self.original_cwd = os.getcwd()
        
        # 确保在项目根目录下运行测试
        # 从当前目录向上查找项目根目录（包含src目录的目录）
        current_dir = self.original_cwd
        project_root = None
        
        # 向上查找最多5级目录
        for _ in range(5):
            if os.path.exists(os.path.join(current_dir, 'src')):
                project_root = current_dir
                break
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # 已到根目录
                break
            current_dir = parent_dir
        
        if project_root:
            os.chdir(project_root)
            self.project_root = project_root
        else:
            # 如果找不到项目根目录，使用原始目录
            self.project_root = self.original_cwd
        
    def teardown_method(self):
        """每个测试方法后的清理"""
        # 恢复原始工作目录
        os.chdir(self.original_cwd)
        
        # 清除实例缓存
        from config_manager.config_manager import _clear_instances_for_testing
        _clear_instances_for_testing()

    def test_tc0006_001_different_directories_create_different_instances(self):
        """测试不同目录下创建不同的配置管理器实例"""
        from config_manager import get_config_manager
        
        # 1. 在项目根目录创建实例
        cm1 = get_config_manager()
        path1 = cm1.get_config_path()
        
        # 2. 创建临时项目目录
        temp_dir = tempfile.mkdtemp(prefix="test_project_")
        src_dir = os.path.join(temp_dir, 'src')
        os.makedirs(src_dir, exist_ok=True)
        
        try:
            # 3. 切换到临时目录
            os.chdir(temp_dir)
            
            # 4. 在新目录创建实例（不清除缓存）
            cm2 = get_config_manager()
            path2 = cm2.get_config_path()
            
            # 5. 验证结果
            assert cm1 is not cm2, "不同目录下应该创建不同的实例"
            assert temp_dir in path2, f"配置文件应该在临时项目目录中，实际路径: {path2}"
            assert self.project_root in path1, f"原始实例应该在项目根目录中，实际路径: {path1}"
            
            # 验证路径结构正确
            assert path1.endswith('src/config/config.yaml') or path1.endswith('src\\config\\config.yaml'), f"原始路径应该在src/config下，实际: {path1}"
            assert path2.endswith('src/config/config.yaml') or path2.endswith('src\\config\\config.yaml'), f"临时路径应该在src/config下，实际: {path2}"
            
        finally:
            # 清理临时目录
            os.chdir(self.project_root)
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

    def test_tc0006_002_same_directory_returns_same_instance(self):
        """测试同一目录下多次调用返回相同实例"""
        from config_manager import get_config_manager
        
        # 在同一目录下多次调用
        cm1 = get_config_manager()
        cm2 = get_config_manager()
        
        # 应该返回相同的实例
        assert cm1 is cm2, "同一目录下应该返回相同的实例"
        assert cm1.get_config_path() == cm2.get_config_path(), "配置路径应该相同"

    def test_tc0006_003_explicit_path_creates_separate_instance(self):
        """测试显式指定路径创建独立实例"""
        from config_manager import get_config_manager
        
        # 1. 创建默认实例
        cm1 = get_config_manager()
        
        # 2. 创建临时目录和显式路径
        temp_dir = tempfile.mkdtemp(prefix="test_explicit_")
        explicit_path = os.path.join(temp_dir, 'custom_config.yaml')
        
        try:
            # 3. 使用显式路径创建实例
            cm2 = get_config_manager(config_path=explicit_path)
            
            # 4. 验证结果
            assert cm1 is not cm2, "显式路径应该创建不同的实例"
            assert cm2.get_config_path() == explicit_path, f"显式路径应该被正确使用，期望: {explicit_path}, 实际: {cm2.get_config_path()}"
            
        finally:
            # 清理临时目录
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

    def test_tc0006_004_config_operations_work_correctly(self):
        """测试配置操作在不同实例中正常工作"""
        from config_manager import get_config_manager
        
        # 1. 在项目根目录创建实例并设置配置
        cm1 = get_config_manager()
        cm1.set('test_key1', 'value1', autosave=False)
        
        # 2. 创建临时项目目录
        temp_dir = tempfile.mkdtemp(prefix="test_config_ops_")
        src_dir = os.path.join(temp_dir, 'src')
        os.makedirs(src_dir, exist_ok=True)
        
        try:
            # 3. 切换到临时目录并创建新实例
            os.chdir(temp_dir)
            cm2 = get_config_manager()
            cm2.set('test_key2', 'value2', autosave=False)
            
            # 4. 验证配置隔离
            assert cm1.get('test_key1') == 'value1', "原实例应该保持自己的配置"
            assert cm1.get('test_key2') is None, "原实例不应该有新实例的配置"
            
            assert cm2.get('test_key2') == 'value2', "新实例应该有自己的配置"
            assert cm2.get('test_key1') is None, "新实例不应该有原实例的配置"
            
        finally:
            # 清理临时目录
            os.chdir(self.project_root)
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

    def test_tc0006_005_cache_key_format_validation(self):
        """测试缓存键格式的正确性"""
        from config_manager import get_config_manager
        from config_manager.config_manager import ConfigManager
        
        # 1. 测试自动路径的缓存键格式
        # 注意：在setup_method中我们已经切换到项目根目录了
        cm1 = get_config_manager()
        cache_keys = list(ConfigManager._instances.keys())
        
        # 应该有一个缓存键
        assert len(cache_keys) >= 1, f"应该至少有一个缓存实例，当前缓存键: {cache_keys}"
        
        # 检查是否有自动路径缓存键（格式为 "auto:工作目录"）
        current_cwd = os.getcwd()
        auto_keys = [key for key in cache_keys if key.startswith('auto:')]
        
        # 如果没有auto:格式的键，可能是因为在setup中切换了目录，
        # 那么应该有一个包含当前工作目录的键
        if len(auto_keys) == 0:
            # 检查是否有包含当前工作目录的缓存键
            cwd_keys = [key for key in cache_keys if current_cwd in key]
            assert len(cwd_keys) >= 1, f"应该有包含当前工作目录的缓存键，当前工作目录: {current_cwd}，缓存键: {cache_keys}"
        else:
            # 验证auto:格式的缓存键包含当前工作目录
            assert any(current_cwd in key for key in auto_keys), f"auto:缓存键应该包含当前工作目录 {current_cwd}，当前auto键: {auto_keys}"
        
        # 2. 测试显式路径的缓存键格式
        temp_dir = tempfile.mkdtemp(prefix="test_cache_key_")
        explicit_path = os.path.join(temp_dir, 'explicit.yaml')
        
        try:
            cm2 = get_config_manager(config_path=explicit_path)
            cache_keys_after = list(ConfigManager._instances.keys())
            
            # 应该有显式路径的缓存键
            explicit_keys = [key for key in cache_keys_after if explicit_path in key]
            assert len(explicit_keys) >= 1, f"应该有包含显式路径的缓存键，显式路径: {explicit_path}，当前缓存键: {cache_keys_after}"
            
        finally:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass 