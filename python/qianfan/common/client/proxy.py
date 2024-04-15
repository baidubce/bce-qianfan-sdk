# Copyright (c) 2024 Baidu, Inc. All Rights Reserved.
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
import json
import logging
from typing import Any, AsyncIterator, Callable, Dict, Optional, Union

from aiohttp import ClientSession
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse, Response, StreamingResponse

import qianfan
from qianfan.resources.auth.oauth import AuthManager
from qianfan.utils.utils import get_ip_address

app = FastAPI()

auth = AuthManager()


async def get_json_response(
    url: str, body: bytes, query_params: Optional[dict] = None
) -> Dict[str, Any]:
    """
    向指定的URL发送POST请求，并将返回的JSON响应体作为字典返回。

    Args:
        url (str): 请求的URL地址。
        body (bytes): 发送的请求体数据。
        query_params (Optional[dict], optional): 查询参数，默认为None。

    Returns:
        Dict[str, Any]: 响应体的JSON数据，以字典形式返回。

    """
    async with ClientSession() as session:
        async with session.post(url, data=body, params=query_params) as resp:
            resp_body = await resp.json()
            logging.info(resp_body)
            return resp_body


async def get_json_response_async(
    url: str, body: bytes, query_params: Optional[dict] = None
) -> AsyncIterator[str]:
    """
    异步获取指定URL的流式响应，并将内容作为字符串返回。

    Args:
        url (str): 请求的URL。
        body (bytes): 请求体，以字节形式传递。
        query_params (Optional[dict], optional): 查询参数，以字典形式传递。默认为None。

    Returns:
        AsyncIterator[str]: 异步迭代器，用于返回解码后的JSON响应内容。

    """
    async with ClientSession() as session:
        async with session.post(url, data=body, params=query_params) as resp:
            async for data in resp.content:
                logging.info(data)
                yield data.decode("utf-8")


async def get_response(
    token: str, request: Request
) -> Union[Dict[str, Any], AsyncIterator]:
    """
    从api服务器获取新的响应。

    Args:
        token (str): 访问令牌。
        request (Request): HTTP请求对象。

    Returns:
        Union[Dict[str, Any], AsyncIterator]:
            如果响应体是流式传输的，则返回一个异步迭代器，否则返回一个包含响应体的字典。

    """
    base_url = request.base_url

    query_params = {}
    if base_url.query:
        query_params = {
            q.split("=")[0]: q.split("=")[1] for q in base_url.query.split("&")
        }
    query_params["access_token"] = token

    url = f"https://aip.baidubce.com{request.scope['path']}"
    body = await request.json()

    assert body is not None
    is_stream = body.get("stream", False)

    if is_stream:
        return get_json_response_async(
            url, json.dumps(body).encode("utf-8"), query_params
        )
    else:
        return await get_json_response(
            url, json.dumps(body).encode("utf-8"), query_params
        )


@app.middleware("http")
async def add_token(request: Request, call_next: Callable) -> Response:
    """
    中间件函数，用于向请求中添加访问令牌。

    Args:
        request (Request): 请求对象。
        call_next (Callable): 调用下一个中间件的函数。

    Returns:
        Response: 处理后的响应对象。

    Raises:
        ValueError: 如果AK和SK未设置，或者获取访问令牌失败，则会抛出异常。
    """
    config = qianfan.get_config()
    ak, sk = config.AK, config.SK

    if ak is None or sk is None:
        raise ValueError("AK and SK must be set.")

    auth.register(ak, sk)
    token = auth.get_access_token(ak, sk)
    if token is None:
        raise ValueError("Failed to get access token.")

    resp = await get_response(token, request)
    if isinstance(resp, AsyncIterator):
        return StreamingResponse(resp, media_type="text/event-stream")

    return JSONResponse(resp)


def entry(host: str, port: int, detach: bool, log_file: Optional[str]) -> None:
    import rich
    import uvicorn
    import uvicorn.config
    from rich.markdown import Markdown

    import qianfan
    from qianfan.common.client.proxy import app as proxy_apps
    from qianfan.utils.logging import logger

    qianfan.enable_log("INFO")

    log_config = uvicorn.config.LOGGING_CONFIG
    if log_file is not None:
        log_config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "filename": log_file,
            "mode": "a",
            "encoding": "utf-8",
        }
        for key in log_config["loggers"]:
            if "handlers" in log_config["loggers"][key]:
                log_config["loggers"][key]["handlers"].append("file")

    messages = ["Proxy server is running at"]
    messages.append(f"- http://127.0.0.1:{port}")
    display_host = host
    if display_host == "0.0.0.0":
        display_host = get_ip_address()
    messages.append(f"- http://{display_host}:{port}")

    rich.print(Markdown("\n".join(messages)))
    rich.print()

    def start_server() -> None:
        uvicorn.run(proxy_apps, host=host, port=port, log_config=log_config)

    if detach:
        import os

        from multiprocess import Process

        # close stderr output
        logger._logger.removeHandler(logger.handler)
        log_config["loggers"]["uvicorn.access"]["handlers"].remove("access")
        log_config["loggers"]["uvicorn"]["handlers"].remove("default")

        process = Process(target=start_server)
        process.start()

        rich.print(f"Proxy server is running in background with PID {process.pid}.")
        os._exit(0)

    start_server()
