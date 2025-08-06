# tests/01_unit_tests/test_config_manager/test_tc0013_001_date_format_consistency.py
from __future__ import annotations
from datetime import datetime
import pytest
import tempfile
import re
from pathlib import Path

from src.config_manager import get_config_manager, _clear_instances_for_testing

@pytest.fixture(autouse=True)
def clear_instances_fixture():
    """在每个测试前后自动清理ConfigManager单例"""
    _clear_instances_for_testing()
    yield
    _clear_instances_for_testing()


class TestDateFormatConsistency:
    """测试日期格式一致性"""
    
    def test_date_format_consistency_in_paths(self):
        """
        测试config.paths中所有日期相关路径使用一致的yyyymmdd格式
        
        这个测试验证：
        1. logs_dir, tsb_logs_dir, backup_dir中的日期都使用yyyymmdd格式
        2. 不应该出现yyyy-mm-dd格式
        
        基于issue #1：
        - 预期：logs_dir和tsb_logs_dir应该使用yyyymmdd格式（如：20250107）
        - 实际：当前使用的是yyyy-mm-dd格式（如：2025-01-07）
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试配置文件
            config_file = Path(temp_dir) / "config.yaml"
            test_time = "2025-01-07T18:15:20"
            
            config_content = f"""
project_name: test_project
experiment_name: experiment_name  
base_dir: {temp_dir}
first_start_time: '{test_time}'
"""
            config_file.write_text(config_content)
            
            # 获取配置管理器
            config = get_config_manager(
                config_path=str(config_file),
                test_mode=True,
                first_start_time=test_time
            )
            
            # 获取路径配置
            paths = config.paths
            
            # 定义日期格式的正则表达式（支持跨平台路径分隔符）
            sep = r'[/\\]'  # 匹配正斜杠或反斜杠
            yyyymmdd_pattern = re.compile(f'{sep}(\\d{{8}}){sep}')  # 匹配 /20250107/ 或 \20250107\ 格式
            yyyy_mm_dd_pattern = re.compile(f'{sep}(\\d{{4}}-\\d{{2}}-\\d{{2}}){sep}')  # 匹配 /2025-01-07/ 或 \2025-01-07\ 格式
            
            # tsb_logs_dir的新格式: yyyy/Www/mmdd，其中Www是带W前缀的两位数周数
            tsb_logs_pattern = re.compile(f'{sep}(\\d{{4}}){sep}(\\d{{2}}){sep}(\\d{{4}}){sep}')  # 匹配 /2025/02/0107/ 格式
            
            # 检查所有日期相关的路径
            date_related_paths = {
                'tsb_logs_dir': paths.tsb_logs_dir,
                'log_dir': paths.log_dir,
                'backup_dir': paths.backup_dir
            }
            
            print("\n=== 测试路径格式 ===")
            for path_name, path_value in date_related_paths.items():
                print(f"{path_name}: {path_value}")
                
                # 检查是否包含yyyy-mm-dd格式（这是不期望的）
                wrong_format_match = yyyy_mm_dd_pattern.search(path_value)
                if wrong_format_match:
                    pytest.fail(
                        f"{path_name}路径中包含错误的日期格式 'yyyy-mm-dd': {wrong_format_match.group(1)}\n"
                        f"完整路径: {path_value}\n"
                        f"预期格式应该是 'yyyymmdd' 或 'yyyy/ww/mm/dd'"
                    )
                
                if path_name == 'tsb_logs_dir':
                    # tsb_logs_dir使用新的yyyy/Www/mmdd格式
                    tsb_format_match = tsb_logs_pattern.search(path_value)
                    assert tsb_format_match, (
                        f"{path_name}路径中未找到正确的日期格式 'yyyy/Www/mmdd'\n"
                        f"完整路径: {path_value}\n"
                        f"预期应该包含类似 '2025/02/0107' 的格式（年/周/月日）"
                    )
                    
                    # 验证tsb_logs_dir的各个组件
                    year, week, monthday = tsb_format_match.groups()
                    
                    assert len(year) == 4, f"{path_name}的年份长度应该是4位，实际: {len(year)}"
                    assert year.isdigit(), f"{path_name}的年份应该全部是数字，实际: {year}"
                    assert 2020 <= int(year) <= 2030, f"{path_name}的年份不合理: {year}"
                    
                    assert len(week) == 2, f"{path_name}的周数长度应该是2位数字，实际: {len(week)}"
                    assert week.isdigit(), f"{path_name}的周数应该是数字，实际: {week}"
                    assert 1 <= int(week) <= 53, f"{path_name}的周数不合理: {week}"
                    
                    assert len(monthday) == 4, f"{path_name}的月日长度应该是4位，实际: {len(monthday)}"
                    assert monthday.isdigit(), f"{path_name}的月日应该全部是数字，实际: {monthday}"
                    month = int(monthday[:2])
                    day = int(monthday[2:])
                    assert 1 <= month <= 12, f"{path_name}的月份不合理: {month}"
                    assert 1 <= day <= 31, f"{path_name}的日期不合理: {day}"
                    
                else:
                    # log_dir 和 backup_dir 保持原有的yyyymmdd格式
                    correct_format_match = yyyymmdd_pattern.search(path_value)
                    assert correct_format_match, (
                        f"{path_name}路径中未找到正确的日期格式 'yyyymmdd'\n"
                        f"完整路径: {path_value}\n"
                        f"预期应该包含类似 '20250107' 的格式"
                    )
                    
                    # 验证日期格式具体值
                    date_part = correct_format_match.group(1)
                    assert len(date_part) == 8, f"{path_name}的日期部分长度应该是8位，实际: {len(date_part)}"
                    assert date_part.isdigit(), f"{path_name}的日期部分应该全部是数字，实际: {date_part}"
                    
                    # 验证日期的合理性（年月日格式）
                    year = int(date_part[:4])
                    month = int(date_part[4:6])
                    day = int(date_part[6:8])
                    
                    assert 2020 <= year <= 2030, f"{path_name}的年份不合理: {year}"
                    assert 1 <= month <= 12, f"{path_name}的月份不合理: {month}"
                    assert 1 <= day <= 31, f"{path_name}的日期不合理: {day}"
    
    def test_time_format_consistency_in_paths(self):
        """
        测试时间格式的一致性
        
        验证所有路径中的时间部分都使用HHMMSS格式
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试配置文件
            config_file = Path(temp_dir) / "config.yaml"
            test_time = "2025-01-07T18:15:20"
            
            config_content = f"""
project_name: test_project
experiment_name: experiment_name  
base_dir: {temp_dir}
first_start_time: '{test_time}'
"""
            config_file.write_text(config_content)
            
            # 获取配置管理器
            config = get_config_manager(
                config_path=str(config_file),
                test_mode=True,
                first_start_time=test_time
            )
            
            # 获取路径配置
            paths = config.paths
            
            # 时间格式正则表达式：查找路径末尾的6位数字（支持跨平台路径分隔符）
            sep = r'[/\\]'  # 匹配正斜杠或反斜杠
            time_pattern = re.compile(f'{sep}(\\d{{6}})$')
            
            # 检查包含时间的路径
            time_related_paths = {
                'tsb_logs_dir': paths.tsb_logs_dir,
                'log_dir': paths.log_dir,
                'backup_dir': paths.backup_dir
            }
            
            print("\n=== 测试时间格式 ===")
            for path_name, path_value in time_related_paths.items():
                print(f"{path_name}: {path_value}")
                
                time_match = time_pattern.search(path_value)
                assert time_match, (
                    f"{path_name}路径末尾未找到6位时间格式\n"
                    f"完整路径: {path_value}\n"
                    f"预期应该以类似 '181520' 的格式结尾"
                )
                
                time_part = time_match.group(1)
                assert len(time_part) == 6, f"{path_name}的时间部分长度应该是6位，实际: {len(time_part)}"
                assert time_part.isdigit(), f"{path_name}的时间部分应该全部是数字，实际: {time_part}"
                
                # 验证时间的合理性（时分秒格式）
                hour = int(time_part[:2])
                minute = int(time_part[2:4])
                second = int(time_part[4:6])
                
                assert 0 <= hour <= 23, f"{path_name}的小时不合理: {hour}"
                assert 0 <= minute <= 59, f"{path_name}的分钟不合理: {minute}"
                assert 0 <= second <= 59, f"{path_name}的秒数不合理: {second}"
    
    def test_specific_issue_case(self):
        """
        测试特定的issue案例
        
        基于GitHub issue #1的具体报告：
        - first_start_time: 2025-01-07T18:15:20
        - 预期日期格式: 20250107
        - 预期时间格式: 181520
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # 使用issue中的具体时间
            config_file = Path(temp_dir) / "config.yaml"
            test_time = "2025-01-07T18:15:20"
            
            config_content = f"""
