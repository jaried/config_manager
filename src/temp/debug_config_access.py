import tempfile
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.config_manager.config_manager import get_config_manager, _clear_instances_for_testing

# 清理实例
_clear_instances_for_testing()

# 创建临时配置文件
with tempfile.TemporaryDirectory() as tmpdir:
    config_file = os.path.join(tmpdir, 'config.yaml')
    
    # 创建配置管理器
    cfg = get_config_manager(config_path=config_file, watch=False)
    
    # 设置值
    print('设置 backup_test = original_value')
    cfg.backup_test = 'original_value'
    
    # 检查是否能立即访问
    try:
        value = cfg.backup_test
        print(f'立即访问成功: {value}')
    except AttributeError as e:
        print(f'立即访问失败: {e}')
    
    # 保存
    print('保存配置...')
    cfg.save()
    
    # 重新加载
    print('重新加载配置...')
    cfg.reload()
    
    # 再次尝试访问
    try:
        value = cfg.backup_test
        print(f'重新加载后访问成功: {value}')
    except AttributeError as e:
        print(f'重新加载后访问失败: {e}')
        
    # 检查_data内容
    print(f'_data内容: {cfg._data}')
    
    # 检查配置文件内容
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f'配置文件内容:\n{content}') 