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
    Unit test for Image2Text
"""

import time

import pytest

import qianfan
import qianfan.tests.utils


def test_image2text_generate():
    """
    Test basic generate image2text
    """
    qfg = qianfan.Image2Text(endpoint="fuyu1")
    resp = qfg.do(prompt="Rag doll cat", image="9j/4AAQSkZJRgABAQAAAQABAAD/xxxxx")
    assert isinstance(resp["body"]["result"], str)

    resp = qfg.do(
        prompt="Rag doll cat", image="9j/4AAQSkZJRgABAQAAAQABAAD/xxxxx", stream=True
    )
    assert resp is not None
    for result in resp:
        assert result is not None


@pytest.mark.asyncio
async def test_image2text_agenerate():
    """
    Test basic async generate image2text
    """
    qfg = qianfan.Image2Text(endpoint="fuyu1")
    resp = await qfg.ado(
        prompt="Rag doll cat", image="9j/4AAQSkZJRgABAQAAAQABAAD/xxxxx"
    )
    assert isinstance(resp["body"]["result"], str)

    resp = await qfg.ado(
        prompt="Rag doll cat", image="9j/4AAQSkZJRgABAQAAAQABAAD/xxxxx", stream=True
    )
    assert resp is not None
    async for result in resp:
        assert result is not None


def test_batch_predict():
    CASE_LEN = 10
    input_list = [
        (f"test prompt {i}", "9j/4AAQSkZJRgABAQAAAQABAAD/xxxxx")
        for i in range(CASE_LEN)
    ]
    # _delay is the argument only for unit test
    # it will make the response delay for a while
    start_time = time.time()
    results = (
        qianfan.Image2Text(endpoint="fuyu1")
        .batch_do(input_list, worker_num=4, _delay=1)
        .results()
    )
    assert 5 >= time.time() - start_time >= 3
    for input, output in zip(input_list, results):
        assert input[0] == output["_request"]["prompt"]
        assert input[1] == output["_request"]["image"]

    start_time = time.time()
    future = qianfan.Image2Text(endpoint="fuyu1").batch_do(
        input_list, worker_num=5, _delay=1
    )
    for i, output in enumerate(future):
        assert input_list[i][0] == output.result()["_request"]["prompt"]
        assert input_list[i][1] == output.result()["_request"]["image"]
    assert 4 >= time.time() - start_time >= 2

    start_time = time.time()
    future = qianfan.Image2Text(endpoint="fuyu1").batch_do(
        input_list, worker_num=5, _delay=1
    )
    assert future.task_count() == CASE_LEN
    while future.finished_count() != future.task_count():
        time.sleep(0.3)
    assert 4 >= time.time() - start_time >= 2
    assert future.finished_count() == CASE_LEN
    for input, output in zip(input_list, future.results()):
        assert input[0] == output["_request"]["prompt"]
        assert input[1] == output["_request"]["image"]

    start_time = time.time()
    future = qianfan.Image2Text(endpoint="fuyu1").batch_do(
        input_list, worker_num=5, _delay=0.5
    )
    assert future.task_count() == CASE_LEN
    future.wait()
    assert 3 >= time.time() - start_time >= 1
    assert future.finished_count() == CASE_LEN
    for input, output in zip(input_list, future.results()):
        assert input[0] == output["_request"]["prompt"]
        assert input[1] == output["_request"]["image"]


@pytest.mark.asyncio
async def test_batch_predict_async():
    CASE_LEN = 10
    input_list = [
        (f"test prompt {i}", "9j/4AAQSkZJRgABAQAAAQABAAD/xxxxx")
        for i in range(CASE_LEN)
    ]
    # _delay is the argument only for unit test
    # it will make the response delay for a while
    start_time = time.time()
    results = await qianfan.Image2Text(endpoint="fuyu1").abatch_do(
        input_list, worker_num=4, _delay=1
    )
    assert 5 >= time.time() - start_time >= 3
    for input, output in zip(input_list, results):
        assert input[0] == output["_request"]["prompt"]
        assert input[1] == output["_request"]["image"]
