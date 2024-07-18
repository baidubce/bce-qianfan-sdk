#!/usr/bin/env python3
# coding=utf-8
"""
utils
"""

import socket
import time


def is_port_in_use(host: str, port: int) -> bool:
    """
    判断port是否被占用
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            s.close()
            return False
        except OSError:
            return True


def select_a_free_port(
    host: str = "127.0.0.1", start_port: int = 8000, end_port: int = 65535
) -> int:
    """
    选择一个空闲的端口
    """
    for i in range(start_port, end_port + 1):
        if not is_port_in_use(host, i):
            return i
    raise RuntimeError(
        "{startPort}-{endPort}没有空闲端口可用".format(
            startPort=str(start_port), endPort=str(end_port)
        )
    )


def strftime(timestamp: float, time_format: str = "%Y-%m-%dT%H:%M:%SZ") -> str:
    """
    timestamp -> string like "2022-04-01T08:40:45Z"
    """
    return time.strftime(time_format, time.localtime(timestamp))
