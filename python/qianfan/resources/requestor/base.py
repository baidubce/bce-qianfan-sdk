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

import copy
import functools
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
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

import qianfan.errors as errors
from qianfan.config import Config, get_config
from qianfan.resources.auth.oauth import Auth, _masked_ak
from qianfan.resources.http_client import HTTPClient
from qianfan.resources.rate_limiter.rate_limiter import VersatileRateLimiter
from qianfan.resources.rate_limiter.redis_rate_limiter import RedisRateLimiter
from qianfan.resources.typing import QfRequest, QfResponse, RetryConfig
from qianfan.utils.logging import log_error, log_trace, log_warn

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


def _check_if_status_code_is_200(response: requests.Response, config: Config) -> None:
    """
    check whether the status code of response is ok(200)
    if the status code is not 200, raise a `RequestError`
    """
    if response.status_code >= 300 or response.status_code < 200:
        failed_msg = (
            f"http request url {response.url} failed with http status code"
            f" {response.status_code}\n"
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

        possible_reason = ""
        x_err_msg = response.headers.get("X-Bce-Error-Message", "")
        if x_err_msg == "NotFound, cause: Could not find credential.":
            access_key = config.ACCESS_KEY
            if access_key:
                possible_reason = f"Access Key(`{_masked_ak(access_key)}`) 错误"
            else:
                possible_reason = "Access Key 未设置"
        elif (
            x_err_msg
            == "SignatureDoesNotMatch, cause: Fail to authn user: Signature does not"
            " match"
        ):
            secret_key = config.SECRET_KEY
            if secret_key:
                possible_reason = f"Secret Key(`{_masked_ak(secret_key)}`) 错误"
            else:
                possible_reason = "Secret Key 未设置"

        if possible_reason != "":
            possible_reason = f"\n可能的原因：{possible_reason}"

        failed_msg += (
            f"request headers: {response.request.headers}\n"
            f"request body: {request_body!r}\n"
            f"response headers: {response.headers}\n"
            f"response body: {response_body!r}"
            f"{possible_reason}"
        )

        log_error(failed_msg)
        raise errors.RequestError(
            failed_msg,
            body=request_body,
            headers=response.headers,
            status_code=response.status_code,
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


def _with_latency(func: Callable) -> Callable:
    """
    general decorator to add latency info into response
    """
    sign = inspect.signature(func)
    if sign.return_annotation is QfResponse:
        if inspect.iscoroutinefunction(func):
            return _async_latency(func)
        return _latency(func)
    elif sign.return_annotation is Iterator[QfResponse]:
        return _stream_latency(func)
    elif sign.return_annotation is AsyncIterator[QfResponse]:
        return _async_stream_latency(func)
    raise errors.InternalError()


_COMPLETION_TOKENS_FIELD = "completion_tokens"


def _get_rate_limit_key(requestor: Any, request: QfRequest) -> str:
    assert isinstance(requestor, BaseAPIRequestor)
    ch = requestor._auth.credential_hash()
    url = request.url
    return f"{ch}_{url}"


def _latency(func: Callable[..., QfResponse]) -> Callable[..., QfResponse]:
    """
    a decorator to add latency info into response
    """

    @functools.wraps(func)
    def wrapper(
        requestor: Any, request: QfRequest, *args: Any, **kwargs: Any
    ) -> QfResponse:
        log_trace(f"raw request: {request}")
        key = _get_rate_limit_key(requestor, request)
        if "key" in kwargs:
            key = kwargs["key"]

        with requestor._rate_limiter.acquire(key):
            start_time = time.perf_counter()
            start_timestamp = int(time.time() * 1000)
            resp = func(requestor, request, *args, **kwargs)
            resp.statistic["total_latency"] = time.perf_counter() - start_time
            resp.statistic["start_timestamp"] = start_timestamp
            usage_tokens = resp.body.get("usage", {}).get(_COMPLETION_TOKENS_FIELD, 0)
            resp.statistic["avg_output_tokens_per_second"] = (
                usage_tokens / resp.statistic["total_latency"]
            )
            return resp

    return wrapper


def _async_latency(
    func: Callable[..., Awaitable[QfResponse]]
) -> Callable[..., Awaitable[QfResponse]]:
    """
    a decorator to add latency info into async response
    """

    @functools.wraps(func)
    async def wrapper(
        requestor: Any, request: QfRequest, *args: Any, **kwargs: Any
    ) -> QfResponse:
        log_trace(f"raw request: {request}")
        key = _get_rate_limit_key(requestor, request)
        if "key" in kwargs:
            key = kwargs["key"]

        async with requestor._rate_limiter.acquire(key):
            start_time = time.perf_counter()
            start_timestamp = int(time.time() * 1000)
            resp = await func(requestor, request, *args, **kwargs)
            resp.statistic["total_latency"] = time.perf_counter() - start_time
            resp.statistic["start_timestamp"] = start_timestamp
            usage_tokens = resp.body.get("usage", {}).get(_COMPLETION_TOKENS_FIELD, 0)
            resp.statistic["avg_output_tokens_per_second"] = (
                usage_tokens / resp.statistic["total_latency"]
            )
            return resp

    return wrapper


def _stream_latency(
    func: Callable[..., Iterator[QfResponse]]
) -> Callable[..., Iterator[QfResponse]]:
    """
    a decorator to add latency info into stream response
    """

    @functools.wraps(func)
    def wrapper(
        requestor: Any, request: QfRequest, *args: Any, **kwargs: Any
    ) -> Iterator[QfResponse]:
        key = _get_rate_limit_key(requestor, request)
        if "key" in kwargs:
            key = kwargs["key"]

        with requestor._rate_limiter.acquire(key):
            start_time = time.perf_counter()
            start_timestamp = int(time.time() * 1000)
            resp = func(requestor, request, *args, **kwargs)

        def iter() -> Iterator[QfResponse]:
            is_first_block = True
            sse_block_receive_time = time.perf_counter()

            for r in resp:
                r.statistic["request_latency"] = (
                    (time.perf_counter() - sse_block_receive_time)
                    if not is_first_block
                    else r.statistic["first_token_latency"]
                )
                is_first_block = False

                r.statistic["total_latency"] = time.perf_counter() - start_time
                r.statistic["start_timestamp"] = start_timestamp
                sse_block_receive_time = time.perf_counter()
                chunk_usage = r.body.get("usage", {}) or {}
                usage_tokens = chunk_usage.get(_COMPLETION_TOKENS_FIELD, 0)
                r.statistic["avg_output_tokens_per_second"] = (
                    usage_tokens / r.statistic["total_latency"]
                )
                yield r

        return iter()

    return wrapper


def _async_stream_latency(
    func: Callable[..., Awaitable[AsyncIterator[QfResponse]]]
) -> Callable[..., Awaitable[AsyncIterator[QfResponse]]]:
    """
    a decorator to add latency info into async stream response
    """

    @functools.wraps(func)
    async def wrapper(
        requestor: Any, request: QfRequest, *args: Any, **kwargs: Any
    ) -> AsyncIterator[QfResponse]:
        key = _get_rate_limit_key(requestor, request)
        if "key" in kwargs:
            key = kwargs["key"]

        async with requestor._rate_limiter.acquire(key):
            start_time = time.perf_counter()
            start_timestamp = int(time.time() * 1000)
            resp = await func(requestor, request, *args, **kwargs)
            first_token_latency = time.perf_counter() - start_time

        async def iter() -> AsyncIterator[QfResponse]:
            nonlocal first_token_latency

            sse_block_receive_time = time.perf_counter()
            is_first_block = True

            async for r in resp:
                r.statistic["request_latency"] = (
                    (time.perf_counter() - sse_block_receive_time)
                    if not is_first_block
                    else first_token_latency
                )
                is_first_block = False

                r.statistic["first_token_latency"] = first_token_latency
                r.statistic["total_latency"] = time.perf_counter() - start_time
                r.statistic["start_timestamp"] = start_timestamp
                sse_block_receive_time = time.perf_counter()
                usage_tokens = r.body.get("usage", {}).get(_COMPLETION_TOKENS_FIELD, 0)
                r.statistic["avg_output_tokens_per_second"] = (
                    usage_tokens / r.statistic["total_latency"]
                )
                yield r

        return iter()

    return wrapper


class BaseAPIRequestor(object):
    """
    Base class of API Requestor
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        `ak`, `sk` and `access_token` can be provided in kwargs.
        """
        self._client = HTTPClient(**kwargs)
        self._auth = Auth(**kwargs)
        self._rate_limiter = (
            VersatileRateLimiter(**kwargs)
            if not kwargs.get("redis_rate_limiter", False)
            else RedisRateLimiter(**kwargs)
        )
        self._host = kwargs.get("host")
        self.config = kwargs.get("config", get_config())

    def _preprocess_request(self, request: QfRequest) -> QfRequest:
        return request

    async def _async_preprocess_request(self, request: QfRequest) -> QfRequest:
        return request

    @_with_latency
    def _request(
        self,
        request: QfRequest,
        data_postprocess: Callable[[QfResponse], QfResponse] = lambda x: x,
        check_error: Callable[
            [requests.Response, Config], None
        ] = _check_if_status_code_is_200,
    ) -> QfResponse:
        """
        simple sync request
        """
        request = self._preprocess_request(request)
        response = self._client.request(request)
        check_error(response, self.config)
        _check_if_status_code_is_200(response, self.config)
        try:
            body = response.json()
        except requests.JSONDecodeError:
            raise errors.RequestError(
                f"Got invalid json response from server, body: {response.content!r}"
            )
        resp = self._parse_response(body, response)
        resp.statistic["request_latency"] = response.elapsed.total_seconds()
        resp.request = QfRequest.from_requests(response.request)
        resp.request.json_body = copy.deepcopy(request.json_body)
        resp.request.retry_config = request.retry_config

        if "X-Ratelimit-Limit-Requests" in resp.headers:
            self._rate_limiter.reset_once(
                float(resp.headers["X-Ratelimit-Limit-Requests"])
            )
        return data_postprocess(resp)

    @_with_latency
    async def _async_request(
        self,
        request: QfRequest,
        data_postprocess: Callable[[QfResponse], QfResponse] = lambda x: x,
    ) -> QfResponse:
        """
        async request
        """
        request = self._preprocess_request(request)
        start = time.perf_counter()
        response, session = await self._client.arequest(request)
        request_latency = time.perf_counter() - start

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
                resp = await self._parse_async_response(body, response)
                resp.statistic["request_latency"] = request_latency
                resp.request = QfRequest.from_aiohttp(response.request_info)
                resp.request.json_body = copy.deepcopy(request.json_body)
                resp.request.retry_config = request.retry_config
                if "X-Ratelimit-Limit-Requests" in resp.headers:
                    await self._rate_limiter.async_reset_once(
                        float(resp.headers["X-Ratelimit-Limit-Requests"])
                    )

                return data_postprocess(resp)

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

    async def _parse_async_response(
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

        def predicate_api_err(result: Any) -> bool:
            if config.retry_err_handler:
                if config.retry_err_handler(result):
                    return True
            if isinstance(result, errors.APIError):
                # llm openapi error
                if result.error_code in config.retry_err_codes:
                    log_warn(
                        f"got error code {result.error_code} from server, retrying... "
                    )
                    return True
            if isinstance(result, requests.RequestException):
                log_error(f"request exception: {result}, retrying...")
                return True
            return False

        @retry(
            wait=wait_exponential_jitter(
                initial=config.backoff_factor,
                jitter=config.jitter,
                max=config.max_wait_interval,
            ),
            retry=retry_if_exception(predicate_api_err),
            stop=stop_after_attempt(config.retry_count),
            reraise=True,
        )
        def _retry_wrapper(*args: Any) -> _T:
            return func(*args)

        return _retry_wrapper(*args)

    async def _async_with_retry(
        self, config: RetryConfig, func: Callable[..., Awaitable[_T]], *args: Any
    ) -> _T:
        """
        async retry wrapper
        """

        def predicate_api_err_code(result: Any) -> bool:
            if isinstance(result, errors.APIError):
                if result.error_code in config.retry_err_codes:
                    log_warn(
                        f"got error code {result.error_code} from server, retrying... "
                    )
                    return True
            if isinstance(result, aiohttp.ClientError):
                log_error(f"request exception: {result}, retrying...")
                return True
            return False

        @retry(
            wait=wait_exponential_jitter(
                initial=config.backoff_factor,
                jitter=config.jitter,
                max=config.max_wait_interval,
            ),
            retry=retry_if_exception(predicate_api_err_code),
            stop=stop_after_attempt(config.retry_count),
            reraise=True,
        )
        async def _retry_wrapper(*args: Any) -> _T:
            return await func(*args)

        return await _retry_wrapper(*args)
