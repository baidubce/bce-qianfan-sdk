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

import json
import os
import threading
import time

import pytest

import qianfan
import qianfan.tests.utils
from qianfan.consts import Consts
from qianfan.tests.utils import EnvHelper, fake_access_token

QIANFAN_SUPPORT_CHAT_MODEL = {
    "ERNIE-Bot",
    "ERNIE-Lite-8K",
    "BLOOMZ-7B",
    "Qianfan-BLOOMZ-7B-compressed",
    "Llama-2-7B-Chat",
    "Llama-2-13B-Chat",
    "Llama-2-70B-Chat",
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
        assert "/chat/" + ut_res["model"] == qfg.get_model_info(model).endpoint
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


def test_auto_concat_truncated():
    qfg = qianfan.ChatCompletion()
    resp = qfg.do(
        endpoint="truncated", messages=TEST_MESSAGE, auto_concat_truncate=True
    )
    assert isinstance(resp, qianfan.QfResponse)
    assert resp["result"] == "[begin truncate-->end of truncated]"

    # test stream
    resp_content = ""
    for r in qfg.do(
        endpoint="truncated",
        messages=TEST_MESSAGE[:1],
        auto_concat_truncate=True,
        stream=True,
    ):
        resp_content += r["result"]
    assert resp_content == "truncated_0truncated_1truncated_2==end"


@pytest.mark.asyncio
async def test_async_auto_concat_truncated():
    qfc = qianfan.ChatCompletion()
    resp = await qfc.ado(
        endpoint="truncated", messages=TEST_MESSAGE, auto_concat_truncate=True
    )
    assert isinstance(resp, qianfan.QfResponse)
    assert resp["result"] == "[begin truncate-->end of truncated]"

    # test stream
    async_content = ""
    async for r in await qfc.ado(
        endpoint="truncated",
        messages=TEST_MESSAGE[:1],
        auto_concat_truncate=True,
        stream=True,
    ):
        async_content += r["result"]
    assert async_content == "truncated_0truncated_1truncated_2==end"


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
            assert "/chat/" + ut_res["model"] == sqfg.get_model_info(model).endpoint
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
                assert "/chat/" + ut_res["model"] == sqfg.get_model_info(model).endpoint
                assert ut_res["type"] == "chat"
                assert ut_res["stream"] is True
            turn += 1
            messages.append({"role": "assistant", "content": next_msg})
            messages.append(
                {"role": "user", "content": TEST_MULTITURN_MESSAGES[turn + 1]}
            )


def test_request_id():
    chat_comp = qianfan.ChatCompletion()
    resp = chat_comp.do(messages=TEST_MESSAGE, request_id="custom_req")
    assert resp.headers[Consts.XResponseID] == "custom_req"


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
        assert "/chat/" + ut_res["model"] == qfg.get_model_info(model).endpoint
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
            assert "/chat/" + ut_res["model"] == sqfg.get_model_info(model).endpoint
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
                assert "/chat/" + ut_res["model"] == sqfg.get_model_info(model).endpoint
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


def test_priority():
    """
    Test priority between model and endpoint
    """
    # cls means the argument from constructor
    # do means the argument from do method
    # M: model
    # E: endpoint
    # NM: invalid model
    qfg_list = [
        qianfan.ChatCompletion(model="ERNIE-Bot"),  # cls.M
        qianfan.ChatCompletion(endpoint="endpoint_from_init_1"),  # cls.E
        qianfan.ChatCompletion(model="invalid_model"),  # cls.NM
        qianfan.ChatCompletion(
            model="ERNIE-Bot", endpoint="endpoint_from_init_2"
        ),  # cls.M+E
        qianfan.ChatCompletion(
            model="invalid_model", endpoint="endpoint_from_init_3"
        ),  # cls. NM+E
        qianfan.ChatCompletion(),  # cls.None
    ]
    for qfg in qfg_list:
        # do.M
        resp = qfg.do(model="ERNIE-Bot-turbo", messages=TEST_MESSAGE[:1])
        assert resp["_for_ut"]["model"] == "eb-instant"
        # do.E
        resp = qfg.do(endpoint="custom_endpoint_1", messages=TEST_MESSAGE[:1])
        assert resp["_for_ut"]["model"] == "custom_endpoint_1"
        # do.NM
        try:
            resp = qfg.do(model="unknown_model", messages=TEST_MESSAGE[:1])
            # exception should be raised and here is unreachable
            assert False
        except Exception:
            pass
        # do.M+E
        resp = qfg.do(
            model="ERNIE-Lite-8K",
            endpoint="custom_endpoint_2",
            messages=TEST_MESSAGE[:1],
        )
        assert resp["_for_ut"]["model"] == "custom_endpoint_2"
        # do.NM+E
        resp = qfg.do(
            model="unknown_model",
            endpoint="custom_endpoint_3",
            messages=TEST_MESSAGE[:1],
        )
        assert resp["_for_ut"]["model"] == "custom_endpoint_3"

    # do.None
    # cls.M
    resp = qianfan.ChatCompletion(model="ERNIE-Bot").do(messages=TEST_MESSAGE[:1])
    assert resp["_for_ut"]["model"] == "completions"
    # cls.E
    resp = qianfan.ChatCompletion(endpoint="custom_endpoint").do(
        messages=TEST_MESSAGE[:1]
    )
    assert resp["_for_ut"]["model"] == "custom_endpoint"
    # cls.NM
    try:
        resp = qianfan.ChatCompletion(model="unknown_model").do(
            messages=TEST_MESSAGE[:1]
        )
        # exception should be raised and here is unreachable
        assert False
    except Exception:
        pass
    # cls.M+E
    resp = qianfan.ChatCompletion(model="ERNIE-Bot", endpoint="custom_endpoint").do(
        messages=TEST_MESSAGE[:1]
    )
    assert resp["_for_ut"]["model"] == "custom_endpoint"
    # cls.NM+E
    resp = qianfan.ChatCompletion(model="unknown_model", endpoint="custom_endpoint").do(
        messages=TEST_MESSAGE[:1]
    )
    assert resp["_for_ut"]["model"] == "custom_endpoint"
    # cls.None
    resp = qianfan.ChatCompletion().do(messages=TEST_MESSAGE[:1])
    assert resp["_for_ut"]["model"] == "ernie-lite-8k"


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
    qfg_list = [
        qianfan.ChatCompletion(model="ERNIE-Bot"),  # cls.M
        qianfan.ChatCompletion(endpoint="endpoint_from_init_1"),  # cls.E
        qianfan.ChatCompletion(model="invalid_model"),  # cls.NM
        qianfan.ChatCompletion(
            model="ERNIE-Bot", endpoint="endpoint_from_init_2"
        ),  # cls.M+E
        qianfan.ChatCompletion(
            model="invalid_model", endpoint="endpoint_from_init_3"
        ),  # cls. NM+E
        qianfan.ChatCompletion(),  # cls.None
    ]
    for qfg in qfg_list:
        # do.M
        resp = await qfg.ado(model="ERNIE-Bot-turbo", messages=TEST_MESSAGE[:1])
        assert resp["_for_ut"]["model"] == "eb-instant"
        # do.E
        resp = await qfg.ado(endpoint="custom_endpoint_1", messages=TEST_MESSAGE[:1])
        assert resp["_for_ut"]["model"] == "custom_endpoint_1"
        # do.NM
        try:
            resp = await qfg.ado(model="unknown_model", messages=TEST_MESSAGE[:1])
            # exception should be raised and here is unreachable
            assert False
        except Exception:
            pass
        # do.M+E
        resp = await qfg.ado(
            model="ERNIE-Lite-8K",
            endpoint="custom_endpoint_2",
            messages=TEST_MESSAGE[:1],
        )
        assert resp["_for_ut"]["model"] == "custom_endpoint_2"
        # do.NM+E
        resp = await qfg.ado(
            model="unknown_model",
            endpoint="custom_endpoint_3",
            messages=TEST_MESSAGE[:1],
        )
        assert resp["_for_ut"]["model"] == "custom_endpoint_3"

    # do.None
    # cls.M
    resp = await qianfan.ChatCompletion(model="ERNIE-Bot").ado(
        messages=TEST_MESSAGE[:1]
    )
    assert resp["_for_ut"]["model"] == "completions"
    # cls.E
    resp = await qianfan.ChatCompletion(endpoint="custom_endpoint").ado(
        messages=TEST_MESSAGE[:1]
    )
    assert resp["_for_ut"]["model"] == "custom_endpoint"
    # cls.NM
    try:
        resp = await qianfan.ChatCompletion(model="unknown_model").ado(
            messages=TEST_MESSAGE[:1]
        )
        # exception should be raised and here is unreachable
        assert False
    except Exception:
        pass
    # cls.M+E
    resp = await qianfan.ChatCompletion(
        model="ERNIE-Bot", endpoint="custom_endpoint"
    ).ado(messages=TEST_MESSAGE[:1])
    assert resp["_for_ut"]["model"] == "custom_endpoint"
    # cls.NM+E
    resp = await qianfan.ChatCompletion(
        model="unknown_model", endpoint="custom_endpoint"
    ).ado(messages=TEST_MESSAGE[:1])
    assert resp["_for_ut"]["model"] == "custom_endpoint"
    # cls.None
    resp = await qianfan.ChatCompletion().ado(messages=TEST_MESSAGE[:1])
    assert resp["_for_ut"]["model"] == "ernie-lite-8k"


def test_in_other_thread():
    t = threading.Thread(target=test_generate_with_endpoint)
    t.start()
    t.join()


def test_batch_predict():
    CASE_LEN = 10
    messages_list = [
        [{"role": "user", "content": f"test prompt {i}"}] for i in range(CASE_LEN)
    ]
    # _delay is the argument only for unit test
    # it will make the response delay for a while
    start_time = time.time()
    results = (
        qianfan.ChatCompletion()
        .batch_do(messages_list, worker_num=4, _delay=1)
        .results()
    )
    assert 5 >= time.time() - start_time >= 3
    for input, output in zip(messages_list, results):
        assert input[0]["content"] in output["result"]

    start_time = time.time()
    future = qianfan.ChatCompletion().batch_do(messages_list, worker_num=5, _delay=1)
    for i, output in enumerate(future):
        assert messages_list[i][0]["content"] in output.result()["result"]
    assert 3 >= time.time() - start_time >= 2

    start_time = time.time()
    future = qianfan.ChatCompletion().batch_do(messages_list, worker_num=5, _delay=1)
    assert future.task_count() == CASE_LEN
    while future.finished_count() != future.task_count():
        time.sleep(0.3)
    assert 3 >= time.time() - start_time >= 2
    assert future.finished_count() == CASE_LEN
    for input, output in zip(messages_list, future.results()):
        assert input[0]["content"] in output["result"]

    start_time = time.time()
    future = qianfan.ChatCompletion().batch_do(messages_list, worker_num=5, _delay=0.5)
    assert future.task_count() == CASE_LEN
    future.wait()
    assert 2 >= time.time() - start_time >= 1
    assert future.finished_count() == CASE_LEN
    for input, output in zip(messages_list, future.results()):
        assert input[0]["content"] in output["result"]


@pytest.mark.asyncio
async def test_batch_predict_async():
    CASE_LEN = 10
    messages_list = [
        [{"role": "user", "content": f"test prompt {i}"}] for i in range(CASE_LEN)
    ]
    # _delay is the argument only for unit test
    # it will make the response delay for a while
    start_time = time.time()
    results = await qianfan.ChatCompletion().abatch_do(
        messages_list, worker_num=4, _delay=1
    )
    assert 5 >= time.time() - start_time >= 3
    for input, output in zip(messages_list, results):
        assert input[0]["content"] in output["result"]


def test_auth_using_iam():
    qianfan.get_config().AK = None
    qianfan.get_config().SK = None

    results = qianfan.ChatCompletion().do(messages=TEST_MESSAGE[:1])
    assert "X-Bce-Date" in results["_header"]
    assert "Authorization" in results["_header"]


def test_keyword_arguments_passing():
    cc = qianfan.ChatCompletion(ssl=False)
    assert not cc._real._client._client.ssl


def test_truncated_message():
    messages = [{"role": "user", "content": "hello " * 10000}]
    resp = qianfan.ChatCompletion().do(messages=messages, truncate_overlong_msgs=True)
    req = resp["_request"]
    req_messages = req["messages"]
    assert len(req_messages) == 1

    messages.extend(
        [{"role": "assistant", "content": "hi1"}, {"role": "user", "content": "hi2"}]
    )
    resp = qianfan.ChatCompletion().do(messages=messages, truncate_overlong_msgs=True)
    req_messages = resp["_request"]["messages"]
    assert len(req_messages) == 1
    assert req_messages[0]["content"] == "hi2"

    messages = [
        {"role": "user", "content": "s1"},
        {"role": "assistant", "content": "s2"},
        {"role": "user", "content": "s3 " * 10000},
        {"role": "assistant", "content": "s4"},
        # cut here
        {"role": "user", "content": "s5"},
    ]
    resp = qianfan.ChatCompletion(model="BLOOMZ-7B").do(
        messages=messages, truncate_overlong_msgs=True
    )
    req_messages = resp["_request"]["messages"]
    assert len(req_messages) == 1
    assert req_messages[0]["content"] == "s5"

    messages = [
        {"role": "user", "content": "s1 " * 10000},
        {"role": "assistant", "content": "s2"},
        # cut here
        {"role": "user", "content": "s3"},
        {"role": "assistant", "content": "s4"},
        {"role": "user", "content": "s5"},
    ]
    resp = qianfan.ChatCompletion(model="BLOOMZ-7B").do(
        messages=messages, truncate_overlong_msgs=True
    )
    req_messages = resp["_request"]["messages"]
    assert len(req_messages) == 3
    assert req_messages[0]["content"] == "s3"
    assert req_messages[1]["content"] == "s4"
    assert req_messages[2]["content"] == "s5"

    # exceed max_input_token, but not exceed max_input_chars
    messages = [
        {"role": "user", "content": "s " * 5000},
        {"role": "assistant", "content": "s2"},
        # cut here
        {"role": "user", "content": "h " * 3000},
        {"role": "assistant", "content": "s4"},
        {"role": "user", "content": "s5"},
    ]
    resp = qianfan.ChatCompletion(model="ERNIE-3.5-8K").do(
        messages=messages, truncate_overlong_msgs=True
    )
    req_messages = resp["_request"]["messages"]
    assert len(req_messages) == 3
    assert req_messages[0]["content"] == "h " * 3000
    assert req_messages[1]["content"] == "s4"
    assert req_messages[2]["content"] == "s5"

    resp = qianfan.ChatCompletion(model="ERNIE-3.5-8K").do(
        messages=messages, truncate_overlong_msgs=False
    )
    # no cut
    req_messages = resp["_request"]["messages"]
    assert len(req_messages) == 5
    assert req_messages[0]["content"] == "s " * 5000
    assert req_messages[4]["content"] == "s5"

    messages = [
        {"role": "user", "content": "s1 " * 7000},
        {"role": "assistant", "function_call": {}, "name": "funcname"},
        # cut here
        {"role": "user", "content": "s3"},
        {"role": "assistant", "content": "s4"},
        {"role": "user", "content": "s5"},
    ]
    resp = qianfan.ChatCompletion(model="ERNIE-Bot").do(
        messages=messages, truncate_overlong_msgs=True
    )
    req_messages = resp["_request"]["messages"]
    assert len(req_messages) == 3
    assert req_messages[0]["content"] == "s3"
    assert req_messages[2]["content"] == "s5"

    # test msgs with system
    messages = [
        {"role": "user", "content": "s "},
        {"role": "assistant", "content": "s2"},
        {"role": "user", "content": "h " * 3000},
        {"role": "assistant", "content": "s4"},
        {"role": "user", "content": "s5"},
    ]
    system = "s " * 3000
    resp = qianfan.ChatCompletion(model="ERNIE-3.5-8K").do(
        messages=messages, truncate_overlong_msgs=True
    )
    req_messages = resp["_request"]["messages"]
    assert len(req_messages) == 5

    resp = qianfan.ChatCompletion(model="ERNIE-3.5-8K").do(
        messages=messages, truncate_overlong_msgs=True, system=system
    )
    req_messages = resp["_request"]["messages"]
    assert len(req_messages) == 1
    assert req_messages[0]["content"] == "s5"

    messages = [
        {"role": "user", "content": "s "},
        {"role": "assistant", "content": "s2"},
        {"role": "user", "content": "h " * 3000},
        {"role": "assistant", "content": "s4"},
        {"role": "user", "content": "s " * 10000},
    ]
    resp = qianfan.ChatCompletion(model="ERNIE-3.5-8K").do(
        messages=messages, truncate_overlong_msgs=True, system=system
    )
    req_messages = resp["_request"]["messages"]
    assert len(req_messages) == 1

    resp = qianfan.ChatCompletion(model="ERNIE-3.5-8K").do(
        messages=messages[-1:], truncate_overlong_msgs=True, system=system
    )
    req_messages = resp["_request"]["messages"]
    assert len(req_messages) == 1


def test_auto_model_list():
    model_list = qianfan.ChatCompletion().models()

    assert "ERNIE-99" in model_list
    assert qianfan.ChatCompletion().get_model_info("ernie-99")


def test_function_chat():
    def get_current_weather(location):
        return "25度"

    func_list = [
        {
            "name": "get_current_weather",
            "description": "获取一个地区的天气情况",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string", "description": "地点"}},
                "required": ["location"],
            },
        }
    ]
    f = qianfan.Function()
    query = "请帮我查一下上海的气温"
    msgs = qianfan.QfMessages()
    msgs.append(query, role="user")
    resp = f.do(messages=msgs, functions=func_list)
    assert resp["body"].get("function_call")

    func_call_result = resp["function_call"]
    location = json.loads(func_call_result["arguments"]).get("location")
    func_resp = get_current_weather(location)

    msgs.append(resp, role="assistant")
    msgs.append(json.dumps({"return": func_resp}), role="function")

    resp = f.do(messages=msgs, functions=func_list)
    assert resp["body"].get("result")

    # test input with model
    model_func = "ERNIE-Functions-8K"
    f = qianfan.ChatCompletion()
    query = "请帮我查一下上海的气温"
    msgs = qianfan.QfMessages()
    msgs.append(query, role="user")

    resp = f.do(model=model_func, messages=msgs, functions=func_list)
    assert resp["body"].get("function_call")

    func_call_result = resp["function_call"]
    location = json.loads(func_call_result["arguments"]).get("location")
    func_resp = get_current_weather(location)

    msgs.append(resp, role="assistant")
    msgs.append(json.dumps({"return": func_resp}), role="function")

    resp = f.do(model=model_func, messages=msgs, functions=func_list)
    assert resp["body"].get("result")


@pytest.mark.asyncio
async def test_async_function_chat():
    def get_current_weather(location):
        return "25度"

    func_list = [
        {
            "name": "get_current_weather",
            "description": "获取一个地区的天气情况",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string", "description": "地点"}},
                "required": ["location"],
            },
        }
    ]
    f = qianfan.Function()
    query = "请帮我查一下上海的气温"
    msgs = qianfan.QfMessages()
    msgs.append(query, role="user")
    resp = await f.ado(messages=msgs, functions=func_list)
    assert resp["body"].get("function_call")

    func_call_result = resp["function_call"]
    location = json.loads(func_call_result["arguments"]).get("location")
    func_resp = get_current_weather(location)

    msgs.append(resp, role="assistant")
    msgs.append(json.dumps({"return": func_resp}), role="function")

    resp = await f.ado(messages=msgs, functions=func_list)
    assert resp["body"].get("result")


def test_compat_message_format():
    resp = qianfan.ChatCompletion().do(
        messages=[
            {"role": "system", "content": "你是智能助手BD"},
            {"role": "user", "content": "你是谁"},
        ],
        adapt_openai_message_format=True,
    )

    assert "system" in resp.request.json_body
    assert resp.request.json_body.get("system") == "你是智能助手BD"
