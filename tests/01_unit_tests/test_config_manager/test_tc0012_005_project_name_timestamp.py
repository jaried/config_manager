# tests/01_unit_tests/test_config_manager/test_tc0012_005_project_name_timestamp.py
from __future__ import annotations
from datetime import datetime
import os
import tempfile
import pytest
from src.config_manager import get_config_manager, _clear_instances_for_testing


class TestTC0012005ProjectNameTimestamp:
    """测试project_name和first_start_time的正确使用"""

    def setup_method(self):
        """每个测试前的设置"""
        _clear_instances_for_testing()

    def teardown_method(self):
        """每个测试后的清理"""
        _clear_instances_for_testing()

    def test_tc0012_005_001_project_name_from_config(self):
        """测试从配置文件中读取project_name"""
        # 使用生产环境配置管理器，应该读取到config_manager
        cfg = get_config_manager()
        
        # 验证project_name被正确读取
        project_name = cfg.get('project_name')
        assert project_name == 'config_manager', f"期望project_name为'config_manager'，实际: {project_name}"
        
        print(f"✓ 生产环境project_name: {project_name}")

    def test_tc0012_005_002_test_mode_path_with_project_name(self):
        """测试test_mode下路径包含project_name"""
        fixed_time = datetime(2025, 1, 7, 15, 30, 45)
        
        # 创建测试模式配置管理器
        cfg = get_config_manager(test_mode=True, first_start_time=fixed_time)
        test_path = cfg.get_config_file_path()
        
        # 验证路径包含project_name
        assert 'config_manager' in test_path, f"测试路径应包含project_name 'config_manager': {test_path}"
        
        # 验证路径包含正确的时间戳
        assert '20250107' in test_path, f"测试路径应包含日期20250107: {test_path}"
        assert '153045' in test_path, f"测试路径应包含时间153045: {test_path}"
        
        # 验证路径格式：/temp/tests/YYYYMMDD/HHMMSS/project_name/src/config/config.yaml
        temp_base = tempfile.mkdtemp(prefix="test_project_")
        expected_pattern = os.path.join(temp_base, 'tests', '20250107', '153045', 'config_manager', 'src', 'config', 'config.yaml')
        assert test_path == expected_pattern, f"路径格式不正确，期望: {expected_pattern}，实际: {test_path}"
        
        print(f"✓ 测试环境路径: {test_path}")

    def test_tc0012_005_003_test_config_contains_project_name(self):
        """测试测试配置文件包含project_name"""
        fixed_time = datetime(2025, 1, 7, 16, 45, 30)
        
        # 创建测试模式配置管理器
        cfg = get_config_manager(test_mode=True, first_start_time=fixed_time)
        
        # 验证测试配置中包含project_name
        project_name = cfg.get('project_name')
        assert project_name == 'config_manager', f"测试配置中的project_name应为'config_manager'，实际: {project_name}"
        
        # 验证first_start_time被正确设置
        first_start_time = cfg.get('first_start_time')
        assert first_start_time == '2025-01-07T16:45:30', f"first_start_time应为'2025-01-07T16:45:30'，实际: {first_start_time}"
        
        print(f"✓ 测试配置project_name: {project_name}")
        print(f"✓ 测试配置first_start_time: {first_start_time}")

    def test_tc0012_005_004_first_start_time_priority(self):
        """测试first_start_time的优先级：传入参数 > 配置文件 > 当前时间"""
        # 传入参数优先级最高
        param_time = datetime(2025, 1, 7, 10, 0, 0)
        cfg1 = get_config_manager(test_mode=True, first_start_time=param_time)
        
        # 验证使用了传入的时间
        first_start_time1 = cfg1.get('first_start_time')
        assert first_start_time1 == '2025-01-07T10:00:00', f"应使用传入的first_start_time，实际: {first_start_time1}"
        
        # 验证路径包含传入的时间戳
        test_path1 = cfg1.get_config_file_path()
        assert '20250107' in test_path1 and '100000' in test_path1, f"路径应包含传入的时间戳: {test_path1}"
        
        print(f"✓ 传入参数优先级验证通过: {first_start_time1}")
        
        # 清理实例
        _clear_instances_for_testing()
        
        # 配置文件中的时间优先级次之（当前配置文件中有first_start_time）
        cfg2 = get_config_manager(test_mode=True)  # 不传入first_start_time
        
        # 验证使用了配置文件中的时间
        first_start_time2 = cfg2.get('first_start_time')
        assert first_start_time2 == '2025-01-07T10:00:00', f"应使用配置文件中的first_start_time，实际: {first_start_time2}"
        
        print(f"✓ 配置文件优先级验证通过: {first_start_time2}")

    def test_tc0012_005_005_default_project_name(self):
        """测试默认project_name的使用"""
        # 创建一个临时配置文件，不包含project_name
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
__data__:
  app_name: "测试应用"
  first_start_time: "2025-01-07T12:00:00"
