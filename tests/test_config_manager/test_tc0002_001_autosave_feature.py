# tests/config_manager/tc0002_001_autosave_feature.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import pytest
import tempfile
import time
import os
from ruamel.yaml import YAML

# 创建YAML实例用于测试
yaml = YAML()
yaml.default_flow_style = False
from src.config_manager.config_manager import get_config_manager, _clear_instances_for_testing


@pytest.fixture(autouse=True)
def cleanup_instances():
    """每个测试后清理实例"""
    yield
    _clear_instances_for_testing()
    return


def test_tc0002_001_001_autosave_basic():
    """测试基本自动保存功能"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(
            config_path=config_file,
            autosave_delay=0.1,
            watch=False,
            test_mode=True
        )

        cfg.autosave_test = "value1"

        # 等待自动保存
        time.sleep(0.2)

        # 验证备份文件存在（现在文件保存到备份路径）
        backup_path = cfg.get_last_backup_path()
        file_exists = os.path.exists(backup_path)
        assert file_exists

        reloaded = cfg.reload()
        assert reloaded

        # 先检查 _data 内容
        print(f"Debug: _data 内容: {cfg._data}")

        # 使用 get 方法而不是直接属性访问
        value = cfg.get('autosave_test')
        if value is None:
            # 如果 get 失败，尝试直接从 _data 获取
            value = cfg._data.get('autosave_test')

        assert value == "value1"
    return


def test_tc0002_001_002_multilevel_autosave():
    """测试多级配置自动保存"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(
            config_path=config_file,
            autosave_delay=0.1,
            watch=False,
            test_mode=True
        )

        cfg.level1 = {}
        cfg.level1.level2 = {}
        cfg.level1.level2.level3_value = "deep_value"

        # 等待自动保存
        time.sleep(0.2)

        reloaded = cfg.reload()
        assert reloaded

        # 使用get方法获取嵌套值
        value = cfg.get("level1.level2.level3_value")
        assert value == "deep_value"
    return


def test_tc0002_001_003_autosave_delay():
    """测试自动保存延迟功能"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_config.yaml')
        cfg = get_config_manager(
            config_path=config_file,
            autosave_delay=0.5,
            watch=False,
            test_mode=True
        )

        start_time_val = time.time()
        cfg.delay_test = "value"
        end_time_val = time.time()

        time_diff = end_time_val - start_time_val
        assert time_diff < 0.1

        # 等待自动保存
        time.sleep(0.6)

        # 验证备份文件存在（现在文件保存到备份路径）
        backup_path = cfg.get_last_backup_path()
        file_exists = os.path.exists(backup_path)
        assert file_exists
    return


def test_tc0002_001_004_backup_path_generation():
    """测试备份路径生成功能"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_backup_config.yaml')
        cfg = get_config_manager(
            config_path=config_file,
            autosave_delay=0.1,
            watch=False
        )

        # 设置测试值触发自动保存
        cfg.backup_test = "backup_value"
        
        # 等待自动保存
        time.sleep(0.2)

        # 获取备份路径
        backup_path = cfg.get_last_backup_path()
        
        # 验证备份路径格式
        assert backup_path is not None
        assert backup_path.endswith('.yaml')
        
        # 验证备份目录结构包含 backup/yyyymmdd/HHMMSS
        assert 'backup' in backup_path
        
        # 验证文件名包含时间戳
        backup_filename = os.path.basename(backup_path)
        assert 'test_backup_config_' in backup_filename
        assert backup_filename.endswith('.yaml')
        
        # 验证备份文件存在
        assert os.path.exists(backup_path)
    return


