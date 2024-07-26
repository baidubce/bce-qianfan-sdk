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

from typing import Any, AsyncIterator, Callable, Dict, Optional, Tuple

from aiohttp import ClientResponse
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import JSONResponse, Response, StreamingResponse

from qianfan.consts import DefaultValue
from qianfan.extensions.proxy.proxy import ClientProxy
from qianfan.utils.utils import get_ip_address

base_app = FastAPI()
console_app = FastAPI()
proxy = ClientProxy()


async def get_stream(
    request: AsyncIterator[Tuple[bytes, ClientResponse]]
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


@base_app.middleware("http")
async def base_openapi(request: Request, callback: Callable) -> Response:
    """
    用于向base请求中添加访问令牌。

    Args:
        request (Request): 请求对象。
        callback (Callable): 回调函数。

    Returns:
        Response: 处理后的响应对象。
    """
    if not proxy.direct and proxy.access_token is not None:
        try:
            key = request.url._url.split("?access_token=")[1]
        except Exception:
            return JSONResponse(
                {
                    "error": {
                        "message": "No ACCESS_TOKEN provided, please check",
                        "type": "invalid_request_error",
                        "param": None,
                        "code": "NO_ACCESS_TOKEN",
                    }
                },
                status_code=401,
            )
        if key != proxy.access_token:
            return JSONResponse(
                {
                    "error": {
                        "message": (
                            f"Incorrect ACCESS_TOKEN provided: {key}, please check"
                        ),
                        "type": "invalid_request_error",
                        "param": None,
                        "code": "invalid_ACCESS_TOKEN",
                    }
                },
                status_code=401,
            )
        else:
            new_scope = dict(request.scope)
            if proxy._config.ACCESS_KEY and proxy._config.SECRET_KEY:
                new_scope["query_string"] = b""
            else:
                proxy._direct = True
            request = StarletteRequest(scope=new_scope, receive=request.receive)

    else:
        pass
    resp = await proxy.get_response(request, DefaultValue.BaseURL)
    if isinstance(resp, AsyncIterator):
        return StreamingResponse(get_stream(resp), media_type="text/event-stream")

    return JSONResponse(resp)


@console_app.middleware("http")
async def console_iam(request: Request, callback: Callable) -> Response:
    """
    用于向console请求中添加访问令牌。

    Args:
        request (Request): 请求对象。
        callback (Callable): 回调函数。

    Returns:
        Response: 处理后的响应对象。
    """
    resp = await proxy.get_response(request, DefaultValue.ConsoleAPIBaseURL)

    if isinstance(resp, AsyncIterator):
        return StreamingResponse(resp, media_type="text/event-stream")

    return JSONResponse(resp)


def entry(
    host: str,
    base_port: int,
    console_port: int,
    detach: bool,
    log_file: Optional[str],
    mock_port: int,
    ssl_config: Dict[str, Any],
    access_token: Optional[str],
    direct: bool,
) -> None:
    import os

    import rich
    import uvicorn
    import uvicorn.config
    from multiprocess import Process
    from rich.markdown import Markdown

    import qianfan
    from qianfan.utils.logging import logger

    qianfan.enable_log("DEBUG")

    if access_token is not None:
        proxy.access_token = access_token
    if direct:
        proxy._direct = True

    proxy.mock_port = mock_port

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
    display_host = host
    if display_host == "0.0.0.0":
        display_host = get_ip_address()

    http_header = "http" if not ssl_config else "https"

    messages.append(f"- base: {http_header}://{display_host}:{base_port}")
    messages.append(f"- console: {http_header}://{display_host}:{console_port}")

    rich.print(Markdown("\n".join(messages)))
    rich.print()

    def set_cors(app: FastAPI) -> None:
        origins = [
            "*",
        ]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def start_server(app: FastAPI, port: int) -> None:
        uvicorn.run(
            app, host=display_host, port=port, log_config=log_config, **ssl_config
        )

    set_cors(base_app)
    set_cors(console_app)

    # close stderr output
    if detach:
        logger._logger.removeHandler(logger.handler)
        log_config["loggers"]["uvicorn.access"]["handlers"].remove("access")
        log_config["loggers"]["uvicorn"]["handlers"].remove("default")

    process_base = Process(target=start_server, args=(base_app, base_port))
    process_console = Process(target=start_server, args=(console_app, console_port))
    process_base.start()
    process_console.start()

    rich.print(
        f"Proxy base server is running in background with PID {process_base.pid}."
    )
    rich.print(
        f"Proxy console server is running in background with PID {process_console.pid}."
    )
    if detach:
        os._exit(0)
    else:
        try:
            process_base.join()
            process_console.join()
        except KeyboardInterrupt:
            process_base.terminate()
            process_console.terminate()
