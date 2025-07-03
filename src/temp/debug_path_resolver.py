import tempfile
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.config_manager.core.path_resolver import PathResolver

# 创建临时项目目录结构
temp_dir = tempfile.mkdtemp(prefix="debug_project_")
src_dir = os.path.join(temp_dir, 'src')
scripts_dir = os.path.join(temp_dir, 'scripts')

os.makedirs(src_dir, exist_ok=True)
os.makedirs(scripts_dir, exist_ok=True)

print(f"创建的临时目录结构:")
print(f"  项目根目录: {temp_dir}")
print(f"  src目录: {src_dir}")
print(f"  scripts目录: {scripts_dir}")

# 保存原始工作目录
original_cwd = os.getcwd()

try:
    # 切换到scripts目录
    os.chdir(scripts_dir)
    print(f"\n当前工作目录: {os.getcwd()}")
    
    # 测试项目根目录查找
    print(f"\n测试 _find_project_root_from_path:")
    result = PathResolver._find_project_root_from_path(scripts_dir)
    print(f"  从 {scripts_dir} 查找结果: {result}")
    
    print(f"\n测试 _find_project_root:")
    result2 = PathResolver._find_project_root()
    print(f"  _find_project_root 结果: {result2}")
    
    print(f"\n测试 _is_temp_test_directory:")
    is_temp = PathResolver._is_temp_test_directory(scripts_dir)
    print(f"  {scripts_dir} 是否为临时目录: {is_temp}")
    
    print(f"\n测试 resolve_config_path:")
    config_path = PathResolver.resolve_config_path(None)
    print(f"  解析的配置路径: {config_path}")
    
finally:
    # 恢复原始工作目录
    os.chdir(original_cwd)
    
    # 清理临时目录
    import shutil
    try:
        shutil.rmtree(temp_dir)
    except:
        pass 