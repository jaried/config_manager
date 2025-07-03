# temp/test_minimal_logger.py
from __future__ import annotations

import os
import sys
import tempfile
import shutil

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_manager.logger import get_minimal_logger


def test_minimal_logger():
    """测试最简logger功能"""
    print("=== 测试最简logger功能 ===")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    try:
        # 创建测试配置
        test_config = {
            'logger': {
                'console_level': 'DEBUG',
                'file_level': 'DEBUG',
                'log_dir': temp_dir
            }
        }
        
        # 获取logger实例
        logger = get_minimal_logger("test")
        
        # 测试各种日志级别
        print("\n1. 测试日志级别:")
        logger.debug("这是一条DEBUG日志")
        logger.info("这是一条INFO日志")
        logger.warning("这是一条WARNING日志")
        logger.error("这是一条ERROR日志")
        logger.critical("这是一条CRITICAL日志")
        
        # 测试格式化消息
        print("\n2. 测试格式化消息:")
        logger.info("用户 {} 在 {} 登录", "张三", "2025-01-07")
        logger.debug("配置项 {} 的值是 {}", "database.host", "localhost")
        
        # 检查日志文件
        print("\n3. 检查日志文件:")
        log_files = [f for f in os.listdir(temp_dir) if f.endswith('.log')]
        for log_file in log_files:
            log_path = os.path.join(temp_dir, log_file)
            print(f"日志文件: {log_file}")
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"文件大小: {len(content)} 字节")
                print("前几行内容:")
                lines = content.split('\n')[:5]
                for line in lines:
                    if line.strip():
                        print(f"  {line}")
        
        print("\n=== 测试完成 ===")
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_minimal_logger() 