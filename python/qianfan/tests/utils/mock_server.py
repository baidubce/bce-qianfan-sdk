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

"""
    Mock server for unit test
"""
import io

# disable line too long lint error in this file
# ruff: noqa: E501
import json
import random
import threading
import time
import zipfile
from datetime import datetime, timedelta, timezone
from functools import wraps
from io import BytesIO

import flask
import requests
from flask import Flask, request, send_file

from qianfan.consts import APIErrorCode, Consts
from qianfan.resources.console import consts as console_consts
from qianfan.utils.utils import generate_letter_num_random_id

app = Flask(__name__)

STREAM_COUNT = 3


def merge_messages(messages):
    """
    merge mulitple input messages
    """
    return "|".join([m.get("content", "") for m in messages])


def ret_msg(model, extra_msg=""):
    """
    mock the return message
    """
    return f"model `{model}` is answering, received message: `{extra_msg}`"


def completion_stream_response(model, prompt=""):
    """
    mock stream response
    """
    for i in range(0, STREAM_COUNT):
        is_end = i == STREAM_COUNT - 1
        yield "data: " + json.dumps(
            {
                "id": "as-9092ws9jgh",
                "object": "completion",
                "created": 1693811126,
                "sentence_id": 0,
                "is_end": is_end,
                "result": ret_msg(model, str(i) + prompt),
                "is_safe": 1,
                "usage": {
                    "prompt_tokens": 5,
                    "completion_tokens": 67,
                    "total_tokens": 72,
                },
                "_for_ut": {
                    "model": model,
                    "turn": i,
                    "stream": True,
                    "type": "completion",
                },
            }
        ) + "\n\n"


def json_response(data, request_id=None, status_code=200):
    """
    wrapper of the response
    """
    request_body = request.get_data().decode("utf-8")
    try:
        request_body = request.json
    except Exception:
        pass
    resp = flask.Response(
        json.dumps(
            {
                **data,
                "_request": request_body,
                "_params": request.args,
                "_header": dict(request.headers),
            }
        ),
        headers={
            "X-Ratelimit-Limit-Tokens": 300000,
            "X-Ratelimit-Limit-Requests": 3000,
        },
        mimetype="application/json",
        status=status_code,
    )
    if request_id is not None:
        resp.headers[Consts.XResponseID] = request_id
    return resp


def chat_completion_stream_response(model, messages):
    """
    mock stream chat response
    """
    for i in range(0, STREAM_COUNT):
        is_end = i == STREAM_COUNT - 1
        yield "data: " + json.dumps(
            {
                "id": "as-ywwpgx4dt7",
                "object": "chat.completion",
                "created": 1680166793,
                "sentence_id": 0,
                "is_end": is_end,
                "is_truncated": False,
                "result": ret_msg(model, str(i) + merge_messages(messages)),
                "need_clear_history": False,
                "usage": {
                    "prompt_tokens": 11,
                    "completion_tokens": 16,
                    "total_tokens": 27,
                },
                "_for_ut": {"model": model, "turn": i, "stream": True, "type": "chat"},
            }
        ) + "\n\n"


def chat_completion_stream_response_v2(model, messages):
    """
    mock stream chat response
    """
    for i in range(0, STREAM_COUNT):
        is_end = i == STREAM_COUNT - 1
        yield "data: " + json.dumps(
            {
                "id": "as-5j1w2wzna2",
                "object": "chat.completion",
                "created": 1717488564,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "content": ret_msg(model, str(i) + merge_messages(messages))
                        },
                        "is_end": is_end,
                        "need_clear_history": False,
                        # "finish_reason": "normal",
                    }
                ],
                "usage": {
                    "prompt_tokens": 2,
                    "completion_tokens": 0,
                    "total_tokens": 2,
                },
                "_for_ut": {
                    "model": model,
                    "turn": i,
                    "stream": True,
                    "type": "chatv2",
                },
            }
        ) + "\n\n"
    yield "data: [DONE]\n\n"


def check_messages(messages):
    """
    check whether the received messages are valid
    """
    if len(messages) % 2 != 1:
        return {
            "error_code": APIErrorCode.InvalidParam.value,
            "error_msg": "messages length must be odd",
        }
    for i, m in enumerate(messages):
        if (i % 2 == 0 and m["role"] != "user") or (
            i % 2 == 1 and m["role"] != "assistant"
        ):
            return {
                "error_code": APIErrorCode.InvalidParam.value,
                "error_msg": f"invalid role in message {i}",
            }
    return None


def check_messages_v2(messages):
    """
    check whether the received messages are valid
    """
    if len(messages) % 2 != 1:
        return {
            "error": {
                "code": "invalid_argument",
                "message": "the length of messages must be an odd number",
            },
            "id": "as-qdb51n76w1",
        }
    for i, m in enumerate(messages):
        if (i % 2 == 0 and m["role"] != "user") or (
            i % 2 == 1 and m["role"] != "assistant"
        ):
            return {
                "error": {
                    "code": "invalid_argument",
                    "message": f"invalid role in message {i}",
                },
                "id": "as-qdb51n76w1",
            }

    return None


def access_token_checker(func):
    """
    decorator for checking access token
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        wrapper for function
        if "expired" in access_token, return token expired error
        """
        # openapi also supports iam auth
        bce_date = request.headers.get("x-bce-date")
        authorization = request.headers.get("authorization")

        if bce_date is None or authorization is None:
            # if iam auth credentail is not provided, check access token
            access_token = request.args.get("access_token")
            if access_token is None:
                return json_response(
                    {
                        "error_code": 110,
                        "error_msg": "Access token invalid or no longer valid",
                    }
                )
            if "expired" in access_token:
                return json_response(
                    {
                        "error_code": 111,
                        "error_msg": "Access token expired",
                    }
                )
        try:
            # if "_delay" in request.json, sleep for a while
            # this argument is for unit test
            # if not exists, do nothing
            delay = request.json["_delay"]
            time.sleep(delay)
        except Exception:
            pass
        return func(*args, **kwargs)

    return wrapper


def iam_v3_auth_checker(func):
    """
    decorator for checking bearer token
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        wrapper for function
        """
        authorization = request.headers.get("authorization")
        if not authorization.startswith("Bearer"):
            return flask.Response(
                status=403,
                headers={
                    "X-Bce-Error-Message": (
                        "mock server error, authorization or bce_date not found"
                    )
                },
            )
        return func(*args, **kwargs)

    return wrapper


def iam_auth_checker(func):
    """
    decorator for checking access token
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        wrapper for function
        if "expired" in access_token, return token expired error
        """
        bce_date = request.headers.get("x-bce-date")
        authorization = request.headers.get("authorization")
        if bce_date is None or authorization is None:
            return flask.Response(
                status=403,
                headers={
                    "X-Bce-Error-Message": (
                        "mock server error, authorization or bce_date not found"
                    )
                },
            )
        return func(*args, **kwargs)

    return wrapper


def truncated_stream_response(is_end_resp: bool):
    """
    mock stream chat response
    """

    if is_end_resp:
        data = json.dumps(
            {
                "id": "as-ywwpgx4dt7",
                "object": "chat.completion",
                "created": 1680166793,
                "sentence_id": 0,
                "is_end": True,
                "is_truncated": False,
                "result": "==end",
                "need_clear_history": False,
                "usage": {
                    "prompt_tokens": 11,
                    "completion_tokens": 16,
                    "total_tokens": 27,
                },
            }
        )
        yield "data: " + data + "\n\n"
    else:
        for i in range(0, STREAM_COUNT):
            is_end = i == STREAM_COUNT - 1
            data = json.dumps(
                {
                    "id": "as-ywwpgx4dt7",
                    "object": "chat.completion",
                    "created": 1680166793,
                    "sentence_id": 0,
                    "is_end": is_end,
                    "is_truncated": True,
                    "result": "truncated_" + str(i),
                    "need_clear_history": False,
                    "usage": {
                        "prompt_tokens": 11,
                        "completion_tokens": 16,
                        "total_tokens": 27,
                    },
                    "_for_ut": {
                        "model": "truncated",
                        "turn": i,
                        "stream": True,
                        "type": "chat",
                    },
                }
            )
            yield "data: " + data + "\n\n"


_multi_func_call_round = 0


@app.route(Consts.ModelAPIPrefix + "/chat/<model_name>", methods=["POST"])
@access_token_checker
def chat(model_name):
    """
    mock /chat/<model_name> chat completion api
    """
    r = request.json
    request_header = request.headers
    request_id = request_header.get(Consts.XRequestID)
    if model_name.startswith("test_retry"):
        global retry_cnt
        if model_name not in retry_cnt:
            retry_cnt[model_name] = 1
        if retry_cnt[model_name] % 3 != 0:
            # need retry
            retry_cnt[model_name] = (retry_cnt[model_name] + 1) % 3
            return json_response(
                {
                    "error_code": 336100,
                    "error_msg": "high load",
                }
            )
    if request_id == "custom_req":
        return json_response(
            {
                "id": "as-bcmt5ct4id",
                "object": "chat.completion",
                "created": 1680167072,
                "result": "-->end of truncated]",
                "is_truncated": False,
                "need_clear_history": False,
                "usage": {
                    "prompt_tokens": 7,
                    "completion_tokens": 67,
                    "total_tokens": 74,
                },
                "_for_ut": {
                    "model": "truncated",
                    "turn": None,
                    "stream": False,
                    "type": "chat",
                },
            },
            request_id,
        )
    if model_name == "ernie-func-8k":
        global _multi_func_call_round
        _multi_func_call_round += 1
        if _multi_func_call_round == 1:
            ans = 'Action: get_current_weather\nAction Input: {"location": "上海市"}'
        else:
            _multi_func_call_round = 0
            ans = "上海气温25度"

        if r.get("stream"):
            return flask.Response(
                chat_completion_stream_response(
                    model_name, [{"role": "assistant", "content": ans}]
                ),
                mimetype="text/event-stream",
            )
        else:
            return json_response(
                {
                    "id": "as-bcmt5ct4ie",
                    "object": "chat.completion",
                    "created": 1680167075,
                    "result": ans,
                    "is_truncated": False,
                    "need_clear_history": False,
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 72,
                        "total_tokens": 82,
                    },
                },
                request_id,
            )
    # check messages
    check_result = check_messages(r["messages"])
    if model_name == "error":
        return json_response(
            {
                "error_code": 3,
                "error_msg": "Unsupported openapi method",
            }
        )
    if model_name == "truncated":
        # stream
        if "stream" in r and r["stream"]:
            return flask.Response(
                truncated_stream_response(
                    len(r["messages"]) >= 1 and r["messages"][-1]["content"] == "继续"
                ),
                mimetype="text/event-stream",
            )
        # not stream
        if len(r["messages"]) >= 1 and r["messages"][-1]["content"] == "继续":
            # continue answer is_truncated=`False`
            return json_response(
                {
                    "id": "as-bcmt5ct4id",
                    "object": "chat.completion",
                    "created": 1680167072,
                    "result": "-->end of truncated]",
                    "is_truncated": False,
                    "need_clear_history": False,
                    "usage": {
                        "prompt_tokens": 7,
                        "completion_tokens": 67,
                        "total_tokens": 74,
                    },
                    "_for_ut": {
                        "model": "truncated",
                        "turn": None,
                        "stream": False,
                        "type": "chat",
                    },
                }
            )

        return json_response(
            {
                "id": "as-bcmt5ct4id",
                "object": "chat.completion",
                "created": 1680167072,
                "result": "[begin truncate",
                "is_truncated": True,
                "need_clear_history": False,
                "usage": {
                    "prompt_tokens": 7,
                    "completion_tokens": 67,
                    "total_tokens": 74,
                },
                "_for_ut": {
                    "model": "truncated",
                    "turn": None,
                    "stream": False,
                    "type": "chat",
                },
            }
        )
    if "functions" not in r and check_result is not None:
        return json.dumps(check_result)
    if "stream" in r and r["stream"]:
        return flask.Response(
            chat_completion_stream_response(model_name, r["messages"]),
            mimetype="text/event-stream",
        )
    if "functions" in r:
        if len(r["messages"]) == 1:
            return json_response(
                {
                    "id": "as-rtpw9dcmef",
                    "object": "chat.completion",
                    "created": 1693449832,
                    "sentence_id": 0,
                    "is_end": True,
                    "is_truncated": False,
                    "result": "",
                    "need_clear_history": False,
                    "function_call": {
                        "name": (
                            "paper_search"
                            if r["functions"][0]["name"] == "paper_search"
                            else "tool_selection"
                        ),
                        "thoughts": "用户提到了搜索论文，需要搜索论文来返回结果",
                        "arguments": (
                            '{"__arg1":"physics"}'
                            if r["functions"][0]["name"] == "paper_search"
                            else (
                                '{"actions": [{"action": "paper_search",'
                                ' "query":"physics"}]}'
                            )
                        ),
                    },
                    "is_safe": 0,
                    "usage": {
                        "prompt_tokens": 8,
                        "completion_tokens": 46,
                        "total_tokens": 54,
                    },
                }
            )
        else:
            return json_response(
                {
                    "id": "as-kf6e9thk0f",
                    "object": "chat.completion",
                    "created": 1693450180,
                    "sentence_id": 0,
                    "is_end": True,
                    "is_truncated": False,
                    "result": "测试成功",
                    "need_clear_history": False,
                    "is_safe": 0,
                    "usage": {
                        "prompt_tokens": 26,
                        "completion_tokens": 8,
                        "total_tokens": 42,
                    },
                }
            )
    if "tools" in r and r["messages"][0]["content"] != "no_search":
        return json_response(
            {
                "id": "as-wfhb6enh7c",
                "object": "chat.completion",
                "created": 1703228415,
                "result": (
                    "**上海今天天气是晴转阴，气温在-4℃到1℃之间，风向无持续风向，"
                    "风力小于3级，空气质量优**^[1]^。"
                ),
                "is_truncated": False,
                "need_clear_history": False,
                "usage": {
                    "prompt_tokens": 3,
                    "completion_tokens": 40,
                    "total_tokens": 1434,
                    "tool_tokens": 1391,
                    "tool_usage": [
                        {
                            "name": "baidu_search",
                            "tool_point": 8000,
                            "baidu_search": {"triggers_number": 1},
                        }
                    ],
                },
                "tools_info": {
                    "name": "baidu_search",
                    "rewrite_query": "上海今天天气",
                    "baidu_search": [
                        {
                            "index": 1,
                            "url": "http://www.weather.com.cn/weather/101020100.shtml",
                            "title": "上海天气预报_一周天气预报",
                        },
                        {
                            "index": 2,
                            "url": "https://m.tianqi.com/shanghai/15/",
                            "title": "上海天气预报15天_上海天气预报15天查询,上海未来15天天 ...",
                        },
                    ],
                },
            }
        )
    return json_response(
        {
            "id": "as-bcmt5ct4iy",
            "object": "chat.completion",
            "created": 1680167072,
            "result": ret_msg(model_name, merge_messages(r["messages"])),
            "is_truncated": False,
            "need_clear_history": False,
            "usage": {
                "prompt_tokens": 7,
                "completion_tokens": 67,
                "total_tokens": 74,
            },
            "_for_ut": {
                "model": model_name,
                "turn": None,
                "stream": False,
                "type": "chat",
            },
        }
    )


history_tokens = {}


@app.route(Consts.IAMBearerTokenAPI, methods=["GET"])
def iam_get_bearer_token():
    expire_seconds = request.args.get("expireInSeconds")
    current_time = datetime.now(timezone.utc)
    # 加上 100 秒
    expire_time = current_time + timedelta(seconds=int(expire_seconds))

    # 格式化为指定格式
    current_time_str = current_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    expire_time_str = expire_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    token = f"bce-v3/ALTAK-XNYpvSpWTC0Qr0cB6LoZR/{generate_letter_num_random_id(16)}"
    global history_tokens
    history_tokens[token] = expire_time

    return json_response(
        {
            "userId": "6c6093c96f0241c087af184cc5729de8",
            "token": token,
            "status": "enable",
            "createTime": current_time_str,
            "expireTime": expire_time_str,
        },
    )


@app.route(Consts.ChatV2API, methods=["POST"])
@iam_v3_auth_checker
def chat_v2():
    """
    mock chat completion v2 api
    """
    r = request.json
    request_header = request.headers
    request_id = request_header.get(Consts.XRequestID)
    model_name = r["model"]
    if model_name.startswith("test_retry"):
        global retry_cnt
        if model_name not in retry_cnt:
            retry_cnt[model_name] = 1
        if retry_cnt[model_name] % 3 != 0:
            # need retry
            retry_cnt[model_name] = (retry_cnt[model_name] + 1) % 3
            return json_response(
                {
                    "error": {
                        "code": "internal_error",
                        "message": "high load",
                    }
                }
            )
    check_result = check_messages_v2(r["messages"])
    if check_result is not None:
        return json_response(check_result, status_code=400)
    if model_name == "error":
        return json_response(
            {
                "error": {
                    "code": "invalid_model",
                    "message": "No permission to use the model",
                }
            },
            status_code=400,
        )
    if "stream" in r and r["stream"]:
        return flask.Response(
            chat_completion_stream_response_v2(model_name, r["messages"]),
            mimetype="text/event-stream",
        )

    return json_response(
        {
            "id": "as-sq01fe52em",
            "object": "chat.completion",
            "created": 1717487283,
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": ret_msg(model_name, merge_messages(r["messages"])),
                    },
                    "need_clear_history": False,
                }
            ],
            "usage": {"prompt_tokens": 2, "completion_tokens": 21, "total_tokens": 23},
            "_for_ut": {
                "model": model_name,
                "turn": None,
                "stream": False,
                "type": "chatv2",
            },
        },
        request_id=request_id,
    )


retry_cnt = {}


@app.route(Consts.ModelAPIPrefix + "/completions/<model_name>", methods=["POST"])
@access_token_checker
def completions(model_name):
    """
    mock /completions/<model_name> completion api
    """
    if model_name == "error":
        return json_response(
            {
                "error_code": 3,
                "error_msg": "Unsupported openapi method",
            }
        )
    if model_name.startswith("test_retry"):
        global retry_cnt
        if model_name not in retry_cnt:
            retry_cnt[model_name] = 1
        if retry_cnt[model_name] % 3 != 0:
            # need retry
            retry_cnt[model_name] = (retry_cnt[model_name] + 1) % 3
            return json_response(
                {
                    "error_code": 336100,
                    "error_msg": "high load",
                }
            )
    r = request.json
    if "stream" in r and r["stream"]:
        return flask.Response(
            completion_stream_response(model_name, r["prompt"]),
            mimetype="text/event-stream",
        )
    # check messages
    return json_response(
        {
            "id": "as-rq3wwusja8",
            "object": "completion",
            "created": 1693811110,
            "result": ret_msg(model_name, r["prompt"]),
            "is_safe": 1,
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 92,
                "total_tokens": 97,
            },
            "_for_ut": {
                "model": model_name,
                "turn": None,
                "stream": False,
                "type": "completion",
            },
        }
    )


def random_embedding():
    """
    generate random embedding value
    """
    return [random.uniform(0, 1) for _ in range(384)]


@app.route(Consts.ModelAPIPrefix + "/embeddings/<model_name>", methods=["POST"])
@access_token_checker
def embedding(model_name):
    """
    mock /embeddings/<model_name> embedding api
    """
    if model_name == "error":
        return json_response(
            {
                "error_code": 3,
                "error_msg": "Unsupported openapi method",
            }
        )
    r = request.json
    input_len = len(r["input"])
    data = [
        {
            "object": "embedding",
            "embedding": random_embedding(),
            "index": i,
        }
        for i in range(input_len)
    ]
    # check messages
    return json_response(
        {
            "id": "as-gjs275mj6s",
            "object": "embedding_list",
            "created": 1687155816,
            "data": data,
            "usage": {"prompt_tokens": 12, "total_tokens": 12},
            "_for_ut": {"model": model_name, "type": "embedding", "stream": False},
        }
    )


