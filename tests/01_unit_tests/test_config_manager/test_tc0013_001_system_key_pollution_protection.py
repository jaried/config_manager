# tests/01_unit_tests/test_config_manager/test_tc0013_001_system_key_pollution_protection.py
"""
TC0013-001: 系统键污染防护测试

这是一个关键的回归测试，确保系统键(__type_hints__, __data__, debug_mode)
不会被错误地写入__data__节点内部，造成数据结构污染。

背景：之前发现的严重问题，__type_hints__被错误写入__data__节点内部，
影响了多个项目(bakamh, gplearn_trading等)的正常运行。

测试覆盖：
1. ConfigNode层面的系统键过滤
2. ConfigManager层面的系统键过滤  
3. 文件保存时的系统键清理
4. 测试模式下的系统键污染防护
5. 不同操作路径的污染检测
"""
from __future__ import annotations
from datetime import datetime

import tempfile
import os
import pytest
import yaml
from config_manager import get_config_manager
from config_manager.config_node import ConfigNode


class TestSystemKeyPollutionProtection:
    """系统键污染防护测试类"""

    def test_tc0013_001_001_config_node_system_key_filtering(self):
        """TC0013-001-001: ConfigNode层面的系统键过滤测试"""
        node = ConfigNode()
        
        # 设置正常配置
        node.app_name = "test_app"
        node.version = "1.0"
        node["database_host"] = "localhost"
        
        # 尝试设置系统键（应该被过滤）
        node.__type_hints__ = {"malicious": "data"}
        node.__data__ = {"malicious": "data"}
        node.debug_mode = True
        
        # 通过字典方式尝试设置系统键
        node["__type_hints__"] = {"malicious2": "data"}
        node["__data__"] = {"malicious2": "data"}
        node["debug_mode"] = False
        
        # 验证正常配置存在
        assert node.app_name == "test_app"
        assert node.version == "1.0"
        assert node["database_host"] == "localhost"
        
        # 验证系统键没有被污染到_data中
        internal_data = node._data
        assert "__type_hints__" not in internal_data, "❌ 系统键污染: __type_hints__出现在ConfigNode._data中"
        assert "__data__" not in internal_data, "❌ 系统键污染: __data__出现在ConfigNode._data中"
        assert "debug_mode" not in internal_data, "❌ 系统键污染: debug_mode出现在ConfigNode._data中"
        
        # 验证to_dict方法不包含系统键
        dict_data = node.to_dict()
        assert "__type_hints__" not in dict_data, "❌ 系统键污染: __type_hints__出现在to_dict结果中"
        assert "__data__" not in dict_data, "❌ 系统键污染: __data__出现在to_dict结果中"
        assert "debug_mode" not in dict_data, "❌ 系统键污染: debug_mode出现在to_dict结果中"
        
        # 验证正常键存在
        assert "app_name" in dict_data
        assert "version" in dict_data
        assert "database_host" in dict_data
        
        return

    def test_tc0013_001_002_config_node_from_dict_filtering(self):
        """TC0013-001-002: ConfigNode.from_dict方法的系统键过滤测试"""
        node = ConfigNode()
        
        # 准备包含系统键污染的数据
        polluted_data = {
            "app_name": "test_app",
            "version": "1.0",
            "__type_hints__": {"malicious": "type"},
            "__data__": {"malicious": "data"},
            "debug_mode": True,
            "normal_config": "value"
        }
        
        # 使用from_dict加载污染数据
        node.from_dict(polluted_data)
        
        # 验证正常键被加载
        assert node.app_name == "test_app"
        assert node.version == "1.0"
        assert node.normal_config == "value"
        
        # 验证系统键没有被加载到_data中
        internal_data = node._data
        assert "__type_hints__" not in internal_data, "❌ from_dict系统键污染: __type_hints__"
        assert "__data__" not in internal_data, "❌ from_dict系统键污染: __data__"
        assert "debug_mode" not in internal_data, "❌ from_dict系统键污染: debug_mode"
        
        return

    def test_tc0013_001_003_config_node_update_filtering(self):
        """TC0013-001-003: ConfigNode.update方法的系统键过滤测试"""
        node = ConfigNode()
        
        # 使用update方法尝试添加系统键
        node.update({
            "app_name": "test_app",
            "__type_hints__": {"malicious": "type"},
            "__data__": {"malicious": "data"},
            "debug_mode": True,
            "normal_key": "normal_value"
        })
        
        # 验证正常键存在
        assert node.app_name == "test_app"
        assert node.normal_key == "normal_value"
        
        # 验证系统键没有被污染
        internal_data = node._data
        assert "__type_hints__" not in internal_data, "❌ update系统键污染: __type_hints__"
        assert "__data__" not in internal_data, "❌ update系统键污染: __data__"
        assert "debug_mode" not in internal_data, "❌ update系统键污染: debug_mode"
        
        return

    def test_tc0013_001_004_config_manager_system_key_protection(self):
        """TC0013-001-004: ConfigManager层面的系统键污染防护测试"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "test_config.yaml")
            
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                auto_create=True
            )
            
            # 设置正常配置
            config.app_name = "test_app"
            config.database = {"host": "localhost", "port": 5432}
            
            # 尝试通过各种方式设置系统键
            config.__type_hints__ = {"malicious": "type"}
            config.__data__ = {"malicious": "data"}
            config.debug_mode = True
            
            config["__type_hints__"] = {"malicious2": "type"}
            config["__data__"] = {"malicious2": "data"}
            config["debug_mode"] = False
            
            # 手动保存确保文件已写入
            config.save()
            
            # 验证内存中的数据结构正确
            internal_data = config._data
            assert "__type_hints__" not in internal_data, "❌ ConfigManager内存污染: __type_hints__"
            assert "__data__" not in internal_data, "❌ ConfigManager内存污染: __data__"
            assert "debug_mode" not in internal_data, "❌ ConfigManager内存污染: debug_mode"
            
            # 验证文件结构正确
            actual_config_path = config.get_config_path()
            with open(actual_config_path, 'r', encoding='utf-8') as f:
                file_content = yaml.safe_load(f)
            
            # 检查文件顶层结构
            assert '__data__' in file_content, "配置文件应该有__data__节点"
            assert '__type_hints__' in file_content, "配置文件应该有__type_hints__节点"
            
            # 关键检查：__data__节点中不应该有系统键污染
            data_section = file_content['__data__']
            assert '__type_hints__' not in data_section, "❌ 文件污染: __type_hints__出现在__data__节点中"
            assert '__data__' not in data_section, "❌ 文件污染: __data__出现在__data__节点中"
            assert 'debug_mode' not in data_section, "❌ 文件污染: debug_mode出现在__data__节点中"
            
            # 验证正常配置存在
            assert 'app_name' in data_section, "正常配置app_name应该在__data__节点中"
            assert 'database' in data_section, "正常配置database应该在__data__节点中"
            
            return

    def test_tc0013_001_005_yaml_file_structure_integrity(self):
        """TC0013-001-005: YAML文件结构完整性测试"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "test_config.yaml")
            
            # 创建配置并设置数据
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                auto_create=True
            )
            
            config.app_name = "integrity_test"
            config.version = "2.0"
            config.nested = {"level1": {"level2": "value"}}
            config.first_start_time = datetime.now()
            
            # 保存配置
            config.save()
            
            # 验证保存的文件结构
            actual_config_path = config.get_config_path()
            with open(actual_config_path, 'r', encoding='utf-8') as f:
                file_content = yaml.safe_load(f)
            
            # 验证顶层结构
            required_top_level_keys = {'__data__', '__type_hints__'}
            actual_top_level_keys = set(file_content.keys())
            
            # __data__和__type_hints__必须存在
            for key in required_top_level_keys:
                assert key in actual_top_level_keys, f"缺少必要的顶层键: {key}"
            
            # 检查是否有不应该存在的顶层键（排除first_start_time，它可能作为顶层别名存在）
            allowed_extra_keys = {'first_start_time'}
            unexpected_keys = actual_top_level_keys - required_top_level_keys - allowed_extra_keys
            assert not unexpected_keys, f"发现不应该存在的顶层键: {unexpected_keys}"
            
            # 验证__data__节点结构
            data_section = file_content['__data__']
            assert isinstance(data_section, dict), "__data__节点应该是字典类型"
            
            # 验证__data__节点包含正确的配置数据
            expected_data_keys = {'app_name', 'version', 'nested', 'first_start_time'}
            for key in expected_data_keys:
                assert key in data_section, f"__data__节点中缺少配置键: {key}"
            
            # 验证__type_hints__节点结构
            type_hints_section = file_content['__type_hints__']
            assert isinstance(type_hints_section, dict), "__type_hints__节点应该是字典类型"
            
            return

    def test_tc0013_001_006_pollution_detection_in_existing_files(self):
        """TC0013-001-006: 现有文件中的污染检测和清理测试"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "polluted_config.yaml")
            
            # 创建一个包含污染的配置文件
            polluted_config = {
                '__data__': {
                    'app_name': 'test_app',
                    'version': '1.0',
                    '__type_hints__': {'malicious': 'type'},  # 污染！
                    '__data__': {'nested': 'pollution'},      # 污染！
                    'debug_mode': True,                       # 污染！
                    'normal_config': 'value'
                },
                '__type_hints__': {
                    'first_start_time': 'datetime'
                }
            }
            
            # 保存污染的配置文件
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(polluted_config, f)
            
            # 使用ConfigManager加载这个污染的文件
            config = get_config_manager(
                config_path=config_path,
                test_mode=True
            )
            
            # 进行一些配置操作触发保存
            config.new_key = "new_value"
            config.save()
            
            # 重新读取文件，验证污染已被清理（使用实际的配置文件路径）
            actual_config_path = config.get_config_path()
            with open(actual_config_path, 'r', encoding='utf-8') as f:
                cleaned_content = yaml.safe_load(f)
            
            # 验证__data__节点已被清理
            data_section = cleaned_content['__data__']
            assert '__type_hints__' not in data_section, "❌ 污染未清理: __type_hints__仍在__data__中"
            assert '__data__' not in data_section, "❌ 污染未清理: __data__仍在__data__中"
            assert 'debug_mode' not in data_section, "❌ 污染未清理: debug_mode仍在__data__中"
            
            # 验证正常配置仍然存在
            assert 'app_name' in data_section, "正常配置丢失: app_name"
            assert 'version' in data_section, "正常配置丢失: version"
            assert 'normal_config' in data_section, "正常配置丢失: normal_config"
            assert 'new_key' in data_section, "新增配置丢失: new_key"
            
            return

    def test_tc0013_001_007_regression_test_for_issue_fix(self):
        """TC0013-001-007: 问题修复的回归测试"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "regression_test.yaml")
            
            # 模拟导致原始问题的场景
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                auto_create=True,
                first_start_time=datetime.now()
            )
            
            # 设置各种类型的配置
            config.project_name = "regression_test"
            config.first_start_time = datetime.now()
            config.complex_config = {
                "database": {"host": "localhost", "port": 5432},
                "cache": {"ttl": 3600}
            }
            
            # 多次保存和重新加载（这是发现原始问题的场景）
            for i in range(3):
                config.iteration = i
                config.save()
                
                # 重新读取验证
                with open(config.get_config_path(), 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                
                # 每次都验证没有污染
                data_section = content['__data__']
                assert '__type_hints__' not in data_section, f"❌ 第{i}次迭代发现污染: __type_hints__"
                assert '__data__' not in data_section, f"❌ 第{i}次迭代发现污染: __data__"
                assert 'debug_mode' not in data_section, f"❌ 第{i}次迭代发现污染: debug_mode"
            
            return

    def test_tc0013_001_008_multi_level_nesting_protection(self):
        """TC0013-001-008: 多层嵌套结构的系统键污染防护测试"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "nested_test.yaml")
            
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                auto_create=True
            )
            
            # 创建深层嵌套结构
            config.level1 = {
                "level2": {
                    "level3": {
                        "data": "deep_value",
                        "__type_hints__": "should_not_appear",  # 尝试在深层嵌套中添加系统键
                        "__data__": "should_not_appear"
                    }
                }
            }
            
            config.save()
            
            # 验证嵌套结构中的系统键被正确过滤
            assert config.level1.level2.level3.data == "deep_value"
            
            # 检查内部数据结构
            level3_data = config.level1.level2.level3._data
            assert "__type_hints__" not in level3_data, "❌ 深层嵌套污染: __type_hints__"
            assert "__data__" not in level3_data, "❌ 深层嵌套污染: __data__"
            
            return

    def test_tc0013_001_009_system_key_pollution_comprehensive_coverage(self):
        """TC0013-001-009: 系统键污染的全面覆盖测试"""
        
        # 定义所有需要防护的系统键
        system_keys = {'__type_hints__', '__data__', 'debug_mode'}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "comprehensive_test.yaml")
            
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                auto_create=True
            )
            
            # 测试所有系统键的各种设置方式
            for sys_key in system_keys:
                # 属性设置
                setattr(config, sys_key, f"malicious_value_{sys_key}")
                
                # 字典设置
                config[sys_key] = f"malicious_dict_{sys_key}"
                
                # update方式设置
                config.update({sys_key: f"malicious_update_{sys_key}"})
            
            # 添加正常配置确保功能正常
            config.normal_key = "normal_value"
            config.save()
            
            # 验证所有系统键都没有被污染
            internal_data = config._data
            for sys_key in system_keys:
                assert sys_key not in internal_data, f"❌ 全面测试污染检测: {sys_key}出现在内存中"
            
            # 验证文件结构
            with open(config.get_config_path(), 'r', encoding='utf-8') as f:
                file_content = yaml.safe_load(f)
            
            data_section = file_content['__data__']
            for sys_key in system_keys:
                assert sys_key not in data_section, f"❌ 全面测试文件污染: {sys_key}出现在文件中"
            
            # 验证正常功能不受影响
            assert 'normal_key' in data_section, "正常功能受影响"
            assert config.normal_key == "normal_value", "配置读取功能受影响"
            
            return


if __name__ == "__main__":
    # 可以直接运行这个文件进行测试
    pytest.main([__file__, "-v"])