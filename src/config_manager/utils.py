# src/config_manager/utils.py
from __future__ import annotations
from datetime import datetime
start_time = datetime.now()

import os
import sys
from typing import Iterable, Any, List

# 修改锁文件函数的实现
if sys.platform == 'win32':
    import msvcrt
    def lock_file(f):
        file_handle = msvcrt.get_osfhandle(f.fileno())
        msvcrt.locking(file_handle, msvcrt.LK_NBLCK, 1)
        return
    def unlock_file(f):
        file_handle = msvcrt.get_osfhandle(f.fileno())
        msvcrt.locking(file_handle, msvcrt.LK_UNLCK, 1)
        return
else:
    import fcntl  # 只在非Windows系统导入fcntl
    def lock_file(f):
        fcntl.flock(f, fcntl.LOCK_EX)
        return
    def unlock_file(f):
        fcntl.flock(f, fcntl.LOCK_UN)
        return

def unique_list_order_preserved(seq: Iterable) -> List[Any]:
    """返回保持原始顺序的唯一元素列表"""
    seen = set()
    seen_add = seen.add
    result = [x for x in seq if not (x in seen or seen_add(x))]
    return result