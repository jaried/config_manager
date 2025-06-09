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
                    # 修复：不管初始化是否成功，都返回实例，确保不返回None
                    try:
                        instance.initialize(
                            config_path, watch, auto_create, autosave_delay, first_start_time=first_start_time
                        )
                    except Exception as e:
                        # 即使初始化失败，也要确保实例可用（用于测试环境）
                        print(f"配置管理器初始化警告: {e}")
                        # 设置基本的默认状态
                        if not hasattr(instance, '_data') or instance._data is None:
                            instance._data = {}
                        if not hasattr(instance, '_config_path'):
                            instance._config_path = cache_key.replace('auto:', '') if cache_key.startswith(
                                'auto:') else cache_key

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
        if original_config_path:
            prod_config_path = original_config_path
        else:
            prod_config_path = cls._detect_production_config()

        # 2. 从生产配置中读取project_name和first_start_time
        project_name = "project_name"  # 默认值
        config_first_start_time = None

        if prod_config_path and os.path.exists(prod_config_path):
            try:
                from ruamel.yaml import YAML
                yaml = YAML()
                with open(prod_config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.load(f) or {}

                # 获取project_name
                if '__data__' in config_data:
                    project_name = config_data['__data__'].get('project_name', 'project_name')
                    config_first_start_time = config_data['__data__'].get('first_start_time')
                else:
                    project_name = config_data.get('project_name', 'project_name')
                    config_first_start_time = config_data.get('first_start_time')

            except Exception as e:
                print(f"⚠️  读取生产配置失败，使用默认project_name: {e}")

        # 3. 确定使用的first_start_time（优先级：传入参数 > 配置文件 > 当前时间）
        final_first_start_time = first_start_time or config_first_start_time
        if isinstance(final_first_start_time, str):
            try:
                from datetime import datetime
                final_first_start_time = datetime.fromisoformat(final_first_start_time.replace('Z', '+00:00'))
            except:
                final_first_start_time = None

        # 4. 生成测试环境路径（基于first_start_time和project_name）
        test_base_dir, test_config_path = cls._generate_test_environment_path(final_first_start_time, project_name)

        # 5. 复制配置到测试环境
        if prod_config_path and os.path.exists(prod_config_path):
            cls._copy_production_config_to_test(prod_config_path, test_config_path, final_first_start_time)
            print(f"✓ 已从生产环境复制配置: {prod_config_path} -> {test_config_path}")
        else:
            # 创建空的测试配置
            cls._create_empty_test_config(test_config_path, final_first_start_time)
            print(f"✓ 已创建空的测试配置: {test_config_path}")

        # 6. 设置测试环境变量（可选）
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
            return standard_config_path

        # 3. 检查其他可能的配置路径
        possible_paths = [
            os.path.join(project_root, 'config', 'config.yaml'),
            os.path.join(project_root, 'config.yaml'),
            os.path.join(project_root, 'src', 'config.yaml')
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    @classmethod
    def _copy_production_config_to_test(cls, prod_config_path: str, test_config_path: str,
                                        first_start_time: datetime = None):
        """将生产配置复制到测试环境"""
        # 确保测试目录存在
        os.makedirs(os.path.dirname(test_config_path), exist_ok=True)

        if os.path.exists(prod_config_path):
            # 复制配置文件
            shutil.copy2(prod_config_path, test_config_path)

            # 修改测试配置中的路径信息
            cls._update_test_config_paths(test_config_path, first_start_time)
        else:
            # 如果生产配置不存在，创建空的测试配置
            cls._create_empty_test_config(test_config_path, first_start_time)

    @classmethod
    def _update_test_config_paths(cls, test_config_path: str, first_start_time: datetime = None):
        """更新测试配置中的路径信息"""
        try:
            from ruamel.yaml import YAML
            yaml = YAML()
            yaml.preserve_quotes = True
            yaml.default_flow_style = False

            # 读取配置文件
            with open(test_config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.load(f) or {}

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

            # 从路径中提取project_name
            project_name = "project_name"  # 默认值
            try:
                # 路径格式: /temp/tests/YYYYMMDD/HHMMSS/project_name/src/config/config.yaml
                path_parts = test_config_path.replace('\\', '/').split('/')
                if len(path_parts) >= 3:
                    # 找到project_name部分（在src之前的最后一个部分）
                    for i, part in enumerate(path_parts):
                        if part == 'src' and i > 0:
                            project_name = path_parts[i - 1]
                            break
            except:
                pass  # 使用默认值

            # 更新路径信息和时间信息
            if '__data__' in config_data:
                # 标准格式
                config_data['__data__']['config_file_path'] = test_config_path
                if time_to_use is not None:  # 只在需要时更新first_start_time
                    config_data['__data__']['first_start_time'] = time_to_use.isoformat()

                # 确保project_name字段存在
                if 'project_name' not in config_data['__data__']:
                    config_data['__data__']['project_name'] = project_name

                # 动态替换所有路径字段
                cls._replace_all_paths_in_config(config_data['__data__'], test_base_dir, temp_base)
            else:
                # 原始格式
                config_data['config_file_path'] = test_config_path
                if time_to_use is not None:  # 只在需要时更新first_start_time
                    config_data['first_start_time'] = time_to_use.isoformat()

                # 确保project_name字段存在
                if 'project_name' not in config_data:
                    config_data['project_name'] = project_name

                # 动态替换所有路径字段
                cls._replace_all_paths_in_config(config_data, test_base_dir, temp_base)

            # 保存更新后的配置
            with open(test_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)

        except Exception as e:
            print(f"⚠️  更新测试配置路径失败: {e}")

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
            'base_dir': test_base_dir,
            'work_dir': test_base_dir,
            'log_dir': os.path.join(test_base_dir, 'logs'),
            'data_dir': os.path.join(test_base_dir, 'data'),
            'output_dir': os.path.join(test_base_dir, 'output'),
            'temp_dir': os.path.join(test_base_dir, 'temp'),
            'cache_dir': os.path.join(test_base_dir, 'cache'),
            'backup_dir': os.path.join(test_base_dir, 'backup'),
            'download_dir': os.path.join(test_base_dir, 'downloads'),
            'upload_dir': os.path.join(test_base_dir, 'uploads'),
            'storage_dir': os.path.join(test_base_dir, 'storage')
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
            return os.path.join(test_base_dir, original_path.lstrip('./'))

        # 处理绝对路径
        if os.path.isabs(original_path):
            # 提取路径的最后几个部分，在测试环境中重建
            path_parts = original_path.replace('\\', '/').split('/')
            # 取最后1-2个有意义的部分
            meaningful_parts = [part for part in path_parts[-2:] if part and part != '..']
            if meaningful_parts:
                return os.path.join(test_base_dir, *meaningful_parts)
            else:
                return test_base_dir

        # 其他情况，直接在测试环境下创建
        return os.path.join(test_base_dir, original_path)

    @classmethod
    def _create_empty_test_config(cls, test_config_path: str, first_start_time: datetime = None):
        """创建空的测试配置"""
        # 确保测试目录存在
        os.makedirs(os.path.dirname(test_config_path), exist_ok=True)

        # 确定使用的时间
        if first_start_time:
            time_to_use = first_start_time
        else:
            time_to_use = datetime.now()

        # 从路径中提取project_name
        project_name = "project_name"  # 默认值
        try:
            # 路径格式: /temp/tests/YYYYMMDD/HHMMSS/project_name/src/config/config.yaml
            path_parts = test_config_path.replace('\\', '/').split('/')
            if len(path_parts) >= 3:
                # 找到project_name部分（在src之前的最后一个部分）
                for i, part in enumerate(path_parts):
                    if part == 'src' and i > 0:
                        project_name = path_parts[i - 1]
                        break
        except:
            pass  # 使用默认值

        # 创建空配置
        empty_config = {
            '__data__': {
                'config_file_path': test_config_path,
                'first_start_time': time_to_use.isoformat(),
                'project_name': project_name
            },
            '__type_hints__': {}
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
                f.write(
                    f"__data__:\n  config_file_path: {test_config_path}\n  first_start_time: {time_str}\n  project_name: {project_name}\n__type_hints__: {{}}\n")

def get_config_manager(
        config_path: str = None,
        watch: bool = False,
        auto_create: bool = False,
        autosave_delay: float = None,
        first_start_time: datetime = None,
        test_mode: bool = False
) -> ConfigManager:
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
        ConfigManager 实例（永远不返回None）
    """
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
