# temp/test_first_start_time_no_save.py
from __future__ import annotations
from datetime import datetime
import os
import tempfile
import time

# 添加src目录到Python路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_manager import get_config_manager

def test_first_start_time_no_save():
    """测试first_start_time变化不会触发自动保存"""
    print("=== 测试first_start_time变化不会触发自动保存 ===")
    
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        config_path = tmp.name
    
    try:
        print(f"使用临时配置文件: {config_path}")
        
        # 记录开始时间
        start_time = datetime.now()
        print(f"开始时间: {start_time}")
        
        # 创建配置管理器
        print("\n1. 创建配置管理器...")
        cfg = get_config_manager(
            config_path=config_path,
            watch=False,  # 禁用文件监视，避免干扰
            auto_create=True,
            autosave_delay=0.1,
            first_start_time=start_time
        )
        
        if cfg is None:
            print("❌ 配置管理器创建失败")
            return False
        
        print("✅ 配置管理器创建成功")
        
        # 等待初始化完成
        print("\n2. 等待初始化完成...")
        time.sleep(0.2)
        
        # 记录初始备份文件数量
        config_dir = os.path.dirname(config_path)
        backup_dir = os.path.join(config_dir, 'backup')
        
        if os.path.exists(backup_dir):
            initial_backup_files = []
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    if file.endswith('.yaml'):
                        initial_backup_files.append(os.path.join(root, file))
            initial_count = len(initial_backup_files)
            print(f"初始备份文件数量: {initial_count}")
        else:
            initial_count = 0
            print("初始备份文件数量: 0")
        
        # 修改first_start_time
        print("\n3. 修改first_start_time...")
        new_time = datetime.now()
        cfg.set('first_start_time', new_time.isoformat())
        
        # 等待一段时间，看是否会触发自动保存
        print("\n4. 等待观察是否触发自动保存...")
        time.sleep(0.3)
        
        # 检查备份文件数量是否增加
        print("\n5. 检查备份文件数量...")
        if os.path.exists(backup_dir):
            final_backup_files = []
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    if file.endswith('.yaml'):
                        final_backup_files.append(os.path.join(root, file))
            final_count = len(final_backup_files)
            print(f"最终备份文件数量: {final_count}")
        else:
            final_count = 0
            print("最终备份文件数量: 0")
        
        # 验证备份文件数量没有增加
        if final_count == initial_count:
            print("✅ first_start_time变化没有触发自动保存")
            return True
        else:
            print(f"❌ first_start_time变化触发了自动保存（期望{initial_count}个，实际{final_count}个）")
            return False
            
    finally:
        # 清理临时文件
        try:
            if os.path.exists(config_path):
                os.unlink(config_path)
            
            # 清理备份目录
            config_dir = os.path.dirname(config_path)
            backup_dir = os.path.join(config_dir, 'backup')
            if os.path.exists(backup_dir):
                import shutil
                shutil.rmtree(backup_dir)
        except Exception as e:
            print(f"清理临时文件时出错: {e}")

if __name__ == '__main__':
    success = test_first_start_time_no_save()
    if success:
        print("\n🎉 first_start_time变化不触发保存测试通过！")
    else:
        print("\n❌ first_start_time变化不触发保存测试失败！") 