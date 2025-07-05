# debug_test.py - 验证日期格式修改
from __future__ import annotations
from datetime import datetime
from src.config_manager import get_config_manager

def test_date_format():
    """测试新的日期格式"""
    print("=== 日期格式验证测试 ===")
    
    # 创建测试配置管理器
    fixed_time = datetime(2025, 7, 5, 14, 30, 45)
    config = get_config_manager(test_mode=True, first_start_time=fixed_time)
    
    # 检查路径中的日期格式
    print(f"first_start_time: {config.first_start_time}")
    print(f"tsb_logs_dir: {config.paths.tsb_logs_dir}")
    print(f"log_dir: {config.paths.log_dir}")
    print(f"backup_dir: {config.paths.backup_dir}")
    
    # 验证日期格式为 YYYYMMDD
    assert '20250705' in config.paths.tsb_logs_dir, f"tsb_logs_dir 应包含 20250705: {config.paths.tsb_logs_dir}"
    assert '20250705' in config.paths.log_dir, f"log_dir 应包含 20250705: {config.paths.log_dir}"
    assert '20250705' in config.paths.backup_dir, f"backup_dir 应包含 20250705: {config.paths.backup_dir}"
    
    # 验证时间格式为 HHMMSS  
    assert '143045' in config.paths.tsb_logs_dir, f"tsb_logs_dir 应包含 143045: {config.paths.tsb_logs_dir}"
    assert '143045' in config.paths.log_dir, f"log_dir 应包含 143045: {config.paths.log_dir}"
    assert '143045' in config.paths.backup_dir, f"backup_dir 应包含 143045: {config.paths.backup_dir}"
    
    # 验证不包含旧格式的连字符
    assert '2025-07-05' not in config.paths.tsb_logs_dir, f"tsb_logs_dir 不应包含旧格式: {config.paths.tsb_logs_dir}"
    assert '2025-07-05' not in config.paths.log_dir, f"log_dir 不应包含旧格式: {config.paths.log_dir}"
    assert '2025-07-05' not in config.paths.backup_dir, f"backup_dir 不应包含旧格式: {config.paths.backup_dir}"
    
    print("✓ 所有日期格式验证通过！")
    print("✓ 新格式：YYYYMMDD/HHMMSS")

if __name__ == '__main__':
    test_date_format()