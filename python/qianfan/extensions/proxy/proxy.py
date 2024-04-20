import json
import logging
from typing import Any, AsyncIterator, Dict, Union

from aiohttp import ClientSession
from fastapi import Request

from qianfan import get_config
from qianfan.config import GlobalConfig
from qianfan.resources.auth.iam import iam_sign
from qianfan.resources.auth.oauth import Auth
from qianfan.resources.typing import QfRequest
from qianfan.consts import DefaultValue


class ClientProxy(object):
    _auth: Auth = Auth()
    _config: GlobalConfig = get_config()

    def __init__(self) -> None:
        pass

    async def get_request(self, request: Request, url_route: str) -> QfRequest:
        base_url = request.base_url

        query_params = {}
        if base_url.query:
            query_params = {
                q.split("=")[0]: q.split("=")[1] for q in base_url.query.split("&")
            }

        if url_route is DefaultValue.BaseURL:
            url = f"{DefaultValue.BaseURL}{request.scope['path'].replace('/base','')}"
        else:
            url = f"{DefaultValue.ConsoleAPIBaseURL}{request.scope['path'].replace('/console','')}"
        headers = {k: v for k, v in request.headers.items()}
        headers["content-type"] = "application/json; charset=UTF-8"
        print(f"json::{await request.json()}\n")
        return QfRequest(
            url=url,
            method=request.method,
            headers=headers,
            query=query_params,
            json_body=(await request.json()),
        )

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
        is_stream = qf_req.json_body.get("stream", False)
        print(qf_req)

        if is_stream:
            return self.get_json_response_stream(qf_req)
        else:
            return await self.get_json_response(qf_req)

    async def get_json_response(
        self,
        req: QfRequest,
    ) -> Dict[str, Any]:
        """
        向指定的URL发送POST请求，并将返回的JSON响应体作为字典返回。

        Args:
            req (QfRequest): 请求对象。

        Returns:
            Dict[str, Any]: 响应体的JSON数据，以字典形式返回。

        """
        async with ClientSession() as session:
            async with session.request(**req.requests_args()) as resp:
                resp_body = await resp.json()
                logging.info(resp_body)
                return resp_body

    async def get_json_response_stream(
        self,
        req: QfRequest,
    ) -> AsyncIterator[str]:
        """
        异步获取指定URL的流式响应，并将内容作为字符串返回。

        Args:
            req (QfRequest): 请求对象。

        Returns:
            AsyncIterator[str]: 异步迭代器，用于返回解码后的JSON响应内容。

        """
        async with ClientSession() as session:
            async with session.request(**req.requests_args()) as resp:
                async for data in resp.content:
                    logging.info(data)
                    yield data.decode("utf-8")
