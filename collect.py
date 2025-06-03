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

用法：在项目根目录下执行 `python collect.py`
"""

import os
from typing import List


def collect_files_recursive(source_dir: str, output_file: str, exts: List[str]) -> None:
    """
    递归收集 source_dir 下所有指定扩展名文件内容并追加写入 output_file，
    每个文件前添加注释说明源文件路径。

    Args:
        source_dir: 源目录路径
        output_file: 输出文件路径
        exts: 文件扩展名列表
    """
    with open(output_file, 'a', encoding='utf-8') as fout:
        for root, _, files in os.walk(source_dir):
            for fname in sorted(files):
                if any(fname.endswith(ext) for ext in exts):
                    full_path = os.path.join(root, fname)
                    rel_path = os.path.relpath(full_path, os.getcwd())
                    fout.write(f"# ======= 源文件: {rel_path} =======\n")
                    with open(full_path, 'r', encoding='utf-8') as fin:
                        fout.write(fin.read())
                    fout.write("\n\n")
    return


def collect_root_files(output_file: str, exts: List[str], exclude_files: List[str]) -> None:
    """
    收集根目录下指定扩展名的文件内容并追加写入 output_file（不递归搜索子文件夹），
    每个文件前添加注释说明源文件路径。

    Args:
        output_file: 输出文件路径
        exts: 文件扩展名列表
        exclude_files: 要排除的文件名列表
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

    # 需要合并的文件扩展名列表
    common_exts = ['.py', '.ini', '.yaml', '.yml']
    root_exts = ['.py', '.toml', '.cfg', '.ini', '.cmd', '.yaml', '.yml']

    # 要排除的根目录文件
    exclude_files = ['collect.py']

    # 删除已存在的输出文件
    for f in (output_src, output_test, output_root):
        if os.path.exists(f):
            os.remove(f)
            print(f"已删除已存在文件：{f}")

    # 定义输入输出目录映射（递归搜索）
    recursive_mappings = [
        (['src'], output_src),
        (['test', 'tests'], output_test),
    ]

    # 处理递归搜索的目录
    for src_dirs, out_file in recursive_mappings:
        found = False
        for src_dir in src_dirs:
            if os.path.isdir(src_dir):
                found = True
                print(f"正在处理目录 `{src_dir}/` → 输出文件 `{out_file}`")
                collect_files_recursive(src_dir, out_file, common_exts)
        if not found:
            dirs = ' 或 '.join([f"`{d}/`" for d in src_dirs])
            print(f"警告：目录 {dirs} 不存在，跳过。")

    # 处理根目录文件
    print(f"正在处理根目录文件 → 输出文件 `{output_root}`")
    collect_root_files(output_root, root_exts, exclude_files)

    print("文件收集完成！")