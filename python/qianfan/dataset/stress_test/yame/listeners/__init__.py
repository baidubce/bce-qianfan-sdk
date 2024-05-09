"""
yame plugins
"""
from typing import Any

from locust import events

from qianfan.dataset.stress_test.yame.listeners.custom_handler import CustomHandler
from qianfan.dataset.stress_test.yame.logger import set_filehandler

__all__ = ["CustomHandler"]


@events.init.add_listener
def init_all_listeners(environment: Any, **kwargs: Any) -> None:
    """
    注册所有listeners
    """
    # set file handler of 'yame' logger
    if environment.parsed_options.logfile:
        set_filehandler(environment.parsed_options.logfile)
