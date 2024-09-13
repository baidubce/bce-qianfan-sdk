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
Qianfan API Requestor
"""
import copy
import json
import os
from datetime import datetime
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    TypeVar,
    Union,
)
from urllib.parse import urlparse

import aiohttp
import requests

import qianfan.errors as errors
from qianfan.config import get_config
from qianfan.consts import APIErrorCode, Consts
from qianfan.resources.auth.iam import iam_sign
from qianfan.resources.auth.oauth import Auth, _masked_ak
from qianfan.resources.requestor.base import (
    BaseAPIRequestor,
    _async_check_if_status_code_is_200,
    _check_if_status_code_is_200,
    _with_latency,
)
from qianfan.resources.token_limiter import AsyncTokenLimiter, TokenLimiter
from qianfan.resources.typing import QfRequest, QfResponse, RetryConfig
from qianfan.utils.logging import log_debug, log_error, log_info

_T = TypeVar("_T")


class QfAPIRequestor(BaseAPIRequestor):
    """
    object to manage Qianfan API requests
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        `ak`, `sk` and `access_token` can be provided in kwargs.
        """
        super().__init__(**kwargs)
        self._token_limiter = TokenLimiter(**kwargs)
        self._async_token_limiter = AsyncTokenLimiter(**kwargs)

    def _retry_if_token_expired(self, func: Callable[..., _T]) -> Callable[..., _T]:
        """
        this is a wrapper to deal with token expired error
        """
        token_refreshed = False

        def retry_wrapper(*args: Any, **kwargs: Any) -> _T:
            nonlocal token_refreshed
            # if token is refreshed, token expired exception will not be dealt with
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

    @_with_latency
    def _request_stream(
        self,
        request: QfRequest,
        data_postprocess: Callable[[QfResponse], QfResponse] = lambda x: x,
    ) -> Iterator[QfResponse]:
        """
        stream sync request
        """
        request = self._preprocess_request(request)
        responses = self._client.request_stream(request)

        _, resp = next(responses)
        if "json" in resp.headers.get("content-type", "") or resp.status_code != 200:
            try:
                status_code = resp.status_code
                body, resp = next(responses)
                self._check_error(json.loads(body))
            except Exception as e:
                log_error(
                    f"stream ended with status code: {status_code}, error: {e},"
                    f" headers: {resp.headers}"
                )
                raise e

        if "X-Ratelimit-Limit-Requests" in resp.headers:
            self._rate_limiter.reset_once(
                float(resp.headers["X-Ratelimit-Limit-Requests"])
            )

        def iter() -> Iterator[QfResponse]:
            event = ""
            token_refreshed = False
            nonlocal responses
            while True:
                try:
                    body, resp = next(responses)
                except StopIteration:
                    break
                _check_if_status_code_is_200(resp, self.config)
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
                    except errors.AccessTokenExpiredError:
                        if not token_refreshed:
                            token_refreshed = True
                            self._auth.refresh_access_token()
                            self._add_access_token(request)
                            with self._rate_limiter.acquire():
                                responses = self._client.request_stream(request)
                            continue
                        raise

                    except json.JSONDecodeError:
                        # the response is not json format
                        # ignore and raise RequestError
                        pass

                    raise errors.RequestError(
                        f"got unexpected stream response from server: {body_str}"
                    )
                body_str = body_str[len(Consts.STREAM_RESPONSE_PREFIX) :]
                if body_str != Consts.V2_STREAM_RESPONSE_END_NOTE:
                    json_body = json.loads(body_str)
                else:
                    return
                if event != "":
                    json_body["_event"] = event
                    event = ""
                parsed = self._parse_response(json_body, resp)
                parsed.request = QfRequest.from_requests(resp.request)
                parsed.request.json_body = copy.deepcopy(request.json_body)
                parsed.request.retry_config = request.retry_config
                parsed.statistic["first_token_latency"] = resp.elapsed.total_seconds()
                yield data_postprocess(parsed)

        return iter()

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

    @_with_latency
    async def _async_request_stream(
        self,
        request: QfRequest,
        data_postprocess: Callable[[QfResponse], QfResponse] = lambda x: x,
    ) -> AsyncIterator[QfResponse]:
        """
        async stream request
        """
        request = await self._async_preprocess_request(request)
        responses = self._client.arequest_stream(request)

        _, resp = await responses.__anext__()
        if "X-Ratelimit-Limit-Requests" in resp.headers:
            await self._rate_limiter.async_reset_once(
                float(resp.headers["X-Ratelimit-Limit-Requests"])
            )

        if "json" in resp.headers.get("content-type", "") or resp.status != 200:
            try:
                status_code = resp.status
                body, _ = await responses.__anext__()
                self._check_error(json.loads(body))
            except Exception as e:
                log_error(
                    f"stream ended with status code: {status_code}, error: {e},"
                    f" headers: {resp.headers}"
                )
                await responses.aclose()
                raise e

        async def iter() -> AsyncIterator[QfResponse]:
            nonlocal responses
            token_refreshed = False
            count = 0
            async for body, resp in responses:
                count += 1
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
                    except errors.AccessTokenExpiredError:
                        if not token_refreshed:
                            token_refreshed = True
                            await self._auth.arefresh_access_token()
                            await self._async_add_access_token(request)
                            async with self._rate_limiter.acquire():
                                responses = self._client.arequest_stream(request)
                            continue
                        raise
                    raise errors.RequestError(
                        f"got unexpected stream response from server: {body_str}"
                    )
                body_str = body_str[len(Consts.STREAM_RESPONSE_PREFIX) :]
                if not body_str.startswith(Consts.V2_STREAM_RESPONSE_END_NOTE):
                    json_body = json.loads(body_str)
                else:
                    return
                parsed = await self._parse_async_response(json_body, resp)
                parsed.request = QfRequest.from_aiohttp(resp.request_info)
                parsed.request.json_body = copy.deepcopy(request.json_body)
                parsed.request.retry_config = request.retry_config
                yield data_postprocess(parsed)

        return iter()

    def _check_error(self, body: Dict[str, Any]) -> None:
        """
        check whether error_code in response body
        if there is an APITokenExpired error,
        raise AccessTokenExpiredError
        """
        if "error_code" in body:
            req_id = body.get("id", "")
            error_code = body["error_code"]
            err_msg = body.get("error_msg", "no error message found in response body")
            possible_reason = ""
            if error_code == APIErrorCode.IAMCertificationFailed.value:
                possible_reason = (
                    "IAM 鉴权失败，请检查 Access Key 与 Secret Key 是否正确，"
                    "当前使用的 Access Key 为"
                    f" `{_masked_ak(self.config.ACCESS_KEY or '')}`"
                )
            elif error_code == APIErrorCode.DailyLimitReached.value:
                possible_reason = "未开通所调用服务的付费权限，或者账户已欠费"
            if possible_reason != "":
                err_msg += f" 可能的原因: {possible_reason}"
            log_error(
                f"api request req_id: {req_id} failed with error code: {error_code},"
                f" err msg: {err_msg}, please check"
                " https://cloud.baidu.com/doc/WENXINWORKSHOP/s/tlmyncueh"
            )
            if error_code in {
                APIErrorCode.APITokenExpired.value,
                APIErrorCode.APITokenInvalid.value,
            }:
                raise errors.AccessTokenExpiredError
            raise errors.APIError(error_code, err_msg, req_id)

    def _parse_response(
        self, body: Dict[str, Any], resp: requests.Response
    ) -> QfResponse:
        try:
            return super()._parse_response(body, resp)
        except errors.APIError as e:
            if e.error_code == APIErrorCode.TPMLimitReached.value:
                self._token_limiter.clear()
            raise e

    async def _parse_async_response(
        self, body: Dict[str, Any], resp: aiohttp.ClientResponse
    ) -> QfResponse:
        try:
            return await super()._parse_async_response(body, resp)
        except errors.APIError as e:
            if e.error_code == APIErrorCode.TPMLimitReached.value:
                await self._async_token_limiter.clear()
            raise e

    def _get_token_count_from_body(self, body: Dict[str, Any]) -> int:
        token_count = 0
        messages = body.get("messages", None)
        prompt = body.get("prompt", None)

        if messages and prompt:
            err_msg = "messages and prompt exist simultaneously"
            log_error(err_msg)
            raise ValueError(err_msg)

        if messages:
            assert isinstance(messages, list)
            for message in messages:
                content = message.get("content", None)
                if not content:
                    continue
                if isinstance(content, str):
                    token_count += self._token_limiter.tokenizer.count_tokens(content)
                elif isinstance(content, List):
                    for ct in content:
                        token_count += self._token_limiter.tokenizer.count_tokens(
                            ct.get("text", "")
                        )

        if prompt:
            assert isinstance(prompt, str)
            token_count += self._token_limiter.tokenizer.count_tokens(prompt)

        return token_count

    def _compensate_token_usage_non_stream(
        self, resp: QfResponse, token_count: int
    ) -> QfResponse:
        if isinstance(resp, QfResponse):
            token_usage = resp.body.get("usage", {}).get("total_tokens", 0)
            if token_usage:
                self._token_limiter.compensate(token_count - token_usage)

            if "X-Ratelimit-Limit-Tokens" in resp.headers:
                self._token_limiter.reset_once(
                    int(resp.headers["X-Ratelimit-Limit-Tokens"])
                )

            return resp

    def _compensate_token_usage_stream(
        self, resp: Iterator[QfResponse], token_count: int
    ) -> Iterator[QfResponse]:
        if isinstance(resp, Iterator):
            token_usage = 0
            for res in resp:
                if "X-Ratelimit-Limit-Tokens" in res.headers:
                    self._token_limiter.reset_once(
                        int(res.headers["X-Ratelimit-Limit-Tokens"])
                    )

                chunk_usage = res.body.get("usage", {}) or {}
                chunk_usage.get("total_tokens", 0)
                yield res

            if token_usage:
                self._token_limiter.compensate(token_count - token_usage)

    async def _async_compensate_token_usage_non_stream(
        self, resp: QfResponse, token_count: int
    ) -> QfResponse:
        if isinstance(resp, QfResponse):
            token_usage = resp.body.get("usage", {}).get("total_tokens", 0)
            if token_usage:
                await self._async_token_limiter.compensate(token_count - token_usage)

            if "X-Ratelimit-Limit-Tokens" in resp.headers:
                await self._async_token_limiter.reset_once(
                    int(resp.headers["X-Ratelimit-Limit-Tokens"])
                )

            return resp

    def _preprocess_request(self, request: QfRequest) -> QfRequest:
        return self._add_access_token(request)

    async def _async_preprocess_request(self, request: QfRequest) -> QfRequest:
        return await self._async_add_access_token(request)

    async def _async_compensate_token_usage_stream(
        self, resp: AsyncIterator[QfResponse], token_count: int
    ) -> AsyncIterator[QfResponse]:
        if isinstance(resp, AsyncIterator):
            token_usage = 0
            async for res in resp:
                if "X-Ratelimit-Limit-Tokens" in res.headers:
                    await self._async_token_limiter.reset_once(
                        int(res.headers["X-Ratelimit-Limit-Tokens"])
                    )

                token_usage = res.body.get("usage", {}).get("total_tokens", 0)
                yield res

            if token_usage:
                await self._async_token_limiter.compensate(token_count - token_usage)

    def llm(
        self,
        endpoint: str,
        header: Dict[str, Any] = {},
        query: Dict[str, Any] = {},
        body: Dict[str, Any] = {},
        stream: bool = False,
        data_postprocess: Callable[[QfResponse], QfResponse] = lambda x: x,
        retry_config: RetryConfig = RetryConfig(),
        show_total_latency: bool = False,
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        llm related api request
        """
        log_debug(f"requesting llm api endpoint: {endpoint}")
        # TODO 应该放在Adapter中做处理。
        for m in body.get("messages", []):
            if m.get("role", "") == "function":
                if not m.get("name", None):
                    m["name"] = m.get("tool_call_id", "")
                    m.pop("tool_call_id", None)

        @self._retry_if_token_expired
        def _helper() -> Union[QfResponse, Iterator[QfResponse]]:
            req = self._base_llm_request(
                endpoint,
                header=header,
                query=query,
                body=body,
                retry_config=retry_config,
            )

            token_count = self._get_token_count_from_body(body)
            self._token_limiter.decline(token_count)

            def _generator_wrapper(
                generator: Iterator[QfResponse],
            ) -> Iterator[QfResponse]:
                for res in generator:
                    if not show_total_latency:
                        res.statistic["total_latency"] = 0
                        res.statistic["request_latency"] = 0

                    yield res

            def _list_generator(data: List) -> Any:
                for res in data:
                    yield res

            if stream:
                generator = self._compensate_token_usage_stream(
                    self._request_stream(req, data_postprocess=data_postprocess),
                    token_count,
                )

                if not show_total_latency:
                    return _generator_wrapper(generator)
                else:
                    result_list: List[QfResponse] = []
                    for res in generator:
                        result_list.append(res)

                    return _list_generator(result_list)
            else:
                return self._compensate_token_usage_non_stream(
                    self._request(
                        req,
                        data_postprocess=data_postprocess,
                    ),
                    token_count,
                )

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
        show_total_latency: bool = False,
    ) -> Union[QfResponse, AsyncIterator[QfResponse]]:
        """
        llm related api request
        """
        log_debug(f"async requesting llm api endpoint: {endpoint}")
        for m in body.get("messages", []):
            if m.get("role", "") == "function":
                if not m.get("name", None):
                    m["name"] = m.get("tool_call_id", "")
                    m.pop("tool_call_id", None)

        class AsyncListIterator:
            def __init__(self, data: List[QfResponse]):
                self.data = data
                self.index = 0

            def __aiter__(self) -> "AsyncListIterator":
                return self

            async def __anext__(self) -> Any:
                if self.index < len(self.data):
                    value = self.data[self.index]
                    self.index += 1
                    return value
                else:
                    raise StopAsyncIteration

        @self._async_retry_if_token_expired
        async def _helper() -> Union[QfResponse, AsyncIterator[QfResponse]]:
            req = self._base_llm_request(
                endpoint,
                header=header,
                query=query,
                body=body,
                retry_config=retry_config,
            )

            token_count = self._get_token_count_from_body(body)
            await self._async_token_limiter.decline(token_count)

            async def _async_generator_wrapper(
                generator: AsyncIterator[QfResponse],
            ) -> AsyncIterator[QfResponse]:
                async for res in generator:
                    if not show_total_latency:
                        res.statistic["total_latency"] = 0
                        res.statistic["request_latency"] = 0

                    yield res

            if stream:
                generator = self._async_compensate_token_usage_stream(
                    await self._async_request_stream(
                        req, data_postprocess=data_postprocess
                    ),
                    token_count,
                )

                if not show_total_latency:
                    return _async_generator_wrapper(generator)
                else:
                    result_list: List[QfResponse] = []
                    async for res in generator:
                        result_list.append(res)

                    return AsyncListIterator(result_list)
            else:
                return await self._async_compensate_token_usage_non_stream(
                    await self._async_request(req, data_postprocess=data_postprocess),
                    token_count,
                )

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

    @staticmethod
    def _sign(request: QfRequest, ak: str, sk: str) -> None:
        """
        sign the request
        """
        url = request.url
        parsed_uri = urlparse(request.url)
        if os.environ.get("QIANFAN_IAM_HOST"):
            host = str(os.environ.get("QIANFAN_IAM_HOST"))
            parsed_uri = parsed_uri._replace(scheme="https", netloc=host)
        else:
            host = parsed_uri.netloc
        request.url = parsed_uri.path
        request.headers = {
            "Content-Type": "application/json",
            "Host": host,
            **(request.headers if request.headers else {}),
        }
        iam_sign(ak, sk, request)
        request.url = url

    def _add_access_token(
        self, req: QfRequest, auth: Optional[Auth] = None
    ) -> QfRequest:
        """
        add access token to QfRequest
        """
        if self.config.NO_AUTH:
            # 配置无鉴权，不签名，不抛出需要刷新token的异常，直接跳出。
            return req
        if auth is None:
            auth = self._auth
        access_token = auth.access_token()
        if access_token == "":
            # use IAM auth
            access_key = auth._access_key
            secret_key = auth._secret_key
            if access_key is None or secret_key is None:
                raise errors.AccessTokenExpiredError
            self._sign(req, access_key, secret_key)
        else:
            # use openapi auth
            req.query["access_token"] = access_token
        return req

    async def _async_add_access_token(
        self, req: QfRequest, auth: Optional[Auth] = None
    ) -> QfRequest:
        """
        async add access token to QfRequest
        """
        if self.config.NO_AUTH:
            # 配置无鉴权，不签名，不抛出需要刷新token的异常，直接跳出。
            return req
        if auth is None:
            auth = self._auth
        access_token = await auth.a_access_token()
        if access_token == "":
            # use IAM auth
            access_key = auth._access_key
            secret_key = auth._secret_key
            if access_key is None or secret_key is None:
                raise errors.AccessTokenExpiredError
            self._sign(req, access_key, secret_key)
        else:
            # use openapi auth
            req.query["access_token"] = access_token
        return req

    def _llm_api_url(self, endpoint: str) -> str:
        """
        convert endpoint to llm api url
        """
        return "{}{}{}".format(
            self.config.BASE_URL,
            self.config.MODEL_API_PREFIX,
            endpoint,
        )

    def _request_api(self, req: QfRequest, auth: Optional[Auth] = None) -> QfResponse:
        """
        request api with auth and retry
        """

        @self._retry_if_token_expired
        def _helper() -> QfResponse:
            return self._request(req)

        return self._with_retry(req.retry_config, _helper)

    def _async_request_api(
        self, req: QfRequest, auth: Optional[Auth] = None
    ) -> Awaitable[QfResponse]:
        """
        async request api with auth and retry
        """

        @self._async_retry_if_token_expired
        async def _helper() -> QfResponse:
            return await self._async_request(req)

        return self._async_with_retry(req.retry_config, _helper)


