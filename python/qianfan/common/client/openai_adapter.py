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
from typing import Any, AsyncIterator, Iterator, Optional

from flask import Flask, Response, jsonify, request

from qianfan.extensions.openai.adapter import OpenAIApdater
from qianfan.utils.utils import check_dependency

app = Flask(__name__)

adapter = OpenAIApdater()


def stream(resp: AsyncIterator[Any]) -> Iterator[str]:
    """
    Convert an async iterator to a stream.

    The return value of OpenAIAdapter is an async iterator, but Response
    of Flask only accepts sync iterator. Therefore, we need to convert
    the async iterator to a sync iterator.
    """
    loop = asyncio.new_event_loop()
    while True:
        try:
            data = loop.run_until_complete(resp.__anext__())
            yield "data: " + json.dumps(data) + "\n\n"
        except StopAsyncIteration:
            break


@app.post("/v1/chat/completions")
async def chat_completion() -> Response:
    openai_params = request.json
    assert openai_params is not None
    resp = await adapter.chat(openai_params)

    if isinstance(resp, AsyncIterator):
        return Response(stream(resp), mimetype="text/event-stream")

    return jsonify(resp)


@app.post("/v1/completions")
async def completion() -> Response:
    openai_params = request.json
    assert openai_params is not None
    resp = await adapter.completion(openai_params)

    if isinstance(resp, AsyncIterator):
        return Response(stream(resp), mimetype="text/event-stream")

    return jsonify(resp)


@app.post("/v1/embeddings")
async def embedding() -> Response:
    openai_params = request.json
    assert openai_params is not None
    resp = await adapter.embedding(openai_params)

    return jsonify(resp)


def entry(host: str, port: int, detach: bool, log_file: Optional[str]) -> None:
    check_dependency("openai", ["flask", "gevent", "werkzeug"])
    import logging
    import socket

    import rich
    from gevent.pywsgi import WSGIServer
    from rich.markdown import Markdown
    from werkzeug.serving import get_interface_ip

    import qianfan
    from qianfan.common.client.openai_adapter import app as openai_apps
    from qianfan.utils.logging import logger

    qianfan.enable_log("INFO")
    if log_file is not None:
        logger._logger.addHandler(logging.FileHandler(log_file))

    http_server = WSGIServer((host, port), openai_apps, log=logger._logger)

    messages = ["OpenAI wrapper server is running at"]
    messages.append(f"- http://127.0.0.1:{port}")
    display_host = host
    if display_host == "0.0.0.0":
        display_host = get_interface_ip(socket.AddressFamily.AF_INET)
    messages.append(f"- http://{display_host}:{port}")

    messages.append("\nRemember to set the environment variables:")
    messages.append(f"""```shell
    export OPENAI_API_KEY='any-content-you-want'
    export OPENAI_BASE_URL='http://{display_host}:{port}/v1'
    """)

    rich.print(Markdown("\n".join(messages)))
    rich.print()

    if detach:
        import os

        from multiprocess import Process

        # close stderr output
        logger._logger.removeHandler(logger.handler)
        process = Process(target=http_server.serve_forever)
        process.start()

        rich.print(
            f"OpenAI wrapper server is running in background with PID {process.pid}."
        )
        os._exit(0)

    http_server.serve_forever()
