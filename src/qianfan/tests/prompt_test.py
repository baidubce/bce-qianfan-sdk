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
    Unit test for Prompt
"""

import pytest

from qianfan import Prompt


def test_local_prompt():
    """
    test local prompt
    """
    prompt = Prompt(template="test prompt {t1} 11 {t2} 534")
    s = prompt.render(t1="t1t1t1", t2="t2t2t2")
    assert s == "test prompt t1t1t1 11 t2t2t2 534"


@pytest.mark.asyncio
async def test_local_prompt_async():
    """
    test local prompt async
    """
    prompt = Prompt(template="test prompt {t1} 11 {t2} 534")
    s = await prompt.arender(t1="t1t1t1", t2="t2t2t2")
    assert s == "test prompt t1t1t1 11 t2t2t2 534"


def test_online_prompt():
    """
    test online prompt
    """
    prompt = Prompt(id=1203)
    resp = prompt.render(name="test")
    assert resp == "mock server template response"
    resp = prompt.render(name="test", raw=True)
    assert resp["_params"]["id"] == "1203"
    assert resp["_params"]["name"] == "test"
    result = resp["result"]
    assert "content" in result
    assert "templateContent" in result


@pytest.mark.asyncio
async def test_render_prompt_async():
    """
    test online prompt async
    """
    prompt = Prompt(id=1103)
    resp = await prompt.arender(name="test")
    assert resp == "mock server template response"
    resp = await prompt.arender(name="test", raw=True)
    assert resp["_params"]["id"] == "1103"
    assert resp["_params"]["name"] == "test"
    result = resp["result"]
    assert "content" in result
    assert "templateContent" in result