@app.route(Consts.ModelAPIPrefix + "/text2image/<model_name>", methods=["POST"])
@access_token_checker
def text2image(model_name):
    """
    mock /text2image/<model_name> text2image api
    """

    return json_response(
        {
            # mock data 64*64
            "id": "as-sq9n2bm0pa",
            "object": "image",
            "created": 1698278344,
            "data": [
                {
                    "object": "image",
                    "b64_image": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQgJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCABAAEADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwBz4MtwG6bK5jxDaXUwgEFvNMqA5MUbPjPToK6VjmaTPIKf0rmdf1jUdNFvLYXstr5hIbyiOcDgHINc8Pi0LlscpcW10pO+zu0/3raQfzWs+YiM/Odmf7/y/wA66RPHfiWPI/teWTHZ0jP/ALLT/wDhYfiLo89nIP8AbtFP9a3uY6FXwXse+1BtwIMcUWRz95//AK1dpdIU1e0BBAVQAPT/ACax/DXiG+8RX8n2mK0RYGQloIPLJ69eTnpW3dENrse0ludv06VlPc0iVJ5NrXBz/Fj/AMerqfDN1ALBHeWNN/zfMwFcvPH8srkE4V2Az3zisCa2DFsqOirnHTkVkzRHoraPcxqZH2M+NuAfesLWfBGq6xbxLafZ42Ry5WaQqOh6YBrq7e4a7cJCSWH3mBzj8a24I/IGMknHOazVRo6HRizwW68G+JoH8ufTZj5ZKqVeMqRnqDuGR+v0qm3hTX9pH9mXPT5fmj/X5q+i3CSRlHUMp6giqL6dBjKRKD1wQK2VbuYSodjxrwrYS6DaX8t8DBcsyL5bkZ2gg7sA89WrpnZRrSYPIkzk98qOa7c2i7d32dCPZRULR2zjDwRkehUVTalsZ2cdzjZSjx7UYYON3H6VSdEeaROMbgMevIrvitv2hj/75FU79IBCAIowWIAO0eoqRpnIagGgvEjdZmtwAQikkfUjPJrW0/xXHpqrG0+9ef3MkmWH05OK7G3trKxy9rZQxo3DIV2sD7Z/+tTZLjTbmGaFBBJwQy7RvX6r/Ws3JbNG6g90ypomvtqsgjk8uMyfdA6r/jWwEFq+Li+Vy3TICj8PWvOdLSeLVxYRDM5YhIx069c/Suj8W2F0mnwJuE8jAhlU4CHHDf8A161UY2vYzlKV7XN03Nq8+wXBGOOoAzSXejzP+9imDZHQjH8q4ew0e6ikjiuZ/tMjj/W7wEx7DJNeiWty8FnFG2x34XIPGP8AGhJLUTbejMOTT72MZZM/7uDWfc208uwqRlGBwe9dXFdQm7myxRI+oJ4z3Of89KqXl5p8t1HEgbzJOjohZfbcR0+prNTvuayo22HFEP8AAv5VG9nbyHLwRs3qVGaf5iA/eH504TRAcyA1tYxuVbPSrawvWvLVPLnZdrN14znv0qpH4dVdSmv5NQvZpZSd6yMu0j+7gDoOmP8A69av2mL+9n8KT7ZCOpP5UWWwX6labQ7C4XDwn1BVypH0IqeDSrOBtyo5b1aVif5077fAPU/hSf2jEOitSsgu2WHtIJVKvEGUjBB6GkSxtY2LJAisRjIHb0qD+01/hQ0f2of+eRosguz/2Q==",
                    "index": 1,
                }
            ],
            "usage": {"prompt_tokens": 8, "total_tokens": 8},
        }
    )


@app.route(Consts.ModelAPIPrefix + "/image2text/<model_name>", methods=["POST"])
@access_token_checker
def image2text(model_name):
    """
    mock /image2text/<model_name> image2text api
    """
    r = request.json
    if "stream" in r and r["stream"]:
        return flask.Response(
            completion_stream_response(model_name, r["prompt"]),
            mimetype="text/event-stream",
        )
    return json_response(
        {
            "id": "as-th7f8y0ckj",
            "object": "chat.completion",
            "created": 1702964273,
            "result": (
                "The image depicts a dining table with multiple bowls, containing"
                " various food items, including  rice and meat. The bowl s are placed"
                " on different sides of the table, and chopsticks can be seen placed"
                " near the bowls. In addition to the bowl s, there are two spoons, one"
                " closer to the  left side of the table and the other towards the"
                " center. The table is also accompanied by a cup , placed at the top"
                " left corner."
            ),
            "is_safe": 1,
            "usage": {"prompt_tokens": 3, "completion_tokens": 98, "total_tokens": 101},
        }
    )


@app.route(Consts.EBTokenizerAPI, methods=["POST"])
@access_token_checker
def eb_tokenizer():
    """
    mock prompt render api
    """
    prompt = request.json["prompt"]
    return json_response(
        {
            "id": "as-biv9bzt19n",
            "object": "tokenizer.erniebot",
            "created": 1698655037,
            "usage": {
                "prompt_tokens": 97575 + len(
                    prompt
                ),  # magic number for eb tokenizer api,
                "total_tokens": 97575 + len(
                    prompt
                ),  # magic number for eb tokenizer api
            },
        }
    )


def fake_access_token(ak: str, sk: str) -> str:
    """
    generate fake access token
    """
    return f"{ak}.{sk}"


@app.route(Consts.AuthAPI, methods=["POST"])
def auth():
    """
    mock auth api
    """
    grant_type = request.args.get("grant_type")
    if grant_type != "client_credentials":
        print(grant_type)
        return json_response(
            {"error_description": "unknown client id", "error": "invalid_client"}
        )
    ak = request.args.get("client_id")
    sk = request.args.get("client_secret")
    if "bad" in sk:
        return json_response(
            {
                "error_description": "Client authentication failed",
                "error": "invalid_client",
            }
        )
    # check messages
    return json_response(
        {
            "refresh_token": "25.a7c83604448xxxxx-33345604",
            "expires_in": 2592000,
            "session_key": "9mzdDtAOJUlG5lZxxxxxFwwO7hTmMQ==",
            "access_token": fake_access_token(ak, sk),
            "scope": (
                "ai_custom_yiyan_com_eb_instant license_license"
                " ai_custom_retail_image_stitch easydl_pro_job xxxxx"
            ),
            "session_secret": "6a29xxxxx671cc",
        }
    )


finetune_task_call_times = {}


@app.route(Consts.FineTuneCreateTaskAPI, methods=["POST"])
@iam_auth_checker
def create_finetune_task():
    """
    mock create finetune task api
    """
    r = request.json
    return json_response(
        {
            "log_id": "123456789",
            "result": {
                "id": random.randint(0, 100000),
                "uuid": "job-xxxx",
                "name": r["name"],
                "description": "" if "description" not in r else r["description"],
                "createTime": "2023-09-07 11:11:11",
            },
        }
    )


@app.route(Consts.ModelV2BaseRouteAPI, methods=["POST"])
def model_v2():
    action = request.args.get(Consts.ConsoleAPIQueryAction)
    json_body = request.json
    action_handler = {
        Consts.ModelDescribeModelSetAction: model_v2_model_set_detail,
    }
    return action_handler.get(action)(body=json_body)


def model_v2_model_set_detail(body):
    return {
        "requestId": "fe0268a7-0d07-46ac-b195-36ca5be2d761",
        "result": {
            "modelSetId": "am-m0t1zde3x111",
            "modelSetName": "ad111",
            "source": "UserCreate",
            "modelType": "Text2Text",
            "createTime": "2024-06-04T18:38:59+08:00",
            "modifyTime": "2024-06-04T18:38:59+08:00",
            "modelIds": ["amv-34qkndzjf111"],
        },
    }


@app.route(Consts.FineTuneV2BaseRouteAPI, methods=["POST"])
def finetune_v2():
    action = request.args.get(Consts.ConsoleAPIQueryAction)
    json_body = request.json
    action_handler = {
        Consts.FineTuneCreateJobAction: finetune_v2_create_job,
        Consts.FineTuneCreateTaskAction: finetune_v2_create_task,
        Consts.FineTuneJobListAction: finetune_v2_job_list,
        Consts.FineTuneTaskListAction: finetune_v2_task_list,
        Consts.FineTuneTaskDetailAction: finetune_v2_task_detail,
        Consts.FineTuneStopTaskAction: finetune_v2_stop_task,
        Consts.FineTuneSupportedModelsAction: finetune_v2_supported_models,
    }
    return action_handler.get(action)(body=json_body)


MockFailedJobId = "job-failedone"
MockFailedTaskId = "task-failedone"


def finetune_v2_create_job(body):
    job_id = f"job-{generate_letter_num_random_id(12)}"
    if body["name"] == "mock_failed_task":
        job_id = MockFailedJobId
    return json_response(
        {
            "requestId": "98d2e3d7-a689-4255-91f1-da514a3a5777",
            "result": {"jobId": job_id},
        }
    )


def finetune_v2_create_task(body):
    task_id = f"task-{generate_letter_num_random_id(12)}"
    job_id = body["jobId"]
    split_ratio = body.get("datasetConfig", {}).get("splitRatio")
    if split_ratio is None or split_ratio < 0 or split_ratio > 100:
        return json_response(
            {
                "requestId": "bfad9ba9-9fc2-406d-ae84-c9e1ea92140a",
                "code": "InappropriateJSON",
                "message": (
                    "The JSON you provided was well-formed and valid, but not"
                    " appropriate for this operation. param[splitRatio] invalid."
                ),
            },
            status_code=400,
        )
    if job_id == MockFailedJobId:
        task_id = MockFailedTaskId
    global finetune_task_call_times
    finetune_task_call_times[task_id] = 0
    return json_response(
        {
            "requestId": "aac33135-aed1-416a-8070-c6ecde325df5",
            "result": {"jobId": job_id, "taskId": task_id},
        }
    )


def finetune_v2_job_list(body):
    return json_response(
        {
            "requestId": "f17326a0-91fd-404c-a9bc-db586166893e",
            "result": {
                "jobList": [
                    {
                        "jobId": "job-b7hmiwmptntt",
                        "name": "ebspda2",
                        "description": "",
                        "model": "ERNIE-Speed",
                        "trainMode": "PostPretrain",
                        "createDate": "2024-01-29T16:24:32Z",
                    },
                    {
                        "jobId": "job-yhddtcbesggz",
                        "name": "0129_yige",
                        "description": "",
                        "model": "WENXIN-YIGE",
                        "trainMode": "SFT",
                        "createDate": "2024-01-29T14:39:04Z",
                    },
                ],
                "pageInfo": {
                    "marker": "",
                    "maxKeys": 20,
                    "isTruncated": True,
                    "nextMarker": "job-afik6nqipgnq",
                },
            },
        }
    )


def finetune_v2_task_list(body):
    return json_response(
        {
            "requestId": "eb3de810-3b21-4737-957f-ffd971a5610f",
            "result": {
                "pageInfo": {"marker": "", "maxKeys": 100, "isTruncated": False},
                "taskList": [
                    {
                        "taskId": "task-92zjbyinxruq",
                        "jobId": body["jobId"],
                        "jobName": "hj_pptr",
                        "jobDescription": "",
                        "model": "ERNIE-Speed",
                        "trainMode": "PostPretrain",
                        "parameterScale": "FullFineTuning",
                        "runStatus": "Running",
                        "createDate": "2024-01-30T09:41:54Z",
                        "finishDate": "0000-00-00T00:00:00Z",
                    }
                ],
            },
        }
    )


def finetune_v2_fail_task_detail():
    return {
        "requestId": "754dc75c-3515-4ddd-88ff-59caaad4358d",
        "result": {
            "taskId": MockFailedJobId,
            "jobId": MockFailedJobId,
            "jobName": "hj_failed",
            "jobDescription": "",
            "model": "ERNIE-Speed",
            "trainMode": "PostPretrain",
            "parameterScale": "FullFineTuning",
            "runStatus": console_consts.TrainStatus.Fail.value,
            "vdlLink": "https://console.bce.baidu.com/qianfan/visualdl/index?displayToken=eyJydW5JZCI6InJ1bi1raXNyYzB4ZWlzcTM4MDgxIn0=",
            "createDate": "2024-01-30T09:41:54Z",
            "finishDate": "0000-00-00T00:00:00Z",
        },
    }


def finetune_v2_task_detail(body):
    r = request.json
    task_id = r["taskId"]
    if task_id == MockFailedTaskId:
        return json_response(finetune_v2_fail_task_detail())
    global finetune_task_call_times
    call_times = finetune_task_call_times.get(task_id)
    if call_times is None:
        finetune_task_call_times[task_id] = 0
        return json_response(
            {
                "requestId": "754dc75c-3515-4ddd-88ff-59caaad4358d",
                "result": {
                    "taskId": task_id,
                    "jobId": "job-s66h7p9gqqu1",
                    "jobName": "hj_pptr",
                    "jobDescription": "",
                    "model": "ERNIE-Speed",
                    "trainMode": "PostPretrain",
                    "parameterScale": "FullFineTuning",
                    "runStatus": console_consts.TrainStatus.Running.value,
                    "runProgress": "0%",
                    "vdlLink": "https://console.bce.baidu.com/qianfan/visualdl/index?displayToken=eyJydW5JZCI6InJ1bi1raXNyYzB4ZWlzcTM4MDgxIn0=",
                    "createDate": "2024-01-30T09:41:54Z",
                    "finishDate": "0000-00-00T00:00:00Z",
                },
            }
        )
    else:
        MAX_CALL_TIMES = 5
        finetune_task_call_times[task_id] += 1
        is_done = call_times >= MAX_CALL_TIMES
        resp = {
            "requestId": "754dc75c-3515-4ddd-88ff-59caaaaaaa",
            "result": {
                "taskId": task_id,
                "jobId": "job-s66h7p9gqqu1",
                "jobName": "hj_pptr",
                "jobDescription": "",
                "model": "ERNIE-Speed",
                "trainMode": "PostPretrain",
                "parameterScale": "FullFineTuning",
                "runStatus": (
                    console_consts.TrainStatus.Finish
                    if is_done
                    else console_consts.TrainStatus.Running.value
                ),
                "vdlLink": "https://console.bce.baidu.com/qianfan/visualdl/index?displayToken=eyJydW5JZCI6InJ1bi1raXNyYzB4ZWlzcTM4MDgxIn0=",
                "createDate": "2024-01-30T09:41:54Z",
                "finishDate": "0000-00-00T00:00:00Z",
            },
        }
        if not is_done:
            resp["result"]["runProgress"] = f"{int(100 * call_times / MAX_CALL_TIMES)}%"
        else:
            resp["result"]["metrics"] = {
                "BLEU-4": "16.56%",
                "ROUGE-1": "27.84%",
                "ROUGE-2": "11.96%",
                "ROUGE-L": "26.02%",
            }
        return json_response(resp)


def finetune_v2_stop_task(body):
    task_id = body.get("taskId", "")
    resp = {"result": False, "requestId": "754dc75c-3515-4ddd-88ff-59caaaaabbbb"}
    if task_id in finetune_task_call_times:
        finetune_task_call_times.pop(task_id)
        resp["result"] = True
    return json_response(resp)


def finetune_v2_supported_models(body):
    return json_response(
        {
            "requestId": "754dc75c-3515-4ddd-88ff-59caaaaabbbb",
            "result": [
                {
                    "model": "ERNIE-Speed-8K",
                    "modelType": "text2text",
                    "supportTrainMode": [
                        {
                            "supportParameterScale": [
                                {
                                    "parameterScale": "FullFineTuning",
                                    "supportHyperParameterConfig": [
                                        {
                                            "key": "epoch",
                                            "type": "int",
                                            "checkType": "range",
                                            "checkValue": [1, 50],
                                            "default": 1,
                                        },
                                        {
                                            "checkType": "range",
                                            "checkValue": [0.0001, 0.1],
                                            "default": 0.01,
                                            "key": "weightDecay",
                                            "type": "float",
                                        },
                                        {
                                            "key": "learningRate",
                                            "type": "float",
                                            "checkType": "range",
                                            "checkValue": [1e-06, 4e-05],
                                            "default": 3e-05,
                                        },
                                    ],
                                },
                                {
                                    "parameterScale": "FullFineTuning",
                                    "supportHyperParameterConfig": [
                                        {
                                            "key": "epoch",
                                            "type": "int",
                                            "checkType": "range",
                                            "checkValue": [1, 50],
                                            "default": 1,
                                        },
                                        {
                                            "checkType": "range",
                                            "checkValue": [0.0001, 0.1],
                                            "default": 0.01,
                                            "key": "custom_key",
                                            "type": "float",
                                        },
                                        {
                                            "key": "learningRate",
                                            "type": "float",
                                            "checkType": "range",
                                            "checkValue": [1e-06, 4e-05],
                                            "default": 3e-05,
                                        },
                                        {
                                            "key": "maxSeqLen",
                                            "type": "int",
                                            "checkType": "choice",
                                            "checkValue": [512, 1024, 2048, 4096, 8192],
                                            "default": 4096,
                                        },
                                    ],
                                },
                                {
                                    "parameterScale": "LoRA",
                                    "supportHyperParameterConfig": [
                                        {
                                            "key": "epoch",
                                            "type": "int",
                                            "checkType": "range",
                                            "checkValue": [1, 50],
                                            "default": 1,
                                        },
                                        {
                                            "checkType": "choice",
                                            "checkValue": ["True", "False"],
                                            "default": "True",
                                            "key": "loraAllLinear",
                                            "type": "string",
                                        },
                                        {
                                            "key": "learningRate",
                                            "type": "float",
                                            "checkType": "range",
                                            "checkValue": [1e-06, 4e-05],
                                            "default": 3e-05,
                                        },
                                        {
                                            "key": "maxSeqLen",
                                            "type": "int",
                                            "checkType": "choice",
                                            "checkValue": [512, 1024, 2048, 4096, 8192],
                                            "default": 4096,
                                        },
                                    ],
                                },
                            ],
                            "trainMode": "SFT",
                        },
                        {
                            "supportParameterScale": [
                                {
                                    "parameterScale": "FullFineTuning",
                                    "supportHyperParameterConfig": [
                                        {
                                            "key": "epoch",
                                            "type": "int",
                                            "checkType": "range",
                                            "checkValue": [1, 50],
                                            "default": 1,
                                        },
                                        {
                                            "checkType": "choice",
                                            "checkValue": [4096, 8192],
                                            "default": 4096,
                                            "key": "maxSeqLenb",
                                            "type": "int",
                                        },
                                        {
                                            "key": "learningRate",
                                            "type": "float",
                                            "checkType": "range",
                                            "checkValue": [1e-06, 4e-05],
                                            "default": 3e-05,
                                        },
                                        {
                                            "key": "maxSeqLen",
                                            "type": "int",
                                            "checkType": "choice",
                                            "checkValue": [512, 1024, 2048, 4096, 8192],
                                            "default": 4096,
                                        },
                                    ],
                                }
                            ],
                            "trainMode": "PostPretrain",
                        },
                    ],
                }
            ],
        }
    )


@app.route(Consts.DatasetV2OfflineBatchInferenceAPI, methods=["POST"])
def offline_batch_inference_task_v2():
    action = request.args.get(Consts.ConsoleAPIQueryAction)
    body = request.json
    action_handler = {
        Consts.DatasetCreateOfflineBatchInferenceAction: (
            create_offline_batch_inference_task_v2
        ),
        Consts.DatasetDescribeOfflineBatchInferenceAction: (
            describe_offline_batch_inference_task_v2
        ),
        Consts.DatasetDescribeOfflineBatchInferencesAction: (
            describe_offline_batch_inference_tasks_v2
        ),
    }
    return action_handler.get(action)(body)


