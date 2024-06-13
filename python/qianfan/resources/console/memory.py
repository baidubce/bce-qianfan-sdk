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
Memory API
"""

from typing import Any, List, Optional

from qianfan.consts import Consts
from qianfan.resources.console.utils import _get_console_v2_query, console_api_request
from qianfan.resources.typing import QfRequest


class Memory(object):
    """
    Class for Memory API
    """

    @classmethod
    def base_api_route(cls) -> str:
        """
        base api url route for memory.

        Returns:
            str: base api url route
        """
        return Consts.MemoryBaseRouteAPI

    @classmethod
    @console_api_request
    def create_system_memory(
        cls,
        app_id: str,
        description: str,
        **kwargs: Any,
    ) -> QfRequest:
        """
        create a named system memory.

        Parameters:
        app_id (str):
            id of qianfan app
        description (str):
            The description of the memory.
        kwargs:
            Additional keyword arguments that can be passed to customize the
            request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling
        it to send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/2lnlebz15
        """
        req = QfRequest(
            method="POST",
            url=cls.base_api_route(),
            query=_get_console_v2_query(Consts.MemoryCreateSystemMemoryAction),
        )
        req.json_body = {**kwargs, "appId": app_id, "description": description}
        return req

    @classmethod
    @console_api_request
    def describe_system_memories(
        cls,
        app_id: Optional[str] = None,
        marker: Optional[str] = None,
        max_keys: Optional[int] = None,
        **kwargs: Any,
    ) -> QfRequest:
        """
        list system memories.

        Parameters:
        app_id (str):
            id of qianfan app
        marker: Optional[str] = None,
                job_id, the marker of the first page.
        max_keys: Optional[int] = None,
            max keys of the page.
        kwargs:
            Additional keyword arguments that can be passed to customize the
            request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling
        it to send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/2lnlebz15
        """
        req = QfRequest(
            method="POST",
            url=cls.base_api_route(),
            query=_get_console_v2_query(Consts.MemoryDescribeSystemMemoriesAction),
            json_body={**kwargs},
        )
        if app_id:
            req.json_body["appId"] = app_id
        if marker:
            req.json_body["marker"] = marker
        if max_keys:
            req.json_body["maxKeys"] = max_keys
        return req

    @classmethod
    @console_api_request
    def delete_system_memory(
        cls,
        system_memory_id: str,
        **kwargs: Any,
    ) -> QfRequest:
        """
        delete system memory.

        Parameters:
        system_memory_id (str):
            id of existed memory
        kwargs:
            Additional keyword arguments that can be passed to customize the
            request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling
        it to send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/2lnlebz15
        """
        req = QfRequest(
            method="POST",
            url=cls.base_api_route(),
            query=_get_console_v2_query(Consts.MemoryDeleteSystemMemoryAction),
            json_body={**kwargs, "systemMemoryId": system_memory_id},
        )
        return req

    @classmethod
    @console_api_request
    def describe_system_memory(
        cls,
        system_memory_id: str,
        **kwargs: Any,
    ) -> QfRequest:
        """
        get memory detail.

        Parameters:
        system_memory_id (str):
            id of existed memory
        kwargs:
            Additional keyword arguments that can be passed to customize the
            request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling
        it to send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/2lnlebz15
        """
        req = QfRequest(
            method="POST",
            url=cls.base_api_route(),
            query=_get_console_v2_query(Consts.MemoryDescribeSystemMemoryAction),
            json_body={**kwargs, "systemMemoryId": system_memory_id},
        )
        return req

    @classmethod
    @console_api_request
    def modify_system_memory(
        cls,
        system_memory_id: str,
        memories: List[Any],
        **kwargs: Any,
    ) -> QfRequest:
        """
        modify system memory.

        Parameters:
        system_memory_id (str):
            id of existed memory
        memories (List[Any]):
            new content for the memory
        kwargs:
            Additional keyword arguments that can be passed to customize the
            request.

        Note:
        The `@console_api_request` decorator is applied to this method, enabling
        it to send the generated QfRequest and return a QfResponse to the user.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/2lnlebz15
        """
        req = QfRequest(
            method="POST",
            url=cls.base_api_route(),
            query=_get_console_v2_query(Consts.MemoryModifySystemMemoryAction),
            json_body={
                **kwargs,
                "systemMemoryId": system_memory_id,
                "memories": memories,
            },
        )
        return req
