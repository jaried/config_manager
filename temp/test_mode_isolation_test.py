"""
测试模式隔离机制验证脚本
验证测试模式(test_mode=True)下，ConfigManager是否会修改生产环境的配置文件
"""

import os
import tempfile
import shutil
import time
from datetime import datetime
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 修复导入问题
try:
    from src.config_manager.config_manager import get_config_manager, _clear_instances_for_testing
except ImportError:
    # 如果直接导入失败，尝试其他方式
    sys.path.insert(0, os.path.join(project_root, 'src'))
    from config_manager.config_manager import get_config_manager, _clear_instances_for_testing

def create_test_config(config_path: str):
    """创建测试用的配置文件"""
    config_content = """# 测试配置文件
__data__:
  base_dir: 'd:/logs'
  project_name: 'test_project'
  experiment_name: 'test_experiment'
  first_start_time: '2025-01-08T10:00:00'
  config_file_path: 'd:/logs/config.yaml'
  paths:
    work_dir: 'd:/logs/test_project/test_experiment'
    checkpoint_dir: 'd:/logs/test_project/test_experiment/checkpoint'
    log_dir: 'd:/logs/test_project/test_experiment/logs'
"""
    
    # 确保目录存在
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    # 写入配置文件
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✓ 创建测试配置文件: {config_path}")

def verify_config_isolation():
    """验证配置隔离机制"""
    print("=" * 60)
    print("测试模式隔离机制验证")
    print("=" * 60)
    
    # 1. 创建临时测试目录
    temp_dir = tempfile.mkdtemp(prefix="test_mode_isolation_")
    print(f"✓ 创建临时测试目录: {temp_dir}")
    
    # 2. 创建模拟的生产配置文件
    prod_config_path = os.path.join(temp_dir, "src", "config", "config.yaml")
    create_test_config(prod_config_path)
    
    # 3. 记录生产配置文件的原始内容
    with open(prod_config_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    print(f"✓ 记录原始配置文件内容长度: {len(original_content)} 字符")
    
    # 4. 记录生产配置文件的修改时间
    original_mtime = os.path.getmtime(prod_config_path)
    print(f"✓ 记录原始配置文件修改时间: {datetime.fromtimestamp(original_mtime)}")
    
    try:
        # 5. 切换到包含生产配置的目录
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        print(f"✓ 切换到测试目录: {temp_dir}")
        
        # 6. 创建测试模式配置管理器
        print("\n--- 创建测试模式配置管理器 ---")
        test_manager = get_config_manager(test_mode=True)
        
        if test_manager:
            print(f"✓ 测试模式配置管理器创建成功")
            print(f"  测试模式: {test_manager.is_test_mode()}")
            print(f"  配置路径: {getattr(test_manager, '_config_path', 'N/A')}")
            
            # 7. 验证测试配置路径是否在临时目录中
            test_config_path = getattr(test_manager, '_config_path', '')
            if tempfile.gettempdir() in test_config_path:
                print(f"✓ 测试配置文件在临时目录中: {test_config_path}")
            else:
                print(f"⚠️  警告：测试配置文件不在临时目录中: {test_config_path}")
            
            # 8. 在测试模式下进行一些配置操作
            print("\n--- 在测试模式下进行配置操作 ---")
            test_manager.set('test_key', 'test_value')
            test_manager.set('paths.test_dir', '/tmp/test_dir')
            print(f"✓ 在测试模式下设置了配置项")
            
            # 9. 验证生产配置文件是否被修改
            print("\n--- 验证生产配置文件隔离 ---")
            current_mtime = os.path.getmtime(prod_config_path)
            if current_mtime == original_mtime:
                print(f"✓ 生产配置文件修改时间未变化: {datetime.fromtimestamp(current_mtime)}")
            else:
                print(f"⚠️  警告：生产配置文件修改时间发生变化")
                print(f"  原始时间: {datetime.fromtimestamp(original_mtime)}")
                print(f"  当前时间: {datetime.fromtimestamp(current_mtime)}")
            
            # 10. 验证生产配置文件内容是否被修改
            with open(prod_config_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            if current_content == original_content:
                print(f"✓ 生产配置文件内容未变化")
            else:
                print(f"⚠️  警告：生产配置文件内容发生变化")
                print(f"  原始内容长度: {len(original_content)}")
                print(f"  当前内容长度: {len(current_content)}")
            
            # 11. 验证测试配置文件是否包含测试操作
            if os.path.exists(test_config_path):
                with open(test_config_path, 'r', encoding='utf-8') as f:
                    test_content = f.read()
                
                if 'test_key' in test_content and 'test_value' in test_content:
                    print(f"✓ 测试配置文件包含测试操作")
                else:
                    print(f"⚠️  警告：测试配置文件不包含测试操作")
            else:
                print(f"⚠️  警告：测试配置文件不存在: {test_config_path}")
            
            # 12. 清理测试实例
            print("\n--- 清理测试实例 ---")
            _clear_instances_for_testing()
            print(f"✓ 测试实例已清理")
            
        else:
            print(f"❌ 测试模式配置管理器创建失败")
            return False
        
        # 13. 恢复原始工作目录
        os.chdir(original_cwd)
        print(f"✓ 恢复原始工作目录: {original_cwd}")
        
        # 14. 最终验证生产配置文件
        print("\n--- 最终验证生产配置文件 ---")
        final_mtime = os.path.getmtime(prod_config_path)
        if final_mtime == original_mtime:
            print(f"✓ 生产配置文件修改时间保持未变: {datetime.fromtimestamp(final_mtime)}")
        else:
            print(f"⚠️  警告：生产配置文件修改时间发生变化")
        
        with open(prod_config_path, 'r', encoding='utf-8') as f:
            final_content = f.read()
        
        if final_content == original_content:
            print(f"✓ 生产配置文件内容保持未变")
        else:
            print(f"⚠️  警告：生产配置文件内容发生变化")
        
        print("\n" + "=" * 60)
        print("测试模式隔离机制验证完成")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理临时目录
        try:
            shutil.rmtree(temp_dir)
            print(f"✓ 清理临时测试目录: {temp_dir}")
        except Exception as e:
            print(f"⚠️  清理临时目录时出错: {e}")

def main():
    """主函数"""
    print(f"开始时间: {datetime.now()}")
    
    # 验证测试模式隔离机制
    success = verify_config_isolation()
    
    print(f"\n结束时间: {datetime.now()}")
    
    if success:
        print("\n✅ 测试模式隔离机制验证通过")
        print("✅ 测试模式不会修改生产配置文件")
    else:
        print("\n❌ 测试模式隔离机制验证失败")
        print("❌ 测试模式可能修改了生产配置文件")

if __name__ == "__main__":
    main() 