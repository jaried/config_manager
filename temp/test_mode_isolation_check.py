#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试模式隔离验证脚本
验证test_mode=True时是否会修改生产配置文件
"""

import os
import tempfile
import shutil
from datetime import datetime
from src.config_manager.config_manager import get_config_manager, _clear_instances_for_testing

def test_mode_isolation_check():
    """验证测试模式的隔离机制"""
    print("=== 测试模式隔离验证 ===")
    
    # 清理现有实例
    _clear_instances_for_testing()
    
    # 1. 创建生产配置文件
    print("\n1. 创建生产配置文件...")
    prod_config_content = """__data__:
  app_name: "生产应用"
  version: "2.0.0"
  database:
    host: "prod-db"
    port: 3306
  test_value: "production_original"
__type_hints__: {}"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        f.write(prod_config_content)
        prod_config_path = f.name
    
    print(f"✓ 生产配置文件路径: {prod_config_path}")
    
    try:
        # 2. 创建生产模式配置管理器
        print("\n2. 创建生产模式配置管理器...")
        prod_cfg = get_config_manager(config_path=prod_config_path, test_mode=False)
        print(f"✓ 生产模式配置路径: {prod_cfg.get_config_file_path()}")
        print(f"✓ 生产模式test_value: {prod_cfg.get('test_value')}")
        
        # 3. 创建测试模式配置管理器
        print("\n3. 创建测试模式配置管理器...")
        test_cfg = get_config_manager(config_path=prod_config_path, test_mode=True)
        test_config_path = test_cfg.get_config_file_path()
        print(f"✓ 测试模式配置路径: {test_config_path}")
        print(f"✓ 测试模式test_value: {test_cfg.get('test_value')}")
        
        # 4. 验证路径隔离
        print("\n4. 验证路径隔离...")
        assert prod_config_path != test_config_path, "生产配置路径和测试配置路径应该不同"
        assert tempfile.gettempdir() in test_config_path, "测试配置应该在临时目录中"
        print("✓ 路径隔离验证通过")
        
        # 5. 修改测试配置
        print("\n5. 修改测试配置...")
        test_cfg.test_value = "test_modified"
        test_cfg.save()
        print(f"✓ 测试配置test_value已修改为: {test_cfg.get('test_value')}")
        
        # 6. 验证生产配置未被修改
        print("\n6. 验证生产配置未被修改...")
        # 重新加载生产配置
        prod_cfg.reload()
        prod_test_value = prod_cfg.get('test_value')
        print(f"✓ 生产配置test_value: {prod_test_value}")
        
        assert prod_test_value == "production_original", f"生产配置应该保持原值，实际: {prod_test_value}"
        print("✓ 生产配置隔离验证通过")
        
        # 7. 验证测试配置修改生效
        print("\n7. 验证测试配置修改生效...")
        test_cfg.reload()
        test_test_value = test_cfg.get('test_value')
        print(f"✓ 测试配置test_value: {test_test_value}")
        
        assert test_test_value == "test_modified", f"测试配置应该保持修改值，实际: {test_test_value}"
        print("✓ 测试配置修改验证通过")
        
        # 8. 验证实例隔离
        print("\n8. 验证实例隔离...")
        assert prod_cfg is not test_cfg, "生产模式和测试模式应该是不同的实例"
        print("✓ 实例隔离验证通过")
        
        # 9. 验证文件内容
        print("\n9. 验证文件内容...")
        # 读取生产配置文件内容
        with open(prod_config_path, 'r', encoding='utf-8') as f:
            prod_file_content = f.read()
        
        # 读取测试配置文件内容
        with open(test_config_path, 'r', encoding='utf-8') as f:
            test_file_content = f.read()
        
        assert "production_original" in prod_file_content, "生产配置文件应包含原始值"
        assert "test_modified" in test_file_content, "测试配置文件应包含修改值"
        assert prod_file_content != test_file_content, "两个配置文件内容应该不同"
        print("✓ 文件内容隔离验证通过")
        
        print("\n=== 所有隔离验证通过 ===")
        return True
        
    except Exception as e:
        print(f"\n❌ 隔离验证失败: {e}")
        return False
        
    finally:
        # 清理临时文件
        print("\n10. 清理临时文件...")
        try:
            if prod_config_path.startswith(tempfile.gettempdir()):
                os.unlink(prod_config_path)
                print("✓ 生产配置文件已清理")
        except:
            pass
        
        # 清理测试环境
        _clear_instances_for_testing()
        print("✓ 实例已清理")

if __name__ == "__main__":
    success = test_mode_isolation_check()
    if success:
        print("\n🎉 测试模式隔离机制验证成功！")
    else:
        print("\n💥 测试模式隔离机制验证失败！") 