# Copyright (c) 2023 Baidu, Inc. All Rights Reserved.
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

from __future__ import annotations

import asyncio
import copy
import json
import re
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, TypeVar, Union

import qianfan
from qianfan import QfResponse
from qianfan.utils import log_debug

_T = TypeVar("_T")
OpenAIRequest = Dict[str, Any]
OpenAIResponse = Dict[str, Any]
QianfanRequest = Dict[str, Any]
QianfanResponse = Dict[str, Any]


def merge_async_iters(*aiters: AsyncIterator[_T]) -> AsyncIterator[_T]:
    """
    Merge multiple async iterators into one.
    """
    queue: asyncio.Queue[Tuple[bool, Union[_T, Exception]]] = asyncio.Queue(1)
    run_count = len(aiters)
    cancelling = False

    async def drain(aiter: AsyncIterator[_T]) -> None:
        nonlocal run_count
        try:
            async for item in aiter:
                await queue.put((False, item))
            await queue.put((False, StopAsyncIteration()))
        except Exception as e:
            if not cancelling:
                await queue.put((True, e))
            else:
                raise e
        finally:
            run_count -= 1

    async def merged() -> AsyncIterator[_T]:
        try:
            while run_count:
                raised, next_item = await queue.get()
                if raised:
                    assert isinstance(next_item, Exception)
                    cancel_tasks()
                    raise next_item
                if isinstance(next_item, Exception):
                    continue
                yield next_item
        finally:
            cancel_tasks()

    def cancel_tasks() -> None:
        nonlocal cancelling
        cancelling = True
        for t in tasks:
            t.cancel()

    tasks = [asyncio.create_task(drain(aiter)) for aiter in aiters]
    return merged()


