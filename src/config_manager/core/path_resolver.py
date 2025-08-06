# src/config_manager/core/path_resolver.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import os
import inspect


class PathResolver:
    """配置文件路径解析器"""

    _cached_project_root = None  # 类级别缓存，确保一致性

    @staticmethod
    def normalize_path(path: str) -> str:
        """
        规范化路径为统一格式（使用正斜杠）
        
        Args:
            path: 需要规范化的路径
            
        Returns:
            规范化后的路径（正斜杠格式）
        """
        if not path:
            return path
        # 统一使用正斜杠格式
        return path.replace('\\', '/')
    
    @staticmethod
    def generate_tsb_logs_path(work_dir: str, timestamp: datetime = None) -> str:
        """
        生成TSB日志路径
        
        Args:
            work_dir: 工作目录根路径
            timestamp: 时间戳，默认为当前时间
            
        Returns:
            格式化的TSB日志路径: {work_dir}/tsb_logs/{yyyy}/{week_number}/{mmdd}/{HHMMSS}
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # 提取时间组件
        # 使用ISO日历，因为ISO周可能跨年
        iso_year, iso_week, iso_weekday = timestamp.isocalendar()
        year = str(iso_year)  # 使用ISO年份而不是日历年份
        week_str = f"{iso_week:02d}"  # 格式化为两位数字，不带W前缀
        date_str = timestamp.strftime('%m%d')
        time_str = timestamp.strftime('%H%M%S')
        
        # 确保work_dir是绝对路径
        if not os.path.isabs(work_dir):
            work_dir = os.path.abspath(work_dir)
        
        # 构建路径
        path_components = [
            work_dir,
            'tsb_logs',
            year,
            week_str,
            date_str,
            time_str
        ]
        
        # 使用os.path.join构建路径
        path = os.path.join(*path_components)
        # 使用normalize_path确保跨平台一致性
        return PathResolver.normalize_path(path)

    @staticmethod
    def resolve_config_path(config_path: str) -> str:
        """解析配置文件路径"""
        if config_path is not None:
            resolved_path = os.path.abspath(config_path)
            return resolved_path

        # 修复：智能查找项目根目录，优先向上查找包含src目录的项目根目录
        cwd = os.getcwd()

        # 首先尝试智能查找项目根目录
        project_root = PathResolver._find_project_root()

        if project_root:
            # 找到项目根目录，使用项目根目录下的src/config
            config_dir = os.path.join(project_root, 'src', 'config')
        elif os.path.exists(os.path.join(cwd, 'src')) or PathResolver._is_temp_test_directory(cwd):
            # 当前目录有src结构或是测试目录，直接使用
            config_dir = os.path.join(cwd, 'src', 'config')
        else:
            # 没有找到项目根目录，使用当前工作目录下的config目录
            config_dir = os.path.join(cwd, 'config')

        # 不再自动创建目录，目录创建由config对象生成前统一处理
        resolved_path = os.path.join(config_dir, 'config.yaml')
        return resolved_path

    @staticmethod
    def _find_project_root() -> str | None:
        """查找项目根目录"""
        # 修复：不使用缓存，每次都重新检测，确保在不同目录下能正确检测
        # 这对于测试环境特别重要，因为测试会切换到不同的临时目录

        project_root = None

        # 策略1：从当前工作目录查找（优先级最高，特别是对测试环境）
        cwd = os.getcwd()
        project_root = PathResolver._find_project_root_from_path(cwd)

        # 如果当前工作目录是临时测试目录，直接返回结果，不再查找其他位置
        if PathResolver._is_temp_test_directory(cwd):
            return project_root

        # 策略2：如果当前工作目录没找到，从调用栈查找主程序路径
        if project_root is None:
            main_file_path = PathResolver._find_main_file_from_stack()
            if main_file_path:
                main_dir = os.path.dirname(main_file_path)
                project_root = PathResolver._find_project_root_from_path(main_dir)

        # 策略3：从所有调用栈中的非系统文件查找
        if project_root is None:
            project_root = PathResolver._find_project_root_from_stack()

        return project_root

    @staticmethod
    def _find_main_file_from_stack() -> str | None:
        """从调用栈中找到主程序文件"""
        try:
            for frame_info in reversed(inspect.stack()):  # 从栈底开始查找
                filename = frame_info.filename

                # 跳过系统文件和调试器文件
                if (('site-packages' in filename) or
                        ('lib/python' in filename.lower()) or
                        ('pydev' in filename.lower()) or
                        ('_pydev_' in filename.lower()) or
                        ('<' in filename and '>' in filename)):  # 跳过 <stdin>, <string> 等
                    continue

                # 找到可能的主程序文件
                if filename.endswith('main.py') or '__main__' in frame_info.frame.f_globals.get('__name__', ''):
                    return filename

        except Exception:
            pass
        return None

    @staticmethod
    def _find_project_root_from_stack() -> str | None:
        """从调用栈查找项目根目录"""
        try:
            for frame_info in inspect.stack():
                filename = frame_info.filename
                module_name = frame_info.frame.f_globals.get('__name__', '')

                # 跳过系统模块和调试器模块
                if (module_name.startswith('config_manager') or
                        module_name.startswith('src.config_manager') or
                        'site-packages' in filename or
                        'lib/python' in filename.lower() or
                        'pydev' in filename.lower() or
                        '_pydev_' in filename.lower() or
                        module_name in ['inspect', 'threading', '__main__']):
                    continue

                # 从文件路径开始查找项目根目录
                file_dir = os.path.dirname(filename)
                project_root = PathResolver._find_project_root_from_path(file_dir)
                if project_root:
                    return project_root
        except Exception:
            pass

        return None

    @staticmethod
    def _find_project_root_from_path(start_path: str) -> str | None:
        """从指定路径开始向上查找包含src目录的项目根目录"""
        if not start_path or not os.path.exists(start_path):
            return None

        current_path = os.path.abspath(start_path)
        visited_paths = set()

        while current_path not in visited_paths:
            visited_paths.add(current_path)

            # 特殊处理：如果当前路径本身就是src目录，向上查找
            if os.path.basename(current_path) == 'src':
                parent_path = os.path.dirname(current_path)
                if parent_path != current_path and PathResolver._is_valid_project_root(parent_path):
                    return parent_path

            # 检查当前目录是否包含src子目录
            src_path = os.path.join(current_path, 'src')
            if os.path.exists(src_path) and os.path.isdir(src_path):
                # 找到src目录，检查是否是有效的项目根目录
                if PathResolver._is_valid_project_root(current_path):
                    return current_path
                # 即使没有项目指示文件，如果src目录包含Python代码，也认为是项目根目录
                elif PathResolver._src_has_python_code(src_path):
                    return current_path
                # 特殊处理：如果是临时测试目录且包含src目录，也认为是项目根目录
                elif PathResolver._is_temp_test_directory(current_path):
                    return current_path

            # 向上一级目录
            parent_path = os.path.dirname(current_path)
            if parent_path == current_path:  # 已到根目录
                break
            current_path = parent_path

        return None

    @staticmethod
    def _is_temp_test_directory(path: str) -> bool:
        """检测是否是临时测试目录"""
        try:
            # 检查路径是否包含临时目录标识
            path_lower = path.lower()
            temp_indicators = ['temp', 'tmp', 'test']

            # 检查路径中是否包含临时目录标识
            for indicator in temp_indicators:
                if indicator in path_lower:
                    return True

            # 检查是否在系统临时目录下
            import tempfile
            temp_dir = tempfile.gettempdir().lower()
            if path_lower.startswith(temp_dir):
                return True

            return False
        except Exception:
            return False

    @staticmethod
    def _is_valid_project_root(path: str) -> bool:
        """验证是否是有效的项目根目录"""
        try:
            # 检查项目指示文件
            project_indicators = [
                'setup.py', 'pyproject.toml', 'requirements.txt',
                '.git', '.gitignore', 'README.md', 'main.py', 'pytest.ini'
            ]

            has_indicators = any(
                os.path.exists(os.path.join(path, indicator))
                for indicator in project_indicators
            )

            # 检查src目录下是否有Python代码
            src_path = os.path.join(path, 'src')
            src_has_python = PathResolver._src_has_python_code(src_path)

            return has_indicators or src_has_python

        except Exception:
            return False

    @staticmethod
    def _src_has_python_code(src_path: str) -> bool:
        """检查src目录下是否有Python代码"""
        if not os.path.exists(src_path) or not os.path.isdir(src_path):
            return False

        try:
            for item in os.listdir(src_path):
                if item.startswith('.'):
                    continue
                item_path = os.path.join(src_path, item)
                if (item.endswith('.py') or
                        (os.path.isdir(item_path) and
                         os.path.exists(os.path.join(item_path, '__init__.py')))):
                    return True
        except (PermissionError, OSError):
            pass

        return False