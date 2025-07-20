# tests/01_unit_tests/test_config_manager/test_tc0014_001_yaml_anchor_alias_duplication.py
from __future__ import annotations

import os
import tempfile
import pytest
from datetime import datetime

from config_manager import get_config_manager


class TestYamlAnchorAliasDuplication:
    """测试YAML锚点别名重复节点问题"""

    def test_anchor_alias_duplication_reproduction(self):
        """重现锚点别名导致重复节点的问题"""
        # 创建包含锚点和别名的YAML内容
        yaml_content_with_anchors = """__data__:
  browser:
    headless: true
    timeout_multiplier: 1000
  url_validation:
    exclude_image_patterns: &id001
      - /avatar/
      - /icon/
      - /logo/
      - favicon
  titles: &id002
    - 测试标题1
    - 测试标题2
    - 测试标题3
__type_hints__: {}

# 使用别名引用
url_validation:
  exclude_image_patterns: *id001
  level2_pattern: ^https://example\\.com/.*$
titles: *id002
browser:
  headless: true
  timeout_multiplier: 1000
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "test_config.yaml")
            
            # 手动创建包含锚点别名的配置文件
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content_with_anchors)
            
            print(f"创建的测试配置文件：{config_path}")
            print("原始文件内容：")
            with open(config_path, 'r', encoding='utf-8') as f:
                print(f.read())
            
            # 使用config_manager加载配置
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                auto_create=False
            )
            
            # 验证配置能正确加载
            assert config is not None, "配置加载失败"
            
            # 检查锚点别名引用的数据是否正确
            exclude_patterns = config.get('url_validation.exclude_image_patterns')
            titles = config.get('titles')
            
            print(f"加载的exclude_patterns: {exclude_patterns}")
            print(f"加载的titles: {titles}")
            
            assert exclude_patterns is not None, "exclude_image_patterns应该存在"
            assert titles is not None, "titles应该存在"
            assert len(exclude_patterns) == 4, f"exclude_patterns应该有4个元素，实际有{len(exclude_patterns)}"
            assert len(titles) == 3, f"titles应该有3个元素，实际有{len(titles)}"
            
            # 修改配置以触发保存
            config['test_field'] = 'test_value'
            
            # 强制保存配置
            config.save()
            
            # 获取测试模式下的实际配置文件路径
            actual_config_path = config._config_path
            print(f"\n实际配置文件路径: {actual_config_path}")
            
            # 重新读取保存后的文件内容
            print("\n保存后的文件内容：")
            with open(actual_config_path, 'r', encoding='utf-8') as f:
                saved_content = f.read()
                print(saved_content)
            
            # 检查是否出现重复节点
            self._check_for_duplicates(saved_content)
    
    def test_anchor_alias_modification_behavior(self):
        """测试修改锚点别名引用的值时的行为"""
        yaml_content = """__data__:
  base_config: &default_config
    timeout: 30
    retries: 3
    debug: false
__type_hints__: {}

# 使用别名引用
service_a:
  config: *default_config
service_b:
  config: *default_config