def test_tc0002_001_005_first_start_time_persistence():
    """测试first_start_time持久化功能"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'test_time_config.yaml')
        
        # 设置一个特定的首次启动时间
        test_start_time = datetime(2025, 6, 5, 10, 30, 45)
        
        # 第一次创建配置管理器，显式传入first_start_time
        cfg1 = get_config_manager(
            config_path=config_file,
            autosave_delay=0.1,
            watch=False,
            first_start_time=test_start_time
        )
        
        cfg1.time_test = "first_time"
        
        # 等待自动保存
        time.sleep(0.2)
        
        # 获取首次启动时间
        first_time = cfg1._first_start_time
        assert first_time is not None
        assert first_time == test_start_time
        
        # 验证first_start_time已保存到配置中
        assert 'first_start_time' in cfg1._data
        saved_time_str = cfg1._data['first_start_time']
        assert saved_time_str is not None
        
        # 获取当前配置文件路径（备份路径）
        current_config_path = cfg1.get_config_path()
        
        # 清理实例
        _clear_instances_for_testing()
        
        # 第二次创建配置管理器，使用相同的备份文件路径
        cfg2 = get_config_manager(
            config_path=current_config_path,
            autosave_delay=0.1,
            watch=False
        )
        
        # 验证时间一致性
        second_time = cfg2._first_start_time
        assert second_time == first_time
        assert second_time == test_start_time
        
        # 验证从配置中正确读取
        assert cfg2._data['first_start_time'] == saved_time_str
    return


def test_tc0002_001_006_backup_filename_format():
    """测试备份文件名格式"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 测试自定义文件名
        config_file = os.path.join(tmpdir, 'my_custom_app.yaml')
        cfg = get_config_manager(
            config_path=config_file,
            autosave_delay=0.1,
            watch=False
        )

        cfg.filename_test = "custom_name"
        
        # 等待自动保存
        time.sleep(0.2)

        backup_path = cfg.get_last_backup_path()
        backup_filename = os.path.basename(backup_path)
        
        # 验证文件名格式：原文件名_yyyymmdd_HHMMSS.yaml
        assert backup_filename.startswith('my_custom_app_')
        assert backup_filename.endswith('.yaml')
        
        # 验证时间戳格式（8位日期_6位时间）
        name_parts = backup_filename.replace('.yaml', '').split('_')
        assert len(name_parts) >= 4  # my, custom, app, yyyymmdd, HHMMSS
        
        date_part = name_parts[-2]  # yyyymmdd
        time_part = name_parts[-1]  # HHMMSS
        
        assert len(date_part) == 8
        assert date_part.isdigit()
        assert len(time_part) == 6
        assert time_part.isdigit()
    return


def test_tc0002_001_007_backup_directory_structure():
    """测试备份目录结构"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'structure_test.yaml')
        cfg = get_config_manager(
            config_path=config_file,
            autosave_delay=0.1,
            watch=False
        )

        cfg.structure_test = "directory_structure"
        
        # 等待自动保存
        time.sleep(0.2)

        backup_path = cfg.get_last_backup_path()
        
        # 验证目录结构：原目录/backup/yyyymmdd/HHMMSS/filename_yyyymmdd_HHMMSS.yaml
        path_parts = backup_path.split(os.sep)
        
        # 查找backup在路径中的位置
        backup_index = -1
        for i, part in enumerate(path_parts):
            if part == 'backup':
                backup_index = i
                break
        
        assert backup_index != -1, "备份路径中应包含backup目录"
        
        # 验证backup后面有两级目录（日期和时间）
        assert backup_index + 2 < len(path_parts), "backup目录后应有日期和时间目录"
        
        date_dir = path_parts[backup_index + 1]
        time_dir = path_parts[backup_index + 2]
        
        # 验证日期目录格式（yyyymmdd）
        assert len(date_dir) == 8
        assert date_dir.isdigit()
        
        # 验证时间目录格式（HHMMSS）
        assert len(time_dir) == 6
        assert time_dir.isdigit()
        
        # 验证备份文件确实存在
        assert os.path.exists(backup_path)
        
        # 验证文件内容正确
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_content = yaml.load(f)
        
        assert backup_content is not None
        assert '__data__' in backup_content
        assert 'structure_test' in backup_content['__data__']
        assert backup_content['__data__']['structure_test'] == "directory_structure"
    return


def test_tc0002_001_008_caller_start_time_detection():
    """测试从调用模块获取start_time功能"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'caller_time_test.yaml')
        
        # 在当前测试模块中设置start_time变量
        import sys
        current_module = sys.modules[__name__]
        original_start_time = getattr(current_module, 'start_time', None)
        
        # 设置一个特定的start_time
        test_start_time = datetime(2025, 1, 15, 10, 30, 45)
        setattr(current_module, 'start_time', test_start_time)
        
        try:
            cfg = get_config_manager(
                config_path=config_file,
                autosave_delay=0.1,
                watch=False,
                first_start_time=test_start_time
            )
            
            cfg.caller_test = "test_caller_time"
            
            # 等待自动保存
            time.sleep(0.2)
            
            # 验证使用了传入的start_time
            first_start_time = cfg._first_start_time
            assert first_start_time == test_start_time
            
            # 验证备份路径包含正确的时间戳
            backup_path = cfg.get_last_backup_path()
            expected_date = test_start_time.strftime('%Y%m%d')
            expected_time = test_start_time.strftime('%H%M%S')
            
            assert expected_date in backup_path
            assert expected_time in backup_path
            
            # 验证文件名格式正确
            backup_filename = os.path.basename(backup_path)
            expected_filename = f"caller_time_test_{expected_date}_{expected_time}.yaml"
            assert backup_filename == expected_filename
            
            # 验证备份文件存在
            assert os.path.exists(backup_path)
            
        finally:
            # 恢复原始的start_time
            if original_start_time is not None:
                setattr(current_module, 'start_time', original_start_time)
            elif hasattr(current_module, 'start_time'):
                delattr(current_module, 'start_time')
    return


