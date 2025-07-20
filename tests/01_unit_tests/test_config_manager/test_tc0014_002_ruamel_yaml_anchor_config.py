# tests/01_unit_tests/test_config_manager/test_tc0014_002_ruamel_yaml_anchor_config.py
from __future__ import annotations

import tempfile
import os
from ruamel.yaml import YAML


class TestRuamelYamlAnchorConfig:
    """测试ruamel.yaml锚点别名配置选项"""
    
    def test_default_ruamel_yaml_behavior(self):
        """测试默认ruamel.yaml对锚点别名的处理行为"""
        yaml_content = """config: &default_config
  timeout: 30
  retries: 3

service_a:
  settings: *default_config
service_b:
  settings: *default_config
"""
        
        # 默认配置
        yaml_default = YAML()
        yaml_default.preserve_quotes = True
        yaml_default.map_indent = 2
        yaml_default.sequence_indent = 4
        yaml_default.sequence_dash_offset = 2
        yaml_default.default_flow_style = False
        
        # 加载并保存
        data = yaml_default.load(yaml_content)
        
        print("原始YAML内容：")
        print(yaml_content)
        print("\n加载的数据结构：")
        print(data)
        
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=False) as f:
            yaml_default.dump(data, f)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                saved_content = f.read()
                
            print("\n默认配置保存后的内容：")
            print(saved_content)
            
            # 检查是否保留了锚点和别名
            has_anchor = '&' in saved_content
            has_alias = '*' in saved_content
            
            print(f"保存后是否包含锚点(&): {has_anchor}")
            print(f"保存后是否包含别名(*): {has_alias}")
            
        finally:
            os.unlink(temp_path)
    
    def test_ignore_aliases_configuration(self):
        """测试禁用别名的配置"""
        yaml_content = """config: &default_config
  timeout: 30
  retries: 3

service_a:
  settings: *default_config
service_b:
  settings: *default_config
"""
        
        # 配置禁用别名
        yaml_no_alias = YAML()
        yaml_no_alias.preserve_quotes = True
        yaml_no_alias.map_indent = 2
        yaml_no_alias.sequence_indent = 4
        yaml_no_alias.sequence_dash_offset = 2
        yaml_no_alias.default_flow_style = False
        
        # 禁用别名
        yaml_no_alias.representer.ignore_aliases = lambda x: True
        
        # 加载并保存
        data = yaml_no_alias.load(yaml_content)
        
        print("原始YAML内容：")
        print(yaml_content)
        
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=False) as f:
            yaml_no_alias.dump(data, f)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                saved_content = f.read()
                
            print("\n禁用别名后保存的内容：")
            print(saved_content)
            
            # 检查是否还有锚点和别名
            has_anchor = '&' in saved_content
            has_alias = '*' in saved_content
            
            print(f"保存后是否包含锚点(&): {has_anchor}")
            print(f"保存后是否包含别名(*): {has_alias}")
            
        finally:
            os.unlink(temp_path)
    
    def test_current_config_manager_yaml_setup(self):
        """测试当前config_manager的YAML配置"""
        from config_manager.core.file_operations import FileOperations
        
        file_ops = FileOperations()
        yaml_instance = file_ops._yaml
        
        print("当前config_manager的YAML配置：")
        print(f"preserve_quotes: {yaml_instance.preserve_quotes}")
        print(f"map_indent: {yaml_instance.map_indent}")
        print(f"sequence_indent: {yaml_instance.sequence_indent}")
        print(f"sequence_dash_offset: {yaml_instance.sequence_dash_offset}")
        print(f"default_flow_style: {yaml_instance.default_flow_style}")
        
        # 检查是否有ignore_aliases配置
        try:
            ignore_aliases_method = yaml_instance.representer.ignore_aliases
            print(f"ignore_aliases方法: {ignore_aliases_method}")
            
            # 测试ignore_aliases的行为
            test_data = {"test": "value"}
            ignore_result = ignore_aliases_method(test_data)
            print(f"ignore_aliases返回值: {ignore_result}")
            
        except AttributeError as e:
            print(f"未找到ignore_aliases配置: {e}")
    
    def test_complex_anchor_alias_scenario_solutions(self):
        """测试复杂锚点别名场景的不同解决方案"""
        yaml_content_with_duplicates = """__data__:
  defaults: &defaults
    timeout: 30
    retries: 3
__type_hints__: {}

# 重复使用
config:
  app_settings: *defaults
monitoring:
  settings: *defaults
"""
        
        print("=== 测试1: 默认行为 ===")
        yaml1 = YAML()
        yaml1.preserve_quotes = True
        yaml1.map_indent = 2
        yaml1.sequence_indent = 4
        yaml1.default_flow_style = False
        
        data1 = yaml1.load(yaml_content_with_duplicates)
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=False) as f:
            yaml1.dump(data1, f)
            temp_path1 = f.name
        
        try:
            with open(temp_path1, 'r') as f:
                result1 = f.read()
            print("默认行为结果：")
            print(result1)
        finally:
            os.unlink(temp_path1)
        
        print("\n=== 测试2: 禁用别名 ===")
        yaml2 = YAML()
        yaml2.preserve_quotes = True
        yaml2.map_indent = 2
        yaml2.sequence_indent = 4
        yaml2.default_flow_style = False
        yaml2.representer.ignore_aliases = lambda x: True
        
        data2 = yaml2.load(yaml_content_with_duplicates)
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=False) as f:
            yaml2.dump(data2, f)
            temp_path2 = f.name
        
        try:
            with open(temp_path2, 'r') as f:
                result2 = f.read()
            print("禁用别名结果：")
            print(result2)
        finally:
            os.unlink(temp_path2)


if __name__ == "__main__":
    # 直接运行测试
    test_instance = TestRuamelYamlAnchorConfig()
    
    print("=== 测试ruamel.yaml默认行为 ===")
    test_instance.test_default_ruamel_yaml_behavior()
    
    print("\n=== 测试禁用别名配置 ===")
    test_instance.test_ignore_aliases_configuration()
    
    print("\n=== 测试当前config_manager配置 ===")
    test_instance.test_current_config_manager_yaml_setup()
    
    print("\n=== 测试复杂场景解决方案 ===")
    test_instance.test_complex_anchor_alias_scenario_solutions()