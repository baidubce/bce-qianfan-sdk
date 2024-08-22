import asyncio
import importlib.resources as pkg_resources
import time
from hashlib import sha1
from typing import Any, Dict

from redis import ConnectionPool, Redis
from redis.asyncio import ConnectionPool as AsyncConnectionPool
from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import NoScriptError

from qianfan.resources.rate_limiter.base_rate_limiter import BaseRateLimiter


class RedisConnectionInfo:
    host: str = "127.0.0.1"
    port: int = 6379
    db: int = 0
    other: Dict[str, Any] = {}


class RedisRateLimiter(BaseRateLimiter):
    def __init__(
        self,
        query_per_second: float = 0,
        request_per_minute: float = 0,
        buffer_ratio: float = 0.1,
        forcing_disable: bool = False,
        redis_key: str = "default_key",
        redis_connection_info: RedisConnectionInfo = RedisConnectionInfo(),
        **kwargs: Any
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
            redis_key: (str),
                redis key used to identify redis rate limiter info
        """

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

        self._connection = Redis(
            connection_pool=ConnectionPool(
                host=redis_connection_info.host,
                port=redis_connection_info.port,
                db=redis_connection_info.db,
                **redis_connection_info.other
            )
        )
        self._async_connection = AsyncRedis(
            connection_pool=AsyncConnectionPool(
                host=redis_connection_info.host,
                port=redis_connection_info.port,
                db=redis_connection_info.db,
                **redis_connection_info.other
            )
        )

        self._request_per_minute = request_per_minute
        self._query_per_second = query_per_second

        self._rpm_key = redis_key + "_rpm"
        self._rpm_10s_key = redis_key + "_rpm_10s"
        self._qps_key = redis_key + "_qps"

        if request_per_minute:
            self._set_limit_info(self._rpm_key, request_per_minute, 60)
            self._set_limit_info(self._rpm_10s_key, request_per_minute / 6, 10)
        if query_per_second:
            if 0 < query_per_second < 1:
                period = 1 / query_per_second
                query_per_second = 1
                self._set_limit_info(self._qps_key, query_per_second, period)
            else:
                self._set_limit_info(self._qps_key, query_per_second, 1)

    def check_forcing_disable(self) -> bool:
        return self._forcing_disable

    def _set_limit_info(self, key: str, quantity: float, period: float) -> None:
        try:
            self._connection.evalsha(
                self._reset_limit_script_hash, 1, key, quantity, period
            )
        except NoScriptError:
            self._connection.eval(self._reset_limit_script, 1, key, quantity, period)

    async def _async_set_limit_info(
        self, key: str, quantity: float, period: float
    ) -> None:
        try:
            await self._async_connection.evalsha(
                self._reset_limit_script_hash, 1, key, quantity, period
            )
        except NoScriptError:
            await self._async_connection.eval(
                self._reset_limit_script, 1, key, quantity, period
            )

    def reset_once(self, rpm: float) -> None:
        if self.check_forcing_disable():
            return

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
        if self.check_forcing_disable():
            return

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
        if self.check_forcing_disable() or (
            self._request_per_minute == 0 and self._query_per_second == 0
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

            if wait_time_10s != 0 or wait_time != 0:
                time.sleep(max(wait_time_10s, wait_time))

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

            if wait_time:
                time.sleep(wait_time)

            return

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    async def __aenter__(self) -> None:
        if self.check_forcing_disable() or (
            self._request_per_minute == 0 and self._query_per_second == 0
        ):
            return

        if self._request_per_minute:
            try:
                wait_time_10s = await self._async_connection.evalsha(
                    self._check_limit_script_hash, 1, self._rpm_10s_key
                )
                wait_time = await self._async_connection.evalsha(
                    self._check_limit_script_hash, 1, self._rpm_key
                )
            except NoScriptError:
                wait_time_10s = await self._async_connection.eval(
                    self._check_limit_script, 1, self._rpm_10s_key
                )
                wait_time = await self._async_connection.eval(
                    self._check_limit_script, 1, self._rpm_key
                )

            if wait_time_10s != 0 or wait_time != 0:
                await asyncio.sleep(max(wait_time_10s, wait_time))

            return
        elif self._query_per_second:
            try:
                wait_time = await self._async_connection.evalsha(
                    self._check_limit_script_hash, 1, self._qps_key
                )
            except NoScriptError:
                wait_time = await self._async_connection.eval(
                    self._check_limit_script, 1, self._qps_key
                )

            if wait_time:
                await asyncio.sleep(wait_time)

            return

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass
