# tests/01_unit_tests/test_config_manager/test_tc0018_001_first_start_time_type_fix.py
from __future__ import annotations
from datetime import datetime

import pytest
from config_manager import get_config_manager
from ruamel.yaml.scalarstring import SingleQuotedScalarString


def test_first_start_time_type_consistency():
    """验证 first_start_time 类型一致性问题"""
    # 创建配置管理器
    test_time = datetime(2025, 1, 7, 18, 15, 20)
    config = get_config_manager(test_mode=True, first_start_time=test_time)
    
    # 验证首次启动时间应该是 datetime 对象，而不是字符串
    print(f"config.first_start_time 类型: {type(config.first_start_time)}")
    print(f"config.first_start_time 值: {config.first_start_time}")
    
    assert isinstance(config.first_start_time, datetime), f"first_start_time 应该是 datetime 对象，实际是 {type(config.first_start_time)}"
    
    # 验证不应该是 SingleQuotedScalarString
    assert not isinstance(config.first_start_time, SingleQuotedScalarString), "first_start_time 不应该是 SingleQuotedScalarString 类型"
    
    # 验证时间值是否正确
    assert config.first_start_time == test_time, f"first_start_time 值不正确: {config.first_start_time} != {test_time}"


def test_first_start_time_yaml_type_hints():
    """验证 first_start_time 在 YAML 中的类型注释"""
    test_time = datetime(2025, 1, 7, 18, 15, 20)
    config = get_config_manager(test_mode=True, first_start_time=test_time)
    
    # 保存配置
    config.save()
    
    # 验证 __type_hints__ 中包含 first_start_time 的类型注释
    assert '__type_hints__' in config._data, "配置中应该包含 __type_hints__"
    
    type_hints = config._data.get('__type_hints__', {})
    print(f"类型注释: {type_hints}")
    
    # 验证 first_start_time 的类型注释
    assert 'first_start_time' in type_hints, "类型注释中应该包含 first_start_time"
    assert type_hints['first_start_time'] == 'datetime', f"first_start_time 类型注释应该是 'datetime'，实际是 {type_hints['first_start_time']}"


def test_first_start_time_reload_with_type_hints():
    """验证从 YAML 重新加载时根据类型注释转换类型"""
    test_time = datetime(2025, 1, 7, 18, 15, 20)
    config = get_config_manager(test_mode=True, first_start_time=test_time)
    config.save()
    
    # 手动清理内存中的配置管理器实例
    from config_manager.config_manager import ConfigManager
    if hasattr(ConfigManager, '_instances'):
        ConfigManager._instances.clear()
    
    # 重新加载配置
    new_config = get_config_manager(test_mode=True)
    
    print(f"重新加载后 first_start_time 类型: {type(new_config.first_start_time)}")
    print(f"重新加载后 first_start_time 值: {new_config.first_start_time}")
    
    # 验证从 YAML 加载的时间类型
    assert isinstance(new_config.first_start_time, datetime), f"从 YAML 加载的 first_start_time 应该是 datetime 对象，实际是 {type(new_config.first_start_time)}"
    
    # 验证时间值是否正确
    assert new_config.first_start_time == test_time, f"从 YAML 加载的时间值不正确: {new_config.first_start_time} != {test_time}"


def test_first_start_time_string_conversion():
    """验证 first_start_time 字符串转换功能"""
    # 测试传入字符串格式的时间
    time_str = "2025-01-07T18:15:20"
    config = get_config_manager(test_mode=True, first_start_time=time_str)
    
    # 验证应该被自动转换为 datetime 对象
    assert isinstance(config.first_start_time, datetime), f"字符串时间应该被转换为 datetime 对象，实际是 {type(config.first_start_time)}"
    
    # 验证时间值是否正确
    expected_time = datetime.fromisoformat(time_str)
    assert config.first_start_time == expected_time, f"转换后的时间值不正确: {config.first_start_time} != {expected_time}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])