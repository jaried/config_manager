# tests/01_unit_tests/test_config_manager/test_tsb_path_week_format.py
from __future__ import annotations
from datetime import datetime
import os
import pytest

from config_manager.core.path_resolver import PathResolver
from config_manager.core.path_configuration import TimeProcessor


class TestTsbPathWeekFormat:
    """测试TSB路径中的周数格式（两位数字，不带W前缀）"""
    
    def test_week_number_two_digits_without_w(self):
        """测试周数格式为两位数字，不带W前缀"""
        test_cases = [
            (datetime(2025, 1, 1), "01"),   # 第1周
            (datetime(2025, 1, 8), "02"),   # 第2周
            (datetime(2025, 2, 10), "07"),  # 第7周
            (datetime(2025, 7, 15), "29"),  # 第29周
            (datetime(2025, 12, 25), "52"), # 第52周
        ]
        
        for test_time, expected_week in test_cases:
            path = PathResolver.generate_tsb_logs_path("/test", test_time)
            path_parts = path.split(os.sep)
            
            # 查找年份后面的周数部分
            for i, part in enumerate(path_parts):
                if part == str(test_time.year):
                    week_part = path_parts[i + 1]
                    assert week_part == expected_week, (
                        f"日期{test_time}的周数应该是{expected_week}，"
                        f"实际是{week_part}"
                    )
                    # 确保不包含W前缀
                    assert not week_part.startswith("W"), (
                        f"周数不应包含W前缀，实际值：{week_part}"
                    )
                    break
    
    def test_time_processor_week_format(self):
        """测试TimeProcessor的周数格式化"""
        test_cases = [
            (datetime(2025, 1, 1), "01"),
            (datetime(2025, 3, 15), "11"),
            (datetime(2025, 10, 10), "41"),
            (datetime(2025, 12, 31), "01"),  # 可能属于下一年
        ]
        
        for test_time, expected_week in test_cases:
            week_str = TimeProcessor.get_week_number(test_time)
            assert week_str == expected_week, (
                f"TimeProcessor.get_week_number({test_time})应返回{expected_week}，"
                f"实际返回{week_str}"
            )
            # 验证格式：两位数字
            assert len(week_str) == 2, f"周数应该是两位数字，实际：{week_str}"
            assert week_str.isdigit(), f"周数应该只包含数字，实际：{week_str}"
    
    def test_iso_week_number_accuracy(self):
        """测试ISO周数计算的准确性"""
        # 测试已知的ISO周数
        known_cases = [
            # ISO 8601标准：周一是一周的第一天
            # 一年的第一周是包含该年第一个周四的那一周
            (datetime(2024, 1, 1), 1),    # 2024年1月1日（周一）是第1周
            (datetime(2024, 1, 7), 1),    # 2024年1月7日（周日）是第1周
            (datetime(2024, 1, 8), 2),    # 2024年1月8日（周一）是第2周
            (datetime(2024, 12, 30), 1),  # 2024年12月30日（周一）是2025年第1周
            (datetime(2025, 1, 1), 1),    # 2025年1月1日（周三）是第1周
            (datetime(2025, 1, 6), 2),    # 2025年1月6日（周一）是第2周
            (datetime(2025, 12, 29), 1),  # 2025年12月29日（周一）是2026年第1周
            (datetime(2025, 12, 28), 52), # 2025年12月28日（周日）是2025年第52周
        ]
        
        for test_date, expected_week in known_cases:
            iso_year, iso_week, iso_day = test_date.isocalendar()
            assert iso_week == expected_week, (
                f"{test_date}的ISO周数应该是{expected_week}，"
                f"实际是{iso_week}"
            )
    
    def test_year_boundary_week_numbers(self):
        """测试跨年边界的周数处理"""
        # 测试年末可能属于下一年第1周的情况
        test_cases = [
            # 2024年末
            (datetime(2024, 12, 29), 2024, 52),  # 周日，属于2024年第52周
            (datetime(2024, 12, 30), 2025, 1),   # 周一，属于2025年第1周
            (datetime(2024, 12, 31), 2025, 1),   # 周二，属于2025年第1周
            # 2025年初
            (datetime(2025, 1, 1), 2025, 1),     # 周三，属于2025年第1周
            (datetime(2025, 1, 5), 2025, 1),     # 周日，属于2025年第1周
            (datetime(2025, 1, 6), 2025, 2),     # 周一，属于2025年第2周
            # 2025年末
            (datetime(2025, 12, 28), 2025, 52),  # 周日，属于2025年第52周
            (datetime(2025, 12, 29), 2026, 1),   # 周一，属于2026年第1周
        ]
        
        for test_date, expected_year, expected_week in test_cases:
            iso_year, iso_week, _ = test_date.isocalendar()
            assert iso_year == expected_year, (
                f"{test_date}的ISO年份应该是{expected_year}，实际是{iso_year}"
            )
            assert iso_week == expected_week, (
                f"{test_date}的ISO周数应该是{expected_week}，实际是{iso_week}"
            )
            
            # 验证路径生成使用ISO年份
            path = PathResolver.generate_tsb_logs_path("/test", test_date)
            assert f"/{expected_year}/" in path, (
                f"路径应包含ISO年份{expected_year}，实际路径：{path}"
            )
            assert f"/{expected_week:02d}/" in path, (
                f"路径应包含周数{expected_week:02d}，实际路径：{path}"
            )
    
    def test_leap_year_week_numbers(self):
        """测试闰年的周数计算"""
        # 2024年是闰年
        leap_year_cases = [
            (datetime(2024, 2, 29), 9),   # 闰年2月29日，第9周
            (datetime(2024, 12, 31), 1),  # 闰年最后一天，属于2025年第1周
        ]
        
        for test_date, expected_week in leap_year_cases:
            iso_year, iso_week, _ = test_date.isocalendar()
            week_str = TimeProcessor.get_week_number(test_date)
            assert week_str == f"{expected_week:02d}", (
                f"闰年{test_date}的周数应该是{expected_week:02d}，"
                f"实际是{week_str}"
            )
    
    def test_monday_first_day_of_week(self):
        """验证ISO标准：周一是一周的第一天"""
        # 2025年1月6日是周一，应该是新的一周开始
        monday = datetime(2025, 1, 6)
        sunday = datetime(2025, 1, 5)
        
        monday_week = monday.isocalendar()[1]
        sunday_week = sunday.isocalendar()[1]
        
        assert monday_week == 2, "2025年1月6日（周一）应该是第2周"
        assert sunday_week == 1, "2025年1月5日（周日）应该是第1周"
        assert monday_week == sunday_week + 1, "周一应该是新一周的开始"
    
    def test_week_53_special_cases(self):
        """测试特殊的第53周情况"""
        # 某些年份可能有53周
        # 2020年有53周（2020年12月28日-2021年1月3日）
        test_date = datetime(2020, 12, 31)  # 2020年12月31日
        iso_year, iso_week, _ = test_date.isocalendar()
        assert iso_week == 53, f"2020年12月31日应该是第53周，实际是第{iso_week}周"
        
        # 验证路径生成正确处理53周
        path = PathResolver.generate_tsb_logs_path("/test", test_date)
        assert "/53/" in path, f"路径应包含第53周，实际路径：{path}"
    
    def test_consistent_week_format_in_path(self):
        """测试路径中周数格式的一致性"""
        # 测试多个日期，确保格式一致
        dates = [
            datetime(2025, 1, 1),   # 第1周
            datetime(2025, 2, 14),  # 第7周
            datetime(2025, 5, 20),  # 第21周
            datetime(2025, 11, 30), # 第48周
        ]
        
        for date in dates:
            path = PathResolver.generate_tsb_logs_path("/work", date)
            parts = path.split(os.sep)
            
            # 找到年份后的周数部分
            year_str = str(date.isocalendar()[0])
            year_index = parts.index(year_str)
            week_part = parts[year_index + 1]
            
            # 验证格式
            assert len(week_part) == 2, (
                f"周数应该是两位数字，实际：{week_part} (路径：{path})"
            )
            assert week_part.isdigit(), (
                f"周数应该只包含数字，实际：{week_part} (路径：{path})"
            )
            assert not week_part.startswith("W"), (
                f"周数不应包含W前缀，实际：{week_part} (路径：{path})"
            )
    
    pass