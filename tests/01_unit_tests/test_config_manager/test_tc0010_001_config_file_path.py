# tests/01_unit_tests/test_config_manager/test_tc0010_001_config_file_path.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import os
import sys
import time
from ruamel.yaml import YAML

# 创建YAML实例用于测试
yaml = YAML()
yaml.default_flow_style = False

# 添加src到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from config_manager import get_config_manager
from config_manager.config_manager import _clear_instances_for_testing


@pytest.fixture(autouse=True)
def cleanup_instances():
    """每个测试后清理实例"""
    yield
    _clear_instances_for_testing()
    return



class TestConfigFilePath:
    """测试配置文件路径功能"""

    def test_tc0010_001_001_config_file_path_storage(self):
        """测试配置文件路径存储功能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'test_config.yaml')
            
            # 创建配置管理器
            cfg = get_config_manager(
                config_path=config_file,
                auto_create=True,
                autosave_delay=0.1,
                first_start_time=start_time
            )
            
            # 设置一些配置值
            cfg.test_value = "path_storage_test"
            time.sleep(0.2)  # 等待自动保存
            
            # 验证配置文件路径被正确存储
            stored_path = cfg._data.get('config_file_path')
            retrieved_path = cfg.get_config_file_path()
            actual_path = cfg.get_config_path()
            
            assert stored_path is not None, "配置文件路径应该被存储"
            assert stored_path == config_file, f"存储的路径应该匹配，期望: {config_file}, 实际: {stored_path}"
            assert retrieved_path == config_file, f"检索的路径应该匹配，期望: {config_file}, 实际: {retrieved_path}"
            assert actual_path == config_file, f"实际路径应该匹配，期望: {config_file}, 实际: {actual_path}"
            
            # 验证路径信息在重载后仍然存在
            cfg.reload()
            reloaded_path = cfg.get_config_file_path()
            assert reloaded_path == config_file, f"重载后路径应该保持一致，期望: {config_file}, 实际: {reloaded_path}"
            
            print("✓ 配置文件路径存储功能正常")
        return

    def test_tc0010_001_002_config_file_path_default(self):
        """测试默认配置路径的存储"""
        # 使用默认路径
        cfg = get_config_manager(first_start_time=start_time)
        
        # 获取路径信息
        stored_path = cfg._data.get('config_file_path')
        retrieved_path = cfg.get_config_file_path()
        actual_path = cfg.get_config_path()
        
        assert stored_path is not None, "默认配置文件路径应该被存储"
        assert stored_path == actual_path, "存储的路径应该与实际路径匹配"
        assert retrieved_path == actual_path, "检索的路径应该与实际路径匹配"
        assert stored_path.endswith('.yaml'), "配置文件应该是yaml格式"
        
        print(f"✓ 默认配置路径存储正常: {stored_path}")
        return

    def test_tc0010_001_003_config_file_path_persistence(self):
        """测试配置文件路径的持久性"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'persistent_config.yaml')
            
            # 第一次创建配置
            cfg1 = get_config_manager(
                config_path=config_file,
                auto_create=True,
                autosave_delay=0.1,
                first_start_time=start_time
            )
            
            cfg1.persistent_test = "first_value"
            cfg1.test_data = {"key1": "value1", "key2": 42}
            time.sleep(0.2)  # 等待自动保存
            
            # 验证路径被保存到文件中
            first_path = cfg1.get_config_file_path()
            assert first_path == config_file
            
            # 清理实例缓存
            _clear_instances_for_testing()
            
            # 创建新的配置管理器实例（模拟重启）
            cfg2 = get_config_manager(
                config_path=config_file,
                auto_create=False,
                autosave_delay=0.1
            )
            
            # 验证路径信息被正确加载
            second_path = cfg2.get_config_file_path()
            assert second_path == config_file, f"重新加载后路径应该一致，期望: {config_file}, 实际: {second_path}"
            assert cfg2.persistent_test == "first_value", "配置值应该被正确加载"
            assert cfg2.test_data.key1 == "value1", "嵌套配置值应该被正确加载"
            assert cfg2.test_data.key2 == 42, "数值配置应该被正确加载"
            
            print("✓ 配置文件路径持久性功能正常")
        return

    def test_tc0010_001_004_config_file_path_attribute_access(self):
        """测试配置文件路径的属性访问方式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'attribute_test.yaml')
            
            cfg = get_config_manager(
                config_path=config_file,
                auto_create=True,
                autosave_delay=0.1,
                first_start_time=start_time
            )
            
            # 通过方法访问
            method_path = cfg.get_config_file_path()
            
            # 通过属性访问
            attribute_path = cfg.config_file_path
            
            # 验证两种访问方式结果一致
            assert method_path == attribute_path, f"方法访问和属性访问应该一致，方法: {method_path}, 属性: {attribute_path}"
            assert method_path == config_file, f"路径应该匹配，期望: {config_file}, 实际: {method_path}"
            
            print("✓ 配置文件路径属性访问功能正常")
        return

    def test_tc0010_001_005_config_file_path_with_relative_path(self):
        """测试相对路径的配置文件路径处理"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 切换到临时目录
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                relative_config_file = 'relative_config.yaml'
                expected_absolute_path = os.path.join(tmpdir, relative_config_file)
                
                cfg = get_config_manager(
                    config_path=relative_config_file,
                    auto_create=True,
                    autosave_delay=0.1,
                    first_start_time=start_time
                )
                
                cfg.relative_test = "relative_path_test"
                time.sleep(0.2)  # 等待自动保存
                
                # 验证存储的是绝对路径
                stored_path = cfg.get_config_file_path()
                assert os.path.isabs(stored_path), f"存储的路径应该是绝对路径: {stored_path}"
                assert stored_path == expected_absolute_path, f"绝对路径应该正确，期望: {expected_absolute_path}, 实际: {stored_path}"
                
                print("✓ 相对路径转换为绝对路径功能正常")
                
            finally:
                # 恢复原始工作目录
                os.chdir(original_cwd)
        return

    def test_tc0010_001_006_config_file_path_consistency_after_operations(self):
        """测试各种操作后配置文件路径的一致性"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'consistency_test.yaml')
            
            cfg = get_config_manager(
                config_path=config_file,
                auto_create=True,
                autosave_delay=0.1,
                first_start_time=start_time
            )
            
            # 初始路径
            initial_path = cfg.get_config_file_path()
            assert initial_path == config_file
            
            # 设置配置值后
            cfg.consistency_test = "test_value"
            after_set_path = cfg.get_config_file_path()
            assert after_set_path == config_file, "设置配置值后路径应该保持一致"
            
            # 手动保存后
            cfg.save()
            after_save_path = cfg.get_config_file_path()
            assert after_save_path == config_file, "手动保存后路径应该保持一致"
            
            # 重载后
            cfg.reload()
            after_reload_path = cfg.get_config_file_path()
            assert after_reload_path == config_file, "重载后路径应该保持一致"
            
            # 批量更新后
            cfg.update({
                "batch_test": "batch_value",
                "nested": {"key": "value"}
            })
            after_update_path = cfg.get_config_file_path()
            assert after_update_path == config_file, "批量更新后路径应该保持一致"
            
            # 使用快照和恢复后
            snapshot = cfg.snapshot()
            cfg.temp_value = "temporary"
            cfg.restore(snapshot)
            after_restore_path = cfg.get_config_file_path()
            assert after_restore_path == config_file, "快照恢复后路径应该保持一致"
            
            print("✓ 各种操作后配置文件路径一致性正常")
        return

    def test_tc0010_001_007_config_file_path_in_yaml_structure(self):
        """测试配置文件路径在YAML文件中的存储结构"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'yaml_structure_test.yaml')
            
            cfg = get_config_manager(
                config_path=config_file,
                auto_create=True,
                autosave_delay=0.1,
                first_start_time=start_time
            )
            
            cfg.yaml_test = "structure_test"
            cfg.nested_data = {
                "level1": {
                    "level2": "deep_value"
                }
            }
            time.sleep(0.2)  # 等待自动保存
            
            # 直接读取YAML文件验证结构
            with open(config_file, 'r', encoding='utf-8') as f:
                yaml_content = yaml.load(f)
            
            # 验证YAML文件结构
            assert '__data__' in yaml_content, "YAML文件应该包含__data__节点"
            data_section = yaml_content['__data__']
            
            assert 'config_file_path' in data_section, "数据节点应该包含config_file_path字段"
            assert data_section['config_file_path'] == config_file, "YAML中的路径应该正确"
            
            # 验证用户数据也正确存储
            assert 'yaml_test' in data_section, "用户配置应该正确存储"
            assert data_section['yaml_test'] == "structure_test"
            assert 'nested_data' in data_section, "嵌套配置应该正确存储"
            
            print("✓ 配置文件路径在YAML文件中的存储结构正常")
        return

    def test_tc0010_001_008_config_file_path_error_handling(self):
        """测试配置文件路径功能的错误处理"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'error_handling_test.yaml')
            
            cfg = get_config_manager(
                config_path=config_file,
                auto_create=True,
                autosave_delay=0.1,
                first_start_time=start_time
            )
            
            # 正常情况
            normal_path = cfg.get_config_file_path()
            assert normal_path == config_file
            
            # 模拟配置数据中路径字段丢失的情况
            original_path = cfg._data.get('config_file_path')
            del cfg._data['config_file_path']
            
            # 验证回退机制
            fallback_path = cfg.get_config_file_path()
            assert fallback_path == cfg._config_path, "路径字段丢失时应该回退到内部路径"
            
            # 恢复路径字段
            cfg._data['config_file_path'] = original_path
            restored_path = cfg.get_config_file_path()
            assert restored_path == config_file, "恢复路径字段后应该正常工作"
            
            print("✓ 配置文件路径错误处理功能正常")
        return


if __name__ == "__main__":
    # 运行所有测试
    test_instance = TestConfigFilePath()
    
    test_methods = [
        test_instance.test_tc0010_001_001_config_file_path_storage,
        test_instance.test_tc0010_001_002_config_file_path_default,
        test_instance.test_tc0010_001_003_config_file_path_persistence,
        test_instance.test_tc0010_001_004_config_file_path_attribute_access,
        test_instance.test_tc0010_001_005_config_file_path_with_relative_path,
        test_instance.test_tc0010_001_006_config_file_path_consistency_after_operations,
        test_instance.test_tc0010_001_007_config_file_path_in_yaml_structure,
        test_instance.test_tc0010_001_008_config_file_path_error_handling,
    ]
    
    print("开始运行配置文件路径功能测试...")
    print("=" * 60)
    
    for i, test_method in enumerate(test_methods, 1):
        try:
            print(f"\n{i}. 运行 {test_method.__name__}")
            test_method()
            print(f"   ✓ 测试通过")
        except Exception as e:
            print(f"   ✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("所有测试完成！") 