    # 修复现有方法中的bug，只需要替换这两个方法：

    @classmethod
    def _is_regex_pattern(cls, value: str) -> bool:
        """判断是否是正则表达式模式"""
        # 先排除Windows路径，避免误判
        if len(value) >= 2 and value[1] == ':' and value[0].isalpha():
            return False

        # 检查正则表达式特征
        regex_indicators = [
            value.startswith('^') or value.endswith('$'),  # 锚点
            '\\' in value and any(char in value for char in ['d', 'w', 's', 'n', 't']) and not (
                        '\\' in value and ('/' in value or ':' in value)),  # 转义字符但排除路径
            '[' in value and ']' in value,  # 字符类
            '(' in value and ')' in value,  # 分组
            '+' in value or '*' in value or '?' in value,  # 量词
            '|' in value,  # 或操作符
            '{' in value and '}' in value,  # 重复次数
        ]
        return any(regex_indicators)


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

        return False


    # 此外，还需要添加路径替换相关方法（如果ConfigManager类中还没有的话）：

    @classmethod
    def _replace_all_paths_in_config(cls, config_data: Dict[str, Any], test_base_dir: str, temp_base: str):
        """递归替换配置中的所有路径字段"""
        # 特殊路径映射 - 预定义的路径字段映射
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
            'storage_dir': os.path.join(test_base_dir, 'storage'),
        }

        def replace_paths_recursive(obj, parent_key=''):
            """递归替换路径"""
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
                                    print(f"✓ 替换路径字段 {full_key}: {value} -> {new_path}")
                            else:
                                # 通用路径替换：将绝对路径替换为测试环境路径
                                new_path = cls._convert_to_test_path(value, test_base_dir, temp_base)
                                if new_path != value:
                                    obj[key] = new_path
                                    print(f"✓ 替换路径字段 {full_key}: {value} -> {new_path}")
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
                            print(f"✓ 替换列表路径 {parent_key}[{i}]: {item} -> {new_path}")

        replace_paths_recursive(config_data)


    @classmethod
    def _convert_to_test_path(cls, original_path: str, test_base_dir: str, temp_base: str) -> str:
        """将原始路径转换为测试环境路径"""
        if not original_path or not isinstance(original_path, str):
            return original_path

        # 如果已经是测试环境的路径，直接返回
        if temp_base in original_path:
            return original_path

        # 相对路径处理
        if original_path.startswith('./') or original_path.startswith('../'):
            # 相对路径映射到测试环境根目录
            relative_part = original_path[2:] if original_path.startswith('./') else original_path[3:]
            return os.path.join(test_base_dir, relative_part)

        # 绝对路径处理
        if os.path.isabs(original_path):
            # 提取文件名或最后一个目录名
            path_name = os.path.basename(original_path.rstrip('/\\')) or 'data'
            return os.path.join(test_base_dir, path_name)

        # 其他情况，映射到测试环境
        return os.path.join(test_base_dir, original_path)