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

"""
Utils for console api
"""
import copy
import functools
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

from qianfan import get_config
from qianfan.consts import Consts
from qianfan.errors import InvalidArgumentError
from qianfan.resources.requestor.console_requestor import ConsoleAPIRequestor
from qianfan.resources.typing import ParamSpec, QfRequest, QfResponse, RetryConfig
from qianfan.version import VERSION

P = ParamSpec("P")


def console_api_request(func: Callable[P, QfRequest]) -> Callable[P, QfResponse]:
    """
    wrapper for all functions in sdk for console api, so that the function
    only needs to provide the request
    this decorator will:
    1. extract ak and sk from kwargs
    2. extract retry config from kwargs
    3. use the requestor to send request
    4. return the response to the user
    """

    @functools.wraps(func)
    def inner(*args: Any, **kwargs: Any) -> QfResponse:
        """
        inner function of wrapper
        """
        ak, sk = _get_console_ak_sk(**kwargs)
        config = get_config()
        retry_config = RetryConfig(
            retry_count=kwargs.pop("retry_count", config.CONSOLE_API_RETRY_COUNT),
            timeout=kwargs.pop("request_timeout", config.CONSOLE_API_RETRY_TIMEOUT),
            backoff_factor=kwargs.pop(
                "backoff_factor", config.CONSOLE_API_RETRY_BACKOFF_FACTOR
            ),
            jitter=kwargs.pop("retry_jitter", config.CONSOLE_API_RETRY_JITTER),
            retry_err_codes=kwargs.pop(
                "retry_err_codes", config.CONSOLE_API_RETRY_ERR_CODES
            ),
            max_wait_interval=kwargs.pop(
                "max_wait_interval", config.CONSOLE_API_RETRY_MAX_WAIT_INTERVAL
            ),
        )
        req = func(*args, **kwargs)
        req.headers["request-source"] = f"qianfan_py_sdk_v{VERSION}"
        return ConsoleAPIRequestor(**kwargs)._request_console_api(
            req, ak, sk, retry_config
        )

    return inner


def async_console_api_request(
    func: Callable[P, Awaitable[QfRequest]]
) -> Callable[P, Awaitable[QfResponse]]:
    """
    wrapper for all functions in sdk for console api, so that the function
    only needs to provide the request
    this decorator will:
    1. extract ak and sk from kwargs
    2. extract retry config from kwargs
    3. use the requestor to send request
    4. return the response to the user
    """

    @functools.wraps(func)
    async def inner(*args: Any, **kwargs: Any) -> QfResponse:
        """
        inner function of wrapper
        """
        ak, sk = _get_console_ak_sk(**kwargs)
        config = get_config()
        retry_config = RetryConfig(
            retry_count=kwargs.get("retry_count", config.CONSOLE_API_RETRY_COUNT),
            timeout=kwargs.get("request_timeout", config.CONSOLE_API_RETRY_TIMEOUT),
            backoff_factor=kwargs.get(
                "backoff_factor", config.CONSOLE_API_RETRY_BACKOFF_FACTOR
            ),
            jitter=kwargs.get("retry_jitter", config.CONSOLE_API_RETRY_JITTER),
            retry_err_codes=kwargs.get(
                "retry_err_codes", config.CONSOLE_API_RETRY_ERR_CODES
            ),
        )
        req = await func(*args, **kwargs)
        req.headers["request-source"] = f"qianfan_py_sdk_v{VERSION}"
        return await ConsoleAPIRequestor(**kwargs)._async_request_console_api(
            req, ak, sk, retry_config
        )

    return inner


def _get_console_v2_query(
    action: Optional[str] = None, query: Dict[str, Any] = {}
) -> Dict[str, Any]:
    res = copy.deepcopy(query)
    if action is not None:
        res[Consts.ConsoleAPIQueryAction] = action
    return res


def _get_console_ak_sk(pop: bool = True, **kwargs: Any) -> Tuple[str, str]:
    """
    extract ak and sk from kwargs
    if not found in kwargs, will return value from global config and env variable
    if `pop` is True, remove ak and sk from kwargs
    """
    ak = kwargs.get("ak", None) or get_config().ACCESS_KEY
    sk = kwargs.get("sk", None) or get_config().SECRET_KEY
    if ak is None or sk is None:
        raise InvalidArgumentError("access_key and secret_key must be provided")
    if pop:
        # remove ak and sk from kwargs
        for key in ("ak", "sk"):
            if key in kwargs:
                del kwargs[key]
    return ak, sk
