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

from typing import AsyncIterator, Iterator, Tuple

import aiohttp
import requests

from qianfan.resources.typing import QfRequest


class HTTPClient(object):
    """
    object used to make http request
    """

    def __init__(self) -> None:
        """
        init sync and async request session
        """
        self._session = requests.session()

    def request(self, req: QfRequest) -> requests.Response:
        """
        sync request
        """
        resp = self._session.request(
            **req.requests_args(), timeout=req.retry_config.timeout
        )
        return resp

    def request_stream(
        self, req: QfRequest
    ) -> Iterator[Tuple[bytes, requests.Response]]:
        """
        sync stream request
        """
        resp = self._session.request(
            **req.requests_args(), stream=True, timeout=req.retry_config.timeout
        )
        for line in resp.iter_lines():
            yield line, resp

    async def arequest(
        self, req: QfRequest
    ) -> Tuple[aiohttp.ClientResponse, aiohttp.ClientSession]:
        """
        async request
        """
        session = aiohttp.ClientSession()
        timeout = aiohttp.ClientTimeout(total=req.retry_config.timeout)
        response = await session.request(**req.requests_args(), timeout=timeout)
        return response, session

    async def arequest_stream(
        self, req: QfRequest
    ) -> AsyncIterator[Tuple[bytes, aiohttp.ClientResponse]]:
        """
        async stream request
        """
        async with aiohttp.ClientSession() as session:
            timeout = aiohttp.ClientTimeout(total=req.retry_config.timeout)
            async with session.request(**req.requests_args(), timeout=timeout) as resp:
                async for line in resp.content:
                    yield line, resp
