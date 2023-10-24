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

from typing import Any, Dict

from qianfan.config import GLOBAL_CONFIG
from qianfan.consts import Consts
from qianfan.resources.llm.utils import async_qianfan_api_request, qianfan_api_request
from qianfan.resources.typing import QfRequest


class Prompt(object):
    """
    Class for Service API
    """

    @classmethod
    def _render(
        cls, template_id: int, params: Dict[str, str], **kwargs: Any
    ) -> QfRequest:
        """
        inner function for render
        generate a request for render api
        """
        req = QfRequest(
            method="GET", url=GLOBAL_CONFIG.BASE_URL + Consts.PromptRenderAPI
        )
        req.query = {
            "id": str(template_id),
            **params,
            **kwargs,
        }

        return req

    @classmethod
    @qianfan_api_request
    def render(
        cls, template_id: int, params: Dict[str, str], **kwargs: Any
    ) -> QfRequest:
        """
        Render a prompt template with given parameters.

        Parameters:
          template_id (int):
            Unique identifier for the template to be rendered.
          params (Dict[str, str]):
            A dictionary of key-value pairs representing the parameters to be filled in
            the template.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Alisj3ard
        """

        return cls._render(template_id, params, **kwargs)

    @classmethod
    @async_qianfan_api_request
    async def arender(
        cls, template_id: int, params: Dict[str, str], **kwargs: Any
    ) -> QfRequest:
        """
        Async render a prompt template with given parameters.

        Parameters:
          template_id (int):
            Unique identifier for the template to be rendered.
          params (Dict[str, str]):
            A dictionary of key-value pairs representing the parameters to be filled in
            the template.
          kwargs (Any):
            Additional keyword arguments that can be passed to customize the request.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Alisj3ard
        """

        return cls._render(template_id, params, **kwargs)