__type_hints__: {}
""")
            temp_config_path = f.name
        
        try:
            # 使用临时配置文件创建测试模式配置管理器
            cfg = get_config_manager(config_path=temp_config_path, test_mode=True)
            test_path = cfg.get_config_file_path()
            
            # 验证使用了默认的project_name
            assert 'project_name' in test_path, f"应使用默认project_name 'project_name': {test_path}"
            
            # 验证测试配置中包含默认project_name
            project_name = cfg.get('project_name')
            assert project_name == 'project_name', f"应使用默认project_name 'project_name'，实际: {project_name}"
            
            print(f"✓ 默认project_name验证通过: {project_name}")
            print(f"✓ 默认project_name路径: {test_path}")
            
        finally:
            # 清理临时文件
            assert temp_config_path.startswith(tempfile.gettempdir()), f"禁止删除非临时文件: {temp_config_path}"
            os.unlink(temp_config_path)

    def test_tc0012_005_006_timestamp_consistency(self):
        """测试相同first_start_time生成一致的时间戳路径"""
        fixed_time = datetime(2025, 1, 7, 14, 25, 50)
        
        # 创建第一个实例
        cfg1 = get_config_manager(test_mode=True, first_start_time=fixed_time)
        path1 = cfg1.get_config_file_path()
        
        # 清理实例缓存
        _clear_instances_for_testing()
        
        # 创建第二个实例（相同的first_start_time）
        cfg2 = get_config_manager(test_mode=True, first_start_time=fixed_time)
        path2 = cfg2.get_config_file_path()
        
        # 验证路径的时间戳部分相同
        assert '20250107' in path1 and '20250107' in path2, "日期部分应该相同"
        assert '142550' in path1 and '142550' in path2, "时间部分应该相同"
        assert 'config_manager' in path1 and 'config_manager' in path2, "project_name部分应该相同"
        
        # 验证完整路径相同
        assert path1 == path2, f"相同first_start_time应生成相同路径，路径1: {path1}，路径2: {path2}"
        
        print(f"✓ 时间戳一致性验证通过")
        print(f"✓ 路径1: {path1}")
        print(f"✓ 路径2: {path2}")

    def test_tc0012_005_007_work_dir_with_project_name(self):
        """测试work_dir等路径字段包含project_name"""
        fixed_time = datetime(2025, 1, 7, 18, 15, 20)
        
        # 创建测试模式配置管理器
        cfg = get_config_manager(test_mode=True, first_start_time=fixed_time)
        
        # 获取各种路径字段
        base_dir = cfg.get('base_dir', '')
        work_dir = cfg.get('work_dir', '')
        
        # 验证路径包含project_name
        temp_base = tempfile.mkdtemp(prefix="test_work_dir_")
        expected_base = os.path.join(temp_base, 'tests', '20250107', '181520', 'config_manager')
        
        assert base_dir == expected_base, f"base_dir应为{expected_base}，实际: {base_dir}"
        assert work_dir == expected_base, f"work_dir应为{expected_base}，实际: {work_dir}"
        
        print(f"✓ base_dir: {base_dir}")
        print(f"✓ work_dir: {work_dir}") 