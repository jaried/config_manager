# test_simple_logger.py
from src.config_manager.logger import debug, info, warning, error, critical

def test_logger():
    """测试简化后的logger"""
    print("=== 测试简化后的logger ===")
    
    debug("这是一条DEBUG日志")
    info("这是一条INFO日志")
    warning("这是一条WARNING日志")
    error("这是一条ERROR日志")
    critical("这是一条CRITICAL日志")
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    test_logger() 