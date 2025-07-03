# temp/comprehensive_isolation_test.py
"""
全面的测试模式隔离机制验证脚本
验证测试模式(test_mode=True)下的所有隔离机制
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
  test_data:
    key1: 'value1'
    key2: 'value2'
"""
    
    # 确保目录存在
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    # 写入配置文件
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✓ 创建测试配置文件: {config_path}")

def verify_comprehensive_isolation():
    """验证全面的配置隔离机制"""
    print("=" * 80)
    print("全面的测试模式隔离机制验证")
    print("=" * 80)
    
    # 1. 创建临时测试目录
    temp_dir = tempfile.mkdtemp(prefix="comprehensive_isolation_")
    print(f"✓ 创建临时测试目录: {temp_dir}")
    
    # 2. 创建模拟的生产配置文件
    prod_config_path = os.path.join(temp_dir, "src", "config", "config.yaml")
    create_test_config(prod_config_path)
    
    # 3. 记录生产配置文件的原始状态
    with open(prod_config_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    original_mtime = os.path.getmtime(prod_config_path)
    original_size = os.path.getsize(prod_config_path)
    
    print(f"✓ 记录原始配置文件状态:")
    print(f"  内容长度: {len(original_content)} 字符")
    print(f"  修改时间: {datetime.fromtimestamp(original_mtime)}")
    print(f"  文件大小: {original_size} 字节")
    
    try:
        # 4. 切换到包含生产配置的目录
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        print(f"✓ 切换到测试目录: {temp_dir}")
        
        # 5. 创建测试模式配置管理器
        print("\n" + "-" * 50)
        print("创建测试模式配置管理器")
        print("-" * 50)
        
        test_manager = get_config_manager(test_mode=True)
        
        if not test_manager:
            print(f"❌ 测试模式配置管理器创建失败")
            return False
        
        print(f"✓ 测试模式配置管理器创建成功")
        print(f"  测试模式: {test_manager.is_test_mode()}")
        print(f"  配置路径: {getattr(test_manager, '_config_path', 'N/A')}")
        
        # 6. 验证测试配置路径隔离
        test_config_path = getattr(test_manager, '_config_path', '')
        print(f"\n--- 验证配置文件路径隔离 ---")
        
        if tempfile.gettempdir() in test_config_path:
            print(f"✓ 测试配置文件在临时目录中: {test_config_path}")
        else:
            print(f"❌ 测试配置文件不在临时目录中: {test_config_path}")
            return False
        
        if test_config_path != prod_config_path:
            print(f"✓ 测试配置文件与生产配置文件路径不同")
        else:
            print(f"❌ 测试配置文件与生产配置文件路径相同")
            return False
        
        # 7. 验证测试配置文件存在且可读
        if os.path.exists(test_config_path):
            print(f"✓ 测试配置文件存在")
            with open(test_config_path, 'r', encoding='utf-8') as f:
                test_content = f.read()
            print(f"✓ 测试配置文件可读，内容长度: {len(test_content)} 字符")
        else:
            print(f"❌ 测试配置文件不存在: {test_config_path}")
            return False
        
        # 8. 在测试模式下进行各种配置操作
        print(f"\n--- 在测试模式下进行配置操作 ---")
        
        # 8.1 设置新配置项
        test_manager.set('new_test_key', 'new_test_value')
        print(f"✓ 设置了新配置项: new_test_key = new_test_value")
        
        # 8.2 修改现有配置项
        test_manager.set('test_data.key1', 'modified_value1')
        print(f"✓ 修改了现有配置项: test_data.key1 = modified_value1")
        
        # 8.3 设置路径配置
        test_manager.set('paths.test_dir', '/tmp/test_directory')
        print(f"✓ 设置了路径配置: paths.test_dir = /tmp/test_directory")
        
        # 8.4 设置复杂配置
        test_manager.set('complex_config', {
            'nested': {
                'key': 'value',
                'array': [1, 2, 3]
            }
        })
        print(f"✓ 设置了复杂配置: complex_config")
        
        # 9. 验证生产配置文件完全隔离
        print(f"\n--- 验证生产配置文件完全隔离 ---")
        
        # 9.1 验证修改时间
        current_mtime = os.path.getmtime(prod_config_path)
        if current_mtime == original_mtime:
            print(f"✓ 生产配置文件修改时间未变化: {datetime.fromtimestamp(current_mtime)}")
        else:
            print(f"❌ 生产配置文件修改时间发生变化")
            print(f"  原始时间: {datetime.fromtimestamp(original_mtime)}")
            print(f"  当前时间: {datetime.fromtimestamp(current_mtime)}")
            return False
        
        # 9.2 验证文件大小
        current_size = os.path.getsize(prod_config_path)
        if current_size == original_size:
            print(f"✓ 生产配置文件大小未变化: {current_size} 字节")
        else:
            print(f"❌ 生产配置文件大小发生变化")
            print(f"  原始大小: {original_size} 字节")
            print(f"  当前大小: {current_size} 字节")
            return False
        
        # 9.3 验证文件内容
        with open(prod_config_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        if current_content == original_content:
            print(f"✓ 生产配置文件内容完全未变化")
        else:
            print(f"❌ 生产配置文件内容发生变化")
            print(f"  原始内容长度: {len(original_content)}")
            print(f"  当前内容长度: {len(current_content)}")
            return False
        
        # 10. 验证测试配置文件包含所有操作
        print(f"\n--- 验证测试配置文件包含所有操作 ---")
        
        if os.path.exists(test_config_path):
            with open(test_config_path, 'r', encoding='utf-8') as f:
                updated_test_content = f.read()
            
            # 检查是否包含新设置的配置项
            checks = [
                ('new_test_key: new_test_value', 'new_test_key'),
                ('key1: \'modified_value1\'', 'test_data.key1'),
                ('test_dir: /tmp/test_directory', 'paths.test_dir'),
                ('nested:', 'complex_config.nested'),
            ]
            
            all_checks_passed = True
            for check_value, check_key in checks:
                if check_value in updated_test_content:
                    print(f"✓ 测试配置文件包含: {check_key}")
                else:
                    print(f"❌ 测试配置文件不包含: {check_key}")
                    print(f"  期望内容: {check_value}")
                    all_checks_passed = False
            
            if not all_checks_passed:
                return False
        else:
            print(f"❌ 测试配置文件不存在: {test_config_path}")
            return False
        
        # 11. 验证实例隔离
        print(f"\n--- 验证实例隔离 ---")
        
        # 11.1 验证测试模式标志
        if test_manager.is_test_mode():
            print(f"✓ 测试模式标志正确设置")
        else:
            print(f"❌ 测试模式标志未正确设置")
            return False
        
        # 11.2 验证实例ID
        test_instance_id = id(test_manager)
        print(f"✓ 测试实例ID: {test_instance_id}")
        
        # 12. 验证环境变量隔离
        print(f"\n--- 验证环境变量隔离 ---")
        
        test_mode_env = os.environ.get('CONFIG_MANAGER_TEST_MODE')
        test_base_dir_env = os.environ.get('CONFIG_MANAGER_TEST_BASE_DIR')
        
        if test_mode_env == 'true':
            print(f"✓ 测试模式环境变量正确设置: {test_mode_env}")
        else:
            print(f"❌ 测试模式环境变量未正确设置: {test_mode_env}")
            return False
        
        if test_base_dir_env and tempfile.gettempdir() in test_base_dir_env:
            print(f"✓ 测试基础目录环境变量正确设置: {test_base_dir_env}")
        else:
            print(f"❌ 测试基础目录环境变量未正确设置: {test_base_dir_env}")
            return False
        
        # 13. 清理测试实例
        print(f"\n--- 清理测试实例 ---")
        _clear_instances_for_testing()
        print(f"✓ 测试实例已清理")
        
        # 14. 恢复原始工作目录
        os.chdir(original_cwd)
        print(f"✓ 恢复原始工作目录: {original_cwd}")
        
        # 15. 最终验证生产配置文件
        print(f"\n--- 最终验证生产配置文件 ---")
        
        final_mtime = os.path.getmtime(prod_config_path)
        final_size = os.path.getsize(prod_config_path)
        
        with open(prod_config_path, 'r', encoding='utf-8') as f:
            final_content = f.read()
        
        # 验证所有属性都未变化
        if (final_mtime == original_mtime and 
            final_size == original_size and 
            final_content == original_content):
            print(f"✓ 生产配置文件完全未变化")
            print(f"  修改时间: {datetime.fromtimestamp(final_mtime)}")
            print(f"  文件大小: {final_size} 字节")
            print(f"  内容长度: {len(final_content)} 字符")
        else:
            print(f"❌ 生产配置文件发生变化")
            return False
        
        print("\n" + "=" * 80)
        print("全面的测试模式隔离机制验证完成")
        print("=" * 80)
        
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
    
    # 验证全面的测试模式隔离机制
    success = verify_comprehensive_isolation()
    
    print(f"\n结束时间: {datetime.now()}")
    
    if success:
        print("\n✅ 全面的测试模式隔离机制验证通过")
        print("✅ 测试模式完全隔离，不会修改生产配置文件")
        print("✅ 所有隔离机制工作正常")
    else:
        print("\n❌ 全面的测试模式隔离机制验证失败")
        print("❌ 测试模式可能存在隔离问题")

if __name__ == "__main__":
    main() 