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
Utils for qianfan api
"""
import functools
from typing import Any, Awaitable, Callable

from qianfan import get_config
from qianfan.resources.auth.oauth import Auth
from qianfan.resources.requestor.openapi_requestor import QfAPIRequestor
from qianfan.resources.typing import ParamSpec, QfRequest, QfResponse, RetryConfig

P = ParamSpec("P")


def qianfan_api_request(func: Callable[P, QfRequest]) -> Callable[P, QfResponse]:
    """
    wrapper for all functions in sdk for qianfan api, so that the function
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
        auth = Auth(**kwargs)
        config = get_config()
        retry_config = RetryConfig(
            retry_count=kwargs.get("retry_count", config.LLM_API_RETRY_COUNT),
            timeout=kwargs.get("request_timeout", config.LLM_API_RETRY_TIMEOUT),
            backoff_factor=kwargs.get(
                "backoff_factor", config.LLM_API_RETRY_BACKOFF_FACTOR
            ),
            jitter=kwargs.get("jitter", config.LLM_API_RETRY_JITTER),
            max_wait_interval=kwargs.get(
                "max_wait_interval", config.LLM_API_RETRY_MAX_WAIT_INTERVAL
            ),
        )
        req = func(*args, **kwargs)
        req.retry_config = retry_config
        return QfAPIRequestor(**kwargs)._request_api(req, auth)

    return inner


def async_qianfan_api_request(
    func: Callable[P, Awaitable[QfRequest]]
) -> Callable[P, Awaitable[QfResponse]]:
    """
    wrapper for all functions in sdk for qianfan api, so that the function
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
        auth = Auth(**kwargs)
        config = get_config()
        retry_config = RetryConfig(
            retry_count=kwargs.get("retry_count", config.LLM_API_RETRY_COUNT),
            timeout=kwargs.get("request_timeout", config.LLM_API_RETRY_TIMEOUT),
            backoff_factor=kwargs.get(
                "backoff_factor", config.LLM_API_RETRY_BACKOFF_FACTOR
            ),
            jitter=kwargs.get("jitter", config.LLM_API_RETRY_JITTER),
            max_wait_interval=kwargs.get(
                "max_wait_interval", config.LLM_API_RETRY_MAX_WAIT_INTERVAL
            ),
        )
        req = await func(*args, **kwargs)
        req.retry_config = retry_config
        return await QfAPIRequestor(**kwargs)._async_request_api(req, auth)

    return inner
