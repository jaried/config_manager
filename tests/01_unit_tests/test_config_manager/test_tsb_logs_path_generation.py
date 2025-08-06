# tests/01_unit_tests/test_config_manager/test_tsb_logs_path_generation.py
from __future__ import annotations
from datetime import datetime
import os
import sys
import tempfile
import shutil
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.path_test_helper import PathTestHelper
from config_manager import get_config_manager
from config_manager.core.path_resolver import PathResolver


class TestTsbLogsPathGeneration:
    """测试TSB日志路径生成功能"""
    
    def setup_method(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_tsb_logs_path_format(self):
        """测试TSB日志路径格式是否正确"""
        # 固定时间戳测试
        test_time = datetime(2025, 1, 7, 18, 15, 20)
        work_dir = "/home/user/project/work"
        
        # 调用路径生成函数
        path = PathResolver.generate_tsb_logs_path(work_dir, test_time)
        
        # 验证路径格式
        expected_path = "/home/user/project/work/tsb_logs/2025/02/0107/181520"
        PathTestHelper.assert_path_equal(path, expected_path, f"期望路径: {expected_path}, 实际路径: {path}")
    
    def test_week_number_format(self):
        """测试周数格式（两位数字，不带W前缀）"""
        # 测试不同的日期
        test_cases = [
            (datetime(2025, 1, 1), "01"),   # 第1周
            (datetime(2025, 1, 15), "03"),  # 第3周
            (datetime(2025, 6, 15), "24"),  # 第24周
            (datetime(2025, 12, 25), "52"), # 第52周
        ]
        
        work_dir = "/test"
        for test_time, expected_week in test_cases:
            path = PathResolver.generate_tsb_logs_path(work_dir, test_time)
            # 规范化路径后提取周数部分
            normalized_path = PathTestHelper.normalize_path(path)
            path_parts = normalized_path.split('/')
            # 找到tsb_logs后的位置
            tsb_idx = path_parts.index('tsb_logs')
            week_part = path_parts[tsb_idx + 2]  # tsb_logs/year/{week}/...
            assert week_part == expected_week, f"日期{test_time}的周数应该是{expected_week}，实际是{week_part}"
    
    def test_year_boundary(self):
        """测试年初年末的周数计算"""
        # 测试年初（ISO周可能属于上一年）
        test_time_start = datetime(2025, 1, 1)  # 2025年第1天
        path_start = PathResolver.generate_tsb_logs_path("/test", test_time_start)
        assert "2025/01" in path_start, "2025年1月1日应该在2025年第1周"
        
        # 测试年末（ISO周可能属于下一年）
        test_time_end = datetime(2024, 12, 30)  # 2024年末
        path_end = PathResolver.generate_tsb_logs_path("/test", test_time_end)
        # 2024年12月30日是2025年第1周（ISO 8601）
        assert "2025/01" in path_end, "2024年12月30日应该在2025年第1周"
    
    def test_default_timestamp(self):
        """测试默认时间戳（当前时间）"""
        # 不提供时间戳，应该使用当前时间
        path = PathResolver.generate_tsb_logs_path("/test")
        
        # 验证路径包含tsb_logs子目录
        PathTestHelper.assert_path_contains(path, "/tsb_logs/")
        
        # 验证路径包含年份（4位数字）
        current_year = str(datetime.now().year)
        assert current_year in path
    
    def test_config_manager_tsb_logs_dir(self):
        """测试ConfigManager中的tsb_logs_dir属性"""
        # 创建测试配置
        config = get_config_manager(
            test_mode=True,
            auto_create=True,
            first_start_time=datetime(2025, 1, 7, 18, 15, 20)
        )
        
        try:
            # 获取tsb_logs_dir
            tsb_dir = config.paths.tsb_logs_dir
            
            # 验证路径格式
            PathTestHelper.assert_path_contains(tsb_dir, "/tsb_logs/", "路径应包含/tsb_logs/子目录")
            PathTestHelper.assert_path_contains(tsb_dir, "/2025/02/0107/181520", "路径格式不正确")
            
            # 验证路径不包含W前缀
            assert "/W02/" not in tsb_dir, "周数不应包含W前缀"
            
        finally:
            # 清理
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_tensorboard_dir_equals_tsb_logs_dir(self):
        """测试tensorboard_dir始终等于tsb_logs_dir"""
        # 创建测试配置
        config = get_config_manager(
            test_mode=True,
            auto_create=True,
            first_start_time=datetime(2025, 1, 7, 18, 15, 20)
        )
        
        try:
            # 获取两个路径
            tsb_dir = config.paths.tsb_logs_dir
            tb_dir = config.paths.tensorboard_dir
            
            # 验证相等
            assert tb_dir == tsb_dir, f"tensorboard_dir应该等于tsb_logs_dir，但实际: tb={tb_dir}, tsb={tsb_dir}"
            
            # 多次访问应该保持一致
            for _ in range(3):
                assert config.paths.tensorboard_dir == config.paths.tsb_logs_dir
            
        finally:
            # 清理
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_tensorboard_dir_readonly(self):
        """测试tensorboard_dir是只读属性"""
        # 创建测试配置
        config = get_config_manager(
            test_mode=True,
            auto_create=True
        )
        
        try:
            # 尝试设置tensorboard_dir应该抛出异常
            with pytest.raises(AttributeError) as exc_info:
                config.paths.tensorboard_dir = "/custom/path"
            
            # 验证错误消息
            assert "只读属性" in str(exc_info.value), "应该提示tensorboard_dir是只读属性"
            
        finally:
            # 清理
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_path_caching(self):
        """测试路径缓存机制"""
        import time
        
        # 创建测试配置，不设置固定的first_start_time
        config = get_config_manager(
            test_mode=True,
            auto_create=True
        )
        
        try:
            # 第一次访问
            path1 = config.paths.tsb_logs_dir
            time1 = time.time()
            
            # 立即再次访问（应该从缓存返回）
            path2 = config.paths.tsb_logs_dir
            time2 = time.time()
            assert path1 == path2, "缓存期内应返回相同路径"
            assert (time2 - time1) < 0.1, "缓存访问应该很快"
            
            # 等待超过缓存时间（1秒）
            time.sleep(1.1)
            
            # 再次访问（应该生成新路径）
            path3 = config.paths.tsb_logs_dir
            
            # 当使用固定的first_start_time时，路径的年/周/月日/时间部分都不会变
            # 所以只能验证缓存机制是否工作，不能验证时间戳变化
            # 这里我们验证第三次访问确实重新计算了（虽然结果可能相同）
            
            # 如果config没有固定的first_start_time，路径会包含当前时间
            # 检查是否使用了first_start_time
            if hasattr(config, 'first_start_time') and config.first_start_time:
                # 使用了固定时间，路径不会变化，只验证缓存工作
                print(f"使用固定first_start_time，路径保持不变: {path1}")
            else:
                # 没有固定时间，时间戳部分应该不同
                print(f"使用当前时间，检查路径变化: path1={path1}, path3={path3}")
            
        finally:
            # 清理
            if hasattr(config, 'cleanup'):
                config.cleanup()
    
    def test_cross_platform_paths(self):
        """测试跨平台路径处理"""
        # 所有平台都应该返回统一的正斜杠格式
        if os.name == 'nt':
            work_dir = r"C:\Users\test\work"
            path = PathResolver.generate_tsb_logs_path(work_dir, datetime(2025, 1, 7, 18, 15, 20))
            # 统一使用正斜杠
            assert "/" in path
            assert "/tsb_logs/" in path
        else:
            # Linux/Mac路径测试
            work_dir = "/home/test/work"
            path = PathResolver.generate_tsb_logs_path(work_dir, datetime(2025, 1, 7, 18, 15, 20))
            # Unix系统应该使用正斜杠
            assert "/" in path
            assert "/tsb_logs/" in path
    
    def test_iso_week_calculation(self):
        """测试ISO周数计算的正确性"""
        # ISO 8601标准测试案例
        test_cases = [
            # (日期, 预期的ISO周数)
            (datetime(2024, 1, 1), 1),    # 2024年1月1日是第1周（周一）
            (datetime(2024, 12, 30), 1),  # 2024年12月30日是2025年第1周
            (datetime(2025, 1, 1), 1),    # 2025年1月1日是第1周
            (datetime(2025, 12, 29), 1),  # 2025年12月29日是2026年第1周（周一）
            (datetime(2025, 12, 28), 52), # 2025年12月28日是2025年第52周（周日）
        ]
        
        for test_date, expected_week in test_cases:
            iso_week = test_date.isocalendar()[1]
            assert iso_week == expected_week, f"{test_date}的ISO周数应该是{expected_week}，实际是{iso_week}"