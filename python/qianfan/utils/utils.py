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

import asyncio
import importlib.util
import os
import re
import secrets
import string
import threading
import uuid as uuid_lib
from threading import current_thread
from types import TracebackType
from typing import Dict, List, Optional, Type

from qianfan.errors import InvalidArgumentError
from qianfan.utils import log_info

thread_local = threading.local()


def _get_value_from_dict_or_var_or_env(
    dictionary: Dict, key: str, value: Optional[str], env_key: str
) -> Optional[str]:
    """
    Attempt to retrieve a value from the `dictionary` using the `key`.
    If the `key` is not found, try to obtain a value from the environment variable
    using `env_key`.
    If still not found, return None

    Args:
        dictionary (Dict): the dict to search
        key (str): the key of the value in dictionary
        env_key (str): the name of the environment variable

    Returns:
        the value of key, or None if not found
    """
    if key in dictionary:
        return dictionary[key]
    if value is not None:
        return value
    env_value = os.environ.get(env_key)
    return env_value


def _set_val_if_key_exists(src: dict, dst: dict, key: str) -> None:
    """
    if `key` is in `src` dict, set the value of `key` in dst with src[key]

    Args:
        src (Dict): the source dict
        dst (Dict): the destination dict
        key (str): the key to be found in src dict

    Returns:
        None
    """
    if key in src:
        dst[key] = src[key]


def _get_from_env_or_default(env_name: str, default_value: str) -> str:
    """
    Get value from environment variable or return default value

    Args:
        env_name (str): the name of the environment variable
        default_value: the default value if the env var does not exist

    Return:
        str, the value of the environment variable or default_value
    """
    env_value = os.environ.get(env_name)
    if env_value is None:
        return default_value
    return env_value


def _strtobool(val: str) -> bool:
    """
    convert string to bool
    """
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise InvalidArgumentError(f"invalid boolean value `{val}")


def _none_if_empty(val: str) -> Optional[str]:
    """
    convert string to None if it is empty or "None"
    """
    if val == "" or val.lower() == "none":
        return None
    return val


class AsyncLock:
    """
    wrapper of asyncio.Lock
    """

    def __init__(self) -> None:
        self._lock = None
        try:
            self._lock = asyncio.Lock()
        except RuntimeError:
            event_loop_checked = getattr(thread_local, "event_loop_checked", None)
            # only log once for each thread
            if event_loop_checked is None:
                log_info(
                    f"no event loop in thread `{current_thread().name}`, async feature"
                    " won't be available. Please make sure the object is initialized"
                    " in the thread with event loop."
                )
                thread_local.event_loop_checked = True

    async def __aenter__(self) -> None:
        if self._lock is None:
            raise InvalidArgumentError(
                "no event loop found in current thread, please make sure the event loop"
                " is available when the object is initialized"
            )
        await self._lock.__aenter__()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self._lock is None:
            raise InvalidArgumentError(
                "no event loop found in current thread, please make sure the event loop"
                " is available when the object is initialized"
            )
        await self._lock.__aexit__(exc_type, exc_val, exc_tb)


def uuid() -> str:
    return str(uuid_lib.uuid4()).replace("-", "")


def generate_letter_num_random_id(len: int = 10) -> str:
    return "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(len)
    )


def assert_package_installed(package_name: str) -> None:
    if not check_package_installed(package_name):
        raise ImportError(
            f"Unable to import {package_name} package, "
            f"please install it using 'pip install {package_name}'."
        )


def check_package_installed(package_name: str) -> bool:
    return importlib.util.find_spec(package_name) is not None


def camel_to_snake(name: str) -> str:
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def snake_to_camel(name: str) -> str:
    return "".join([x.capitalize() for x in name.split("_")])


def first_lower_case(name: str) -> str:
    return name[:1].lower() + name[1:]


def remove_suffix(name: str, suffix: str) -> str:
    if name.endswith(suffix):
        return name[: -len(suffix)]
    return name


def remove_suffix_list(name: str, suffix_list: List[str]) -> str:
    for suffix in suffix_list:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name
