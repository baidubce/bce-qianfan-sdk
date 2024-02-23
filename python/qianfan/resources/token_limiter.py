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
import unicodedata
from typing import Any

from qianfan import get_config
from qianfan.utils import log_error

_MINUTE_DEAD = datetime.timedelta(minutes=1)


class _MiniLocalTokenizer:
    @classmethod
    def count_tokens(cls, text: str) -> int:
        """
        Calculate the token count for a given text using a local simulation.

        ** THIS IS CALCULATED BY LOCAL SIMULATION, NOT REAL TOKEN COUNT **

        The token count is computed as follows:
        (Chinese characters count) + (English word count * 1.3)
        """
        han_count = 0
        text_only_word = ""
        for ch in text:
            if cls._is_cjk_character(ch):
                han_count += 1
                text_only_word += " "
            elif cls._is_punctuation(ch) or cls._is_space(ch):
                text_only_word += " "
            else:
                text_only_word += ch
        word_count = len(list(filter(lambda x: x != "", text_only_word.split(" "))))
        return han_count + int(word_count * 1.3)

    @staticmethod
    def _is_cjk_character(ch: str) -> bool:
        """
        Check if the character is CJK character.
        """
        code = ord(ch)
        return 0x4E00 <= code <= 0x9FFF

    @staticmethod
    def _is_space(ch: str) -> bool:
        """
        Check if the character is space.
        """
        return ch in {" ", "\n", "\r", "\t"} or unicodedata.category(ch) == "Zs"

    @staticmethod
    def _is_punctuation(ch: str) -> bool:
        """
        Check if the character is punctuation.
        """
        code = ord(ch)
        return (
            33 <= code <= 47
            or 58 <= code <= 64
            or 91 <= code <= 96
            or 123 <= code <= 126
            or unicodedata.category(ch).startswith("P")
        )


class BaseTokenLimiter:
    """Common base function collection of Token Limiter"""

    tokenizer = _MiniLocalTokenizer()

    def __init__(
        self, token_limit_per_minute: int = 0, buffer_ratio: float = 0.1, **kwargs: Any
    ) -> None:
        self._token_limit_per_minute = token_limit_per_minute
        if self._token_limit_per_minute <= 0:
            self._token_limit_per_minute = get_config().TPM_LIMIT

        self._token_limit_per_minute = int(self._token_limit_per_minute * buffer_ratio)

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
        return self._token_limit_per_minute <= 0

    def _refresh_time_and_token(self) -> None:
        current_time = datetime.datetime.utcnow()
        if (
            self._last_check_timestamp.minute != current_time
            or current_time - self._last_check_timestamp >= _MINUTE_DEAD
        ):
            self._token_current = self._token_limit_per_minute
        self._last_check_timestamp = current_time


class TokenLimiter(BaseTokenLimiter):
    """Synchronous Token Limiter implementation"""

    def __init__(
        self, token_per_minute: int = 0, buffer_ratio: float = 0.1, **kwargs: Any
    ) -> None:
        """
        Initialize a synchronous TokenLimiter instance

        Args:
            token_per_minute (int):
                the token-per-minute limitation, default to 0,
                means to disable limitation
            buffer_ratio (float):
                remaining rate ratio for better practice in
                production environment, default to 0.1,
                means only apply 90% rate limitation
        """
        self._lock = threading.Lock()
        super().__init__(token_per_minute, buffer_ratio, **kwargs)

    def decline(self, token_used: int) -> None:
        """decline token from limiter when start to do a request"""

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
        """
        justify the remaining token count in limiter
        when receive a response from server
        """

        if self._lock.acquire(timeout=1):
            self._token_current += compensation
            self._lock.release()


class AsyncTokenLimiter(BaseTokenLimiter):
    """Asynchronous Token Limiter implementation"""

    def __init__(
        self, token_per_minute: int = 0, buffer_ratio: float = 0.1, **kwargs: Any
    ) -> None:
        """
        Initialize an asynchronous TokenLimiter instance

        Args:
            token_per_minute (int):
                the token-per-minute limitation, default to 0,
                means to disable limitation
            buffer_ratio (float):
                remaining rate ratio for better practice in
                production environment, default to 0.1,
                means only apply 90% rate limitation
        """
        self._lock = asyncio.Lock()
        super().__init__(token_per_minute, buffer_ratio, **kwargs)

    async def decline(self, token_used: int) -> None:
        """decline token from limiter when start to do a request"""

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
        """
        justify the remaining token count in limiter
        when receive a response from server
        """

        if not self._lock.locked():
            async with self._lock:
                self._token_current += compensation
