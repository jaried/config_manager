import tempfile
import os
import sys
import time

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.config_manager.config_manager import get_config_manager, _clear_instances_for_testing

# 清理实例
_clear_instances_for_testing()

# 创建临时配置文件
with tempfile.TemporaryDirectory() as tmpdir:
    config_file = os.path.join(tmpdir, 'test_config.yaml')
    
    print(f"配置文件路径: {config_file}")
    
    # 创建配置管理器并设置值
    cfg = get_config_manager(config_path=config_file, watch=False)
    print(f"配置管理器创建成功")
    
    # 设置值
    print("设置 backup_test = 'original_value'")
    cfg.backup_test = "original_value"
    
    print("设置 nested_backup.value = 'nested_value'")
    cfg.nested_backup = {}
    cfg.nested_backup.value = "nested_value"
    
    # 检查设置后的值
    print(f"设置后 backup_test: {cfg.backup_test}")
    print(f"设置后 nested_backup.value: {cfg.nested_backup.value}")
    
    # 等待自动保存
    print("等待自动保存...")
    time.sleep(0.2)
    
    # 修改值
    print("修改 backup_test = 'modified_value'")
    cfg.backup_test = "modified_value"
    
    # 检查修改后的值
    print(f"修改后 backup_test: {cfg.backup_test}")
    
    # 等待自动保存
    print("等待自动保存...")
    time.sleep(0.2)
    
    # 重新加载配置
    print("重新加载配置...")
    reloaded = cfg.reload()
    print(f"重新加载结果: {reloaded}")
    
    # 检查重新加载后的值
    try:
        backup_test_value = cfg.backup_test
        print(f"重新加载后 backup_test: {backup_test_value}")
    except AttributeError as e:
        print(f"重新加载后访问 backup_test 失败: {e}")
        
    try:
        nested_value = cfg.nested_backup.value
        print(f"重新加载后 nested_backup.value: {nested_value}")
    except AttributeError as e:
        print(f"重新加载后访问 nested_backup.value 失败: {e}")
    
    # 检查_data内容
    print(f"_data内容: {cfg._data}")
    
    # 检查配置文件内容
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"配置文件内容:\n{content}")
    else:
        print("配置文件不存在") 