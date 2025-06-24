# test_logger.py
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from config_manager.logger import get_minimal_logger
    
    print("=== 测试最简logger ===")
    
    # 获取logger实例
    logger = get_minimal_logger("test")
    
    # 测试基本功能
    print("测试DEBUG日志:")
    logger.debug("这是一条DEBUG日志")
    
    print("测试INFO日志:")
    logger.info("这是一条INFO日志")
    
    print("测试格式化:")
    logger.info("用户 {} 登录", "张三")
    
    print("测试WARNING日志:")
    logger.warning("这是一条WARNING日志")
    
    print("测试ERROR日志:")
    logger.error("这是一条ERROR日志")
    
    print("=== 测试完成 ===")
    
except Exception as e:
    print(f"测试失败: {e}")
    import traceback
    traceback.print_exc() 