# src/config_manager/config_manager.py
from __future__ import annotations
from datetime import datetime
from typing import Union, Type

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
from config_manager.logger import info
from .core.cross_platform_paths import convert_to_multi_platform_config

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
        """生成缓存键 - 改进版本：更稳定的缓存键生成"""
        try:
            if config_path is not None:
                # 显式路径：使用绝对路径，但标准化路径分隔符
                abs_path = os.path.abspath(config_path)
                # 标准化路径分隔符，确保跨平台一致性
                normalized_path = abs_path.replace('\\', '/')
                cache_key = f"explicit:{normalized_path}"
            else:
                # 自动路径：基于当前工作目录，但使用更稳定的标识
                cwd = os.getcwd()
                normalized_cwd = cwd.replace('\\', '/')
                cache_key = f"auto:{normalized_cwd}"

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

                    print(f"查找第{level + 1}级上级目录: {parent_dir}")
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
                            print(f"✓ 从常见项目结构找到配置文件: {prod_config_path}")
                        else:
                            print("⚠️  模式匹配找到的都是tests目录下的配置文件，已跳过")
                        break

        project_name = None
        if prod_config_path and os.path.exists(prod_config_path):
            try:
                with open(prod_config_path, 'r', encoding='utf-8') as f:
                    # 使用安全的YAML加载
                    from ruamel.yaml import YAML
                    yaml = YAML(typ='safe')
                    config_data = yaml.load(f)
                    if config_data and 'project_name' in config_data:
                        project_name = config_data['project_name']
                        print(f"✓ 从主配置文件读取project_name: {project_name} (文件: {prod_config_path})")
            except Exception as e:
                print(f"读取project_name失败: {e}")

        # 2. 生成测试环境路径
        test_base_dir, test_config_path = cls._generate_test_environment_path(first_start_time)

        # 3. 复制并修改配置
        if prod_config_path and os.path.exists(prod_config_path):
            cls._copy_production_config_to_test(prod_config_path, test_config_path, first_start_time, project_name)
            print(f"✓ 已从生产环境复制配置: {prod_config_path} -> {test_config_path}")
        else:
            # 创建空的测试配置
            cls._create_empty_test_config(test_config_path, first_start_time, project_name)
            print(f"✓ 已创建空的测试配置: {test_config_path}")

        # 7. 设置测试环境变量（可选）
        os.environ['CONFIG_MANAGER_TEST_MODE'] = 'true'
        os.environ['CONFIG_MANAGER_TEST_BASE_DIR'] = test_base_dir

        return test_config_path

    @classmethod
    def _generate_test_environment_path(cls, first_start_time: datetime = None) -> tuple[
        str, str]:
        """生成测试环境路径"""
        from datetime import datetime
        
        # 确定使用的时间
        if first_start_time is None:
            first_start_time = datetime.now()
        elif isinstance(first_start_time, str):
            # 如果是字符串，尝试解析为datetime对象
            try:
                # 修复字符串替换问题
                time_str = first_start_time.replace('Z', '+00:00')
                first_start_time = datetime.fromisoformat(time_str)
            except:
                first_start_time = datetime.now()
        elif not isinstance(first_start_time, datetime):
            first_start_time = datetime.now()

        # 使用更简洁的日期和时间格式
        date_str = first_start_time.strftime("%Y%m%d")
        time_str = first_start_time.strftime("%H%M%S")

        # 优先使用pytest的tmp_path，如果不可用则使用系统临时目录
        temp_dir = tempfile.gettempdir()
        
        # 检查是否在pytest环境中
        pytest_tmp_path = cls._detect_pytest_tmp_path()
        if pytest_tmp_path:
            test_base_dir = pytest_tmp_path
            print(f"✓ 检测到pytest环境，使用pytest tmp_path: {test_base_dir}")
        else:
            # 生成唯一的测试目录
            test_base_dir = os.path.join(temp_dir, 'tests', date_str, time_str)
            print(f"✓ 使用系统临时目录: {test_base_dir}")
        
        test_config_path = os.path.join(test_base_dir, 'src', 'config', 'config.yaml')
        
        print(f"✓ 开始执行路径替换，test_base_dir: {test_base_dir}, temp_base: {temp_dir}")
        return test_base_dir, test_config_path

    @classmethod
    def _detect_pytest_tmp_path(cls) -> Union[str, None]:
        """检测pytest的tmp_path"""
        try:
            # 检查是否在pytest环境中
            import pytest
            import inspect
            
            # 获取当前调用栈
            frame = inspect.currentframe()
            while frame:
                # 检查是否有pytest相关的局部变量
                if 'tmp_path' in frame.f_locals:
                    tmp_path = frame.f_locals['tmp_path']
                    if hasattr(tmp_path, '__str__'):
                        return str(tmp_path)
                elif 'tmp_path_factory' in frame.f_locals:
                    # 如果有tmp_path_factory，尝试创建临时路径
                    tmp_path_factory = frame.f_locals['tmp_path_factory']
                    if hasattr(tmp_path_factory, 'mktemp'):
                        return str(tmp_path_factory.mktemp('config_manager_test'))
                
                frame = frame.f_back
                
        except Exception:
            pass
        
        # 检查环境变量
        pytest_tmp_path = os.environ.get('PYTEST_TMP_PATH')
        if pytest_tmp_path and os.path.exists(pytest_tmp_path):
            return pytest_tmp_path
            
        return None

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
            # 检查源路径和目标路径是否相同
            if os.path.abspath(prod_config_path) == os.path.abspath(test_config_path):
                print(f"✓ 源路径和目标路径相同，跳过复制: {prod_config_path}")
                # 直接更新现有配置
                cls._update_test_config_paths(test_config_path, first_start_time, project_name)
            else:
                # 复制配置文件
                shutil.copy2(prod_config_path, test_config_path)
                print(f"✓ 已从生产环境复制配置: {prod_config_path} -> {test_config_path}")

                # 修改测试配置中的路径信息
                cls._update_test_config_paths(test_config_path, first_start_time, project_name)
        else:
            # 如果生产配置不存在，创建空的测试配置
            cls._create_empty_test_config(test_config_path, first_start_time, project_name)

    @classmethod
    def _update_test_config_paths(cls, test_config_path: str, first_start_time: datetime = None,
                                  project_name: str = None):
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
            loaded_data = yaml.load(content) or {}

            # 判断是否为标准格式（包含__data__节点）
            if '__data__' in loaded_data:
                # 标准格式：提取__data__中的内容
                config_data = loaded_data['__data__']
                type_hints = loaded_data.get('__type_hints__', {})
            else:
                # 原始格式：直接使用
                config_data = loaded_data
                type_hints = {}

            # 获取原配置中的first_start_time
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

            # 确定使用的project_name（优先级：传入参数 > 原配置 > 默认值 'project_name'）
            final_project_name = project_name or config_data.get('project_name', 'project_name')

            # 如果传入了project_name，强制更新
            if project_name:
                config_data['project_name'] = project_name
            
            # 关键简化：只强制覆盖 base_dir
            config_data['base_dir'] = test_base_dir

            # 更新时间信息
            if time_to_use is not None:
                config_data['first_start_time'] = time_to_use.isoformat()
            
            config_data['config_file_path'] = test_config_path

            # 将清理后的数据转换为标准格式
            data_to_save = {
                '__data__': config_data,
                '__type_hints__': type_hints
            }

            # 保存更新后的配置
            with open(test_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(data_to_save, f)

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
                        'base_dir': tempfile.gettempdir(),
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
    def _create_empty_test_config(cls, test_config_path: str, first_start_time: datetime = None,
                                  project_name: str = None):
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

        # 使用系统临时路径作为base_dir
        temp_base_dir = tempfile.gettempdir()
        project_base_dir = os.path.join(temp_base_dir, final_project_name, 'default')

        # 创建包含必要字段的空配置
        empty_config = {
            '__data__': {
                'config_file_path': test_config_path,
                'first_start_time': time_to_use.isoformat(),
                'project_name': final_project_name,
                'experiment_name': 'default',  # 添加默认的experiment_name
                'base_dir': temp_base_dir,  # 使用系统临时路径
                'app_name': f'{final_project_name}系统',  # 添加默认的app_name
                'version': '1.0.0',  # 添加默认版本
                # 添加一些基本的路径配置，避免路径配置更新时出错
                'paths': {
                    'work_dir': project_base_dir,
                    'log_dir': os.path.join(project_base_dir, 'logs'),
                    'checkpoint_dir': os.path.join(project_base_dir, 'checkpoint'),
                    'best_checkpoint_dir': os.path.join(project_base_dir, 'checkpoint', 'best'),
                    'debug_dir': os.path.join(project_base_dir, 'debug'),
                    'data_dir': os.path.join(project_base_dir, 'data'),
                    'output_dir': os.path.join(project_base_dir, 'output'),
                    'temp_dir': os.path.join(project_base_dir, 'temp'),
                    'cache_dir': os.path.join(project_base_dir, 'cache'),
                    'backup_dir': os.path.join(project_base_dir, 'backup'),
                    'download_dir': os.path.join(project_base_dir, 'downloads'),
                    'upload_dir': os.path.join(project_base_dir, 'uploads'),
                    'storage_dir': os.path.join(project_base_dir, 'storage')
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
  base_dir: {temp_base_dir}
  app_name: {final_project_name}系统
  version: 1.0.0
  paths:
    work_dir: {project_base_dir}
    log_dir: {os.path.join(project_base_dir, 'logs')}
    checkpoint_dir: {os.path.join(project_base_dir, 'checkpoint')}
    best_checkpoint_dir: {os.path.join(project_base_dir, 'checkpoint', 'best')}
    debug_dir: {os.path.join(project_base_dir, 'debug')}
    data_dir: {os.path.join(project_base_dir, 'data')}
    output_dir: {os.path.join(project_base_dir, 'output')}
    temp_dir: {os.path.join(project_base_dir, 'temp')}
    cache_dir: {os.path.join(project_base_dir, 'cache')}
    backup_dir: {os.path.join(project_base_dir, 'backup')}
    download_dir: {os.path.join(project_base_dir, 'downloads')}
    upload_dir: {os.path.join(project_base_dir, 'uploads')}
    storage_dir: {os.path.join(project_base_dir, 'storage')}
__type_hints__:
  project_name: str
  experiment_name: str
  base_dir: str
  app_name: str
  version: str
  first_start_time: str
""")

    def is_test_mode(self) -> bool:
        """判断是否为测试模式"""
        if hasattr(self, '_config_path') and self._config_path and ('/tmp/' in self._config_path or '\\temp\\' in self._config_path.lower() or 'pytest' in self._config_path.lower()):
            return True
        return False

    def get_raw_yaml_content(self) -> str:
        """获取原始YAML文件内容"""
        if self._config_path and os.path.exists(self._config_path):
            with open(self._config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 如果内容是标准格式（包含__data__），尝试提取原始内容
            try:
                from ruamel.yaml import YAML
                yaml = YAML()
                yaml.preserve_quotes = True
                yaml.default_flow_style = False
                
                parsed_content = yaml.load(content)
                if isinstance(parsed_content, dict) and '__data__' in parsed_content:
                    # 是标准格式，提取__data__部分作为原始内容
                    original_data = parsed_content['__data__']
                    # 过滤掉ConfigManager自动添加的字段
                    filtered_data = {}
                    for key, value in original_data.items():
                        if key not in ['config_file_path', 'first_start_time', 'paths']:
                            filtered_data[key] = value
                    
                    # 如果有用户数据，重新生成为YAML格式
                    if filtered_data:
                        from io import StringIO
                        output = StringIO()
                        yaml.dump(filtered_data, output)
                        return output.getvalue()
                    else:
                        # 没有用户数据，返回空
                        return ""
                else:
                    # 是原始格式，直接返回内容
                    return content
            except Exception:
                # 解析失败，直接返回原始内容
                return content
                
        raise FileNotFoundError(f"配置文件不存在: {self._config_path}")

    def _resolve_template_variables(self, value: str, context: dict = None) -> str:
        """解析模板变量"""
        if not isinstance(value, str) or '{{' not in value or '}}' not in value:
            return value
        
        if context is None:
            context = self._data
        
        import re
        
        def replace_var(match):
            var_path = match.group(1).strip()
            try:
                # 解析变量路径，支持嵌套访问
                current = context
                for part in var_path.split('.'):
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    elif hasattr(current, '_data') and part in current._data:
                        current = current._data[part]
                    else:
                        return match.group(0)  # 保持原样
                
                return str(current) if current is not None else match.group(0)
            except Exception:
                return match.group(0)  # 保持原样
        
        # 替换模板变量
        result = re.sub(r'\{\{([^}]+)\}\}', replace_var, value)
        return result
    
    def _resolve_all_templates(self, data: dict) -> dict:
        """递归解析所有模板变量"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if isinstance(value, str):
                    result[key] = self._resolve_template_variables(value, data)
                elif isinstance(value, dict):
                    result[key] = self._resolve_all_templates(value)
                else:
                    result[key] = value
            return result
        return data

    def set(self, key: str, value: Any, autosave: bool = True, type_hint: Type = None):
        """设置配置值

        Args:
            key: 配置键
            value: 配置值
            autosave: 是否自动保存
            type_hint: 类型提示
        """
        # 如果是base_dir，尝试转换为多平台格式
        if key == 'base_dir' and isinstance(value, str):
            value = convert_to_multi_platform_config(value, 'base_dir')

        # 设置值
        super().set(key, value, type_hint=type_hint)

        # 如果是路径相关配置，更新路径配置
        if self._should_update_path_config(key):
            self._update_path_configuration()

        # 安排自动保存
        if autosave:
            self._schedule_autosave()




def get_config_manager(
        config_path: str = None,
        watch: bool = True,
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

    if manager:
        # 在返回前，自动设置项目路径（已确保自动创建目录）
        manager.setup_project_paths()
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


def debug_instances():
    """调试方法：显示当前所有实例信息"""
    with ConfigManager._thread_lock:
        print(f"=== ConfigManager实例调试信息 ===")
        print(f"当前实例数量: {len(ConfigManager._instances)}")
        for i, (cache_key, instance) in enumerate(ConfigManager._instances.items()):
            print(f"实例 {i+1}:")
            print(f"  缓存键: {cache_key}")
            print(f"  配置路径: {getattr(instance, '_config_path', 'N/A')}")
            print(f"  已初始化: {getattr(instance, '_initialized', 'N/A')}")
            print(f"  主程序: {getattr(instance, '_is_main_program', 'N/A')}")
            print(f"  实例ID: {id(instance)}")
            print()


def get_instance_count():
    """获取当前实例数量"""
    with ConfigManager._thread_lock:
        return len(ConfigManager._instances)


if __name__ == '__main__':
    get_config_manager(auto_create=True, first_start_time=start_time)