class QfAPIV2Requestor(QfAPIRequestor):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(refresh_func=self._refresh_bearer_token, **kwargs)

    def _refresh_bearer_token(self, *args: Any, **kwargs: Any) -> Dict:
        """
        refresh bearer token
        """
        from qianfan.resources.console.iam import IAM

        resp = IAM.create_bearer_token(
            expire_in_seconds=self.config.BEARER_TOKEN_EXPIRED_INTERVAL,
            ak=self._auth._access_key,
            sk=self._auth._secret_key,
        )

        def _convert_time_str_to_sec(time_str: str) -> float:
            dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            return dt.timestamp()

        return {
            "token": resp.body["token"],
            "refresh_at": _convert_time_str_to_sec(resp.body["createTime"]),
            "expire_at": _convert_time_str_to_sec(resp.body["expireTime"]),
        }

    def _llm_api_url(self, endpoint: str) -> str:
        """
        convert endpoint to llm api url
        """
        return "{}{}".format(
            self.config.CONSOLE_API_BASE_URL,
            endpoint,
        )

    def _add_access_token(
        self, req: QfRequest, auth: Optional[Auth] = None
    ) -> QfRequest:
        """
        add bearer token to QfRequest V2
        """
        if self.config.NO_AUTH:
            # 配置无鉴权，不签名，不抛出需要刷新token的异常，直接跳出。
            return req
        if auth is None:
            auth = self._auth
        bearer_token = auth.bearer_token()
        if bearer_token == "":
            raise errors.BearerTokenExpiredError
        else:
            # use openapi auth
            req.headers["Authorization"] = f"Bearer {bearer_token}"
        return req

    def _retry_if_token_expired(self, func: Callable[..., _T]) -> Callable[..., _T]:
        """
        this is a wrapper to deal with token expired error
        """
        token_refreshed = False

        def retry_wrapper(*args: Any, **kwargs: Any) -> _T:
            nonlocal token_refreshed
            # if token is refreshed, token expired exception will not be dealt with
            if not token_refreshed:
                try:
                    return func(*args)
                except errors.BearerTokenExpiredError:
                    # refresh token and set token_refreshed flag
                    self._auth.refresh_bearer_token()
                    token_refreshed = True
                    # then fallthrough and try again
            return func(*args, **kwargs)

        return retry_wrapper

    async def _async_add_access_token(
        self, req: QfRequest, auth: Optional[Auth] = None
    ) -> QfRequest:
        """
        async add access token to QfRequest
        """
        return self._add_access_token(req, auth)

    def _check_error(self, body: Dict[str, Any]) -> None:
        """
        check whether error_code in response body
        if there is an APITokenExpired error,
        raise AccessTokenExpiredError
        """
        if "error" in body:
            req_id = body.get("id", "")
            error_code = body["error"]["code"]
            err_msg = body["error"].get(
                "message", "no error message found in response body"
            )

            log_error(
                f"api request req_id: {req_id} failed with error code: {error_code},"
                f" err msg: {err_msg}, please check"
                " https://cloud.baidu.com/doc/WENXINWORKSHOP/s/tlmyncueh"
            )

            raise errors.APIError(error_code, err_msg, req_id)

        # TODO 加上过期的raise BearerTokenExpiredError
        # 当前无法区分


