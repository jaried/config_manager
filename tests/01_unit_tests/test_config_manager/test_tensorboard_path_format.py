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
        """测试tensorboard_dir使用年/周/月/日/时间格式"""
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
        
        # 验证路径格式
        expected_path = f"/test/work/dir/tensorboard/{year}/{week}/{month}/{day}/{time}"
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
        
        # 提取路径中的日期时间部分
        tb_parts = tensorboard_dir.split('/tensorboard/')[1] if '/tensorboard/' in tensorboard_dir else ""
        tsb_parts = tsb_logs_dir.split('/tsb_logs/')[1] if '/tsb_logs/' in tsb_logs_dir else ""
        
        # 验证格式相同
        assert tb_parts == tsb_parts, f"路径格式不匹配: tensorboard={tb_parts}, tsb_logs={tsb_parts}"
        
        # 验证格式符合年/周/月/日/时间
        parts = tb_parts.split('/')
        assert len(parts) == 5, f"路径格式应该包含5个部分（年/周/月/日/时间），实际: {parts}"
        
        year, week, month, day, time = parts
        # 验证各部分格式
        assert len(year) == 4 and year.isdigit(), f"年份格式错误: {year}"
        assert len(week) == 2 and week.isdigit(), f"周数格式错误: {week}"
        assert len(month) == 2 and month.isdigit(), f"月份格式错误: {month}"
        assert len(day) == 2 and day.isdigit(), f"日期格式错误: {day}"
        assert len(time) == 6 and time.isdigit(), f"时间格式错误: {time}"
        pass
    
    def test_path_generator_with_different_dates(self):
        """测试不同日期的路径生成"""
        generator = PathGenerator()
        work_dir = "/test/work"
        
        # 测试多个不同的日期
        test_cases = [
            # (datetime对象, 预期周数)
            (datetime(2025, 1, 1, 0, 0, 0), "01"),   # 新年第一天
            (datetime(2025, 12, 31, 23, 59, 59), "01"),  # 年末（可能是下一年第1周）
            (datetime(2025, 7, 15, 12, 0, 0), "29"),  # 年中
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
            
            # 提取时间部分
            tb_time1 = tb_dir1.split('/tensorboard/')[1] if '/tensorboard/' in tb_dir1 else ""
            tsb_time1 = tsb_dir1.split('/tsb_logs/')[1] if '/tsb_logs/' in tsb_dir1 else ""
            
            # 验证格式一致
            assert tb_time1 == tsb_time1, "同一实例中tensorboard和tsb_logs格式应该一致"
            
            # 验证包含周数（格式应该是 年/周/月/日/时间）
            parts = tb_time1.split('/')
            assert len(parts) == 5, "路径应该包含5个部分"
            assert parts[1] == "33", f"2025年8月15日应该是第33周，实际: {parts[1]}"
        pass
    
    def test_path_configuration_integration(self):
        """集成测试：验证完整的路径配置流程"""
        # 使用get_config_manager创建完整的配置管理器
        config = get_config_manager(test_mode=True)
        
        # 验证tensorboard和tsb_logs路径格式
        tb_path = config.paths.tensorboard_dir
        tsb_path = config.paths.tsb_logs_dir
        
        # 验证都包含周数格式（格式: 年/周/月/日/时间）
        # 提取时间部分
        tb_time = tb_path.split('/tensorboard/')[1] if '/tensorboard/' in tb_path else ""
        tsb_time = tsb_path.split('/tsb_logs/')[1] if '/tsb_logs/' in tsb_path else ""
        
        # 验证格式包含5个部分
        tb_parts = tb_time.split('/')
        tsb_parts = tsb_time.split('/')
        
        assert len(tb_parts) == 5, f"tensorboard路径应包含5个部分，实际: {tb_parts}"
        assert len(tsb_parts) == 5, f"tsb_logs路径应包含5个部分，实际: {tsb_parts}"
        
        # 验证时间部分完全相同
        assert tb_time == tsb_time, f"路径时间部分应该相同: tb={tb_time}, tsb={tsb_time}"
        
        # 验证每个部分的格式
        year, week, month, day, time = tb_parts
        assert len(year) == 4 and year.isdigit()
        assert len(week) == 2 and week.isdigit()
        assert len(month) == 2 and month.isdigit()
        assert len(day) == 2 and day.isdigit()
        assert len(time) == 6 and time.isdigit()
        pass