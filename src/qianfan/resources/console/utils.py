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
import functools
from typing import Any, Awaitable, Callable

from qianfan import get_config
from qianfan.resources.requestor.console_requestor import ConsoleAPIRequestor
from qianfan.resources.typing import ParamSpec, QfRequest, QfResponse, RetryConfig
from qianfan.utils import _get_console_ak_sk

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
            retry_count=kwargs.get("retry_count", config.CONSOLE_API_RETRY_COUNT),
            timeout=kwargs.get("request_timeout", config.CONSOLE_API_RETRY_TIMEOUT),
            backoff_factor=kwargs.get(
                "backoff_factor", config.CONSOLE_API_RETRY_BACKOFF_FACTOR
            ),
        )
        req = func(*args, **kwargs)
        return ConsoleAPIRequestor()._request_console_api(req, ak, sk, retry_config)

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
        )
        req = await func(*args, **kwargs)
        return ConsoleAPIRequestor()._request_console_api(req, ak, sk, retry_config)

    return inner
