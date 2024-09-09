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
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse

from qianfan.extensions.openai.adapter import OpenAIApdater
from qianfan.utils.utils import get_ip_address


def entry(
    host: str,
    port: int,
    detach: bool,
    log_file: Optional[str],
    ignore_system: bool,
    model_mapping: Dict[str, str],
    api_key: Optional[str],
) -> None:
    import rich
    import uvicorn
    import uvicorn.config
    from rich.markdown import Markdown

    from qianfan.utils.logging import logger

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

    messages = ["OpenAI wrapper server is running at"]
    messages.append(f"- http://127.0.0.1:{port}")
    display_host = host
    if display_host == "0.0.0.0":
        display_host = get_ip_address()
    if display_host != "127.0.0.1":
        messages.append(f"- http://{display_host}:{port}")

    messages.append("\nRemember to set the environment variables:")
    messages.append(f"""```shell
    export OPENAI_API_KEY='{api_key or "any-content-you-want"}'
    export OPENAI_BASE_URL='http://{display_host}:{port}/v1'
    """)

    rich.print(Markdown("\n".join(messages)))
    rich.print()

    # might not work on Windows if moving this function out of current scope
    def start_server() -> None:
        openai_apps = FastAPI()

        adapter = OpenAIApdater()

        if model_mapping is not None:
            adapter._model_mapping = model_mapping
        adapter._ignore_system = ignore_system

        async def stream(resp: AsyncIterator[Any]) -> AsyncIterator[str]:
            """
            Convert an async iterator to a stream.
            """
            async for data in resp:
                yield "data: " + json.dumps(data) + "\n\n"
            yield "data: [DONE]\n\n"

        @openai_apps.middleware("http")
        async def check_header(request: Request, call_next: Any) -> Any:
            if api_key is not None:
                key = request.headers.get("Authorization")
                if key != f"Bearer {api_key}":
                    return JSONResponse(
                        {
                            "error": {
                                "message": (
                                    f"Incorrect API key provided: {key}. You can find"
                                    " your API key at"
                                    " https://platform.openai.com/account/api-keys."
                                ),
                                "type": "invalid_request_error",
                                "param": None,
                                "code": "invalid_api_key",
                            }
                        },
                        status_code=401,
                    )

            return await call_next(request)

        # 添加CORS中间件，允许跨域以及OPTIONS请求
        openai_apps.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "*"
            ],  # 允许所有来源，或者你可以指定特定的来源，例如：["https://example.com"]
            allow_credentials=True,
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["*"],  # 允许所有头部，或者你可以指定特定的头部
        )

        @openai_apps.post("/v1/chat/completions")
        async def chat_completion(request: Request) -> Response:
            openai_params = await request.json()
            assert openai_params is not None
            resp = await adapter.chat(openai_params)

            if isinstance(resp, AsyncIterator):
                return StreamingResponse(stream(resp), media_type="text/event-stream")

            return JSONResponse(resp)

        @openai_apps.post("/v1/completions")
        async def completion(request: Request) -> Response:
            openai_params = await request.json()
            assert openai_params is not None
            resp = await adapter.completion(openai_params)

            if isinstance(resp, AsyncIterator):
                return StreamingResponse(stream(resp), media_type="text/event-stream")

            return JSONResponse(resp)

        @openai_apps.post("/v1/embeddings")
        async def embedding(request: Request) -> Response:
            openai_params = await request.json()
            assert openai_params is not None
            resp = await adapter.embedding(openai_params)

            return JSONResponse(resp)

        import uvicorn

        uvicorn.run(openai_apps, host=host, port=port, log_config=log_config)

    if detach:
        import os

        from multiprocess import Process

        # close stderr output
        logger._logger.removeHandler(logger.handler)
        log_config["loggers"]["uvicorn.access"]["handlers"].remove("access")
        log_config["loggers"]["uvicorn"]["handlers"].remove("default")

        process = Process(target=start_server)
        process.start()

        rich.print(
            f"OpenAI wrapper server is running in background with PID {process.pid}."
        )
        os._exit(0)

    start_server()
