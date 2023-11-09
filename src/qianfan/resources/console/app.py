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
APP API
"""

from qianfan.consts import Consts
from qianfan.resources.console.utils import (
    async_console_api_request,
    console_api_request,
)
from qianfan.resources.typing import QfRequest


class _App(object):
    """
    Class for App related API
    """

    @classmethod
    def _list_request(cls, **kwargs: str) -> QfRequest:
        """
        create the request for list app
        """
        req = QfRequest(method="GET", url=Consts.AppListAPI)
        req.query = kwargs
        return req

    @classmethod
    @console_api_request
    def list(cls, **kwargs: str) -> QfRequest:
        """
        List all apps of the user.

        This class method is used to retrieve information about all apps of the user,
        including the app ID, api key and secret key.

        Parameters:
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling it to
        send the generated QfRequest and return a QfResponse to the user.

        API Doc: Not available yet.
        """
        return cls._list_request(**kwargs)

    @classmethod
    @async_console_api_request
    async def alist(cls, **kwargs: str) -> QfRequest:
        """
        List all apps of the user.

        This class method is used to retrieve information about all apps of the user,
        including the app ID, api key and secret key.

        Parameters:
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        Note:
        The `@async_console_api_request` decorator is applied to this method, enabling
        it to send the generated QfRequest and return a QfResponse to the user.

        API Doc: Not available yet.
        """
        return cls._list_request(**kwargs)
