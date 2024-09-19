import asyncio
import importlib.resources as pkg_resources
import random
import threading
import time
from hashlib import sha1
from typing import (
    Any,
    Awaitable,
    Optional,
)

from qianfan.utils import log_warn

try:
    from redis import ConnectionPool, Redis
    from redis.asyncio import ConnectionPool as AsyncConnectionPool
    from redis.asyncio import Redis as AsyncRedis
    from redis.exceptions import NoScriptError
except ImportError:
    log_warn("no redis installed, RedisRateLimiter unavailable")

from qianfan.resources.rate_limiter.base_rate_limiter import BaseRateLimiter

rand = random.Random()


class RedisConnectionInfo:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6379,
        db: int = 0,
        **other: Any,
    ) -> None:
        self.host = host
        self.port = port
        self.db = db
        self.other = other


class RedisRateLimiter(BaseRateLimiter):
    def __init__(
        self,
        query_per_second: float = 0,
        request_per_minute: float = 0,
        buffer_ratio: float = 0.1,
        forcing_disable: bool = False,
        redis_connection_info: Optional[RedisConnectionInfo] = None,
        **kwargs: Any,
    ) -> None:
        """
        initialize a RedisRateLimiter instance

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
            forcing_disable (bool):
                Force to disable all functionality of rate limiter.
                Default to False
            redis_connection_info: (Optional[RedisConnectionInfo])：
                redis connection info
                Default to None
        """
        if redis_connection_info is None:
            redis_connection_info = RedisConnectionInfo()

        self._forcing_disable = forcing_disable
        if self.check_forcing_disable():
            return

        with pkg_resources.open_text(
            "qianfan.resources.rate_limiter", "check_rate_limiter.lua", "utf8"
        ) as script:
            self._check_limit_script = script.read()
            self._check_limit_script_hash = sha1(
                bytes(self._check_limit_script, encoding="utf8")
            ).hexdigest()

        with pkg_resources.open_text(
            "qianfan.resources.rate_limiter", "reset_rate_limiter.lua", "utf8"
        ) as script:
            self._reset_limit_script = script.read()
            self._reset_limit_script_hash = sha1(
                bytes(self._reset_limit_script, encoding="utf8")
            ).hexdigest()

        with pkg_resources.open_text(
            "qianfan.resources.rate_limiter", "pulse.lua", "utf8"
        ) as script:
            self._pulse_script = script.read()
            self._pulse_script_hash = sha1(
                bytes(self._pulse_script, encoding="utf8")
            ).hexdigest()

        self._connection = Redis(
            connection_pool=ConnectionPool(
                host=redis_connection_info.host,
                port=redis_connection_info.port,
                db=redis_connection_info.db,
                **redis_connection_info.other,
            )
        )
        self._async_connection = AsyncRedis(
            connection_pool=AsyncConnectionPool(
                host=redis_connection_info.host,
                port=redis_connection_info.port,
                db=redis_connection_info.db,
                **redis_connection_info.other,
            )
        )

        self._request_per_minute = request_per_minute
        self._query_per_second = query_per_second

        self._has_been_reset = False
        self._has_been_init = False

        self._reset_lock = threading.Lock()
        self._async_reset_lock = asyncio.Lock()

        self._init_lock = threading.Lock()

        self.key_prefix = "_default"

        self._rpm_key = self.key_prefix + "_rpm"
        self._rpm_10s_key = self.key_prefix + "_rpm_10s"
        self._qps_key = self.key_prefix + "_qps"

        self._exit = False
        self._pulse_thread = threading.Thread(target=self._pulse, daemon=True)

        super().__init__(**kwargs)

    def check_forcing_disable(self) -> bool:
        return self._forcing_disable

    def _reset_expire_key_time(self, key: str) -> None:
        try:
            self._connection.evalsha(
                self._pulse_script_hash,
                1,
                key,
            )
        except NoScriptError:
            self._connection.eval(
                self._pulse_script,
                1,
                key,
            )

    def _pulse(self) -> None:
        while not self._exit:
            request_per_minute = self._request_per_minute
            query_per_second = self._query_per_second

            if request_per_minute:
                self._reset_expire_key_time(self._rpm_key)
                self._reset_expire_key_time(self._rpm_10s_key)
            elif query_per_second:
                self._reset_expire_key_time(self._qps_key)

            sleep_time = rand.randint(60, 600)
            time.sleep(sleep_time)

    def _set_limit_info(self, key: str, quantity: float, period: float) -> None:
        str_quantity = str(quantity)
        str_period = str(period)

        try:
            self._connection.evalsha(
                self._reset_limit_script_hash, 1, key, str_quantity, str_period
            )
        except NoScriptError:
            self._connection.eval(
                self._reset_limit_script, 1, key, str_quantity, str_period
            )

    async def _async_set_limit_info(
        self, key: str, quantity: float, period: float
    ) -> None:
        str_quantity = str(quantity)
        str_period = str(period)

        try:
            await _assert_awaitable(
                self._async_connection.evalsha(
                    self._reset_limit_script_hash, 1, key, str_quantity, str_period
                )
            )
        except NoScriptError:
            await _assert_awaitable(
                self._async_connection.eval(
                    self._reset_limit_script, 1, key, str_quantity, str_period
                )
            )

    def reset_once(self, rpm: float) -> None:
        if self.check_forcing_disable() or not self._has_been_init:
            return

        with self._reset_lock:
            if self._has_been_reset:
                return

            self._has_been_reset = True

            if self._request_per_minute and (rpm < self._request_per_minute):
                self._request_per_minute = rpm
                self._set_limit_info(self._rpm_key, rpm, 60)
                self._set_limit_info(self._rpm_10s_key, rpm / 6, 10)
            elif self._query_per_second and (rpm < self._query_per_second * 60):
                if rpm < 60:
                    period = 60 / rpm
                    rpm = 60
                else:
                    period = 1

                self._query_per_second = rpm / 60
                self._set_limit_info(self._qps_key, rpm / 60, period)

    async def async_reset_once(self, rpm: float) -> None:
        if self.check_forcing_disable() or not self._has_been_init:
            return

        async with self._async_reset_lock:
            if self._has_been_reset:
                return

            self._has_been_reset = True

            if self._request_per_minute and (rpm < self._request_per_minute):
                self._request_per_minute = rpm
                await self._async_set_limit_info(self._rpm_key, rpm, 60)
                await self._async_set_limit_info(self._rpm_10s_key, rpm / 6, 10)
            elif self._query_per_second and (rpm < self._query_per_second * 60):
                if rpm < 60:
                    period = 60 / rpm
                    rpm = 60
                else:
                    period = 1

                self._query_per_second = rpm / 60
                await self._async_set_limit_info(self._qps_key, rpm / 60, period)

    def __enter__(self) -> None:
        if (
            self.check_forcing_disable()
            or (self._request_per_minute == 0 and self._query_per_second == 0)
            or not self._has_been_init
        ):
            return

        if self._request_per_minute:
            try:
                wait_time_10s = self._connection.evalsha(
                    self._check_limit_script_hash, 1, self._rpm_10s_key
                )
                wait_time = self._connection.evalsha(
                    self._check_limit_script_hash, 1, self._rpm_key
                )
            except NoScriptError:
                wait_time_10s = self._connection.eval(
                    self._check_limit_script, 1, self._rpm_10s_key
                )
                wait_time = self._connection.eval(
                    self._check_limit_script, 1, self._rpm_key
                )

            assert not isinstance(wait_time, Awaitable) and not isinstance(
                wait_time_10s, Awaitable
            )
            float_wait_time = float(wait_time)
            float_wait_time_10s = float(wait_time_10s)
            if float_wait_time_10s != 0 or float_wait_time != 0:
                time.sleep(max(float_wait_time_10s, float_wait_time))

            return
        elif self._query_per_second:
            try:
                wait_time = self._connection.evalsha(
                    self._check_limit_script_hash, 1, self._qps_key
                )
            except NoScriptError:
                wait_time = self._connection.eval(
                    self._check_limit_script, 1, self._qps_key
                )

            assert not isinstance(wait_time, Awaitable)
            float_wait_time = float(wait_time)
            if float_wait_time:
                time.sleep(float_wait_time)

            return

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    async def __aenter__(self) -> None:
        if (
            self.check_forcing_disable()
            or (self._request_per_minute == 0 and self._query_per_second == 0)
            or not self._has_been_init
        ):
            return

        if self._request_per_minute:
            try:
                wait_time_10s = await _assert_awaitable(
                    self._async_connection.evalsha(
                        self._check_limit_script_hash, 1, self._rpm_10s_key
                    )
                )
                wait_time = await _assert_awaitable(
                    self._async_connection.evalsha(
                        self._check_limit_script_hash, 1, self._rpm_key
                    )
                )
            except NoScriptError:
                wait_time_10s = await _assert_awaitable(
                    self._async_connection.eval(
                        self._check_limit_script, 1, self._rpm_10s_key
                    )
                )
                wait_time = await _assert_awaitable(
                    self._async_connection.eval(
                        self._check_limit_script, 1, self._rpm_key
                    )
                )

            float_wait_time = float(wait_time)
            float_wait_time_10s = float(wait_time_10s)
            if float_wait_time_10s != 0 or float_wait_time != 0:
                await asyncio.sleep(max(float_wait_time_10s, float_wait_time))

            return
        elif self._query_per_second:
            try:
                wait_time = await _assert_awaitable(
                    self._async_connection.evalsha(
                        self._check_limit_script_hash, 1, self._qps_key
                    )
                )
            except NoScriptError:
                wait_time = await _assert_awaitable(
                    self._async_connection.eval(
                        self._check_limit_script, 1, self._qps_key
                    )
                )

            float_wait_time = float(wait_time)
            if float_wait_time:
                await asyncio.sleep(float_wait_time)

            return

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    def acquire(self, key: Optional[str] = None) -> "RedisRateLimiter":
        if self._has_been_init:
            return self

        with self._init_lock:
            if self._has_been_init:
                return self

            self._has_been_init = True

            if key is not None:
                self.key_prefix = key
                self._rpm_key = key + "_rpm"
                self._rpm_10s_key = key + "_rpm_10s"
                self._qps_key = key + "_qps"

            self._set_in_redis()
            self._pulse_thread.start()

        return self

    def _set_in_redis(self) -> None:
        request_per_minute = self._request_per_minute
        query_per_second = self._query_per_second

        if request_per_minute:
            self._set_limit_info(self._rpm_key, request_per_minute, 60)
            self._set_limit_info(self._rpm_10s_key, request_per_minute / 6, 10)
        elif query_per_second:
            if 0 < query_per_second < 1:
                period = 1 / query_per_second
                query_per_second = 1
                self._set_limit_info(self._qps_key, query_per_second, period)
            else:
                self._set_limit_info(self._qps_key, query_per_second, 1)

    def __del__(self) -> None:
        self._exit = True
        self._pulse_thread.join(1)


def _assert_awaitable(handler: Any) -> Awaitable:
    assert isinstance(handler, Awaitable)
    return handler
