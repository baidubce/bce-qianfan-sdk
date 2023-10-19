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
from typing import Any, Callable

from qianfan.consts import DefaultValue
from qianfan.resources.api_requestor import ConsoleAPIRequestor
from qianfan.resources.typing import ParamSpec, QfRequest, QfResponse, RetryConfig
from qianfan.utils import _get_console_ak_sk

# requestor for console api
_requestor = ConsoleAPIRequestor()

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
        retry_config = RetryConfig(
            retry_count=kwargs.get("retry_count", DefaultValue.RetryCount),
            timeout=kwargs.get("request_timeout", DefaultValue.RetryTimeout),
            backoff_factor=kwargs.get(
                "backoff_factor", DefaultValue.RetryBackoffFactor
            ),
        )
        req = func(*args, **kwargs)
        return _requestor._request_console_api(req, ak, sk, retry_config)

    return inner
