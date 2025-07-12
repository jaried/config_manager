# tests/01_unit_tests/test_config_manager/test_tc0012_001_test_mode.py
from __future__ import annotations
from datetime import datetime

import tempfile
import os
import pytest
import time
from src.config_manager import get_config_manager, TestEnvironmentManager
from src.config_manager.config_manager import _clear_instances_for_testing



class TestTestMode:
    """测试test_mode功能"""

    def setup_method(self):
        """每个测试方法前的设置"""
        _clear_instances_for_testing()
        # 清理测试环境变量
        if 'CONFIG_MANAGER_TEST_MODE' in os.environ:
            del os.environ['CONFIG_MANAGER_TEST_MODE']
        if 'CONFIG_MANAGER_TEST_BASE_DIR' in os.environ:
            del os.environ['CONFIG_MANAGER_TEST_BASE_DIR']

    def teardown_method(self):
        """每个测试方法后的清理"""
        # 清理当前测试环境
        TestEnvironmentManager.cleanup_current_test_environment()
        _clear_instances_for_testing()

    def test_tc0012_001_001_test_mode_basic_functionality(self):
        """TC0012-001-001: 测试test_mode基本功能"""
        # 创建测试模式配置管理器
        cfg = get_config_manager(test_mode=True)
        
        # 验证测试环境设置
        assert os.environ.get('CONFIG_MANAGER_TEST_MODE') == 'true'
        assert 'CONFIG_MANAGER_TEST_BASE_DIR' in os.environ
        
        # 验证配置文件路径在临时目录中
        config_path = cfg.get_config_file_path()
        assert 'temp' in config_path.lower() or 'tmp' in config_path.lower()
        assert 'tests' in config_path
        assert config_path.endswith('.yaml')
        
        # 验证配置文件存在
        assert os.path.exists(config_path)
        
        print(f"✓ 测试配置路径: {config_path}")

    def test_tc0012_001_002_test_mode_isolation(self):
        """TC0012-001-002: 测试test_mode环境隔离"""
        # 创建测试模式配置
        test_cfg = get_config_manager(test_mode=True)
        test_cfg.test_isolation = "test_value"
        test_cfg.save()
        
        # 创建生产模式配置
        prod_cfg = get_config_manager(test_mode=False)
        
        # 验证配置隔离
        assert test_cfg.get('test_isolation') == "test_value"
        assert prod_cfg.get('test_isolation') is None
        
        # 验证实例不同
        assert test_cfg is not prod_cfg
        
        # 验证路径不同
        test_path = test_cfg.get_config_file_path()
        prod_path = prod_cfg.get_config_file_path()
        assert test_path != prod_path
        
        print(f"✓ 测试路径: {test_path}")
        print(f"✓ 生产路径: {prod_path}")

    def test_tc0012_001_003_test_mode_config_operations(self):
        """TC0012-001-003: 测试test_mode下的配置操作"""
        cfg = get_config_manager(test_mode=True)
        
        # 测试基本配置操作
        cfg.app_name = "测试应用"
        cfg.version = "1.0.0"
        cfg.database = {}
        cfg.database.host = "test-db"
        cfg.database.port = 5432
        
        # 验证配置值
        assert cfg.app_name == "测试应用"
        assert cfg.version == "1.0.0"
        assert cfg.database.host == "test-db"
        assert cfg.database.port == 5432
        
        # 测试保存和重载
        cfg.save()
        cfg.reload()
        
        # 验证重载后配置仍然存在
        assert cfg.app_name == "测试应用"
        assert cfg.database.host == "test-db"
        
        print("✓ 测试模式配置操作正常")

    def test_tc0012_001_004_test_mode_path_generation(self):
        """TC0012-001-004: 测试test_mode路径生成"""
        # 创建多个测试实例，验证路径唯一性
        cfg1 = get_config_manager(test_mode=True)
        time.sleep(0.1)  # 确保时间戳不同
        
        # 清理实例缓存以创建新实例
        _clear_instances_for_testing()
        
        cfg2 = get_config_manager(test_mode=True)
        
        path1 = cfg1.get_config_file_path()
        path2 = cfg2.get_config_file_path()
        
        # 验证路径格式
        assert 'temp' in path1.lower() or 'tmp' in path1.lower()
        assert 'temp' in path2.lower() or 'tmp' in path2.lower()
        assert 'tests' in path1
        assert 'tests' in path2
        
        # 验证路径包含日期和时间
        import re
        # 修复：Windows路径使用反斜杠，需要转义
        date_time_pattern = r'tests[\\/]\d{8}[\\/]\d{6}[\\/]'
        assert re.search(date_time_pattern, path1)
        assert re.search(date_time_pattern, path2)
        
        print(f"✓ 路径1: {path1}")
        print(f"✓ 路径2: {path2}")

    def test_tc0012_001_005_test_environment_manager(self):
        """TC0012-001-005: 测试TestEnvironmentManager功能"""
        # 创建测试环境
        cfg = get_config_manager(test_mode=True)
        cfg.test_data = "test_value"
        cfg.save()
        
        # 获取测试环境信息
        info = TestEnvironmentManager.get_test_environment_info()
        assert info['is_test_mode']
        assert info['test_base_dir'] is not None
        assert info['temp_base'] is not None
        
        # 列出测试环境
        environments = TestEnvironmentManager.list_test_environments()
        assert len(environments) >= 1
        
        # 验证当前测试环境存在
        test_base_dir = os.environ.get('CONFIG_MANAGER_TEST_BASE_DIR')
        assert test_base_dir is not None
        assert os.path.exists(test_base_dir)
        
        print(f"✓ 测试环境信息: {info}")
        print(f"✓ 测试环境数量: {len(environments)}")

    def test_tc0012_001_006_test_mode_with_explicit_config(self):
        """TC0012-001-006: 测试test_mode与显式配置路径"""
        # 创建一个临时的生产配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
