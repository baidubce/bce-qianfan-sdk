# Copyright (c) 2025 Baidu, Inc. All Rights Reserved.
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

import os
import httpx

from qianfan.config import get_config
from datetime import timedelta, datetime
from typing import Dict, List, Union, Iterable, Optional, overload
from openai import OpenAI, APIConnectionError, APIStatusError
from openai.types.chat.chat_completion import ChatCompletion as OpenAIChatCompletion
from ...errors import ArgumentNotFoundError, RequestTimeoutError

class Completions:
    """
    Completions class
    """

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key= api_key, base_url=  get_config().BATCH_ONLINE_BASE_URL)


    def create(self, messages: list[dict], model: str, timeout: int , **kwargs) -> OpenAIChatCompletion:
        """
        create a chat completion
        """
        retry_times = 0
        last_time = self._calculate_request_last_time(timeout)

        while True:
            # Check if the request has timed out.
            if datetime.now() > last_time:
                raise RequestTimeoutError(None, None)

            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream = False, # not support stream
                    **kwargs
                )
                return response
            except (APIConnectionError):
                # retry after wait_time
                wait_time = self._calculate_retry_wait_time(retry_times)

                # if the request has timed out, break the loop
                if datetime.now() + timedelta(seconds=wait_time) > last_time:
                    raise RequestTimeoutError(None, None)

                # sleep for wait_time seconds and increment retry_times
                time.sleep(wait_time)
                retry_times = retry_times + 1
                continue

            except APIStatusError as err:
                # check if the error should be retried
                if self._should_retry(err.response):
                    continue
                else:
                    raise err

            except Exception as err:
                raise err



    def _calculate_request_last_time(self, timeout: int):
        """
        calculate the last time of request based on timeout
        """

        if timeout is None or timeout <= 0:
            timeout = 24 * 3600 # default timeout is 24 hours

        timeout_seconds = 0
        if isinstance(timeout, int):
            timeout_seconds = timeout
        else:
            raise TypeError(
                "timeout type {} is not supported".format(type(timeout))
            )

        # calculate the last time of request based on timeout
        return datetime.now() + timedelta(seconds=timeout_seconds)

    def _calculate_retry_wait_time(retry_times) -> float:
        """
        retry backoff
        """

        max_retry_delay = 60
        initial_retry_delay = 1

        nb_retries = min(retry_times, max_retry_delay / initial_retry_delay)

        sleep_seconds = min(initial_retry_delay * pow(2, nb_retries), max_retry_delay)

        jitter = 1 - 0.25 * random()
        timeout = sleep_seconds * jitter
        return timeout if timeout >= 0 else 0

    def _should_retry(response):
        """
        check if the request should be retried
        """

        # Retry on rate limits.
        if response.status_code == 429:
            return True

        # Retry internal errors.
        if response.status_code >= 500:
            return True

        return False