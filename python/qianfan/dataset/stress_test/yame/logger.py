#!/usr/bin/env python3
# coding=utf-8
"""
yame logger
"""

import logging
import logging.config
import logging.handlers
import socket
from logging import Filter
from typing import Any, Dict

HOSTNAME = socket.gethostname()
loglevel = "DEBUG"
console_logger_name = "yame.stats"
runner_logger_name = "yame.runner"


class LogFilterByLevel(Filter):
    """log filter by loglevel"""

    def __init__(self, levelname: str, name: str = ""):
        super().__init__(name)
        self.levelname = levelname.upper()

    def filter(self, record: Any) -> bool:
        """filter record by loglevel"""
        return record.levelname == self.levelname


LOGGING_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "debug": {"()": LogFilterByLevel, "levelname": "DEBUG"},
        "info": {"()": LogFilterByLevel, "levelname": "INFO"},
        "warning": {"()": LogFilterByLevel, "levelname": "WARNING"},
        "error": {"()": LogFilterByLevel, "levelname": "ERROR"},
        "critical": {"()": LogFilterByLevel, "levelname": "CRITICAL"},
    },
    "formatters": {
        "debug": {"format": "\033[0;36m%(message)s\033[0m"},
        "info": {"format": "[%(asctime)s] \033[0;32m[INFO] %(message)s\033[0m"},
        "warning": {"format": "[%(asctime)s] \033[0;33m[NOTICE] %(message)s\033[0m"},
        "error": {"format": "[%(asctime)s] \033[0;31m[ERROR] %(message)s\033[0m"},
        "default": {
            "format": f"[%(asctime)s] {HOSTNAME}/%(levelname)s/%(name)s: %(message)s",
        },
        "plain": {"format": "%(message)s"},
    },
    "handlers": {
        "debug": {
            "class": "logging.StreamHandler",
            "formatter": "debug",
            "filters": ["debug"],
        },
        "info": {
            "class": "logging.StreamHandler",
            "formatter": "info",
            "filters": ["info"],
        },
        "warning": {
            "class": "logging.StreamHandler",
            "formatter": "warning",
            "filters": ["warning"],
        },
        "error": {
            "class": "logging.StreamHandler",
            "formatter": "error",
            "filters": ["error"],
        },
    },
    "loggers": {
        console_logger_name: {
            "handlers": ["debug", "info", "warning", "error"],
            "level": loglevel,
            "propagate": False,
        },
        runner_logger_name: {
            "handlers": ["debug", "info", "warning", "error"],
            "level": loglevel,
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(runner_logger_name)
console_logger = logging.getLogger(console_logger_name)


def set_filehandler(logfile: str) -> None:
    """set file handler of 'yame.runner' logger"""
    LOGGING_CONFIG["handlers"]["file"] = {
        "class": "logging.FileHandler",
        "filename": logfile,
        "formatter": "default",
    }
    LOGGING_CONFIG["loggers"][runner_logger_name]["handlers"].append("file")
    logging.config.dictConfig(LOGGING_CONFIG)
