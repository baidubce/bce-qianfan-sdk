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
import inspect
import json
import time
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Iterator,
    Optional,
    TypeVar,
    Union,
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


def _is_utf8_encoded_bytes(byte_str: bytes) -> bool:
    """check whether bytes object is utf8 encoded"""
    try:
        byte_str.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def _get_body_str(byte_str: Optional[Union[bytes, str]]) -> Optional[Union[bytes, str]]:
    """get utf8-decoded str"""
    if byte_str is None:
        return ""

    if (
        not byte_str
        or isinstance(byte_str, str)
        or not _is_utf8_encoded_bytes(byte_str)
    ):
        return byte_str

    return str(byte_str, encoding="utf8")


def _check_if_status_code_is_200(response: requests.Response) -> None:
    """
    check whether the status code of response is ok(200)
    if the status code is not 200, raise a `RequestError`
    """
    if response.status_code != 200:
        failed_msg = (
            f"http request url {response.url} failed "
            f"with http status code {response.status_code}\n"
        )
        if response.headers.get("X-Bce-Error-Code", ""):
            failed_msg += (
                f"error code from baidu: {response.headers['X-Bce-Error-Code']}\n"
            )

        if response.headers.get("X-Bce-Error-Message", ""):
            failed_msg += (
                f"error message from baidu: {response.headers['X-Bce-Error-Message']}\n"
            )

        request_body = _get_body_str(response.request.body)
        response_body = _get_body_str(response.content)

        failed_msg += (
            f"request headers: {response.request.headers}\n"
            f"request body: {request_body!r}\n"
            f"response headers: {response.headers}\n"
            f"response body: {response_body!r}"
        )

        log_error(failed_msg)
        raise errors.RequestError(failed_msg)


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


def _with_latency(func: Callable) -> Callable:
    """
    general decorator to add latency info into response
    """
    sign = inspect.signature(func)
    if inspect.iscoroutinefunction(func):
        return _async_latency(func)
    elif sign.return_annotation is Iterator[QfResponse]:
        return _stream_latency(func)
    elif sign.return_annotation is QfResponse:
        return _latency(func)
    elif sign.return_annotation is AsyncIterator[QfResponse]:
        return _async_stream_latency(func)
    return func


def _latency(func: Callable[..., QfResponse]) -> Callable[..., QfResponse]:
    """
    a decorator to add latency info into response
    """

    def wrapper(*args: Any, **kwargs: Any) -> QfResponse:
        start_time = time.perf_counter()
        resp = func(*args, **kwargs)
        resp.statistic["total_latency"] = time.perf_counter() - start_time
        return resp

    return wrapper


def _async_latency(
    func: Callable[..., Awaitable[QfResponse]]
) -> Callable[..., Awaitable[QfResponse]]:
    """
    a decorator to add latency info into async response
    """

    async def wrapper(*args: Any, **kwargs: Any) -> QfResponse:
        start_time = time.perf_counter()
        resp = await func(*args, **kwargs)
        resp.statistic["total_latency"] = time.perf_counter() - start_time
        return resp

    return wrapper


def _stream_latency(
    func: Callable[..., Iterator[QfResponse]]
) -> Callable[..., Iterator[QfResponse]]:
    """
    a decorator to add latency info into stream response
    """

    def wrapper(*args: Any, **kwargs: Any) -> Iterator[QfResponse]:
        start_time = time.perf_counter()
        first_token_latency: Optional[float] = None
        resp = func(*args, **kwargs)
        sse_block_receive_time = time.perf_counter()
        for r in resp:
            if first_token_latency is None:
                first_token_latency = time.perf_counter() - start_time
            r.statistic["request_latency"] = (
                time.perf_counter() - sse_block_receive_time
            )
            r.statistic["first_token_latency"] = first_token_latency
            r.statistic["total_latency"] = time.perf_counter() - start_time
            sse_block_receive_time = time.perf_counter()
            yield r

    return wrapper


def _async_stream_latency(
    func: Callable[..., AsyncIterator[QfResponse]]
) -> Callable[..., AsyncIterator[QfResponse]]:
    """
    a decorator to add latency info into async stream response
    """

    async def wrapper(*args: Any, **kwargs: Any) -> AsyncIterator[QfResponse]:
        start_time = time.perf_counter()
        first_token_latency: Optional[float] = None
        resp = func(*args, **kwargs)
        sse_block_receive_time = time.perf_counter()
        async for r in resp:
            if first_token_latency is None:
                first_token_latency = time.perf_counter() - start_time
            r.statistic["request_latency"] = (
                time.perf_counter() - sse_block_receive_time
            )
            r.statistic["first_token_latency"] = first_token_latency
            r.statistic["total_latency"] = time.perf_counter() - start_time
            sse_block_receive_time = time.perf_counter()
            yield r

    return wrapper


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

    @_with_latency
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
        resp = self._parse_response(body, response)
        resp.statistic["request_latency"] = response.elapsed.total_seconds()
        return data_postprocess(resp)

    @_with_latency
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

    @_with_latency
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
        start = time.perf_counter()
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
                resp = self._parse_async_response(body, response)
                resp.statistic["request_latency"] = time.perf_counter() - start
                return data_postprocess(resp)

    @_with_latency
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