def create_offline_batch_inference_task_v2(body):
    if "afsConfig" in body:
        user_name = body.get("afsConfig").get("userName")
        if user_name in ["test_bf_invalid_username", ""]:
            return json_response(
                data={
                    "requestId": "deb38cd1-d880-4259-a35d-c383f0fcddca",
                    "code": "InappropriateJSON",
                    "message": (
                        "The JSON you provided was well-formed and valid, but"
                        "not appropriate for this operation. param[userName] invalid."
                    ),
                },
                status_code=400,
            )
    return json_response(
        {
            "requestId": "c1111-944f-4a9a-a12b-cc9o99999",
            "result": {"taskId": "65e6cd33bb6ef39c5370ec46"},
        }
    )


def describe_offline_batch_inference_task_v2(body):
    return json_response(
        {
            "requestId": "b6999-5fdc-495c-b526-ef68145345354",
            "result": {
                "taskId": "65e6c354345346",
                "name": "sdk-test-YK5zI923zN",
                "description": "",
                "endpoint": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions",
                "runStatus": "Done",
                "inferenceParams": {},
                "inputBosUri": "bos:/sdk_test/inference-input/",
                "outputBosUri": "bos:/sdk-test/inference-output/",
                "inputAfsUri": "afs:/sdk_test/inference-afs-input/",
                "outputAfsUri": "afs:/sdk-test/inference-afs-output/",
                "outputDir": "662f7bfb805xxx16942",
                "progress": 300,
                "createTime": "2024-03-05T07:43:48Z",
                "finishTime": "2024-03-05T15:44:56Z",
            },
        }
    )


def describe_offline_batch_inference_tasks_v2(body):
    return json_response(
        {
            "requestId": "1bef3f87-c5b2-4419-936b-5xxxxxxxx4",
            "result": {
                "taskList": [
                    {
                        "taskId": "infer-9ixxxxxxmp",
                        "name": "name",
                        "description": "description",
                        "endpoint": "http://xxx",
                        "inferenceParams": {"temperature": 0.9, "top_p": 0.3},
                        "runStatus": "Running",
                        "inputBosUri": "bos:/user_a/bucket",
                        "outputBosUri": "bos:/user_b/output",
                        "outputDir": "662f7bfb80xxxd516942",
                        "inputTokenUsage": 10000,
                        "outputTokenUsage": 10000,
                        "progress": 2000,
                        "creator": "accountName",
                        "createTime": "2024-01-16T09:48:35Z",
                        "finishTime": "2024-01-16T10:48:35Z",
                    },
                    {
                        "taskId": "infer-9ixxxxxxm1",
                        "name": "name",
                        "description": "description",
                        "endpoint": "http://xxx",
                        "inferenceParams": {"temperature": 0.9, "top_p": 0.3},
                        "runStatus": "Done",
                        "inputBosUri": "bos:/user_a/bucket",
                        "outputBosUri": "bos:/user_b/output",
                        "outputDir": "662f7bfb80xxxd516942",
                        "inputTokenUsage": 10000,
                        "outputTokenUsage": 10000,
                        "progress": 300,
                        "creator": "accountName",
                        "createTime": "2024-01-16T09:48:35Z",
                        "finishTime": "2024-01-16T10:48:35Z",
                    },
                ],
                "pageInfo": {
                    "marker": "infer-n50985crhqq3",
                    "maxKeys": 100,
                    "isTruncated": False,
                },
            },
        }
    )


@app.route(Consts.FineTuneCreateJobAPI, methods=["POST"])
@iam_auth_checker
def create_finetune_job():
    """
    mock create finetune job api
    """
    r = request.json
    task_id = r["taskId"]
    job_id = random.randint(0, 100000)
    global finetune_task_call_times
    finetune_task_call_times[(task_id, job_id)] = 0
    return json_response({"log_id": 123, "result": {"id": job_id, "uuid": "task-xxxx"}})


@app.route(Consts.FineTuneGetJobAPI, methods=["POST"])
@iam_auth_checker
def get_finetune_job():
    """
    mock get finetune job api
    """
    r = request.json
    task_id = r["taskId"]
    job_id = r["jobId"]
    global finetune_task_call_times
    call_times = finetune_task_call_times.get((task_id, job_id))
    if call_times is None:
        return json_response(
            {
                "log_id": "2475845384",
                "result": {
                    "id": 8982,
                    "description": "",
                    "taskId": 17263,
                    "taskName": "0725_cqa_fin",
                    "version": 1,
                    "jobRunType": 0,
                    "trainType": "ernieBotLite-v201-8k",
                    "trainMode": "SFT",
                    "peftType": "LoRA",
                    "trainStatus": "FINISH",
                    "progress": 51,
                    "runTime": 2525,
                    "trainTime": 732,
                    "startTime": "2023-12-07 11:40:00",
                    "finishTime": "2023-12-07 12:22:05",
                    "vdlLink": "https://console.bce.baidu.com/qianfan/visualdl/index?displayToken=eyJydW5JZCI6InJ1bi1yeTNqeDg0Z3NoaWt4dnA3In0=",
                },
            }
        )
    else:
        MAX_CALL_TIMES = 10
        finetune_task_call_times[(task_id, job_id)] += 1
        return json_response(
            {
                "log_id": "2475845384",
                "result": {
                    "id": job_id,
                    "description": "",
                    "taskId": task_id,
                    "taskName": "0725_cqa_fin",
                    "version": 1,
                    "jobRunType": 0,
                    "trainType": "ernieBotLite-v201-8k",
                    "trainMode": "SFT",
                    "peftType": "LoRA",
                    "trainStatus": (
                        "FINISH" if call_times >= MAX_CALL_TIMES else "RUNNING"
                    ),
                    "progress": int(100 * call_times / MAX_CALL_TIMES),
                    "runTime": 2525,
                    "trainTime": 732,
                    "startTime": "2023-12-07 11:40:00",
                    "finishTime": "2023-12-07 12:22:05",
                    "vdlLink": "https://console.bce.baidu.com/qianfan/visualdl/index?displayToken=eyJydW5JZCI6InJ1bi1yeTNqeDg0Z3NoaWt4dnA3In0=",
                },
            }
        )


@app.route(Consts.FineTuneStopJobAPI, methods=["POST"])
@iam_auth_checker
def stop_finetune_job():
    """
    mock stop finetune job api
    """
    return json_response({"log_id": 123, "result": True})


@app.route(Consts.ModelVersionDetailAPI, methods=["POST"])
@iam_auth_checker
def get_model_version_detail():
    """
    mock get model version detail api
    """
    return json_response(
        {
            "result": {
                "modelId": 12094,
                "modelIdStr": "am-nvdx92556wpw",
                "modelName": "m_18423_10840",
                "modelVersionId": 14997,
                "modelVersionIdStr": "amv-hcxfe5a8z6nd",
                "version": "1",
                "description": "",
                "sourceType": "Train",
                "sourceExtra": {
                    "trainSourceExtra": {
                        "taskId": 18423,
                        "taskIdStr": "job-vbt3exahqhrv",
                        "taskName": "task_EJD7l6v0TH",
                        "iterationVersion": 1,
                        "runId": 10840,
                        "runIdStr": "task-am9st8hyntpm",
                        "devType": 1,
                        "modelType": 20,
                        "templateType": 2000,
                    },
                    "sourceType": "Train",
                },
                "framework": "paddlepaddle",
                "algorithm": "ERNIE_EB-ERNIEBOT_PRO",
                "modelNet": "paddlepaddle-ERNIE_EB-ERNIEBOT_PRO_LORA",
                "state": "Ready",
                "ioMode": "chat",
                "ioLength": "",
                "copyright": "",
                "property": {},
                "createTime": "2024-01-16T18:38:08+08:00",
                "modifyTime": "2024-01-16T18:42:44+08:00",
                "deployResource": ["Private"],
                "supportOptions": ["Deploy"],
                "trainType": "ernieBotLite-Speed",
                "params": {
                    "input": {
                        "type": "object",
                        "required": ["messages"],
                        "properties": {
                            "messages": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["role", "content"],
                                    "properties": {
                                        "role": {
                                            "name": "role",
                                            "type": "string",
                                            "default": "user",
                                            "description": (
                                                '当前支持以下两个role： "user": 用户'
                                                ' "assistant": 对话助手'
                                            ),
                                        },
                                        "content": {
                                            "name": "content",
                                            "type": "string",
                                            "description": "对话内容，不能为空",
                                        },
                                    },
                                },
                            },
                            "stream": {
                                "name": "stream",
                                "type": "boolean",
                                "description": (
                                    "是否以流式接口的形式返回数据； 默认false"
                                ),
                            },
                            "user_id": {
                                "name": "user_id",
                                "type": "string",
                                "description": "表示最终用户的唯一标识符，可以监视和检测滥用行为，防止接口恶意调用。",
                            },
                        },
                    },
                    "output": {
                        "type": "object",
                        "required": [],
                        "properties": {
                            "id": {
                                "name": "id",
                                "type": "string",
                                "description": "本轮对话的id",
                            },
                            "object": {
                                "name": "object",
                                "type": "string",
                                "description": (
                                    "回包类型 “chat.completion”：多轮对话返回"
                                ),
                            },
                            "created": {
                                "name": "created",
                                "type": "integer",
                                "format": "int32",
                                "description": "时间戳",
                            },
                            "sentence_id": {
                                "name": "sentence_id",
                                "type": "integer",
                                "format": "int32",
                                "description": (
                                    "流式接口模式下会返回，表示当前子句的序号"
                                ),
                            },
                            "is_end": {
                                "name": "is_end",
                                "type": "boolean",
                                "description": (
                                    "流式接口模式下会返回，表示当前子句是否是最后一句"
                                ),
                            },
                            "is_truncated": {
                                "name": "is_truncated",
                                "type": "boolean",
                                "description": "标识当前生成的结果是否被截断",
                            },
                            "result": {
                                "name": "result",
                                "type": "string",
                                "description": (
                                    "对话返回结果, 当前对话返回结果限制在1000个token"
                                ),
                            },
                            "need_clear_history": {
                                "name": "need_clear_history",
                                "type": "boolean",
                                "description": "值为true表示用户输入存在安全风险，建议关闭当前会话，清理历史会话信息",
                            },
                            "ban_round": {
                                "name": "ban_round",
                                "type": "integer",
                                "format": "int32",
                                "description": (
                                    "当need_clear_history为true时，"
                                    "此字段会告知第几轮对话有敏感信息，如果是当前问题，"
                                    "ban_round = -1"
                                ),
                            },
                            "usage": {
                                "type": "object",
                                "required": [],
                                "description": (
                                    "token统计信息，token数 = 汉字数+单词数*1.3 （仅为估算逻辑）"
                                ),
                                "properties": {
                                    "prompt_tokens": {
                                        "name": "prompt_tokens",
                                        "type": "integer",
                                        "format": "int32",
                                        "description": "问题tokens数（包含历史QA）",
                                    },
                                    "completion_tokens": {
                                        "name": "completion_tokens",
                                        "type": "integer",
                                        "format": "int32",
                                        "description": "回答tokens数",
                                    },
                                    "total_tokens": {
                                        "name": "total_tokens",
                                        "type": "integer",
                                        "format": "int32",
                                        "description": "tokens总数",
                                    },
                                },
                            },
                        },
                    },
                },
            },
            "log_id": "2443391389",
        }
    )


@app.route(Consts.AppListAPI, methods=["GET"])
@iam_auth_checker
def get_app_list():
    return json_response(
        {
            "log_id": "8918918516",
            "result": {
                "appList": [
                    {
                        "id": 1,
                        "name": "unit_test_1",
                        "ak": "ak_from_app_list_api_1",
                        "sk": "sk_from_app_list_api_1",
                        "apiIds": "1,2,3",
                    },
                    {
                        "id": 2,
                        "name": "unit_test_2",
                        "ak": "ak_from_app_list_api_2",
                        "sk": "sk_from_app_list_api_2",
                        "apiIds": "1,2,3",
                    },
                    {
                        "id": 3,
                        "name": "unit_test_3",
                        "ak": "ak_from_app_list_api_3",
                        "sk": "sk_from_app_list_api_3",
                        "apiIds": "1,2,3",
                    },
                ]
            },
        }
    )


@app.route(Consts.ModelDetailAPI, methods=["POST"])
@iam_auth_checker
def get_model_detail():
    """
    mock get model detail api
    """
    return json_response(
        {
            "result": {
                "modelId": 12094,
                "modelIdStr": "am-nvdx92556wpw",
                "modelName": "m_18423_10840",
                "source": "UserCreate",
                "modelType": 0,
                "createUserId": 20,
                "createUser": "baidu_aipd",
                "createTime": "2024-01-16T18:38:08+08:00",
                "modifyTime": "2024-01-16T18:38:08+08:00",
                "description": "",
                "trainType": "ernieBotLite-Speed",
                "modelVersionList": [
                    {
                        "modelId": 12094,
                        "modelIdStr": "am-nvdx92556wpw",
                        "modelName": "m_18423_10840",
                        "modelVersionId": 14997,
                        "modelVersionIdStr": "amv-hcxfe5a8z6nd",
                        "version": "1",
                        "description": "",
                        "sourceType": "Train",
                        "sourceExtra": {
                            "trainSourceExtra": {
                                "taskId": 18423,
                                "taskIdStr": "job-vbt3exahqhrv",
                                "taskName": "task_EJD7l6v0TH",
                                "iterationVersion": 1,
                                "runId": 10840,
                                "runIdStr": "task-am9st8hyntpm",
                                "devType": 1,
                                "modelType": 20,
                                "templateType": 2000,
                            },
                            "sourceType": "Train",
                        },
                        "framework": "paddlepaddle",
                        "algorithm": "ERNIE_EB-ERNIEBOT_PRO",
                        "modelNet": "paddlepaddle-ERNIE_EB-ERNIEBOT_PRO_LORA",
                        "state": "Ready",
                        "ioMode": "chat",
                        "ioLength": "",
                        "copyright": "",
                        "property": {},
                        "createTime": "2024-01-16T18:38:08+08:00",
                        "modifyTime": "2024-01-16T18:38:09+08:00",
                        "deployResource": ["Private"],
                        "supportOptions": ["Deploy"],
                        "trainType": "ernieBotLite-Speed",
                    }
                ],
            },
            "log_id": "3662836331",
        }
    )


@app.route(Consts.ModelPublishAPI, methods=["POST"])
@iam_auth_checker
def publish_model():
    """
    mock publish model api
    """
    return json_response(
        {
            "log_id": 1212121,
            "result": {
                "modelIDStr": "am-nvdx92556wpw",
                "modelId": 12094,
                "version": "1",
                "versionId": 14997,
                "versionIdStr": "amv-hcxfe5a8z6nd",
            },
        }
    )


@app.route(Consts.ModelEvalCreateAPI, methods=["POST"])
@iam_auth_checker
def create_evaluation_task():
    """
    mock create evaluation task api
    """
    return json_response(
        {"result": {"evalId": 585, "evalIdStr": "thisisid"}, "log_id": "2255352990"}
    )


@app.route(Consts.ModelEvalInfoAPI, methods=["POST"])
@iam_auth_checker
def get_evaluation_info():
    """
    mock get evaluation task info api
    """
    return json_response(
        {
            "result": {
                "evaluationId": request.json["id"],
                "name": "eval_for_lama2",
                "description": "",
                "state": "Done",
                "evalUnits": [
                    {
                        "modelVersionId": 1819,
                        "modelId": 1354,
                        "modelName": "Llama_2_7b_all",
                        "modelVersion": "1",
                        "modelSource": "Train",
                        "state": "Editing",
                        "modelVersionDesc": "",
                        "message": "",
                        "modelTags": None,
                    }
                ],
                "datasetId": "1337",
                "datasetName": "预置数据集>AGI_EVAL>V1",
                "computeResourceConf": {
                    "vmType": 1,
                    "vmNumber": 8,
                    "computeResourceId": "",
                    "cpu": 0,
                    "memory": 0,
                },
                "evalStandardConf": {
                    "evalMode": "model,manual,rule",
                    "scoreModes": ["similarity", "accuracy"],
                    "stopWordsPath": "",
                    "appId": 1483416585,
                    "appAk": "uiuj6hZY5HUrlFej1deMUAKM",
                    "appSk": "Imvaecl8UrUPTMOyFSraxpt1IpkGFTCp",
                    "apiName": "ERNIE-3.5-8K",
                    "apiUrl": "/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions",
                    "prompt": {
                        "templateName": " 裁判员模型打分模板（含参考答案）",
                        "templateContent": """
                            你是一个好助手。请你为下面问题的回答打分
                            问题如下: {src}
                            标准答案如下：{tgt}
                            回答如下：{prediction}
                            评分的指标如下：综合得分
                            请你遵照以下的评分步骤：1.
                            仔细阅读所提供的问题，确保你理解问题的要求和背景。
                            2.
                            仔细阅读所提供的标准答案，确保你理解问题的标准答案
                            3.
                            阅读答案，并检查是否用词不当
                            4.
                            检查答案是否严格遵照了题目的要求，包括答题方式、答题长度、答题格式等等。
                            根据答案的综合水平给出0到7的评分。如果答案存在明显的不合理之处，则应给出一个较低的评分。如果答案符合以上要求并且与参考答案含义相似，则应给出一个较高的评分。
                            你的回答模版如下:
                            评分: 此处只能回答整数评分
                            原因: 此处只能回答评分原因
                            """,
                        "metric": "综合得分",
                        "steps": """
                            1.仔细阅读所提供的问题，确保你理解问题的要求和背景。
                            2.
                            仔细阅读所提供的标准答案，确保你理解问题的标准答案
                            3.
                            阅读答案，并检查是否用词不当
                            4.
                            检查答案是否严格遵照了题目的要求，包括答题方式、答题长度、答题格式等等。
                            """,
                        "minScore": 0,
                        "maxScore": 7,
                    },
                    "resultDatasetId": 1,
                    "resultDatasetIdStr": "1",
                    "resultDatasetName": "name",
                    "resultDatasetProjectType": 0,
                    "resultDatasetImportStatus": 0,
                    "resultDatasetReleaseStatus": 0,
                    "evaluationDimension": [
                        {
                            "dimension": "满意度",
                            "description": "",
                            "minScore": 0,
                            "maxScore": 2,
                        },
                        {
                            "dimension": "安全性",
                            "description": "安全性备注",
                            "minScore": 0,
                            "maxScore": 2,
                        },
                    ],
                },
            },
            "log_id": "4245751552",
        }
    )


@app.route(Consts.ModelEvalResultAPI, methods=["POST"])
@iam_auth_checker
def get_evaluation_result():
    """
    mock get evaluation result api
    """
    return json_response(
        {
            "result": [
                {
                    "modelName": "llama213blora",
                    "modelVersion": "1",
                    "modelVersionSource": "Train",
                    "evalMode": "model,manual,rule",
                    "evaluationName": "eval_混合_单模型",
                    "id": "65544bbadcb373c893b080df",
                    "modelVersionId": 1576,
                    "modelId": 1164,
                    "evaluationJobId": 2617,
                    "userId": 1,
                    "projectId": "",
                    "evaluationId": request.json["id"],
                    "effectMetric": {
                        "accuracy": 0,
                        "f1Score": 0.095671654,
                        "rouge_1": 0.063611045,
                        "rouge_2": 0.004779625,
                        "rouge_l": 0.072322726,
                        "bleu4": 0.004749891,
                        "avgJudgeScore": 3.875,
                        "stdJudgeScore": 0.59947896,
                        "medianJudgeScore": 4,
                        "scoreDistribution": {
                            "0": 0,
                            "1": 0,
                            "2": 0,
                            "3": 2,
                            "4": 5,
                            "5": 1,
                            "-1": 0,
                        },
                        "manualAvgScore": 2,
                        "goodCaseProportion": 1,
                        "subjectiveImpression": "1",
                        "manualScoreDistribution": [
                            {"dimension": "满意度", "scoreDistribution": {"2": 8}},
                            {"dimension": "安全性", "scoreDistribution": {"2": 8}},
                        ],
                    },
                }
            ],
            "log_id": "2404206370",
        }
    )


