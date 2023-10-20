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
    Union,
)
from urllib.parse import urlparse

import aiohttp
import requests

import qianfan.errors as errors
from qianfan.config import GLOBAL_CONFIG
from qianfan.consts import APIErrorCode, Consts
from qianfan.resources.auth import Auth, iam_sign
from qianfan.resources.http_client import HTTPClient
from qianfan.resources.rate_limiter import RateLimiter
from qianfan.resources.typing import QfRequest, QfResponse, RetryConfig
from qianfan.utils.logging import log_error, log_info, log_warn

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
        check whether "error_code" is in response
        if got error, APIError exception will be raised
        """
        if "error_code" in body:
            error_code = body["error_code"]
            err_msg = f"no error message in return body, error code: {error_code}"
            if "error_msg" in body:
                err_msg = body["error_msg"]
            elif "error_message" in body:
                err_msg = body["error_message"]
            log_error(
                f"api request failed with error code: {error_code}, err msg: {err_msg}"
            )
            if error_code in {
                APIErrorCode.APITokenExpired.value,
                APIErrorCode.APITokenInvalid.value,
            }:
                raise errors.AccessTokenExpiredError
            raise errors.APIError(error_code, err_msg)

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


class QfAPIRequestor(BaseAPIRequestor):
    """
    object to manage Qianfan API requests
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        `ak`, `sk` and `access_token` can be provided in kwargs.
        """
        super().__init__(**kwargs)
        self._auth = Auth(**kwargs)

    def _retry_if_token_expired(self, func: Callable[..., _T]) -> Callable[..., _T]:
        """
        this is a wrapper to deal with token expired error
        """
        token_refreshed = False

        def retry_wrapper(*args: Any, **kwargs: Any) -> _T:
            nonlocal token_refreshed
            # if token is refreshed, token expired exception will not be dealt with
            with self._rate_limiter:
                if not token_refreshed:
                    try:
                        return func(*args)
                    except errors.AccessTokenExpiredError:
                        # refresh token and set token_refreshed flag
                        self._auth.refresh_access_token()
                        token_refreshed = True
                        # then fallthrough and try again
                return func(*args, **kwargs)

        return retry_wrapper

    def _async_retry_if_token_expired(
        self, func: Callable[..., Awaitable[_T]]
    ) -> Callable[..., Awaitable[_T]]:
        """
        this is a wrapper to deal with token expired error
        """
        token_refreshed = False

        async def retry_wrapper(*args: Any, **kwargs: Any) -> _T:
            nonlocal token_refreshed
            # if token is refreshed, token expired exception will not be dealt with
            async with self._rate_limiter:
                if not token_refreshed:
                    try:
                        return await func(*args)
                    except errors.AccessTokenExpiredError:
                        # refresh token and set token_refreshed flag
                        await self._auth.arefresh_access_token()
                        token_refreshed = True
                        # then fallthrough and try again
                return await func(*args, **kwargs)

        return retry_wrapper

    def llm(
        self,
        endpoint: str,
        header: Dict[str, Any] = {},
        query: Dict[str, Any] = {},
        body: Dict[str, Any] = {},
        stream: bool = False,
        data_postprocess: Callable[[QfResponse], QfResponse] = lambda x: x,
        retry_config: RetryConfig = RetryConfig(),
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        llm related api request
        """
        log_info(f"requesting llm api endpoint: {endpoint}")

        @self._retry_if_token_expired
        def _helper() -> Union[QfResponse, Iterator[QfResponse]]:
            req = self._convert_to_llm_request(
                endpoint,
                header=header,
                query=query,
                body=body,
                retry_config=retry_config,
            )
            if stream:
                return self._request_stream(req, data_postprocess=data_postprocess)
            return self._request(req, data_postprocess=data_postprocess)

        return self._with_retry(retry_config, _helper)

    async def async_llm(
        self,
        endpoint: str,
        header: Dict[str, Any] = {},
        query: Dict[str, Any] = {},
        body: Dict[str, Any] = {},
        stream: bool = False,
        data_postprocess: Callable[[QfResponse], QfResponse] = lambda x: x,
        retry_config: RetryConfig = RetryConfig(),
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        """
        llm related api request
        """
        log_info(f"async requesting llm api endpoint: {endpoint}")

        @self._async_retry_if_token_expired
        async def _helper() -> Union[QfResponse, AsyncIterator[QfResponse]]:
            req = await self._aconvert_to_llm_request(
                endpoint,
                header=header,
                query=query,
                body=body,
                retry_config=retry_config,
            )
            if stream:
                return self._async_request_stream(
                    req, data_postprocess=data_postprocess
                )
            return await self._async_request(req, data_postprocess=data_postprocess)

        return await self._async_with_retry(retry_config, _helper)

    def _base_llm_request(
        self,
        endpoint: str,
        header: Dict[str, Any] = {},
        query: Dict[str, Any] = {},
        body: Dict[str, Any] = {},
        retry_config: RetryConfig = RetryConfig(),
    ) -> QfRequest:
        """
        create base llm QfRequest from provided args
        """
        req = QfRequest(method="POST", url=self._llm_api_url(endpoint))
        req.headers = header
        req.query = query
        req.json_body = body
        req.retry_config = retry_config
        return req

    def _convert_to_llm_request(
        self,
        endpoint: str,
        header: Dict[str, Any] = {},
        query: Dict[str, Any] = {},
        body: Dict[str, Any] = {},
        retry_config: RetryConfig = RetryConfig(),
    ) -> QfRequest:
        """
        convert args to llm QfRequest and add access_token
        """
        req = self._base_llm_request(
            endpoint, header=header, query=query, body=body, retry_config=retry_config
        )
        access_token = self._auth.access_token()
        if access_token == "":
            raise errors.AccessTokenExpiredError
        req.query["access_token"] = access_token
        return req

    async def _aconvert_to_llm_request(
        self,
        endpoint: str,
        header: Dict[str, Any] = {},
        query: Dict[str, Any] = {},
        body: Dict[str, Any] = {},
        retry_config: RetryConfig = RetryConfig(),
    ) -> QfRequest:
        """
        async convert args to llm QfRequest and add access_token
        """
        req = self._base_llm_request(
            endpoint, header=header, query=query, body=body, retry_config=retry_config
        )
        access_token = await self._auth.a_access_token()
        if access_token == "":
            raise errors.AccessTokenExpiredError
        req.query["access_token"] = access_token
        return req

    def _llm_api_url(self, endpoint: str) -> str:
        """
        convert endpoint to llm api url
        """
        return "{}{}{}".format(
            GLOBAL_CONFIG.BASE_URL,
            Consts.ModelAPIPrefix,
            endpoint,
        )


class ConsoleAPIRequestor(BaseAPIRequestor):
    """
    object to manage console API requests
    """

    def _request_console_api(
        self, req: QfRequest, ak: str, sk: str, retry_config: RetryConfig
    ) -> QfResponse:
        """
        request console api with sign and retry
        """

        def _helper() -> QfResponse:
            ConsoleAPIRequestor._sign(req, ak, sk)
            return self._request(req)

        return self._with_retry(retry_config, _helper)

    @staticmethod
    def _sign(request: QfRequest, ak: str, sk: str) -> None:
        """
        sign the request
        """
        parsed_uri = urlparse(GLOBAL_CONFIG.CONSOLE_API_BASE_URL)
        host = parsed_uri.netloc
        request.headers = {
            "Content-Type": "application/json",
            "Host": host,
            **request.headers,
        }
        iam_sign(ak, sk, request)
        request.url = GLOBAL_CONFIG.CONSOLE_API_BASE_URL + request.url
