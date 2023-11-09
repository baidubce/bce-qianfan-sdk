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

# disable line too long lint error in this file
# ruff: noqa: E501

import json
import random
import threading
from functools import wraps

import flask
import requests
from flask import Flask, request

from qianfan.consts import APIErrorCode, Consts

app = Flask(__name__)

STREAM_COUNT = 3


def merge_messages(messages):
    """
    merge mulitple input messages
    """
    return "|".join([m["content"] for m in messages])


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


def json_response(data):
    """
    wrapper of the response
    """
    return flask.Response(
        json.dumps({**data, "_request": request.json, "_params": request.args}),
        mimetype="application/json",
    )


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


def check_messages(messages):
    """
    check whether the received messages are valid
    """
    if len(messages) % 2 != 1:
        return {
            "error_code": APIErrorCode.InvalidParam,
            "error_msg": "messages length must be odd",
        }
    for i, m in enumerate(messages):
        if (i % 2 == 0 and m["role"] != "user") or (
            i % 2 == 1 and m["role"] != "assistant"
        ):
            return {
                "error_code": APIErrorCode.InvalidParam,
                "error_msg": f"invalid role in message {i}",
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


@app.route(Consts.ModelAPIPrefix + "/chat/<model_name>", methods=["POST"])
@access_token_checker
def chat(model_name):
    """
    mock /chat/<model_name> chat completion api
    """
    r = request.json
    # check messages
    check_result = check_messages(r["messages"])
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


@app.route(Consts.ModelAPIPrefix + "/completions/<model_name>", methods=["POST"])
@access_token_checker
def completions(model_name):
    """
    mock /completions/<model_name> completion api
    """
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
    mock /text2image/<model_name> chat completion api
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
                    "b64_image": "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",
                    "index": 1,
                }
            ],
            "usage": {"prompt_tokens": 8, "total_tokens": 8},
        }
    )


@app.route(Consts.PromptRenderAPI, methods=["GET"])
@access_token_checker
def prompt():
    """
    mock prompt render api
    """
    return json_response(
        {
            "log_id": "e9d3f283-1091-405b-568e-862e824e679e",
            "result": {
                "templateId": 632,
                "templateName": "原创改写",
                "templateContent": "用{number}种不同的方式改写以下段落，以避免重复，同时保持其含义：{text}。",
                "content": (
                    "用2种不同的方式改写以下段落，以避免重复，"
                    "同时保持其含义：千帆大模型平台是面向企业开发者的一站式大模型开发及服务运行平台。"
                ),
                "templateVariables": "number,text",
            },
            "status": 200,
            "success": True,
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
            "amount": 97575 + len(prompt),  # magic number for eb tokenizer api
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
                "name": r["name"],
                "description": "" if "description" not in r else r["description"],
                "createTime": "2023-09-07 11:11:11",
            },
        }
    )


@app.route(Consts.FineTuneCreateJobAPI, methods=["POST"])
@iam_auth_checker
def create_finetune_job():
    """
    mock create finetune job api
    """
    return json_response({"log_id": 123, "result": {"id": random.randint(0, 100000)}})


