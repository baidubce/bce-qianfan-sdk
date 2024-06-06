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
import time

import pytest

import qianfan
import qianfan.tests.utils
from qianfan.tests.utils import EnvHelper, fake_access_token
from qianfan.version import VERSION

QIANFAN_SUPPORT_COMPLETION_MOCK_MODEL = {
    "ERNIE-Bot",
    "ERNIE-Bot-turbo",
    "BLOOMZ-7B",
    "Qianfan-BLOOMZ-7B-compressed",
    "Llama-2-7B-Chat",
    "Llama-2-13B-Chat",
    "Llama-2-70B-Chat",
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
                == qianfan.ChatCompletion().get_model_info(model).endpoint
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
    # cls means the argument from constructor
    # do means the argument from do method
    # M: model
    # E: endpoint
    # NM: invalid model
    # CM: the chat model which is used to mock completion
    prompt = TEST_PROMPT[0]
    qfg_list = [
        qianfan.Completion(endpoint="endpoint_from_init_1"),  # cls.E
        qianfan.Completion(model="invalid_model"),  # cls.NM
        qianfan.Completion(
            model="invalid_model", endpoint="endpoint_from_init_3"
        ),  # cls.NM+E
        qianfan.Completion(),  # cls.None
        qianfan.Completion(model="ERNIE-Bot"),  # cls.CM
        qianfan.Completion(
            model="ERNIE-Bot", endpoint="endpoint_from_init_2"
        ),  # cls.CM+E
    ]
    for qfg in qfg_list:
        # do.E
        resp = qfg.do(endpoint="custom_endpoint_1", prompt=prompt)
        assert resp["_for_ut"]["model"] == "custom_endpoint_1"
        assert resp["_for_ut"]["type"] == "completion"
        # do.NM
        try:
            resp = qfg.do(model="invalid_model", prompt=prompt)
            # exception should be raised and here is unreachable
            assert False
        except Exception:
            pass

        # do.NM+E
        resp = qfg.do(
            model="invalid_model", endpoint="custom_endpoint_2", prompt=prompt
        )
        assert resp["_for_ut"]["model"] == "custom_endpoint_2"
        assert resp["_for_ut"]["type"] == "completion"
        # do.CM
        resp = qfg.do(model="ERNIE-Bot", prompt=prompt)
        assert resp["_for_ut"]["model"] == "completions"
        assert resp["_for_ut"]["type"] == "chat"
        # do.CM+E
        resp = qfg.do(model="ERNIE-Bot", endpoint="custom_endpoint_3", prompt=prompt)
        assert resp["_for_ut"]["model"] == "custom_endpoint_3"
        assert resp["_for_ut"]["type"] == "chat"

    # do.None
    # cls.E
    resp = qianfan.Completion(endpoint="endpoint_from_init_1").do(prompt=prompt)
    assert resp["_for_ut"]["model"] == "endpoint_from_init_1"
    assert resp["_for_ut"]["type"] == "completion"
    # cls.NM
    try:
        resp = qianfan.Completion(model="invalid_model").do(prompt=prompt)
        # exception should be raised and here is unreachable
        assert False
    except Exception:
        pass
    # cls.NM+E
    resp = qianfan.Completion(
        model="invalid_model", endpoint="endpoint_from_init_2"
    ).do(prompt=prompt)
    assert resp["_for_ut"]["model"] == "endpoint_from_init_2"
    assert resp["_for_ut"]["type"] == "completion"
    # cls.None
    resp = qianfan.Completion().do(prompt=prompt)
    assert resp["_for_ut"]["model"] == "eb-instant"
    assert resp["_for_ut"]["type"] == "chat"
    # cls.CM
    resp = qianfan.Completion(model="ERNIE-Bot").do(prompt=prompt)
    assert resp["_for_ut"]["model"] == "completions"
    assert resp["_for_ut"]["type"] == "chat"
    # cls.CM+E
    resp = qianfan.Completion(model="ERNIE-Bot", endpoint="endpoint_from_init_3").do(
        prompt=prompt
    )
    assert resp["_for_ut"]["model"] == "endpoint_from_init_3"
    assert resp["_for_ut"]["type"] == "chat"


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
                == qianfan.ChatCompletion().get_model_info(model).endpoint
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
    # cls means the argument from constructor
    # do means the argument from do method
    # M: model
    # E: endpoint
    # NM: invalid model
    # CM: the chat model which is used to mock completion
    prompt = TEST_PROMPT[0]
    qfg_list = [
        qianfan.Completion(endpoint="endpoint_from_init_1"),  # cls.E
        qianfan.Completion(model="invalid_model"),  # cls.NM
        qianfan.Completion(
            model="invalid_model", endpoint="endpoint_from_init_3"
        ),  # cls.NM+E
        qianfan.Completion(),  # cls.None
        qianfan.Completion(model="ERNIE-Bot"),  # cls.CM
        qianfan.Completion(
            model="ERNIE-Bot", endpoint="endpoint_from_init_2"
        ),  # cls.CM+E
    ]
    for qfg in qfg_list:
        # do.E
        resp = await qfg.ado(endpoint="custom_endpoint_1", prompt=prompt)
        assert resp["_for_ut"]["model"] == "custom_endpoint_1"
        assert resp["_for_ut"]["type"] == "completion"
        # do.NM
        try:
            resp = await qfg.ado(model="invalid_model", prompt=prompt)
            # exception should be raised and here is unreachable
            assert False
        except Exception:
            pass

        # do.NM+E
        resp = await qfg.ado(
            model="invalid_model", endpoint="custom_endpoint_2", prompt=prompt
        )
        assert resp["_for_ut"]["model"] == "custom_endpoint_2"
        assert resp["_for_ut"]["type"] == "completion"
        # do.CM
        resp = await qfg.ado(model="ERNIE-Bot", prompt=prompt)
        assert resp["_for_ut"]["model"] == "completions"
        assert resp["_for_ut"]["type"] == "chat"
        # do.CM+E
        resp = await qfg.ado(
            model="ERNIE-Bot", endpoint="custom_endpoint_3", prompt=prompt
        )
        assert resp["_for_ut"]["model"] == "custom_endpoint_3"
        assert resp["_for_ut"]["type"] == "chat"

    # do.None
    # cls.E
    resp = await qianfan.Completion(endpoint="endpoint_from_init_1").ado(prompt=prompt)
    assert resp["_for_ut"]["model"] == "endpoint_from_init_1"
    assert resp["_for_ut"]["type"] == "completion"
    # cls.NM
    try:
        resp = await qianfan.Completion(model="invalid_model").ado(prompt=prompt)
        # exception should be raised and here is unreachable
        assert False
    except Exception:
        pass
    # cls.NM+E
    resp = await qianfan.Completion(
        model="invalid_model", endpoint="endpoint_from_init_2"
    ).ado(prompt=prompt)
    assert resp["_for_ut"]["model"] == "endpoint_from_init_2"
    assert resp["_for_ut"]["type"] == "completion"
    # cls.None
    resp = await qianfan.Completion().ado(prompt=prompt)
    assert resp["_for_ut"]["model"] == "eb-instant"
    assert resp["_for_ut"]["type"] == "chat"
    # cls.CM
    resp = await qianfan.Completion(model="ERNIE-Bot").ado(prompt=prompt)
    assert resp["_for_ut"]["model"] == "completions"
    assert resp["_for_ut"]["type"] == "chat"
    # cls.CM+E
    resp = await qianfan.Completion(
        model="ERNIE-Bot", endpoint="endpoint_from_init_3"
    ).ado(prompt=prompt)
    assert resp["_for_ut"]["model"] == "endpoint_from_init_3"
    assert resp["_for_ut"]["type"] == "chat"


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


def test_batch_predict():
    CASE_LEN = 10
    prompt_list = [f"test prompt {i}" for i in range(CASE_LEN)]
    # _delay is the argument only for unit test
    # it will make the response delay for a while
    start_time = time.time()
    results = (
        qianfan.Completion().batch_do(prompt_list, worker_num=4, _delay=1).results()
    )
    assert 5 >= time.time() - start_time >= 3
    for input, output in zip(prompt_list, results):
        assert input in output["result"]

    start_time = time.time()
    future = qianfan.Completion().batch_do(prompt_list, worker_num=5, _delay=1)
    for i, output in enumerate(future):
        assert prompt_list[i] in output.result()["result"]
    assert 3 >= time.time() - start_time >= 2

    start_time = time.time()
    future = qianfan.Completion().batch_do(prompt_list, worker_num=5, _delay=1)
    assert future.task_count() == CASE_LEN
    while future.finished_count() != future.task_count():
        time.sleep(0.3)
    assert 3 >= time.time() - start_time >= 2
    assert future.finished_count() == CASE_LEN
    for input, output in zip(prompt_list, future.results()):
        assert input in output["result"]

    start_time = time.time()
    future = qianfan.Completion().batch_do(prompt_list, worker_num=5, _delay=0.5)
    assert future.task_count() == CASE_LEN
    future.wait()
    assert 2 >= time.time() - start_time >= 1
    assert future.finished_count() == CASE_LEN
    for input, output in zip(prompt_list, future.results()):
        assert input in output["result"]


@pytest.mark.asyncio
async def test_batch_predict_async():
    CASE_LEN = 10
    prompt_list = [f"test prompt {i}" for i in range(CASE_LEN)]
    # _delay is the argument only for unit test
    # it will make the response delay for a while
    start_time = time.time()
    results = await qianfan.Completion().abatch_do(prompt_list, worker_num=4, _delay=1)
    assert 5 >= time.time() - start_time >= 3
    for input, output in zip(prompt_list, results):
        assert input in output["result"]


def test_sdk_indicator():
    res = qianfan.Completion().do("hi")
    assert (
        res["_request"]["extra_parameters"]["request_source"]
        == f"qianfan_py_sdk_v{VERSION}"
    )
