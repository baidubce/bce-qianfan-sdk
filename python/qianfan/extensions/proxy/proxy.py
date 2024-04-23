import logging
from asyncio import TimeoutError
from typing import Any, AsyncIterator, Dict, Tuple, Union
from urllib.parse import urlparse

import fastapi
from aiohttp import ClientResponse
from fastapi import Request

from qianfan import get_config
from qianfan.config import GlobalConfig
from qianfan.errors import InvalidArgumentError
from qianfan.resources.auth.iam import iam_sign
from qianfan.resources.auth.oauth import Auth
from qianfan.resources.http_client import HTTPClient
from qianfan.resources.typing import QfRequest


class ClientProxy(object):
    _auth: Auth = Auth()
    _config: GlobalConfig = get_config()
    _client: HTTPClient = HTTPClient()
    _mock_port: int = 8866

    def __init__(self) -> None:
        pass

    @property
    def mock_port(self) -> int:
        return self._mock_port

    @mock_port.setter
    def mock_port(self, value: int) -> None:
        self._mock_port = value

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
        iam_sign(str(self._config.ACCESS_KEY), str(self._config.SECRET_KEY), request)
        request.url = url

        if not request.headers.get("Authorization", None):
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

        # 获取请求url
        path = (
            request.url.path.replace("/base", "")
            if request.url.path.startswith("/base")
            else request.url.path.replace("/console", "")
        )

        # 获取请求头
        if self.mock_port != -1:
            url_route = f"http://127.0.0.1:{self.mock_port}"

        url = url_route + path
        host = urlparse(url_route).netloc
        headers = {
            "Content-Type": "application/json",
            "Host": host,
        }

        # 获取请求体
        json_body = await request.json()
        return QfRequest(
            url=url,
            headers=headers,
            method=request.method,
            query=dict(request.query_params),
            json_body=json_body,
        )

    async def get_stream(
        self, request: AsyncIterator[Tuple[bytes, ClientResponse]]
    ) -> AsyncIterator[str]:
        """
        改变响应体流式格式。
        Args:
            request (AsyncIterator[tuple[bytes, ClientResponse]]): 响应体流。
        Returns:
            AsyncIterator[str]: 响应体流。
        """
        async for body, response in request:
            yield body.decode("utf-8")

    async def get_response(
        self, request: Request, url_route: str
    ) -> Union[AsyncIterator, Dict[str, Any]]:
        """
        从api服务器获取新的响应。

        Args:
            request (Request): HTTP请求对象。

        Returns:
            Union[Dict[str, Any], AsyncIterator]:
                如果响应体是流式传输的，则返回一个异步迭代器，否则返回一个包含响应体的字典。

        """

        try:
            qf_req = await self.get_request(request, url_route)
            self._sign(qf_req)
            logging.debug(f"request: {qf_req}")

            if qf_req.json_body.get("stream", False):
                return self.get_stream(self._client.arequest_stream(qf_req))
            else:
                resp, session = await self._client.arequest(qf_req)
                async with session:
                    json_body = await resp.json()
                return json_body

        except InvalidArgumentError:
            raise fastapi.HTTPException(status_code=401, detail="Invalid Credential")
        except TimeoutError:
            raise fastapi.HTTPException(status_code=504, detail="Server Timeout")
        except ConnectionError:
            raise fastapi.HTTPException(status_code=503, detail="Server Unavailable")