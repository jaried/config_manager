#!/usr/bin/env python3
"""
config_manager多进程验证演示脚本
=============================

这是一个验证演示脚本，可以直接复制到任何项目中使用。
用于验证config_manager在多进程环境下的pickle序列化功能。

使用方法：
1. 确保config_manager已安装或可导入
2. 直接运行此脚本
3. 观察输出验证功能是否正常
"""

import multiprocessing as mp
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# 尝试导入config_manager - 根据您的项目调整导入路径
try:
    from config_manager import get_config_manager
except ImportError:
    print("❌ 无法导入config_manager")
    print("请确保config_manager已正确安装或调整导入路径")
    sys.exit(1)


def worker_function(config_data):
    """
    简单的worker函数，演示如何使用配置数据
    """
    worker_name = mp.current_process().name
    
    # 从配置中获取数据
    app_name = config_data.app_name
    batch_size = config_data.get('batch_size', 10)
    database_host = config_data.database.host
    
    # 模拟处理工作
    results = []
    for i in range(batch_size):
        results.append(f"{app_name}-{worker_name}-item-{i}")
    
    return {
        'worker': worker_name,
        'app': app_name,
        'db_host': database_host,
        'processed': len(results),
        'sample': results[:3]  # 返回前3个作为示例
    }


def run_multiprocess_demo():
    """主演示函数"""
    print("🧪 config_manager多进程演示")
    print("=" * 50)
    
    # 1. 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        config_path = tmp.name
    
    try:
        # 2. 创建配置管理器
        print("📝 创建配置管理器...")
        config = get_config_manager(
            config_path=config_path,
            auto_create=True,
            watch=False,
            first_start_time=datetime.now()
        )
        
        # 3. 设置配置数据
        print("⚙️  设置配置数据...")
        config.app_name = "DemoApp"
        config.batch_size = 5
        config.database = {
            'host': 'localhost',
            'port': 5432
        }
        
        # 4. 获取可序列化的配置数据
        print("📦 获取可序列化配置...")
        serializable_config = config.get_serializable_data()
        
        # 5. 验证pickle序列化
        import pickle
        try:
            pickle.dumps(serializable_config)
            print("✅ pickle序列化验证通过")
        except Exception as e:
            print(f"❌ pickle序列化失败: {e}")
            return False
        
        # 6. 演示多进程
        print("🚀 启动多进程演示...")
        
        with mp.Pool(processes=2) as pool:
            results = pool.map(worker_function, [serializable_config, serializable_config])
        
        # 7. 验证结果
        print("📊 演示结果:")
        for i, result in enumerate(results, 1):
            print(f"  Worker {i}: {result['worker']} 处理了 {result['processed']} 项")
            print(f"    应用名: {result['app']}")
            print(f"    数据库: {result['db_host']}")
            print(f"    示例数据: {result['sample']}")
        
        # 8. 验证配置一致性
        app_names = [r['app'] for r in results]
        if len(set(app_names)) == 1:
            print("✅ 所有worker使用了相同的配置")
        else:
            print("❌ worker配置不一致")
        
        print("\n🎉 演示完成！config_manager支持多进程环境")
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理临时文件
        try:
            Path(config_path).unlink()
            print(f"🧹 清理临时文件: {config_path}")
        except:
            pass


if __name__ == '__main__':
    # Windows兼容性设置
    if sys.platform.startswith('win'):
        mp.set_start_method('spawn', force=True)
    
    success = run_multiprocess_demo()
    
    if success:
        print("\n" + "=" * 50)
        print("🎯 在您的项目中使用config_manager多进程:")
        print("1. config = get_config_manager(...)")
        print("2. config.设置 = 值")
        print("3. serializable_config = config.get_serializable_data()")
        print("4. pool.map(worker_func, [serializable_config]*n)")
        print("5. 在worker中: config_data.设置")
    
    sys.exit(0 if success else 1) 