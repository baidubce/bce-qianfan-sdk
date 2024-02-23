# Copyright (c) 2023 Baidu, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""utils for logging
"""
import logging
import sys
from functools import partial
from typing import Any, Union

TRACE_LEVEL = 5

logging.addLevelName(TRACE_LEVEL, "TRACE")


class Logger(object):
    _DEFAULT_MSG_FORMAT = (
        "[%(levelname)s] [%(asctime)s] %(filename)s:%(lineno)d [t:%(thread)d]:"
        " %(message)s"
    )
    _DEFAULT_DATE_FORMAT = "%m-%d %H:%M:%S"

    def __init__(
        self,
        name: str = "qianfan",
        format: str = _DEFAULT_MSG_FORMAT,
        datefmt: str = _DEFAULT_DATE_FORMAT,
    ) -> None:
        """
        Args:
            - name (str): name of logger, default "qianfan".
            - format (str): log message format, default `_DEFAULT_MSG_FORMAT`
            - datefmt (str): time format, default `_DEFAULT_DATE_FORMAT`

        Returns:
            None
        """
        # 创建一个loggger
        self.__name = name
        self._logger = logging.getLogger(self.__name)
        self._logger.setLevel(logging.INFO)
        self.formatter = logging.Formatter(format, datefmt)
        self.handler = logging.StreamHandler()
        self.handler.setFormatter(self.formatter)
        self._logger.addHandler(self.handler)

    def format(self) -> logging.Formatter:
        return self.formatter

    def info(self, message: object, *args: object, **params: Any) -> None:
        """
        INFO level log

        Args:
            message (object): message content

        Returns:
            None

        """
        return self._logger.info(message, *args, **params)

    def debug(self, message: object, *args: object, **params: Any) -> None:
        """
        DEBUG level log

        Args:
            message (object): message content

        Returns:
            None
        """
        self._logger.debug(message, *args, **params)

    def error(self, message: object, *args: object, **params: Any) -> None:
        """
        ERROR level log

        Args:
            message (object): message content

        Returns:
            None
        """
        self._logger.error(message, *args, **params)

    def warn(self, message: object, *args: object, **params: Any) -> None:
        """
        WARN level log

        Args:
            message (object): message content

        Returns:
            None

        """
        self._logger.warning(message, *args, **params)

    def trace(self, message: object, *args: object, **params: Any) -> None:
        """
        TRACE level log
        Args:
            message (object): message content
        Returns:
            None
        """
        self._logger.log(TRACE_LEVEL, message, *args, **params)


logger = Logger()

# only Python 3.8+ support stacklevel
if sys.version_info < (3, 8):
    log_info = logger.info
    log_debug = logger.debug
    log_error = logger.error
    log_warn = logger.warn
    log_trace = logger.trace
else:
    log_info = partial(logger.info, stacklevel=2)
    log_debug = partial(logger.debug, stacklevel=2)
    log_error = partial(logger.error, stacklevel=2)
    log_warn = partial(logger.warn, stacklevel=2)
    log_trace = partial(logger.trace, stacklevel=2)


def redirect_log_to_file(file_path: str) -> None:
    """
    redirect log to file with same formatter

    Args:
        file_path (str): local file path
    """
    logger._logger.removeHandler(logger.handler)
    file_handler = logging.FileHandler(file_path)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logger.formatter)
    logger._logger.addHandler(file_handler)


def enable_log(log_level: Union[int, str] = logging.INFO) -> None:
    """
    Set the logging level for the qianfan sdk.

    This function allows you to configure the logging level for the sdk's logging
    system. The logging level determines the verbosity of log messages that will
    be recorded. By default, it is set to 'WARN', which logs only important information.

    Parameters:
      log_level (int, optional):
        The logging level to set for the application. It controls the granularity
        of log messages. You can specify one of the following integer values or str like
        "INFO":

        - logging.CRITICAL (50): Logs only critical messages.
        - logging.ERROR (40): Logs error and critical messages.
        - logging.WARNING (30): Logs warnings, errors, and critical messages.
        - logging.INFO (20): Logs general information, warnings, errors, and critical
          messages.
        - logging.DEBUG (10): Logs detailed debugging information, in addition to all
          the above log levels.

    Example Usage:
    To enable detailed debugging, you can call the function like this:
    enable_log(logging.DEBUG)

    To set the logging level to only log errors and critical messages, use:
    enable_log("ERROR")
    """
    logger._logger.setLevel(log_level)


def disable_log() -> None:
    """
    Disables logging.

    This function turns off the logging feature, preventing the recording of log
    messages.

    Parameters:
      None
    """
    enable_log(logging.CRITICAL)
