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
    Unit test for ChatCompletion V2
"""

import threading
import time

import pytest

import qianfan
import qianfan.tests.utils
from qianfan.consts import Consts
from qianfan.tests.utils import EnvHelper

TEST_BEARER_TOKEN = (
    "bce-v3/ALTAK-JZasis7GfnokSLLXykKHj/054c2e64c06db4d6019f0dbfc964e90aa3fc3ddd"
)
TEST_MODEL = "ernie-unit-test"

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
    qfg = qianfan.ChatCompletion(version="2")

    resp = qfg.do(
        model=TEST_MODEL,
        messages=TEST_MESSAGE,
    )
    assert resp is not None
    assert resp["code"] == 200
    assert "choices" in resp["body"]
    assert resp["object"] == "chat.completion"
    ut_res = resp["body"]["_for_ut"]
    assert ut_res["type"] == "chatv2"
    assert ut_res["stream"] is False
    assert ut_res["turn"] is None
    request = resp["_request"]
    assert request["messages"] == TEST_MESSAGE
    assert request["model"] == TEST_MODEL


def test_custom_args():
    """
    Test pass custom args to api
    """
    qfg = qianfan.ChatCompletion(version="2")
    resp = qfg.do(messages=TEST_MESSAGE, top_p=0.9, temperature=0.5)
    request = resp["_request"]
    assert request["top_p"] == 0.9
    assert request["temperature"] == 0.5
    assert request["messages"] == TEST_MESSAGE


def test_generate_stream():
    """
    Test stream generate
    """
    sqfg = qianfan.ChatCompletion(version=2)

    resp = sqfg.do(
        model=TEST_MODEL,
        messages=TEST_MESSAGE,
        stream=True,
    )
    assert resp is not None
    turn = 0
    for result in resp:
        assert result is not None
        assert "choices" in result["body"]
        assert result["object"] == "chat.completion"
        ut_res = result["body"]["_for_ut"]
        assert ut_res["type"] == "chatv2"
        assert ut_res["stream"] is True
        assert ut_res["turn"] == turn
        turn += 1


def test_generate_multiturn_stream():
    """
    Test multiturn stream generate
    """
    sqfg = qianfan.ChatCompletion(version=2)
    MAX_TURNS = 2

    messages = [
        {
            "role": "user",
            "content": TEST_MULTITURN_MESSAGES[0],
        }
    ]
    for turn in range(0, MAX_TURNS):
        resp = sqfg.do(
            model=TEST_MODEL,
            messages=messages,
            stream=True,
        )
        assert resp is not None
        next_msg = ""
        for result in resp:
            assert result is not None
            assert "choices" in result.body
            assert result["object"] == "chat.completion"
            next_msg += result["choices"][0]["delta"]["content"]
            ut_res = result["body"]["_for_ut"]
            assert ut_res["type"] == "chatv2"
            assert ut_res["stream"] is True
        turn += 1
        messages.append({"role": "assistant", "content": next_msg})
        messages.append({"role": "user", "content": TEST_MULTITURN_MESSAGES[turn + 1]})


def test_request_id():
    chat_comp = qianfan.ChatCompletion(version=2)
    resp = chat_comp.do(messages=TEST_MESSAGE, request_id="custom_req")
    assert resp.headers[Consts.XResponseID] == "custom_req"


@pytest.mark.asyncio
async def test_generate_async():
    """
    Test async generate
    """
    qfg = qianfan.ChatCompletion(version=2)

    resp = await qfg.ado(
        model=TEST_MODEL,
        messages=TEST_MESSAGE,
    )
    assert resp is not None
    assert resp["code"] == 200
    assert "id" in resp.body
    assert resp["object"] == "chat.completion"
    ut_res = resp["body"]["_for_ut"]
    assert ut_res["type"] == "chatv2"
    assert ut_res["stream"] is False


@pytest.mark.asyncio
async def test_generate_stream_async():
    """
    Test async stream generate
    """
    sqfg = qianfan.ChatCompletion(version=2)

    resp = await sqfg.ado(
        model=TEST_MODEL,
        messages=TEST_MESSAGE,
        stream=True,
    )
    assert resp is not None
    turn = 0
    async for result in resp:
        assert result is not None
        assert "choices" in result["body"]
        assert result["object"] == "chat.completion"
        ut_res = result["body"]["_for_ut"]
        assert ut_res["type"] == "chatv2"
        assert ut_res["stream"] is True
        assert ut_res["turn"] == turn
        turn += 1


@pytest.mark.asyncio
async def test_generate_multiturn_stream_async():
    """
    Test multiturn stream generate
    """
    sqfg = qianfan.ChatCompletion(version=2)
    MAX_TURNS = 2

    messages = [
        {
            "role": "user",
            "content": TEST_MULTITURN_MESSAGES[0],
        }
    ]
    for turn in range(0, MAX_TURNS):
        resp = await sqfg.ado(
            model=TEST_MODEL,
            messages=messages,
            stream=True,
        )
        assert resp is not None
        messages.append({"role": "assistant", "content": ""})
        async for result in resp:
            assert result is not None
            assert "choices" in result["body"]
            assert result["object"] == "chat.completion"
            messages[-1]["content"] += result["choices"][0]["delta"]["content"]
            ut_res = result["body"]["_for_ut"]
            assert ut_res["type"] == "chatv2"
            assert ut_res["stream"] is True
            assert ut_res["model"] == TEST_MODEL
        messages.append({"role": "user", "content": TEST_MULTITURN_MESSAGES[turn + 1]})


def test_qfmessage():
    """
    Test QFMessage
    """
    messages = qianfan.Messages()
    chat = qianfan.ChatCompletion(version=2)
    for turn in range(0, 2):
        messages.append(TEST_MULTITURN_MESSAGES[turn])
        resp = chat.do(messages=messages)
        assert resp["_request"]["messages"][-1]["role"] == "user"
        assert (
            resp["_request"]["messages"][-1]["content"] == TEST_MULTITURN_MESSAGES[turn]
        )
        assert "id" in resp["body"]
        assert resp["object"] == "chat.completion"
        messages.append(resp["choices"][0]["message"]["content"], role="assistant")


@pytest.mark.asyncio
async def test_async_qfmessage():
    """
    Test QFMessage in async context
    """
    messages = qianfan.Messages()
    chat = qianfan.ChatCompletion(version=2)
    for turn in range(0, 2):
        messages.append(TEST_MULTITURN_MESSAGES[turn])
        resp = await chat.ado(messages=messages)
        assert resp["_request"]["messages"][-1]["role"] == "user"
        assert (
            resp["_request"]["messages"][-1]["content"] == TEST_MULTITURN_MESSAGES[turn]
        )
        assert "id" in resp["body"]
        assert resp["object"] == "chat.completion"
        messages.append(resp["choices"][0]["message"]["content"], role="assistant")


def test_in_other_thread():
    t = threading.Thread(target=test_generate)
    t.start()
    t.join()


def test_auth_using_bearer_token():
    ak, sk, access_key, secret_key = (
        qianfan.get_config().AK,
        qianfan.get_config().SK,
        qianfan.get_config().ACCESS_KEY,
        qianfan.get_config().SECRET_KEY,
    )
    qianfan.get_config().AK = None
    qianfan.get_config().SK = None
    qianfan.get_config().ACCESS_KEY = None
    qianfan.get_config().SECRET_KEY = None
    qianfan.get_config().BEARER_TOKEN = TEST_BEARER_TOKEN
    resp = qianfan.ChatCompletion(version="2").do(messages=TEST_MESSAGE[:1])
    assert resp.body.get("choices") is not None
    qianfan.get_config().AK = ak
    qianfan.get_config().SK = sk
    qianfan.get_config().ACCESS_KEY = access_key
    qianfan.get_config().SECRET_KEY = secret_key
    qianfan.get_config().BEARER_TOKEN = None


def test_refresh_token():
    with EnvHelper(
        QIANFAN_BEARER_TOKEN_EXPIRED_INTERVAL="15",
        QIANFAN_ACCESS_TOKEN_REFRESH_MIN_INTERVAL="0",
    ):
        chat = qianfan.ChatCompletion(version=2, app_id="app-xxx")

        def call() -> qianfan.QfResponse:
            resp = chat.do(
                messages=[{"role": "user", "content": "你好"}],
                model="xxxx",
                preemptable=True,
                top_p=0.5,
            )
            return resp

        resp1 = call()
        resp2 = call()
        assert (
            resp1.request.headers["Authorization"]
            == resp2.request.headers["Authorization"]
        )
        time.sleep(11)
        resp3 = call()
        assert (
            resp1.request.headers["Authorization"]
            != resp3.request.headers["Authorization"]
        )
