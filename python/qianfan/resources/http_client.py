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

from typing import Any, AsyncIterator, Dict, Iterator, Optional, Tuple

import aiohttp
import requests

from qianfan import get_config
from qianfan.resources.typing import QfRequest


class HTTPClient(object):
    """
    object used to make http request
    """

    def __init__(self, ssl: bool = True, **kwargs: Any) -> None:
        """
        init sync and async request session

        Args:
            ssl (bool):
                whether to use ssl verification in connection,
                default to True
            **kwargs (Any):
                arbitrary arguments
        """
        cfg = get_config()
        if not ssl or not cfg.SSL_VERIFICATION_ENABLED:
            self.ssl = False
        else:
            self.ssl = True
        self._session = requests.session()

    def _requests_proxy(self) -> Optional[Dict[str, str]]:
        """
        return proxy setting for requests
        """
        proxy_url = get_config().PROXY
        if len(proxy_url) == 0:
            return None
        return {"http": proxy_url, "https": proxy_url}

    def _aiohttp_proxy(self) -> Optional[str]:
        """
        return proxy setting for requests
        """
        proxy_url = get_config().PROXY
        if len(proxy_url) == 0:
            return None
        return proxy_url

    def request(self, req: QfRequest) -> requests.Response:
        """
        sync request
        """
        resp = self._session.request(
            **req.requests_args(),
            timeout=req.retry_config.timeout,
            verify=self.ssl,
            proxies=self._requests_proxy(),
        )
        return resp

    def request_stream(
        self, req: QfRequest
    ) -> Iterator[Tuple[bytes, requests.Response]]:
        """
        sync stream request
        """
        resp = self._session.request(
            **req.requests_args(),
            stream=True,
            timeout=req.retry_config.timeout,
            verify=self.ssl,
            proxies=self._requests_proxy(),
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
        response = await session.request(
            **req.requests_args(),
            timeout=timeout,
            ssl=self.ssl,
            proxy=self._aiohttp_proxy(),
        )
        return response, session

    async def arequest_stream(
        self, req: QfRequest
    ) -> AsyncIterator[Tuple[bytes, aiohttp.ClientResponse]]:
        """
        async stream request
        """
        async with aiohttp.ClientSession() as session:
            timeout = aiohttp.ClientTimeout(total=req.retry_config.timeout)
            async with session.request(
                **req.requests_args(),
                timeout=timeout,
                ssl=self.ssl,
                proxy=self._aiohttp_proxy(),
            ) as resp:
                async for line in resp.content:
                    yield line, resp
