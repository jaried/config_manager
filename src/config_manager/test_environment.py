# src/config_manager/test_environment.py
from __future__ import annotations
from datetime import datetime, timedelta

import os
import tempfile
import shutil


class TestEnvironmentManager:
    """测试环境管理器"""

    @staticmethod
    def cleanup_old_test_environments(days_old: int = 7) -> int:
        """
        清理旧的测试环境

        Args:
            days_old: 清理多少天前的测试环境

        Returns:
            清理的目录数量
        """
        temp_base = tempfile.gettempdir()
        tests_dir = os.path.join(temp_base, 'tests')

        if not os.path.exists(tests_dir):
            return 0

        cutoff_time = datetime.now() - timedelta(days=days_old)
        cleaned_count = 0

        try:
            for date_dir in os.listdir(tests_dir):
                date_path = os.path.join(tests_dir, date_dir)
                if os.path.isdir(date_path):
                    try:
                        # 解析日期
                        dir_date = datetime.strptime(date_dir, '%Y%m%d')
                        if dir_date < cutoff_time:
                            shutil.rmtree(date_path)
                            print(f"✓ 已清理旧测试环境: {date_path}")
                            cleaned_count += 1
                    except (ValueError, OSError) as e:
                        print(f"⚠️  清理测试环境失败 {date_path}: {e}")
                        continue
        except OSError as e:
            print(f"⚠️  访问测试目录失败 {tests_dir}: {e}")

        return cleaned_count

    @staticmethod
    def get_test_environment_info() -> dict:
        """
        获取当前测试环境信息

        Returns:
            包含测试环境信息的字典
        """
        info = {
            'is_test_mode': os.environ.get('CONFIG_MANAGER_TEST_MODE') == 'true',
            'test_base_dir': os.environ.get('CONFIG_MANAGER_TEST_BASE_DIR'),
            'temp_base': tempfile.gettempdir(),
            'tests_dir': os.path.join(tempfile.gettempdir(), 'tests')
        }

        # 检查测试目录是否存在
        if info['tests_dir']:
            info['tests_dir_exists'] = os.path.exists(info['tests_dir'])
            if info['tests_dir_exists']:
                try:
                    info['test_environments_count'] = len([
                        d for d in os.listdir(info['tests_dir'])
                        if os.path.isdir(os.path.join(info['tests_dir'], d))
                    ])
                except OSError:
                    info['test_environments_count'] = 0
            else:
                info['test_environments_count'] = 0

        return info

    @staticmethod
    def cleanup_current_test_environment():
        """清理当前测试环境"""
        test_base_dir = os.environ.get('CONFIG_MANAGER_TEST_BASE_DIR')
        if test_base_dir and os.path.exists(test_base_dir):
            try:
                shutil.rmtree(test_base_dir)
                print(f"✓ 已清理当前测试环境: {test_base_dir}")

                # 清理环境变量
                if 'CONFIG_MANAGER_TEST_MODE' in os.environ:
                    del os.environ['CONFIG_MANAGER_TEST_MODE']
                if 'CONFIG_MANAGER_TEST_BASE_DIR' in os.environ:
                    del os.environ['CONFIG_MANAGER_TEST_BASE_DIR']

                return True
            except OSError as e:
                print(f"⚠️  清理当前测试环境失败: {e}")
                return False
        return False

    @staticmethod
    def list_test_environments() -> list[dict]:
        """
        列出所有测试环境

        Returns:
            测试环境信息列表
        """
        temp_base = tempfile.gettempdir()
        tests_dir = os.path.join(temp_base, 'tests')
        environments = []

        if not os.path.exists(tests_dir):
            return environments

        try:
            for date_dir in os.listdir(tests_dir):
                date_path = os.path.join(tests_dir, date_dir)
                if os.path.isdir(date_path):
                    try:
                        # 解析日期
                        dir_date = datetime.strptime(date_dir, '%Y%m%d')

                        # 统计时间目录
                        time_dirs = []
                        for time_dir in os.listdir(date_path):
                            time_path = os.path.join(date_path, time_dir)
                            if os.path.isdir(time_path):
                                time_dirs.append({
                                    'time': time_dir,
                                    'path': time_path,
                                    'size': TestEnvironmentManager._get_dir_size(time_path)
                                })

                        environments.append({
                            'date': date_dir,
                            'date_parsed': dir_date,
                            'path': date_path,
                            'time_environments': time_dirs,
                            'total_size': sum(env['size'] for env in time_dirs)
                        })
                    except (ValueError, OSError):
                        continue
        except OSError:
            pass

        # 按日期排序
        environments.sort(key=lambda x: x['date_parsed'], reverse=True)
        return environments

    @staticmethod
    def _get_dir_size(path: str) -> int:
        """获取目录大小（字节）"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        continue
        except OSError:
            pass
        return total_size

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f} {size_names[i]}" 