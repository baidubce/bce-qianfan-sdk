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
import json
from copy import deepcopy
from typing import Any, AsyncIterator, Callable, Dict, Iterator, Tuple, Union
from urllib.parse import urlparse

import qianfan.errors as errors
from qianfan import get_config
from qianfan.consts import Consts
from qianfan.errors import InvalidArgumentError
from qianfan.resources.auth.iam import iam_sign
from qianfan.resources.requestor.base import (
    BaseAPIRequestor,
    _async_check_if_status_code_is_200,
    _check_if_status_code_is_200,
    _with_latency,
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
        self, req: QfRequest, ak: str, sk: str, retry_config: RetryConfig
    ) -> QfResponse:
        """
        request console api with sign and retry
        """
        # pass request timeout
        req.retry_config = retry_config

        async def _helper() -> QfResponse:
            ConsoleAPIRequestor._sign(req, ak, sk)
            return await self._async_request(req)

        return await self._async_with_retry(retry_config, _helper)

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


class ConsoleInferAPIRequestor(ConsoleAPIRequestor):
    @classmethod
    def _get_url(cls, model_type: str) -> str:
        """
        get infer api url
        """
        if model_type == "chat":
            return Consts.ChatV2API
        raise errors.InvalidArgumentError(f"{model_type} is not supported by V2 API")

    def _base_llm_request(
        self,
        model_type: str,
        header: Dict[str, Any],
        query: Dict[str, Any],
        body: Dict[str, Any],
        retry_config: RetryConfig,
    ) -> QfRequest:
        """
        create base llm QfRequest from provided args
        """
        req = QfRequest(
            method="POST",
            url=self._get_url(model_type),
        )
        req.headers = header
        req.query = query
        req.json_body = body
        req.retry_config = retry_config
        return req

    def llm(
        self,
        model_type: str,
        header: Dict[str, Any] = {},
        query: Dict[str, Any] = {},
        body: Dict[str, Any] = {},
        stream: bool = False,
        retry_config: RetryConfig = RetryConfig(),
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        llm related api request
        """

        req = self._base_llm_request(
            model_type=model_type,
            header=header,
            query=query,
            body=body,
            retry_config=retry_config,
        )
        ak, sk = _get_console_ak_sk()
        # todo: token 限流

        return self._request_console_api(req, ak, sk, retry_config, stream)

    @_with_latency
    def _request_stream(
        self,
        request: QfRequest,
    ) -> Iterator[QfResponse]:
        """
        stream sync request
        """
        responses = self._client.request_stream(request)

        _, resp = next(responses)
        if "json" in resp.headers.get("content-type", ""):
            body, resp = next(responses)
            self._check_error(json.loads(body))

        def iter() -> Iterator[QfResponse]:
            event = ""
            nonlocal responses
            while True:
                try:
                    body, resp = next(responses)
                except StopIteration:
                    break
                _check_if_status_code_is_200(resp)
                body_str = body.decode("utf-8")
                if body_str == "":
                    continue
                if body_str.startswith(Consts.STREAM_RESPONSE_EVENT_PREFIX):
                    # event indicator for the type of data
                    event = body_str[len(Consts.STREAM_RESPONSE_EVENT_PREFIX) :]
                    continue
                elif not body_str.startswith(Consts.STREAM_RESPONSE_PREFIX):
                    try:
                        # the response might be error message in json format
                        json_body = json.loads(body_str)
                        self._check_error(json_body)

                    except json.JSONDecodeError:
                        # the response is not json format
                        # ignore and raise RequestError
                        pass

                    raise errors.RequestError(
                        f"got unexpected stream response from server: {body_str}"
                    )
                body_str = body_str[len(Consts.STREAM_RESPONSE_PREFIX) :]
                json_body = json.loads(body_str)
                if event != "":
                    json_body["_event"] = event
                    event = ""
                parsed = self._parse_response(json_body, resp)
                parsed.request = QfRequest.from_requests(resp.request)
                parsed.request.json_body = deepcopy(request.json_body)
                parsed.statistic["first_token_latency"] = resp.elapsed.total_seconds()
                yield parsed

        return iter()

    @_with_latency
    async def _async_request_stream(
        self,
        request: QfRequest,
        data_postprocess: Callable[[QfResponse], QfResponse] = lambda x: x,
    ) -> AsyncIterator[QfResponse]:
        """
        async stream request
        """
        responses = self._client.arequest_stream(request)

        _, resp = await responses.__anext__()
        if "json" in resp.headers.get("content-type", ""):
            body, _ = await responses.__anext__()
            self._check_error(json.loads(body))

        async def iter() -> AsyncIterator[QfResponse]:
            nonlocal responses
            async for body, resp in responses:
                _async_check_if_status_code_is_200(resp)
                body_str = body.decode("utf-8")
                if body_str.strip() == "":
                    continue
                if not body_str.startswith(Consts.STREAM_RESPONSE_PREFIX):
                    try:
                        # the response might be error message in json format
                        json_body: Dict[str, Any] = json.loads(body_str)
                        self._check_error(json_body)
                    except json.JSONDecodeError:
                        # the response is not json format, ignore and raise RequestError
                        pass

                    raise errors.RequestError(
                        f"got unexpected stream response from server: {body_str}"
                    )
                body_str = body_str[len(Consts.STREAM_RESPONSE_PREFIX) :]
                json_body = json.loads(body_str)
                parsed = await self._parse_async_response(json_body, resp)
                parsed.request = QfRequest.from_aiohttp(resp.request_info)
                parsed.request.json_body = deepcopy(request.json_body)
                yield data_postprocess(parsed)

        return iter()


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
