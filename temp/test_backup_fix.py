# temp/test_backup_fix.py
from __future__ import annotations
from datetime import datetime
import os
import tempfile
import time
import shutil

# 添加src目录到Python路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_manager import get_config_manager

def test_backup_fix():
    """测试备份重复问题是否已修复"""
    print("=== 测试备份重复问题修复 ===")
    
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
        config_path = tmp.name
    
    try:
        print(f"使用临时配置文件: {config_path}")
        
        # 清理可能存在的备份目录
        config_dir = os.path.dirname(config_path)
        backup_dir = os.path.join(config_dir, 'backup')
        if os.path.exists(backup_dir):
            print(f"清理现有备份目录: {backup_dir}")
            shutil.rmtree(backup_dir)
        
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
        
        # 等待一段时间，让自动保存完成
        print("\n2. 等待自动保存完成...")
        time.sleep(0.5)
        
        # 检查备份文件
        print("\n3. 检查备份文件...")
        
        if os.path.exists(backup_dir):
            backup_files = []
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    if file.endswith('.yaml'):
                        backup_files.append(os.path.join(root, file))
            
            print(f"找到 {len(backup_files)} 个备份文件:")
            for backup_file in backup_files:
                print(f"  - {backup_file}")
            
            # 检查是否只有当前测试的备份文件
            current_backup_files = [f for f in backup_files if os.path.basename(config_path).replace('.yaml', '') in f]
            
            if len(current_backup_files) == 1:
                print("✅ 当前测试的备份文件数量正确（只有1个）")
                return True
            else:
                print(f"❌ 当前测试的备份文件数量不正确（期望1个，实际{len(current_backup_files)}个）")
                return False
        else:
            print("❌ 备份目录不存在")
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
                shutil.rmtree(backup_dir)
        except Exception as e:
            print(f"清理临时文件时出错: {e}")

if __name__ == '__main__':
    success = test_backup_fix()
    if success:
        print("\n🎉 备份重复问题修复测试通过！")
    else:
        print("\n❌ 备份重复问题修复测试失败！") 