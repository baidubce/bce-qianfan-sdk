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
    Unit test for RateLimiter
"""
import asyncio
import time

import pytest

import qianfan
from qianfan.resources.rate_limiter import RateLimiter

from qianfan.tests.chat_completion_test import TEST_MESSAGE


def test_not_sync_rate_limiter():
    start_timestamp = time.time()
    rl = RateLimiter()
    for i in range(0, 5):
        with rl:
            pass
    end_timestamp = time.time()
    assert end_timestamp - start_timestamp < 1


@pytest.mark.asyncio
async def test_not_async_rate_limiter():
    async def async_sleep(rl):
        async with rl:
            pass

    start_timestamp = time.time()
    rl = RateLimiter()
    task_list = []
    for i in range(0, 5):
        task_list.append(asyncio.create_task(async_sleep(rl)))

    await asyncio.wait(task_list)
    end_timestamp = time.time()
    assert end_timestamp - start_timestamp < 1


def test_sync_rate_limiter():
    start_timestamp = time.time()
    rl = RateLimiter(query_per_second=1)
    for i in range(0, 5):
        with rl:
            pass
    end_timestamp = time.time()
    assert end_timestamp - start_timestamp >= 4


@pytest.mark.asyncio
async def test_async_rate_limiter():
    async def async_sleep(rl):
        async with rl:
            pass

    start_timestamp = time.time()
    rl = RateLimiter(query_per_second=1)
    task_list = []
    for i in range(0, 5):
        task_list.append(asyncio.create_task(async_sleep(rl)))

    await asyncio.wait(task_list)
    end_timestamp = time.time()
    assert end_timestamp - start_timestamp >= 4


def test_sync_rate_limiter_in_call():
    chat = qianfan.ChatCompletion(query_per_second=2)
    start_timestamp = time.time()
    for i in range(2):
        chat.do(messages=TEST_MESSAGE)
    end_time = time.time()
    assert end_time - start_timestamp < 2

    start_timestamp = time.time()
    for i in range(3):
        chat.do(messages=TEST_MESSAGE)
    end_time = time.time()
    assert end_time - start_timestamp > 1


@pytest.mark.asyncio
async def test_async_rate_limiter_in_call():
    chat = qianfan.ChatCompletion(query_per_second=2)
    start_timestamp = time.time()
    task = []
    for i in range(2):
        task.append(chat.ado(messages=TEST_MESSAGE))
    await asyncio.wait(task)
    end_time = time.time()
    assert end_time - start_timestamp > 1

    start_timestamp = time.time()
    task = []
    for i in range(3):
        task.append(chat.ado(messages=TEST_MESSAGE))
    await asyncio.wait(task)
    end_time = time.time()
    assert end_time - start_timestamp > 4


@pytest.mark.asyncio
async def test_async_rate_limiter_in_call():
    chat = qianfan.ChatCompletion(query_per_second=0.5)
    start_timestamp = time.time()
    task = []
    for i in range(2):
        task.append(chat.ado(messages=TEST_MESSAGE))
    await asyncio.wait(task)
    end_time = time.time()
    assert end_time - start_timestamp > 2

    start_timestamp = time.time()
    task = []
    for i in range(3):
        task.append(chat.ado(messages=TEST_MESSAGE))
    await asyncio.wait(task)
    end_time = time.time()
    assert end_time - start_timestamp > 4
