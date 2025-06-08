#!/usr/bin/env python3
# collect_py.py
from __future__ import annotations

"""
脚本功能：
1. 将 src 目录下所有 .py、.cmd、.ini、.yaml 文件合并到根目录下的 所有的源代码.txt，
   并在每个文件内容前添加注释标明源文件相对路径。
2. 将 test 或 tests 目录下所有 .py、.cmd、.ini、.yaml 文件合并到根目录下的 所有的测试用例.txt，
   并在每个文件内容前添加注释标明源文件相对路径。
3. 将根目录下的配置文件和其他文件合并到根目录下的 根目录配置文件.txt，
   包括 .py、.toml、.cfg、.ini、.cmd、.yaml 文件（排除 collect.py，不搜索子文件夹）。
4. 输出前删除已存在的输出文件。
5. 读取 .gitignore 文件，在收集文件时排除匹配 gitignore 规则的文件。

用法：在项目根目录下执行 `python collect.py`
"""

import os
import fnmatch
from typing import List, Set


def load_gitignore_patterns(gitignore_path: str) -> Set[str]:
    """
    读取 .gitignore 文件并返回忽略模式集合。

    Args:
        gitignore_path: .gitignore 文件路径

    Returns:
        忽略模式集合
    """
    patterns = set()

    if not os.path.exists(gitignore_path):
        return patterns

    with open(gitignore_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释行
            if line and not line.startswith('#'):
                patterns.add(line)

    return patterns


def is_ignored_by_gitignore(file_path: str, gitignore_patterns: Set[str]) -> bool:
    """
    检查文件路径是否匹配 gitignore 规则。

    Args:
        file_path: 文件相对路径
        gitignore_patterns: gitignore 模式集合

    Returns:
        如果文件应被忽略则返回 True，否则返回 False
    """
    # 标准化路径分隔符为正斜杠
    normalized_path = file_path.replace(os.sep, '/')

    for pattern in gitignore_patterns:
        # 处理目录模式（以/结尾）
        if pattern.endswith('/'):
            pattern_no_slash = pattern.rstrip('/')
            if fnmatch.fnmatch(normalized_path, pattern_no_slash + '/*') or normalized_path == pattern_no_slash:
                return True
        else:
            # 处理文件模式
            if fnmatch.fnmatch(normalized_path, pattern):
                return True
            # 也检查文件名部分
            filename = os.path.basename(normalized_path)
            if fnmatch.fnmatch(filename, pattern):
                return True
            # 检查路径中的任何部分是否匹配模式
            path_parts = normalized_path.split('/')
            for part in path_parts:
                if fnmatch.fnmatch(part, pattern):
                    return True

    return False


def collect_files_recursive(
        source_dir: str,
        output_file: str,
        exts: List[str],
        gitignore_patterns: Set[str]
) -> None:
    """
    递归收集 source_dir 下所有指定扩展名文件内容并追加写入 output_file，
    每个文件前添加注释说明源文件路径，同时排除 gitignore 规则匹配的文件。

    Args:
        source_dir: 源目录路径
        output_file: 输出文件路径
        exts: 文件扩展名列表
        gitignore_patterns: gitignore 模式集合
    """
    with open(output_file, 'a', encoding='utf-8') as fout:
        for root, _, files in os.walk(source_dir):
            for fname in sorted(files):
                if any(fname.endswith(ext) for ext in exts):
                    full_path = os.path.join(root, fname)
                    rel_path = os.path.relpath(full_path, os.getcwd())

                    # 检查是否被 gitignore 规则排除
                    if is_ignored_by_gitignore(rel_path, gitignore_patterns):
                        continue

                    fout.write(f"# ======= 源文件: {rel_path} =======\n")
                    try:
                        with open(full_path, 'r', encoding='utf-8') as fin:
                            fout.write(fin.read())
                    except UnicodeDecodeError:
                        # 如果UTF-8解码失败，尝试其他编码
                        try:
                            with open(full_path, 'r', encoding='gbk') as fin:
                                fout.write(fin.read())
                        except UnicodeDecodeError:
                            fout.write(f"[无法读取文件内容 - 编码问题]\n")
                    fout.write("\n\n")
    return


def collect_root_files(
        output_file: str,
        exts: List[str],
        exclude_files: List[str],
        gitignore_patterns: Set[str]
) -> None:
    """
    收集根目录下指定扩展名的文件内容并追加写入 output_file（不递归搜索子文件夹），
    每个文件前添加注释说明源文件路径，同时排除 gitignore 规则匹配的文件。

    Args:
        output_file: 输出文件路径
        exts: 文件扩展名列表
        exclude_files: 要排除的文件名列表
        gitignore_patterns: gitignore 模式集合
    """
    root_dir = os.getcwd()

    with open(output_file, 'a', encoding='utf-8') as fout:
        # 只获取根目录下的文件，不递归
        files = []
        for item in os.listdir(root_dir):
            item_path = os.path.join(root_dir, item)
            if os.path.isfile(item_path):
                files.append(item)

        # 过滤并排序文件
        filtered_files = []
        for fname in sorted(files):
            # 检查文件扩展名
            if any(fname.endswith(ext) for ext in exts):
                # 检查是否在排除列表中
                if fname not in exclude_files:
                    # 检查是否被 gitignore 规则排除
                    if not is_ignored_by_gitignore(fname, gitignore_patterns):
                        filtered_files.append(fname)

        # 写入文件内容
        for fname in filtered_files:
            full_path = os.path.join(root_dir, fname)
            rel_path = os.path.relpath(full_path, root_dir)
            fout.write(f"# ======= 源文件: {rel_path} =======\n")

            try:
                with open(full_path, 'r', encoding='utf-8') as fin:
                    fout.write(fin.read())
            except UnicodeDecodeError:
                # 如果UTF-8解码失败，尝试其他编码
                try:
                    with open(full_path, 'r', encoding='gbk') as fin:
                        fout.write(fin.read())
                except UnicodeDecodeError:
                    fout.write(f"[无法读取文件内容 - 编码问题]\n")

            fout.write("\n\n")
    return


if __name__ == "__main__":
    # 定义输出文件名
    output_src = "所有的源代码.txt"
    output_test = "所有的测试用例.txt"
    output_root = "根目录配置文件.txt"
    output_docs = '所有的文档.txt'

    # 需要合并的文件扩展名列表
    common_exts = ['.py', '.ini', '.yaml', '.yml', '.md']
    root_exts = ['.py', '.toml', '.cfg', '.ini', '.cmd', '.yaml', '.yml']

    # 要排除的根目录文件
    exclude_files = ['collect.py']

    # 加载 gitignore 规则
    gitignore_patterns = load_gitignore_patterns('.gitignore')
    if gitignore_patterns:
        print(f"已加载 {len(gitignore_patterns)} 条 gitignore 规则")

    # 删除已存在的输出文件
    for f in (output_src, output_test, output_root):
        if os.path.exists(f):
            os.remove(f)
            print(f"已删除已存在文件：{f}")

    # 定义输入输出目录映射（递归搜索）
    recursive_mappings = [
        (['src'], output_src),
        (['test', 'tests'], output_test),
        (['docs'], output_docs),
    ]

    # 处理递归搜索的目录
    for src_dirs, out_file in recursive_mappings:
        found = False
        for src_dir in src_dirs:
            if os.path.isdir(src_dir):
                found = True
                print(f"正在处理目录 `{src_dir}/` → 输出文件 `{out_file}`")
                collect_files_recursive(src_dir, out_file, common_exts, gitignore_patterns)
        if not found:
            dirs = ' 或 '.join([f"`{d}/`" for d in src_dirs])
            print(f"警告：目录 {dirs} 不存在，跳过。")

    # 处理根目录文件
    print(f"正在处理根目录文件 → 输出文件 `{output_root}`")
    collect_root_files(output_root, root_exts, exclude_files, gitignore_patterns)

    print("文件收集完成！")
