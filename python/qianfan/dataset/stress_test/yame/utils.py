#!/usr/bin/env python3
# coding=utf-8
"""
utils
"""

import socket
import time


def is_port_in_use(host, port):
    """
    判断port是否被占用
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def select_a_free_port(host="127.0.0.1", start_port=8000, end_port=65535):
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


def strftime(timestamp, time_format="%Y-%m-%dT%H:%M:%SZ"):
    """
    timestamp -> string like "2022-04-01T08:40:45Z"
    """
    return time.strftime(time_format, time.localtime(timestamp))
