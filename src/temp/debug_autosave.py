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
    
    # 创建配置管理器，启用自动保存
    cfg = get_config_manager(config_path=config_file, watch=False, auto_create=True, autosave_delay=0.1)
    print(f"配置管理器创建成功，自动保存延迟: 0.1秒")
    
    # 检查初始_data内容
    print(f"初始_data内容: {cfg._data}")
    
    # 设置值
    print("设置 backup_test = 'original_value'")
    cfg.backup_test = "original_value"
    
    # 检查设置后的_data内容
    print(f"设置后_data内容: {cfg._data}")
    
    # 手动保存
    print("手动保存...")
    save_result = cfg.save()
    print(f"手动保存结果: {save_result}")
    
    # 检查配置文件内容
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"手动保存后配置文件内容:\n{content}")
    else:
        print("配置文件不存在")
    
    # 修改值
    print("修改 backup_test = 'modified_value'")
    cfg.backup_test = "modified_value"
    
    # 检查修改后的_data内容
    print(f"修改后_data内容: {cfg._data}")
    
    # 再次手动保存
    print("再次手动保存...")
    save_result2 = cfg.save()
    print(f"再次手动保存结果: {save_result2}")
    
    # 检查配置文件内容
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"再次保存后配置文件内容:\n{content}")
    
    # 测试to_dict方法
    print(f"to_dict结果: {cfg.to_dict()}")
    
    # 重新加载配置
    print("重新加载配置...")
    reloaded = cfg.reload()
    print(f"重新加载结果: {reloaded}")
    print(f"重新加载后_data内容: {cfg._data}")
    
    # 检查重新加载后的值
    try:
        backup_test_value = cfg.backup_test
        print(f"重新加载后 backup_test: {backup_test_value}")
    except AttributeError as e:
        print(f"重新加载后访问 backup_test 失败: {e}") 