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

from fastapi import FastAPI, Request

from qianfan import ChatCompletion, Completion

app = FastAPI()

client = ChatCompletion()
comp_client = Completion()

model_map = {
    "gpt-3.5-turbo": "ERNIE-Speed",
    "gpt-4": "ERNIE-Bot-4",
    "gpt-4-turbo": "ERNIE-Bot",
}


@app.api_route(
    "/v1/chat/completions",
    methods=["POST", "OPTIONS"],
)
async def chat_completion(request: Request):
    openai_params = await request.json()
    stream = openai_params.get("stream", False)
    if stream:
        return await openai_params.get("engine")(openai_params)
    model = openai_params["model"]
    if model in model_map:
        model = model_map[model]
    messages = openai_params["messages"]

    qianfan_request = {}
    if messages[0]["role"] == "system":
        qianfan_request["system"] = messages[0]["content"]
        messages = messages[1:]
    print(messages)
    qianfan_request["messages"] = messages
    if "frequency_penalty" in openai_params:
        penalty = openai_params["frequency_penalty"]
        # [-2, 2] -> [-0.5, 0.5] -> [1, 2]
        penalty = penalty / 4 + 1.5
        qianfan_request["penalty_score"] = penalty
    if "max_tokens" in openai_params:
        qianfan_request["max_output_tokens"] = openai_params["max_tokens"]
    if "temperature" in openai_params:
        qianfan_request["temperature"] = openai_params["temperature"] / 2
    if "top_p" in openai_params:
        qianfan_request["top_p"] = openai_params["top_p"]
    if "stop" in openai_params:
        qianfan_request["stop"] = openai_params["stop"]
    if "tools" in openai_params:
        qianfan_request["tools"] = openai_params["tools"]
    if "tool_choice" in openai_params:
        qianfan_request["tool_choice"] = openai_params["tool_choice"]
    if "user" in openai_params:
        qianfan_request["user"] = openai_params["user"]
    n = openai_params.get("n", 1)
    resp_list = []
    completion_tokens = 0
    prompt_tokens = 0
    for i in range(n):
        resp = await client.ado(**qianfan_request)
        resp_list.append(
            {
                "index": i,
                "message": {
                    "role": "assistant",
                    "content": resp["result"],
                },
                "finish_reason": "stop",
            }
        )
        completion_tokens += resp["usage"]["completion_tokens"]
        prompt_tokens += resp["usage"]["prompt_tokens"]

    result = {
        "id": resp["id"],
        "object": "chat.completion",
        "choices": resp_list,
        "created": resp["created"],
        "model": model,
        "system_fingerprint": "fp_?",
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }
    return result


@app.api_route(
    "/v1/completions",
    methods=["POST", "OPTIONS"],
)
async def completion(request: Request):
    openai_params = await request.json()
    stream = openai_params.get("stream", False)
    if stream:
        return await openai_params.get("engine")(openai_params)
    model = openai_params["model"]
    if model in model_map:
        model = model_map[model]
    prompt = openai_params["prompt"]
    if isinstance(prompt, list):
        prompt = " ".join(prompt)

    qianfan_request = {}

    qianfan_request["prompt"] = prompt
    if "frequency_penalty" in openai_params:
        penalty = openai_params["frequency_penalty"]
        # [-2, 2] -> [-0.5, 0.5] -> [1, 2]
        penalty = penalty / 4 + 1.5
        qianfan_request["penalty_score"] = penalty
    if "max_tokens" in openai_params:
        qianfan_request["max_output_tokens"] = openai_params["max_tokens"]
    if "temperature" in openai_params:
        qianfan_request["temperature"] = openai_params["temperature"] / 2
    if "top_p" in openai_params:
        qianfan_request["top_p"] = openai_params["top_p"]
    if "stop" in openai_params:
        qianfan_request["stop"] = openai_params["stop"]
    if "tools" in openai_params:
        qianfan_request["tools"] = openai_params["tools"]
    if "tool_choice" in openai_params:
        qianfan_request["tool_choice"] = openai_params["tool_choice"]
    if "user" in openai_params:
        qianfan_request["user"] = openai_params["user"]
    n = openai_params.get("n", 1)
    resp_list = []
    completion_tokens = 0
    prompt_tokens = 0
    for i in range(n):
        resp = await comp_client.ado(**qianfan_request)
        resp_list.append(
            {
                "index": i,
                "text": resp["result"],
                "finish_reason": "stop",
            }
        )
        completion_tokens += resp["usage"]["completion_tokens"]
        prompt_tokens += resp["usage"]["prompt_tokens"]

    result = {
        "id": resp["id"],
        "object": "chat.completion",
        "choices": resp_list,
        "created": resp["created"],
        "model": model,
        "system_fingerprint": "fp_?",
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }
    return result
