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
    Unit test for Completion
"""

import os

import pytest

import qianfan
import qianfan.tests.utils
from qianfan.tests.utils import EnvHelper, fake_access_token

QIANFAN_SUPPORT_COMPLETION_MOCK_MODEL = {
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

TEST_PROMPT = ["世界上第二高的山", "宥怎么读"]
TEST_ENDPOINTS = ["endpoint_jfioasr", "endpoint_58gjhfs"]


def test_generate():
    """
    Test basic generate
    """
    qfg = qianfan.Completion()
    for model in QIANFAN_SUPPORT_COMPLETION_MOCK_MODEL:
        for prompt in TEST_PROMPT:
            resp = qfg.do(
                model=model,
                prompt=prompt,
            )
            assert resp is not None
            assert resp["code"] == 200
            assert "id" in resp["body"]
            assert resp["object"] == "completion"
            ut_meta = resp["_for_ut"]
            assert (
                "/chat/" + ut_meta["model"]
                == qianfan.ChatCompletion._supported_models()[model].endpoint
            )
            assert ut_meta["type"] == "chat"
            assert ut_meta["stream"] is False
            assert resp["_request"]["messages"][-1]["content"] == prompt
    for endpoint in TEST_ENDPOINTS:
        for prompt in TEST_PROMPT:
            resp = qfg.do(endpoint=endpoint, prompt=prompt)
            assert resp is not None
            assert resp["code"] == 200
            assert "id" in resp["body"]
            assert resp["object"] == "completion"
            ut_meta = resp["_for_ut"]
            assert ut_meta["model"] == endpoint
            assert ut_meta["type"] == "completion"
            assert ut_meta["stream"] is False
            assert resp["_request"]["prompt"] == prompt


def test_priority():
    """
    Test priority between model and endpoint
    """
    qfg = qianfan.Completion()
    # if model is a chat model, will use chat api to mock
    resp = qfg.do(model="ERNIE-Bot", endpoint="custom_endpoint_1", prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "custom_endpoint_1"
    assert ut_meta["type"] == "chat"
    # if endpoint is set when initialization, will use it as default
    qfg = qianfan.Completion(endpoint="custom_endpoint_2")
    resp = qfg.do(prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "custom_endpoint_2"
    assert ut_meta["type"] == "completion"
    # endpoint as argument will override default endpoint
    resp = qfg.do(endpoint="custom_endpoint_3", prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "custom_endpoint_3"
    assert ut_meta["type"] == "completion"
    # endpoint as argument will override default endpoint
    resp = qfg.do(model="ERNIE-Bot-turbo", prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "eb-instant"
    assert ut_meta["type"] == "chat"
    # if model is set when initialization, will use it as default
    qfg = qianfan.Completion(model="ERNIE-Bot")
    resp = qfg.do(prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "completions"
    assert ut_meta["type"] == "chat"
    # endpoint as argument will override default endpoint
    resp = qfg.do(endpoint="custom_endpoint_3", prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "custom_endpoint_3"
    assert ut_meta["type"] == "completion"
    # endpoint as argument will override default endpoint
    resp = qfg.do(model="ERNIE-Bot-turbo", prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "eb-instant"
    assert ut_meta["type"] == "chat"
    # when both are provided, will override default endpoint
    resp = qfg.do(model="ERNIE-Bot-turbo", endpoint="custom_endpoint_4", prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "custom_endpoint_4"
    assert ut_meta["type"] == "chat"
    # if both model and endpoint are set when initialization,
    # endpoint will be used as default
    qfg = qianfan.Completion(model="ERNIE-Bot", endpoint="custom_endpoint_5")
    resp = qfg.do(prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "custom_endpoint_5"
    assert ut_meta["type"] == "chat"
    # endpoint as argument will override default endpoint
    resp = qfg.do(endpoint="custom_endpoint_6", prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "custom_endpoint_6"
    assert ut_meta["type"] == "completion"
    # model as argument will override default endpoint
    resp = qfg.do(model="ERNIE-Bot-turbo", prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "eb-instant"
    assert ut_meta["type"] == "chat"
    # when both are provided, will override default endpoint
    resp = qfg.do(model="ERNIE-Bot-turbo", endpoint="custom_endpoint_7", prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "custom_endpoint_7"
    assert ut_meta["type"] == "chat"


def test_generate_stream():
    """
    Test stream generate
    """
    sqfg = qianfan.Completion()
    for model in QIANFAN_SUPPORT_COMPLETION_MOCK_MODEL:
        for prompt in TEST_PROMPT:
            resp = sqfg.do(
                model=model,
                prompt=prompt,
                stream=True,
            )
            assert resp is not None
            for result in resp:
                assert result is not None
                assert "sentence_id" in result["body"]
                assert result["object"] == "completion"


@pytest.mark.asyncio
async def test_generate_async():
    """
    Test async generate
    """
    qfg = qianfan.Completion()
    for model in QIANFAN_SUPPORT_COMPLETION_MOCK_MODEL:
        for prompt in TEST_PROMPT:
            resp = await qfg.ado(model=model, prompt=prompt)

            assert resp is not None
            assert resp["code"] == 200
            assert "id" in resp["body"]
            assert resp["object"] == "completion"

            ut_meta = resp["_for_ut"]
            assert (
                "/chat/" + ut_meta["model"]
                == qianfan.ChatCompletion._supported_models()[model].endpoint
            )
            assert ut_meta["type"] == "chat"
            assert ut_meta["stream"] is False
            assert resp["_request"]["messages"][-1]["content"] == prompt

    for endpoint in TEST_ENDPOINTS:
        for prompt in TEST_PROMPT:
            resp = await qfg.ado(endpoint=endpoint, prompt=prompt)

            assert resp is not None
            assert resp["code"] == 200
            assert "id" in resp["body"]
            assert resp["object"] == "completion"

            ut_meta = resp["_for_ut"]
            assert ut_meta["model"] == endpoint
            assert ut_meta["type"] == "completion"
            assert ut_meta["stream"] is False
            assert resp["_request"]["prompt"] == prompt


@pytest.mark.asyncio
async def test_generate_stream_async():
    """
    Test async stream generate
    """
    sqfg = qianfan.Completion()
    for model in QIANFAN_SUPPORT_COMPLETION_MOCK_MODEL:
        for prompt in TEST_PROMPT:
            resp = await sqfg.ado(
                model=model,
                prompt=prompt,
                stream=True,
            )
            assert resp is not None
            async for result in resp:
                assert result is not None
                assert "sentence_id" in result["body"]
                assert result["object"] == "completion"


@pytest.mark.asyncio
async def test_async_priority():
    """
    Test priority between model and endpoint
    """
    qfg = qianfan.Completion()
    # if model is a chat model, will use chat api to mock
    resp = await qfg.ado(model="ERNIE-Bot", endpoint="custom_endpoint_1", prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "custom_endpoint_1"
    assert ut_meta["type"] == "chat"
    # if endpoint is set when initialization, will use it as default
    qfg = qianfan.Completion(endpoint="custom_endpoint_2")
    resp = await qfg.ado(prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "custom_endpoint_2"
    assert ut_meta["type"] == "completion"
    # endpoint as argument will override default endpoint
    resp = await qfg.ado(endpoint="custom_endpoint_3", prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "custom_endpoint_3"
    assert ut_meta["type"] == "completion"
    # endpoint as argument will override default endpoint
    resp = await qfg.ado(model="ERNIE-Bot-turbo", prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "eb-instant"
    assert ut_meta["type"] == "chat"
    # if model is set when initialization, will use it as default
    qfg = qianfan.Completion(model="ERNIE-Bot")
    resp = await qfg.ado(prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "completions"
    assert ut_meta["type"] == "chat"
    # endpoint as argument will override default endpoint
    resp = await qfg.ado(endpoint="custom_endpoint_3", prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "custom_endpoint_3"
    assert ut_meta["type"] == "completion"
    # endpoint as argument will override default endpoint
    resp = await qfg.ado(model="ERNIE-Bot-turbo", prompt="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "eb-instant"
    assert ut_meta["type"] == "chat"
    # when both are provided, will override default endpoint
    resp = await qfg.ado(
        model="ERNIE-Bot-turbo", endpoint="custom_endpoint_4", prompt="test"
    )
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "custom_endpoint_4"
    assert ut_meta["type"] == "chat"


def test_completion_auth():
    ak = os.environ["QIANFAN_AK"]
    sk = os.environ["QIANFAN_SK"]
    c = qianfan.Completion()
    assert c.access_token() == fake_access_token(ak, sk)
    resp = c.do(prompt="test")
    assert "result" in resp.body
    resp = c.do(prompt="test", endpoint="custom_endpoint")
    assert "result" in resp.body
    resp = c.do(prompt="test", model="ERNIE-Bot")
    assert "result" in resp.body

    ak = "ak_from_global_198357"
    sk = "sk_from_global_198357"
    qianfan.AK(ak)
    qianfan.SK(sk)
    c = qianfan.Completion()
    assert c.access_token() == fake_access_token(ak, sk)
    resp = c.do(prompt="test")
    assert "result" in resp.body
    resp = c.do(prompt="test", endpoint="custom_endpoint")
    assert "result" in resp.body
    resp = c.do(prompt="test", model="ERNIE-Bot")
    assert "result" in resp.body
    qianfan.AK(None)
    qianfan.SK(None)

    with EnvHelper(QIANFAN_AK=None, QIANFAN_SK=None):
        ak = "ak_from_args_858384"
        sk = "sk_from_args_858384"
        c = qianfan.Completion(ak=ak, sk=sk)
        assert c.access_token() == fake_access_token(ak, sk)
        resp = c.do(prompt="test")
        assert "result" in resp.body
        resp = c.do(prompt="test", endpoint="custom_endpoint")
        assert "result" in resp.body
        resp = c.do(prompt="test", model="ERNIE-Bot")
        assert "result" in resp.body