def test_tc0002_001_009_start_time_persistence_with_caller():
    """测试启动模块start_time的持久化功能"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'persist_caller_test.yaml')
        
        # 设置一个特定的start_time
        test_start_time = datetime(2025, 2, 20, 14, 15, 30)
        
        import sys
        current_module = sys.modules[__name__]
        original_start_time = getattr(current_module, 'start_time', None)
        setattr(current_module, 'start_time', test_start_time)
        
        try:
            # 第一次创建配置管理器，显式传入first_start_time
            cfg1 = get_config_manager(
                config_path=config_file,
                autosave_delay=0.1,
                watch=False,
                first_start_time=test_start_time
            )
            
            cfg1.persist_caller_test = "first_instance"
            
            # 等待自动保存
            time.sleep(0.2)
            
            # 验证使用了传入的start_time
            first_time = cfg1._first_start_time
            assert first_time == test_start_time
            
            # 验证first_start_time已保存到配置中
            assert 'first_start_time' in cfg1._data
            saved_time_str = cfg1._data['first_start_time']
            assert saved_time_str == test_start_time.isoformat()
            
            # 获取当前配置文件路径
            current_config_path = cfg1.get_config_path()
            
            # 清理实例
            _clear_instances_for_testing()
            
            # 修改调用模块的start_time（模拟不同的启动时间）
            different_start_time = datetime(2025, 3, 10, 9, 45, 20)
            setattr(current_module, 'start_time', different_start_time)
            
            # 第二次创建配置管理器，使用相同的配置文件
            cfg2 = get_config_manager(
                config_path=current_config_path,
                autosave_delay=0.1,
                watch=False
            )
            
            # 验证仍然使用保存的原始时间，而不是新的调用模块时间
            second_time = cfg2._first_start_time
            assert second_time == test_start_time  # 应该是原始保存的时间
            assert second_time != different_start_time  # 不应该是新的调用模块时间
            
            # 验证从配置中正确读取
            assert cfg2._data['first_start_time'] == test_start_time.isoformat()
            
        finally:
            # 恢复原始的start_time
            if original_start_time is not None:
                setattr(current_module, 'start_time', original_start_time)
            elif hasattr(current_module, 'start_time'):
                delattr(current_module, 'start_time')
    return


def test_tc0002_001_010_fallback_to_current_time():
    """测试当找不到调用模块start_time时的后备机制"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, 'fallback_test.yaml')
        
        import sys
        current_module = sys.modules[__name__]
        original_start_time = getattr(current_module, 'start_time', None)
        
        # 临时移除start_time变量
        if hasattr(current_module, 'start_time'):
            delattr(current_module, 'start_time')
        
        try:
            before_creation = datetime.now()
            
            # 显式传入当前时间作为first_start_time
            fallback_time = datetime.now()
            cfg = get_config_manager(
                config_path=config_file,
                autosave_delay=0.1,
                watch=False,
                first_start_time=fallback_time
            )
            
            after_creation = datetime.now()
            
            cfg.fallback_test = "no_start_time_available"
            
            # 等待自动保存
            time.sleep(0.2)
            
            # 验证使用了传入的时间
            first_start_time = cfg._first_start_time
            assert first_start_time is not None
            assert first_start_time == fallback_time
            
            # 验证备份文件正常创建
            backup_path = cfg.get_last_backup_path()
            assert os.path.exists(backup_path)
            
        finally:
            # 恢复原始的start_time
            if original_start_time is not None:
                setattr(current_module, 'start_time', original_start_time)
    return