project_name: test_project
experiment_name: experiment_name  
base_dir: {temp_dir}
first_start_time: '{test_time}'
"""
            config_file.write_text(config_content)
            
            # 获取配置管理器
            config = get_config_manager(
                config_path=str(config_file),
                test_mode=True,
                first_start_time=test_time
            )
            
            # 验证具体的路径格式
            expected_date = "20250107"
            expected_time = "181520"
            
            # 检查tsb_logs_dir（使用新的yyyy/Www/mmdd格式）
            # 2025-01-07是第2周
            dt = datetime.fromisoformat(test_time)
            expected_year = "2025"
            expected_week = f"{dt.isocalendar()[1]:02d}"  # 获取不带W前缀的周数
            expected_monthday = "0107"  # 月日合并格式
            
            assert expected_year in config.paths.tsb_logs_dir, (
                f"tsb_logs_dir应该包含年份 {expected_year}，"
                f"实际路径: {config.paths.tsb_logs_dir}"
            )
            assert expected_week in config.paths.tsb_logs_dir, (
                f"tsb_logs_dir应该包含周数 {expected_week}，"
                f"实际路径: {config.paths.tsb_logs_dir}"
            )
            assert expected_monthday in config.paths.tsb_logs_dir, (
                f"tsb_logs_dir应该包含月日 {expected_monthday}，"
                f"实际路径: {config.paths.tsb_logs_dir}"
            )
            assert expected_time in config.paths.tsb_logs_dir, (
                f"tsb_logs_dir应该包含时间 {expected_time}，"
                f"实际路径: {config.paths.tsb_logs_dir}"
            )
            
            # 检查log_dir
            assert expected_date in config.paths.log_dir, (
                f"log_dir应该包含日期 {expected_date}，"
                f"实际路径: {config.paths.log_dir}"
            )
            assert expected_time in config.paths.log_dir, (
                f"log_dir应该包含时间 {expected_time}，"
                f"实际路径: {config.paths.log_dir}"
            )
            
            # 检查backup_dir
            assert expected_date in config.paths.backup_dir, (
                f"backup_dir应该包含日期 {expected_date}，"
                f"实际路径: {config.paths.backup_dir}"
            )
            assert expected_time in config.paths.backup_dir, (
                f"backup_dir应该包含时间 {expected_time}，"
                f"实际路径: {config.paths.backup_dir}"
            )
            
            # 确保不包含错误格式
            wrong_date_format = "2025-01-07"
            # tsb_logs_dir现在使用新格式，不需要检查这个错误格式
            assert wrong_date_format not in config.paths.log_dir, (
                f"log_dir不应该包含错误的日期格式 {wrong_date_format}，"
                f"实际路径: {config.paths.log_dir}"
            )
    
    def test_production_mode_issue(self):
        """
        测试生产模式下的日期格式问题
        
        这个测试专门重现生产模式下观察到的bug：
        - tsb_logs_dir 和 log_dir 使用了错误的 yyyy-mm-dd 格式
        - backup_dir 使用了正确的 yyyymmdd 格式
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试配置文件
            config_file = Path(temp_dir) / "config.yaml"
            test_time = "2025-01-07T18:15:20"
            
            config_content = f"""
project_name: test_project
experiment_name: experiment_name  
base_dir: {temp_dir}
first_start_time: '{test_time}'
"""
            config_file.write_text(config_content)
            
            # 获取配置管理器 - 使用生产模式
            config = get_config_manager(
                config_path=str(config_file),
                test_mode=False,  # 关键：使用生产模式
                first_start_time=test_time
            )
            
            # 在生产模式下验证路径格式
            expected_date = "20250107"
            wrong_date_format = "2025-01-07"
            
            print("\n=== 生产模式路径格式检查 ===")
            print(f"tsb_logs_dir: {config.paths.tsb_logs_dir}")
            print(f"log_dir: {config.paths.log_dir}")  
            print(f"backup_dir: {config.paths.backup_dir}")
            
            # 检查不应该包含错误格式（只针对log_dir）
            assert wrong_date_format not in config.paths.log_dir, (
                f"生产模式下log_dir不应该包含错误的日期格式 {wrong_date_format}，"
                f"实际路径: {config.paths.log_dir}"
            )
            
            # 检查tsb_logs_dir的新格式（yyyy/Www/mmdd）
            dt = datetime.fromisoformat(test_time)
            expected_year = "2025"
            expected_week = f"{dt.isocalendar()[1]:02d}"
            
            assert expected_year in config.paths.tsb_logs_dir, (
                f"生产模式下tsb_logs_dir应该包含年份 {expected_year}，"
                f"实际路径: {config.paths.tsb_logs_dir}"
            )
            assert expected_week in config.paths.tsb_logs_dir, (
                f"生产模式下tsb_logs_dir应该包含周数 {expected_week}，"
                f"实际路径: {config.paths.tsb_logs_dir}"
            )
            
            # 检查log_dir和backup_dir的原有格式
            assert expected_date in config.paths.log_dir, (
                f"生产模式下log_dir应该包含正确的日期格式 {expected_date}，"
                f"实际路径: {config.paths.log_dir}"
            )
            assert expected_date in config.paths.backup_dir, (
                f"生产模式下backup_dir应该包含正确的日期格式 {expected_date}，"
                f"实际路径: {config.paths.backup_dir}"
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])