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
    Unit test for Embedding
"""

import os
import time

import pytest

import qianfan
import qianfan.tests.utils
from qianfan.tests.utils import EnvHelper, fake_access_token

QIANFAN_SUPPORT_EMBEDDING_MODEL = {"Embedding-V1"}
TEST_MESSAGE = ["世界上第二高的山", "宥怎么读"]


def test_embedding():
    """
    Test Embedding
    """
    embed = qianfan.Embedding()
    for model in QIANFAN_SUPPORT_EMBEDDING_MODEL:
        resp = embed.do(model=model, texts=TEST_MESSAGE)
        assert resp is not None
        assert resp["code"] == 200
        assert resp["object"] == "embedding_list"
        assert len(resp["data"]) == len(TEST_MESSAGE)
        for data in resp["data"]:
            assert data["object"] == "embedding"
            assert isinstance(data["embedding"][0], float)


def test_custom_endpoint():
    """
    Test Embedding with custom endpoint
    """
    embed = qianfan.Embedding()
    resp = embed.do(texts="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "embedding-v1"
    assert ut_meta["type"] == "embedding"
    resp = embed.do(model="bge-large-zh", texts="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "bge_large_zh"
    assert ut_meta["type"] == "embedding"
    resp = embed.do(endpoint="custom_endpoint_1", texts="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "custom_endpoint_1"
    assert ut_meta["type"] == "embedding"
    # with default model
    embed = qianfan.Embedding(model="bge-large-zh")
    resp = embed.do(texts="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "bge_large_zh"
    assert ut_meta["type"] == "embedding"
    resp = embed.do(endpoint="custom_endpoint_2", texts="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "custom_endpoint_2"
    assert ut_meta["type"] == "embedding"
    # with default endpoint
    embed = qianfan.Embedding(endpoint="custom_endpoint_3")
    resp = embed.do(texts="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "custom_endpoint_3"
    assert ut_meta["type"] == "embedding"
    resp = embed.do(endpoint="custom_endpoint_4", texts="test")
    ut_meta = resp["_for_ut"]
    assert ut_meta["model"] == "custom_endpoint_4"
    assert ut_meta["type"] == "embedding"


@pytest.mark.asyncio
async def test_embedding_async():
    """
    Test async Embedding
    """
    embed = qianfan.Embedding()
    for model in QIANFAN_SUPPORT_EMBEDDING_MODEL:
        resp = await embed.ado(model=model, texts=TEST_MESSAGE)
        assert resp is not None
        assert resp["code"] == 200
        assert resp["object"] == "embedding_list"
        assert len(resp["data"]) == len(TEST_MESSAGE)
        for data in resp["data"]:
            assert data["object"] == "embedding"
            assert isinstance(data["embedding"][0], float)


def test_embedding_auth():
    ak = os.environ["QIANFAN_AK"]
    sk = os.environ["QIANFAN_SK"]
    c = qianfan.Embedding()
    assert c.access_token() == fake_access_token(ak, sk)
    resp = c.do(texts=TEST_MESSAGE[0])
    assert "data" in resp.body
    resp = c.do(texts=TEST_MESSAGE[0], endpoint="custom_endpoint")
    assert "data" in resp.body
    resp = c.do(texts=TEST_MESSAGE[0], model="bge-large-en")
    assert "data" in resp.body

    ak = "ak_from_global_521812"
    sk = "sk_from_global_521812"
    qianfan.AK(ak)
    qianfan.SK(sk)
    c = qianfan.Embedding()
    assert c.access_token() == fake_access_token(ak, sk)
    resp = c.do(texts=TEST_MESSAGE[0])
    assert "data" in resp.body
    resp = c.do(texts=TEST_MESSAGE[0], endpoint="custom_endpoint")
    assert "data" in resp.body
    resp = c.do(texts=TEST_MESSAGE[0], model="bge-large-en")
    assert "data" in resp.body
    qianfan.AK(None)
    qianfan.SK(None)

    with EnvHelper(QIANFAN_AK=None, QIANFAN_SK=None):
        ak = "ak_from_args_846254"
        sk = "sk_from_args_846254"
        c = qianfan.Embedding(ak=ak, sk=sk)
        assert c.access_token() == fake_access_token(ak, sk)
        resp = c.do(texts=TEST_MESSAGE[0])
        assert "data" in resp.body
        resp = c.do(texts=TEST_MESSAGE[0], endpoint="custom_endpoint")
        assert "data" in resp.body
        resp = c.do(texts=TEST_MESSAGE[0], model="bge-large-en")
        assert "data" in resp.body


def test_batch_predict():
    CASE_LEN = 10
    text_list = [[f"test prompt {i}"] for i in range(CASE_LEN)]
    # _delay is the argument only for unit test
    # it will make the response delay for a while
    start_time = time.time()
    results = qianfan.Embedding().batch_do(text_list, worker_num=4, _delay=1).results()
    assert 5 >= time.time() - start_time >= 3
    for input, output in zip(text_list, results):
        assert input == output["_request"]["input"]

    start_time = time.time()
    future = qianfan.Embedding().batch_do(text_list, worker_num=5, _delay=1)
    for i, output in enumerate(future):
        assert text_list[i] == output.result()["_request"]["input"]
    assert 3 >= time.time() - start_time >= 2

    start_time = time.time()
    future = qianfan.Embedding().batch_do(text_list, worker_num=5, _delay=1)
    assert future.task_count() == CASE_LEN
    while future.finished_count() != future.task_count():
        time.sleep(0.3)
    assert 3 >= time.time() - start_time >= 2
    assert future.finished_count() == CASE_LEN
    for input, output in zip(text_list, future.results()):
        assert input == output["_request"]["input"]


@pytest.mark.asyncio
async def test_batch_predict_async():
    CASE_LEN = 10
    text_list = [[f"test prompt {i}"] for i in range(CASE_LEN)]
    # _delay is the argument only for unit test
    # it will make the response delay for a while
    start_time = time.time()
    results = await qianfan.Embedding().abatch_do(text_list, worker_num=4, _delay=1)
    assert 5 >= time.time() - start_time >= 3
    for input, output in zip(text_list, results):
        assert input == output["_request"]["input"]
