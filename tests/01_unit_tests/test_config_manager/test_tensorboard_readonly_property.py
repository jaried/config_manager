# tests/01_unit_tests/test_config_manager/test_tensorboard_readonly_property.py
from __future__ import annotations
from datetime import datetime
import pytest

from config_manager import get_config_manager
from config_manager.core.dynamic_paths import PathsConfigNode, TensorBoardDirDescriptor


class TestTensorBoardReadOnlyProperty:
    """测试tensorboard_dir的只读特性"""
    
    def test_tensorboard_dir_cannot_be_set(self):
        """测试无法设置tensorboard_dir属性"""
        config = get_config_manager(
            test_mode=True,
            auto_create=True
        )
        
        try:
            # 尝试各种方式设置tensorboard_dir
            with pytest.raises(AttributeError) as exc_info:
                config.paths.tensorboard_dir = "/custom/tensorboard/path"
            
            assert "只读属性" in str(exc_info.value), (
                f"错误消息应包含'只读属性'，实际：{exc_info.value}"
            )
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_tensorboard_descriptor_set_raises_error(self):
        """测试TensorBoardDirDescriptor的__set__方法总是抛出错误"""
        # 创建一个PathsConfigNode实例
        paths_node = PathsConfigNode({'work_dir': '/test'})
        descriptor = TensorBoardDirDescriptor()
        
        # 测试描述符的__set__方法
        with pytest.raises(AttributeError) as exc_info:
            descriptor.__set__(paths_node, "/any/value")
        
        assert "只读属性" in str(exc_info.value)
        assert "自动等于tsb_logs_dir" in str(exc_info.value)
    
    def test_tensorboard_dir_always_equals_tsb_logs_dir(self):
        """测试tensorboard_dir始终等于tsb_logs_dir"""
        config = get_config_manager(
            test_mode=True,
            auto_create=True,
            first_start_time=datetime(2025, 1, 8, 15, 30, 45)
        )
        
        try:
            # 多次访问，验证相等性
            for _ in range(5):
                tsb_dir = config.paths.tsb_logs_dir
                tb_dir = config.paths.tensorboard_dir
                assert tb_dir == tsb_dir, (
                    f"tensorboard_dir应该等于tsb_logs_dir\n"
                    f"tsb_logs_dir: {tsb_dir}\n"
                    f"tensorboard_dir: {tb_dir}"
                )
            
            # 修改work_dir后验证
            original_work_dir = config.paths.work_dir
            config.paths.work_dir = "/modified/work/dir"
            
            # 等待缓存过期
            import time
            time.sleep(1.1)
            
            # 再次验证相等性
            new_tsb_dir = config.paths.tsb_logs_dir
            new_tb_dir = config.paths.tensorboard_dir
            assert new_tb_dir == new_tsb_dir, (
                "修改work_dir后，tensorboard_dir仍应等于tsb_logs_dir"
            )
            assert "/modified/work/dir" in new_tb_dir, (
                "新路径应反映work_dir的变化"
            )
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_tensorboard_dir_descriptor_get_method(self):
        """测试TensorBoardDirDescriptor的__get__方法"""
        # 创建测试数据
        config = get_config_manager(
            test_mode=True,
            auto_create=True
        )
        
        try:
            paths_node = config.paths
            descriptor = TensorBoardDirDescriptor()
            
            # 直接调用描述符的__get__方法
            result = descriptor.__get__(paths_node, type(paths_node))
            
            # 验证返回值等于tsb_logs_dir
            assert result == paths_node.tsb_logs_dir, (
                "描述符__get__应返回tsb_logs_dir的值"
            )
            
            # 测试当obj为None时的行为
            result_none = descriptor.__get__(None, type(paths_node))
            assert result_none is descriptor, (
                "当obj为None时，应返回描述符自身"
            )
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_readonly_property_in_different_access_methods(self):
        """测试通过不同方式访问时的只读特性"""
        config = get_config_manager(
            test_mode=True,
            auto_create=True
        )
        
        try:
            # 1. 通过属性访问设置
            with pytest.raises(AttributeError):
                config.paths.tensorboard_dir = "/path1"
            
            # 2. 通过setattr设置
            with pytest.raises(AttributeError):
                setattr(config.paths, 'tensorboard_dir', "/path2")
            
            # 3. 尝试通过__setattr__直接调用
            with pytest.raises(AttributeError):
                config.paths.__setattr__('tensorboard_dir', "/path3")
            
            # 4. 验证可以正常读取
            tb_dir = config.paths.tensorboard_dir
            assert isinstance(tb_dir, str), "应该能正常读取tensorboard_dir"
            assert "/tsb_logs/" in tb_dir, "路径应包含tsb_logs"
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_tensorboard_dir_in_contains_check(self):
        """测试tensorboard_dir在包含性检查中的行为"""
        config = get_config_manager(
            test_mode=True,
            auto_create=True
        )
        
        try:
            # 验证tensorboard_dir在paths中
            assert 'tensorboard_dir' in config.paths, (
                "tensorboard_dir应该在paths中可检测到"
            )
            
            # 验证tsb_logs_dir也在paths中
            assert 'tsb_logs_dir' in config.paths, (
                "tsb_logs_dir应该在paths中可检测到"
            )
            
            # 验证通过get方法访问
            tb_dir_get = config.paths.get('tensorboard_dir')
            tsb_dir_get = config.paths.get('tsb_logs_dir')
            assert tb_dir_get == tsb_dir_get, (
                "通过get方法访问的值应该相等"
            )
            assert tb_dir_get is not None, (
                "get方法应该返回有效值"
            )
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_readonly_error_message_clarity(self):
        """测试只读错误消息的清晰度"""
        config = get_config_manager(
            test_mode=True,
            auto_create=True
        )
        
        try:
            # 捕获错误消息
            try:
                config.paths.tensorboard_dir = "/test/path"
            except AttributeError as e:
                error_msg = str(e)
                
                # 验证错误消息的关键信息
                assert "tensorboard_dir" in error_msg, (
                    "错误消息应包含属性名'tensorboard_dir'"
                )
                assert "只读" in error_msg, (
                    "错误消息应说明是只读属性"
                )
                assert "tsb_logs_dir" in error_msg, (
                    "错误消息应说明与tsb_logs_dir的关系"
                )
                assert "自动" in error_msg, (
                    "错误消息应说明值是自动生成的"
                )
                
                print(f"只读错误消息：{error_msg}")
            else:
                pytest.fail("设置只读属性应该抛出AttributeError")
            
        finally:
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_tensorboard_dir_persistence(self):
        """测试tensorboard_dir值的持久性"""
        # 创建配置并保存
        config1 = get_config_manager(
            test_mode=True,
            auto_create=True,
            first_start_time=datetime(2025, 1, 8, 20, 0, 0),
            autosave_delay=0.1
        )
        
        try:
            # 获取路径值
            tb_dir1 = config1.paths.tensorboard_dir
            tsb_dir1 = config1.paths.tsb_logs_dir
            config_path = config1._config_path
            
            # 触发保存
            config1.set('dummy_key', 'dummy_value')
            import time
            time.sleep(0.2)  # 等待自动保存
            
            # 创建新的配置实例，加载相同文件
            config2 = get_config_manager(
                config_path=config_path,
                test_mode=True
            )
            
            try:
                # 验证tensorboard_dir仍然等于tsb_logs_dir
                tb_dir2 = config2.paths.tensorboard_dir
                tsb_dir2 = config2.paths.tsb_logs_dir
                
                assert tb_dir2 == tsb_dir2, (
                    "重新加载后，tensorboard_dir应该仍等于tsb_logs_dir"
                )
                
                # 由于路径是动态生成的，值可能因时间变化而不同
                # 但格式应该一致
                assert "/tsb_logs/" in tb_dir2, (
                    "路径应包含tsb_logs目录"
                )
                
            finally:
                if hasattr(config2, 'cleanup'):
                    config2.cleanup()
                    
        finally:
            if hasattr(config1, 'cleanup'):
                config1.cleanup()
    
    pass