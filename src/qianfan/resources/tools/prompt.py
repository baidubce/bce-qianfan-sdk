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
Prompt API
"""

from typing import Optional, Union

from qianfan.config import get_config
from qianfan.consts import Consts
from qianfan.errors import InvalidArgumentError
from qianfan.resources.tools.utils import async_qianfan_api_request, qianfan_api_request
from qianfan.resources.typing import QfRequest, QfResponse


class _PromptBase(object):
    """
    Base class for internal prompt object
    """

    def render(self, raw: bool = False, **kwargs: str) -> Union[str, QfResponse]:
        """
        render prompt with `kwargs` as parameters and return rendered string
        if `bool` is set, raw response will be returned
        """
        raise NotImplementedError

    async def arender(self, raw: bool = False, **kwargs: str) -> Union[str, QfResponse]:
        """
        async render prompt with `kwargs` as parameters and return rendered string
        if `bool` is set, raw response will be returned
        """
        raise NotImplementedError


class Prompt(object):
    """
    Class for Prompt API
    """

    _prompt: _PromptBase
    """real prompt object to deal with prompt rendering"""

    def __init__(self, id: Optional[int] = None, template: Optional[str] = None):
        """
        Initialize a Prompt object.

        The object can be local or online. If `id` is provided, the object will be
        online. If `template` is provided, the object will be local.

        Parameters:
          id (Optional[int]):
            An optional integer representing the ID of a prompt. If provided, the
            template will be fetched and rendered from server.
            You can find the id at https://console.bce.baidu.com/qianfan/prompt/template
          template (Optional[str]):
            An optional string containing the template for the prompt. If provided,
            the template will be rendered locally.

        Example usage:

        .. code-block:: python
            # Initialize a Prompt with an ID to fetch a template from the server.
            online_prompt = Prompt(id=123)

            # Initialize a Prompt with a local template string.
            template_str = "This is a sample template: {variable}"
            local_prompt = Prompt(template=template_str)

        """
        if id is not None:
            self._prompt = _OnlinePrompt(id)
        elif template is not None:
            self._prompt = _LocalPrompt(template)
        else:
            raise InvalidArgumentError("either id or template must be provided")

    def render(self, raw: bool = False, **kwargs: str) -> Union[str, QfResponse]:
        """
        Render a prompt template with given parameters.

        Parameters:
          raw (bool):
            Return rendered string if not set, return QfResponse if set.
          kwargs (str):
            The parameters to be filled in the template.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Alisj3ard
        """
        return self._prompt.render(raw, **kwargs)

    async def arender(self, raw: bool = False, **kwargs: str) -> Union[str, QfResponse]:
        """
        Async render a prompt template with given parameters.

        Parameters:
          raw (bool):
            Return rendered string if not set, return QfResponse if set.
          kwargs (str):
            The parameters to be filled in the template.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Alisj3ard
        """
        return await self._prompt.arender(raw, **kwargs)


class _LocalPrompt(_PromptBase):
    """
    Prompt object for local template
    """

    def __init__(self, template: str):
        """
        Init with a template string
        """
        self._template = template

    def _render(self, **kwargs: str) -> str:
        """
        Render the template with given parameters.
        """
        return self._template.format(**kwargs)

    def render(self, raw: bool = False, **kwargs: str) -> Union[str, QfResponse]:
        """
        Render the template.
        """
        if raw:
            raise InvalidArgumentError("raw is not supported for local prompt")
        return self._render(**kwargs)

    async def arender(self, raw: bool = False, **kwargs: str) -> Union[str, QfResponse]:
        """
        Async render the template.
        """
        return self.render(raw, **kwargs)


class _OnlinePrompt(_PromptBase):
    """
    Prompt object for online template
    """

    def __init__(self, id: int):
        """
        Init the object with the prompt id from qianfan console.
        """
        self._id = id

    @staticmethod
    def _render_online_request(template_id: int, **kwargs: str) -> QfRequest:
        """
        generate a request for render api
        """
        req = QfRequest(
            method="GET", url=get_config().BASE_URL + Consts.PromptRenderAPI
        )
        req.query = {
            "id": str(template_id),
            **kwargs,
        }

        return req

    @qianfan_api_request
    def _render_online(self, **kwargs: str) -> QfRequest:
        """
        inner function for render

        @qianfan_api_request is applied to send the request and return the response.
        """
        return self._render_online_request(self._id, **kwargs)

    @async_qianfan_api_request
    async def _arender_online(self, **kwargs: str) -> QfRequest:
        """
        inner function for async render

        @async_qianfan_api_request is applied to send the request and return the
        response.
        """
        return self._render_online_request(self._id, **kwargs)

    def _extract_response(
        self, raw: bool, response: QfResponse
    ) -> Union[str, QfResponse]:
        """
        extract the content from response
        """
        if raw:
            return response
        return response["result"]["content"]

    def render(self, raw: bool = False, **kwargs: str) -> Union[str, QfResponse]:
        """
        send the request and return the response.
        """
        response = self._render_online(**kwargs)
        return self._extract_response(raw, response)

    async def arender(self, raw: bool = False, **kwargs: str) -> Union[str, QfResponse]:
        """
        async send the request and return the response.
        """
        response = await self._arender_online(**kwargs)
        return self._extract_response(raw, response)
