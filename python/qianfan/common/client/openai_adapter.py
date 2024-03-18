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
from typing import Any, AsyncIterator, Iterator

from flask import Flask, Response, jsonify, request

from qianfan.extensions.openai.adapter import OpenAIApdater

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
