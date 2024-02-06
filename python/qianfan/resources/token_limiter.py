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
    Implementation of Token Limiter
"""
import asyncio
import datetime
import threading
import time
from typing import Any

from qianfan import Tokenizer
from qianfan.utils import log_error

_MINUTE_DEAD = datetime.timedelta(minutes=1)


class BaseTokenLimiter:
    tokenizer = Tokenizer()

    def __init__(self, token_limit_per_minute: int = 0, **kwargs: Any) -> None:
        self._token_limit_per_minute = token_limit_per_minute
        self._token_current = self._token_limit_per_minute
        self._last_check_timestamp = datetime.datetime.utcnow()

    def _check_limit(self, token_used: int) -> None:
        if token_used > self._token_limit_per_minute:
            err_msg = (
                f"the value of token_used {token_used} exceeds the limit"
                f" {self._token_limit_per_minute}"
            )
            log_error(err_msg)
            raise ValueError(err_msg)

    def _is_closed(self) -> bool:
        return self._token_limit_per_minute == 0

    def _refresh_time_and_token(self) -> None:
        current_time = datetime.datetime.utcnow()
        if (
            self._last_check_timestamp.minute != current_time
            or current_time - self._last_check_timestamp >= _MINUTE_DEAD
        ):
            self._token_current = self._token_limit_per_minute
        self._last_check_timestamp = current_time


class TokenLimiter(BaseTokenLimiter):
    def __init__(self, token_limit_per_minute: int = 0, **kwargs: Any) -> None:
        self._lock = threading.Lock()
        super().__init__(token_limit_per_minute, **kwargs)

    def decline(self, token_used: int) -> None:
        if self._is_closed():
            return

        self._check_limit(token_used)

        with self._lock:
            for i in range(3):
                self._refresh_time_and_token()
                if token_used <= self._token_current:
                    self._token_current -= token_used
                    return
                else:
                    next_minute_dead_interval = 60 - self._last_check_timestamp.second
                    time.sleep(next_minute_dead_interval)

            err_msg = "get token from token limiter failed"
            log_error(err_msg)
            raise RuntimeError(err_msg)

    def compensate(self, compensation: int) -> None:
        if self._lock.acquire(timeout=1):
            self._token_current += compensation
            self._lock.release()


class AsyncTokenLimiter(BaseTokenLimiter):
    def __init__(self, token_limit_per_minute: int = 0, **kwargs: Any) -> None:
        self._lock = asyncio.Lock()
        super().__init__(token_limit_per_minute, **kwargs)

    async def decline(self, token_used: int) -> None:
        if self._is_closed():
            return

        self._check_limit(token_used)

        async with self._lock:
            for i in range(3):
                self._refresh_time_and_token()
                if token_used <= self._token_current:
                    self._token_current -= token_used
                    return
                else:
                    next_minute_dead_interval = 60 - self._last_check_timestamp.second
                    await asyncio.sleep(next_minute_dead_interval)

            err_msg = "get token from token limiter failed"
            log_error(err_msg)
            raise RuntimeError(err_msg)

    async def compensate(self, compensation: int) -> None:
        if not self._lock.locked():
            async with self._lock:
                self._token_current += compensation
