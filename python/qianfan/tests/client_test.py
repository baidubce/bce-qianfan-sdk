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
from typing import AsyncIterator, Iterator, Optional

import pytest

from qianfan import Qianfan
from qianfan.resources.typing_client import (
    Choice,
    ChoiceDelta,
    Completion,
    CompletionChunk,
    CompletionChunkChoice,
)
from qianfan.tests.utils import Consts, EnvHelper

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


def test_client():
    client = Qianfan()
    resp = client.chat.completions.create(messages=TEST_MESSAGE)
    assert isinstance(resp, Completion)
    assert len(resp.choices) > 0
    assert isinstance(resp.choices[0], Choice)

    resp = client.chat.completions.create(model=TEST_MODEL, messages=TEST_MESSAGE)
    assert isinstance(resp, Completion)
    assert len(resp.choices) > 0
    assert isinstance(resp.choices[0], Choice)
    assert resp.model == TEST_MODEL

    stream_resp = client.chat.completions.create(
        model=TEST_MODEL,
        messages=TEST_MESSAGE,
        stream=True,
    )
    assert isinstance(stream_resp, Iterator)
    for resp in stream_resp:
        assert isinstance(resp, CompletionChunk)
        assert len(resp.choices) > 0
        assert isinstance(resp.choices[0], CompletionChunkChoice)
        assert resp.model == TEST_MODEL
        assert isinstance(resp.choices[0].delta, ChoiceDelta)
        assert resp.choices[0].delta.content != ""


def test_custom_client():
    with EnvHelper(QIANFAN_ACCESS_KEY=None, QIANFAN_SECRET_KEY=None):
        _test_custom_client()


def _test_custom_client():
    client = Qianfan()
    err: Optional[Exception] = None
    try:
        resp = client.chat.completions.create(messages=TEST_MESSAGE)
    except Exception as e:
        err = e
    assert err

    client2 = Qianfan(
        access_key=Consts.test_access_key, secret_key=Consts.test_secret_key
    )
    resp = client2.chat.completions.create(model=TEST_MODEL, messages=TEST_MESSAGE)
    assert isinstance(resp, Completion)
    assert len(resp.choices) > 0
    assert isinstance(resp.choices[0], Choice)
    assert resp.model == TEST_MODEL


@pytest.mark.asyncio
async def test_async_client():
    client = Qianfan()
    resp = await client.chat.completions.acreate(messages=TEST_MESSAGE)
    assert isinstance(resp, Completion)
    assert len(resp.choices) > 0
    assert isinstance(resp.choices[0], Choice)

    resp = await client.chat.completions.acreate(
        model=TEST_MODEL, messages=TEST_MESSAGE
    )
    assert isinstance(resp, Completion)
    assert len(resp.choices) > 0
    assert isinstance(resp.choices[0], Choice)
    assert resp.model == TEST_MODEL

    stream_resp = await client.chat.completions.acreate(
        model=TEST_MODEL,
        messages=TEST_MESSAGE,
        stream=True,
    )
    assert isinstance(stream_resp, AsyncIterator)
    async for resp in stream_resp:
        assert isinstance(resp, CompletionChunk)
        assert len(resp.choices) > 0
        assert isinstance(resp.choices[0], CompletionChunkChoice)
        assert resp.model == TEST_MODEL
        assert isinstance(resp.choices[0].delta, ChoiceDelta)
        assert resp.choices[0].delta.content != ""
