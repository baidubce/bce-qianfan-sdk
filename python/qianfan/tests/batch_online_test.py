# Copyright (c) 2025 Baidu, Inc. All Rights Reserved.
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
import pytest
import asyncio

from qianfan.resources.batch_online import Batch, AsyncBatch
from qianfan import config as qianfan_config

def test_chat_completions():
    test_prompt = "如果我是一个码农，我应该学习哪些知识"
    test_model = "deepseek-v3"

    api_key = "XXX"

    resp = Batch().chat().completions(api_key).create(
        messages=[{"role": "user", "content": test_prompt}],
        model=test_model,
        timeout=10*60
    )

    print("-------")
    print(resp)
    print("-------")

    assert isinstance(resp, str)
    assert len(resp) > 0

    return


def test_chat_completions_raw():
    test_prompt = "如果我是一个码农，我应该学习哪些知识"
    test_model = "deepseek-v3"

    api_key = ""
    resp = Batch().chat().completions(api_key).create_with_raw_response(
        messages=[{"role": "user", "content": test_prompt}],
        model=test_model,
        timeout=10*60
    )

    print("-------")
    print(resp)
    print("-------")

    assert hasattr(resp, "choices")
    assert hasattr(resp.choices[0].message, "content")
    assert len(resp.choices[0].message.content) > 0

    return

@pytest.mark.asyncio
async def test_async_chat_completions():
    test_prompts = ["如果我是老师，我应该学习哪些知识", "如果我是码农，我应该学习哪些知识", "如果我是军人，我应该学习哪些知识"]
    test_model = "deepseek-v3"

    api_key = ""

    print()

    tasks = [
        AsyncBatch().chat().completions(api_key).create(
            messages=[{"role": "user", "content": prompt}],
            model=test_model,
            timeout=10*60
        ) for prompt in test_prompts
    ]

    results = await asyncio.gather(*tasks)


    for r in results:
        print("-------")
        print(r)
        print("-------")
        assert isinstance(r, str)
        assert len(r) > 0

    return


@pytest.mark.asyncio
async def test_async_chat_completions_raw():
    test_prompts = ["如果我是老师，我应该学习哪些知识", "如果我是码农，我应该学习哪些知识", "如果我是军人，我应该学习哪些知识"]
    test_model = "deepseek-v3"

    api_key = ""

    print()

    tasks = [
        AsyncBatch().chat().completions(api_key).create_with_raw_response(
            messages=[{"role": "user", "content": prompt}],
            model=test_model,
            timeout=10*60
        ) for prompt in test_prompts
    ]

    results = await asyncio.gather(*tasks)


    for r in results:
        print("-------")
        print(r)
        print("-------")
        assert hasattr(r, "choices")
        assert hasattr(r.choices[0].message, "content")
        assert len(r.choices[0].message.content) > 0

    return



def test_images_generation():
    test_prompt = "请画一只企鹅"
    test_model = "irag-1.0"

    api_key = ""

    resp = Batch().images().generations(api_key).generate(
        prompt=test_prompt,
        model=test_model,
        timeout=10*60
    )

    print("-------")
    print(resp)
    print("-------")

    assert isinstance(resp, list)
    assert len(resp) > 0

    return

def test_images_generation_raw():
    test_prompt = "请画一只企鹅"
    test_model = "irag-1.0"

    api_key = ""

    resp = Batch().images().generations(api_key).generate_with_raw_response(
        prompt=test_prompt,
        model=test_model,
        timeout=10*60
    )

    print("-------")
    print(resp)
    print("-------")

    assert hasattr(resp, "data")
    assert hasattr(resp.data[0], "url")
    assert len(resp.data[0].url) > 0

    return

@pytest.mark.asyncio
async def test_async_images_generation():
    test_prompts = ["请画一只企鹅", "请画一只兔子"]
    test_model = "irag-1.0"

    api_key = ""

    print()

    tasks = [
        AsyncBatch().images().generations(api_key).generate(
            prompt=prompt,
            model=test_model,
            timeout=10*60
        ) for prompt in test_prompts
    ]

    results = await asyncio.gather(*tasks)


    for r in results:
        print("-------")
        print(r)
        print("-------")
        assert isinstance(r, list)
        assert len(r) > 0

    return


@pytest.mark.asyncio
async def test_async_images_generation_raw():
    test_prompts = ["请画一只企鹅", "请画一只兔子"]
    test_model = "irag-1.0"

    api_key = ""

    print()

    tasks = [
        AsyncBatch().images().generations(api_key).generate_with_raw_response(
            prompt=prompt,
            model=test_model,
            timeout=10*60
        ) for prompt in test_prompts
    ]

    results = await asyncio.gather(*tasks)


    for r in results:
        print("-------")
        print(r)
        print("-------")
        assert hasattr(r, "data")
        assert hasattr(r.data[0], "url")
        assert len(r.data[0].url) > 0

    return