def create_api_requestor(*args: Any, **kwargs: Any) -> QfAPIRequestor:
    if get_config().ENABLE_PRIVATE:
        return PrivateAPIRequestor(**kwargs)

    return QfAPIRequestor(**kwargs)


class PrivateAPIRequestor(QfAPIRequestor):
    """
    qianfan private api requestor
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        `ak`, `sk` and `access_token` can be provided in kwargs.
        """
        super().__init__(**kwargs)
        self._ak = kwargs.get("ak", None) or get_config().AK
        self._sk = kwargs.get("sk", None) or get_config().SK
        self._access_code = kwargs.get("access_code", None) or get_config().ACCESS_CODE

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
        req = QfRequest(
            method="POST",
            url="{}{}".format(
                get_config().MODEL_API_PREFIX,
                endpoint,
            ),
        )
        req.headers = header
        req.query = query
        req.json_body = body
        req.retry_config = retry_config
        return req

    def llm(
        self,
        endpoint: str,
        header: Dict[str, Any] = {},
        query: Dict[str, Any] = {},
        body: Dict[str, Any] = {},
        stream: bool = False,
        data_postprocess: Callable[[QfResponse], QfResponse] = lambda x: x,
        retry_config: RetryConfig = RetryConfig(),
        show_total_latency: bool = False,
    ) -> Union[QfResponse, Iterator[QfResponse]]:
        """
        llm related api request
        """
        log_info(f"requesting llm api endpoint: {endpoint}")

        def _helper() -> Union[QfResponse, Iterator[QfResponse]]:
            req = self._base_llm_request(
                endpoint,
                header=header,
                query=query,
                body=body,
                retry_config=retry_config,
            )
            parsed_uri = urlparse(get_config().BASE_URL)
            host = parsed_uri.netloc
            req.headers["content-type"] = "application/json;"
            req.headers["Host"] = host
            if self._access_code != "" and self._access_code is not None:
                req.headers["Authorization"] = "ACCESSCODE {}".format(self._access_code)
            elif self._ak != "" and self._sk != "":
                iam_sign(str(self._ak), str(self._sk), req)
            req.url = get_config().BASE_URL + req.url

            if stream:
                return self._request_stream(req, data_postprocess=data_postprocess)
            return self._request(req, data_postprocess=data_postprocess)

        return self._with_retry(retry_config, _helper)

    def _add_access_token(
        self, req: QfRequest, auth: Optional[Auth] = None
    ) -> QfRequest:
        return req

    async def _async_add_access_token(
        self, req: QfRequest, auth: Optional[Auth] = None
    ) -> QfRequest:
        return req
