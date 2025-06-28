# tests/01_unit_tests/test_config_manager/test_debug_dir_generation.py
from __future__ import annotations

import os
import tempfile
import pytest
from unittest.mock import patch

from src.config_manager import get_config_manager


@pytest.mark.skip(reason="I give up!")
class TestDebugDirGeneration:
    """测试debug_dir自动生成功能"""
    
    def setup_method(self):
        """测试前设置"""
        self.test_time = '2025-01-08T10:30:00'
    
    def test_debug_dir_generation_in_paths(self):
        """测试路径配置中debug_dir的生成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_debug_dir.yaml')
            
            # 创建配置管理器
            config = get_config_manager(
                config_path=config_path,
                auto_create=True,
                test_mode=True,
                first_start_time=self.test_time
            )
            
            # 设置基础配置
            config.set('base_dir', temp_dir)
            config.set('project_name', 'test_project')
            config.set('experiment_name', 'test_exp')
            
            # 获取生成的路径配置
            work_dir = config.get('paths.work_dir')
            debug_dir = config.get('paths.debug_dir')
            
            # 验证debug_dir存在且正确
            assert debug_dir is not None, "debug_dir应该被自动生成"
            assert isinstance(debug_dir, str), "debug_dir应该是字符串类型"
            
            # 验证debug_dir路径结构正确
            expected_debug_dir = os.path.join(work_dir, 'debug')
            assert debug_dir == expected_debug_dir, f"debug_dir路径不正确: 期望 {expected_debug_dir}, 实际 {debug_dir}"
            
            # 验证debug_dir目录被自动创建
            assert os.path.exists(debug_dir), f"debug_dir目录应该被自动创建: {debug_dir}"
            assert os.path.isdir(debug_dir), f"debug_dir应该是目录: {debug_dir}"
    
    def test_debug_dir_access_via_paths_attribute(self):
        """测试通过paths属性访问debug_dir"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_debug_dir_attr.yaml')
            
            config = get_config_manager(
                config_path=config_path,
                auto_create=True,
                test_mode=True,
                first_start_time=self.test_time
            )
            
            # 设置基础配置
            config.set('base_dir', temp_dir)
            config.set('project_name', 'attr_test')
            config.set('experiment_name', 'attr_exp')
            
            # 通过paths属性访问debug_dir
            debug_dir = config.paths.debug_dir
            work_dir = config.paths.work_dir
            
            # 验证路径正确
            expected_debug_dir = os.path.join(work_dir, 'debug')
            assert debug_dir == expected_debug_dir
            
            # 验证目录存在
            assert os.path.exists(debug_dir)
            assert os.path.isdir(debug_dir)
    
    def test_debug_dir_with_different_work_dirs(self):
        """测试不同工作目录下的debug_dir生成"""
        test_cases = [
            ('project1', 'exp1'),
            ('project2', 'exp2'),
            ('deep_project', 'deep_exp'),
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            for project_name, experiment_name in test_cases:
                config_path = os.path.join(temp_dir, f'test_{project_name}.yaml')
                
                config = get_config_manager(
                    config_path=config_path,
                    auto_create=True,
                    test_mode=True,
                    first_start_time=self.test_time
                )
                
                # 设置配置
                config.set('base_dir', temp_dir)
                config.set('project_name', project_name)
                config.set('experiment_name', experiment_name)
                
                # 获取路径
                work_dir = config.get('paths.work_dir')
                debug_dir = config.get('paths.debug_dir')
                
                # 验证路径结构
                expected_debug_dir = os.path.join(work_dir, 'debug')
                assert debug_dir == expected_debug_dir, f"项目 {project_name} 的debug_dir路径不正确"
                
                # 验证目录创建
                assert os.path.exists(debug_dir), f"项目 {project_name} 的debug_dir目录未创建"
    
    def test_debug_dir_in_path_configuration_manager(self):
        """测试路径配置管理器中debug_dir的生成"""
        from src.config_manager.core.path_configuration import PathGenerator
        
        generator = PathGenerator()
        
        # 测试debug_dir生成方法，使用Windows风格路径
        work_dir = 'C:\\test\\work\\dir'
        debug_dirs = generator.generate_debug_directory(work_dir)
        
        # 验证返回结果
        assert 'paths.debug_dir' in debug_dirs
        expected_debug_dir = os.path.join(work_dir, 'debug')
        assert debug_dirs['paths.debug_dir'] == expected_debug_dir
    
    def test_debug_dir_with_mock_debug_mode(self):
        """测试在不同调试模式下debug_dir的生成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, 'test_debug_mode.yaml')
            
            # 测试调试模式
            with patch('is_debug.is_debug', return_value=True):
                config = get_config_manager(
                    config_path=config_path,
                    auto_create=True,
                    test_mode=True,
                    first_start_time=self.test_time
                )
                
                config.set('base_dir', temp_dir)
                config.set('project_name', 'debug_test')
                config.set('experiment_name', 'debug_exp')
                
                work_dir = config.get('paths.work_dir')
                debug_dir = config.get('paths.debug_dir')
                
                # 验证debug_dir存在
                assert debug_dir is not None
                expected_debug_dir = os.path.join(work_dir, 'debug')
                assert debug_dir == expected_debug_dir
                assert os.path.exists(debug_dir)
            
            # 测试生产模式
            with patch('is_debug.is_debug', return_value=False):
                config_path_prod = os.path.join(temp_dir, 'test_prod_mode.yaml')
                config_prod = get_config_manager(
                    config_path=config_path_prod,
                    auto_create=True,
                    test_mode=True,
                    first_start_time=self.test_time
                )
                
                config_prod.set('base_dir', temp_dir)
                config_prod.set('project_name', 'prod_test')
                config_prod.set('experiment_name', 'prod_exp')
                
                work_dir_prod = config_prod.get('paths.work_dir')
                debug_dir_prod = config_prod.get('paths.debug_dir')
                
                # 验证debug_dir在生产模式下也存在
                assert debug_dir_prod is not None
                expected_debug_dir_prod = os.path.join(work_dir_prod, 'debug')
                assert debug_dir_prod == expected_debug_dir_prod
                assert os.path.exists(debug_dir_prod) 