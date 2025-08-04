# tests/01_unit_tests/test_config_manager/test_unified_tensorboard_path.py
from __future__ import annotations
from datetime import datetime
import tempfile
import os
from pathlib import Path
from config_manager import get_config_manager
from config_manager.core.path_configuration import PathGenerator, TimeProcessor


class TestUnifiedTensorBoardPath:
    """测试统一的TensorBoard路径生成功能"""
    
    def test_generate_unified_tensorboard_path_basic(self):
        """测试基础的统一路径生成功能"""
        generator = PathGenerator()
        work_dir = "/test/work"
        date_str = "20250108"
        time_str = "143025"
        test_time = datetime(2025, 1, 8, 14, 30, 25)
        test_time_str = test_time.isoformat()
        
        # 生成统一路径
        path = generator.generate_unified_tensorboard_path(
            work_dir, date_str, time_str, test_time_str
        )
        
        # 验证路径格式：{work_dir}/{yyyy}/{WXX}/{mmdd}/{HHMMSS}
        expected_path = "/test/work/2025/W02/0108/143025"
        assert path == expected_path, f"期望路径: {expected_path}, 实际路径: {path}"
        pass
    
    def test_tsb_logs_dir_and_tensorboard_dir_are_identical(self):
        """测试tsb_logs_dir和tensorboard_dir生成相同的路径"""
        generator = PathGenerator()
        work_dir = "/test/work"
        date_str = "20250815"
        time_str = "103045"
        test_time = datetime(2025, 8, 15, 10, 30, 45)
        test_time_str = test_time.isoformat()
        
        # 生成日志目录
        log_dirs = generator.generate_log_directories(
            work_dir, date_str, time_str, test_time_str
        )
        
        # 生成TensorBoard目录
        tb_dirs = generator.generate_tensorboard_directory(
            work_dir, date_str, time_str, test_time_str
        )
        
        # 验证两个路径完全相同
        tsb_path = log_dirs['paths.tsb_logs_dir']
        tb_path = tb_dirs['paths.tensorboard_dir']
        
        assert tsb_path == tb_path, f"tsb_logs_dir和tensorboard_dir应该相同: tsb={tsb_path}, tb={tb_path}"
        
        # 验证路径格式
        expected_path = "/test/work/2025/W33/0815/103045"
        assert tsb_path == expected_path, f"路径格式不正确: 期望={expected_path}, 实际={tsb_path}"
        pass
    
    def test_week_number_format(self):
        """测试周数格式是否正确（W前缀+两位数字）"""
        generator = PathGenerator()
        work_dir = "/test/work"
        
        test_cases = [
            # (datetime对象, 预期的周数字符串)
            (datetime(2025, 1, 1, 0, 0, 0), "W01"),   # 新年第一天
            (datetime(2025, 2, 10, 0, 0, 0), "W07"),  # 第7周
            (datetime(2025, 7, 15, 12, 0, 0), "W29"), # 第29周
            (datetime(2025, 12, 29, 0, 0, 0), "W01"), # 年末可能是下一年第1周
        ]
        
        for test_time, expected_week in test_cases:
            test_time_str = test_time.isoformat()
            date_str = test_time.strftime('%Y%m%d')
            time_str = test_time.strftime('%H%M%S')
            
            # 生成路径
            path = generator.generate_unified_tensorboard_path(
                work_dir, date_str, time_str, test_time_str
            )
            
            # 验证路径包含正确的周数格式
            parts = Path(path).parts
            year_idx = parts.index(str(test_time.year))
            week_part = parts[year_idx + 1]
            
            assert week_part == expected_week, \
                f"日期 {test_time_str} 的周数应该是 {expected_week}，实际是 {week_part}"
        pass
    
    def test_fallback_to_old_format_on_error(self):
        """测试时间解析失败时降级到旧格式"""
        generator = PathGenerator()
        work_dir = "/test/work"
        date_str = "20250108"
        time_str = "143025"
        
        # 使用无效的时间字符串
        invalid_time_str = "invalid-time-string"
        
        # 生成路径，应该降级到旧格式
        path = generator.generate_unified_tensorboard_path(
            work_dir, date_str, time_str, invalid_time_str
        )
        
        # 验证使用了旧格式
        expected_path = "/test/work/20250108/143025"
        assert path == expected_path, f"降级格式不正确: 期望={expected_path}, 实际={path}"
        pass
    
    def test_no_first_start_time_uses_old_format(self):
        """测试没有first_start_time时使用旧格式"""
        generator = PathGenerator()
        work_dir = "/test/work"
        date_str = "20250108"
        time_str = "143025"
        
        # 不提供first_start_time
        path = generator.generate_unified_tensorboard_path(
            work_dir, date_str, time_str, None
        )
        
        # 验证使用了旧格式
        expected_path = "/test/work/20250108/143025"
        assert path == expected_path, f"旧格式不正确: 期望={expected_path}, 实际={path}"
        pass
    
    def test_integration_with_config_manager(self):
        """集成测试：通过ConfigManager验证路径一致性"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 使用固定时间创建配置管理器
            fixed_time = datetime(2025, 3, 15, 9, 45, 30)
            config = get_config_manager(
                test_mode=True,
                first_start_time=fixed_time
            )
            
            # 获取路径
            tsb_path = config.paths.tsb_logs_dir
            tb_path = config.paths.tensorboard_dir
            
            # 验证路径相同
            assert tsb_path == tb_path, f"路径应该相同: tsb={tsb_path}, tb={tb_path}"
            
            # 验证路径格式
            # 2025年3月15日是第11周
            assert "/2025/W11/0315/094530" in tsb_path, f"路径格式不正确: {tsb_path}"
        pass
    
    def test_cross_platform_path_separators(self):
        """测试跨平台路径分隔符处理"""
        generator = PathGenerator()
        work_dir = "C:\\test\\work" if os.name == 'nt' else "/test/work"
        date_str = "20250108"
        time_str = "143025"
        test_time = datetime(2025, 1, 8, 14, 30, 25)
        test_time_str = test_time.isoformat()
        
        # 生成路径
        path = generator.generate_unified_tensorboard_path(
            work_dir, date_str, time_str, test_time_str
        )
        
        # 验证路径使用正确的分隔符
        if os.name == 'nt':
            assert '\\' in path, "Windows路径应该包含反斜杠"
        else:
            assert '/' in path, "Unix路径应该包含正斜杠"
            assert '\\' not in path, "Unix路径不应该包含反斜杠"
        pass
    
    def test_year_boundary_week_calculation(self):
        """测试跨年边界的周数计算"""
        generator = PathGenerator()
        work_dir = "/test/work"
        
        # 测试跨年的情况
        test_cases = [
            # 2024年最后几天可能属于2025年第1周
            (datetime(2024, 12, 30, 0, 0, 0), "2024", "W01"),
            # 2025年第一天
            (datetime(2025, 1, 1, 0, 0, 0), "2025", "W01"),
            # 2025年最后一天可能属于2026年第1周
            (datetime(2025, 12, 31, 0, 0, 0), "2025", "W01"),
        ]
        
        for test_time, expected_year, expected_week in test_cases:
            test_time_str = test_time.isoformat()
            date_str = test_time.strftime('%Y%m%d')
            time_str = test_time.strftime('%H%M%S')
            
            # 生成路径
            path = generator.generate_unified_tensorboard_path(
                work_dir, date_str, time_str, test_time_str
            )
            
            # 验证路径包含正确的年份和周数
            assert f"/{expected_year}/{expected_week}/" in path, \
                f"日期 {test_time_str} 的路径应包含 {expected_year}/{expected_week}，实际路径: {path}"
        pass