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

"""
    Unit test for Token Limiter
"""
import asyncio
import functools
import threading
import time

import pytest

from qianfan.resources.token_limiter import AsyncTokenLimiter, TokenLimiter


def test_multi_thread_case_token_limiter():
    start_timestamp = time.time()
    tpm_rl = TokenLimiter(token_per_minute=500, buffer_ratio=0)
    t_list = []

    def _inner_thread_working_function():
        tpm_rl.decline(100)

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
    tpm_rl = AsyncTokenLimiter(token_per_minute=500, buffer_ratio=0)
    awaitable_list = []

    async def _inner_coroutine_working_function():
        await tpm_rl.decline(100)

    for i in range(5):
        t = _inner_coroutine_working_function()
        awaitable_list.append(asyncio.create_task(t))

    await asyncio.wait(awaitable_list)
    end_timestamp = time.time()
    assert end_timestamp - start_timestamp <= 2


def test_token_limit_in_thread():
    t_list = []
    for i in range(5):
        t = threading.Thread(target=test_multi_thread_case_token_limiter)
        t.start()
        t_list.append(t)

    for t in t_list:
        t.join()


def test_token_limit_in_thread_async():
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
    tpm_rl = TokenLimiter(token_per_minute=500)
    t_list = []

    for i in range(5):
        t = threading.Thread(target=functools.partial(tpm_rl.reset_once, 200))
        t.start()
        t_list.append(t)

    for t in t_list:
        t.join()

    assert tpm_rl._token_limit_per_minute == 180
    assert tpm_rl._has_been_reset


@pytest.mark.asyncio
async def test_reset_once_async():
    tpm_rl = AsyncTokenLimiter(token_per_minute=500)
    awaitable_list = []

    for i in range(5):
        awaitable_list.append(asyncio.create_task(tpm_rl.reset_once(200)))

    await asyncio.wait(awaitable_list)

    assert tpm_rl._token_limit_per_minute == 180
    assert tpm_rl._has_been_reset