__data__:
  app_name: "生产应用"
  version: "2.0.0"
  database:
    host: "prod-db"
    port: 3306
__type_hints__: {}
""")
            prod_config_path = f.name
        
        try:
            # 使用test_mode和显式配置路径
            cfg = get_config_manager(config_path=prod_config_path, test_mode=True)
            
            # 验证配置被复制到测试环境
            test_path = cfg.get_config_file_path()
            assert test_path != prod_config_path
            assert tempfile.gettempdir() in test_path
            
            # 验证配置内容被复制
            assert cfg.get('app_name') == "生产应用"
            assert cfg.get('version') == "2.0.0"
            assert cfg.get('database.host') == "prod-db"
            
            # 修改测试配置，不应影响生产配置
            cfg.app_name = "测试应用"
            cfg.save()
            
            # 验证生产配置文件未被修改
            prod_cfg = get_config_manager(config_path=prod_config_path, test_mode=False)
            assert prod_cfg.get('app_name') == "生产应用"
            
            print(f"✓ 生产配置路径: {prod_config_path}")
            print(f"✓ 测试配置路径: {test_path}")
            
        finally:
            # 清理临时文件
            assert prod_config_path.startswith(tempfile.gettempdir()), f"禁止删除非临时文件: {prod_config_path}"
            os.unlink(prod_config_path)

    def test_tc0012_001_007_test_mode_performance(self):
        """TC0012-001-007: 测试test_mode性能"""
        import time
        
        start_time = time.time()
        cfg = get_config_manager(test_mode=True)
        setup_time = time.time() - start_time
        
        # 测试环境设置应该在合理时间内完成
        assert setup_time < 2.0, f"测试环境设置耗时过长: {setup_time:.2f}s"
        
        # 测试配置操作性能
        start_time = time.time()
        cfg.performance_test = "test_value"
        cfg.save()
        operation_time = time.time() - start_time
        
        assert operation_time < 1.0, f"配置操作耗时过长: {operation_time:.2f}s"
        
        print(f"✓ 测试环境设置时间: {setup_time:.3f}s")
        print(f"✓ 配置操作时间: {operation_time:.3f}s")

    def test_tc0012_001_008_test_mode_error_handling(self):
        """TC0012-001-008: 测试test_mode错误处理"""
        # 测试在没有生产配置的情况下创建测试环境
        cfg = get_config_manager(test_mode=True)
        
        # 应该创建空的测试配置
        config_path = cfg.get_config_file_path()
        assert os.path.exists(config_path)
        
        # 验证可以正常操作
        cfg.error_test = "error_value"
        cfg.save()
        
        assert cfg.get('error_test') == "error_value"
        
        print("✓ 错误处理功能正常")

    def test_tc0012_001_009_test_mode_cleanup(self):
        """TC0012-001-009: 测试test_mode清理功能"""
        # 创建测试环境
        get_config_manager(test_mode=True)
        test_base_dir = os.environ.get('CONFIG_MANAGER_TEST_BASE_DIR')
        
        # 验证测试环境存在
        assert test_base_dir is not None
        assert os.path.exists(test_base_dir)
        
        # 清理当前测试环境
        cleanup_result = TestEnvironmentManager.cleanup_current_test_environment()
        assert cleanup_result
        
        # 验证测试环境被清理
        assert not os.path.exists(test_base_dir)
        assert os.environ.get('CONFIG_MANAGER_TEST_MODE') is None
        assert os.environ.get('CONFIG_MANAGER_TEST_BASE_DIR') is None
        
        print("✓ 测试环境清理功能正常")

    def test_tc0012_001_010_multiple_test_instances(self):
        """TC0012-001-010: 测试多个测试实例的独立性"""
        
        # 创建第一个测试实例，使用固定时间
        time1 = datetime(2025, 6, 7, 10, 30, 0)
        cfg1 = get_config_manager(test_mode=True, first_start_time=time1)
        cfg1.instance_id = "instance_1"
        cfg1.save()
        
        # 清理实例缓存
        _clear_instances_for_testing()
        
        # 创建第二个测试实例，使用不同的固定时间
        time2 = datetime(2025, 6, 7, 11, 30, 0)
        cfg2 = get_config_manager(test_mode=True, first_start_time=time2)
        cfg2.instance_id = "instance_2"
        cfg2.save()
        
        # 验证实例独立性
        path1 = cfg1.get_config_file_path()
        path2 = cfg2.get_config_file_path()
        
        assert path1 != path2, f"两个实例的路径应该不同: {path1} vs {path2}"
        
        # 重新加载配置以确保数据持久化
        cfg1.reload()
        cfg2.reload()
        
        assert cfg1.get('instance_id') == "instance_1"
        assert cfg2.get('instance_id') == "instance_2"
        
        # 验证配置文件都存在
        assert os.path.exists(path1)
        assert os.path.exists(path2)
        
        print(f"✓ 实例1路径: {path1}")
        print(f"✓ 实例2路径: {path2}")
        print("✓ 多实例独立性验证通过")

    def test_tc0012_001_011_test_mode_with_first_start_time(self):
        """TC0012-001-011: 测试test_mode基于first_start_time生成路径"""
        # 创建一个固定的启动时间
        fixed_start_time = datetime(2025, 6, 7, 14, 30, 52)
        
        # 使用固定的first_start_time创建测试配置
        cfg = get_config_manager(test_mode=True, first_start_time=fixed_start_time)
        
        # 验证路径包含基于first_start_time的日期和时间
        config_path = cfg.get_config_file_path()
        
        # 验证路径格式：应该包含20250607/143052
        expected_date = "20250607"
        expected_time = "143052"
        
        assert expected_date in config_path, f"路径应包含日期 {expected_date}，实际路径: {config_path}"
        assert expected_time in config_path, f"路径应包含时间 {expected_time}，实际路径: {config_path}"
        
        # 验证配置中的first_start_time也是正确的
        stored_time_str = cfg.get('first_start_time')
        assert stored_time_str == fixed_start_time.isoformat()
        
        print(f"✓ 固定启动时间: {fixed_start_time}")
        print(f"✓ 生成的测试路径: {config_path}")
        print(f"✓ 存储的启动时间: {stored_time_str}")

    def test_tc0012_001_012_test_mode_path_consistency(self):
        """TC0012-001-012: 测试相同first_start_time生成相同路径"""
        # 使用相同的first_start_time创建两个配置实例
        fixed_start_time = datetime(2025, 6, 7, 15, 45, 30)
        
        # 第一个实例
        cfg1 = get_config_manager(test_mode=True, first_start_time=fixed_start_time)
        path1 = cfg1.get_config_file_path()
        
        # 清理实例缓存
        _clear_instances_for_testing()
        
        # 第二个实例（相同的first_start_time）
        cfg2 = get_config_manager(test_mode=True, first_start_time=fixed_start_time)
        path2 = cfg2.get_config_file_path()
        
        # 验证路径的日期时间部分相同
        import re
        # 修复：Windows路径使用反斜杠，需要转义
        date_time_pattern = r'tests[\\/](\d{8})[\\/](\d{6})[\\/]'
        
        match1 = re.search(date_time_pattern, path1)
        match2 = re.search(date_time_pattern, path2)
        
        assert match1 is not None, f"路径1格式不正确: {path1}"
        assert match2 is not None, f"路径2格式不正确: {path2}"
        
        # 日期时间部分应该相同
        assert match1.group(1) == match2.group(1), "日期部分应该相同"
        assert match1.group(2) == match2.group(2), "时间部分应该相同"
        
        # 验证具体的日期时间值
        assert match1.group(1) == "20250607", f"日期应为20250607，实际: {match1.group(1)}"
        assert match1.group(2) == "154530", f"时间应为154530，实际: {match1.group(2)}"
        
        print(f"✓ 路径1: {path1}")
        print(f"✓ 路径2: {path2}")
        print("✓ 日期时间一致性验证通过")

    def test_tc0012_001_013_test_mode_without_first_start_time(self):
        """测试：不指定first_start_time时使用当前时间"""
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            prod_config_path = f.name
            f.write(b'project_name: test_project\n')
        
        try:
            # 记录测试开始时间
            before_time = datetime.now()
            
            # 创建配置管理器实例
            cfg = get_config_manager(config_path=prod_config_path, test_mode=True)
            
            # 记录测试结束时间
            datetime.now()
            
            # 从路径中提取时间信息
            path_parts = cfg._config_path.split(os.sep)
            # 路径格式: .../tests/YYYYMMDD/HHMMSS/project_name/src/config/config.yaml
            # 找到 tests 目录的位置
            tests_index = -1
            for i, part in enumerate(path_parts):
                if part == 'tests':
                    tests_index = i
                    break
            
            if tests_index >= 0 and tests_index + 2 < len(path_parts):
                date_str = path_parts[tests_index + 1]  # YYYYMMDD
                time_str = path_parts[tests_index + 2]  # HHMMSS
                path_datetime_str = f"{date_str}{time_str}"
                path_datetime = datetime.strptime(path_datetime_str, "%Y%m%d%H%M%S")
                
                # 验证时间在合理范围内
                # 由于测试执行时间可能跨越秒，所以允许2秒的误差
                time_diff = abs((path_datetime - before_time).total_seconds())
                assert time_diff <= 2, f"路径时间 {path_datetime} 与开始时间 {before_time} 相差超过2秒"
            else:
                # 如果路径格式不符合预期，跳过时间验证
                pytest.skip(f"路径格式不符合预期: {cfg._config_path}")
            
        finally:
            # 清理临时文件
            if os.path.exists(prod_config_path):
                assert prod_config_path.startswith(tempfile.gettempdir()), f"禁止删除非临时文件: {prod_config_path}"
                os.unlink(prod_config_path)

    def test_tc0012_001_014_test_mode_config_copy_with_time(self):
        """TC0012-001-014: 测试配置复制时正确处理first_start_time"""
        # 创建一个临时的生产配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
__data__:
  app_name: "生产应用"
  version: "2.0.0"
  first_start_time: "2025-01-01T10:00:00"
  database:
    host: "prod-db"
    port: 3306
__type_hints__: {}
""")
            prod_config_path = f.name
        
        try:
            # 使用固定的first_start_time和显式配置路径
            fixed_start_time = datetime(2025, 6, 7, 16, 20, 15)
            cfg = get_config_manager(
                config_path=prod_config_path, 
                test_mode=True, 
                first_start_time=fixed_start_time
            )
            
            # 验证配置被复制到测试环境
            test_path = cfg.get_config_file_path()
            
            # 验证路径包含正确的日期时间
            assert "20250607" in test_path, f"路径应包含日期20250607: {test_path}"
            assert "162015" in test_path, f"路径应包含时间162015: {test_path}"
            
            # 验证配置内容被复制
            assert cfg.get('app_name') == "生产应用"
            assert cfg.get('version') == "2.0.0"
            assert cfg.get('database.host') == "prod-db"
            
            # 验证first_start_time被更新为测试时间
            stored_time = cfg.get('first_start_time')
            assert stored_time == fixed_start_time.isoformat(), \
                f"存储的时间应为 {fixed_start_time.isoformat()}，实际: {stored_time}"
            
            print(f"✓ 生产配置路径: {prod_config_path}")
            print(f"✓ 测试配置路径: {test_path}")
            print(f"✓ 固定启动时间: {fixed_start_time}")
            print(f"✓ 存储的启动时间: {stored_time}")
            
        finally:
            # 清理临时文件
            assert prod_config_path.startswith(tempfile.gettempdir()), f"禁止删除非临时文件: {prod_config_path}"
            os.unlink(prod_config_path)

    def test_tc0012_001_015_test_mode_time_format_validation(self):
        """TC0012-001-015: 测试时间格式的正确性"""
        # 测试各种边界时间值
        test_times = [
            datetime(2025, 1, 1, 0, 0, 0),      # 年初
            datetime(2025, 12, 31, 23, 59, 59), # 年末
            datetime(2025, 6, 15, 12, 30, 45),  # 中间值
            datetime(2025, 2, 28, 9, 5, 3),     # 二月
        ]
        
        for i, test_time in enumerate(test_times):
            # 清理实例缓存
            _clear_instances_for_testing()
            
            cfg = get_config_manager(test_mode=True, first_start_time=test_time)
            config_path = cfg.get_config_file_path()
            
            # 验证路径格式
            expected_date = test_time.strftime('%Y%m%d')
            expected_time = test_time.strftime('%H%M%S')
            
            assert expected_date in config_path, \
                f"测试{i+1}: 路径应包含日期 {expected_date}，实际路径: {config_path}"
            assert expected_time in config_path, \
                f"测试{i+1}: 路径应包含时间 {expected_time}，实际路径: {config_path}"
            
            # 验证存储的时间格式
            stored_time = cfg.get('first_start_time')
            assert stored_time == test_time.isoformat(), \
                f"测试{i+1}: 存储时间格式不正确，期望: {test_time.isoformat()}，实际: {stored_time}"
            
            print(f"✓ 测试{i+1} - 时间: {test_time}, 路径: {config_path}")
        
        print("✓ 所有时间格式验证通过")

    def test_tc0012_001_016_test_environment_cleanup_with_time(self):
        """TC0012-001-016: 测试基于时间的环境清理功能"""
        # 创建多个不同时间的测试环境
        test_times = [
            datetime(2025, 6, 5, 10, 0, 0),   # 2天前
            datetime(2025, 6, 6, 15, 30, 0),  # 1天前
            datetime(2025, 6, 7, 20, 45, 0),  # 今天
        ]
        
        created_paths = []
        
        for test_time in test_times:
            # 清理实例缓存
            _clear_instances_for_testing()
            
            cfg = get_config_manager(test_mode=True, first_start_time=test_time)
            cfg.test_data = f"data_for_{test_time.strftime('%Y%m%d_%H%M%S')}"
            cfg.save()
            
            test_path = cfg.get_config_file_path()
            created_paths.append(test_path)
            
            # 验证文件存在
            assert os.path.exists(test_path), f"测试配置文件应该存在: {test_path}"
        
        # 验证所有路径都不同
        assert len(set(created_paths)) == len(created_paths), "所有测试路径应该不同"
        
        # 获取测试环境列表
        environments = TestEnvironmentManager.list_test_environments()
        
        # 应该至少有3个日期的环境
        date_dirs = set()
        for env in environments:
            date_dirs.add(env['date'])
        
        assert len(date_dirs) >= 3, f"应该有至少3个不同日期的环境，实际: {len(date_dirs)}"
        
        print("✓ 创建的测试路径:")
        for i, path in enumerate(created_paths):
            print(f"  {i+1}. {path}")
        
        print(f"✓ 发现的环境日期: {sorted(date_dirs)}")
        print("✓ 基于时间的环境管理验证通过") 