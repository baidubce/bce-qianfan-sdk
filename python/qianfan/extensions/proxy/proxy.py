from typing import Any, AsyncIterator, Dict, Union

from aiohttp import ClientResponse
from fastapi import Request

from qianfan import get_config
from qianfan.config import GlobalConfig
from qianfan.resources.http_client import HTTPClient
from qianfan.resources.auth.iam import iam_sign
from qianfan.resources.auth.oauth import Auth
from qianfan.resources.typing import QfRequest
from qianfan.consts import DefaultValue


class ClientProxy(object):
    _auth: Auth = Auth()
    _config: GlobalConfig = get_config()
    _client: HTTPClient = HTTPClient()

    def __init__(self) -> None:
        pass

    async def get_request(self, request: Request, url_route: str) -> QfRequest:
        """
        获取请求对象。
        Args:
            request (Request): HTTP请求对象。
            url_route (str): 请求路由。
        Returns:
            QfRequest: 请求对象。
        """
        print(request.scope)

        # 获取请求参数
        query_params = {}
        if request.scope["query_string"] != b"":
            query_params = {
                q.split("=")[0]: q.split("=")[1]
                for q in request.scope["query_string"].decode("utf-8").split("&")
            }

        # 获取请求url
        if url_route is DefaultValue.BaseURL:
            url = f"{DefaultValue.BaseURL}{request.scope['path'].replace('/base', '')}"
        else:
            url = (
                f"{DefaultValue.ConsoleAPIBaseURL}{request.scope['path'].replace('/console', '')}"
            )

        # 获取请求头
        headers = {
            k.decode("utf-8"): v.decode("utf-8") for k, v in request.scope["headers"]
        }

        # 获取请求体
        json_body = await request.json()
        return QfRequest(
            url=url,
            method=request.scope["method"],
            headers=headers,
            query=query_params,
            json_body=json_body,
        )

    async def get_stream(
        self, request: AsyncIterator[tuple[bytes, ClientResponse]]
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
    ) -> Union[Dict[str, Any], AsyncIterator]:
        """
        从api服务器获取新的响应。

        Args:
            request (Request): HTTP请求对象。

        Returns:
            Union[Dict[str, Any], AsyncIterator]:
                如果响应体是流式传输的，则返回一个异步迭代器，否则返回一个包含响应体的字典。

        """

        qf_req = await self.get_request(request, url_route)
        iam_sign(self._config.ACCESS_KEY, self._config.SECRET_KEY, qf_req)
        qf_req.query["access_token"] = self._auth.access_token()

        if qf_req.json_body.get("stream", False):
            resp = self._client.arequest_stream(qf_req)
            return self.get_stream(resp)
        else:
            resp, session = await self._client.arequest(qf_req)
            async with session:
                json_body = await resp.json()
            return json_body