@app.route(Consts.FineTuneGetJobAPI, methods=["POST"])
@iam_auth_checker
def get_finetune_job():
    """
    mock get finetune job api
    """
    return json_response(
        {
            "log_id": 123,
            "result": {
                "id": 1,
                "taskId": 1,
                "taskName": "test",
                "version": 1,
                "trainType": "ernieBotLite-v200",
                "trainMode": "SFT",
                "peftType": "ALL",
                "trainStatus": "FINISH",
                "startTime": "2023-05-05 00:00:00",
                "finishtime": "2023-05-05 01:00:00",
                "runTime": 3600,
                "trainTime": 1800,
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
                "modelId": 7,
                "modelName": "ERNIE-Bot",
                "modelVersionId": 39,
                "version": "ERNIE-Bot",
                "description": "百度⾃⾏研发的⼤语⾔模型，覆盖海量中⽂数据，具有更强的对话问答、内容创作⽣成等能⼒。",
                "sourceType": "PlatformPreset",
                "sourceExtra": {},
                "framework": "paddle",
                "algorithm": "Ernie_Bot_105B",
                "modelNet": "paddlepaddle-ERNIE_EB-ERNIEBOT_105B-2.4.0-V1.25.3",
                "state": "Ready",
                "ioMode": "chat",
                "ioLength": "",
                "copyright": "",
                "property": {},
                "createTime": "2023-05-31T21:49:00+08:00",
                "modifyTime": "2023-08-29T19:28:15+08:00",
                "deployResource": ["Private"],
                "supportOptions": ["Deploy"],
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
                            "temperature": {
                                "name": "temperature",
                                "type": "number",
                                "format": "float",
                                "description": (
                                    "较高的数值会使输出更加随机，"
                                    "而较低的数值会使其更加集中和确定。 默认0.95，范围"
                                    " (0, 1.0]，不能为0 建议该参数和top_p只设置1个"
                                ),
                            },
                            "top_p": {
                                "name": "top_p",
                                "type": "number",
                                "format": "float",
                                "description": (
                                    "影响输出文本的多样性，取值越大，"
                                    "生成文本的多样性越强。 默认0.8，取值范围 [0, 1.0]"
                                    " 建议该参数和temperature只设置1个"
                                ),
                            },
                            "penalty_score": {
                                "name": "penalty_score",
                                "type": "number",
                                "format": "float",
                                "description": (
                                    "通过对已生成的token增加惩罚，减少重复生成的现象。"
                                    "值越大表示惩罚越大。 默认1.0，取值范围：[1.0, 2.0]"
                                ),
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
                                    "回包类型，“chat.completion”：多轮对话返回"
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
                                "name": "is_end",
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
                                    "次字段会告知第几轮对话有敏感信息，如果是当前问题，"
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
                                        "description": "问题tokens数",
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
                "modelId": 7,
                "modelName": "ERNIE-Bot",
                "source": "PlatformPreset",
                "modelType": 0,
                "createUserId": -1,
                "createUser": "",
                "createTime": "2023-05-31T21:48:59+08:00",
                "modifyTime": "2023-07-20T15:08:40+08:00",
                "description": "百度⾃⾏研发的⼤语⾔模型，覆盖海量中⽂数据，具有更强的对话问答、内容创作⽣成等能⼒。",
                "modelVersionList": [
                    {
                        "modelId": 7,
                        "modelName": "ERNIE-Bot",
                        "modelVersionId": 39,
                        "version": "ERNIE-Bot",
                        "description": "百度⾃⾏研发的⼤语⾔模型，覆盖海量中⽂数据，具有更强的对话问答、内容创作⽣成等能⼒。",
                        "sourceType": "PlatformPreset",
                        "sourceExtra": {},
                        "framework": "paddle",
                        "algorithm": "Ernie_Bot_105B",
                        "modelNet": "paddlepaddle-ERNIE_EB-ERNIEBOT_105B-2.4.0-V1.25.3",
                        "state": "Ready",
                        "ioMode": "chat",
                        "ioLength": "",
                        "copyright": "",
                        "property": {},
                        "createTime": "2023-05-31T21:49:00+08:00",
                        "modifyTime": "2023-08-29T19:28:15+08:00",
                        "deployResource": ["Private"],
                        "supportOptions": ["Deploy"],
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
        {"log_id": 1212121, "result": {"modelId": 1, "versionId": 2, "version": "1"}}
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
                "serviceStatus": 1,
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


@app.route(Consts.DatasetCreateAPI, methods=["POST"])
@iam_auth_checker
def create_dataset():
    args = request.json
    return json_response(
        {
            "log_id": "log_id",
            "status": 200,
            "success": True,
            "result": {
                "groupId": 12,
                "id": 42,
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
                    "storageId": args.get("storageId", ""),
                    "storagePath": (
                        "/easydata/_system_/dataset/ds-z07hkq2kyvsmrmdw/texts"
                    ),
                    "storageName": args.get("storageId"),
                    "rawStoragePath": args.get("rawStoragePath", ""),
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
    return json_response(
        {
            "log_id": "log_id",
            "result": {
                "groupId": 14510,
                "name": "ChineseMedicalDialogueData中文医疗问答数据集",
                "dataType": 4,
                "versionInfo": {
                    "groupId": 14510,
                    "datasetId": args["datasetId"],
                    "importRecordCount": 1,
                    "exportRecordCount": 0,
                    "bmlDatasetId": "ds-7pkzh1exthpuy10n",
                    "userId": 0,
                    "versionId": 1,
                    "displayName": "",
                    "importStatus": 2,
                    "importProgress": 100,
                    "exportStatus": -1,
                    "exportProgress": 0,
                    "dataType": 4,
                    "projectType": 20,
                    "templateType": 2000,
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
                    "description": (
                        "中文医疗对话数据集由792099个问答对组成，包括男科、内科、妇产科、肿瘤科、儿科和外科"
                    ),
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
    )


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
                for idx in args["datasetIds"].split(",")
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
                    "downloadUrl": "url",
                    "startTime": "2023-11-07 10:04:44",
                    "finishTime": "2023-11-07 10:04:53",
                }
            ],
            "status": 200,
            "success": True,
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
