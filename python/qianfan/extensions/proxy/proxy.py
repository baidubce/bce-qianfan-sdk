import logging
from typing import Any, AsyncIterator, Dict, Optional, Union
from urllib.parse import urlparse

from fastapi import Request
from starlette.requests import ClientDisconnect

from qianfan import get_config
from qianfan.config import Config
from qianfan.consts import DefaultValue
from qianfan.errors import InvalidArgumentError
from qianfan.resources.auth.iam import iam_sign
from qianfan.resources.auth.oauth import Auth
from qianfan.resources.http_client import HTTPClient
from qianfan.resources.rate_limiter import VersatileRateLimiter
from qianfan.resources.typing import QfRequest, RetryConfig


class ClientProxy(object):
    _auth: Auth = Auth()
    _config: Config = get_config()
    _client: HTTPClient = HTTPClient()
    _mock_port: int = -1
    _rate_limiter: VersatileRateLimiter = VersatileRateLimiter()
    _retry_base_config: Optional[RetryConfig] = None
    _retry_console_config: Optional[RetryConfig] = None
    _access_token: Optional[str] = None
    _direct: bool = False

    def __init__(self) -> None:
        pass

    @property
    def direct(self) -> Optional[bool]:
        return self._direct

    @property
    def access_token(self) -> Optional[str]:
        return self._access_token

    @access_token.setter
    def access_token(self, access_token: str) -> None:
        self._access_token = access_token
        self._auth._access_token = access_token

    @property
    def mock_port(self) -> int:
        return self._mock_port

    @mock_port.setter
    def mock_port(self, value: int) -> None:
        self._mock_port = value

    @property
    def retry_base_config(self) -> RetryConfig:
        if self._retry_base_config is None:
            self._retry_base_config = RetryConfig(
                retry_count=self._config.LLM_API_RETRY_COUNT,
                timeout=self._config.LLM_API_RETRY_TIMEOUT,
                max_wait_interval=self._config.LLM_API_RETRY_MAX_WAIT_INTERVAL,
                backoff_factor=self._config.LLM_API_RETRY_BACKOFF_FACTOR,
                jitter=self._config.LLM_API_RETRY_JITTER,
                retry_err_codes=self._config.LLM_API_RETRY_ERR_CODES,
            )
        return self._retry_base_config

    @property
    def retry_console_config(self) -> RetryConfig:
        if self._retry_console_config is None:
            self._retry_console_config = RetryConfig(
                retry_count=self._config.CONSOLE_API_RETRY_COUNT,
                timeout=self._config.CONSOLE_API_RETRY_TIMEOUT,
                max_wait_interval=self._config.CONSOLE_API_RETRY_MAX_WAIT_INTERVAL,
                backoff_factor=self._config.CONSOLE_API_RETRY_BACKOFF_FACTOR,
                jitter=self._config.CONSOLE_API_RETRY_JITTER,
                retry_err_codes=self._config.CONSOLE_API_RETRY_ERR_CODES,
            )
        return self._retry_console_config

    def _sign(self, request: QfRequest) -> None:
        """
        对请求进行签名。
        Args:
            request (QfRequest): 请求对象。
        """
        if not self._auth._credential_available():
            raise InvalidArgumentError(
                "no enough credential found, any one of (access_key, secret_key),"
                " (ak, sk), access_token must be provided"
            )

        url, path = request.url, urlparse(request.url).path

        request.url = path
        if not (request.query.get("client_id") or request.query.get("client_secret")):
            iam_sign(
                str(self._config.ACCESS_KEY), str(self._config.SECRET_KEY), request
            )
        request.url = url
        if not request.headers.get("Authorization", None):
            self._auth._ak = request.query.get("client_id")
            self._auth._sk = request.query.get("client_secret")
            request.query["access_token"] = self._auth.access_token()

    async def get_request(self, request: Request, url_route: str) -> QfRequest:
        """
        获取请求对象。
        Args:
            request (Request): HTTP请求对象。
            url_route (str): 请求路由。
        Returns:
            QfRequest: 请求对象。
        """

        # 获取重试配置
        retry_config = (
            self.retry_console_config
            if url_route == DefaultValue.ConsoleAPIBaseURL
            else self.retry_base_config
        )

        # 获取请求头
        if self.mock_port != -1:
            url_route = f"http://127.0.0.1:{self.mock_port}"
        url = url_route + request.url.path
        host = urlparse(url_route).netloc

        headers = {
            "Content-Type": "application/json",
            "Host": host,
        }

        # 获取请求体
        json_body = await request.json()
        return QfRequest(
            url=url,
            headers=headers if not self._direct else dict(request.headers),
            method=request.method,
            query=dict(request.query_params),
            json_body=json_body,
            retry_config=retry_config,
        )

    async def get_response(
        self, request: Request, url_route: str
    ) -> Union[AsyncIterator, Dict[str, Any]]:
        """
        从api服务器获取新的响应。

        Args:
            request (Request): HTTP请求对象。
            url_route (str): 请求路由。

        Returns:
            Union[Dict[str, Any], AsyncIterator]:
                如果响应体是流式传输的，则返回一个异步迭代器，否则返回一个包含响应体的字典。

        """
        try:
            async with self._rate_limiter.acquire():
                qf_req = await self.get_request(request, url_route)
                if self._direct:
                    pass
                else:
                    self._sign(qf_req)
                logging.debug(f"request: {qf_req}")
                if qf_req.json_body.get("stream", False):
                    resp, session = await self._client.arequest(qf_req)
                    if (
                        "Content-Type" in resp.headers
                        and "application/json" in resp.headers["Content-Type"]
                    ):  # 判断返回中是否有流式数据
                        resp, session = await self._client.arequest(qf_req)
                        async with session:
                            json_body = await resp.json()
                        return json_body
                    else:
                        return self._client.arequest_stream(qf_req)
                else:
                    resp, session = await self._client.arequest(qf_req)
                    async with session:
                        json_body = await resp.json()
                    return json_body
        except ClientDisconnect as e:
            logging.error(f"client disconnected, {e}")
        return {}
