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
import asyncio
import json
import logging
from aiohttp import ClientSession, ClientResponse
from typing import Any, AsyncIterator, Optional, Dict, Tuple, Union

import qianfan
import requests
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse, Response, StreamingResponse

from qianfan.extensions.openai.adapter import OpenAIApdater
from qianfan.utils.utils import get_ip_address
from qianfan.resources.auth.oauth import AuthManager, Auth

app = FastAPI()

adapter = OpenAIApdater()
auth = AuthManager()


async def get_response(
    token: str, request: Request
) -> Union[Dict[str, Any], AsyncIterator[str]]:
    """
    Get a new response from the server.
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

    async with ClientSession() as session:
        async with session.post(
            url, data=json.dumps(body).encode("utf-8"), params=query_params
        ) as resp:
            if is_stream:
                async for data in resp.content:
                    logging.info(data)
                    yield data
            resp_body = await resp.json()
            logging.info(resp_body)
            yield resp_body


@app.middleware("http")
async def add_token(request: Request, call_next):
    config = qianfan.get_config()
    ak, sk = config.AK, config.SK

    auth.register(ak, sk)
    token = auth.get_access_token(ak, sk)

    if token is None:
        raise ValueError("Failed to get access token.")

    resp = get_response(token, request)

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

    # messages.append("\nRemember to set the environment variables:")
    # messages.append(f"""```shell
    # export OPENAI_API_KEY='any-content-you-want'
    # export OPENAI_BASE_URL='http://{display_host}:{port}/v1'
    # """)

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
