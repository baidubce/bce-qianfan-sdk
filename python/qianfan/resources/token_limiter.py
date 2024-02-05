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
import datetime
import threading
import time

from qianfan.utils import log_error

_MINUTE_DEAD = datetime.timedelta(minutes=1)


class TokenLimiter:
    def __init__(self, token_limit_per_minute: int):
        self._token_limit_per_minute = token_limit_per_minute
        self._token_current = self._token_limit_per_minute
        self._last_check_timestamp = datetime.datetime.utcnow()
        self._lock = threading.Lock()

    def _refresh_time_and_token(self) -> None:
        current_time = datetime.datetime.utcnow()
        if (
            self._last_check_timestamp.minute != current_time
            or current_time - self._last_check_timestamp >= _MINUTE_DEAD
        ):
            self._token_current = self._token_limit_per_minute
        self._last_check_timestamp = current_time

    def decline(self, token_used: int) -> None:
        if token_used > self._token_limit_per_minute:
            err_msg = (
                f"the value of token_used {token_used} exceeds the limit"
                f" {self._token_limit_per_minute}"
            )
            log_error(err_msg)
            raise ValueError(err_msg)

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

    def set_current_usage(self, token_remaining: int) -> None:
        self._token_current = token_remaining
