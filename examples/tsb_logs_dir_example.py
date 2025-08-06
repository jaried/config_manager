#!/usr/bin/env python3
# examples/tsb_logs_dir_example.py
"""
演示config_manager中tsb_logs_dir和tensorboard_dir的新功能
"""
from datetime import datetime
import time

from config_manager import get_config_manager


def main():
    print("=== TSB日志路径功能演示 ===\n")
    
    # 创建配置管理器
    config = get_config_manager(
        auto_create=True,
        first_start_time=datetime(2025, 1, 15, 10, 30, 45)
    )
    
    print("1. 基本路径访问：")
    print(f"   工作目录: {config.paths.work_dir}")
    print(f"   TSB日志目录: {config.paths.tsb_logs_dir}")
    print(f"   TensorBoard目录: {config.paths.tensorboard_dir}")
    
    # 验证路径格式
    tsb_path = config.paths.tsb_logs_dir
    parts = tsb_path.split('/')
    print("\n2. 路径格式分析：")
    print(f"   完整路径: {tsb_path}")
    print(f"   包含/tsb_logs/子目录: {'tsb_logs' in parts}")
    print(f"   年份: {[p for p in parts if p.isdigit() and len(p) == 4]}")
    print(f"   周数(无W前缀): {[p for p in parts if p.isdigit() and len(p) == 2]}")
    
    print("\n3. 路径一致性验证：")
    print(f"   tensorboard_dir == tsb_logs_dir: {config.paths.tensorboard_dir == config.paths.tsb_logs_dir}")
    
    print("\n4. 只读属性测试：")
    try:
        config.paths.tensorboard_dir = "/custom/path"
        print("   ❌ 不应该到达这里")
    except AttributeError as e:
        print(f"   ✓ 正确抛出异常: {e}")
    
    try:
        config.set('paths.tensorboard_dir', "/custom/path")
        print("   ❌ 不应该到达这里")
    except AttributeError as e:
        print(f"   ✓ 正确抛出异常: {e}")
    
    print("\n5. 缓存机制演示：")
    print("   连续访问10次（1秒内）：")
    start_time = time.time()
    first_path = config.paths.tsb_logs_dir
    for i in range(10):
        path = config.paths.tsb_logs_dir
        assert path == first_path, f"第{i+1}次访问路径不一致"
    elapsed = time.time() - start_time
    print(f"   ✓ 10次访问耗时: {elapsed:.4f}秒（使用缓存）")
    
    print("\n6. ISO周数计算示例：")
    test_dates = [
        datetime(2025, 1, 1),    # 年初
        datetime(2025, 6, 15),   # 年中
        datetime(2025, 12, 25),  # 年末
        datetime(2024, 12, 30),  # 跨年周
    ]
    
    for date in test_dates:
        iso_year, iso_week, iso_weekday = date.isocalendar()
        print(f"   {date.strftime('%Y-%m-%d')}: ISO年份={iso_year}, ISO周数={iso_week:02d}")
    
    print("\n7. 实际使用场景：")
    print("   在训练脚本中使用TSB日志目录：")
    print(f"   writer = SummaryWriter(log_dir='{config.paths.tsb_logs_dir}')")
    print(f"   # TSB日志会保存到: {config.paths.tsb_logs_dir}")
    print(f"   # TensorBoard可以从相同路径读取: {config.paths.tensorboard_dir}")
    
    # 保存配置
    config.save()
    print("\n✓ 配置已保存")


if __name__ == "__main__":
    main()