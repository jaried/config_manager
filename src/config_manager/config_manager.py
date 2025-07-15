# src/config_manager/config_manager.py
from __future__ import annotations
from datetime import datetime
from typing import Union, Type

start_time = datetime.now()

import os
import threading
import uuid
import tempfile
from typing import Any
from .core.manager import ConfigManagerCore
from .core.path_resolver import PathResolver
from .core.cross_platform_paths import convert_to_multi_platform_config

# 全局调用链显示开关 - 手工修改这个值来控制调用链显示
ENABLE_CALL_CHAIN_DISPLAY = False  # 默认关闭调用链显示


class ConfigManager(ConfigManagerCore):
    """配置管理器类，支持自动保存和类型提示"""
    _production_instances = {}  # 生产模式实例缓存（基于配置路径）
    _instances = {}  # 多例缓存（测试模式）
    _thread_lock = threading.Lock()
    _global_listeners = []
    _initialized = False  # 初始化标志
    _test_mode = False  # 测试模式标志
    _paths_initialized = False  # 路径配置初始化标志

    def __new__(cls, config_path: str = None,
                watch: bool = True, auto_create: bool = False,
                autosave_delay: float = 0.1, first_start_time: datetime = None,
                test_mode: bool = False):
        
        # 设置测试模式标志
        cls._test_mode = test_mode
        
        if test_mode:
            # 测试模式：使用多例模式
            return cls._create_test_instance(config_path, watch, auto_create, autosave_delay, first_start_time)
        else:
            # 生产模式：使用基于路径的实例缓存模式
            return cls._create_production_instance(config_path, watch, auto_create, autosave_delay, first_start_time)

    @classmethod
    def _create_test_instance(cls, config_path: str, watch: bool, auto_create: bool, 
                             autosave_delay: float, first_start_time: datetime):
        """创建测试模式实例（多例模式）"""
        # 生成缓存键，包含first_start_time信息以区分不同时间的测试实例
        cache_key = cls._generate_test_cache_key(config_path, first_start_time)
        
        if cache_key not in cls._instances:
            with cls._thread_lock:
                if cache_key not in cls._instances:
                    # 创建新实例
                    instance = object.__new__(cls)
                    instance.__dict__['_data'] = {}
                    ConfigManagerCore.__init__(instance)
                    
                    # 设置测试模式标志
                    instance._test_mode = True
                    
                    success = instance.initialize(
                        config_path, watch, auto_create, autosave_delay, first_start_time=first_start_time
                    )
                    
                    if not success:
                        print("⚠️  配置管理器初始化失败，返回None")
                        return None
                    
                    cls._instances[cache_key] = instance
        
        return cls._instances[cache_key]

    @classmethod
    def _create_production_instance(cls, config_path: str, watch: bool, auto_create: bool, 
                                   autosave_delay: float, first_start_time: datetime):
        """创建生产模式实例（基于路径的实例缓存模式）"""
        # 生成缓存键
        cache_key = cls._generate_production_cache_key(config_path)
        
        if cache_key not in cls._production_instances:
            with cls._thread_lock:
                if cache_key not in cls._production_instances:
                    # 创建新实例
                    instance = object.__new__(cls)
                    instance.__dict__['_data'] = {}
                    ConfigManagerCore.__init__(instance)
                    
                    # 设置测试模式标志
                    instance._test_mode = False
                    
                    success = instance.initialize(
                        config_path, watch, auto_create, autosave_delay, first_start_time=first_start_time
                    )
                    
                    if not success:
                        print("⚠️  配置管理器初始化失败，返图None")
                        return None
                    
                    cls._production_instances[cache_key] = instance
                    cls._initialized = True
        
        return cls._production_instances[cache_key]
    
    @classmethod
    def _generate_production_cache_key(cls, config_path: str) -> str:
        """生成生产模式的缓存键，基于配置文件的绝对路径"""
        try:
            if config_path is not None:
                # 显式路径：使用绝对路径，标准化路径分隔符
                abs_path = os.path.abspath(config_path)
                normalized_path = abs_path.replace('\\', '/')
                return f"production:{normalized_path}"
            else:
                # 默认路径：基于当前工作目录
                cwd = os.getcwd()
                default_config_path = os.path.join(cwd, "src", "config", "config.yaml")
                abs_path = os.path.abspath(default_config_path)
                normalized_path = abs_path.replace('\\', '/')
                return f"production:{normalized_path}"
        except Exception:
            # 如果路径解析失败，生成一个基于输入参数的缓存键
            if config_path is not None:
                return f"production:explicit:{config_path}"
            else:
                return f"production:default:{os.getcwd()}"

    @classmethod  
    def _generate_test_cache_key(cls, config_path: str, first_start_time: datetime = None) -> str:
        """生成测试模式的缓存键，同一测试用例内相同路径返回相同键，不同测试用例间隔离"""
        try:
            # 获取测试用例标识符实现测试间隔离
            test_identifier = cls._get_test_identifier()
            
            # 如果提供了first_start_time，添加到缓存键中以区分不同时间的实例
            time_suffix = ""
            if first_start_time is not None:
                time_suffix = f":{first_start_time.strftime('%Y%m%d_%H%M%S')}"
            
            # 对于测试模式，缓存键主要基于测试标识符，而不是具体的配置路径
            # 这样同一个测试中的多次调用会使用相同的缓存键
            if config_path is not None:
                # 如果明确指定了配置路径，检查是否是测试环境路径
                if '/tmp/tests/' in config_path or '\\temp\\tests\\' in config_path.lower():
                    # 是测试环境路径，使用explicit前缀和完整路径
                    abs_path = os.path.abspath(config_path)
                    normalized_path = abs_path.replace('\\', '/')
                    base_key = f"explicit:{normalized_path}:test:{test_identifier}{time_suffix}"
                else:
                    # 是显式指定的路径，包含路径信息
                    abs_path = os.path.abspath(config_path)
                    normalized_path = abs_path.replace('\\', '/')
                    base_key = f"explicit:{normalized_path}:test:{test_identifier}{time_suffix}"
            else:
                # 自动路径：生成测试环境路径并使用explicit前缀
                try:
                    _, test_config_path = cls._generate_test_environment_path(first_start_time)
                    normalized_path = os.path.abspath(test_config_path).replace('\\', '/')
                    base_key = f"explicit:{normalized_path}:test:{test_identifier}{time_suffix}"
                except Exception:
                    # 如果生成测试环境路径失败，使用当前工作目录
                    current_dir = os.getcwd()
                    normalized_dir = os.path.abspath(current_dir).replace('\\', '/')
                    base_key = f"auto:{normalized_dir}:test:{test_identifier}{time_suffix}"
            
            return base_key
        except Exception:
            # 如果出错，生成一个基于测试标识符的缓存键
            test_identifier = cls._get_test_identifier()
            time_suffix = ""
            if first_start_time is not None:
                try:
                    time_suffix = f":{first_start_time.strftime('%Y%m%d_%H%M%S')}"
                except:
                    pass
            return f"fallback:test:{test_identifier}{time_suffix}"
    
    @classmethod
    def _get_test_identifier(cls) -> str:
        """获取当前测试用例的唯一标识符"""
        try:
            import inspect
            
            # 遍历调用栈查找测试函数
            for frame_info in inspect.stack():
                function_name = frame_info.function
                filename = frame_info.filename
                
                # 检查是否是测试函数（函数名以test_开头或在测试文件中）
                if (function_name.startswith('test_') and 
                    ('test_' in filename or 'tests/' in filename)):
                    
                    # 生成基于测试函数和文件的唯一标识，但不包含行号以确保稳定性
                    test_id = f"{filename}::{function_name}"
                    # 使用哈希生成短标识符
                    import hashlib
                    return hashlib.md5(test_id.encode()).hexdigest()[:8]
            
            # 如果找不到测试函数，使用当前进程ID作为备用方案，这样同一个测试进程内是稳定的
            import os
            fallback_id = f"process_{os.getpid()}"
            import hashlib
            return hashlib.md5(fallback_id.encode()).hexdigest()[:8]
            
        except Exception:
            # 最后的备用方案：基于进程ID的稳定标识符
            import os
            try:
                process_id = f"process_{os.getpid()}"
                import hashlib
                return hashlib.md5(process_id.encode()).hexdigest()[:8]
            except (ImportError, AttributeError, OSError):
                return "default"

    def __init__(self, config_path: str = None,
                 watch: bool = False, auto_create: bool = False,
                 autosave_delay: float = 0.1, first_start_time: datetime = None,
                 test_mode: bool = False):
        """初始化配置管理器，单例模式下可能被多次调用"""
        # 单例模式下，__init__可能被多次调用，但只有第一次有效
        pass

    @staticmethod
    def generate_config_id() -> str:
        """生成唯一配置ID"""
        config_id = str(uuid.uuid4())
        return config_id

    @classmethod
    def _setup_test_environment(cls, original_config_path: str = None, first_start_time: datetime = None) -> str:
        """设置测试环境"""
        # 基于当前工作目录生成测试配置路径
        cwd = os.getcwd()
        print(f"✓ 基于当前工作目录生成测试路径: {cwd}")
        
        # 生成测试环境路径
        test_base_dir, test_config_path = cls._generate_test_environment_path(first_start_time)
        
        # 设置测试模式环境变量
        os.environ['CONFIG_MANAGER_TEST_MODE'] = 'true'
        os.environ['CONFIG_MANAGER_TEST_BASE_DIR'] = test_base_dir
        print(f"✓ 开始执行路径替换，test_base_dir: {test_base_dir}, temp_base: {tempfile.gettempdir()}")
        
        # 确保测试配置目录存在
        os.makedirs(os.path.dirname(test_config_path), exist_ok=True)
        
        # 如果传入了明确的配置路径，将其作为生产配置源
        prod_config_path = original_config_path
        
        # 如果没有传入明确的配置路径，尝试检测生产配置
        if not prod_config_path:
            prod_config_path = cls._detect_production_config()
            if prod_config_path:
                print(f"✓ 检测到生产配置: {prod_config_path}")
            else:
                print("⚠️  未检测到生产配置，将尝试其他方法")

        # 如果没有找到生产配置，尝试更广泛的搜索
        if not prod_config_path or not os.path.exists(prod_config_path):
            print("⚠️  生产配置不存在，尝试更广泛的搜索...")

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

                        # 跳过pytest相关文件
                        if 'pytest' in filename or '_pytest' in filename:
                            continue

                        # 跳过Python标准库文件
                        if filename.startswith('<') or 'site-packages' in filename:
                            continue

                        # 尝试从调用文件所在目录查找配置文件
                        call_dir = os.path.dirname(os.path.abspath(filename))
                        print(f"从调用文件目录查找: {call_dir}")

                        test_paths = [
                            os.path.join(call_dir, 'src', 'config', 'config.yaml'),
                            os.path.join(call_dir, 'config', 'config.yaml'),
                            os.path.join(call_dir, 'config.yaml'),
                        ]

                        for path in test_paths:
                            if os.path.exists(path):
                                # 修复: 如果找到的配置文件在tests目录下，跳过
                                if 'tests' + os.sep in path or '/tests/' in path:
                                    print(f"⚠️  跳过tests目录下的配置文件: {path}")
                                    continue
                                prod_config_path = path
                                print(f"✓ 从调用文件目录找到配置文件: {prod_config_path}")
                                break

                            if prod_config_path and os.path.exists(prod_config_path):
                                break

                except Exception as e:
                    print(f"⚠️  从调用栈查找时出错: {e}")

            # 策略4: 尝试常见项目结构
            if not prod_config_path or not os.path.exists(prod_config_path):
                print("尝试常见项目结构...")
                try:
                    # 尝试从当前工作目录向上查找，寻找包含src/config/config.yaml的项目结构
                    current_dir = os.getcwd()
                    for level in range(10):  # 最多向上查找10级目录
                        test_path = os.path.join(current_dir, 'src', 'config', 'config.yaml')
                        if os.path.exists(test_path):
                            prod_config_path = test_path
                            print(f"✓ 从常见项目结构找到配置文件: {prod_config_path}")
                            break
                        
                        parent_dir = os.path.dirname(current_dir)
                        if parent_dir == current_dir:  # 已到根目录
                            break
                        current_dir = parent_dir
                except Exception as e:
                    print(f"⚠️  尝试常见项目结构时出错: {e}")

        # 如果找到了生产配置，复制到测试环境
        if prod_config_path and os.path.exists(prod_config_path):
            # 复制生产配置到测试环境
            cls._copy_production_config_to_test(prod_config_path, test_config_path, first_start_time)
            
            return test_config_path
        else:
            # 如果没有找到生产配置，创建空的测试配置
            # 创建空的测试配置
            cls._create_empty_test_config(test_config_path, first_start_time)
            
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
            except (ValueError, AttributeError, TypeError):
                first_start_time = datetime.now()
        elif not isinstance(first_start_time, datetime):
            first_start_time = datetime.now()

        # 使用更简洁的日期和时间格式
        date_str = first_start_time.strftime("%Y%m%d")
        time_str = first_start_time.strftime("%H%M%S")

        # 基于当前工作目录生成测试路径
        cwd = os.getcwd()
        
        # 检查是否在pytest环境中
        pytest_tmp_path = cls._detect_pytest_tmp_path()
        if pytest_tmp_path:
            test_base_dir = pytest_tmp_path
            print(f"✓ 检测到pytest环境，使用pytest tmp_path: {test_base_dir}")
        else:
            # 基于当前工作目录生成唯一的测试目录
            # 使用当前工作目录的哈希值来确保不同目录生成不同的路径
            import hashlib
            cwd_hash = hashlib.md5(cwd.encode()).hexdigest()[:8]
            test_base_dir = os.path.join(tempfile.gettempdir(), 'tests', date_str, time_str, cwd_hash)
            print(f"✓ 基于当前工作目录生成测试路径: {test_base_dir}")
        
        test_config_path = os.path.join(test_base_dir, 'src', 'config', 'config.yaml')
        
        print(f"✓ 开始执行路径替换，test_base_dir: {test_base_dir}, temp_base: {tempfile.gettempdir()}")
        return test_base_dir, test_config_path

    @classmethod
    def _detect_pytest_tmp_path(cls) -> Union[str, None]:
        """检测pytest的tmp_path"""
        try:
            # 检查是否在pytest环境中
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
    def _is_production_config_path(cls, config_path: str) -> bool:
        """判断配置路径是否是生产配置路径"""
        if not config_path:
            return False
            
        abs_config_path = os.path.abspath(config_path)
        
        # 检查是否在临时目录中（临时配置文件）
        import tempfile
        temp_dir = tempfile.gettempdir()
        if abs_config_path.startswith(temp_dir):
            return False
            
        # 检查是否是标准的项目配置路径（包含src/config结构）
        if 'src/config/config.yaml' in abs_config_path.replace('\\', '/'):
            return True
            
        # 检查是否在项目根目录的config目录中
        if abs_config_path.endswith('/config/config.yaml') or abs_config_path.endswith('\\config\\config.yaml'):
            return True
            
        return False

    @classmethod
    def _copy_production_config_to_test(cls, prod_config_path: str, test_config_path: str,
                                        first_start_time: datetime = None, project_name: str = None):
        """将生产配置复制到测试环境"""
        # 确保测试目录存在
        os.makedirs(os.path.dirname(test_config_path), exist_ok=True)

        # 判断是否是真正的生产配置（在项目标准位置）
        is_production_config = cls._is_production_config_path(prod_config_path)

        if os.path.exists(prod_config_path):
            # 检查源路径和目标路径是否相同
            if os.path.abspath(prod_config_path) == os.path.abspath(test_config_path):
                print(f"✓ 源路径和目标路径相同，跳过复制: {prod_config_path}")
                # 直接更新现有配置
                cls._update_test_config_paths(test_config_path, first_start_time, project_name, from_production=is_production_config)
            else:
                # 复制配置文件（添加重试机制处理Windows文件锁定）
                cls._safe_copy_file(prod_config_path, test_config_path)
                if is_production_config:
                    print(f"✓ 已从生产环境复制配置: {prod_config_path} -> {test_config_path}")
                else:
                    print(f"✓ 已从自定义配置复制: {prod_config_path} -> {test_config_path}")

                # 修改测试配置中的路径信息
                cls._update_test_config_paths(test_config_path, first_start_time, project_name, from_production=is_production_config)
        else:
            # 如果生产配置不存在，创建空的测试配置
            cls._create_empty_test_config(test_config_path, first_start_time, project_name)

    @classmethod
    def _safe_copy_file(cls, src_path: str, dst_path: str, max_retries: int = 3):
        """安全复制文件，处理Windows文件锁定问题"""
        import time
        
        for attempt in range(max_retries):
            try:
                # 确保目标目录存在
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                
                # 先读取源文件内容
                with open(src_path, 'r', encoding='utf-8') as src_file:
                    content = src_file.read()
                
                # 写入目标文件
                with open(dst_path, 'w', encoding='utf-8') as dst_file:
                    dst_file.write(content)
                
                return  # 成功复制，退出函数
                
            except PermissionError as e:
                if attempt < max_retries - 1:
                    print(f"⚠️  文件复制失败（尝试 {attempt + 1}/{max_retries}）: {e}")
                    time.sleep(0.1 * (attempt + 1))  # 递增延迟
                    continue
                else:
                    # 最后一次尝试失败，抛出异常
                    raise PermissionError(f"无法复制文件（已重试{max_retries}次）: {src_path} -> {dst_path}") from e
            except Exception as e:
                raise RuntimeError(f"复制文件时发生未知错误: {e}") from e

    @classmethod
    def _update_test_config_paths(cls, test_config_path: str, first_start_time: datetime = None,
                                  project_name: str = None, from_production: bool = False):
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
            current_project_name = config_data.get('project_name', 'project_name')
            
            # 如果传入了project_name，强制更新
            if project_name:
                config_data['project_name'] = project_name
            # 只有从生产配置复制且project_name是默认的'project_name'时，才替换为'test_project'
            elif from_production and current_project_name == 'project_name':
                config_data['project_name'] = 'test_project'
            
            # 根据任务6：简化test_mode逻辑，只设置base_dir
            # 只修改base_dir，其他路径字段保持原值
            config_data['base_dir'] = test_base_dir

            # 更新时间信息
            if time_to_use is not None:
                if isinstance(time_to_use, datetime):
                    config_data['first_start_time'] = time_to_use.isoformat()
                else:
                    # time_to_use是字符串，直接使用
                    config_data['first_start_time'] = str(time_to_use)
            
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

    def __getattr__(self, name: str) -> Any:
        """ConfigManager的属性访问，支持选择性自动解包
        
        对于ConfigManager的顶级属性访问，支持单值ConfigNode的自动解包
        但只对特定键名进行解包，避免破坏嵌套结构
        """
        # 先调用父类方法获取值
        value = super().__getattr__(name)
        
        # 对于ConfigNode，检查是否应该自动解包
        from .config_node import ConfigNode
        if isinstance(value, ConfigNode):
            # 只对顶级属性进行自动解包，不对嵌套结构进行解包
            return value._get_auto_unpacked_value()
        
        return value


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
    # 测试模式特殊处理：如果当前有生产模式实例，需要清理
    if test_mode and ConfigManager._production_instances:
        print("⚠️  测试模式：清理现有生产模式实例")
        _clear_instances_for_testing()
    
    # 测试模式处理
    if test_mode:
        # 测试模式下，先检查缓存，避免重复生成测试环境
        original_config_path = config_path  # 保存原始路径
        cache_key = ConfigManager._generate_test_cache_key(original_config_path)
        
        # 如果缓存中已有实例，直接返回
        if cache_key in ConfigManager._instances:
            return ConfigManager._instances[cache_key]
        
        # 缓存中没有，才生成测试环境路径
        config_path = ConfigManager._setup_test_environment(original_config_path, first_start_time)
        auto_create = True  # 测试模式强制启用自动创建
        watch = False  # 测试模式禁用文件监视
    else:
        # 非测试模式：智能检测测试环境 - 如果配置路径包含临时目录，自动启用auto_create
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
        # 修复：只在首次初始化时设置项目路径，避免重复初始化
        if not getattr(manager, '_paths_initialized', False):
            manager.setup_project_paths()
            manager._paths_initialized = True
    return manager


