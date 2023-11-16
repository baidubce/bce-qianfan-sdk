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
    Unit test for Txt2Image
"""

import time

import pytest

import qianfan
import qianfan.tests.utils


def test_text2image_generate():
    """
    Test basic generate text2image
    """
    qfg = qianfan.Text2Image()
    resp = qfg.do(prompt="Rag doll cat")
    assert len(resp["body"]["data"]) == 1

    resp = qfg.do(prompt="Rag doll cat", with_decode="base64")
    assert resp["body"]["data"] is not None
    assert "image" in resp["body"]["data"][0]


@pytest.mark.asyncio
async def test_text2image_agenerate():
    """
    Test basic async generate text2image
    """
    qfg = qianfan.Text2Image()
    resp = await qfg.ado(prompt="Rag doll cat")
    assert len(resp["body"]["data"]) == 1

    resp = await qfg.ado(prompt="Rag doll cat", with_decode="base64")
    assert resp["body"]["data"] is not None
    assert "image" in resp["body"]["data"][0]


def test_batch_predict():
    CASE_LEN = 10
    prompt_list = [f"test prompt {i}" for i in range(CASE_LEN)]
    # _delay is the argument only for unit test
    # it will make the response delay for a while
    start_time = time.time()
    results = (
        qianfan.Text2Image().batch_do(prompt_list, worker_num=4, _delay=1).results()
    )
    assert 5 >= time.time() - start_time >= 3
    for input, output in zip(prompt_list, results):
        assert input == output["_request"]["prompt"]

    start_time = time.time()
    future = qianfan.Text2Image().batch_do(prompt_list, worker_num=5, _delay=1)
    for i, output in enumerate(future):
        assert prompt_list[i] == output.result()["_request"]["prompt"]
    assert 3 >= time.time() - start_time >= 2

    start_time = time.time()
    future = qianfan.Text2Image().batch_do(prompt_list, worker_num=5, _delay=1)
    assert future.task_count() == CASE_LEN
    while future.finished_count() != future.task_count():
        time.sleep(0.3)
    assert 3 >= time.time() - start_time >= 2
    assert future.finished_count() == CASE_LEN
    for input, output in zip(prompt_list, future.results()):
        assert input == output["_request"]["prompt"]

    start_time = time.time()
    future = qianfan.Text2Image().batch_do(prompt_list, worker_num=5, _delay=0.5)
    assert future.task_count() == CASE_LEN
    future.wait()
    assert 2 >= time.time() - start_time >= 1
    assert future.finished_count() == CASE_LEN
    for input, output in zip(prompt_list, future.results()):
        assert input == output["_request"]["prompt"]


@pytest.mark.asyncio
async def test_batch_predict_async():
    CASE_LEN = 10
    prompt_list = [f"test prompt {i}" for i in range(CASE_LEN)]
    # _delay is the argument only for unit test
    # it will make the response delay for a while
    start_time = time.time()
    results = await qianfan.Text2Image().abatch_do(prompt_list, worker_num=4, _delay=1)
    assert 5 >= time.time() - start_time >= 3
    for input, output in zip(prompt_list, results):
        assert input == output["_request"]["prompt"]
