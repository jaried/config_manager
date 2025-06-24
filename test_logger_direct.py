# test_logger_direct.py
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config_manager.logger.minimal_logger import debug, info, warning, error, critical

def test_logger():
    """测试简化后的logger"""
    print("=== 测试简化后的logger ===")
    
    debug("这是一条DEBUG日志")
    info("这是一条INFO日志")
    warning("这是一条WARNING日志")
    error("这是一条ERROR日志")
    critical("这是一条CRITICAL日志")
    
    # 测试格式化
    info("测试格式化: {} + {} = {}", 1, 2, 3)
    debug("测试关键字参数: name={}, age={}", name="张三", age=25)
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    test_logger() 