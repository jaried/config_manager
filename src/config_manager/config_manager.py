# src/config_manager/config_manager.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import os
import threading
import uuid
import tempfile
import shutil
from typing import Any, Dict
from .config_node import ConfigNode
from .core.manager import ConfigManagerCore
from .core.path_resolver import PathResolver

# 全局调用链显示开关 - 手工修改这个值来控制调用链显示
ENABLE_CALL_CHAIN_DISPLAY = False  # 默认关闭调用链显示


class ConfigManager(ConfigManagerCore):
    """配置管理器类，支持自动保存和类型提示"""
    _instances = {}
    _thread_lock = threading.Lock()
    _global_listeners = []

    def __new__(cls, config_path: str = None,
                watch: bool = True, auto_create: bool = False,
                autosave_delay: float = 0.1, first_start_time: datetime = None,
                test_mode: bool = False):
        # 测试模式处理
        if test_mode:
            config_path = cls._setup_test_environment(config_path, first_start_time)
            auto_create = True  # 测试模式强制启用自动创建
            watch = False  # 测试模式禁用文件监视

        # 生成缓存键 - 修复：基于实际解析的路径
        cache_key = cls._generate_cache_key(config_path, test_mode)

        if cache_key not in cls._instances:
            with cls._thread_lock:
                if cache_key not in cls._instances:
                    # 创建新实例，直接调用object.__new__避免递归
                    instance = object.__new__(cls)

                    # 手动初始化ConfigNode的_data属性
                    instance.__dict__['_data'] = {}

                    # 初始化ConfigManagerCore
                    ConfigManagerCore.__init__(instance)

                    # 执行配置管理器的初始化
                    success = instance.initialize(
                        config_path, watch, auto_create, autosave_delay, first_start_time=first_start_time
                    )
                    
                    if not success:
                        # 初始化失败，不缓存实例，返回None
                        print(f"⚠️  配置管理器初始化失败，返回None")
                        return None

                    cls._instances[cache_key] = instance
        return cls._instances[cache_key]

    def __init__(self, config_path: str = None,
                 watch: bool = False, auto_create: bool = False,
                 autosave_delay: float = 0.1, first_start_time: datetime = None,
                 test_mode: bool = False):
        """初始化配置管理器，单例模式下可能被多次调用"""
        # 单例模式下，__init__可能被多次调用，但只有第一次有效
        pass

    @classmethod
    def _generate_cache_key(cls, config_path: str, test_mode: bool = False) -> str:
        """生成缓存键 - 修复版本：基于当前工作目录和配置路径"""
        try:
            # 修复：不在缓存键生成时调用路径解析，避免循环依赖
            cwd = os.getcwd()

            if config_path is not None:
                # 显式路径：使用绝对路径
                abs_path = os.path.abspath(config_path)
                cache_key = f"explicit:{abs_path}"
            else:
                # 自动路径：基于当前工作目录
                cache_key = f"auto:{cwd}"

            # 测试模式添加特殊标识，确保测试实例独立
            if test_mode:
                cache_key = f"test:{cache_key}"

            return cache_key
        except Exception as e:
            # 如果路径解析失败，生成一个基于输入参数的缓存键
            if config_path is not None:
                base_key = f"explicit:{config_path}"
            else:
                base_key = f"default:{os.getcwd()}"

            if test_mode:
                base_key = f"test:{base_key}"

            return base_key

    @staticmethod
    def generate_config_id() -> str:
        """生成唯一配置ID"""
        config_id = str(uuid.uuid4())
        return config_id

    @classmethod
    def _setup_test_environment(cls, original_config_path: str = None, first_start_time: datetime = None) -> str:
        """设置测试环境"""
        # 1. 检测生产配置，获取project_name
        prod_config_path = None
        
        if original_config_path:
            # 如果明确传入了配置路径，优先使用
            prod_config_path = original_config_path
            print(f"✓ 使用传入的配置路径: {prod_config_path}")
        else:
            # 尝试检测生产配置
            prod_config_path = cls._detect_production_config()
            if prod_config_path:
                print(f"✓ 检测到生产配置: {prod_config_path}")
            else:
                print("⚠️  未检测到生产配置，将尝试其他方法")

        # 2. 如果没有找到生产配置，尝试更广泛的搜索
        if not prod_config_path or not os.path.exists(prod_config_path):
            print("⚠️  生产配置不存在，尝试更广泛的搜索...")
            
            # 获取当前工作目录
            cwd = os.getcwd()
            print(f"当前工作目录: {cwd}")
            
            # 策略1: 从当前工作目录的不同位置查找配置文件
            possible_config_paths = [
                os.path.join(cwd, 'src', 'config', 'config.yaml'),
                os.path.join(cwd, 'config', 'config.yaml'),
                os.path.join(cwd, 'config.yaml'),
            ]
            
            for path in possible_config_paths:
                if os.path.exists(path):
                    # 修复: 如果找到的配置文件在tests目录下，跳过
                    if 'tests' + os.sep in path or '/tests/' in path:
                        print(f"⚠️  跳过tests目录下的配置文件: {path}")
                        continue
                    prod_config_path = path
                    print(f"✓ 找到配置文件: {prod_config_path}")
                    break
            
            # 策略2: 如果还是没找到，尝试向上查找
            if not prod_config_path or not os.path.exists(prod_config_path):
                print("在当前目录未找到，向上查找...")
                current_dir = cwd
                for level in range(5):  # 最多向上查找5级目录
                    parent_dir = os.path.dirname(current_dir)
                    if parent_dir == current_dir:  # 已到根目录
                        break
                    
                    print(f"查找第{level+1}级上级目录: {parent_dir}")
                    test_paths = [
                        os.path.join(parent_dir, 'src', 'config', 'config.yaml'),
                        os.path.join(parent_dir, 'config', 'config.yaml'),
                        os.path.join(parent_dir, 'config.yaml'),
                    ]
                    
                    for path in test_paths:
                        if os.path.exists(path):
                            # 修复: 如果找到的配置文件在tests目录下，跳过
                            if 'tests' + os.sep in path or '/tests/' in path:
                                print(f"⚠️  跳过tests目录下的配置文件: {path}")
                                continue
                            prod_config_path = path
                            print(f"✓ 在上级目录找到配置文件: {prod_config_path}")
                            break
                    
                    if prod_config_path and os.path.exists(prod_config_path):
                        break
                    
                    current_dir = parent_dir
            
            # 策略3: 如果还是没找到，尝试从调用栈中查找
            if not prod_config_path or not os.path.exists(prod_config_path):
                print("在上级目录未找到，从调用栈查找...")
                try:
                    import inspect
                    for frame_info in inspect.stack():
                        filename = frame_info.filename
                        
                        # 跳过config_manager自身的文件
                        if 'config_manager' in filename:
                            continue
                        
                        # 跳过系统文件
                        if ('site-packages' in filename or 
                            'lib/python' in filename.lower() or
                            '<' in filename):
                            continue
                        
                        # 从调用文件的目录开始查找
                        file_dir = os.path.dirname(filename)
                        print(f"从调用文件目录查找: {file_dir}")
                        
                        # 在调用文件的目录及其上级目录中查找
                        search_dir = file_dir
                        for level in range(5):  # 最多向上查找5级
                            test_paths = [
                                os.path.join(search_dir, 'src', 'config', 'config.yaml'),
                                os.path.join(search_dir, 'config', 'config.yaml'),
                                os.path.join(search_dir, 'config.yaml'),
                            ]
                            
                            for path in test_paths:
                                if os.path.exists(path):
                                    # 修复: 如果找到的配置文件在tests目录下，跳过
                                    if 'tests' + os.sep in path or '/tests/' in path:
                                        print(f"⚠️  跳过tests目录下的配置文件: {path}")
                                        continue
                                    prod_config_path = path
                                    print(f"✓ 从调用栈找到配置文件: {prod_config_path}")
                                    break
                            
                            if prod_config_path and os.path.exists(prod_config_path):
                                break
                            
                            parent = os.path.dirname(search_dir)
                            if parent == search_dir:  # 已到根目录
                                break
                            search_dir = parent
                        
                        if prod_config_path and os.path.exists(prod_config_path):
                            break
                            
                except Exception as e:
                    print(f"从调用栈查找配置文件失败: {e}")
            
            # 策略4: 最后尝试一些常见的项目结构
            if not prod_config_path or not os.path.exists(prod_config_path):
                print("尝试常见项目结构...")
                # 尝试一些常见的项目名称和结构
                common_patterns = [
                    # 当前目录的兄弟目录
                    os.path.join(os.path.dirname(cwd), '*/src/config/config.yaml'),
                    # 当前目录的父目录
                    os.path.join(os.path.dirname(os.path.dirname(cwd)), 'src/config/config.yaml'),
                ]
                
                import glob
                for pattern in common_patterns:
                    matches = glob.glob(pattern)
                    if matches:
                        # 修复: 过滤掉tests目录下的配置文件
                        filtered_matches = [
                            match for match in matches
                            if not ('tests' + os.sep in match or '/tests/' in match)
                        ]
                        if filtered_matches:
                            # 选择第一个匹配的文件
                            prod_config_path = filtered_matches[0]
                            print(f"✓ 通过模式匹配找到配置文件: {prod_config_path}")
                        else:
                            print("⚠️  模式匹配找到的都是tests目录下的配置文件，已跳过")
                        break

        # 3. 从生产配置中读取project_name和first_start_time
        project_name = "project_name"  # 默认值
        config_first_start_time = None

        # 优先从主配置文件读取project_name（不是测试配置文件）
        main_config_path = None
        if prod_config_path and os.path.exists(prod_config_path):
            # 如果传入的是测试配置文件路径，尝试找到对应的主配置文件
            if 'tests' in prod_config_path:
                # 从测试路径推导主配置路径
                # 例如: /project/tests/src/config/config.yaml -> /project/src/config/config.yaml
                main_config_path = prod_config_path.replace('/tests/', '/').replace('\\tests\\', '\\')
                if not os.path.exists(main_config_path):
                    # 如果推导的路径不存在，尝试其他方式
                    project_root = os.path.dirname(prod_config_path)
                    # 向上查找直到找到包含src目录的根目录
                    for _ in range(10):  # 最多向上查找10级
                        parent = os.path.dirname(project_root)
                        if parent == project_root:  # 已到根目录
                            break
                        if os.path.exists(os.path.join(parent, 'src', 'config', 'config.yaml')):
                            main_config_path = os.path.join(parent, 'src', 'config', 'config.yaml')
                            break
                        project_root = parent
            else:
                main_config_path = prod_config_path

            # 从主配置文件读取project_name
            if main_config_path and os.path.exists(main_config_path):
                try:
                    from ruamel.yaml import YAML
                    yaml = YAML()
                    yaml.preserve_quotes = True
                    yaml.default_flow_style = False
                    
                    # 先尝试读取文件内容并处理Windows路径转义问题
                    with open(main_config_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 处理Windows路径中的反斜杠转义问题
                    # 将 "d:\logs" 这样的路径转换为 "d:/logs" 或使用原始字符串
                    import re
                    # 匹配双引号中的Windows路径并修复转义问题
                    def fix_windows_path(match):
                        path = match.group(1)
                        # 将反斜杠替换为正斜杠，避免转义问题
                        fixed_path = path.replace('\\', '/')
                        return f'"{fixed_path}"'
                    
                    # 修复常见的Windows路径转义问题
                    content = re.sub(r'"([a-zA-Z]:\\[^"]*)"', fix_windows_path, content)
                    
                    # 解析修复后的YAML内容
                    config_data = yaml.load(content) or {}

                    # 获取project_name
                    if '__data__' in config_data:
                        project_name = config_data['__data__'].get('project_name', 'project_name')
                        config_first_start_time = config_data['__data__'].get('first_start_time')
                    else:
                        project_name = config_data.get('project_name', 'project_name')
                        config_first_start_time = config_data.get('first_start_time')

                    print(f"✓ 从主配置文件读取project_name: {project_name} (文件: {main_config_path})")

                except Exception as e:
                    print(f"⚠️  读取主配置失败，使用默认project_name: {e}")
                    # 如果YAML解析失败，尝试简单的文本解析来提取project_name
                    try:
                        with open(main_config_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 使用正则表达式提取project_name
                        import re
                        # 匹配 project_name: "value" 或 project_name: value
                        match = re.search(r'project_name:\s*["\']?([^"\'\n\r]+)["\']?', content)
                        if match:
                            project_name = match.group(1).strip()
                            print(f"✓ 通过文本解析提取project_name: {project_name}")
                        else:
                            print("⚠️  无法从配置文件中提取project_name，使用默认值")
                    except Exception as e2:
                        print(f"⚠️  文本解析也失败: {e2}")
            else:
                print(f"⚠️  主配置文件不存在: {main_config_path}")
        else:
            print("⚠️  没有找到任何配置文件，将创建空配置")

        # 4. 确定使用的first_start_time（优先级：传入参数 > 配置文件 > 当前时间）
        final_first_start_time = first_start_time or config_first_start_time
        if isinstance(final_first_start_time, str):
            try:
                from datetime import datetime
                final_first_start_time = datetime.fromisoformat(final_first_start_time.replace('Z', '+00:00'))
            except:
                final_first_start_time = None

        # 5. 生成测试环境路径（基于first_start_time和project_name）
        test_base_dir, test_config_path = cls._generate_test_environment_path(final_first_start_time, project_name)

        # 6. 复制配置到测试环境，并强制更新project_name
        if prod_config_path and os.path.exists(prod_config_path):
            cls._copy_production_config_to_test(prod_config_path, test_config_path, final_first_start_time, project_name)
            print(f"✓ 已从生产环境复制配置: {prod_config_path} -> {test_config_path}")
        else:
            # 创建空的测试配置
            cls._create_empty_test_config(test_config_path, final_first_start_time, project_name)
            print(f"✓ 已创建空的测试配置: {test_config_path}")

        # 7. 设置测试环境变量（可选）
        os.environ['CONFIG_MANAGER_TEST_MODE'] = 'true'
        os.environ['CONFIG_MANAGER_TEST_BASE_DIR'] = test_base_dir

        return test_config_path

    @classmethod
    def _generate_test_environment_path(cls, first_start_time: datetime = None, project_name: str = None) -> tuple[
        str, str]:
        """生成测试环境路径（基于first_start_time和project_name）"""
        temp_base = tempfile.gettempdir()

        # 使用first_start_time或当前时间生成路径
        if first_start_time:
            base_time = first_start_time
        else:
            base_time = datetime.now()

        # 使用project_name或默认值
        if not project_name:
            project_name = "project_name"

        date_str = base_time.strftime('%Y%m%d')
        time_str = base_time.strftime('%H%M%S')

        test_base_dir = os.path.join(temp_base, 'tests', date_str, time_str, project_name)
        test_config_path = os.path.join(test_base_dir, 'src', 'config', 'config.yaml')

        return test_base_dir, test_config_path

    @classmethod
    def _detect_production_config(cls) -> str:
        """检测生产环境配置文件路径"""
        # 1. 查找项目根目录
        project_root = PathResolver._find_project_root()
        if not project_root:
            return None

        # 2. 检查标准配置路径
        standard_config_path = os.path.join(project_root, 'src', 'config', 'config.yaml')
        if os.path.exists(standard_config_path):
            # 修复: 确保不是tests目录下的配置文件
            if not ('tests' + os.sep in standard_config_path or '/tests/' in standard_config_path):
                return standard_config_path

        # 3. 检查其他可能的配置路径
        possible_paths = [
            os.path.join(project_root, 'config', 'config.yaml'),
            os.path.join(project_root, 'config.yaml'),
            os.path.join(project_root, 'src', 'config.yaml')
        ]

        for path in possible_paths:
            if os.path.exists(path):
                # 修复: 确保不是tests目录下的配置文件
                if not ('tests' + os.sep in path or '/tests/' in path):
                    return path

        return None

    @classmethod
    def _copy_production_config_to_test(cls, prod_config_path: str, test_config_path: str,
                                        first_start_time: datetime = None, project_name: str = None):
        """将生产配置复制到测试环境"""
        # 确保测试目录存在
        os.makedirs(os.path.dirname(test_config_path), exist_ok=True)

        if os.path.exists(prod_config_path):
            # 复制配置文件
            shutil.copy2(prod_config_path, test_config_path)

            # 修改测试配置中的路径信息
            cls._update_test_config_paths(test_config_path, first_start_time, project_name)
        else:
            # 如果生产配置不存在，创建空的测试配置
            cls._create_empty_test_config(test_config_path, first_start_time, project_name)

    @classmethod
    def _update_test_config_paths(cls, test_config_path: str, first_start_time: datetime = None, project_name: str = None):
        """更新测试配置中的路径信息"""
        try:
            from ruamel.yaml import YAML
            yaml = YAML()
            yaml.preserve_quotes = True
            yaml.default_flow_style = False

            # 读取配置文件并处理Windows路径转义问题
            with open(test_config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 处理Windows路径中的反斜杠转义问题
            import re
            def fix_windows_path(match):
                path = match.group(1)
                # 将反斜杠替换为正斜杠，避免转义问题
                fixed_path = path.replace('\\', '/')
                return f'"{fixed_path}"'
            
            # 修复常见的Windows路径转义问题
            content = re.sub(r'"([a-zA-Z]:\\[^"]*)"', fix_windows_path, content)
            
            # 解析修复后的YAML内容
            config_data = yaml.load(content) or {}

            # 获取原配置中的first_start_time
            original_first_start_time = None
            if '__data__' in config_data:
                original_first_start_time = config_data['__data__'].get('first_start_time')
            else:
                original_first_start_time = config_data.get('first_start_time')

            # 确定最终使用的时间（优先级：传入参数 > 原配置 > 当前时间）
            time_to_use = None
            if first_start_time:
                # 优先使用传入的参数
                time_to_use = first_start_time
                print(f"✓ 使用传入的first_start_time: {first_start_time}")
            elif original_first_start_time:
                # 保留原配置中的时间，不需要更新
                print(f"✓ 保留原配置中的first_start_time: {original_first_start_time}")
                time_to_use = None  # 标记不需要更新
            else:
                # 只有在都没有的情况下才使用当前时间
                time_to_use = datetime.now()
                print(f"✓ 使用当前时间作为first_start_time: {time_to_use}")

            # 生成测试环境的基础路径
            test_base_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(test_config_path)))  # 去掉 /src/config/config.yaml
            temp_base = tempfile.gettempdir()

            # 无论如何都要执行路径替换
            print(f"✓ 开始执行路径替换，test_base_dir: {test_base_dir}, temp_base: {temp_base}")

            # 确定使用的project_name（优先级：传入参数 > 原配置 > 从路径提取 > 默认值）
            final_project_name = project_name  # 优先使用传入的project_name
            if not final_project_name:
                # 如果没有传入project_name，尝试从原配置读取
                if '__data__' in config_data:
                    final_project_name = config_data['__data__'].get('project_name')
                else:
                    final_project_name = config_data.get('project_name')
                
                if not final_project_name:
                    # 最后从路径中提取
                    final_project_name = "project_name"  # 默认值
                    try:
                        # 路径格式: /temp/tests/YYYYMMDD/HHMMSS/project_name/src/config/config.yaml
                        path_parts = test_config_path.replace('\\', '/').split('/')
                        if len(path_parts) >= 3:
                            # 找到project_name部分（在src之前的最后一个部分）
                            for i, part in enumerate(path_parts):
                                if part == 'src' and i > 0:
                                    final_project_name = path_parts[i - 1]
                                    break
                    except:
                        pass  # 使用默认值

            # 如果传入了project_name，强制更新配置中的project_name
            if project_name:
                print(f"✓ 强制更新配置中的project_name: {project_name}")

            # 更新路径信息和时间信息
            if '__data__' in config_data:
                # 标准格式
                config_data['__data__']['config_file_path'] = test_config_path
                if time_to_use is not None:  # 只在需要时更新first_start_time
                    config_data['__data__']['first_start_time'] = time_to_use.isoformat()

                # 强制更新project_name（如果传入了参数）
                if project_name:
                    config_data['__data__']['project_name'] = project_name
                elif 'project_name' not in config_data['__data__']:
                    config_data['__data__']['project_name'] = final_project_name

                # 动态替换所有路径字段
                cls._replace_all_paths_in_config(config_data['__data__'], test_base_dir, temp_base)
            else:
                # 原始格式
                config_data['config_file_path'] = test_config_path
                if time_to_use is not None:  # 只在需要时更新first_start_time
                    config_data['first_start_time'] = time_to_use.isoformat()

                # 强制更新project_name（如果传入了参数）
                if project_name:
                    config_data['project_name'] = project_name
                elif 'project_name' not in config_data:
                    config_data['project_name'] = final_project_name

                # 动态替换所有路径字段
                cls._replace_all_paths_in_config(config_data, test_base_dir, temp_base)

            # 保存更新后的配置，确保路径使用正斜杠
            with open(test_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)

        except Exception as e:
            print(f"⚠️  更新测试配置路径失败: {e}")
            # 如果YAML处理失败，尝试创建一个基本的配置文件
            try:
                print("尝试创建基本配置文件...")
                basic_config = {
                    '__data__': {
                        'config_file_path': test_config_path,
                        'first_start_time': (first_start_time or datetime.now()).isoformat(),
                        'project_name': project_name or 'project_name',
                        'experiment_name': 'default',
                        'base_dir': 'd:/logs',
                        'app_name': f'{project_name or "project_name"}系统',
                        'version': '1.0.0'
                    },
                    '__type_hints__': {}
                }
                
                from ruamel.yaml import YAML
                yaml = YAML()
                with open(test_config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(basic_config, f)
                print("✓ 已创建基本配置文件")
                
            except Exception as e2:
                print(f"⚠️  创建基本配置文件也失败: {e2}")

    @classmethod
    def _replace_all_paths_in_config(cls, config_data: dict, test_base_dir: str, temp_base: str):
        """递归替换配置中的所有路径字段"""
        # 常见的路径字段名称模式
        path_field_patterns = [
            'dir', 'path', 'directory', 'folder', 'location', 'root', 'base',
            'work_dir', 'base_dir', 'log_dir', 'data_dir', 'output_dir', 'temp_dir',
            'cache_dir', 'backup_dir', 'download_dir', 'upload_dir', 'storage_dir'
        ]

        # 需要特殊处理的路径字段映射
        special_path_mappings = {
            'base_dir': os.path.normpath(test_base_dir),
            'work_dir': os.path.normpath(test_base_dir),
            'log_dir': os.path.normpath(os.path.join(test_base_dir, 'logs')),
            'data_dir': os.path.normpath(os.path.join(test_base_dir, 'data')),
            'output_dir': os.path.normpath(os.path.join(test_base_dir, 'output')),
            'temp_dir': os.path.normpath(os.path.join(test_base_dir, 'temp')),
            'cache_dir': os.path.normpath(os.path.join(test_base_dir, 'cache')),
            'backup_dir': os.path.normpath(os.path.join(test_base_dir, 'backup')),
            'download_dir': os.path.normpath(os.path.join(test_base_dir, 'downloads')),
            'upload_dir': os.path.normpath(os.path.join(test_base_dir, 'uploads')),
            'storage_dir': os.path.normpath(os.path.join(test_base_dir, 'storage'))
        }

        # 首先确保关键路径字段存在，并强制替换特殊路径字段
        for key, default_path in special_path_mappings.items():
            if key not in config_data:
                config_data[key] = default_path
            else:
                # 对于已存在的特殊路径字段，如果不是测试路径，则强制替换
                current_value = config_data[key]
                if isinstance(current_value, str) and temp_base not in current_value:
                    config_data[key] = default_path

        def replace_paths_recursive(obj, parent_key=''):
            """递归替换对象中的路径"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    full_key = f"{parent_key}.{key}" if parent_key else key

                    if isinstance(value, str):
                        # 检查是否是路径字段，但跳过已经是测试路径的字段
                        if cls._is_path_field(key, value) and temp_base not in value:
                            # 优先使用特殊映射
                            if key in special_path_mappings:
                                new_path = special_path_mappings[key]
                                if new_path != value:  # 只在值不同时才替换
                                    obj[key] = new_path
                            else:
                                # 通用路径替换：将绝对路径替换为测试环境路径
                                new_path = cls._convert_to_test_path(value, test_base_dir, temp_base)
                                if new_path != value:
                                    obj[key] = new_path
                    elif isinstance(value, (dict, list)):
                        # 递归处理嵌套结构
                        replace_paths_recursive(value, full_key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, (dict, list)):
                        replace_paths_recursive(item, f"{parent_key}[{i}]")
                    elif isinstance(item, str) and cls._is_path_like(item) and temp_base not in item:
                        # 列表中的路径字符串，跳过已经是测试路径的
                        new_path = cls._convert_to_test_path(item, test_base_dir, temp_base)
                        if new_path != item:
                            obj[i] = new_path

        replace_paths_recursive(config_data)

    @classmethod
    def _is_path_field(cls, key: str, value: str) -> bool:
        """判断字段是否是路径字段
        
        只有以特定路径相关名词结尾的字段才被识别为路径字段：
        - _dir, dir: 目录路径
        - _path, path: 文件或目录路径  
        - _file, file: 文件路径
        - _directory, directory: 目录路径
        - _folder, folder: 文件夹路径
        - _location, location: 位置路径
        """
        if not isinstance(value, str) or not value.strip():
            return False

        # 首先检查是否是需要保护的字段类型
        if cls._is_protected_field(key, value):
            return False

        # 检查字段名是否以路径相关名词结尾
        key_lower = key.lower()
        path_suffixes = [
            '_dir', 'dir',
            '_path', 'path', 
            '_file', 'file',
            '_directory', 'directory',
            '_folder', 'folder',
            '_location', 'location'
        ]

        for suffix in path_suffixes:
            if key_lower.endswith(suffix):
                return True

        return False

    @classmethod
    def _is_protected_field(cls, key: str, value: str) -> bool:
        """判断字段是否是需要保护的字段（不应该被路径替换）
        
        由于路径字段识别已改为只识别特定后缀，保护模式主要用于：
        1. 防止网络URL被误识别为路径
        2. 防止正则表达式被误识别为路径
        3. 保护特殊配置字段
        """
        if not isinstance(value, str) or not value.strip():
            return False

        key_lower = key.lower()
        value_lower = value.lower()

        # 1. HTTP/HTTPS URL保护（最重要的保护）
        if value.startswith(('http://', 'https://', 'ftp://', 'ws://', 'wss://')):
            return True

        # 2. 网络相关字段保护
        network_keywords = ['proxy', 'url', 'endpoint', 'api', 'host', 'server']
        for keyword in network_keywords:
            if keyword in key_lower:
                return True

        # 3. HTTP Headers保护
        header_keywords = ['header', 'accept', 'content-type', 'user-agent', 'user_agent', 'cookie', 'authorization']
        for keyword in header_keywords:
            if keyword in key_lower:
                return True
        
        # 常见的HTTP Header字段名
        if key_lower in ['accept', 'content-type', 'user-agent', 'authorization', 'cookie']:
            return True

        # 4. 正则表达式保护
        if cls._is_regex_pattern(value):
            return True

        # 5. MIME类型保护
        if '/' in value and any(mime in value_lower for mime in [
            'text/', 'application/', 'image/', 'video/', 'audio/', 'multipart/', 'message/'
        ]):
            return True

        # 6. URL模式保护
        if cls._is_url_pattern(value):
            return True

        return False

    @classmethod
    def _is_regex_pattern(cls, value: str) -> bool:
        """判断是否是正则表达式模式"""
        # 检查正则表达式特征
        regex_indicators = [
            value.startswith('^') or value.endswith('$'),  # 锚点
            '\\' in value and any(char in value for char in ['d', 'w', 's', 'n', 't']),  # 转义字符
            '[' in value and ']' in value,  # 字符类
            '(' in value and ')' in value,  # 分组
            '+' in value or '*' in value or '?' in value,  # 量词
            '|' in value,  # 或操作符
            '{' in value and '}' in value,  # 重复次数
        ]
        return any(regex_indicators)

    @classmethod
    def _is_url_pattern(cls, value: str) -> bool:
        """判断是否是URL模式"""
        # 检查URL模式特征
        url_patterns = [
            # API路径模式：以/开头且包含api相关关键词
            value.startswith('/') and not value.startswith('//') and any(api_keyword in value.lower() for api_keyword in ['/api/', '/v1/', '/v2/', '/rest/', '/graphql']),
            '*.' in value,  # 通配符域名
            # URL路径格式：包含域名的URL路径（必须包含顶级域名）
            value.count('/') >= 2 and '.' in value and any(tld in value.lower() for tld in ['.com', '.org', '.net', '.edu', '.gov', '.io', '.co']),
            # 单独的顶级域名检查（用于域名字符串）
            any(tld in value.lower() for tld in ['.com', '.org', '.net', '.edu', '.gov', '.io', '.co']) and not value.startswith('/'),
        ]
        return any(url_patterns)

    @classmethod
    def _is_path_like(cls, value: str) -> bool:
        """判断字符串是否看起来像文件路径"""
        if not value or len(value) < 2:
            return False

        # 排除网络URL
        if value.startswith(('http://', 'https://', 'ftp://', 'ws://', 'wss://', 'file://')):
            return False

        # 排除MIME类型
        if '/' in value and any(mime in value.lower() for mime in [
            'text/', 'application/', 'image/', 'video/', 'audio/', 'multipart/', 'message/'
        ]):
            return False

        # 首先检查Windows盘符格式（在正则表达式检查之前）
        if len(value) >= 2 and value[1] == ':' and value[0].isalpha():
            return True

        # 排除明显的正则表达式（但已经排除了Windows路径）
        if cls._is_regex_pattern(value):
            return False

        # 检查是否以常见文件路径前缀开始
        file_path_prefixes = ['~/', './', '../', '/tmp/', '/var/', '/usr/', '/opt/', '/home/', '/etc/']
        for prefix in file_path_prefixes:
            if value.startswith(prefix):
                return True

        # 检查是否包含路径分隔符且看起来像文件路径
        if ('/' in value or '\\' in value):
            # 进一步验证是否真的是文件路径
            # 排除看起来像URL路径的情况
            if value.startswith('/') and not value.startswith('//'):
                # 可能是绝对路径，但要排除API路径
                if any(api_indicator in value.lower() for api_indicator in ['/api/', '/v1/', '/v2/', '/rest/']):
                    return False
                return True

            # Windows路径或相对路径
            if '\\' in value or value.startswith('./') or value.startswith('../'):
                return True

            # 包含文件扩展名的路径
            if '.' in value and not value.startswith('.'):
                # 检查是否有常见的文件扩展名
                common_extensions = ['.txt', '.log', '.yaml', '.yml', '.json', '.xml', '.ini', '.conf', '.cfg']
                if any(ext in value.lower() for ext in common_extensions):
                    return True

        # 检查是否包含常见的路径组件
        path_components = ['bin', 'lib', 'src', 'config', 'data', 'logs', 'temp', 'cache', 'backup', 'users', 'documents']
        if any(component in value.lower() for component in path_components):
            return True

        return False

    @classmethod
    def _convert_to_test_path(cls, original_path: str, test_base_dir: str, temp_base: str) -> str:
        """将原始路径转换为测试环境路径"""
        if not original_path or not cls._is_path_like(original_path):
            return original_path

        # 如果已经是测试路径，不需要转换
        if temp_base in original_path:
            return original_path

        # 处理相对路径
        if original_path.startswith('./') or original_path.startswith('../'):
            # 相对路径转换为测试环境下的相对路径
            result = os.path.join(test_base_dir, original_path.lstrip('./'))
            return os.path.normpath(result)

        # 处理绝对路径
        if os.path.isabs(original_path):
            # 提取路径的最后几个部分，在测试环境中重建
            # 使用 os.path.normpath 来正确处理路径分隔符
            normalized_path = os.path.normpath(original_path)
            path_parts = normalized_path.split(os.sep)
            # 取最后1-2个有意义的部分
            meaningful_parts = [part for part in path_parts[-2:] if part and part != '..']
            if meaningful_parts:
                result = os.path.join(test_base_dir, *meaningful_parts)
                return os.path.normpath(result)
            else:
                return os.path.normpath(test_base_dir)

        # 其他情况，直接在测试环境下创建
        result = os.path.join(test_base_dir, original_path)
        return os.path.normpath(result)

    @classmethod
    def _create_empty_test_config(cls, test_config_path: str, first_start_time: datetime = None, project_name: str = None):
        """创建空的测试配置"""
        # 确保测试目录存在
        os.makedirs(os.path.dirname(test_config_path), exist_ok=True)

        # 确定使用的时间
        if first_start_time:
            time_to_use = first_start_time
        else:
            time_to_use = datetime.now()

        # 确定使用的project_name
        final_project_name = project_name if project_name else "project_name"

        # 创建包含必要字段的空配置
        empty_config = {
            '__data__': {
                'config_file_path': test_config_path,
                'first_start_time': time_to_use.isoformat(),
                'project_name': final_project_name,
                'experiment_name': 'default',  # 添加默认的experiment_name
                'base_dir': 'd:/logs',  # 添加默认的base_dir
                'app_name': f'{final_project_name}系统',  # 添加默认的app_name
                'version': '1.0.0',  # 添加默认版本
                # 添加一些基本的路径配置，避免路径配置更新时出错
                'paths': {
                    'work_dir': f'd:/logs/{final_project_name}/default',
                    'log_dir': f'd:/logs/{final_project_name}/default/logs',
                    'checkpoint_dir': f'd:/logs/{final_project_name}/default/checkpoint',
                    'best_checkpoint_dir': f'd:/logs/{final_project_name}/default/checkpoint/best',
                    'debug_dir': f'd:/logs/{final_project_name}/default/debug',
                    'data_dir': f'd:/logs/{final_project_name}/default/data',
                    'output_dir': f'd:/logs/{final_project_name}/default/output',
                    'temp_dir': f'd:/logs/{final_project_name}/default/temp',
                    'cache_dir': f'd:/logs/{final_project_name}/default/cache',
                    'backup_dir': f'd:/logs/{final_project_name}/default/backup',
                    'download_dir': f'd:/logs/{final_project_name}/default/downloads',
                    'upload_dir': f'd:/logs/{final_project_name}/default/uploads',
                    'storage_dir': f'd:/logs/{final_project_name}/default/storage'
                }
            },
            '__type_hints__': {
                'project_name': 'str',
                'experiment_name': 'str',
                'base_dir': 'str',
                'app_name': 'str',
                'version': 'str',
                'first_start_time': 'str'
            }
        }

        try:
            from ruamel.yaml import YAML
            yaml = YAML()
            yaml.preserve_quotes = True
            yaml.default_flow_style = False

            with open(test_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(empty_config, f)

        except Exception as e:
            print(f"⚠️  创建空测试配置失败: {e}")
            # 回退到简单的文件创建
            time_str = time_to_use.isoformat()
            with open(test_config_path, 'w', encoding='utf-8') as f:
                f.write(f"""__data__:
  config_file_path: {test_config_path}
  first_start_time: {time_str}
  project_name: {final_project_name}
  experiment_name: default
  base_dir: d:/logs
  app_name: {final_project_name}系统
  version: 1.0.0
  paths:
    work_dir: d:/logs/{final_project_name}/default
    log_dir: d:/logs/{final_project_name}/default/logs
    checkpoint_dir: d:/logs/{final_project_name}/default/checkpoint
    best_checkpoint_dir: d:/logs/{final_project_name}/default/checkpoint/best
    debug_dir: d:/logs/{final_project_name}/default/debug
    data_dir: d:/logs/{final_project_name}/default/data
    output_dir: d:/logs/{final_project_name}/default/output
    temp_dir: d:/logs/{final_project_name}/default/temp
    cache_dir: d:/logs/{final_project_name}/default/cache
    backup_dir: d:/logs/{final_project_name}/default/backup
    download_dir: d:/logs/{final_project_name}/default/downloads
    upload_dir: d:/logs/{final_project_name}/default/uploads
    storage_dir: d:/logs/{final_project_name}/default/storage
__type_hints__:
  project_name: str
  experiment_name: str
  base_dir: str
  app_name: str
  version: str
  first_start_time: str
""")

def get_config_manager(
        config_path: str = None,
        watch: bool = False,
        auto_create: bool = False,
        autosave_delay: float = None,
        first_start_time: datetime = None,
        test_mode: bool = False
) -> ConfigManager | None:
    """
    获取配置管理器单例

    Args:
        config_path: 配置文件路径
        watch: 是否监视文件变化并自动重载
        auto_create: 配置文件不存在时是否自动创建
        autosave_delay: 自动保存延迟时间（秒）
        first_start_time: 首次启动时间
        test_mode: 测试模式开关，为True时创建完全隔离的测试环境

    Returns:
        ConfigManager 实例，如果初始化失败则返回None
    """
    # 智能检测测试环境 - 如果配置路径包含临时目录，自动启用auto_create
    if config_path and not auto_create:
        import tempfile
        temp_dir = tempfile.gettempdir()
        # Windows和Unix的临时目录检测
        if (temp_dir.lower() in config_path.lower() or 
            '/tmp/' in config_path or 
            '\\temp\\' in config_path.lower() or
            'tmpdir' in config_path.lower()):
            auto_create = True
            print(f"✓ 检测到测试环境，自动启用auto_create: {config_path}")
    
    manager = ConfigManager(config_path, watch, auto_create, autosave_delay, first_start_time=first_start_time,
                            test_mode=test_mode)
    return manager


def _clear_instances_for_testing():
    """清理所有实例，仅用于测试"""
    with ConfigManager._thread_lock:
        for instance in ConfigManager._instances.values():
            if hasattr(instance, '_cleanup'):
                try:
                    instance._cleanup()
                except:
                    pass  # 忽略清理过程中的错误
        ConfigManager._instances.clear()

    # 强制垃圾回收
    import gc
    gc.collect()
    return


if __name__ == '__main__':
    get_config_manager(auto_create=True, first_start_time=start_time)
