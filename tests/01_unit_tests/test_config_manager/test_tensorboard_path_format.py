# tests/01_unit_tests/test_config_manager/test_tensorboard_path_format.py
from __future__ import annotations
from datetime import datetime
import tempfile
import os
from config_manager import get_config_manager
from config_manager.core.path_configuration import PathGenerator, TimeProcessor


class TestTensorboardPathFormat:
    """测试TensorBoard路径格式"""
    
    def test_tensorboard_dir_uses_week_format(self):
        """测试tensorboard_dir使用年/周/月日/时间格式"""
        # 创建测试时间
        test_time = datetime(2025, 7, 26, 10, 30, 45)
        test_time_str = test_time.isoformat()
        
        # 创建PathGenerator实例
        generator = PathGenerator()
        
        # 解析时间组件
        year, week, month, day, time = TimeProcessor.parse_time_with_week(test_time_str)
        
        # 生成tensorboard目录
        work_dir = "/test/work/dir"
        date_str = test_time.strftime('%Y%m%d')
        time_str = test_time.strftime('%H%M%S')
        
        result = generator.generate_tensorboard_directory(
            work_dir, date_str, time_str, test_time_str
        )
        
        # 验证路径格式 - 新格式直接在work_dir下，无tensorboard子目录
        expected_path = f"/test/work/dir/{year}/W{week}/{month}{day}/{time}"
        assert result['paths.tensorboard_dir'] == expected_path
        
        # 验证各个组件
        assert year == "2025"
        assert week == "30"  # 2025年7月26日是第30周
        assert month == "07"
        assert day == "26"
        assert time == "103045"
        pass
    
    def test_tensorboard_dir_matches_tsb_logs_dir_format(self):
        """测试tensorboard_dir与tsb_logs_dir使用相同格式"""
        # 创建测试配置管理器
        config = get_config_manager(test_mode=True)
        
        # 获取路径配置
        tensorboard_dir = config.paths.tensorboard_dir
        tsb_logs_dir = config.paths.tsb_logs_dir
        
        # 根据新的需求，两个路径应该完全相同
        assert tensorboard_dir == tsb_logs_dir, f"tensorboard_dir和tsb_logs_dir应该相同: tb={tensorboard_dir}, tsb={tsb_logs_dir}"
        
        # 验证路径格式符合新规范：年/W周/月日/时间
        # 找到年份部分来定位时间部分
        path_parts = tensorboard_dir.split('/')
        # 查找4位数字的年份
        year_idx = None
        for i, part in enumerate(path_parts):
            if len(part) == 4 and part.isdigit():
                year_idx = i
                break
        
        assert year_idx is not None, f"路径中未找到年份: {tensorboard_dir}"
        
        # 从年份开始的路径部分
        time_parts = path_parts[year_idx:]
        assert len(time_parts) >= 4, f"路径格式应该至少包含4个部分（年/W周/月日/时间），实际: {time_parts}"
        
        year, week, monthday, time = time_parts[:4]
        # 验证各部分格式
        assert len(year) == 4 and year.isdigit(), f"年份格式错误: {year}"
        assert week.startswith('W') and len(week) == 3 and week[1:].isdigit(), f"周数格式错误（应为WXX）: {week}"
        assert len(monthday) == 4 and monthday.isdigit(), f"月日格式错误（应为MMDD）: {monthday}"
        assert len(time) == 6 and time.isdigit(), f"时间格式错误（应为HHMMSS）: {time}"
        pass
    
    def test_path_generator_with_different_dates(self):
        """测试不同日期的路径生成"""
        generator = PathGenerator()
        work_dir = "/test/work"
        
        # 测试多个不同的日期
        test_cases = [
            # (datetime对象, 预期周数带W前缀)
            (datetime(2025, 1, 1, 0, 0, 0), "W01"),   # 新年第一天
            (datetime(2025, 12, 31, 23, 59, 59), "W01"),  # 年末（可能是下一年第1周）
            (datetime(2025, 7, 15, 12, 0, 0), "W29"),  # 年中
        ]
        
        for test_time, expected_week in test_cases:
            test_time_str = test_time.isoformat()
            date_str = test_time.strftime('%Y%m%d')
            time_str = test_time.strftime('%H%M%S')
            
            # 生成tensorboard路径
            result = generator.generate_tensorboard_directory(
                work_dir, date_str, time_str, test_time_str
            )
            
            # 验证路径包含正确的周数
            path = result['paths.tensorboard_dir']
            parts = path.split('/')
            
            # 找到周数部分（在年份后面）
            year_idx = parts.index(test_time.strftime('%Y'))
            week_in_path = parts[year_idx + 1]
            
            assert week_in_path == expected_week, \
                f"日期 {test_time_str} 的周数应该是 {expected_week}，实际是 {week_in_path}"
        pass
    
    def test_tensorboard_and_tsb_logs_consistency_across_instances(self):
        """测试多个配置实例间tensorboard和tsb_logs路径的一致性"""
        # 创建两个配置管理器实例，使用相同的时间
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = os.path.join(tmp_dir, "test_config.yaml")
            
            # 使用固定时间创建第一个实例
            fixed_time = datetime(2025, 8, 15, 14, 30, 0)
            config1 = get_config_manager(
                config_path=config_path,
                test_mode=True,
                first_start_time=fixed_time
            )
            
            tb_dir1 = config1.paths.tensorboard_dir
            tsb_dir1 = config1.paths.tsb_logs_dir
            
            # 根据新需求，两个路径应该完全相同
            assert tb_dir1 == tsb_dir1, "tensorboard和tsb_logs路径应该完全相同"
            
            # 验证路径格式符合新规范
            path_parts = tb_dir1.split('/')
            # 查找4位数字的年份
            year_idx = None
            for i, part in enumerate(path_parts):
                if len(part) == 4 and part.isdigit() and part == "2025":
                    year_idx = i
                    break
            
            assert year_idx is not None, f"路径中未找到2025年份: {tb_dir1}"
            
            # 验证包含周数（格式应该是 年/W周/月日/时间）
            time_parts = path_parts[year_idx:]
            assert len(time_parts) >= 4, "路径应该包含至少4个部分"
            assert time_parts[1] == "W33", f"2025年8月15日应该是第33周，实际: {time_parts[1]}"
        pass
    
    def test_path_configuration_integration(self):
        """集成测试：验证完整的路径配置流程"""
        # 使用get_config_manager创建完整的配置管理器
        config = get_config_manager(test_mode=True)
        
        # 验证tensorboard和tsb_logs路径格式
        tb_path = config.paths.tensorboard_dir
        tsb_path = config.paths.tsb_logs_dir
        
        # 根据新需求，两个路径应该完全相同
        assert tb_path == tsb_path, f"路径应该相同: tb={tb_path}, tsb={tsb_path}"
        
        # 验证路径格式符合新规范
        path_parts = tb_path.split('/')
        # 查找4位数字的年份
        year_idx = None
        for i, part in enumerate(path_parts):
            if len(part) == 4 and part.isdigit():
                year_idx = i
                break
        
        assert year_idx is not None, f"路径中未找到年份: {tb_path}"
        
        # 从年份开始的路径部分应该是：年/W周/月日/时间
        time_parts = path_parts[year_idx:]
        assert len(time_parts) >= 4, f"路径应包含至少4个部分，实际: {time_parts}"
        
        # 验证每个部分的格式
        year, week, monthday, time = time_parts[:4]
        assert len(year) == 4 and year.isdigit()
        assert week.startswith('W') and len(week) == 3 and week[1:].isdigit()
        assert len(monthday) == 4 and monthday.isdigit()
        assert len(time) == 6 and time.isdigit()
        pass