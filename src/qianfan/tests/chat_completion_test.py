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
    Unit test for ChatCompletion
"""

import os

import pytest

import qianfan
import qianfan.tests.utils
from qianfan.tests.utils import EnvHelper, fake_access_token

QIANFAN_SUPPORT_CHAT_MODEL = {
    "ERNIE-Bot",
    "ERNIE-Bot-turbo",
    "BLOOMZ-7B",
    "Qianfan-BLOOMZ-7B-compressed",
    "Llama-2-7b-chat",
    "Llama-2-13b-chat",
    "Llama-2-70b-chat",
    "Qianfan-Chinese-Llama-2-7B",
    "ChatGLM2-6B-32K",
    "AquilaChat-7B",
}

TEST_ENDPOINTS = ["endpoint_1bhmit", "endpoint_iasnigo"]

TEST_MESSAGE = [
    {"role": "user", "content": "请问你是谁？"},
    {
        "role": "assistant",
        "content": (
            "我是百度公司开发的人工智能语言模型，我的中文名是文心一言，"
            "英文名是ERNIE-Bot，"
            "可以协助您完成范围广泛的任务并提供有关各种主题的信息，比如回答问题，"
            "提供定义和解释及建议。"
            "如果您有任何问题，请随时向我提问。"
        ),
    },
    {"role": "user", "content": "我在深圳，周末可以去哪里玩？"},
]

TEST_MULTITURN_MESSAGES = [
    "你好，请问你是谁？",
    "我在深圳，周末可以去哪里玩?",
    "你觉得世界之窗值得一玩吗？",
    "这个周末的天气怎么样？",
]


def test_generate():
    """
    Test basic generate
    """
    qfg = qianfan.ChatCompletion()
    for model in QIANFAN_SUPPORT_CHAT_MODEL:
        resp = qfg.do(
            model=model,
            messages=TEST_MESSAGE,
        )
        assert resp is not None
        assert resp["code"] == 200
        assert "id" in resp["body"]
        assert resp["object"] == "chat.completion"
        ut_res = resp["body"]["_for_ut"]
        assert "/chat/" + ut_res["model"] == qfg._supported_models()[model].endpoint
        assert ut_res["type"] == "chat"
        assert ut_res["stream"] is False
        assert ut_res["turn"] is None
        request = resp["_request"]
        assert request["messages"] == TEST_MESSAGE


def test_generate_with_endpoint():
    """
    Test basic generate
    """
    qfg = qianfan.ChatCompletion()
    for endpoint in TEST_ENDPOINTS:
        resp = qfg.do(
            endpoint=endpoint,
            messages=TEST_MESSAGE,
        )
        assert resp is not None
        assert resp["code"] == 200
        assert "id" in resp["body"]
        assert resp["object"] == "chat.completion"
        ut_res = resp["body"]["_for_ut"]
        assert ut_res["model"] == endpoint
        assert ut_res["type"] == "chat"
        assert ut_res["stream"] is False
        assert ut_res["turn"] is None


def test_custom_args():
    """
    Test pass custom args to api
    """
    qfg = qianfan.ChatCompletion()
    resp = qfg.do(messages=TEST_MESSAGE, top_p=0.9, temperature=0.5)
    request = resp["_request"]
    assert request["top_p"] == 0.9
    assert request["temperature"] == 0.5
    assert request["messages"] == TEST_MESSAGE


def test_generate_stream():
    """
    Test stream generate
    """
    sqfg = qianfan.ChatCompletion()
    for model in QIANFAN_SUPPORT_CHAT_MODEL:
        resp = sqfg.do(
            model=model,
            messages=TEST_MESSAGE,
            stream=True,
        )
        assert resp is not None
        turn = 0
        for result in resp:
            assert result is not None
            assert "sentence_id" in result["body"]
            assert result["object"] == "chat.completion"
            ut_res = result["body"]["_for_ut"]
            assert (
                "/chat/" + ut_res["model"] == sqfg._supported_models()[model].endpoint
            )
            assert ut_res["type"] == "chat"
            assert ut_res["stream"] is True
            assert ut_res["turn"] == turn
            turn += 1


def test_generate_multiturn_stream():
    """
    Test multiturn stream generate
    """
    sqfg = qianfan.ChatCompletion()
    MAX_TURNS = 2
    for model in QIANFAN_SUPPORT_CHAT_MODEL:
        messages = [
            {
                "role": "user",
                "content": TEST_MULTITURN_MESSAGES[0],
            }
        ]
        for turn in range(0, MAX_TURNS):
            resp = sqfg.do(
                model=model,
                messages=messages,
                stream=True,
            )
            assert resp is not None
            next_msg = ""
            for result in resp:
                assert result is not None
                assert "sentence_id" in result.body
                assert result["object"] == "chat.completion"
                next_msg += result["result"]
                ut_res = result["body"]["_for_ut"]
                assert (
                    "/chat/" + ut_res["model"]
                    == sqfg._supported_models()[model].endpoint
                )
                assert ut_res["type"] == "chat"
                assert ut_res["stream"] is True
            turn += 1
            messages.append({"role": "assistant", "content": next_msg})
            messages.append(
                {"role": "user", "content": TEST_MULTITURN_MESSAGES[turn + 1]}
            )


@pytest.mark.asyncio
async def test_generate_async():
    """
    Test async generate
    """
    qfg = qianfan.ChatCompletion()
    for model in QIANFAN_SUPPORT_CHAT_MODEL:
        resp = await qfg.ado(
            model=model,
            messages=TEST_MESSAGE,
        )
        assert resp is not None
        assert resp["code"] == 200
        assert "id" in resp.body
        assert resp["object"] == "chat.completion"
        ut_res = resp["body"]["_for_ut"]
        assert "/chat/" + ut_res["model"] == qfg._supported_models()[model].endpoint
        assert ut_res["type"] == "chat"
        assert ut_res["stream"] is False


@pytest.mark.asyncio
async def test_generate_stream_async():
    """
    Test async stream generate
    """
    sqfg = qianfan.ChatCompletion()
    for model in QIANFAN_SUPPORT_CHAT_MODEL:
        resp = await sqfg.ado(
            model=model,
            messages=TEST_MESSAGE,
            stream=True,
        )
        assert resp is not None
        turn = 0
        async for result in resp:
            assert result is not None
            assert "sentence_id" in result["body"]
            assert result["object"] == "chat.completion"
            ut_res = result["body"]["_for_ut"]
            assert (
                "/chat/" + ut_res["model"] == sqfg._supported_models()[model].endpoint
            )
            assert ut_res["type"] == "chat"
            assert ut_res["stream"] is True
            assert ut_res["turn"] == turn
            turn += 1


@pytest.mark.asyncio
async def test_generate_multiturn_stream_async():
    """
    Test multiturn stream generate
    """
    sqfg = qianfan.ChatCompletion()
    MAX_TURNS = 2
    for model in QIANFAN_SUPPORT_CHAT_MODEL:
        messages = [
            {
                "role": "user",
                "content": TEST_MULTITURN_MESSAGES[0],
            }
        ]
        for turn in range(0, MAX_TURNS):
            resp = await sqfg.ado(
                model=model,
                messages=messages,
                stream=True,
            )
            assert resp is not None
            messages.append({"role": "assistant", "content": ""})
            async for result in resp:
                assert result is not None
                assert "sentence_id" in result["body"]
                assert result["object"] == "chat.completion"
                messages[-1]["content"] += result["result"]
                ut_res = result["body"]["_for_ut"]
                assert (
                    "/chat/" + ut_res["model"]
                    == sqfg._supported_models()[model].endpoint
                )
                assert ut_res["type"] == "chat"
                assert ut_res["stream"] is True
            messages.append(
                {"role": "user", "content": TEST_MULTITURN_MESSAGES[turn + 1]}
            )


def test_qfmessage():
    """
    Test QFMessage
    """
    messages = qianfan.Messages()
    chat = qianfan.ChatCompletion()
    for turn in range(0, 2):
        messages.append(TEST_MULTITURN_MESSAGES[turn])
        resp = chat.do(messages=messages)
        assert resp["_request"]["messages"][-1]["role"] == "user"
        assert (
            resp["_request"]["messages"][-1]["content"] == TEST_MULTITURN_MESSAGES[turn]
        )
        assert "id" in resp["body"]
        assert resp["object"] == "chat.completion"
        messages.append(resp)


@pytest.mark.asyncio
async def test_async_qfmessage():
    """
    Test QFMessage in async context
    """
    messages = qianfan.Messages()
    chat = qianfan.ChatCompletion()
    for turn in range(0, 2):
        messages.append(TEST_MULTITURN_MESSAGES[turn])
        resp = await chat.ado(messages=messages)
        assert resp["_request"]["messages"][-1]["role"] == "user"
        assert (
            resp["_request"]["messages"][-1]["content"] == TEST_MULTITURN_MESSAGES[turn]
        )
        assert "id" in resp["body"]
        assert resp["object"] == "chat.completion"
        messages.append(resp)


def test_chat_completion_auth():
    ak = os.environ["QIANFAN_AK"]
    sk = os.environ["QIANFAN_SK"]
    c = qianfan.ChatCompletion()
    assert c.access_token() == fake_access_token(ak, sk)
    resp = c.do(messages=TEST_MESSAGE[:1])
    assert "result" in resp.body
    resp = c.do(messages=TEST_MESSAGE[:1], endpoint="custom_endpoint")
    assert "result" in resp.body
    resp = c.do(messages=TEST_MESSAGE[:1], model="ERNIE-Bot")
    assert "result" in resp.body

    ak = "ak_from_global_368548"
    sk = "sk_from_global_368548"
    qianfan.AK(ak)
    qianfan.SK(sk)
    c = qianfan.ChatCompletion()
    assert c.access_token() == fake_access_token(ak, sk)
    resp = c.do(messages=TEST_MESSAGE[:1])
    assert "result" in resp.body
    resp = c.do(messages=TEST_MESSAGE[:1], endpoint="custom_endpoint")
    assert "result" in resp.body
    resp = c.do(messages=TEST_MESSAGE[:1], model="ERNIE-Bot")
    assert "result" in resp.body
    qianfan.AK(None)
    qianfan.SK(None)

    with EnvHelper(QIANFAN_AK=None, QIANFAN_SK=None):
        ak = "ak_from_args_547881"
        sk = "sk_from_args_547881"
        c = qianfan.ChatCompletion(ak=ak, sk=sk)
        assert c.access_token() == fake_access_token(ak, sk)
        resp = c.do(messages=TEST_MESSAGE[:1])
        assert "result" in resp.body
        resp = c.do(messages=TEST_MESSAGE[:1], endpoint="custom_endpoint")
        assert "result" in resp.body
        resp = c.do(messages=TEST_MESSAGE[:1], model="ERNIE-Bot")
        assert "result" in resp.body
