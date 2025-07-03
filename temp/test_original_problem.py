# temp/test_original_problem.py
from __future__ import annotations
import tempfile
import os
import shutil
from datetime import datetime

# 导入配置管理器
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from config_manager import get_config_manager, _clear_instances_for_testing


def test_original_problem_fix():
    """验证原始问题的修复"""
    print("=== 验证原始问题修复 ===")
    
    # 清理实例
    _clear_instances_for_testing()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, 'config.yaml')
        
        # 创建一个包含Windows路径的配置文件（模拟FuturesTradingPL的配置）
        original_config = '''__data__:
  base_dir: "d:\\logs"
  project_name: "FuturesTradingPL"
  experiment_name: "feature_network_mvp"
  app_name: "Feature Network训练系统"
  version: "1.0.0"
  paths:
    work_dir: "d:\\logs\\FuturesTradingPL\\feature_network_mvp"
    checkpoint_dir: "d:\\logs\\FuturesTradingPL\\feature_network_mvp\\checkpoint"
    log_dir: "d:\\logs\\FuturesTradingPL\\feature_network_mvp\\logs"
  logs:
    base_root_dir: ".\\logs"
__type_hints__: {}'''
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(original_config)
        
        print(f"1. 创建了包含Windows路径的配置文件: {config_path}")
        
        # 备份原始内容
        original_content = original_config
        
        # 尝试加载配置（这在修复前会失败）
        print("2. 尝试加载配置...")
        config = get_config_manager(
            config_path=config_path,
            auto_create=True,
            first_start_time=datetime.now()
        )
        
        if config is None:
            print("❌ 配置加载失败")
            return False
        
        print("✅ 配置加载成功")
        
        # 验证配置内容
        print("3. 验证配置内容...")
        try:
            assert config.project_name == "FuturesTradingPL"
            assert config.experiment_name == "feature_network_mvp"
            assert hasattr(config, 'base_dir')
            assert hasattr(config, 'paths')
            print("✅ 配置内容验证成功")
        except Exception as e:
            print(f"❌ 配置内容验证失败: {e}")
            return False
        
        # 验证原始文件没有被破坏
        print("4. 验证原始文件完整性...")
        with open(config_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        # 检查关键字段是否保留
        if ('project_name' in current_content and 
            'FuturesTradingPL' in current_content and
            'feature_network_mvp' in current_content):
            print("✅ 原始配置文件完整性验证成功")
        else:
            print("❌ 原始配置文件被破坏")
            print(f"当前内容: {current_content[:200]}...")
            return False
        
        # 测试保存功能
        print("5. 测试配置保存功能...")
        config.set('test_key', 'test_value')
        config.save()
        
        # 重新加载验证
        _clear_instances_for_testing()
        config2 = get_config_manager(
            config_path=config_path,
            auto_create=False
        )
        
        if config2 and hasattr(config2, 'test_key') and config2.test_key == 'test_value':
            print("✅ 配置保存和重新加载成功")
        else:
            print("❌ 配置保存或重新加载失败")
            return False
        
        print("🎉 所有测试通过！原始问题已修复")
        return True


def test_error_protection():
    """测试错误保护机制"""
    print("\n=== 验证错误保护机制 ===")
    
    _clear_instances_for_testing()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, 'config.yaml')
        
        # 创建一个有语法错误的配置文件
        invalid_config = '''__data__:
  project_name: "TestProject"
  base_dir: "d:\\invalid\\escape\\sequence"
  invalid_yaml: [unclosed list
__type_hints__: {}'''
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(invalid_config)
        
        print(f"1. 创建了有语法错误的配置文件: {config_path}")
        
        # 尝试加载配置
        print("2. 尝试加载有错误的配置...")
        config = get_config_manager(
            config_path=config_path,
            auto_create=True  # 即使设置auto_create=True也不应该覆盖
        )
        
        if config is None:
            print("✅ 正确拒绝了有错误的配置")
        else:
            print("❌ 错误地接受了有错误的配置")
            return False
        
        # 验证原始文件没有被覆盖
        print("3. 验证原始文件没有被覆盖...")
        with open(config_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        if current_content == invalid_config:
            print("✅ 原始错误文件没有被覆盖")
        else:
            print("❌ 原始错误文件被覆盖了")
            return False
        
        print("🎉 错误保护机制工作正常")
        return True


if __name__ == "__main__":
    success1 = test_original_problem_fix()
    success2 = test_error_protection()
    
    if success1 and success2:
        print("\n🎉🎉🎉 所有验证测试通过！修复成功！")
    else:
        print("\n❌❌❌ 部分测试失败，需要进一步修复") 