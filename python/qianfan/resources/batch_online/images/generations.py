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
from openai import OpenAI, AsyncOpenAI, APIConnectionError, APIStatusError
from openai.types.images_response import ImagesResponse as OpenAIImagesResponse
from .._helper import request_with_retry, calculate_request_last_time, async_request_with_retry

class Generations:
    """
    Generations class
    """

    def __init__(self, api_key: str = None):

        api_key = api_key or os.getenv("QIANFAN_BEARER_TOKEN")
        if not api_key:
            raise ValueError("API key is required. Please set api_key or QIANFAN_API_KEY env var.")

        self.openai_client = OpenAI(api_key= api_key, base_url=  get_config().BATCH_ONLINE_BASE_URL)


    def generate(self, prompt: str, model: str, timeout: int, **kwargs) -> List[str]:
        """
        generate images
        """

        resp = self.generate_with_raw_response(prompt, model, timeout, **kwargs)

        images = []
        for data in resp.data:
            images.append(data.url)

        return images


    def generate_with_raw_response(self, prompt: str, model: str, timeout: int, **kwargs) -> OpenAIImagesResponse:
        """
        generate images
        """

        last_time = calculate_request_last_time(timeout)
        resp = request_with_retry(
            last_time,
            self.openai_client.images.generate,
            model=model,
            prompt=prompt,
            **kwargs
        )

        return resp


class AsyncGenerations:
    """
    AsyncGenerations class
    """

    def __init__(self, api_key: str = None):
        api_key = api_key or os.getenv("QIANFAN_BEARER_TOKEN")
        if not api_key:
            raise ValueError("API key is required. Please set api_key or QIANFAN_API_KEY env var.")

        self.openai_client = AsyncOpenAI(api_key=api_key, base_url=get_config().BATCH_ONLINE_BASE_URL)

    async def generate(self, prompt: str, model: str, timeout: int, **kwargs) -> List[str]:
        """
        async  generate images
        """

        last_time = calculate_request_last_time(timeout)
        resp = self.generate_with_raw_response(prompt, model, timeout, **kwargs)

        images = []
        for data in resp:
            images.append(data.url)

        return images

    async def generate_with_raw_response(self, prompt: str, model: str, timeout: int, **kwargs) -> OpenAIImagesResponse:
        """
        async generate images
        """

        last_time = calculate_request_last_time(timeout)
        resp = await async_request_with_retry(
            last_time,
            self.openai_client.images.generate,
            model=model,
            prompt=prompt,
            **kwargs
        )

        return resp