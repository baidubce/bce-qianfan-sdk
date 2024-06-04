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
Console API Requestor
"""
from copy import deepcopy
from typing import Any, AsyncIterator, Dict, Iterator, Tuple, Union
from urllib.parse import urlparse

import qianfan.errors as errors
from qianfan import get_config
from qianfan.errors import InvalidArgumentError
from qianfan.resources.auth.iam import iam_sign
from qianfan.resources.requestor.base import (
    BaseAPIRequestor,
)
from qianfan.resources.typing import QfRequest, QfResponse, RetryConfig
from qianfan.utils.logging import log_error


class ConsoleAPIRequestor(BaseAPIRequestor):
    """
    object to manage console API requests
    """

    def _check_error(self, body: Dict[str, Any]) -> None:
        """
        check whether error_code is in the response body
        """
        if "error_code" in body:
            req_id = body.get("log_id", "")
            error_code = body["error_code"]
            err_msg = body.get("error_msg", "no error message found in response body")
            log_error(
                f"console api request req_id: {req_id} failed with error code:"
                f" {error_code}, err msg: {err_msg}, please check the api doc"
            )
            raise errors.APIError(error_code, err_msg, req_id)

    def _request_console_api(
        self, req: QfRequest, ak: str, sk: str, retry_config: RetryConfig, stream: bool
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        request console api with sign and retry
        """
        # pass request timeout
        req.retry_config = retry_config

        def _helper() -> Union[QfResponse, Iterator[QfResponse]]:
            req_copy = deepcopy(req)
            ConsoleAPIRequestor._sign(req_copy, ak, sk)
            if stream:
                return self._request_stream(req_copy)
            return self._request(req_copy)

        return self._with_retry(retry_config, _helper)

    def _request_stream(
        self,
        request: QfRequest,
    ) -> Iterator[QfResponse]:
        raise NotImplementedError("stream request is not supported")

    async def _async_request_console_api(
        self, req: QfRequest, ak: str, sk: str, retry_config: RetryConfig, stream: bool
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        """
        request console api with sign and retry
        """
        # pass request timeout
        req.retry_config = retry_config

        async def _helper() -> Union[QfResponse, AsyncIterator[QfResponse]]:
            req_copy = deepcopy(req)
            ConsoleAPIRequestor._sign(req, ak, sk)
            if stream:
                return await self._async_request_stream(req_copy)

            return await self._async_request(req)

        return await self._async_with_retry(retry_config, _helper)

    async def _async_request_stream(
        self,
        request: QfRequest,
    ) -> AsyncIterator[QfResponse]:
        raise NotImplementedError("stream request is not supported")

    @staticmethod
    def _sign(request: QfRequest, ak: str, sk: str) -> None:
        """
        sign the request
        """
        parsed_uri = urlparse(get_config().CONSOLE_API_BASE_URL)
        host = parsed_uri.netloc
        request.headers = {
            "Content-Type": "application/json",
            "Host": host,
            **request.headers,
        }
        iam_sign(ak, sk, request)
        request.url = get_config().CONSOLE_API_BASE_URL + request.url


def _get_console_ak_sk(pop: bool = True, **kwargs: Any) -> Tuple[str, str]:
    """
    extract ak and sk from kwargs
    if not found in kwargs, will return value from global config and env variable
    if `pop` is True, remove ak and sk from kwargs
    """
    ak = kwargs.get("ak", None) or get_config().ACCESS_KEY
    sk = kwargs.get("sk", None) or get_config().SECRET_KEY
    if ak is None or sk is None:
        raise InvalidArgumentError(
            "access_key and secret_key must be provided! 未提供 access_key 或"
            " secret_key ！"
        )
    if pop:
        # remove ak and sk from kwargs
        for key in ("ak", "sk"):
            if key in kwargs:
                del kwargs[key]
    return ak, sk
