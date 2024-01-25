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
    Unit test for Plugin
"""
import pytest

import qianfan
import qianfan.tests.utils
from qianfan.resources import QfMessages

TEST_MESSAGE = [
    {
        "role": "user",
        "content": (
            "请按照下面要求给我生成雷达图：学校教育质量: 维度：师资力量、设施、"
            "课程内容、学生满意度。对象：A,B,C三所学校。学校A的师资力量得分为10分，"
            "设施得分为8分，课程内容的得分为7分，学生满意度的得分为9分。\n*"
            " 学校B的师资力量得分为8分，设施得分为9分，课程内容的得分为8分，"
            "学生满意度的得分为7分。\n* 学校C的师资力量得分为7分，设施得分为7分，"
            "课程内容的得分为9分，学生满意度的得分为8分。"
        ),
    }
]

_TEST_PROMPT = "这个周末的天气怎么样？"


def test_qianfan_plugin_generate():
    """
    Test qianfan plugin
    """
    qfg = qianfan.Plugin(endpoint="plugin123")
    resp = qfg.do(
        _TEST_PROMPT,
    )
    assert resp is not None
    assert resp["code"] == 200
    assert "id" in resp["body"]
    assert resp["object"] == "chat.completion"
    assert len(resp["result"]) != 0
    assert "meta_info" in resp


def test_eb_plugin_generate():
    """
    Test eb plugin
    """
    qfg = qianfan.Plugin()
    resp = qfg.do(
        TEST_MESSAGE,
        plugins=["eChart"],
    )
    assert resp is not None
    assert resp["code"] == 200
    assert "id" in resp["body"]
    assert resp["object"] == "chat.completion"
    assert len(resp["result"]) != 0
    assert "plugin_info" in resp
    qfmsgs = QfMessages()
    qfmsgs.append(_TEST_PROMPT, "user")

    resp = qfg.do(
        qfmsgs,
        plugins=["eChart"],
    )
    assert resp is not None
    assert resp["code"] == 200
    assert "id" in resp["body"]
    assert resp["object"] == "chat.completion"
    assert len(resp["result"]) != 0
    assert "plugin_info" in resp


def test_eb_plugin_generate_with_params():
    plugin = qianfan.Plugin("EBPluginV2")
    for r in plugin.do(TEST_MESSAGE, plugins=["eChart"], stream=True):
        assert r is not None
        assert r["body"].get("_event")


@pytest.mark.asyncio
async def test_async_qianfan_plugin_generate():
    """
    Test qianfan plugin
    """
    qfg = qianfan.Plugin(endpoint="plugin123")
    resp = await qfg.ado(
        _TEST_PROMPT,
    )
    assert resp is not None
    assert resp["code"] == 200
    assert "id" in resp["body"]
    assert resp["object"] == "chat.completion"
    assert len(resp["result"]) != 0
    assert "meta_info" in resp


@pytest.mark.asyncio
async def test_async_eb_plugin_generate():
    """
    Test eb plugin
    """
    qfg = qianfan.Plugin()
    resp = await qfg.ado(
        TEST_MESSAGE,
        plugins=["eChart"],
    )
    assert resp is not None
    assert resp["code"] == 200
    assert "id" in resp["body"]
    assert resp["object"] == "chat.completion"
    assert len(resp["result"]) != 0
    assert "plugin_info" in resp
