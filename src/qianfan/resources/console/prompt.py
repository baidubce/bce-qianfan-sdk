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
from typing import Optional, List, Any, Dict, Literal, TypeAlias, NewType
from qianfan.resources.console.utils import console_api_request
from qianfan.resources.typing import QfRequest
from qianfan.consts import (
    PromptSceneType,
    PromptFrameworkType,
    PromptType,
)
from qianfan.consts import Consts


class Prompt(object):
    """
    Class for Prompt API
    """

    @classmethod
    @console_api_request
    def create(
        cls,
        name: str,
        template: str,
        identifier: Literal["{}", "{{}}", "[]", "[[]]", "()", "(())"] = "{}",
        scene: PromptSceneType = PromptSceneType.Text2Text,
        framework: PromptFrameworkType = PromptFrameworkType.NotUse,
        variables: Optional[List[str]] = None,
        label_ids: Optional[List[int]] = None,
        negative_template: Optional[str] = None,
        negative_variables: Optional[List[str]] = None,
        **kwargs: Any
    ) -> QfRequest:
        req = QfRequest(method="POST", path=Consts.PromptCreateAPI)
        req.json_body = {
            "templateName": name,
            "templateContent": template,
            "variableIdentifier": identifier,
            "sceneType": scene.value,
            "frameworkType": framework.value,
            **kwargs,
        }
        if variables:
            req.json_body["templateVariables"] = ",".join(variables)
        if label_ids:
            req.json_body["labelIds"] = label_ids
        if negative_template:
            req.json_body["negativeTemplateContent"] = negative_template
        if negative_variables:
            req.json_body["negativeTemplateVariables"] = ",".join(negative_variables)
        return req

    @classmethod
    @console_api_request
    def detail(cls, id: int, **kwargs: Any) -> QfRequest:
        req = QfRequest(method="POST", path=Consts.PromptInfoAPI)
        req.json_body = {"templateId": id, **kwargs}
        return req

    @classmethod
    @console_api_request
    def update(
        cls,
        id: int,
        name: Optional[str] = None,
        label_ids: Optional[List[int]] = None,
        template: Optional[str] = None,
        identifier: Optional[Literal["{}", "{{}}", "[]", "[[]]", "()", "(())"]] = None,
        negative_template: Optional[str] = None,
        **kwargs: Any
    ) -> QfRequest:
        req = QfRequest(method="POST", path=Consts.PromptUpdateAPI)
        req.json_body = {"templateId": id, **kwargs}
        if name is not None:
            req.json_body["templateName"] = name
        if label_ids:
            req.json_body["labelIds"] = label_ids
        if identifier:
            req.json_body["variableIdentifier"] = identifier
        if template:
            req.json_body["templateContent"] = template
        if negative_template:
            req.json_body["negativeTemplateContent"] = negative_template
        return req

    @classmethod
    @console_api_request
    def delete(cls, id: int) -> QfRequest:
        req = QfRequest(method="POST", path=Consts.PromptDeleteAPI)
        req.json_body = {"templateId": id}
        return req

    @classmethod
    @console_api_request
    def list(
        cls,
        offset: int = 0,
        page_size: int = 10,
        name: Optional[str] = None,
        label_ids: List[int] = [],
        type: Optional[PromptType] = None,
        **kwargs: Any
    ) -> QfRequest:
        req = QfRequest(method="GET", path=Consts.PromptListAPI)
        req.json_body = {
            "offset": offset,
            "pageSize": page_size,
            "labelIds": label_ids,
            **kwargs,
        }
        if name is not None:
            req.json_body["name"] = name
        if type:
            req.json_body["type"] = type.value
        return req

    @classmethod
    @console_api_request
    def label_list(
        cls, offset: int = 0, page_size: int = 10, **kwargs: Any
    ) -> QfRequest:
        req = QfRequest(method="GET", path=Consts.PromptLabelListAPI)
        req.json_body = {"offset": offset, "pageSize": page_size, **kwargs}
        return req
