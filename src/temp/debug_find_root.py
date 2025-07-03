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

# 手动模拟 _find_project_root_from_path 的逻辑
def debug_find_project_root_from_path(start_path: str):
    """调试版本的 _find_project_root_from_path"""
    print(f"\n开始从路径查找项目根目录: {start_path}")
    
    if not start_path or not os.path.exists(start_path):
        print("  路径不存在，返回None")
        return None

    current_path = os.path.abspath(start_path)
    visited_paths = set()
    
    print(f"  绝对路径: {current_path}")

    while current_path not in visited_paths:
        visited_paths.add(current_path)
        print(f"  检查路径: {current_path}")

        # 特殊处理：如果当前路径本身就是src目录，向上查找
        if os.path.basename(current_path) == 'src':
            print(f"    当前路径是src目录")
            parent_path = os.path.dirname(current_path)
            if parent_path != current_path and PathResolver._is_valid_project_root(parent_path):
                print(f"    父目录是有效项目根目录: {parent_path}")
                return parent_path

        # 检查当前目录是否包含src子目录
        src_path = os.path.join(current_path, 'src')
        print(f"    检查src路径: {src_path}")
        if os.path.exists(src_path) and os.path.isdir(src_path):
            print(f"    找到src目录")
            # 找到src目录，检查是否是有效的项目根目录
            if PathResolver._is_valid_project_root(current_path):
                print(f"    是有效的项目根目录: {current_path}")
                return current_path
            # 即使没有项目指示文件，如果src目录包含Python代码，也认为是项目根目录
            elif PathResolver._src_has_python_code(src_path):
                print(f"    src目录包含Python代码，认为是项目根目录: {current_path}")
                return current_path
            else:
                print(f"    不是有效的项目根目录")

        # 向上一级目录
        parent_path = os.path.dirname(current_path)
        print(f"    向上查找到: {parent_path}")
        if parent_path == current_path:  # 已到根目录
            print(f"    已到根目录，停止查找")
            break
        current_path = parent_path

    print("  未找到项目根目录，返回None")
    return None

# 测试手动模拟的方法
result = debug_find_project_root_from_path(scripts_dir)
print(f"\n手动模拟结果: {result}")

# 测试实际的方法
print(f"\n测试实际的 _find_project_root_from_path:")
actual_result = PathResolver._find_project_root_from_path(scripts_dir)
print(f"  实际结果: {actual_result}")

# 测试 _is_temp_test_directory
print(f"\n测试 _is_temp_test_directory:")
print(f"  {temp_dir} 是否为临时目录: {PathResolver._is_temp_test_directory(temp_dir)}")
print(f"  {scripts_dir} 是否为临时目录: {PathResolver._is_temp_test_directory(scripts_dir)}")

# 测试 _is_valid_project_root
print(f"\n测试 _is_valid_project_root:")
print(f"  {temp_dir} 是否有效: {PathResolver._is_valid_project_root(temp_dir)}")
print(f"  {scripts_dir} 是否有效: {PathResolver._is_valid_project_root(scripts_dir)}")

# 测试 _src_has_python_code
print(f"\n测试 _src_has_python_code:")
print(f"  {src_dir} 是否有Python代码: {PathResolver._src_has_python_code(src_dir)}")

# 清理临时目录
import shutil
try:
    shutil.rmtree(temp_dir)
except:
    pass 