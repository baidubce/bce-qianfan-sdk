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
    Implementation of Rate Limiter
"""
import asyncio
import threading
import time
from types import TracebackType
from typing import Any, Optional, Type

from aiolimiter import AsyncLimiter

from qianfan.config import get_config
from qianfan.utils import log_error


class VersatileRateLimiter:
    """
    Implementation of Versatile Rate Limiter.
    There are different rules between synchronous and asynchronous method using,
    we recommend only use one of two method within single rate limiter at same time
    """

    def __init__(
        self,
        query_per_second: float = 0,
        request_per_minute: float = 0,
        buffer_ratio: float = 0.1,
        **kwargs: Any
    ) -> None:
        """
        initialize a VersatileRateLimiter instance

        Args:
            query_per_second (float):
                the query-per-second limitation, default to 0,
                means to not limit
            request_per_minute (float):
                the request-per-minute limitation, default to 0,
                means to not limit
            buffer_ratio (float):
                remaining rate ratio for better practice in
                production environment, default to 0.1,
                means only apply 90% rate limitation
        """
        if request_per_minute <= 0:
            request_per_minute = get_config().RPM_LIMIT
        if query_per_second <= 0:
            query_per_second = get_config().QPS_LIMIT

        if buffer_ratio > 1 or buffer_ratio <= 0:
            err_msg = "the value of buffer_ratio should between 0 and 1"
            log_error(err_msg)
            raise ValueError(err_msg)

        if request_per_minute > 0 and query_per_second > 0:
            err_msg = (
                "can't set both request_per_minute and query_per_second simultaneously"
            )
            log_error(err_msg)
            raise ValueError(err_msg)

        self._og_request_per_minute = request_per_minute
        self._og_query_per_second = query_per_second
        self._buffer_ratio = buffer_ratio
        self._has_been_reset = False
        self._reset_once_lock = threading.Lock()
        self._async_reset_once_lock = asyncio.Lock()

        self.is_closed = request_per_minute <= 0 and query_per_second <= 0
        if self.is_closed:
            return

        request_per_minute *= 1 - buffer_ratio
        query_per_second *= 1 - buffer_ratio

        if request_per_minute > 0:
            self._is_rpm = True
            self._internal_qp10s_rate_limiter = RateLimiter(request_per_minute / 6, 10)
            self._internal_rpm_rate_limiter = RateLimiter(request_per_minute, 60)

        if query_per_second > 0:
            self._is_rpm = False
            self._internal_qps_rate_limiter = RateLimiter(query_per_second)

    async def async_reset_once(self, rpm: float) -> None:
        # 检查是否已经重置过，如是，则直接返回
        if self._has_been_reset:
            return

        # 拿锁
        await self._async_reset_once_lock.acquire()
        # 检查是否在等待锁的时候被其它 worker 重置了，如是则返回
        if self._has_been_reset:
            self._async_reset_once_lock.release()
            return

        og_rpm = max(
            (
                self._og_request_per_minute
                if self._og_request_per_minute <= 0
                else self._og_query_per_second * 60
            ),
            0,
        )

        # 如果新旧值一致则不需要操作
        if og_rpm == rpm:
            self._has_been_reset = True
            self._async_reset_once_lock.release()
            return

        # 取最小的那个，如果是关闭的则直接取重置的
        rpm = min(rpm, og_rpm) if not self.is_closed else rpm
        rpm = max(rpm, 0)

        # 如果重置为 0 则直接关闭
        if rpm == 0:
            self.is_closed = True
            self._has_been_reset = True
            self._async_reset_once_lock.release()
            return

        # 重置
        self._reset_internal_rate_limiter(rpm)

        self._has_been_reset = True
        self._async_reset_once_lock.release()

    def reset_once(self, rpm: float) -> None:
        # 检查是否已经重置过，如是，则直接返回
        if self._has_been_reset:
            return

        # 拿锁
        self._reset_once_lock.acquire()
        # 检查是否在等待锁的时候被其它 worker 重置了，如是则返回
        if self._has_been_reset:
            self._reset_once_lock.release()
            return

        og_rpm = max(
            (
                self._og_request_per_minute
                if self._og_request_per_minute <= 0
                else self._og_query_per_second * 60
            ),
            0,
        )

        # 如果新旧值一致则不需要操作
        if og_rpm == rpm:
            self._has_been_reset = True
            self._reset_once_lock.release()
            return

        # 取最小的那个，如果是关闭的则直接取重置的
        rpm = min(rpm, og_rpm) if not self.is_closed else rpm
        rpm = max(rpm, 0)

        # 如果重置为 0 则直接关闭
        if rpm == 0:
            self.is_closed = True
            self._has_been_reset = True
            self._reset_once_lock.release()
            return

        # 重置
        self._reset_internal_rate_limiter(rpm)

        self._has_been_reset = True
        self._reset_once_lock.release()

    def _reset_internal_rate_limiter(self, rpm: float) -> None:
        self._is_rpm = (
            True
            if self.is_closed
            else (True if self._og_request_per_minute > 0 else False)
        )

        # 记录一下新值
        if self._is_rpm:
            self._new_request_per_minute = rpm
        else:
            self._new_query_per_second = rpm / 60

        # 重置
        rpm *= self._buffer_ratio

        if self._is_rpm:
            self._internal_qp10s_rate_limiter = RateLimiter(rpm / 6, 10)
            self._internal_rpm_rate_limiter = RateLimiter(rpm, 60)
        else:
            self._internal_qps_rate_limiter = RateLimiter(rpm / 60)

    def __enter__(self) -> None:
        if self.is_closed:
            return

        if not self._has_been_reset:
            self._reset_once_lock.acquire()
            if self._has_been_reset:
                self._reset_once_lock.release()

        if self._is_rpm:
            with self._internal_rpm_rate_limiter:
                with self._internal_qp10s_rate_limiter:
                    ...
        else:
            with self._internal_qps_rate_limiter:
                ...

        if not self._has_been_reset:
            self._reset_once_lock.release()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        return

    async def __aenter__(self) -> None:
        if self.is_closed:
            return

        if not self._has_been_reset:
            await self._async_reset_once_lock.acquire()
            if self._has_been_reset:
                self._async_reset_once_lock.release()

        if self._is_rpm:
            async with self._internal_rpm_rate_limiter:
                async with self._internal_qp10s_rate_limiter:
                    ...
        else:
            async with self._internal_qps_rate_limiter:
                ...

        if not self._has_been_reset:
            self._async_reset_once_lock.release()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        return


class RateLimiter:
    """
    Implementation of Rate Limiter.
    They're different rules between synchronous and asynchronous method using,
    we recommend only use one of two method within single rate limiter at same time
    """

    class _SyncLimiter:
        def __init__(
            self,
            query_per_period: float = 1,
            period_in_second: float = 1,
            **kwargs: Any
        ):
            """
            initialize rate limiter

            Args:
                query_per_period (float): query times in one period, default to 1.0.
                period_in_second (float): time of period, default to 1.0.

            Raises:
                ValueError: A ValueError will be raised if `query_per_period` is smaller
                than 0 or `period_in_second` isn't positive
            """
            if not (query_per_period >= 0 and period_in_second > 0):
                raise ValueError(
                    "argument illegal with query_per_period {} and period_in_second {}"
                    .format(query_per_period, period_in_second)
                )
            self._query_per_period = query_per_period
            self._period_in_second = period_in_second
            self._query_per_second = query_per_period / period_in_second
            self._token_count = 0.0
            self._last_leak_timestamp = time.time()
            self._sync_lock = threading.Lock()

        def _leak(self) -> None:
            timestamp = time.time()
            delta = timestamp - self._last_leak_timestamp
            self._last_leak_timestamp = timestamp
            self._token_count = min(
                self._query_per_period,
                self._token_count + delta * self._query_per_second,
            )

        def acquire(self, amount: float = 1) -> None:
            if amount > self._query_per_period:
                raise ValueError("Can't acquire more than the maximum capacity")

            with self._sync_lock:
                while True:
                    self._leak()
                    if self._token_count >= amount:
                        self._token_count -= amount
                        return
                    time.sleep((amount - self._token_count) / self._query_per_second)

        def __enter__(self) -> None:
            """
            synchronous entrance of rate limiter
            """
            self.acquire()

        def __exit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType],
        ) -> None:
            """
            exit
            """
            return

    def _check_is_closed(self) -> bool:
        return self._is_closed

    def __init__(
        self, query_per_period: float = 0, period_in_second: float = 1, **kwargs: Any
    ):
        """
        initialize rate limiter

        Args:
            query_per_period (float):
                query times in one period, default to 0,
                meaning rate limiter close.
            period_in_second (float):
                the length of period in second, default to 1 sec.
            **kwargs (Any):
                other keyword arguments
        """

        self._is_closed = query_per_period <= 0
        if self._check_is_closed():
            return

        # 向上取整到 1，避免 AsyncLimiter 失效
        if query_per_period < 1:
            period_in_second = period_in_second / query_per_period
            query_per_period = 1

        self._async_limiter = AsyncLimiter(query_per_period, period_in_second)
        self._sync_limiter = self._SyncLimiter(query_per_period, period_in_second)

        self._query_per_period = query_per_period
        self._period_in_second = period_in_second

        # 必要的 warmup 环节，清空 bucket 中的 token，勿删以下片段
        def _warmup_procedure() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_limiter.acquire(query_per_period))

        warmup_thread = threading.Thread(target=_warmup_procedure)
        warmup_thread.start()
        warmup_thread.join()

    def acquire(self, amount: float) -> None:
        if self._check_is_closed():
            return

        self._sync_limiter.acquire(amount)

    async def async_acquire(self, amount: float) -> None:
        if self._check_is_closed():
            return

        await self._async_limiter.acquire(amount)

    def __enter__(self) -> None:
        """
        synchronous entrance of rate limiter
        """
        if self._check_is_closed():
            return

        with self._sync_limiter:
            return

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """
        exit
        """
        return

    async def __aenter__(self) -> None:
        """
        asynchronous entrance of rate limiter
        """
        if self._check_is_closed():
            return

        async with self._async_limiter:
            return

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """
        exit
        """
        return