@app.route(Consts.ModelEvalStopAPI, methods=["POST"])
@iam_auth_checker
def stop_evaluation_task():
    """
    mock stop evaluation task api
    """
    return json_response(
        {"result": {"result": True, "errorMessage": ""}, "log_id": "2398985472"}
    )


@app.route(Consts.ModelEvalResultExportAPI, methods=["POST"])
@iam_auth_checker
def create_evaluation_result_export_task():
    """
    mock create evaluation result export task api
    """

    return json_response(
        {
            "log_id": "4159183555",
            "result": {"exportID": 105, "exportIDStr": "amemt-hkkf5y9e64j8"},
        }
    )


@app.route(Consts.ModelEvalResultExportStatusAPI, methods=["POST"])
@iam_auth_checker
def get_evaluation_result_export_task_status():
    """
    mock get evaluation result export task status
    """

    return json_response(
        {
            "log_id": "2340692759",
            "result": {
                "id": 305,
                "exportID": request.json["exportID"],
                "exportIDStr": "amemt-hkkf5y9e64j8",
                "state": "Done",
                "exportType": "storage",
                "volumeId": "modelrepo-test",
                "exportPath": "qianfan_modelrepo_offline/workspace/model_eval_result_export/cl_test23_305_1704338430470.csv",
                "downloadUrl": "http://127.0.0.1:8866/eval_result_mock",
            },
        }
    )


@app.route("/eval_result_mock", methods=["GET"])
def get_mock_eval_resul():
    sio = io.StringIO()
    sio.writelines(
        [
            (
                '[{"模型名称": "ERNIE-Lite-8K", "模型版本": "ERNIE-Lite-8K",'
                ' "Prompt问题": "请根据下面的新闻生成摘要, 内容如下：周末采摘杨桃助农，'
                "游玩澄迈养生农庄自驾活动，快来报名~1月31日早上8点半出发哦，"
                "前往澄迈杨桃园采摘，入园免费，"
                "漫山遍野的杨桃和你亲密接触（带走的按2.5元/斤）。"
                '报名方式：拨136-3755-3497报名，或戳链接生成摘要如下：", "模型结果":'
                ' "周末采摘杨桃助农活动将于1月31日早上8点半出发，前往澄迈杨桃园采摘，'
                "报名方式为拨打电话或点击链接。活动还包含游玩澄迈养生农庄，可自驾前往。"
                '报名免费，采摘带走按2.5元/斤。", "预期回答":'
                ' "这个周末自驾游去摘杨桃啦！", "BLEU-4": "0.80%", "ROUGE-1": "7.84%",'
                ' "ROUGE-2": "0.00%", "ROUGE-L": "6.45%", "裁判员模型打分": "5",'
                ' "裁判员模型打分理由": "该答案对题目所提问题的理解完全正确，'
                "答案详细清晰，用词恰当，符合题目的要求，"
                "同时也准确地概括了新闻的主要内容。答案中包含了活动的所有关键信息，"
                "如时间、地点、活动内容和报名方式等，且格式规范，易于理解。因此，"
                '我认为这个答案应该得到满分。"}]'
            ),
            "\n",
            (
                '[{"模型名称": "Llama-2-7B", "模型版本": "Qianfan-Chinese-Llama-2-7B",'
                ' "Prompt问题": "请根据下面的新闻生成摘要, 内容如下：周末采摘杨桃助农，'
                "游玩澄迈养生农庄自驾活动，快来报名~1月31日早上8点半出发哦，"
                "前往澄迈杨桃园采摘，入园免费，"
                "漫山遍野的杨桃和你亲密接触（带走的按2.5元/斤）。"
                '报名方式：拨136-3755-3497报名，或戳链接生成摘要如下：", "模型结果":'
                ' "周末去澄迈采摘杨桃，入园免费，带走按2.5元/斤，快来报名！",'
                ' "预期回答": "这个周末自驾游去摘杨桃啦！", "BLEU-4": "2.71%",'
                ' "ROUGE-1": "30.77%", "ROUGE-2": "0.00%", "ROUGE-L": "28.57%",'
                ' "裁判员模型打分": "5", "裁判员模型打分理由":'
                ' "该答案准确地概括了原文的主要信息，'
                "即周末前往澄迈杨桃园采摘杨桃的活动，并提到了入园免费和带走的杨桃价格。"
                "同时，该答案简洁明了，没有使用不当的词汇或语法错误。因此，"
                '该答案符合题目的要求，可以得到5分的高分。"}]'
            ),
        ]
    )

    bio = io.BytesIO()
    with zipfile.ZipFile(bio, mode="w") as f:
        f.writestr(
            "data.jsonl",
            data=sio.getvalue(),
        )

    def gen() -> str:
        yield bio.getvalue()

    return flask.Response(gen())


@app.route(Consts.ModelEvaluableModelListAPI, methods=["POST"])
@iam_auth_checker
def evaluable_model_list():
    """mock get all evaluable model list api"""
    return json_response(
        {
            "log_id": "2347238209",
            "result": [
                {
                    "modelId": 2,
                    "modelIdStr": "am-ju3hi4ts39u9",
                    "modelName": "ERNIE Lite",
                    "source": "PlatformPreset",
                    "modelType": 0,
                    "trainType": "",
                    "modelVersionList": [
                        {
                            "modelVersionId": 26382,
                            "modelVersionIdStr": "amv-k8npfy0yz90r",
                            "version": "ERNIE-Lite-128K-0419",
                            "sourceType": "PlatformPreset",
                            "framework": "paddle",
                            "algorithm": "ERNIE_EB-ERNIEBOT_LITE_128K",
                            "modelNet": "paddlepaddle-ERNIE_EB-ERNIEBOT_LITE_128K",
                            "trainType": "",
                            "description": "2024年4月19日发布版本，优化模型效果，支持128K上下文长度",
                        },
                        {
                            "modelVersionId": 19879,
                            "modelVersionIdStr": "amv-irrrsmxabb6r",
                            "version": "ERNIE-Lite-8K-0308",
                            "sourceType": "PlatformPreset",
                            "framework": "paddle",
                            "algorithm": "ERNIE_EB-ERNIEBOT_LITE_8K",
                            "modelNet": "paddlepaddle-ERNIE_EB-ERNIEBOT_LITE_8K",
                            "trainType": "ernieBotLite-8k",
                            "description": (
                                "2024年3月8日发布版本，优化模型效果，支持8K上下文长度"
                            ),
                        },
                    ],
                },
                {
                    "modelId": 446,
                    "modelIdStr": "am-44f8ji8eegp0",
                    "modelName": "Yi-34B",
                    "source": "PlatformPreset",
                    "modelType": 0,
                    "trainType": "",
                    "modelVersionList": [
                        {
                            "modelVersionId": 635,
                            "modelVersionIdStr": "amv-mpjrtxej6hye",
                            "version": "Yi-34B-Chat",
                            "sourceType": "PlatformPreset",
                            "framework": "Pytorch",
                            "algorithm": "opensource-yi-34b",
                            "modelNet": "pytorch-yi-34b-chat-1.13.1",
                            "trainType": "",
                            "description": "支持对话的chat版本",
                        },
                        {
                            "modelVersionId": 620,
                            "modelVersionIdStr": "amv-ffff66e1fm3d",
                            "version": "Yi-34B",
                            "sourceType": "PlatformPreset",
                            "framework": "Pytorch",
                            "algorithm": "opensource-yi-34b",
                            "modelNet": "pytorch-yi-34b-1.13.1",
                            "trainType": "",
                            "description": "初始预训练版本",
                        },
                    ],
                },
            ],
        }
    )


@app.route(Consts.ServiceV2BaseRouteAPI, methods=["POST"])
@iam_auth_checker
def service_v2():
    action = request.args.get(Consts.ConsoleAPIQueryAction)
    json_body = request.json
    action_handler = {
        Consts.ServiceCreateAction: service_v2_create_service,
        Consts.ServiceDetailAction: service_v2_get_service,
        Consts.ServiceMetricAction: service_v2_get_service_metrics,
    }
    return action_handler.get(action)(body=json_body)


def service_v2_create_service(body):
    return json_response(
        {
            "requestId": "1bef3f87-c5b2-4419-936b-50f9884f10d4",
            "result": {
                "serviceId": "svco-ktth9mkb5cqn",
                "instanceId": "44961088f51d4b91b4c539e9379f5daf",
            },
        }
    )


def service_v2_get_service(body):
    return json_response(
        {
            "requestId": "e39a7511-50f6-45ff-a94f-fed58e4a32c5",
            "result": {
                "serviceId": "svco-ktth9mkb5cqn",
                "modelId": "am-b6ngmk0j3cap",
                "modelVersionId": "amv-6g8nng4auutg",
                "name": "mydasvc",
                "description": "hi",
                "url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/kzpitmni_daxx",
                "serviceType": "chat",
                "runStatus": "Serving",
                "chargeStatus": "Free",
                "resourceConfig": {"type": "GPU-I-2", "replicasCount": 1, "qps": 0.5},
                "createTime": "2024-05-16T15:23:30Z",
            },
        }
    )


def service_v2_get_service_metrics(body):
    return json_response(
        {
            "requestId": "3f2cefc4-b139-42f8-8fb2-48758e65afbf",
            "result": {
                "startTime": "2024-05-06T08:23:49Z",
                "endTime": "2024-05-17T08:23:49Z",
                "serviceList": [
                    {
                        "serviceId": "svco-ktth9mkb5cqn",
                        "serviceName": "mydasvc",
                        "appList": [
                            {
                                "appId": "26217442",
                                "metric": {
                                    "inputTokensTotal": 3,
                                    "outputTokensTotal": 61,
                                    "tokensTotal": 64,
                                    "succeedCallTotal": 1,
                                    "failureCallTotal": 0,
                                    "callTotal": 1,
                                },
                            }
                        ],
                    }
                ],
            },
        }
    )


@app.route(Consts.ServiceCreateAPI, methods=["POST"])
@iam_auth_checker
def create_service():
    """
    mock create service api
    """
    return json_response(
        {"log_id": "2771697584", "result": {"result": True, "serviceId": 164}}
    )


@app.route(Consts.ServiceDetailAPI, methods=["POST"])
@iam_auth_checker
def get_service():
    """
    mock get service api
    """
    return json_response(
        {
            "log_id": "3902119009",
            "result": {
                "id": 169,
                "modelId": 287,
                "modelName": "wxq_llama_0830",
                "modelType": 0,
                "templateType": 2000,
                "iterationId": 384,
                "modelVersion": "1",
                "version": "1",
                "name": "xm",
                "uri": "xbiimimv_xxx",
                "fullUri": "http://gzns-inf-h22-for-idl28.gzns:8192/rpc/v1/agile/chat/xbiimimv_xxx",
                "applyStatus": 2,
                "serviceStatus": "Done",
                "sourceType": 1,
                "onlineTime": 1694601667,
                "callUnitPrice": "0",
                "description": "",
                "devApiId": 29076,
                "apiId": 1029076,
                "vmConfig": {
                    "resourceId": "",
                    "instanceCount": 2,
                    "CPUNum": 0,
                    "memory": 0,
                    "GPUType": "",
                    "GPUNum": 0,
                    "volumeId": "",
                },
                "timeout": 0,
                "qps": 0,
                "noAuthAccess": False,
                "hasDeploying": True,
                "openDcl": False,
                "payType": 3,
                "creator": "百里慕蕊",
                "createTime": 1694586667,
                "modifyTime": 1695728714,
            },
        }
    )


@app.route(Consts.ServiceListAPI, methods=["POST"])
@iam_auth_checker
def list_service():
    """
    mock create service api
    """
    services = [
        {
            "name": "ERNIE-99",
            "url": (
                "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb99"
            ),
            "apiType": "chat",
            "chargeStatus": "OPENED",
            "versionList": [{"trainType": "ernieBot_4", "serviceStatus": "Done"}],
        },
        {
            "name": "ERNIE-88-completions",
            "url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/completions/eb88",
            "apiType": "completions",
            "chargeStatus": "OPENED",
            "versionList": [{"trainType": "ernieBot_4", "serviceStatus": "Done"}],
        },
        {
            "name": "ERNIE-Bot 4.0",
            "url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro",
            "apiType": "chat",
            "chargeStatus": "OPENED",
            "versionList": [{"trainType": "ernieBot_4", "serviceStatus": "Done"}],
        },
        {
            "name": "ERNIE-Bot",
            "url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions",
            "apiType": "chat",
            "chargeStatus": "OPENED",
            "versionList": [{"trainType": "ernieBot", "serviceStatus": "Done"}],
        },
        {
            "name": "Stable-Diffusion-XL",
            "url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/text2image/sd_xl",
            "apiType": "text2image",
            "chargeStatus": "FREE",
            "versionList": [
                {
                    "trainType": "stablediffusion_VXL",
                    "serviceStatus": "Done",
                }
            ],
        },
        {
            "name": "Embedding-V1",
            "url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/embeddings/embedding-v1",
            "apiType": "embeddings",
            "chargeStatus": "OPENED",
            "versionList": [{"trainType": "embedding", "serviceStatus": "Done"}],
        },
        {
            "name": "bge-large-zh",
            "url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/embeddings/bge_large_zh",
            "apiType": "embeddings",
            "chargeStatus": "OPENED",
            "versionList": [{"trainType": "embedding", "serviceStatus": "Done"}],
        },
        {
            "name": "bge-large-en",
            "url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/embeddings/bge_large_en",
            "apiType": "embeddings",
            "chargeStatus": "OPENED",
            "versionList": [{"trainType": "embedding", "serviceStatus": "Done"}],
        },
        {
            "name": "embed-test",
            "url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/embeddings/embed_test",
            "apiType": "embeddings",
            "chargeStatus": "OPENED",
            "versionList": [{"trainType": "embedding", "serviceStatus": "Done"}],
        },
    ]

    apiTypes = request.json.get("apiTypefilter")
    if apiTypes:
        services = [service for service in services if service["apiType"] in apiTypes]
    return json_response(
        {
            "log_id": "3333888838",
            "result": {
                "common": services,
                "custom": [],
            },
        }
    )


@app.route(Consts.DatasetCreateAPI, methods=["POST"])
@iam_auth_checker
def create_dataset():
    args = request.json
    if args["storageType"] == "sysBos":
        return json_response(
            {
                "log_id": "log_id",
                "status": 200,
                "success": True,
                "result": {
                    "id": 46563,
                    "groupId": 12,
                    "groupPK": "12",
                    "datasetId": "ds-9cetiuhvnbn4mqs3",
                    "versionId": 1,
                    "groupName": args["name"],
                    "displayName": "displayName",
                    "createFrom": 0,
                    "bmlDatasetId": "bmlDatasetId",
                    "userId": 123,
                    "dataType": args["dataType"],
                    "projectType": args["projectType"],
                    "templateType": args["templateType"],
                    "remark": "this is remark",
                    "storageInfo": {
                        "storageId": args.get("storageId", "1231"),
                        "storagePath": args.get(
                            "storagePath",
                            "/easydata/_system_/dataset/ds-z07hkq2kyvsmrmdw/texts",
                        ),
                        "storageName": args.get("storageId", "1231"),
                    },
                    "importStatus": 1,
                    "importProgress": 0,
                    "exportStatus": -1,
                    "releaseStatus": 0,
                    "ShouldHide": True,
                    "status": 0,
                    "isUnique": 0,
                    "errCode": None,
                    "createTime": "2023-10-25T16:16:38.430058683+08:00",
                    "modifyTime": "2023-10-25T16:16:38.430066297+08:00",
                },
            }
        )
    else:
        return json_response(
            {
                "log_id": "log_id",
                "status": 200,
                "success": True,
                "result": {
                    "id": 46563,
                    "groupId": 12,
                    "groupPK": "12",
                    "datasetId": "ds-9cetiuhvnbn4mqs3",
                    "versionId": 1,
                    "groupName": args["name"],
                    "displayName": "displayName",
                    "createFrom": 0,
                    "bmlDatasetId": "bmlDatasetId",
                    "userId": 123,
                    "dataType": args["dataType"],
                    "projectType": args["projectType"],
                    "templateType": args["templateType"],
                    "remark": "this is remark",
                    "storageInfo": {
                        "storageId": args.get("storageId", "1231"),
                        "storagePath": args.get(
                            "storagePath",
                            "/easydata/_system_/dataset/ds-z07hkq2kyvsmrmdw/texts",
                        ),
                        "storageName": args.get("storageId", "1231"),
                        "rawStoragePath": args.get("rawStoragePath", ""),
                        "region": "bj",
                    },
                    "importStatus": 1,
                    "importProgress": 0,
                    "exportStatus": -1,
                    "releaseStatus": 0,
                    "ShouldHide": True,
                    "status": 0,
                    "isUnique": 0,
                    "errCode": None,
                    "createTime": "2023-10-25T16:16:38.430058683+08:00",
                    "modifyTime": "2023-10-25T16:16:38.430066297+08:00",
                },
            }
        )


@app.route(Consts.DatasetImportAPI, methods=["POST"])
@iam_auth_checker
def create_data_import_task():
    return json_response(
        {
            "log_id": "log_id",
            "status": 200,
            "success": True,
            "result": True,
        }
    )


@app.route(Consts.DatasetReleaseAPI, methods=["POST"])
@iam_auth_checker
def release_dataset():
    return json_response(
        {
            "log_id": "log_id",
            "status": 200,
            "success": True,
            "result": True,
        }
    )


@app.route(Consts.DatasetInfoAPI, methods=["POST"])
@iam_auth_checker
def get_dataset_info():
    args = request.json
    resp = {
        "log_id": "log_id",
        "result": {
            "groupPK": "14510",
            "name": "ChineseMedicalDialogueData中文医疗问答数据集",
            "dataType": 4,
            "versionInfo": {
                "id": 123,
                "groupId": 14510,
                "datasetId": 12444,
                "datasetPK": args["datasetId"],
                "importRecordCount": 1,
                "exportRecordCount": 0,
                "bmlDatasetId": "ds-7pkzh1exthpuy10n",
                "userId": 0,
                "versionId": 1,
                "displayName": "",
                "importStatus": 2,
                "importProgress": 100,
                "exportStatus": 2,
                "exportProgress": 0,
                "dataType": 4,
                "projectType": 20,
                "templateType": (
                    2000 if "generic" not in str(args["datasetId"]) else 40100
                ),
                "errCode": None,
                "uniqueType": 0,
                "importErrorInfo": None,
                "createTime": "2023-09-08 17:10:11",
                "modifyTime": "2023-10-25 20:45:23",
                "storageType": "sysBos",
                "storage": {
                    "storageId": "easydata",
                    "storageName": "easydata",
                    "storagePath": (
                        "/easydata/_system_/dataset/ds-7pkzh1exthpuy10n/texts"
                    ),
                    "rawStoragePath": "",
                    "region": "bj",
                },
                "releaseStatus": 2,
                "releaseErrCode": 0,
                "releaseStoragePath": (
                    "/easydata/_system_/dataset/ds-7pkzh1exthpuy10n/texts/jsonl"
                ),
                "releaseProgress": 0,
                "remark": "",
                "annotatedEntityCount": 792099,
                "entityCount": 792099,
                "labelCount": 1,
                "memorySize": 513.42,
                "characterCount": 173338860,
                "isEnhancing": False,
                "enhanceStatus": -1,
                "hasEnhance": False,
                "isSelfInstructEnhance": False,
                "interAnnoRunning": False,
                "hardSampleCount": 0,
                "etlStatus": 0,
                "hasEtl": False,
                "isPipelineEtl": False,
                "teamAnnoStatus": -1,
                "hasTeamAnno": False,
                "promptOptimizeStatus": 0,
                "demandStatus": "",
                "view": 2446,
                "usage": 262,
                "description": "中文医疗对话数据集由792099个问答对组成，包括男科、内科、妇产科、肿瘤科、儿科和外科",
                "tag": [
                    {"name": "文本对话非排序"},
                    {"name": "限定式问答"},
                    {"name": "调优"},
                ],
                "license": "MIT",
                "copyright": "toyhom",
                "copyrightLink": (
                    "https://github.com/Toyhom/Chinese-medical-dialogue-data"
                ),
            },
        },
        "status": 200,
        "success": True,
    }
    if args["datasetId"] == "ds-mock-generic":
        resp["result"]["versionInfo"]["projectType"] = 401
        resp["result"]["versionInfo"]["templateType"] = 40100
    return json_response(resp)


@app.route(Consts.DatasetStatusFetchInBatchAPI, methods=["POST"])
@iam_auth_checker
def get_dataset_status():
    args = request.json
    return json_response(
        {
            "log_id": "log_id",
            "status": 200,
            "success": True,
            "result": {
                idx: {
                    "importStatus": 1,
                    "importProgress": 1,
                    "releaseStatus": 0,
                    "releaseProgress": 0,
                    "exportStatus": 255,
                    "exportProgress": 0,
                    "enhanceStatus": -1,
                    "etlStatus": 0,
                    "importErrorInfo": None,
                    "entityCount": 0,
                    "annotatedEntityCount": 0,
                    "labelCount": 1,
                    "characterCount": 0,
                    "modifyTime": "2023-10-26 12:34:08",
                }
                for idx in args["datasetIds"]
            },
        }
    )


@app.route(Consts.DatasetImportErrorDetail, methods=["POST"])
@iam_auth_checker
def get_dataset_import_error_detail():
    return json_response(
        {
            "log_id": "log_id",
            "result": {
                "dataType": "file",
                "downloadUrl": "url",
                "isZip": 0,
                "projectType": 401,
                "content": [
                    {
                        "sequence": 1,
                        "sampleFileName": "",
                        "sampleName": "WENXINWORKSHOP (1).docx",
                        "textLocation": 0,
                        "textContent": "",
                    }
                ],
            },
            "status": 200,
            "success": True,
        }
    )


@app.route(Consts.DatasetDeleteAPI, methods=["POST"])
@iam_auth_checker
def delete_dataset():
    return json_response(
        {
            "log_id": "9rbmg0i9v2ufkdb2",
            "result": {"versionCount": 0},
            "status": 200,
            "success": True,
        }
    )


@app.route(Consts.DatasetExportAPI, methods=["POST"])
@iam_auth_checker
def create_dataset_export_task():
    return json_response(
        {
            "log_id": "dhqc1wmm2tyg61m7",
            "result": True,
            "status": 200,
            "success": True,
        }
    )


@app.route(Consts.DatasetExportRecordAPI, methods=["POST"])
@iam_auth_checker
def get_export_record():
    return json_response(
        {
            "log_id": "59sjmnq2xzda5spn",
            "result": [
                {
                    "creatorName": "yyw02",
                    "storageId": "easydata-upload",
                    "storagePath": "path",
                    "size": 0.01,
                    "exportFormat": 0,
                    "exportType": 1,
                    "status": 2,
                    "recordNum": 9,
                    "exportTo": 0,
                    "downloadUrl": "http://127.0.0.1:8866/url",
                    "startTime": "2023-11-07 10:04:44",
                    "finishTime": "2023-11-07 10:04:53",
                }
            ],
            "status": 200,
            "success": True,
        }
    )


@app.route("/url", methods=["GET"])
def get_mock_zip_file():
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, mode="w") as f:
        f.writestr(
            "1.jsonl",
            data='[{"prompt": "a prompt", "response": [["no response"]]}]',
        )

    def gen() -> bytes:
        yield bio.getvalue()

    return flask.Response(gen())


@app.route(Consts.PromptCreateAPI, methods=["POST"])
@iam_auth_checker
def create_prompt():
    return json_response(
        {
            "log_id": "py3yxbi7ffdj7kuc",
            "result": {
                "templateId": 732,
                "templatePK": f"pt-{generate_letter_num_random_id()}",
            },
            "status": 200,
            "success": True,
        }
    )


@app.route(Consts.PromptInfoAPI, methods=["POST"])
@iam_auth_checker
def prompt_detail():
    return json_response(
        {
            "log_id": "i1sm6juguyzyqrpd",
            "result": {
                "templateId": 732,
                "templatePK": f"pt-{generate_letter_num_random_id()}",
                "templateName": "文生文1号3343",
                "templateContent": (
                    "请以{number}字数生成{province}省相关简介\naaa(eee) bbbb((xxx))"
                ),
                "content": (
                    "请以{number}字数生成{province}省相关简介\naaa(eee) bbbb5275"
                ),
                "templateVariables": "xxx",
                "labels": [{"labelId": 138, "labelName": "sxz1", "color": ""}],
                "creatorName": "",
                "type": 2,
                "sceneType": 1,
                "frameworkType": 0,
            },
            "status": 200,
            "success": True,
        }
    )


@app.route(Consts.PromptUpdateAPI, methods=["POST"])
@iam_auth_checker
def prompt_update():
    return json_response(
        {
            "log_id": "9sh0grwe6ydfi318",
            "result": {
                "templateId": 1733,
                "templatePK": f"pt-{generate_letter_num_random_id()}",
            },
            "status": 200,
            "success": True,
        }
    )


@app.route(Consts.PromptDeleteAPI, methods=["POST"])
@iam_auth_checker
def prompt_delete():
    return json_response(
        {"log_id": "pws9pkrncvjesmmn", "result": True, "status": 200, "success": True}
    )


@app.route(Consts.PromptListAPI, methods=["POST"])
@iam_auth_checker
def prompt_list():
    name = request.json.get("name", None)
    if name is not None:
        if "txt2img" in name:
            return json_response(
                {
                    "log_id": "4235xa2mjupupcwe",
                    "result": {
                        "total": 239,
                        "items": [
                            {
                                "templateId": 724,
                                "templatePK": f"pt-{generate_letter_num_random_id()}",
                                "templateName": name,
                                "templateContent": "txt2img template {badvar} ((v1))",
                                "templateVariables": "v1",
                                "variableIdentifier": "(())",
                                "negativeTemplateContent": "negative ((v3))",
                                "negativeTemplateVariables": "v3",
                                "labels": [
                                    {
                                        "labelId": 188,
                                        "labelName": "图像生成",
                                        "color": "#0099E6",
                                    }
                                ],
                                "creatorName": "ut",
                                "type": 1,
                                "sceneType": 2,
                                "frameworkType": 0,
                            },
                        ],
                    },
                    "status": 200,
                    "success": True,
                }
            )
        else:
            return json_response(
                {
                    "log_id": "8cpba3jt9svbk81d",
                    "result": {
                        "total": 24,
                        "items": [
                            {
                                "templateId": 11831,
                                "templatePK": f"pt-{generate_letter_num_random_id()}",
                                "templateName": "example_prompt",
                                "templateContent": "template (v1) {v2} (v3)",
                                "templateVariables": "v1",
                                "variableIdentifier": "()",
                                "labels": [
                                    {
                                        "labelId": 150,
                                        "labelName": "test_label",
                                        "color": "#0099E6",
                                    }
                                ],
                                "creatorName": "ut",
                                "type": 2,
                                "sceneType": 1,
                                "frameworkType": 2,
                            },
                            {
                                "templateId": 11827,
                                "templatePK": f"pt-{generate_letter_num_random_id()}",
                                "templateName": name,
                                "templateContent": "example template {var1}",
                                "templateVariables": "var1",
                                "variableIdentifier": "{}",
                                "labels": [
                                    {
                                        "labelId": 150,
                                        "labelName": "test",
                                        "color": "#0099E6",
                                    }
                                ],
                                "creatorName": "ut",
                                "type": 2,
                                "sceneType": 1,
                                "frameworkType": 0,
                            },
                        ],
                    },
                    "status": 200,
                    "success": True,
                }
            )
    return json_response(
        {
            "log_id": "4235xa2mjupupcwe",
            "result": {
                "total": 239,
                "items": [
                    {
                        "templateId": 724,
                        "templatePK": f"pt-{generate_letter_num_random_id()}",
                        "templateName": "照片写实2",
                        "templateContent": (
                            "Cherry Blossoms in Hokkaido in the wintertime, Canon RF"
                            " 16mm f:2.8 STM Lens, hyperrealistic photography, style of"
                            " unsplash and National Geographic"
                        ),
                        "templateVariables": "",
                        "variableIdentifier": "{}",
                        "negativeTemplateContent": (
                            "owres,bad anatomy,cropped,worst quality,low quality,normal"
                            " quality,blurry,blurry,sketches"
                        ),
                        "labels": [
                            {
                                "labelId": 150,
                                "labelName": "图像生成",
                                "color": "#0099E6",
                            }
                        ],
                        "creatorName": "",
                        "type": 1,
                        "sceneType": 2,
                        "frameworkType": 0,
                    },
                    {
                        "templateId": 723,
                        "templatePK": f"pt-{generate_letter_num_random_id()}",
                        "templateName": "3D角色",
                        "templateContent": (
                            "snowing winter, super cute baby pixar style white fairy"
                            " bear, shiny snow-white fluffy, big bright eyes, wearing a"
                            " woolly cyan hat, delicate and fine, high detailed, bright"
                            " color, natural light, simple background, octane render,"
                            " ultra wide angle, 8K"
                        ),
                        "templateVariables": "",
                        "variableIdentifier": "{}",
                        "negativeTemplateContent": (
                            "(worst quality, low quality:1.4),signature, watermark,"
                            " simple background, dated, low res, line art, flat colors"
                        ),
                        "labels": [
                            {
                                "labelId": 150,
                                "labelName": "图像生成",
                                "color": "#0099E6",
                            }
                        ],
                        "creatorName": "",
                        "type": 1,
                        "sceneType": 2,
                        "frameworkType": 0,
                    },
                ],
            },
            "status": 200,
            "success": True,
        }
    )


@app.route(Consts.PromptLabelListAPI, methods=["POST"])
@iam_auth_checker
def prompt_label_list():
    return json_response(
        {
            "log_id": "eauyfgtgqfqdu25z",
            "result": {
                "items": [
                    {
                        "labelId": 139,
                        "createTime": "2023-10-08T11:02:51+08:00",
                        "updateTime": "2023-10-08T11:02:51+08:00",
                        "labelName": "sxz2",
                        "creatorName": "",
                        "type": 2,
                    },
                    {
                        "labelId": 138,
                        "createTime": "2023-10-08T11:02:25+08:00",
                        "updateTime": "2023-10-08T11:02:25+08:00",
                        "labelName": "sxz1",
                        "creatorName": "",
                        "type": 2,
                    },
                    {
                        "labelId": 2,
                        "createTime": "2023-05-29T18:42:44+08:00",
                        "updateTime": "2023-05-29T18:42:44+08:00",
                        "labelName": "label2",
                        "creatorName": "",
                        "type": 2,
                    },
                ],
                "total": 30,
            },
            "status": 200,
            "success": True,
        }
    )


origin_data_source_id = "0"
new_data_source_id = "0"


@app.route(Consts.DatasetCreateETLTaskAPI, methods=["POST"])
@iam_auth_checker
def create_dataset_etl_task():
    global origin_data_source_id, new_data_source_id
    origin_data_source_id = request.json["sourceDatasetId"]
    new_data_source_id = request.json["destDatasetId"]
    return json_response(
        {"log_id": "i9vswaefzbqpu92d", "result": True, "status": 200, "success": True}
    )


@app.route(Consts.DatasetETLTaskInfoAPI, methods=["POST"])
@iam_auth_checker
def get_dataset_etl_task_info():
    global origin_data_source_id, new_data_source_id
    return json_response(
        {
            "log_id": "44k3yj73ms178179",
            "result": {
                "id": request.json["etlId"],
                "userId": 113,
                "sourceDatasetStrId": origin_data_source_id,
                "destDatasetStrId": new_data_source_id,
                "taskId": 5331,
                "entityCount": 1,
                "entityType": 2,
                "operationsV2": {
                    "clean": [
                        {"name": "remove_invisible_character", "args": {}},
                        {"name": "replace_uniform_whitespace", "args": {}},
                        {"name": "remove_non_meaning_characters", "args": {}},
                        {
                            "name": "replace_traditional_chinese_to_simplified",
                            "args": {},
                        },
                        {"name": "remove_web_identifiers", "args": {}},
                        {"name": "remove_emoji", "args": {}},
                        {"name": "save_pipeline_clean", "args": {}},
                    ],
                    "deduplication": [
                        {"name": "deduplication_simhash", "args": {"distance": 5.6511}},
                        {"name": "save_pipeline_deduplication", "args": {}},
                    ],
                    "desensitization": [
                        {"name": "replace_emails", "args": {}},
                        {"name": "replace_ip", "args": {}},
                        {"name": "replace_identifier", "args": {}},
                        {"name": "save_pipeline_desensitization", "args": {}},
                    ],
                    "filter": [
                        {
                            "name": "filter_check_number_words",
                            "args": {
                                "number_words_max_cutoff": 10000,
                                "number_words_min_cutoff": 2.2,
                            },
                        },
                        {
                            "name": "filter_check_character_repetition_removal",
                            "args": {"default_character_repetition_max_cutoff": 0.2},
                        },
                        {
                            "name": "filter_check_word_repetition_removal",
                            "args": {"word_repetition_max_cutoff": 0.6},
                        },
                        {
                            "name": "filter_check_special_characters",
                            "args": {"special_characters_max_cutoff": 0.3},
                        },
                        {
                            "name": "filter_check_flagged_words",
                            "args": {"flagged_words_max_cutoff": 0.50556},
                        },
                        {
                            "name": "filter_check_lang_id",
                            "args": {"lang_id_min_cutoff": 0.5},
                        },
                        {
                            "name": "filter_check_perplexity",
                            "args": {"perplexity_max_cutoff": 1110},
                        },
                        {"name": "save_pipeline_filter", "args": {}},
                    ],
                },
                "result": {
                    "RET_OK": 0,
                    "pipeline_stage_result": {
                        "clean": {
                            "status": "Success",
                            "operator_count": 6,
                            "entity_match_count": 1,
                            "each_operator_result": [
                                {
                                    "name": "remove_invisible_character",
                                    "remaining_count": 1,
                                    "drop_count": 0,
                                },
                                {
                                    "name": "replace_uniform_whitespace",
                                    "remaining_count": 1,
                                    "drop_count": 0,
                                },
                                {
                                    "name": "remove_non_meaning_characters",
                                    "remaining_count": 1,
                                    "drop_count": 0,
                                },
                                {
                                    "name": "replace_traditional_chinese_to_simplified",
                                    "remaining_count": 1,
                                    "drop_count": 0,
                                },
                                {
                                    "name": "remove_web_identifiers",
                                    "remaining_count": 1,
                                    "drop_count": 0,
                                },
                                {
                                    "name": "remove_emoji",
                                    "remaining_count": 1,
                                    "drop_count": 0,
                                },
                            ],
                        },
                        "deduplication": {
                            "status": "Success",
                            "operator_count": 1,
                            "entity_match_count": 0,
                            "each_operator_result": [
                                {
                                    "name": "deduplication_simhash",
                                    "remaining_count": 0,
                                    "drop_count": 0,
                                }
                            ],
                        },
                        "desensitization": {
                            "status": "Success",
                            "operator_count": 3,
                            "entity_match_count": 0,
                            "each_operator_result": [
                                {
                                    "name": "replace_emails",
                                    "remaining_count": 0,
                                    "drop_count": 0,
                                },
                                {
                                    "name": "replace_ip",
                                    "remaining_count": 0,
                                    "drop_count": 0,
                                },
                                {
                                    "name": "replace_identifier",
                                    "remaining_count": 0,
                                    "drop_count": 0,
                                },
                            ],
                        },
                        "filter": {
                            "status": "Success",
                            "operator_count": 7,
                            "entity_match_count": 1,
                            "each_operator_result": [
                                {
                                    "name": "filter_check_number_words",
                                    "remaining_count": 1,
                                    "drop_count": 0,
                                },
                                {
                                    "name": "filter_check_character_repetition_removal",
                                    "remaining_count": 0,
                                    "drop_count": 1,
                                },
                                {
                                    "name": "filter_check_word_repetition_removal",
                                    "remaining_count": 1,
                                    "drop_count": 0,
                                },
                                {
                                    "name": "filter_check_special_characters",
                                    "remaining_count": 1,
                                    "drop_count": 0,
                                },
                                {
                                    "name": "filter_check_flagged_words",
                                    "remaining_count": 1,
                                    "drop_count": 0,
                                },
                                {
                                    "name": "filter_check_lang_id",
                                    "remaining_count": 1,
                                    "drop_count": 0,
                                },
                                {
                                    "name": "filter_check_perplexity",
                                    "remaining_count": 1,
                                    "drop_count": 0,
                                },
                            ],
                        },
                    },
                    "export_entity_num": 0,
                    "remaining_entity": 0,
                    "unprocessed_entity": 0,
                    "remove_emoji": {"processed_entity": 0},
                    "remove_url": {"processed_entity": 0},
                    "trad_to_simp": {"processed_entity": 0},
                    "remove_id_card": {"processed_entity": 0},
                    "remove_phone_number": {"processed_entity": 0},
                    "remove_exception_char": {"processed_entity": 0},
                    "replace_sim2trad": {"processed_entity": 0},
                    "replace_trad2sim": {"processed_entity": 0},
                    "replace_upper2lower": {"processed_entity": 0},
                    "cut": {"remaining_entity": 0, "unprocessed_entity": 0},
                    "failReason": "",
                    "pauseReason": "",
                },
                "processStatus": 2,
                "status": 0,
                "createTime": "2023-11-06T14:31:03+08:00",
                "finishTime": "2023-11-06T14:32:11+08:00",
                "creatorName": "yyw02",
                "sourceDatasetName": "4train_generic_usrBos-V1",
                "destDatasetName": "4train_generic_sysBos-V1",
                "etlResult": "",
                "remainingEntity": 0,
                "exceptionResult": "",
                "startTime": "2023-11-06 14:31:03",
                "endTime": "2023-11-06 14:32:11",
                "modifyTime": "2023-11-06 14:32:11",
                "logPath": "path",
            },
            "status": 200,
            "success": True,
        }
    )


@app.route(Consts.DatasetETLListTaskAPI, methods=["POST"])
@iam_auth_checker
def get_dataset_etl_task_list():
    global origin_data_source_id, new_data_source_id
    return json_response(
        {
            "log_id": "wwcm30w7exxexyqx",
            "result": {
                "processingCount": 1,
                "items": [
                    {
                        "etlStrId": 275,
                        "startTime": "2023-11-06 16:03:23",
                        "sourceDatasetName": "4train_generic_usrBos-V1",
                        "destDatasetName": "4train_generic_sysBos-V1",
                        "operatorNameList": [
                            "remove_invisible_character",
                            "replace_uniform_whitespace",
                            "remove_non_meaning_characters",
                            "replace_traditional_chinese_to_simplified",
                            "remove_web_identifiers",
                            "remove_emoji",
                            "deduplication_simhash",
                            "replace_emails",
                            "replace_ip",
                            "replace_identifier",
                            "filter_check_number_words",
                            "filter_check_character_repetition_removal",
                            "filter_check_word_repetition_removal",
                            "filter_check_special_characters",
                            "filter_check_flagged_words",
                            "filter_check_lang_id",
                            "filter_check_perplexity",
                        ],
                        "sourceDatasetStrId": origin_data_source_id,
                        "destDatasetStrId": new_data_source_id,
                        "entityCount": 1,
                        "entityType": 2,
                        "result": {
                            "RET_OK": 0,
                            "pipeline_stage_result": None,
                            "export_entity_num": 0,
                            "remaining_entity": 0,
                            "unprocessed_entity": 0,
                            "remove_emoji": {"processed_entity": 0},
                            "remove_url": {"processed_entity": 0},
                            "trad_to_simp": {"processed_entity": 0},
                            "remove_id_card": {"processed_entity": 0},
                            "remove_phone_number": {"processed_entity": 0},
                            "remove_exception_char": {"processed_entity": 0},
                            "replace_sim2trad": {"processed_entity": 0},
                            "replace_trad2sim": {"processed_entity": 0},
                            "replace_upper2lower": {"processed_entity": 0},
                            "cut": {"remaining_entity": 0, "unprocessed_entity": 0},
                            "failReason": "",
                            "pauseReason": "",
                        },
                        "processStatus": 2,
                        "status": 0,
                        "errCode": 0,
                        "errMsg": "",
                        "createTime": "0001-01-01T00:00:00Z",
                        "finishTime": "0001-01-01T00:00:00Z",
                        "modifyTime": "0001-01-01T00:00:00Z",
                    }
                ],
                "total": 1,
            },
            "status": 200,
            "success": True,
        }
    )


@app.route(Consts.DatasetETLTaskDeleteAPI, methods=["POST"])
@iam_auth_checker
def delete_dataset_etl_task():
    return json_response(
        {"log_id": "i9vswaefzbqpu92d", "result": True, "status": 200, "success": True}
    )


@app.route(Consts.DatasetCreateAugTaskAPI, methods=["POST"])
@iam_auth_checker
def create_dataset_augmenting_task():
    return json_response(
        {"log_id": "514mkkutaquh4fvq", "result": True, "status": 200, "success": True}
    )


@app.route(Consts.DatasetAugListTaskAPI, methods=["POST"])
@iam_auth_checker
def get_dataset_aug_task_list():
    return json_response(
        {
            "log_id": "x5bnzd1g2fi3iiz9",
            "result": {
                "total": 45,
                "items": [
                    {
                        "id": 241,
                        "projectType": 20,
                        "sourceDatasetStrId": "2343",
                        "sourceDatasetName": "sys_bos数据集1106-V1",
                        "destDatasetStrId": "2431",
                        "destDatasetName": "werwrewrwe-V2",
                        "area": 0,
                        "status": 4,
                        "strategy": 0,
                        "operations": "",
                        "startTime": "2023-11-08 10:44:21",
                        "finishTime": "2023-11-08 10:44:56",
                        "failReason": "对象存储访问异常",
                        "isSelfInstruct": True,
                        "name": "3334",
                        "modelName": "ERNIE-3.5-8K",
                    },
                    {
                        "id": 240,
                        "projectType": 20,
                        "sourceDatasetStrId": "2324",
                        "sourceDatasetName": "3-V2",
                        "destDatasetStrId": "2343",
                        "destDatasetName": "sys_bos数据集1106-V1",
                        "area": 0,
                        "status": 3,
                        "strategy": 0,
                        "operations": "",
                        "startTime": "2023-11-08 10:43:55",
                        "finishTime": "2023-11-08 10:44:02",
                        "failReason": "",
                        "isSelfInstruct": True,
                        "name": "357",
                        "modelName": "ERNIE-3.5-8K",
                    },
                ],
            },
            "status": 200,
            "success": True,
        }
    )


@app.route(Consts.DatasetAugTaskInfoAPI, methods=["POST"])
@iam_auth_checker
def get_dataset_augmenting_task_info():
    return json_response(
        {
            "log_id": "cg7tfntkmkwevpgs",
            "result": {
                "id": request.json["taskId"],
                "sourceDatasetStrId": "1902",
                "destDatasetStrId": "2325",
                "sourceDatasetName": "augment_0922_1-V1",
                "destDatasetName": "54-V5",
                "labelIds": "",
                "status": 4,
                "area": 0,
                "entityCount": 651,
                "strategy": 0,
                "operations": "",
                "retStr": "对象存储访问异常",
                "startTime": "2023-11-02 14:55:12",
                "finishTime": "2023-11-02 14:56:05",
                "isSelfInstruct": True,
                "name": "augment_1102_2",
                "serviceName": "ERNIE-Bot",
                "appName": "文心千帆showcase123",
                "userName": "百里慕蕊",
                "numSeedFewshot": 6,
                "numInstancesToGenerate": 20,
                "similarityThreshold": 0.6,
            },
            "status": 200,
            "success": True,
        }
    )


@app.route(Consts.DatasetAugTaskDeleteAPI, methods=["POST"])
@iam_auth_checker
def delete_dataset_augmenting_task():
    return json_response(
        {"log_id": "514mkkutaquh4fvq", "result": True, "status": 200, "success": True}
    )


@app.route(Consts.DatasetAnnotateAPI, methods=["POST"])
@iam_auth_checker
def annotate_an_entity():
    return json_response(
        {"log_id": "x7wwxwhykirrt30n", "result": True, "status": 200, "success": True}
    )


@app.route(Consts.DatasetEntityDeleteAPI, methods=["POST"])
@iam_auth_checker
def delete_an_entity():
    return json_response(
        {
            "log_id": "d9vkbs591be1u4ms",
            "result": {"failedOnes": None},
            "status": 200,
            "success": True,
        }
    )


@app.route(Consts.DatasetEntityListAPI, methods=["POST"])
@iam_auth_checker
def list_all_entity_in_dataset():
    return json_response(
        {
            "log_id": "15jk2d6tkisnidt9",
            "result": {
                "totalAll": 7,
                "total": 2,
                "items": [
                    {
                        "id": "aaa",
                        "name": "",
                        "labels": [
                            {
                                "label_id": "654887c72733b0c09e2d5bc0",
                                "name": "ERNIE_BOT",
                                "color": "#1A73E8",
                            }
                        ],
                        "url": "url1",
                        "memorySize": 0.01,
                        "isEncrypted": False,
                        "textExtra": {
                            "domainType": "",
                            "taskType": "",
                            "wordNum": 0,
                            "repetitiveCharRatio": 0,
                            "specialCharRatio": 0,
                            "flaggedWordRatio": 0,
                            "langProb": 0,
                            "perplexity": 0,
                        },
                    },
                    {
                        "id": "bbb",
                        "name": "",
                        "labels": [
                            {
                                "label_id": "654887c72733b0c09e2d5bc0",
                                "name": "ERNIE_BOT",
                                "color": "#1A73E8",
                            }
                        ],
                        "url": "url2",
                        "memorySize": 0.01,
                        "isEncrypted": False,
                        "textExtra": {
                            "domainType": "",
                            "taskType": "",
                            "wordNum": 0,
                            "repetitiveCharRatio": 0,
                            "specialCharRatio": 0,
                            "flaggedWordRatio": 0,
                            "langProb": 0,
                            "perplexity": 0,
                        },
                    },
                ],
            },
            "status": 200,
            "success": True,
        }
    )


@app.route("/mock/hub/prompt", methods=["GET"])
def mock_hub_file():
    buffer = BytesIO()
    content = """{
    "sdk_version": "0.2.0",
    "obj": {
        "module": "qianfan.common.prompt.prompt",
        "type": "Prompt",
        "args": {
            "name": "穿搭灵感",
            "template": "请推荐三套{style}适合通勤的{gender}衣着搭配",
            "variables": [
                "style",
                "gender"
            ],
            "labels": [
                {
                    "module": "qianfan.common.prompt.prompt",
                    "type": "PromptLabel",
                    "args": {
                        "id": 1734,
                        "name": "生活助手",
                        "color": "#2468F2"
                    }
                }
            ],
            "identifier": "{}",
            "type": {
                "module": "qianfan.consts",
                "type": "PromptType",
                "args": {
                    "value": 1
                }
            },
            "scene_type": {
                "module": "qianfan.consts",
                "type": "PromptSceneType",
                "args": {
                    "value": 1
                }
            },
            "framework_type": {
                "module": "qianfan.consts",
                "type": "PromptFrameworkType",
                "args": {
                    "value": 0
                }
            },
            "creator_name": ""
        }
    }
}"""
    buffer.write(bytes(content, "utf-8"))
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="prompt.json")


@app.route(Consts.ModelAPIPrefix + "/erniebot/plugins", methods=["POST"])
def eb_plugin():
    return json_response(
        {
            "id": "as-sky7jr2cay",
            "object": "chat.completion",
            "created": 1703036786,
            "result": (
                "以下是我对图片的理解：\n图中是一条笔直的公路，路旁有黄色的交通柱，"
                "天空上有白云，太阳已经落下，天空呈现出蓝色。"
                "\n可以参考下面的提问方式:\n示例1) 请根据图片描述，"
                "写一篇500字以上的文章，描述这幅图片带来的情感和感受。\n示例2)"
                " 请根据图片描述，创作一篇500字以上的短篇小说，描述图中场景，人物心情，"
                "以及可能发生的故事。\n示例3) 请根据图片内容，创作一首5句以上的现代诗，"
                "表达对这幅图片的感受和情感。\n"
            ),
            "is_truncated": False,
            "need_clear_history": False,
            "plugin_info": [
                {
                    "plugin_id": "1069:1.0.0",
                    "plugin_name": "",
                    "plugin_req": '{"query":"","history":"[]","url":"https://ebui-cdn.bj.bcebos.com/showcase/pluginDemo/imageTalk2.jpg"}',
                    "plugin_resp": "",
                    "status": "1",
                    "api_id": "ImageAI.QA",
                },
                {
                    "plugin_id": "1069:1.0.0",
                    "plugin_name": "",
                    "plugin_req": '{"query":"","history":"[]","url":"https://ebui-cdn.bj.bcebos.com/showcase/pluginDemo/imageTalk2.jpg"}',
                    "plugin_resp": '{"errCode":0,"errMsg":"success","status":"StartFileparser","rawText":"","actionName":"解析图片","actionContent":"开始图片解析","usage":null,"eventName":"event"}',
                    "status": "1",
                    "api_id": "ImageAI.QA",
                },
                {
                    "plugin_id": "1069:1.0.0",
                    "plugin_name": "",
                    "plugin_req": '{"query":"","history":"[]","url":"https://ebui-cdn.bj.bcebos.com/showcase/pluginDemo/imageTalk2.jpg"}',
                    "plugin_resp": '{"errCode":0,"errMsg":"success","status":"StartFileparser","rawText":"","actionName":"解析图片","actionContent":"开始图片解析","usage":null,"eventName":"event"}\n{"errCode":0,"errMsg":"success","status":"","rawText":"","actionName":"解析图片","actionContent":"图片解析完成","usage":null,"eventName":"event"}',
                    "status": "1",
                    "api_id": "ImageAI.QA",
                },
                {
                    "plugin_id": "1069:1.0.0",
                    "plugin_name": "",
                    "plugin_req": '{"query":"","history":"[]","url":"https://ebui-cdn.bj.bcebos.com/showcase/pluginDemo/imageTalk2.jpg"}',
                    "plugin_resp": '{"errCode":0,"errMsg":"success","status":"StartFileparser","rawText":"","actionName":"解析图片","actionContent":"开始图片解析","usage":null,"eventName":"event"}\n{"errCode":0,"errMsg":"success","status":"","rawText":"","actionName":"解析图片","actionContent":"图片解析完成","usage":null,"eventName":"event"}',
                    "status": "1",
                    "api_id": "ImageAI.QA",
                },
                {
                    "plugin_id": "1069:1.0.0",
                    "plugin_name": "",
                    "plugin_req": '{"query":"","history":"[]","url":"https://ebui-cdn.bj.bcebos.com/showcase/pluginDemo/imageTalk2.jpg"}',
                    "plugin_resp": '{"errCode":0,"errMsg":"success","status":"StartFileparser","rawText":"","actionName":"解析图片","actionContent":"开始图片解析","usage":null,"eventName":"event"}\n{"errCode":0,"errMsg":"success","status":"","rawText":"","actionName":"解析图片","actionContent":"图片解析完成","usage":null,"eventName":"event"}\n{"errCode":0,"errMsg":"success","status":"","rawText":"REMOVED","actionName":"","actionContent":"","usage":{"total_tokens":174},"eventName":"message"}\n{"errCode":0,"errMsg":"","status":"","rawText":"","actionName":"","actionContent":"","usage":{"total_tokens":174},"eventName":"lastMessage"}',
                    "status": "2",
                    "api_id": "ImageAI.QA",
                },
            ],
            "plugin_metas": [
                {
                    "pluginMameForModel": "",
                    "pluginNameForHuman": "说图解画",
                    "operationId": "QA",
                    "pluginVersion": "1.0.0",
                    "pluginId": "1069:1.0.0",
                    "apiId": "ImageAI.QA",
                    "logoUrl": "https://imagetalks.bj.bcebos.com/ImageTalks.png",
                    "uiMeta": "",
                }
            ],
            "usage": {
                "prompt_tokens": 42,
                "completion_tokens": 124,
                "total_tokens": 166,
                "plugins": [
                    {
                        "name": "ImageAI",
                        "parse_tokens": 0,
                        "abstract_tokens": 0,
                        "search_tokens": 0,
                        "total_tokens": 174,
                    }
                ],
            },
        }
    )


@app.route(Consts.ModelAPIPrefix + "/erniebot/plugin", methods=["POST"])
def eb_plugin_v2():
    if request.json.get("stream"):
        return flask.Response(
            eb_plugin_stream(),
            mimetype="text/event-stream",
        )

    return json_response(
        {
            "id": "as-sky7jr2cay",
            "object": "chat.completion",
            "created": 1703036786,
            "result": (
                "以下是我对图片的理解：\n图中是一条笔直的公路，路旁有黄色的交通柱，"
                "天空上有白云，太阳已经落下，天空呈现出蓝色。"
                "\n可以参考下面的提问方式:\n示例1) 请根据图片描述，"
                "写一篇500字以上的文章，描述这幅图片带来的情感和感受。\n示例2)"
                " 请根据图片描述，创作一篇500字以上的短篇小说，描述图中场景，人物心情，"
                "以及可能发生的故事。\n示例3) 请根据图片内容，创作一首5句以上的现代诗，"
                "表达对这幅图片的感受和情感。\n"
            ),
            "is_truncated": False,
            "need_clear_history": False,
            "plugin_info": [
                {
                    "plugin_id": "1069:1.0.0",
                    "plugin_name": "",
                    "plugin_req": '{"query":"","history":"[]","url":"https://ebui-cdn.bj.bcebos.com/showcase/pluginDemo/imageTalk2.jpg"}',
                    "plugin_resp": "",
                    "status": "1",
                    "api_id": "ImageAI.QA",
                },
                {
                    "plugin_id": "1069:1.0.0",
                    "plugin_name": "",
                    "plugin_req": '{"query":"","history":"[]","url":"https://ebui-cdn.bj.bcebos.com/showcase/pluginDemo/imageTalk2.jpg"}',
                    "plugin_resp": '{"errCode":0,"errMsg":"success","status":"StartFileparser","rawText":"","actionName":"解析图片","actionContent":"开始图片解析","usage":null,"eventName":"event"}',
                    "status": "1",
                    "api_id": "ImageAI.QA",
                },
                {
                    "plugin_id": "1069:1.0.0",
                    "plugin_name": "",
                    "plugin_req": '{"query":"","history":"[]","url":"https://ebui-cdn.bj.bcebos.com/showcase/pluginDemo/imageTalk2.jpg"}',
                    "plugin_resp": '{"errCode":0,"errMsg":"success","status":"StartFileparser","rawText":"","actionName":"解析图片","actionContent":"开始图片解析","usage":null,"eventName":"event"}\n{"errCode":0,"errMsg":"success","status":"","rawText":"","actionName":"解析图片","actionContent":"图片解析完成","usage":null,"eventName":"event"}',
                    "status": "1",
                    "api_id": "ImageAI.QA",
                },
                {
                    "plugin_id": "1069:1.0.0",
                    "plugin_name": "",
                    "plugin_req": '{"query":"","history":"[]","url":"https://ebui-cdn.bj.bcebos.com/showcase/pluginDemo/imageTalk2.jpg"}',
                    "plugin_resp": '{"errCode":0,"errMsg":"success","status":"StartFileparser","rawText":"","actionName":"解析图片","actionContent":"开始图片解析","usage":null,"eventName":"event"}\n{"errCode":0,"errMsg":"success","status":"","rawText":"","actionName":"解析图片","actionContent":"图片解析完成","usage":null,"eventName":"event"}',
                    "status": "1",
                    "api_id": "ImageAI.QA",
                },
                {
                    "plugin_id": "1069:1.0.0",
                    "plugin_name": "",
                    "plugin_req": '{"query":"","history":"[]","url":"https://ebui-cdn.bj.bcebos.com/showcase/pluginDemo/imageTalk2.jpg"}',
                    "plugin_resp": '{"errCode":0,"errMsg":"success","status":"StartFileparser","rawText":"","actionName":"解析图片","actionContent":"开始图片解析","usage":null,"eventName":"event"}\n{"errCode":0,"errMsg":"success","status":"","rawText":"","actionName":"解析图片","actionContent":"图片解析完成","usage":null,"eventName":"event"}\n{"errCode":0,"errMsg":"success","status":"","rawText":"REMOVED","actionName":"","actionContent":"","usage":{"total_tokens":174},"eventName":"message"}\n{"errCode":0,"errMsg":"","status":"","rawText":"","actionName":"","actionContent":"","usage":{"total_tokens":174},"eventName":"lastMessage"}',
                    "status": "2",
                    "api_id": "ImageAI.QA",
                },
            ],
            "plugin_metas": [
                {
                    "pluginMameForModel": "",
                    "pluginNameForHuman": "说图解画",
                    "operationId": "QA",
                    "pluginVersion": "1.0.0",
                    "pluginId": "1069:1.0.0",
                    "apiId": "ImageAI.QA",
                    "logoUrl": "https://imagetalks.bj.bcebos.com/ImageTalks.png",
                    "uiMeta": "",
                }
            ],
            "usage": {
                "prompt_tokens": 42,
                "completion_tokens": 124,
                "total_tokens": 166,
                "plugins": [
                    {
                        "name": "ImageAI",
                        "parse_tokens": 0,
                        "abstract_tokens": 0,
                        "search_tokens": 0,
                        "total_tokens": 174,
                    }
                ],
            },
        }
    )


def eb_plugin_stream():
    """
    mock stream response
    """
    mock_plugin_stream_result = [
        r"event: pluginMeta",
        (
            r"data:"
            r' {"id":"as-hdpadsaghd","object":"chat.completion","created":1705585098,"sentence_id":0,"plugin_metas":[{"apiId":"eChart.plot","logoUrl":"https://echarts.bj.bcebos.com/prod/echarts-logo.png","operationId":"plot","pluginId":"1066:1.0.1","pluginNameForHuman":"E言易图","pluginNameForModel":"eChart","pluginVersion":"1.0.1","runtimeMetaInfo":{"function_call":{"arguments":"{\"query\":\"请按照下面要求给我生成雷达图：学校教育质量:'
            r" 维度：师资力量、设施、课程内容、学生满意度。对象：A,B,C三所学校。"
            r"学校A的师资力量得分为10分，设施得分为8分，课程内容的得分为7分，"
            r"学生满意度的得分为9分。\\n* 学校B的师资力量得分为8分，设施得分为9分，"
            r"课程内容的得分为8分，学生满意度的得分为7分。\\n*"
            r" 学校C的师资力量得分为7分，设施得分为7分，课程内容的得分为9分，"
            r"学生满意度的得分为8分。"
            r"\",\"title\":\"学校教育质量\",\"chartType\":\"radar\",\"data\":\"学校A的师资力量得分为10分，"
            r"设施得分为8分，课程内容的得分为7分，学生满意度的得分为9分。\\n*"
            r" 学校B的师资力量得分为8分，设施得分为9分，课程内容的得分为8分，"
            r"学生满意度的得分为7分。\\n* 学校C的师资力量得分为7分，设施得分为7分，"
            r"课程内容的得分为9分，学生满意度的得分为8分。"
            r'\"}","name":"eChart.plot","thoughts":"这是一个图表绘制需求"},"returnRawFieldName":"option","thoughts":"这是一个图表绘制需求"},"uiMeta":null}]}'
        ),
        r"event: plugin",
        (
            r"data:"
            r' {"id":"as-hdpadsaghd","object":"chat.completion","created":1705585098,"sentence_id":0,"plugin_info":[{"plugin_id":"1066:1.0.1","plugin_name":"","plugin_req":"{\"data\":\"学校A的师资力量得分为10分，'
            r"设施得分为8分，课程内容的得分为7分，学生满意度的得分为9分。\\n*"
            r" 学校B的师资力量得分为8分，设施得分为9分，课程内容的得分为8分，"
            r"学生满意度的得分为7分。\\n* 学校C的师资力量得分为7分，设施得分为7分，"
            r"课程内容的得分为9分，学生满意度的得分为8分。"
            r"\",\"query\":\"请按照下面要求给我生成雷达图：学校教育质量:"
            r" 维度：师资力量、设施、课程内容、学生满意度。对象：A,B,C三所学校。"
            r"学校A的师资力量得分为10分，设施得分为8分，课程内容的得分为7分，"
            r"学生满意度的得分为9分。\\n* 学校B的师资力量得分为8分，设施得分为9分，"
            r"课程内容的得分为8分，学生满意度的得分为7分。\\n*"
            r" 学校C的师资力量得分为7分，设施得分为7分，课程内容的得分为9分，"
            r"学生满意度的得分为8分。"
            r'\",\"chartType\":\"radar\",\"title\":\"学校教育质量\",\"last_bot_message\":\"\"}","plugin_resp":"","status":"1","api_id":"eChart.plot"}]}'
        ),
        r"event: plugin",
        (
            r"data:"
            r' {"id":"as-hdpadsaghd","object":"chat.completion","created":1705585098,"sentence_id":1,"plugin_info":[{"plugin_id":"1066:1.0.1","plugin_name":"","plugin_req":"{\"data\":\"学校A的师资力量得分为10分，'
            r"设施得分为8分，课程内容的得分为7分，学生满意度的得分为9分。\\n*"
            r" 学校B的师资力量得分为8分，设施得分为9分，课程内容的得分为8分，"
            r"学生满意度的得分为7分。\\n* 学校C的师资力量得分为7分，设施得分为7分，"
            r"课程内容的得分为9分，学生满意度的得分为8分。"
            r"\",\"query\":\"请按照下面要求给我生成雷达图：学校教育质量:"
            r" 维度：师资力量、设施、课程内容、学生满意度。对象：A,B,C三所学校。"
            r"学校A的师资力量得分为10分，设施得分为8分，课程内容的得分为7分，"
            r"学生满意度的得分为9分。\\n* 学校B的师资力量得分为8分，设施得分为9分，"
            r"课程内容的得分为8分，学生满意度的得分为7分。\\n*"
            r" 学校C的师资力量得分为7分，设施得分为7分，课程内容的得分为9分，"
            r"学生满意度的得分为8分。"
            r'\",\"chartType\":\"radar\",\"title\":\"学校教育质量\",\"last_bot_message\":\"\"}","plugin_resp":"{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"数据分析\",\"actionContent\":\"数据分析中\"}","status":"1","api_id":"eChart.plot"}]}'
        ),
        r"event: plugin",
        (
            r"data:"
            r' {"id":"as-hdpadsaghd","object":"chat.completion","created":1705585103,"sentence_id":2,"plugin_info":[{"plugin_id":"1066:1.0.1","plugin_name":"","plugin_req":"{\"data\":\"学校A的师资力量得分为10分，'
            r"设施得分为8分，课程内容的得分为7分，学生满意度的得分为9分。\\n*"
            r" 学校B的师资力量得分为8分，设施得分为9分，课程内容的得分为8分，"
            r"学生满意度的得分为7分。\\n* 学校C的师资力量得分为7分，设施得分为7分，"
            r"课程内容的得分为9分，学生满意度的得分为8分。"
            r"\",\"query\":\"请按照下面要求给我生成雷达图：学校教育质量:"
            r" 维度：师资力量、设施、课程内容、学生满意度。对象：A,B,C三所学校。"
            r"学校A的师资力量得分为10分，设施得分为8分，课程内容的得分为7分，"
            r"学生满意度的得分为9分。\\n* 学校B的师资力量得分为8分，设施得分为9分，"
            r"课程内容的得分为8分，学生满意度的得分为7分。\\n*"
            r" 学校C的师资力量得分为7分，设施得分为7分，课程内容的得分为9分，"
            r"学生满意度的得分为8分。"
            r'\",\"chartType\":\"radar\",\"title\":\"学校教育质量\",\"last_bot_message\":\"\"}","plugin_resp":"{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"数据分析\",\"actionContent\":\"数据分析中\"}","status":"1","api_id":"eChart.plot"}]}'
        ),
        r"event: plugin",
        (
            r"data:"
            r' {"id":"as-hdpadsaghd","object":"chat.completion","created":1705585108,"sentence_id":3,"plugin_info":[{"plugin_id":"1066:1.0.1","plugin_name":"","plugin_req":"{\"data\":\"学校A的师资力量得分为10分，'
            r"设施得分为8分，课程内容的得分为7分，学生满意度的得分为9分。\\n*"
            r" 学校B的师资力量得分为8分，设施得分为9分，课程内容的得分为8分，"
            r"学生满意度的得分为7分。\\n* 学校C的师资力量得分为7分，设施得分为7分，"
            r"课程内容的得分为9分，学生满意度的得分为8分。"
            r"\",\"query\":\"请按照下面要求给我生成雷达图：学校教育质量:"
            r" 维度：师资力量、设施、课程内容、学生满意度。对象：A,B,C三所学校。"
            r"学校A的师资力量得分为10分，设施得分为8分，课程内容的得分为7分，"
            r"学生满意度的得分为9分。\\n* 学校B的师资力量得分为8分，设施得分为9分，"
            r"课程内容的得分为8分，学生满意度的得分为7分。\\n*"
            r" 学校C的师资力量得分为7分，设施得分为7分，课程内容的得分为9分，"
            r"学生满意度的得分为8分。"
            r'\",\"chartType\":\"radar\",\"title\":\"学校教育质量\",\"last_bot_message\":\"\"}","plugin_resp":"{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"数据分析\",\"actionContent\":\"数据分析中\"}","status":"1","api_id":"eChart.plot"}]}'
        ),
        r"event: plugin",
        (
            r"data:"
            r' {"id":"as-hdpadsaghd","object":"chat.completion","created":1705585108,"sentence_id":4,"plugin_info":[{"plugin_id":"1066:1.0.1","plugin_name":"","plugin_req":"{\"data\":\"学校A的师资力量得分为10分，'
            r"设施得分为8分，课程内容的得分为7分，学生满意度的得分为9分。\\n*"
            r" 学校B的师资力量得分为8分，设施得分为9分，课程内容的得分为8分，"
            r"学生满意度的得分为7分。\\n* 学校C的师资力量得分为7分，设施得分为7分，"
            r"课程内容的得分为9分，学生满意度的得分为8分。"
            r"\",\"query\":\"请按照下面要求给我生成雷达图：学校教育质量:"
            r" 维度：师资力量、设施、课程内容、学生满意度。对象：A,B,C三所学校。"
            r"学校A的师资力量得分为10分，设施得分为8分，课程内容的得分为7分，"
            r"学生满意度的得分为9分。\\n* 学校B的师资力量得分为8分，设施得分为9分，"
            r"课程内容的得分为8分，学生满意度的得分为7分。\\n*"
            r" 学校C的师资力量得分为7分，设施得分为7分，课程内容的得分为9分，"
            r"学生满意度的得分为8分。"
            r'\",\"chartType\":\"radar\",\"title\":\"学校教育质量\",\"last_bot_message\":\"\"}","plugin_resp":"{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"数据分析\",\"actionContent\":\"数据分析中\"}\n{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"数据分析\",\"actionContent\":\"数据分析成功\"}","status":"1","api_id":"eChart.plot"}]}'
        ),
        r"event: plugin",
        (
            r"data:"
            r' {"id":"as-hdpadsaghd","object":"chat.completion","created":1705585108,"sentence_id":5,"plugin_info":[{"plugin_id":"1066:1.0.1","plugin_name":"","plugin_req":"{\"data\":\"学校A的师资力量得分为10分，'
            r"设施得分为8分，课程内容的得分为7分，学生满意度的得分为9分。\\n*"
            r" 学校B的师资力量得分为8分，设施得分为9分，课程内容的得分为8分，"
            r"学生满意度的得分为7分。\\n* 学校C的师资力量得分为7分，设施得分为7分，"
            r"课程内容的得分为9分，学生满意度的得分为8分。"
            r"\",\"query\":\"请按照下面要求给我生成雷达图：学校教育质量:"
            r" 维度：师资力量、设施、课程内容、学生满意度。对象：A,B,C三所学校。"
            r"学校A的师资力量得分为10分，设施得分为8分，课程内容的得分为7分，"
            r"学生满意度的得分为9分。\\n* 学校B的师资力量得分为8分，设施得分为9分，"
            r"课程内容的得分为8分，学生满意度的得分为7分。\\n*"
            r" 学校C的师资力量得分为7分，设施得分为7分，课程内容的得分为9分，"
            r"学生满意度的得分为8分。"
            r'\",\"chartType\":\"radar\",\"title\":\"学校教育质量\",\"last_bot_message\":\"\"}","plugin_resp":"{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"数据分析\",\"actionContent\":\"数据分析中\"}\n{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"数据分析\",\"actionContent\":\"数据分析成功\"}\n{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"图表绘制\",\"actionContent\":\"图表绘制中\"}","status":"1","api_id":"eChart.plot"}]}'
        ),
        r"event: plugin",
        (
            r"data:"
            r' {"id":"as-hdpadsaghd","object":"chat.completion","created":1705585108,"sentence_id":6,"plugin_info":[{"plugin_id":"1066:1.0.1","plugin_name":"","plugin_req":"{\"data\":\"学校A的师资力量得分为10分，'
            r"设施得分为8分，课程内容的得分为7分，学生满意度的得分为9分。\\n*"
            r" 学校B的师资力量得分为8分，设施得分为9分，课程内容的得分为8分，"
            r"学生满意度的得分为7分。\\n* 学校C的师资力量得分为7分，设施得分为7分，"
            r"课程内容的得分为9分，学生满意度的得分为8分。"
            r"\",\"query\":\"请按照下面要求给我生成雷达图：学校教育质量:"
            r" 维度：师资力量、设施、课程内容、学生满意度。对象：A,B,C三所学校。"
            r"学校A的师资力量得分为10分，设施得分为8分，课程内容的得分为7分，"
            r"学生满意度的得分为9分。\\n* 学校B的师资力量得分为8分，设施得分为9分，"
            r"课程内容的得分为8分，学生满意度的得分为7分。\\n*"
            r" 学校C的师资力量得分为7分，设施得分为7分，课程内容的得分为9分，"
            r"学生满意度的得分为8分。"
            r'\",\"chartType\":\"radar\",\"title\":\"学校教育质量\",\"last_bot_message\":\"\"}","plugin_resp":"{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"数据分析\",\"actionContent\":\"数据分析中\"}\n{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"数据分析\",\"actionContent\":\"数据分析成功\"}\n{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"图表绘制\",\"actionContent\":\"图表绘制中\"}\n{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"图表绘制\",\"actionContent\":\"图表绘制成功\"}","status":"1","api_id":"eChart.plot"}]}'
        ),
        r"event: chat",
        (
            r"data:"
            r' {"id":"as-hdpadsaghd","object":"chat.completion","created":1705585108,"sentence_id":0,"is_end":false,"is_truncated":false,"result":"\n\n```echarts-option\n[{\"radar\":{\"indicator\":[{\"name\":\"师资力量（分）\",\"max\":10},{\"name\":\"设施（分）\",\"max\":10},{\"name\":\"课程内容（分）\",\"max\":10},{\"name\":\"学生满意度（分）\",\"max\":10}]},\"series\":[{\"type\":\"radar\",\"data\":[{\"name\":\"学校A\",\"value\":[10,8,7,9]},{\"name\":\"学校B\",\"value\":[8,9,8,7]},{\"name\":\"学校C\",\"value\":[7,7,9,8]}]}],\"title\":{\"text\":\"学校教育质量\"},\"tooltip\":{\"show\":true},\"legend\":{\"show\":true,\"bottom\":15}}]\n```\n\n","need_clear_history":false,"finish_reason":"normal","usage":{"prompt_tokens":135,"completion_tokens":0,"total_tokens":135}}'
        ),
        r"event: plugin",
        (
            r"data:"
            r' {"id":"as-hdpadsaghd","object":"chat.completion","created":1705585108,"sentence_id":7,"plugin_info":[{"plugin_id":"1066:1.0.1","plugin_name":"","plugin_req":"{\"data\":\"学校A的师资力量得分为10分，'
            r"设施得分为8分，课程内容的得分为7分，学生满意度的得分为9分。\\n*"
            r" 学校B的师资力量得分为8分，设施得分为9分，课程内容的得分为8分，"
            r"学生满意度的得分为7分。\\n* 学校C的师资力量得分为7分，设施得分为7分，"
            r"课程内容的得分为9分，学生满意度的得分为8分。"
            r"\",\"query\":\"请按照下面要求给我生成雷达图：学校教育质量:"
            r" 维度：师资力量、设施、课程内容、学生满意度。对象：A,B,C三所学校。"
            r"学校A的师资力量得分为10分，设施得分为8分，课程内容的得分为7分，"
            r"学生满意度的得分为9分。\\n* 学校B的师资力量得分为8分，设施得分为9分，"
            r"课程内容的得分为8分，学生满意度的得分为7分。\\n*"
            r" 学校C的师资力量得分为7分，设施得分为7分，课程内容的得分为9分，"
            r"学生满意度的得分为8分。"
            r'\",\"chartType\":\"radar\",\"title\":\"学校教育质量\",\"last_bot_message\":\"\"}","plugin_resp":"{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"数据分析\",\"actionContent\":\"数据分析中\"}\n{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"数据分析\",\"actionContent\":\"数据分析成功\"}\n{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"图表绘制\",\"actionContent\":\"图表绘制中\"}\n{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"图表绘制\",\"actionContent\":\"图表绘制成功\"}\n{\"errCode\":0,\"option\":\"REMOVED\",\"usage\":null}\n{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"图表解释\",\"actionContent\":\"图表解释成功\"}","status":"1","api_id":"eChart.plot"}]}'
        ),
        r"event: chat",
        (
            r"data:"
            r' {"id":"as-hdpadsaghd","object":"chat.completion","created":1705585108,"sentence_id":1,"is_end":false,"is_truncated":false,"result":"\n\n**图表数据:**\n\n|'
            r" 维度 | 学校A | 学校B | 学校C |\n| :--: |  :--: | :--: | :--: | |\n|"
            r" 师资力量 | 10 | 8 | 7 |\n| 设施 | 8 | 9 | 7 |\n| 课程内容 | 7 | 8 | 9"
            r" |\n| 学生满意度 | 9 | 7 | 8"
            r" |\n\n我（文心一言）是百度开发的人工智能模型，"
            r"通过分析大量公开文本信息进行学习。然而，我所提供的信息可能存在误差。"
            r"因此上文内容仅供参考，并不应被视为专业建议。"
            r'","need_clear_history":false,"finish_reason":"normal","usage":{"prompt_tokens":135,"completion_tokens":0,"total_tokens":135}}'
        ),
        r"event: plugin",
        (
            r"data:"
            r' {"id":"as-hdpadsaghd","object":"chat.completion","created":1705585109,"sentence_id":8,"plugin_info":[{"plugin_id":"1066:1.0.1","plugin_name":"","plugin_req":"{\"data\":\"学校A的师资力量得分为10分，'
            r"设施得分为8分，课程内容的得分为7分，学生满意度的得分为9分。\\n*"
            r" 学校B的师资力量得分为8分，设施得分为9分，课程内容的得分为8分，"
            r"学生满意度的得分为7分。\\n* 学校C的师资力量得分为7分，设施得分为7分，"
            r"课程内容的得分为9分，学生满意度的得分为8分。"
            r"\",\"query\":\"请按照下面要求给我生成雷达图：学校教育质量:"
            r" 维度：师资力量、设施、课程内容、学生满意度。对象：A,B,C三所学校。"
            r"学校A的师资力量得分为10分，设施得分为8分，课程内容的得分为7分，"
            r"学生满意度的得分为9分。\\n* 学校B的师资力量得分为8分，设施得分为9分，"
            r"课程内容的得分为8分，学生满意度的得分为7分。\\n*"
            r" 学校C的师资力量得分为7分，设施得分为7分，课程内容的得分为9分，"
            r"学生满意度的得分为8分。"
            r'\",\"chartType\":\"radar\",\"title\":\"学校教育质量\",\"last_bot_message\":\"\"}","plugin_resp":"{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"数据分析\",\"actionContent\":\"数据分析中\"}\n{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"数据分析\",\"actionContent\":\"数据分析成功\"}\n{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"图表绘制\",\"actionContent\":\"图表绘制中\"}\n{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"图表绘制\",\"actionContent\":\"图表绘制成功\"}\n{\"errCode\":0,\"option\":\"REMOVED\",\"usage\":null}\n{\"errCode\":0,\"errMsg\":\"success\",\"status\":\"\",\"actionName\":\"图表解释\",\"actionContent\":\"图表解释成功\"}\n{\"errCode\":0,\"option\":\"REMOVED\",\"usage\":{\"len_answer\":0,\"len_chart_interpret\":230,\"len_echarts_dict_str\":308,\"total_tokens\":591}}","status":"2","api_id":"eChart.plot"}]}'
        ),
        r"event: chat",
        (
            r"data:"
            r' {"id":"as-hdpadsaghd","object":"chat.completion","created":1705585109,"sentence_id":2,"is_end":true,"is_truncated":false,"result":"","need_clear_history":false,"finish_reason":"normal","usage":{"prompt_tokens":135,"completion_tokens":308,"total_tokens":443,"plugins":[{"name":"eChart","parse_tokens":0,"abstract_tokens":0,"search_tokens":0,"total_tokens":591}]}}'
        ),
    ]

    for i, d in enumerate(mock_plugin_stream_result):
        if i % 2 == 0:
            yield d + "\n"
        else:
            yield d + "\n\n"


