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
    Unit test for VersatileRateLimiter
"""
import asyncio
import threading
import time

import pytest

import qianfan
from qianfan.config import get_config
from qianfan.resources.rate_limiter import VersatileRateLimiter
from qianfan.tests.chat_completion_test import TEST_MESSAGE


def test_not_sync_rate_limiter():
    start_timestamp = time.time()
    rl = VersatileRateLimiter()
    for i in range(0, 5):
        with rl.acquire():
            pass
    end_timestamp = time.time()
    assert end_timestamp - start_timestamp < 1


@pytest.mark.asyncio
async def test_not_async_rate_limiter():
    async def async_sleep(rl):
        async with rl.acquire():
            pass

    start_timestamp = time.time()
    rl = VersatileRateLimiter()
    task_list = []
    for i in range(0, 5):
        task_list.append(asyncio.create_task(async_sleep(rl)))

    await asyncio.wait(task_list)
    end_timestamp = time.time()
    assert end_timestamp - start_timestamp < 1


def test_sync_rate_limiter():
    start_timestamp = time.time()
    rl = VersatileRateLimiter(query_per_second=1)
    for i in range(0, 5):
        with rl.acquire():
            pass
    end_timestamp = time.time()
    assert end_timestamp - start_timestamp >= 4


@pytest.mark.asyncio
async def test_async_rate_limiter():
    async def async_sleep(rl):
        async with rl.acquire():
            pass

    start_timestamp = time.time()
    rl = VersatileRateLimiter(query_per_second=1)
    task_list = []
    for i in range(0, 5):
        task_list.append(asyncio.create_task(async_sleep(rl)))

    await asyncio.wait(task_list)
    end_timestamp = time.time()
    assert end_timestamp - start_timestamp >= 4


def test_sync_rate_limiter_in_call():
    chat = qianfan.ChatCompletion(query_per_second=2, key="1")
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
    chat = qianfan.ChatCompletion(query_per_second=2, key="2")
    start_timestamp = time.time()
    task = []
    for i in range(2):
        task.append(asyncio.create_task(chat.ado(messages=TEST_MESSAGE)))
    await asyncio.wait(task)
    end_time = time.time()
    assert end_time - start_timestamp < 1.2

    start_timestamp = time.time()
    task = []
    for i in range(3):
        task.append(asyncio.create_task(chat.ado(messages=TEST_MESSAGE)))
    await asyncio.wait(task)
    end_time = time.time()
    assert end_time - start_timestamp > 1


@pytest.mark.asyncio
async def test_async_rate_limiter_in_call_with_qps_sub1():
    chat = qianfan.ChatCompletion(query_per_second=0.5, key="3")
    start_timestamp = time.time()
    task = []
    for i in range(2):
        task.append(asyncio.create_task(chat.ado(messages=TEST_MESSAGE)))
    await asyncio.wait(task)
    end_time = time.time()
    assert end_time - start_timestamp > 2

    start_timestamp = time.time()
    task = []
    for i in range(3):
        task.append(asyncio.create_task(chat.ado(messages=TEST_MESSAGE)))
    await asyncio.wait(task)
    end_time = time.time()
    assert end_time - start_timestamp > 4


def test_set_rate_limiter_through_environment_variable():
    get_config().QPS_LIMIT = 0.5
    start_timestamp = time.time()
    rl = VersatileRateLimiter()
    for i in range(0, 5):
        with rl.acquire():
            pass
    end_timestamp = time.time()
    assert end_timestamp - start_timestamp >= 6
    get_config().QPS_LIMIT = 0


def test_set_rpm_limiter_function():
    start_timestamp = time.time()
    rpm_rl = VersatileRateLimiter(request_per_minute=10)
    for i in range(0, 2):
        with rpm_rl.acquire():
            pass
    end_timestamp = time.time()
    assert end_timestamp - start_timestamp >= 2


def test_multi_thread_case_limiter():
    start_timestamp = time.time()
    rpm_rl = VersatileRateLimiter(query_per_second=5)
    t_list = []

    def _inner_thread_working_function():
        with rpm_rl.acquire():
            ...

    for i in range(5):
        t = threading.Thread(target=_inner_thread_working_function)
        t.start()
        t_list.append(t)

    for t in t_list:
        t.join()

    end_timestamp = time.time()
    assert end_timestamp - start_timestamp <= 2


@pytest.mark.asyncio
async def test_async_case_limiter():
    start_timestamp = time.time()
    rpm_rl = VersatileRateLimiter(query_per_second=5)
    awaitable_list = []

    async def _inner_coroutine_working_function():
        async with rpm_rl.acquire():
            ...

    for i in range(5):
        t = _inner_coroutine_working_function()
        awaitable_list.append(asyncio.create_task(t))

    await asyncio.wait(awaitable_list)
    end_timestamp = time.time()
    assert end_timestamp - start_timestamp <= 2


def test_limit_in_thread():
    t_list = []
    for i in range(5):
        t = threading.Thread(target=test_multi_thread_case_limiter)
        t.start()
        t_list.append(t)

    for t in t_list:
        t.join()


def test_limit_in_thread_async():
    t_list = []

    def _async_run():
        asyncio.run(test_async_case_limiter())

    for i in range(5):
        t = threading.Thread(target=_async_run)
        t.start()
        t_list.append(t)

    for t in t_list:
        t.join()


def test_reset_once():
    rpm_rl = VersatileRateLimiter(query_per_second=5)
    rpm_rl.acquire()

    assert not rpm_rl._impl._is_rpm
    assert (
        rpm_rl._impl._internal_qps_rate_limiter._sync_limiter._query_per_period == 4.5
    )

    def _reset_once():
        rpm_rl.reset_once(200)

    t_list = []
    for i in range(5):
        t = threading.Thread(target=_reset_once)
        t.start()
        t_list.append(t)

    for t in t_list:
        t.join()

    assert rpm_rl._impl._has_been_reset
    assert not rpm_rl._impl._is_rpm
    assert rpm_rl._impl._new_query_per_second == 200 / 60
    assert rpm_rl._impl._internal_qps_rate_limiter._sync_limiter._query_per_period == 3


@pytest.mark.asyncio
async def test_reset_once_async():
    rpm_rl = VersatileRateLimiter(request_per_minute=300)
    rpm_rl.acquire()

    assert rpm_rl._impl._is_rpm
    assert rpm_rl._impl._internal_rpm_rate_limiter._async_limiter.max_rate == 270

    awaitable_list = []
    for i in range(5):
        awaitable_list.append(asyncio.create_task(rpm_rl.async_reset_once(200)))

    await asyncio.wait(awaitable_list)

    assert rpm_rl._impl._has_been_reset
    assert rpm_rl._impl._is_rpm
    assert rpm_rl._impl._new_request_per_minute == 200
    assert rpm_rl._impl._internal_rpm_rate_limiter._async_limiter.max_rate == 180


def test_reset_once_from_closed():
    rpm_rl = VersatileRateLimiter()
    rpm_rl.acquire()

    assert rpm_rl._impl.is_closed

    def _reset_once():
        rpm_rl.reset_once(200)

    t_list = []
    for i in range(5):
        t = threading.Thread(target=_reset_once)
        t.start()
        t_list.append(t)

    for t in t_list:
        t.join()

    assert rpm_rl._impl._has_been_reset
    assert rpm_rl._impl._is_rpm
    assert rpm_rl._impl._new_request_per_minute == 200
    assert (
        rpm_rl._impl._internal_rpm_rate_limiter._sync_limiter._query_per_period == 180
    )


@pytest.mark.asyncio
async def test_reset_once_async_from_closed():
    rpm_rl = VersatileRateLimiter()
    rpm_rl.acquire()

    assert rpm_rl._impl.is_closed

    awaitable_list = []
    for i in range(5):
        awaitable_list.append(asyncio.create_task(rpm_rl.async_reset_once(200)))

    await asyncio.wait(awaitable_list)

    assert rpm_rl._impl._has_been_reset
    assert rpm_rl._impl._is_rpm
    assert rpm_rl._impl._new_request_per_minute == 200
    assert (
        rpm_rl._impl._internal_rpm_rate_limiter._sync_limiter._query_per_period == 180
    )