class OpenAIApdater(object):
    """
    Adapter for OpenAI API to Qianfan API.
    """

    EmbeddingBatchSize = 16
    """
    Batch size for embedding requests.

    Qianfan API only supports batch size of 16, but OpenAI has not limits.
    This value is used to split OpenAI requests into multiple Qianfan requests.
    """

    def __init__(
        self,
        ignore_system: bool = True,
        model_mapping: Dict[str, str] = {
            r"gpt-3.5.*": "ERNIE-3.5-8K",
            r"gpt-4.*": "ERNIE-4.0-8K",
            r"text-embedding.*": "Embedding-V1",
        },
    ) -> None:
        self._chat_client = qianfan.ChatCompletion()
        self._comp_client = qianfan.Completion()
        self._embed_client = qianfan.Embedding()

        self._ignore_system = ignore_system
        self._model_mapping = model_mapping

    def _convert_model(self, model: str) -> str:
        """
        Convert OpenAI model name to Qianfan model name.
        """
        for pattern, qianfan_model in self._model_mapping.items():
            new_model, n = re.subn(pattern, qianfan_model, model)
            if n != 0:
                return new_model

        return model

    def openai_base_request_to_qianfan(
        self, openai_request: OpenAIRequest
    ) -> QianfanRequest:
        """
        Convert general arguments in OpenAI request to Qianfan request.
        """
        qianfan_request = copy.deepcopy(openai_request)

        def add_if_exist(openai_key: str, qianfan_key: Optional[str] = None) -> None:
            qianfan_key = openai_key if qianfan_key is None else qianfan_key
            if openai_key in openai_request:
                qianfan_request[qianfan_key] = openai_request[openai_key]
            if qianfan_key is not None and qianfan_key != openai_key:
                if openai_key in qianfan_request:
                    del qianfan_request[openai_key]

        add_if_exist("max_tokens", "max_output_tokens")
        add_if_exist("response_format")
        add_if_exist("top_p")
        add_if_exist("stop")
        add_if_exist("stream")
        add_if_exist("functions")
        add_if_exist("user", "user_id")
        add_if_exist("tool_choice")

        model = openai_request["model"]
        qianfan_request["model"] = self._convert_model(model)

        if "presence_penalty" in openai_request:
            penalty = openai_request["presence_penalty"]
            # [-2, 2] -> [-0.5, 0.5] -> [1, 2]
            penalty = penalty / 4 + 1.5
            qianfan_request["penalty_score"] = penalty
            qianfan_request.pop("presence_penalty")
        if "temperature" in openai_request:
            temperature = openai_request["temperature"] / 2
            if temperature == 0:
                temperature = 1e-9
            qianfan_request["temperature"] = temperature
        if "stop" in openai_request:
            stop = openai_request["stop"]
            if isinstance(stop, str):
                stop = [stop]
            qianfan_request["stop"] = stop
        if "tools" in openai_request:
            qianfan_request["functions"] = []
            tools = openai_request["tools"]
            for tool in tools:
                if tool["type"] == "function":
                    qianfan_request["functions"].append(tool["function"])
        if "function_call" in openai_request:
            function_call = openai_request["function_call"]
            if not isinstance(function_call, str):
                qianfan_request["tool_choice"] = {
                    "type": "function",
                    "function": function_call,
                }
        if qianfan_request.get("tool_choice") == "auto":
            qianfan_request.pop("tool_choice")
        if "response_format" in openai_request:
            response_format = openai_request["response_format"]
            if not isinstance(response_format, str):
                response_format = response_format["type"]
            qianfan_request["response_format"] = response_format
        return qianfan_request

    def openai_chat_request_to_qianfan(
        self, openai_request: OpenAIRequest
    ) -> QianfanRequest:
        """
        Convert chat request in OpenAI to Qianfan request.
        """
        qianfan_request = self.openai_base_request_to_qianfan(openai_request)
        messages = openai_request["messages"]
        if messages[0]["role"] == "system":
            if not self._ignore_system:
                qianfan_request["system"] = messages[0]["content"]
            messages = messages[1:]

        for item in messages:
            if item["role"] == "tool":
                item["role"] = "function"
                # json 格式的 function 结果模型才能正常处理，所以这里转一下
                item["content"] = json.dumps(
                    {"result": item["content"]}, ensure_ascii=False
                )

            if item["content"] is not None and item["content"].strip() == "":
                item["content"] = "/"
            if "tool_calls" in item:
                item["function_call"] = item["tool_calls"][0]["function"]
        qianfan_request["messages"] = messages
        self.qianfan_req_post_process(qianfan_request)
        return qianfan_request

    def openai_completion_request_to_qianfan(
        self, openai_request: OpenAIRequest
    ) -> QianfanRequest:
        """
        Convert completion request in OpenAI to Qianfan request.
        """
        qianfan_request = self.openai_base_request_to_qianfan(openai_request)
        prompt = openai_request["prompt"]
        if isinstance(prompt, list):
            prompt = "".join(prompt)
        qianfan_request["prompt"] = prompt
        self.qianfan_req_post_process(qianfan_request)
        return qianfan_request

    def convert_openai_embedding_request(
        self, openai_request: OpenAIRequest
    ) -> List[QianfanRequest]:
        """
        Converts embedding request in OpenAI to multiple Qianfan requests.

        Since Qianfan has limits on the count of texts in one request, we need to
        split the OpenAI request to multiple Qianfan requests.
        """
        qianfan_request = self.openai_base_request_to_qianfan(openai_request)
        input = openai_request["input"]
        if isinstance(input, str):
            input = [input]
        request_list = []
        i = 0
        while i < len(input):
            self.qianfan_req_post_process(qianfan_request)
            request_list.append(
                self.qianfan_req_post_process(
                    {
                        "texts": input[
                            i : min(i + self.EmbeddingBatchSize, len(input))
                        ],
                        **qianfan_request,
                    }
                )
            )
            i += self.EmbeddingBatchSize

        return request_list

    def qianfan_req_post_process(
        self, qianfan_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        qianfan_request["extra_parameters"] = {
            "request_source": f"qianfan_py_sdk_v{qianfan.VERSION}_openai"
        }
        return qianfan_request

    @classmethod
    def qianfan_chat_response_to_openai(
        cls, openai_request: OpenAIRequest, qianfan_response_list: List[QianfanResponse]
    ) -> OpenAIResponse:
        """
        Convert chat response in Qianfan to OpenAI.
        """
        resp_list = []
        completion_tokens = 0
        prompt_tokens = 0
        for i, resp in enumerate(qianfan_response_list):
            choice = {
                "index": i,
                "message": {
                    "role": "assistant",
                    "content": resp["result"],
                },
                "finish_reason": resp.get("finish_reason", "normal"),
            }
            if "function_call" in resp and (
                "functions" in openai_request or "tools" in openai_request
            ):
                choice["message"]["tool_calls"] = [
                    {
                        "id": resp["function_call"]["name"],
                        "type": "function",
                        "function": resp["function_call"],
                    }
                ]

                choice["message"]["content"] = None
                choice["message"]["function_call"] = resp["function_call"]
                choice["finish_reason"] = "tool_calls"

            resp_list.append(choice)

            completion_tokens += resp["usage"]["completion_tokens"]
            prompt_tokens += resp["usage"]["prompt_tokens"]
        resp = qianfan_response_list[0]
        result = {
            "id": resp["id"],
            "object": "chat.completion",
            "choices": resp_list,
            "created": resp["created"],
            "model": openai_request["model"],
            "system_fingerprint": "fp_?",
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }
        return result

    @classmethod
    def qianfan_completion_response_to_openai(
        cls, openai_request: OpenAIRequest, qianfan_response_list: List[QianfanResponse]
    ) -> OpenAIResponse:
        """
        Convert completion response in Qianfan to OpenAI.
        """
        resp_list = []
        completion_tokens = 0
        prompt_tokens = 0
        prefix = openai_request["prompt"] if openai_request.get("echo", False) else ""
        suffix = openai_request.get("suffix", "")
        for i, resp in enumerate(qianfan_response_list):
            choice = {
                "index": i,
                "text": f"{prefix}{resp['result']}{suffix}",
                "finish_reason": resp.get("finish_reason", "stop"),
            }
            resp_list.append(choice)

            completion_tokens += resp["usage"]["completion_tokens"]
            prompt_tokens += resp["usage"]["prompt_tokens"]
        resp = qianfan_response_list[0]
        result = {
            "id": resp["id"],
            "object": "text_completion",
            "choices": resp_list,
            "created": resp["created"],
            "model": openai_request["model"],
            "system_fingerprint": "fp_?",
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }
        return result

    @classmethod
    def qianfan_embedding_response_to_openai(
        cls, openai_request: OpenAIRequest, qianfan_response_list: List[QianfanResponse]
    ) -> OpenAIResponse:
        """
        Converts embedding response in Qianfan to OpenAI.
        """
        embed_list: List[Any] = []

        prompt_tokens = 0

        for resp in qianfan_response_list:
            for data in resp["data"]:
                embed = {
                    "index": len(embed_list),
                    "embedding": data["embedding"],
                    "object": "embedding",
                }
                embed_list.append(embed)
                prompt_tokens += resp["usage"]["prompt_tokens"]

        resp = qianfan_response_list[0]
        result = {
            "id": resp["id"],
            "object": "list",
            "data": embed_list,
            "created": resp["created"],
            "model": openai_request["model"],
            "system_fingerprint": "fp_?",
            "usage": {
                "prompt_tokens": prompt_tokens,
                "total_tokens": prompt_tokens,
            },
        }
        return result

    async def chat(
        self, request: OpenAIRequest
    ) -> Union[OpenAIResponse, AsyncIterator[OpenAIResponse]]:
        """
        Chat Wrapper API
        """
        stream = request.get("stream", False)
        log_debug(f"recv openai request: {request}")
        qianfan_request = self.openai_chat_request_to_qianfan(request)
        log_debug(f"convert to qianfan request: {qianfan_request}")
        n = request.get("n", 1)
        if stream:
            return self._chat_stream(n, request, qianfan_request)

        res = await asyncio.gather(
            *[self._chat_client.ado(**qianfan_request) for _ in range(n)]
        )
        result = self.qianfan_chat_response_to_openai(request, res)
        return result

    async def completion(
        self, request: OpenAIRequest
    ) -> Union[OpenAIResponse, AsyncIterator[OpenAIResponse]]:
        """
        Completion Wrapper API
        """
        stream = request.get("stream", False)
        qianfan_request = self.openai_completion_request_to_qianfan(request)
        n = request.get("n", 1)
        if stream:
            return self._completion_stream(n, request, qianfan_request)

        res = await asyncio.gather(
            *[self._comp_client.ado(**qianfan_request) for _ in range(n)]
        )
        result = self.qianfan_completion_response_to_openai(request, res)
        return result

    async def embedding(
        self, request: OpenAIRequest
    ) -> Union[OpenAIResponse, AsyncIterator[OpenAIResponse]]:
        """
        Embedding Wrapper API
        """
        qianfan_request_list = self.convert_openai_embedding_request(request)
        res = await asyncio.gather(
            *[
                self._embed_client.ado(**qianfan_request)
                for qianfan_request in (qianfan_request_list)
            ]
        )

        result = self.qianfan_embedding_response_to_openai(request, res)
        return result

    async def _chat_stream(
        self, n: int, openai_request: OpenAIRequest, qianfan_request: QianfanRequest
    ) -> AsyncIterator[OpenAIResponse]:
        """
        Convert multiple qianfan response stream into one openai response stream.
        """

        async def task(n: int) -> AsyncIterator[Tuple[int, QfResponse]]:
            res_stream = await self._chat_client.ado(**qianfan_request)
            assert isinstance(res_stream, AsyncIterator)
            async for res in res_stream:
                yield (n, res)

        tasks = [task(i) for i in range(n)]
        results = merge_async_iters(*tasks)
        base = None
        async for i, res in results:
            if base is None:
                base = {
                    "id": res["id"],
                    "created": res["created"],
                    "model": openai_request["model"],
                    "system_fingerprint": "fp_?",
                    "object": "chat.completion.chunk",
                }
                for j in range(n):
                    yield {
                        "choices": [
                            {
                                "index": j,
                                "delta": {"role": "assistant", "content": ""},
                                "logprobs": None,
                                "finish_reason": None,
                            }
                        ],
                        **base,
                    }
            choices: List[Dict] = [
                {
                    "index": i,
                    "delta": {"content": res["result"]},
                    "logprobs": None,
                    "finish_reason": (
                        None
                        if not res["is_end"]
                        else res.get("finish_reason", "normal")
                    ),
                }
            ]
            if "function_call" in res and (
                "functions" in openai_request or "tools" in openai_request
            ):
                choices[0]["delta"]["tool_calls"] = [
                    {
                        "index": 0,
                        "id": res["function_call"]["name"],
                        "type": "function",
                        "function": res["function_call"],
                    }
                ]

                choices[0]["delta"]["content"] = None
                choices[0]["delta"]["finish_reason"] = "tool_calls"
                choices[0]["delta"]["function_call"] = res["function_call"]

            yield {
                "choices": choices,
                **base,
            }

    async def _completion_stream(
        self, n: int, openai_request: OpenAIRequest, qianfan_request: QianfanRequest
    ) -> AsyncIterator[OpenAIResponse]:
        """
        Convert multiple qianfan response stream into one openai response stream.
        """

        async def task(n: int) -> AsyncIterator[Tuple[int, QfResponse]]:
            res_stream = await self._comp_client.ado(**qianfan_request)
            assert isinstance(res_stream, AsyncIterator)
            async for res in res_stream:
                yield (n, res)

        tasks = [task(i) for i in range(n)]
        results = merge_async_iters(*tasks)
        base = None
        async for i, res in results:
            if base is None:
                base = {
                    "id": res["id"],
                    "created": res["created"],
                    "model": openai_request["model"],
                    "system_fingerprint": "fp_?",
                    "object": "text_completion",
                }
                for j in range(n):
                    yield {
                        "choices": [
                            {
                                "index": j,
                                "delta": {"text": ""},
                                "logprobs": None,
                                "finish_reason": None,
                            }
                        ],
                        **base,
                    }
            choices = [
                {
                    "index": i,
                    "delta": {"text": res["result"]},
                    "logprobs": None,
                    "finish_reason": (
                        None if not res["is_end"] else res["finish_reason"]
                    ),
                }
            ]

            yield {
                "choices": choices,
                **base,
            }
