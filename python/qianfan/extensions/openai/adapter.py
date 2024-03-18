import asyncio
from typing import Any, Dict, List, Optional

import qianfan

model_map = {
    "gpt-3.5-turbo": "ERNIE-Speed",
    "gpt-4": "ERNIE-Bot-4",
    "gpt-4-turbo": "ERNIE-Bot",
}


def merge_async_iters(*aiters):
    queue = asyncio.Queue(1)
    run_count = len(aiters)
    cancelling = False

    async def drain(aiter):
        nonlocal run_count
        try:
            async for item in aiter:
                await queue.put((False, item))
        except Exception as e:
            if not cancelling:
                await queue.put((True, e))
            else:
                raise
        finally:
            run_count -= 1

    async def merged():
        try:
            while run_count:
                raised, next_item = await queue.get()
                if raised:
                    cancel_tasks()
                    raise next_item
                yield next_item
        finally:
            cancel_tasks()

    def cancel_tasks():
        nonlocal cancelling
        cancelling = True
        for t in tasks:
            t.cancel()

    tasks = [asyncio.create_task(drain(aiter)) for aiter in aiters]
    return merged()


class OpenAIApdater(object):
    def __init__(self):
        self._chat_client = qianfan.ChatCompletion()

    @classmethod
    def convert_openai_request_base(cls, openai_request: Dict[str, Any]):
        qianfan_request = {}

        def add_if_exist(openai_key: str, qianfan_key: Optional[str] = None):
            qianfan_key = openai_key if qianfan_key is None else qianfan_key
            if openai_key in openai_request:
                qianfan_request[qianfan_key] = openai_request[openai_key]

        add_if_exist("max_tokens", "max_output_tokens")
        add_if_exist("response_format")
        add_if_exist("top_p")
        add_if_exist("stop")
        add_if_exist("stream")
        add_if_exist("functions")
        add_if_exist("function_call", "tool_choice")
        add_if_exist("tools", "functions")
        add_if_exist("user", "user_id")

        model = openai_request["model"]
        if model in model_map:
            model = model_map[model]
        qianfan_request["model"] = model

        if "presence_penalty" in openai_request:
            penalty = openai_request["presence_penalty"]
            # [-2, 2] -> [-0.5, 0.5] -> [1, 2]
            penalty = penalty / 4 + 1.5
            qianfan_request["penalty_score"] = penalty
        if "temperature" in openai_request:
            qianfan_request["temperature"] = openai_request["temperature"] / 2
        if "stop" in openai_request:
            stop = openai_request["stop"]
            if isinstance(stop, str):
                stop = [stop]
            qianfan_request["stop"] = stop
        return qianfan_request

    @classmethod
    def convert_openai_chat_request(cls, openai_request: Dict[str, Any]):
        qianfan_request = cls.convert_openai_request_base(openai_request)
        messages = openai_request["messages"]
        if messages[0]["role"] == "system":
            qianfan_request["system"] = messages[0]["content"]
            messages = messages[1:]
        qianfan_request["messages"] = messages
        return qianfan_request

    @classmethod
    def convert_openai_completion_request(cls, openai_request: Dict[str, Any]):
        qianfan_request = cls.convert_openai_request_base(openai_request)
        qianfan_request["prompt"] = openai_request["prompt"]
        return qianfan_request

    @classmethod
    def convert_qianfan_chat_response(
        cls, openai_request, qianfan_response_list: List[Dict[str, Any]]
    ):
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
                "finish_reason": resp["finish_reason"],
            }
            if "function_call" in resp:
                if "function_call" in openai_request:
                    choice["message"]["function_call"] = resp["function_call"]
                if "tool_choice" in openai_request:
                    choice["message"]["tool_calls"] = resp["function_call"]
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

    async def chat(self, request):
        stream = request.get("stream", False)
        qianfan_request = self.convert_openai_chat_request(request)
        n = request.get("n", 1)
        if stream:
            return self._chat_stream(n, request, qianfan_request)

        res = await asyncio.gather(
            *[self._chat_client.ado(**qianfan_request) for _ in range(n)]
        )
        result = self.convert_qianfan_chat_response(request, res)
        return result

    async def _chat_stream(self, n, openai_request, qianfan_request):
        async def task(n):
            print(qianfan_request)
            async for res in await self._chat_client.ado(**qianfan_request):
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
            choices = [
                {
                    "index": i,
                    "delta": {"content": res["result"]},
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
