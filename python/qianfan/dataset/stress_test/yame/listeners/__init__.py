"""
yame plugins
"""

from locust import events
from qianfan.dataset.stress_test.yame.listeners.custom_handler import CustomHandler
from qianfan.dataset.stress_test.yame.logger import set_filehandler


@events.init.add_listener
def init_all_listeners(environment, **kwargs):
    """
    注册所有listeners
    """
    # set file handler of 'yame' logger
    if environment.parsed_options.logfile:
        set_filehandler(environment.parsed_options.logfile)