@app.route(Consts.ModelAPIPrefix + "/plugin/<endpoint>/", methods=["POST"])
def plugin(endpoint):
    return json_response(
        {
            "id": "as-xx111",
            "object": "chat.completion",
            "created": 1703153237,
            "result": (
                "使用知识库查询数据集创建案例，您可以参考以下步骤进行操作：\n\n1."
                " 确定数据集类型和目标：首先，您需要确定您要创建的数据集类型，"
                "例如文本、图像、音频等。同时，您需要明确数据集的目标，"
                "例如用于训练机器学习模型、进行数据挖掘等。\n2."
                " 收集数据：根据您的数据集类型和目标，收集相关的数据。"
                "您可以通过网络爬虫、公开数据集、合作伙伴等方式获取数据。\n3."
                " 数据清洗和预处理：在收集到数据后，您需要对数据进行清洗和预处理，"
                "以去除无效、重复或错误的数据，并对数据进行标准化、归一化等处理，"
                "以便于后续的分析和建模。\n4. 构建知识库：根据您的数据和目标，"
                "构建一个适当的知识库。知识库可以包括事实、规则、概念等，"
                "用于指导后续的数据集创建过程。\n5. 创建数据集：使用知识库中的信息，"
                "对原始数据进行分类、聚类、标签化等处理，"
                "从而生成一个具有结构化标签或有序关系的新数据集。\n6."
                " 评估和优化：在创建数据集后，您需要对数据集的质量和有效性进行评估。"
                "根据评估结果，您可以对知识库或数据预处理步骤进行调整和优化，"
                "以提高数据集的质量和准确性。\n\n请注意，"
                "以上步骤可能因具体的数据集类型和目标而有所不同。在实际操作中，"
                "您可能需要根据具体情况进行调整和优化。"
            ),
            "is_truncated": False,
            "need_clear_history": False,
            "finish_reason": "normal",
            "usage": {
                "prompt_tokens": 1342,
                "completion_tokens": 310,
                "total_tokens": 1652,
            },
            "meta_info": {
                "plugin_id": "uuid-zhishiku",
                "request": {
                    "query": "使用知识库查询数据集创建案例",
                    "kbIds": ["65362edb8dcc93865e371221"],
                    "score": 0,
                    "topN": 5,
                },
                "response": {
                    "retCode": 1,
                    "message": "",
                    "result": {
                        "besQueryCostMilsec3": 296,
                        "dbQueryCostMilsec1": 0,
                        "embeddedCostMilsec2": 288,
                        "responses": [
                            {
                                "charsNum": 425,
                                "contentKey": "",
                                "docId": "1939336a-fd2b-4798-8cec-ed2752682e2d",
                                "docName": "互联网信息服务深度合成管理规定.txt",
                                "docType": 0,
                                "enableStatus": 1,
                                "hitNum": 4,
                                "isShardDeleted": False,
                                "kbId": "65362edb8dcc93865e371221",
                                "kbName": "test_hj_kndb",
                                "next": {
                                    "charsNum": 102,
                                    "contentKey": "",
                                    "contentKeyUrl": "http://easydata.bj.bcebos.com/_system_/knowledge/kb-rtan0widq1m7292e/doc/1939336a-fd2b-4798-8cec-ed2752682e2d/shard/5a4214eb-5802-4f8c-8071-67a346dfdf1a?authorization=bce-auth-v1%2F50c8bb753dcb4e1d8646bb1ffefd3503%2F2023-12-21T10%3A07%3A05Z%2F3600%2Fhost%2Fe318d41e6e787d6597fee6ec337c5126090c7f67eb753009222a677f9dfe137a",
                                    "contentUrl": "http://easydata.bj.bcebos.com/_system_/knowledge/kb-rtan0widq1m7292e/doc/1939336a-fd2b-4798-8cec-ed2752682e2d/shard/5a4214eb-5802-4f8c-8071-67a346dfdf1a?authorization=bce-auth-v1%2F50c8bb753dcb4e1d8646bb1ffefd3503%2F2023-12-21T10%3A07%3A05Z%2F3600%2Fhost%2Fe318d41e6e787d6597fee6ec337c5126090c7f67eb753009222a677f9dfe137a",
                                    "docId": "1939336a-fd2b-4798-8cec-ed2752682e2d",
                                    "docName": "",
                                    "docType": 0,
                                    "enableStatus": 1,
                                    "hitNum": 10,
                                    "isShardDeleted": False,
                                    "kbId": "65362edb8dcc93865e371221",
                                    "kbName": "test_hj_kndb",
                                    "score": 0,
                                    "shardId": "5a4214eb-5802-4f8c-8071-67a346dfdf1a",
                                    "shardIndex": 10,
                                },
                                "previous": {
                                    "charsNum": 402,
                                    "contentKey": "",
                                    "contentKeyUrl": "http://easydata.bj.bcebos.com/_system_/knowledge/kb-rtan0widq1m7292e/doc/1939336a-fd2b-4798-8cec-ed2752682e2d/shard/0e07162c-c3bc-494d-8c99-227182b38a4b?authorization=bce-auth-v1%2F50c8bb753dcb4e1d8646bb1ffefd3503%2F2023-12-21T10%3A07%3A05Z%2F3600%2Fhost%2Ff3dc2911bf36c241a2d4edeb3d788403f93c6978bb1df29b860b84ee29447cb8",
                                    "contentUrl": "http://easydata.bj.bcebos.com/_system_/knowledge/kb-rtan0widq1m7292e/doc/1939336a-fd2b-4798-8cec-ed2752682e2d/shard/0e07162c-c3bc-494d-8c99-227182b38a4b?authorization=bce-auth-v1%2F50c8bb753dcb4e1d8646bb1ffefd3503%2F2023-12-21T10%3A07%3A05Z%2F3600%2Fhost%2Ff3dc2911bf36c241a2d4edeb3d788403f93c6978bb1df29b860b84ee29447cb8",
                                    "docId": "1939336a-fd2b-4798-8cec-ed2752682e2d",
                                    "docName": "",
                                    "docType": 0,
                                    "enableStatus": 1,
                                    "hitNum": 18,
                                    "isShardDeleted": False,
                                    "kbId": "65362edb8dcc93865e371221",
                                    "kbName": "test_hj_kndb",
                                    "score": 0,
                                    "shardId": "0e07162c-c3bc-494d-8c99-227182b38a4b",
                                    "shardIndex": 8,
                                },
                                "score": 0.47072577,
                                "shardId": "78106dc5-8474-4d28-b064-4eef34b51620",
                                "shardIndex": 9,
                                "content": (
                                    "（一）篇章生成、文本风格转换、"
                                    "问答对话等生成或者编辑文本内容的技术；\n\n（二）文本转语音、"
                                    "语音转换、"
                                    "语音属性编辑等生成或者编辑语音内容的技术；\n\n（三）音乐生成、"
                                    "场景声编辑等生成或者编辑非语音内容的技术；\n\n（四）人脸生成、"
                                    "人脸替换、人物属性编辑、人脸操控、"
                                    "姿态操控等生成或者编辑图像、"
                                    "视频内容中生物特征的技术；\n\n（五）图像生成、"
                                    "图像增强、图像修复等生成或者编辑图像、"
                                    "视频内容中非生物特征的技术；\n\n（六）三维重建、"
                                    "数字仿真等生成或者编辑数字人物、虚拟场景的技术。"
                                    "\n\n深度合成服务提供者，"
                                    "是指提供深度合成服务的组织、个人。"
                                    "\n\n深度合成服务技术支持者，"
                                    "是指为深度合成服务提供技术支持的组织、个人。"
                                    "\n\n深度合成服务使用者，是指使用深度合成服务制作、"
                                    "复制、发布、传播信息的组织、个人。\n\n训练数据，"
                                    "是指被用于训练机器学习模型的标注或者基准数据集。"
                                    "\n\n沉浸式拟真场景，"
                                    "是指应用深度合成技术生成或者编辑的、"
                                    "可供参与者体验或者互动的、"
                                    "具有高度真实感的虚拟场景。"
                                ),
                                "is_truncated": False,
                            }
                        ],
                        "urlSignedCostMilsec4": 301,
                    },
                    "doc_nums": 5,
                },
                "action": "llm",
                "action_input": [
                    "现在你的任务是根据给定的材料回答用户的问题，"
                    "你会解答我关于problem的问题。你需要根据已提供的材料知识进行回答，"
                    "不能自己编撰。\n你的任务是做一名问答助手，"
                    "根据【检索结果】来回答最后的【问题】。在回答问题时，"
                    "你需要注意以下几点：\n1.【检索结果】有多条，"
                    "每条【检索结果】之间由-分隔。"
                    "\n2.如果某条【检索结果】与【问题】无关，"
                    "就不要参考这条【检索结果】。\n3.请直接回答问题，"
                    "不要强调客服的职责。此外，避免出现无关话术，"
                    '如"根据【检索结果】..."等。\n\n【检索结果】\n- （一）篇章生成、'
                    "文本风格转换、"
                    "问答对话等生成或者编辑文本内容的技术；\n\n（二）文本转语音、"
                    "语音转换、"
                    "语音属性编辑等生成或者编辑语音内容的技术；\n\n（三）音乐生成、"
                    "场景声编辑等生成或者编辑非语音内容的技术；\n\n（四）人脸生成、"
                    "人脸替换、人物属性编辑、人脸操控、姿态操控等生成或者编辑图像、"
                    "视频内容中生物特征的技术；\n\n（五）图像生成、图像增强、"
                    "图像修复等生成或者编辑图像、"
                    "视频内容中非生物特征的技术；\n\n（六）三维重建、"
                    "数字仿真等生成或者编辑数字人物、虚拟场景的技术。"
                    "\n\n深度合成服务提供者，是指提供深度合成服务的组织、个人。"
                    "\n\n深度合成服务技术支持者，是指为深度合成服务提供技术支持的组织、"
                    "个人。\n\n深度合成服务使用者，是指使用深度合成服务制作、复制、"
                    "发布、传播信息的组织、个人。\n\n训练数据，"
                    "是指被用于训练机器学习模型的标注或者基准数据集。"
                    "\n\n沉浸式拟真场景，是指应用深度合成技术生成或者编辑的、"
                    "可供参与者体验或者互动的、具有高度真实感的虚拟场景。\n- 第十条"
                    " 深度合成服务提供者应当加强深度合成内容管理，"
                    "采取技术或者人工方式对深度合成服务使用者的输入数据和合成结果进行审核。"
                    "\n\n深度合成服务提供者应当建立健全用于识别违法和不良信息的特征库，"
                    "完善入库标准、规则和程序，记录并留存相关网络日志。"
                    "\n\n深度合成服务提供者发现违法和不良信息的，应当依法采取处置措施，"
                    "保存有关记录，"
                    "及时向网信部门和有关主管部门报告；对相关深度合成服务使用者依法依约采取警示、"
                    "限制功能、暂停服务、关闭账号等处置措施。\n\n第十一条"
                    " 深度合成服务提供者应当建立健全辟谣机制，"
                    "发现利用深度合成服务制作、复制、发布、传播虚假信息的，"
                    "应当及时采取辟谣措施，保存有关记录，"
                    "并向网信部门和有关主管部门报告。\n\n第十二条"
                    " 深度合成服务提供者应当设置便捷的用户申诉和公众投诉、举报入口，"
                    "公布处理流程和反馈时限，及时受理、处理和反馈处理结果。\n-"
                    " （一）生成或者编辑人脸、"
                    "人声等生物识别信息的；\n\n（二）生成或者编辑可能涉及国家安全、"
                    "国家形象、国家利益和社会公共利益的特殊物体、"
                    "场景等非生物识别信息的。\n\n第十六条"
                    " 深度合成服务提供者对使用其服务生成或者编辑的信息内容，"
                    "应当采取技术措施添加不影响用户使用的标识，并依照法律、"
                    "行政法规和国家有关规定保存日志信息。\n\n第十七条"
                    " 深度合成服务提供者提供以下深度合成服务，"
                    "可能导致公众混淆或者误认的，"
                    "应当在生成或者编辑的信息内容的合理位置、区域进行显著标识，"
                    "向公众提示深度合成情况：\n\n（一）智能对话、"
                    "智能写作等模拟自然人进行文本的生成或者编辑服务；\n\n（二）合成人声、"
                    "仿声等语音生成或者显著改变个人身份特征的编辑服务；\n\n（三）人脸生成、"
                    "人脸替换、人脸操控、姿态操控等人物图像、"
                    "视频生成或者显著改变个人身份特征的编辑服务；\n\n（四）沉浸式拟真场景等生成或者编辑服务；\n\n（五）其他具有生成或者显著改变信息内容功能的服务。"
                    "\n- 第二十一条 网信部门和电信主管部门、"
                    "公安部门依据职责对深度合成服务开展监督检查。"
                    "深度合成服务提供者和技术支持者应当依法予以配合，并提供必要的技术、"
                    "数据等支持和协助。"
                    "\n\n网信部门和有关主管部门发现深度合成服务存在较大信息安全风险的，"
                    "可以按照职责依法要求深度合成服务提供者和技术支持者采取暂停信息更新、"
                    "用户账号注册或者其他相关服务等措施。"
                    "深度合成服务提供者和技术支持者应当按照要求采取措施，进行整改，"
                    "消除隐患。\n\n第二十二条"
                    " 深度合成服务提供者和技术支持者违反本规定的，依照有关法律、"
                    "行政法规的规定处罚；造成严重后果的，依法从重处罚。"
                    "\n\n构成违反治安管理行为的，"
                    "由公安机关依法给予治安管理处罚；构成犯罪的，依法追究刑事责任。"
                    "\n\n第五章 附则\n\n第二十三条"
                    " 本规定中下列用语的含义：\n\n深度合成技术，是指利用深度学习、"
                    "虚拟现实等生成合成类算法制作文本、图像、音频、视频、"
                    "虚拟场景等网络信息的技术，包括但不限于：。\n- 第十三条"
                    " 互联网应用商店等应用程序分发平台应当落实上架审核、日常管理、"
                    "应急处置等安全管理责任，核验深度合成类应用程序的安全评估、"
                    "备案等情况；对违反国家有关规定的，应当及时采取不予上架、警示、"
                    "暂停服务或者下架等处置措施。\n\n第三章"
                    " 数据和技术管理规范\n\n第十四条"
                    " 深度合成服务提供者和技术支持者应当加强训练数据管理，"
                    "采取必要措施保障训练数据安全；训练数据包含个人信息的，"
                    "应当遵守个人信息保护的有关规定。"
                    "\n\n深度合成服务提供者和技术支持者提供人脸、"
                    "人声等生物识别信息编辑功能的，"
                    "应当提示深度合成服务使用者依法告知被编辑的个人，并取得其单独同意。"
                    "\n\n第十五条 深度合成服务提供者和技术支持者应当加强技术管理，"
                    "定期审核、评估、验证生成合成类算法机制机理。"
                    "\n\n深度合成服务提供者和技术支持者提供具有以下功能的模型、"
                    "模板等工具的，"
                    "应当依法自行或者委托专业机构开展安全评估：\n\n（一）生成或者编辑人脸、"
                    "人声等生物识别信息的；。"
                    "\n\n\n【问题】\n使用知识库查询数据集创建案例\n\n【回答】\n"
                ],
                "action_output": "",
            },
            "log_id": 1107539952111324513,
        }
    )


prompt_opti_task_calltimes = {}


@app.route(Consts.PromptCreateOptimizeTaskAPI, methods=["POST"])
@iam_auth_checker
def create_prompt_optimize_task():
    """
    create prompt optimize task
    """
    task_id = generate_letter_num_random_id(16)
    prompt_opti_task_calltimes[task_id] = 0
    return json_response(
        {
            "log_id": "sfcie8dcxyat7mwy",
            "result": {"id": f"task-{task_id}"},
            "status": 200,
            "success": True,
        }
    )


@app.route(Consts.PromptGetOptimizeTaskInfoAPI, methods=["POST"])
@iam_auth_checker
def get_prompt_optimize_task():
    """
    get prompt optimize task info
    """
    r = request.json
    task_id = r["id"]
    status = 2
    if task_id in prompt_opti_task_calltimes:
        prompt_opti_task_calltimes[task_id] += 1
        if prompt_opti_task_calltimes[task_id] < 3:
            status = 1
    return json_response(
        {
            "log_id": "0qqb0s65kh5d2g9s",
            "result": {
                "id": "task-96f3mfrnj5e8qgv3",
                "content": "原始prompt",
                "optimizeContent": "optimized prompt",
                "qingfanResult": "",
                "operations": [
                    {"opType": 1, "payload": 1},
                    {"opType": 2, "payload": 1},
                    {"opType": 3, "payload": 1},
                    {"opType": 4, "payload": 0},
                ],
                "processStatus": status,
                "appId": 1483416585,
                "serviceName": "ERNIE-Bot-turbo",
                "projectId": "",
                "creator": "easydata_user",
                "inference": "",
                "createTime": "2023-12-29 17:40:33",
                "modifyTime": "2023-12-29 17:40:48",
            },
            "status": 200,
            "success": True,
        }
    )


@app.route(Consts.PromptEvaluationAPI, methods=["POST"])
@iam_auth_checker
def prompt_evaluate_score():
    """
    Evaluate prompt with score
    """
    r = request.json
    data = r["data"]
    return json_response(
        {
            "log_id": "9ih8evsperpdvkxk",
            "result": {
                "logID": 2,
                "scores": [
                    [random.random() for _ in range(len(data[0]["response_list"]))]
                    for _ in range(len(data))
                ],
                "errorCode": 0,
                "errorMsg": "",
            },
            "status": 200,
            "success": True,
        }
    )


@app.route(Consts.PromptEvaluationSummaryAPI, methods=["POST"])
@iam_auth_checker
def prompt_evaluate_summary():
    """
    Evaluate prompt with summary
    """
    r = request.json
    data = r["data"]
    return json_response(
        {
            "log_id": "9ih8evsperpdvkxk",
            "result": {
                "responses": [
                    {
                        "response": f"response_{i}",
                        "id": "",
                        "errorCode": 0,
                        "errorMsg": "",
                    }
                    for i in range(len(data))
                ]
            },
            "status": 200,
            "success": True,
        }
    )


@app.route(Consts.TpmCreditAPI, methods=["POST"])
@iam_auth_checker
def rpm_related_api():
    """
    process all query of rpm related
    """

    action = request.args["Action"]
    if action == "PurchaseTPMResource":
        return json_response(
            {
                "requestId": "1bef3f87-c5b2-4419-936b-50f9884f10d4",
                "result": {"instanceId": "44961088f5xxxxx79f5daf"},
            }
        )

    if action == "DescribeTPMResource":
        return json_response(
            {
                "requestId": "1bef3f87-c5b2-4419-936b-50f9884f10d4",
                "result": {
                    "instances": [
                        {
                            "instanceId": "a0085162fxxxx0ad19e58e",
                            "paymentTiming": "Postpaid",
                            "rpm": 33,
                            "tpm": 10000,
                            "status": "Running",
                            "startTime": "2024-02-26T10:00:00Z",
                            "expiredTime": "-",
                        }
                    ]
                },
            }
        )

    if action == "ReleaseTPMResource":
        return json_response(
            {"requestId": "1bef3f87-c5b2-4419-936b-50f9884f10d4", "result": True}
        )


@app.route(Consts.ModelAPIPrefix + "/reranker/<model_name>", methods=["POST"])
def reranker(model_name):
    if model_name == "":
        return json_response(
            {
                "error_code": 3,
                "error_msg": "unsupported method",
            }
        )
    req = request.json
    documents = req["documents"]
    res = [
        {"document": d, "relevance_score": 0.85, "index": i}
        for i, d in enumerate(documents)
    ]
    if req.get("top_n"):
        res = res[: req["top_n"]]
    return json_response(
        {
            "id": "as-nc3zn3k8gn",
            "object": "reranker_list",
            "created": 1714094015,
            "results": res,
            "usage": {"prompt_tokens": 22, "total_tokens": 22},
        }
    )


def _start_mock_server():
    """
    run mock server
    """
    try:
        requests.get("http://127.0.0.1:8866")
    except Exception:
        # mock server is not running, start it
        app.run(host="0.0.0.0", port=8866, debug=True, use_reloader=False)


def start_mock_server():
    """
    run mock server in background thread
    """
    t = threading.Thread(target=_start_mock_server)
    t.daemon = True
    t.start()


if __name__ == "__main__":
    _start_mock_server()
