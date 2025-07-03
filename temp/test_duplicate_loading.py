# temp/test_duplicate_loading.py
from __future__ import annotations
import threading
import time
from config_manager.config_manager import get_config_manager, debug_instances, get_instance_count

def test_duplicate_loading():
    """测试重复加载问题"""
    print("=== 测试重复加载问题 ===")
    
    # 清理之前的实例
    from config_manager.config_manager import _clear_instances_for_testing
    _clear_instances_for_testing()
    
    print(f"初始实例数量: {get_instance_count()}")
    
    # 第一次调用
    print("\n1. 第一次调用get_config_manager()")
    cfg1 = get_config_manager(
        config_path="temp/test_config.yaml",
        watch=False,
        auto_create=True,
        first_start_time=None
    )
    print(f"第一次调用后实例数量: {get_instance_count()}")
    
    # 第二次调用（相同参数）
    print("\n2. 第二次调用get_config_manager()（相同参数）")
    cfg2 = get_config_manager(
        config_path="temp/test_config.yaml",
        watch=False,
        auto_create=True,
        first_start_time=None
    )
    print(f"第二次调用后实例数量: {get_instance_count()}")
    print(f"两个实例是否相同: {cfg1 is cfg2}")
    
    # 第三次调用（不同参数）
    print("\n3. 第三次调用get_config_manager()（不同参数）")
    cfg3 = get_config_manager(
        config_path="temp/test_config2.yaml",
        watch=False,
        auto_create=True,
        first_start_time=None
    )
    print(f"第三次调用后实例数量: {get_instance_count()}")
    print(f"cfg1和cfg3是否相同: {cfg1 is cfg3}")
    
    # 显示所有实例信息
    print("\n4. 显示所有实例信息")
    debug_instances()
    
    return True

def test_multithread_loading():
    """测试多线程环境下的重复加载"""
    print("\n=== 测试多线程环境下的重复加载 ===")
    
    # 清理之前的实例
    from config_manager.config_manager import _clear_instances_for_testing
    _clear_instances_for_testing()
    
    results = []
    
    def worker_thread(thread_id: int):
        """工作线程函数"""
        try:
            cfg = get_config_manager(
                config_path=f"temp/thread_{thread_id}_config.yaml",
                watch=False,
                auto_create=True,
                first_start_time=None
            )
            results.append((thread_id, cfg is not None))
            print(f"线程 {thread_id} 完成，实例数量: {get_instance_count()}")
        except Exception as e:
            print(f"线程 {thread_id} 失败: {e}")
            results.append((thread_id, False))
    
    # 创建多个线程
    threads = []
    for i in range(3):
        thread = threading.Thread(target=worker_thread, args=(i,))
        threads.append(thread)
    
    # 启动所有线程
    for thread in threads:
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    print(f"多线程测试完成，最终实例数量: {get_instance_count()}")
    print(f"线程结果: {results}")
    
    # 显示所有实例信息
    debug_instances()
    
    return True

if __name__ == "__main__":
    print("开始测试重复加载问题...")
    
    # 测试基本重复加载
    success1 = test_duplicate_loading()
    
    # 测试多线程重复加载
    success2 = test_multithread_loading()
    
    if success1 and success2:
        print("\n✓ 所有测试通过")
    else:
        print("\n✗ 部分测试失败") 