def _clear_instances_for_testing():
    """清理所有实例，仅用于测试"""
    with ConfigManager._thread_lock:
        # 清理生产模式实例
        for instance in ConfigManager._production_instances.values():
            if hasattr(instance, '_cleanup'):
                try:
                    instance._cleanup()
                except Exception:
                    pass  # 忽略清理过程中的错误
        ConfigManager._production_instances.clear()
        ConfigManager._initialized = False
        ConfigManager._paths_initialized = False
        
        # 清理测试模式实例
        for instance in ConfigManager._instances.values():
            if hasattr(instance, '_cleanup'):
                try:
                    instance._cleanup()
                except Exception:
                    pass  # 忽略清理过程中的错误
        ConfigManager._instances.clear()

    # 强制垃圾回收
    import gc
    gc.collect()
    return


def debug_instances():
    """调试方法：显示当前所有实例信息"""
    with ConfigManager._thread_lock:
        print("=== ConfigManager实例调试信息 ===")
        print(f"测试模式: {ConfigManager._test_mode}")
        
        if ConfigManager._test_mode:
            # 测试模式：显示多例信息
            print(f"测试模式实例数量: {len(ConfigManager._instances)}")
            for i, (cache_key, instance) in enumerate(ConfigManager._instances.items()):
                print(f"测试实例 {i+1}:")
                print(f"  缓存键: {cache_key}")
                print(f"  配置路径: {getattr(instance, '_config_path', 'N/A')}")
                print(f"  测试模式: {getattr(instance, '_test_mode', 'N/A')}")
                print(f"  路径已初始化: {getattr(instance, '_paths_initialized', 'N/A')}")
                print(f"  实例ID: {id(instance)}")
        else:
            # 生产模式：显示所有实例信息
            if ConfigManager._production_instances:
                print(f"生产模式实例数量: {len(ConfigManager._production_instances)}")
                for i, (cache_key, instance) in enumerate(ConfigManager._production_instances.items()):
                    print(f"  实例 {i+1}:")
                    print(f"    缓存键: {cache_key}")
                    print(f"    配置路径: {getattr(instance, '_config_path', 'N/A')}")
                    print(f"    已初始化: {getattr(instance, '_initialized', 'N/A')}")
                    print(f"    测试模式: {getattr(instance, '_test_mode', 'N/A')}")
                    print(f"    路径已初始化: {getattr(instance, '_paths_initialized', 'N/A')}")
                    print(f"    实例ID: {id(instance)}")
            else:
                print("当前没有生产模式实例")
        print()


def get_instance_count():
    """获取当前实例数量"""
    with ConfigManager._thread_lock:
        if ConfigManager._test_mode:
            return len(ConfigManager._instances)
        else:
            return len(ConfigManager._production_instances)


if __name__ == '__main__':
    get_config_manager(auto_create=True, first_start_time=start_time)
