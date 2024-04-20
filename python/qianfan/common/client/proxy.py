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
from typing import AsyncIterator, Callable, Optional

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse, Response, StreamingResponse

from qianfan.extensions.proxy.proxy import ClientProxy
from qianfan.utils.utils import get_ip_address
from qianfan.consts import DefaultValue

app = FastAPI()
proxy = ClientProxy()


@app.post("/base/{url_path:path}")
async def base_iam(request: Request, url_path: str) -> Response:
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

    print(request.scope)
    resp = await proxy.get_response(request, DefaultValue.BaseURL)
    if isinstance(resp, AsyncIterator):
        return StreamingResponse(resp, media_type="text/event-stream")

    return JSONResponse(resp)


@app.post("/console/{url_path:path}")
async def console_iam(request: Request, url_path: str) -> Response:
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

    print(request.scope)
    resp = await proxy.get_response(request, DefaultValue.ConsoleAPIBaseURL)
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

    qianfan.enable_log("DEBUG")

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