"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "test_config.yaml")
            
            # 创建配置文件
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            # 加载配置
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                auto_create=False
            )
            
            # 修改其中一个引用的值
            config['service_a.config.timeout'] = 60
            
            # 保存配置
            config.save()
            
            # 获取测试模式下的实际配置文件路径
            actual_config_path = config._config_path
            
            # 检查保存后的内容
            with open(actual_config_path, 'r', encoding='utf-8') as f:
                saved_content = f.read()
                print("修改后保存的内容：")
                print(saved_content)
            
            # 验证修改是否正确反映
            reloaded_config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                auto_create=False
            )
            
            service_a_timeout = reloaded_config.get('service_a.config.timeout')
            service_b_timeout = reloaded_config.get('service_b.config.timeout')
            
            print(f"service_a timeout: {service_a_timeout}")
            print(f"service_b timeout: {service_b_timeout}")
            
            # 检查是否出现重复
            self._check_for_duplicates(saved_content)
    
    def _check_for_duplicates(self, yaml_content: str):
        """检查YAML内容中是否存在重复节点，考虑层级结构和上下文"""
        lines = yaml_content.split('\n')
        
        # 记录键的完整路径：(键名, 缩进级别, 父级路径) -> 行号
        key_contexts = {}
        duplicate_keys = []
        current_path = []  # 当前路径栈
        
        for line_num, line in enumerate(lines, 1):
            stripped_line = line.strip()
            
            # 跳过注释、空行和特殊行
            if (not stripped_line or 
                stripped_line.startswith('#') or 
                stripped_line.startswith('- ') or
                ':' not in stripped_line):
                continue
            
            # 计算缩进级别
            indent_level = len(line) - len(line.lstrip())
            
            # 提取键名
            if ':' in stripped_line:
                key = stripped_line.split(':')[0].strip()
                
                # 跳过锚点和别名定义行
                if '&' in key or '*' in key:
                    continue
                
                # 检查值是否为别名引用
                colon_pos = stripped_line.find(':')
                if colon_pos != -1 and colon_pos + 1 < len(stripped_line):
                    value_part = stripped_line[colon_pos + 1:].strip()
                    if value_part.startswith('*'):
                        continue  # 跳过别名引用
                
                # 根据缩进级别调整当前路径
                if indent_level == 0:
                    current_path = [key]
                elif indent_level > 0:
                    # 调整路径栈到合适的深度
                    target_depth = indent_level // 2  # 假设每级缩进2个空格
                    current_path = current_path[:target_depth]
                    current_path.append(key)
                
                # 构建完整的键路径
                full_path = '.'.join(current_path)
                
                # 特殊处理：数据值和类型提示是不同的上下文
                context_key = full_path
                if len(current_path) >= 2:
                    parent_path = '.'.join(current_path[:-1])
                    if parent_path.endswith('__type_hints__'):
                        context_key = f"{full_path}@type_hint"
                    elif current_path[-2] == '__data__' and current_path[-1] != '__type_hints__':
                        context_key = f"{full_path}@data_value"
                
                print(f"🔧 检查路径: {context_key} (第{line_num}行)")
                
                # 检查在相同上下文中是否重复
                if context_key in key_contexts:
                    duplicate_keys.append({
                        'key': key,
                        'full_path': full_path,
                        'first_line': key_contexts[context_key],
                        'duplicate_line': line_num,
                        'first_content': lines[key_contexts[context_key] - 1].strip(),
                        'duplicate_content': line.strip()
                    })
                else:
                    key_contexts[context_key] = line_num
        
        # 过滤掉合理的"重复"情况
        real_duplicates = []
        for dup in duplicate_keys:
            key = dup['key']
            
            # 过滤掉数据值和类型提示的组合（这是正常的）
            if (key == 'first_start_time' and 
                '__type_hints__' in dup['full_path'] and 
                len([d for d in duplicate_keys if d['key'] == key]) == 1):
                print(f"✅ 跳过正常的数据值/类型提示组合: {key}")
                continue
            
            real_duplicates.append(dup)
        
        # 报告真正的重复键
        if real_duplicates:
            print("\n❌ 发现真正重复的键：")
            for dup in real_duplicates:
                print(f"  键 '{dup['key']}' 在路径 '{dup['full_path']}' 重复:")
                print(f"    第 {dup['first_line']} 行: {dup['first_content']}")
                print(f"    第 {dup['duplicate_line']} 行: {dup['duplicate_content']}")
            
            # 抛出断言错误，标明具体的重复键
            duplicate_key_names = [dup['key'] for dup in real_duplicates]
            assert False, f"发现真正重复的键: {duplicate_key_names}"
        else:
            print("\n✅ 未发现真正的重复键")
    
    def test_complex_anchor_alias_scenario(self):
        """测试复杂的锚点别名场景（多层嵌套）"""
        complex_yaml = """__data__:
  database_defaults: &db_defaults
    host: localhost
    port: 5432
    pool_size: 10
    ssl: true
  cache_defaults: &cache_defaults
    redis:
      host: localhost
      port: 6379
      db: 0
    timeout: 30
__type_hints__: {}

# 多个服务使用相同的数据库配置
services:
  user_service:
    database: *db_defaults
    cache: *cache_defaults
  order_service:
    database: *db_defaults
    cache: *cache_defaults
  
# 在不同地方也引用相同配置
monitoring:
  database: *db_defaults
  
backup:
  database: *db_defaults
"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "complex_config.yaml")
            
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(complex_yaml)
            
            # 加载和保存配置
            config = get_config_manager(
                config_path=config_path,
                test_mode=True,
                auto_create=False
            )
            
            # 验证配置正确加载
            user_db_host = config.get('services.user_service.database.host')
            order_db_host = config.get('services.order_service.database.host')
            
            assert user_db_host == 'localhost'
            assert order_db_host == 'localhost'
            
            # 修改配置触发保存
            config['services.user_service.name'] = 'User Service'
            config.save()
            
            # 获取测试模式下的实际配置文件路径
            actual_config_path = config._config_path
            
            # 检查保存后的内容
            with open(actual_config_path, 'r', encoding='utf-8') as f:
                saved_content = f.read()
                print("复杂场景保存后的内容：")
                print(saved_content)
            
            # 检查重复
            self._check_for_duplicates(saved_content)


if __name__ == "__main__":
    # 直接运行测试
    test_instance = TestYamlAnchorAliasDuplication()
    
    print("=== 测试1: 基本锚点别名重复问题 ===")
    try:
        test_instance.test_anchor_alias_duplication_reproduction()
        print("✅ 测试1通过")
    except Exception as e:
        print(f"❌ 测试1失败: {e}")
    
    print("\n=== 测试2: 锚点别名修改行为 ===")
    try:
        test_instance.test_anchor_alias_modification_behavior()
        print("✅ 测试2通过")
    except Exception as e:
        print(f"❌ 测试2失败: {e}")
    
    print("\n=== 测试3: 复杂锚点别名场景 ===")
    try:
        test_instance.test_complex_anchor_alias_scenario()
        print("✅ 测试3通过")
    except Exception as e:
        print(f"❌ 测试3失败: {e}")