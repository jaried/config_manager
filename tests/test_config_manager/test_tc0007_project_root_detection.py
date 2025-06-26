# tests/config_manager/test_tc0007_project_root_detection.py
from __future__ import annotations
import os
import tempfile
import shutil
import pytest
from pathlib import Path


class TestProjectRootDetection:
    """测试项目根目录检测功能"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 清除所有实例缓存
        from src.config_manager.config_manager import _clear_instances_for_testing
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
        from src.config_manager.config_manager import _clear_instances_for_testing
        _clear_instances_for_testing()

    def test_tc0007_001_detect_project_root_from_subdirectory(self):
        """测试从子目录检测项目根目录"""
        from src.config_manager.config_manager import get_config_manager

        # 1. 在项目根目录创建实例
        cm1 = get_config_manager(auto_create=True)
        path1 = cm1.get_config_path()

        # 2. 创建临时项目目录
        temp_dir = tempfile.mkdtemp(prefix="test_project_")
        src_dir = os.path.join(temp_dir, 'src')
        sub_dir = os.path.join(temp_dir, 'scripts')
        deep_dir = os.path.join(temp_dir, 'docs', 'api')

        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(sub_dir, exist_ok=True)
        os.makedirs(deep_dir, exist_ok=True)

        expected_config_path = os.path.join(src_dir, 'config', 'config.yaml')

        try:
            # 测试从scripts目录运行
            os.chdir(sub_dir)
            cm1 = get_config_manager(auto_create=True)
            actual_path1 = cm1.get_config_path()

            assert temp_dir in actual_path1, f"配置文件应该在项目目录中，实际路径: {actual_path1}"
            assert 'site-packages' not in actual_path1, f"配置文件不应该在site-packages中，实际路径: {actual_path1}"
            assert actual_path1 == expected_config_path, f"应该使用项目根目录的src/config，期望: {expected_config_path}, 实际: {actual_path1}"

            # 清除缓存，测试从深层目录运行
            from src.config_manager.config_manager import _clear_instances_for_testing
            _clear_instances_for_testing()

            os.chdir(deep_dir)
            cm2 = get_config_manager(auto_create=True)
            actual_path2 = cm2.get_config_path()

            assert actual_path2 == expected_config_path, f"从深层目录也应该找到项目根目录，期望: {expected_config_path}, 实际: {actual_path2}"

        finally:
            os.chdir(self.original_cwd)
            try:
                assert temp_dir.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {temp_dir}"
                shutil.rmtree(temp_dir)
            except:
                pass

    def test_tc0007_002_reproduce_site_packages_issue(self):
        """重现配置文件被保存到site-packages的问题"""
        from src.config_manager.config_manager import get_config_manager

        # 创建一个没有src目录的临时目录
        temp_dir = tempfile.mkdtemp(prefix="test_no_src_")

        try:
            # 切换到没有src目录的目录
            os.chdir(temp_dir)

            # 创建配置管理器实例
            cm = get_config_manager(auto_create=True)
            actual_path = cm.get_config_path()

            # 当前的实现会错误地使用site-packages路径
            # 这个测试应该失败，直到我们修复了_resolve_config_path方法
            print(f"当前路径: {actual_path}")

            # 验证问题：配置文件被错误地保存到site-packages
            if 'site-packages' in actual_path:
                pytest.fail(f"问题重现：配置文件被错误保存到site-packages: {actual_path}")

        finally:
            os.chdir(self.original_cwd)
            try:
                assert temp_dir.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {temp_dir}"
                shutil.rmtree(temp_dir)
            except:
                pass

    def test_tc0007_004_nested_project_structure(self):
        """测试嵌套项目结构的检测"""
        from src.config_manager.config_manager import get_config_manager

        # 创建嵌套项目结构
        temp_root = tempfile.mkdtemp(prefix="test_nested_")

        # 外层项目
        outer_project = os.path.join(temp_root, 'outer_project')
        outer_src = os.path.join(outer_project, 'src')
        os.makedirs(outer_src, exist_ok=True)

        # 内层项目
        inner_project = os.path.join(outer_project, 'subprojects', 'inner_project')
        inner_src = os.path.join(inner_project, 'src')
        os.makedirs(inner_src, exist_ok=True)

        try:
            # 从内层项目运行，应该使用内层项目的配置
            inner_work_dir = os.path.join(inner_project, 'scripts')
            os.makedirs(inner_work_dir, exist_ok=True)
            os.chdir(inner_work_dir)

            cm = get_config_manager(auto_create=True)
            actual_path = cm.get_config_path()

            # 应该使用最近的项目根目录（内层项目）
            expected_config_path = os.path.join(inner_src, 'config', 'config.yaml')
            assert actual_path == expected_config_path, f"应该使用最近的项目根目录，期望: {expected_config_path}, 实际: {actual_path}"

        finally:
            os.chdir(self.original_cwd)
            try:
                assert temp_root.startswith(tempfile.gettempdir()), f"禁止删除非临时目录: {temp_root}"
                shutil.rmtree(temp_root)
            except:
                pass
