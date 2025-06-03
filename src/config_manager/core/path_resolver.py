# src/config_manager/core/path_resolver.py
from __future__ import annotations
from datetime import datetime

start_time = datetime.now()

import os
import inspect


class PathResolver:
    """配置文件路径解析器"""

    @staticmethod
    def resolve_config_path(config_path: str) -> str:
        """解析配置文件路径"""
        if config_path is not None:
            resolved_path = os.path.abspath(config_path)
            return resolved_path

        # 智能查找项目根目录
        project_root = PathResolver._find_project_root()

        if project_root:
            config_dir = os.path.join(project_root, 'src', 'config')
        else:
            # 没有找到项目根目录，使用当前工作目录下的config目录
            cwd = os.getcwd()
            config_dir = os.path.join(cwd, 'config')

        os.makedirs(config_dir, exist_ok=True)
        resolved_path = os.path.join(config_dir, 'config.yaml')
        return resolved_path

    @staticmethod
    def _find_project_root() -> str | None:
        """查找项目根目录"""
        # 先从当前工作目录查找
        cwd = os.getcwd()
        project_root = PathResolver._find_project_root_from_path(cwd)

        # 如果没找到，从调用栈中的文件路径查找
        if project_root is None:
            try:
                for i, frame_info in enumerate(inspect.stack()):
                    filename = frame_info.filename
                    module_name = frame_info.frame.f_globals.get('__name__', '')

                    # 跳过config_manager模块自身和标准库模块
                    if (module_name.startswith('config_manager') or
                            module_name.startswith('src.config_manager') or
                            'site-packages' in filename or
                            'lib/python' in filename.lower() or
                            module_name in ['inspect', 'threading', '__main__']):
                        continue

                    # 从文件路径开始查找项目根目录
                    file_dir = os.path.dirname(filename)
                    project_root = PathResolver._find_project_root_from_path(file_dir)
                    if project_root:
                        break
            except Exception:
                # 如果调用栈分析失败，继续使用当前工作目录
                pass

        return project_root

    @staticmethod
    def _find_project_root_from_path(start_path: str) -> str | None:
        """从指定路径开始向上查找包含src目录的项目根目录"""
        current_path = os.path.abspath(start_path)

        while True:
            # 避免将src目录本身识别为项目根目录
            current_dir_name = os.path.basename(current_path)
            if current_dir_name == 'src':
                parent_path = os.path.dirname(current_path)
                if parent_path != current_path:
                    current_path = parent_path
                    continue
                else:
                    break

            # 检查是否存在src子目录
            src_path = os.path.join(current_path, 'src')
            if os.path.exists(src_path) and os.path.isdir(src_path):
                return current_path

            # 向上一级目录
            parent_path = os.path.dirname(current_path)
            if parent_path == current_path:
                break
            current_path = parent_path

        return None