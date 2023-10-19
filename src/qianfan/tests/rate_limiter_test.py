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

from qianfan.resources.rate_limiter import RateLimiter


def test_sync_rate_limiter():
    start_timestamp = time.time()
    rl = RateLimiter()
    for i in range(0, 5):
        with rl:
            time.sleep(1)
    end_timestamp = time.time()
    assert end_timestamp - start_timestamp >= 5


@pytest.mark.asyncio
async def test_async_rate_limiter():
    start_timestamp = time.time()
    rl = RateLimiter()
    for i in range(0, 5):
        async with rl:
            await asyncio.sleep(1)
    end_timestamp = time.time()
    assert end_timestamp - start_timestamp >= 5
