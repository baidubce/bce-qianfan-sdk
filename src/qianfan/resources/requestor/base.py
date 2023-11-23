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
API Requestor for SDK
"""

import asyncio
import json
import time
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Iterator,
    TypeVar,
)

import aiohttp
import requests

import qianfan.errors as errors
from qianfan.consts import APIErrorCode, Consts
from qianfan.resources.http_client import HTTPClient
from qianfan.resources.rate_limiter import RateLimiter
from qianfan.resources.typing import QfRequest, QfResponse, RetryConfig
from qianfan.utils.logging import log_error, log_warn

_T = TypeVar("_T")


def _check_if_status_code_is_200(response: requests.Response) -> None:
    """
    check whether the status code of response is ok(200)
    if the status code is not 200, raise a `RequestError`
    """
    if response.status_code != 200:
        raise errors.RequestError(
            f"request failed with status code `{response.status_code}`, "
            f"headers: `{response.headers}`, "
            f"body: `{response.content!r}`"
        )


def _async_check_if_status_code_is_200(response: aiohttp.ClientResponse) -> None:
    """
    async check whether the status code of response is ok(200)
    if the status code is not 200, raise a `RequestError`
    """
    if response.status != 200:
        raise errors.RequestError(
            f"request failed with status code `{response.status}`, "
            f"headers: `{response.headers}`, "
            f"body: `{response.content}`"
        )


class BaseAPIRequestor(object):
    """
    Base class of API Requestor
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        `ak`, `sk` and `access_token` can be provided in kwargs.
        """
        self._client = HTTPClient()
        self._rate_limiter = RateLimiter(**kwargs)

    def _request(
        self,
        request: QfRequest,
        data_postprocess: Callable[[QfResponse], QfResponse] = lambda x: x,
    ) -> QfResponse:
        """
        simple sync request
        """
        with self._rate_limiter:
            response = self._client.request(request)
        _check_if_status_code_is_200(response)
        try:
            body = response.json()
        except requests.JSONDecodeError:
            raise errors.RequestError(
                f"Got invalid json response from server, body: {response.content!r}"
            )
        return data_postprocess(self._parse_response(body, response))

    def _request_stream(
        self,
        request: QfRequest,
        data_postprocess: Callable[[QfResponse], QfResponse] = lambda x: x,
    ) -> Iterator[QfResponse]:
        """
        stream sync request
        """
        with self._rate_limiter:
            responses = self._client.request_stream(request)
        for body, resp in responses:
            _check_if_status_code_is_200(resp)
            body_str = body.decode("utf-8")
            if body_str == "":
                continue
            if not body_str.startswith(Consts.STREAM_RESPONSE_PREFIX):
                try:
                    # the response might be error message in json format
                    json_body = json.loads(body_str)
                    self._check_error(json_body)
                except json.JSONDecodeError:
                    # the response is not json format, ignore and raise InternalError
                    pass

                raise errors.RequestError(
                    f"got unexpected stream response from server: {body_str}"
                )
            body_str = body_str[len(Consts.STREAM_RESPONSE_PREFIX) :]
            json_body = json.loads(body_str)
            parsed = self._parse_response(json_body, resp)
            yield data_postprocess(parsed)

    async def _async_request(
        self,
        request: QfRequest,
        data_postprocess: Callable[[QfResponse], QfResponse] = lambda x: x,
    ) -> QfResponse:
        """
        async request
        """
        async with self._rate_limiter:
            response, session = await self._client.arequest(request)
        async with session:
            async with response:
                _async_check_if_status_code_is_200(response)
                try:
                    body = await response.json()
                except json.JSONDecodeError:
                    raise errors.RequestError(
                        "Got invalid json response from server, body:"
                        f" {response.content}"
                    )
                return data_postprocess(self._parse_async_response(body, response))

    async def _async_request_stream(
        self,
        request: QfRequest,
        data_postprocess: Callable[[QfResponse], QfResponse] = lambda x: x,
    ) -> AsyncIterator[QfResponse]:
        """
        async stream request
        """
        async with self._rate_limiter:
            responses = self._client.arequest_stream(request)
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
            parsed = self._parse_async_response(json_body, resp)
            yield data_postprocess(parsed)

    def _parse_response(
        self, body: Dict[str, Any], resp: requests.Response
    ) -> QfResponse:
        """
        parse response to QfResponse
        """
        self._check_error(body)
        qf_response = QfResponse(
            code=resp.status_code, headers=dict(resp.headers), body=body
        )
        return qf_response

    def _parse_async_response(
        self, body: Dict[str, Any], resp: aiohttp.ClientResponse
    ) -> QfResponse:
        """
        parse async response to QfResponse
        """
        self._check_error(body)

        qf_response = QfResponse(
            code=resp.status, headers=dict(resp.headers), body=body
        )
        return qf_response

    def _check_error(self, body: Dict[str, Any]) -> None:
        """
        check whether there is error in response
        """
        raise NotImplementedError

    def _with_retry(
        self, config: RetryConfig, func: Callable[..., _T], *args: Any
    ) -> _T:
        """
        retry wrapper
        """
        retry_count = 0

        while retry_count < config.retry_count - 1:
            try:
                return func(*args)
            except errors.APIError as e:
                if e.error_code in {
                    APIErrorCode.ServerHighLoad,
                    APIErrorCode.QPSLimitReached,
                }:
                    log_warn(
                        f"got error code {e.error_code} from server, retrying... count:"
                        f" {retry_count}"
                    )
                else:
                    # other error cannot be recovered by retrying, so directly raise
                    raise
            except requests.RequestException as e:
                log_error(f"request exception: {e}, retrying... count: {retry_count}")
            # other exception cannot be recovered by retrying
            # will be directly raised

            time.sleep(config.backoff_factor * (2**retry_count))
            retry_count += 1
        # the last retry
        # exception will be directly raised
        return func(*args)

    async def _async_with_retry(
        self, config: RetryConfig, func: Callable[..., Awaitable[_T]], *args: Any
    ) -> _T:
        """
        async retry wrapper
        """
        retry_count = 0

        # the last retry will not catch exception
        while retry_count < config.retry_count - 1:
            try:
                return await func(*args)
            except errors.APIError as e:
                if e.error_code in {
                    APIErrorCode.ServerHighLoad,
                    APIErrorCode.QPSLimitReached,
                }:
                    log_warn(
                        f"got error code {e.error_code} from server, retrying... count:"
                        f" {retry_count}"
                    )
                else:
                    # other error cannot be recovered by retrying, so directly raise
                    raise
            except aiohttp.ClientError as e:
                log_warn(
                    f"async request exception: {e}, retrying... count: {retry_count}"
                )
            # other exception cannot be recovered by retrying
            # will be directly raised

            await asyncio.sleep(config.backoff_factor * (2**retry_count))
            retry_count += 1
        # the last retry
        # exception will be directly raised
        return await func(*args)
