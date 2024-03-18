import asyncio
import json
from typing import AsyncGenerator

from flask import Flask, Response, request

from qianfan.extensions.openai.adapter import OpenAIApdater

app = Flask(__name__)

adapter = OpenAIApdater()


@app.post("/v1/chat/completions")
async def chat_completion():
    openai_params = request.json
    resp = await adapter.chat(openai_params)

    def stream():
        loop = asyncio.new_event_loop()
        while True:
            try:
                data = loop.run_until_complete(resp.__anext__())
                yield "data: " + json.dumps(data) + "\n\n"
            except StopAsyncIteration as e:
                print(e)
                break

    if isinstance(resp, AsyncGenerator):
        return Response(stream(), mimetype="text/event-stream")

    return json.dumps(resp)
